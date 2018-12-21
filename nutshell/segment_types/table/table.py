import re
from collections import Iterable
from functools import partial
from itertools import chain, cycle, islice, zip_longest
from inspect import signature, Parameter

import bidict
from ergo.misc import typecast

from nutshell.cli import cli
from nutshell.common.classes import TableRange
from nutshell.common.utils import printv, printq
from nutshell.common import macros
from nutshell.common.errors import *
from .lark_assets import parser as lark_standalone
from ._transformer import Preprocess, NUTSHELL_GRAMMAR
from ._classes import VarName, StateList
from . import _symutils as symutils, _neighborhoods as nbhoods

# no need to catch \s*,\s* because directive values are translated with KILL_WS
CUSTOM_NBHD = re.compile(r'(?:[NS][EW]?|[EW])(?:,(?:[NS][EW]?|[EW]))*')


def generate_cardinals(d):
    """{'name': ('N', 'E', ...)} >>> {'name': {'N' :: 1, 'E' :: 2, ...}}"""
    return {k: bidict.bidict(enumerate(v, 1)).inv for k, v in d.items()}


class Bidict(bidict.bidict):
    on_dup_kv = bidict.IGNORE
    on_dup_val = bidict.IGNORE


class TableSegment:
    CARDINALS = generate_cardinals({
      'oneDimensional': ('W', 'E'),
      'vonNeumann': ('N', 'E', 'S', 'W'),
      'hexagonal': ('N', 'E', 'SE', 'S', 'W', 'NW'),
      'Moore': ('N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'),
      })
    TRLENS = {k: len(v) for k, v in CARDINALS.items()}

    def __init__(self, tbl, start=0, *, dep: ['@NUTSHELL'] = (None,)):
        # parser (lexer?) dies if there are blank lines right at the start
        # so idk
        tbl = list(tbl)
        while tbl and not tbl[0].split('#', 1)[0].strip():
            del tbl[0]
            start += 1
        self._src = tbl
        self.start = start
        self._n_states = 0
        self.comments = {}
        self._nbhd = self._trlen = None
        dep, = dep
        
        if dep is not None:
            dep.replace(self._src)
            self._constants = dep.constants
            if self._constants:
                self._n_states = 1 + max(self._constants.values())
        
        self.directives = {'neighborhood': 'Moore', 'symmetries': 'none', 'states': self._n_states}
        self.gollyize_nbhd = None
        self.default_sym_used = False
        self.vars = Bidict()  # {VarName(name) | str(name) :: Variable(value)}
        self.sym_types = set()
        self.transitions = []
        self._constants = {}
        self.current_macros = []
        self._prepped_macros = {}
        self.available_macros = macros.__dict__.copy()

        self.specials = {'any': VarName('any'), 'live': VarName('live')}
        self.new_varname = VarName.new_generator()
        
        if not tbl:
            self.final = []
            self._n_states = self.directives['n_states'] = max(2, self.directives.pop('states', 2))
            return
        
        transformer = Preprocess(tbl=self)
        parser = lark_standalone.Lark_StandAlone(tbl=self)
        try:
            _parsed = parser.parse('\n'.join(self._src))
        except lark_standalone.UnexpectedCharacters as e:
            raise SyntaxErr(
              (e.line, e.column, 1+e.column),
              f"Unexpected character {{span!r}}{f' (expected {e.allowed})' if e.allowed else ''}",
              shift=self.start
              )
        except lark_standalone.UnexpectedToken as e:
            raise SyntaxErr(
              (e.line, e.column, 1+e.column),
              f"Unexpected token {{span!r}} (expected {'/'.join(e.expected)})",
              shift=self.start
              )
        else:
            self.update_special_vars()
        self._data = transformer.transform(_parsed)
        
        if len(self.sym_types) <= 1 and not hasattr(next(iter(self.sym_types), None), 'fallback'):
            sym = next(iter(self.sym_types), None)
            if sym is not None:
                # force these to be equal (in the event of, say, inline-rulestring
                # napkins' having been used, which don't update directives)
                self.directives['symmetries'] = sym.name[0] if hasattr(sym, 'name') else sym.__name__.lower()
            self.final = [t.fix_vars() for t in self._data]
        else:
            MinSym = symutils.find_min_sym_type(self.sym_types, self.trlen)
            self.directives['symmetries'] = MinSym.name[0] if hasattr(MinSym, 'name') else MinSym.__name__.lower()
            self.final = [new_tr for tr in self._data for new_tr in tr.in_symmetry(MinSym)]
        self.directives['n_states'] = self.directives.pop('states')
        self._apply_macros()
    
    def __getitem__(self, item):
        return self._src[item]
    
    def __iter__(self):
        vars_valid = any(i.rep > -1 for i in self.vars)
        yield f"neighborhood: {self.directives['neighborhood']}"
        for directive, value in self.directives.items():
            if directive != 'neighborhood':
                yield f'{directive}: {value}'
        if vars_valid or self.final:  # if there are more things to yield
            yield ''
        for var, states in self.vars.items():
            if var.rep == -1:
                continue
            # set() removes duplicates and gives braces
            # Golly gives up reading variables past a certain line length so we unfortunately have to .replace(' ', '')
            yield f'var {var.name}.0 = ' + f'{set(states)}'.replace(' ', '')
            for suf in range(1, 1+var.rep):
                yield f'var {var.name}.{suf} = {var.name}.0'
        if vars_valid:  # if that loop ran
            yield ''
        yield from self._iter_final_transitions()
    
    def _iter_final_transitions(self):
        src, cmt = cli.result.transpile.comment_src, cli.result.transpile.preserve_comments
        seen = set()
        last_cmt_lno = -1
        for tr in self.final:
            if tr.ctx not in seen:
                seen.add(tr.ctx)
                lno, start, end = tr.ctx
                start, end = None if not start else start-1, None if end is None else end-1
                if cmt:
                    for comment_lno in self.comments:
                        if last_cmt_lno < comment_lno < lno:
                            last_cmt_lno = comment_lno
                            yield self.comments[comment_lno]
                if src:
                    #yield ''
                    yield src.format(line=lno+self.start, span=self[lno-1][start:end])
                if cmt and lno in self.comments:
                    last_cmt_lno = lno
                    yield '{}{}'.format(', '.join(map(str, tr)), self.comments[lno])
                    continue
            yield ', '.join(map(str, tr))
    
    @property
    def neighborhood(self):
        if self._nbhd is None:
            self._nbhd = self.CARDINALS[self.directives['neighborhood']]
        return self._nbhd
    
    @neighborhood.setter
    def neighborhood(self, val):
        if CUSTOM_NBHD.fullmatch(val):
            nbhd = val.split(',')
            if len(nbhd) != len(set(nbhd)):
                raise ValueError('Duplicate compass directions in neighborhood')
            self._nbhd = bidict.bidict(enumerate(nbhd, 1)).inv
            self.gollyize_nbhd = nbhoods.get_gollyizer(self, nbhd)
        elif val in self.CARDINALS:
            self._nbhd = self.CARDINALS[val]
        else:
            raise ValueError('Unknown or invalid neighborhood')
        self._trlen = None

    @property
    def trlen(self):
        if self._trlen is None:
            self._trlen = len(self.neighborhood)
        return self._trlen
    
    @property
    def symmetries(self):
        return symutils.get_sym_type(self.directives['symmetries'])
    
    @property
    def n_states(self):
        return self._n_states
    
    @n_states.setter
    def n_states(self, value):
        try:
            value = int(value)
        except (TypeError, ValueError):
            if value == '?':
                self.directives['states'] = self._n_states
        else:
            self._n_states = self.directives['states'] = value
    
    def update_special_vars(self, value=None):
        if value == '?':
            self.directives['states'] = self.n_states
        elif value is not None:
            if not value.isdigit():
                raise ValueError(value)
            self.n_states = int(value)
        self.vars[self.specials['any']] = StateList(range(self.n_states), context=None)
        self.vars[self.specials['live']] = StateList(range(1, self.n_states), context=None)
    
    def add_sym_type(self, name):
        try:
            self.sym_types.add(symutils.get_sym_type(name))
        except (ImportError, ModuleNotFoundError):
            raise ImportError(f'No symmetry type {name!r} found')
    
    def add_macros(self, path):
        with open(path) as f:
            exec(f.read(), self.available_macros)
    
    def set_macro(self, meta, name, args):
        self.current_macros.append((meta.lno, self._prep_macro(self.available_macros[name]), args.split()))
    
    def _prep_macro(self, func):
        if func not in self._prepped_macros:
            kwargs = {i.name for i in signature(func).parameters.values() if i.kind is Parameter.KEYWORD_ONLY}
            special_params = {
              'directives': self.directives,
              'n_states': self.n_states,
              'variables': self.vars,
              'table': self
            }.items()
            self._prepped_macros[func] = partial(typecast(func), **{k: v for k, v in special_params if k in kwargs})
        return self._prepped_macros[func]

    def _apply_macros(self):
        if not self.final or not self.current_macros:
            return
        mcrs = {}
        for lno, macro, args in self.current_macros:
            if '\\' not in args:
                mcrs.setdefault(macro, []).append((lno, args))
                continue
            start, args = mcrs[macro].pop()
            from_ = next(i for i, v in enumerate(self.final) if v.ctx.lno > start)
            to = next(i for i, v in enumerate(self.final) if v.ctx.lno > lno)
            self.final[from_:to] = macro([i for i in self.final if start < i.ctx.lno < lno], *args)
    
    def check_cdir(self, cdir, meta, *, return_int=True, enforce_int=False):
        if cdir in ('FG', 'BG'):
            raise SyntaxErr(meta, f'Invalid reference {cdir!r} outside of inline-rulestring transition')
        if enforce_int and hasattr(self.symmetries, 'special') and not cdir.isdigit():
            raise SyntaxErr(
              meta,
              f"Compass directions have no meaning under {self.directives['symmetries']} symmetry. "
              f'Instead, refer to previous states using numbers 0..8: here, {cdir} would be {self.neighborhood[cdir]}'
              )
        try:
            if return_int:
                return int(cdir) if cdir.isdigit() else self.neighborhood[str(cdir)]
            return int(cdir != '0') and self.neighborhood.inv[int(cdir)] if cdir.isdigit() else str(cdir)
        except KeyError:
            pre = 'Transition index' if cdir.isdigit() else 'Compass direction'
            raise ReferenceErr(
              meta,
              f"{pre} {cdir} does not exist in neighborhood {self.directives['neighborhood']!r}"
              )
    
    def match(self, tr):
        printq('Complete!\n\nSearching for match...')
        start, *in_napkin, end = tr
        if len(in_napkin) != self.trlen:
            raise Error(None, f'Bad length for match (expected {2+self.trlen} states, got {2+len(in_napkin)})')
        in_trs = [(start, *napkin, end) for napkin in self.symmetries(in_napkin).expand()]
        for tr in self._data:
            for in_tr in in_trs:
                for cur_len, (in_state, tr_state) in enumerate(zip(in_tr, tr), -1):
                    if in_state != '*' and not (in_state in tr_state if isinstance(tr_state, Iterable) else in_state == getattr(tr_state, 'value', tr_state)):
                        if cur_len == self.trlen:
                            lno, start, end = tr.ctx
                            return (
                              'No match\n\n'
                              f'Impossible match!\nOverridden on line {self.start+lno} by:\n  {self[lno-1]}\n'
                              f"""{"" if start == 1 else f"  {' '*(start-1)}{'^'*(end-start)}"}\n"""  # TODO FIXME: deuglify
                              f"Specifically (compiled line):\n  {', '.join(map(str, tr.fix_vars()))}"
                              )
                        break
                else:
                    lno, start, end = tr.ctx
                    return (
                      'Found!\n\n'
                      f'Line {self.start+lno}:\n  {self[lno-1]}\n'
                      f"""{"" if start == 1 else f"  {' '*(start-1)}{'^'*(end-start)}"}\n"""  # TODO FIXME: deuglify
                      f"Compiled line:\n  {', '.join(map(str, tr.fix_vars()))}"
                      )
        if start == end:
            return 'No match\n\nThis transition is the result of unspecified default behavior'
        return 'No match'
