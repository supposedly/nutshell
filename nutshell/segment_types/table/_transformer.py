from functools import wraps
from inspect import signature
from itertools import chain, repeat
from operator import attrgetter

import bidict
import lark
from lark import Transformer, Tree, Discard, v_args

from nutshell.common.errors import *
from nutshell.common.utils import KILL_WS
from . import _symutils as symutils
from ._classes import *

SPECIALS = {'...', '_', 'N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'}
with open('nutshell/segment_types/table/lark_assets/grammar.lark') as f:
    NUTSHELL_GRAMMAR = f.read()


def fix(meta):
    if isinstance(meta, tuple):
        return meta
    return (meta.line, meta.column, meta.end_column)


def inline(func):
    @wraps(func)
    def wrapper(self, children, meta):
        return func(self, fix(meta), *children)
    return wrapper


def _add_mod(modulus, index, add, start=1):
    index += add - start
    return index % modulus + start


class MetaTuple(tuple):  # eh
    def __new__(cls, meta, it):
        return super().__new__(cls, it)
    
    def __init__(self, meta, _):
        self.meta = meta


@v_args(meta=True)
class Preprocess(Transformer):
    """
    Collect var declarations and directives
    """
    def __init__(self, tbl):
        self._tbl = tbl
        self.directives = tbl.directives
        self.vars = tbl.vars
    
    def kill_string(self, val, meta, li=False):
        if isinstance(val, str):
            if val in SPECIALS:
                return str(val)
            if val.isdigit():
                return [int(val)] if li else int(val)
            try:
                return self._tbl.vars[val]
            except KeyError:
                raise ReferenceErr(
                  meta,
                  f'Undefined variable {val}'
                )
        return val
    
    def kill_strings(self, val, meta):
        return [self.kill_string(i, meta) for i in val]
    
    def check_cdir(self, cdir, meta, *, return_int=True, enforce_int=False):
        if enforce_int and hasattr(self._tbl.symmetries, 'special') and not cdir.isdigit():
            raise SyntaxErr(
              fix(meta),
              f"Compass directions have no meaning under {self.directives['symmetries']} symmetry. "
              f'Instead, refer to previous states using numbers 0..8: here, {cdir} would be {self._tbl.neighborhood[cdir]}'
              )
        try:
            if return_int:
                return int(cdir) if cdir.isdigit() else self._tbl.neighborhood[str(cdir)]
            return int(cdir != '0') and self._tbl.neighborhood.inv[int(cdir)] if cdir.isdigit() else str(cdir)
        except KeyError:
            pre = 'Transition index' if cdir.isdigit() else 'Compass direction'
            raise ReferenceErr(
              fix(meta),
              f"{pre} {cdir} does not exist in {self.directives['neighborhood']} neighborhood"
              )
    
    def special_transform(self, initial, resultant, napkin):
        """
        Handle the special ~ syntax for current symmetries
        """
        special_params = {
          'length': self._tbl.trlen,
          'initial': initial,
          'resultant': resultant,
          'values': napkin,
          }.items()
        params = signature(self._tbl.symmetries.special).parameters
        return self._tbl.symmetries.special(**{k: v for k, v in special_params if k in params})
    
    def unravel_permute(self, tree, meta):
        if isinstance(tree, tuple):
            return tree
        first, *rest = tree.children
        if not rest:
            return (self.kill_string(first, meta), None)
        # We can now assume first is a tree, I think
        if first.data in ('cdir', 'crange'):
            raise SyntaxErr(
              fix(first.meta),
              f"Cannot specify compass directions under {self.directives['symmetries']} symmetry"
              )
        # Nothing left to return here... right? Because permute_shorthand trees
        # will already have been transformed (by self.permute_shorthand) and
        # returned by the first conditional in this method
    
    #-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#
    
    def table(self, transitions, meta):
        return list(chain.from_iterable(transitions))
    
    @inline
    def transition(self, meta, main, aux_first=None, aux_second=None):
        if aux_first is not None and aux_first.meta == 'normal':
            return list(chain(main.apply_aux(aux_second), main.expand(), main.apply_aux(aux_first)))
        return list(chain(main.apply_aux(aux_first), main.expand(), main.apply_aux(aux_second)))
    
    @inline
    def print_var(self, meta, var):
        print(self.kill_string(var, meta))
        raise Discard
    
    @inline
    def directive(self, meta, name, val):
        val = val.translate(KILL_WS)
        self.directives[str(name)] = val
        if name in ('n_states', 'states'):
            if val == '?':
                raise UnsupportedFeature(
                  fix(meta),
                  f"`{name}: ?` is currently not supported. Please specify your rule's number of states explicitly :("
                  )
            self._tbl.n_states = val
        if name == 'symmetries':
            self._tbl.add_sym_type(val)
        raise Discard
    
    @inline
    def var_decl(self, meta, name, var):
        self.vars[VarName(name)] = self.noref_var(var, meta)
        raise Discard
    
    def permute_shorthand(self, children, meta):
        state, *permute = children
        return MetaTuple(meta, (self.kill_string(state, meta), permute[0] if permute else None))
    
    def main(self, children, meta):
        initial, resultant = children.pop(0), children.pop(-1)
        try:
            initial = self.kill_string(initial, meta.line)
        except ReferenceErr as e:
            raise ReferenceErr((meta.line, meta.column, meta.column + len(str(initial))), e.msg)
        try:
            resultant = self.kill_string(resultant, meta.line)
        except ReferenceErr as e:
            raise ReferenceErr((meta.line, meta.end_column - len(str(resultant)), meta.end_column), e.msg)
        
        if hasattr(self._tbl.symmetries, 'special'):
            seq = [self.unravel_permute(i, meta) for i in children]
            napkin = dict(enumerate(self.special_transform(initial, resultant, seq), 1))
        else:
            idx = 1
            napkin = {}
            add_mod = partial(_add_mod, self._tbl.trlen)
            offset_initial = False  # whether it starts on a compass dir other than the first
            
            for tr_state in children:
                m = fix(tr_state.meta)
                first, *rest = tr_state.children
                first_data = getattr(first, 'data', None)
                rest = self.kill_strings(rest, m)
                
                if first_data == 'cdir':
                    cdir = self.check_cdir(first.children[0], first.meta)
                    napkin[cdir], = rest
                    if cdir != idx:
                        if idx == 1:
                            idx = cdir
                            offset_initial = True
                        else:
                            raise SyntaxErr(
                              fix(first.meta),
                              'Out-of-sequence compass direction '
                              f'(expected {self._tbl.neighborhood.inv[idx]}, got {first.children[0]})'
                              )
                    idx = add_mod(idx, 1)
                elif first_data == 'crange':
                    a, b = first.children
                    int_a = self.check_cdir(a, (first.meta.line, first.meta.column, len(a) + first.meta.column))
                    int_b = self.check_cdir(b, (first.meta.line, first.meta.end_column - len(b), first.meta.end_column))
                    crange = range(int_a, 1+int_b)
                    
                    if len(crange) == 1 or not crange and not offset_initial:
                        if idx != 1:
                            raise SyntaxErr(
                              fix(first.meta),
                              f'Invalid compass-direction range ({b} does not follow {a} going clockwise)'
                              )
                        offset_initial = True
                    
                    if not crange and offset_initial:
                        crange = (*range(self._tbl.neighborhood[a], 1+self._tbl.trlen), *range(1, 1+self._tbl.neighborhood[b]))
                    
                    if idx != crange[0]:
                        if idx == 1:
                            idx = crange[0]
                            offset_initial = True
                        else:
                            nbhd = self._tbl.neighborhood.inv
                            raise SyntaxErr(
                              (first.meta.line, first.meta.column, len(a) + first.meta.column),
                              'Out-of-sequence compass direction '
                              f'(expected {nbhd[idx]}, got {nbhd[crange[0]]})'
                              )
                    
                    for i in crange:
                        if i in napkin:
                            raise ValueErr(
                              fix(first.meta),
                              'Compass-direction range contains duplicate '
                              '(i.e. contains at least one compass direction used elsewhere in this transition)'
                              )
                        napkin[i], = rest
                        idx = add_mod(idx, 1)
                else:
                    napkin[idx], = self.kill_strings(tr_state.children, m)
                    idx = add_mod(idx, 1)
            if len(napkin) != self._tbl.trlen:
                raise ValueErr(
                  (meta.line, children[0].meta.column, children[-1].meta.end_column),
                  f"Bad transition length for {self.directives['neighborhood']!r} neighborhood "
                  f'(expected {2+self._tbl.trlen} states, got {2+len(napkin)})'
                  )
        return TransitionGroup(self._tbl, initial, napkin, resultant, context=fix(meta))
    
    def hoist_aux(self, children, meta):
        for idx, i in enumerate(children):
            if isinstance(i, tuple):
                for child in i:
                    child.hoist = True
                children[idx:1+idx] = i
            else:
                i.hoist = True
        return MetaTuple('hoist', children)
    
    def normal_aux(self, children, meta):
        for idx, i in enumerate(children):
            if isinstance(i, tuple):
                children[idx:1+idx] = i
        return MetaTuple('normal', children)
    
    def cdir_delay(self, children, meta):
        return {
          'cdir': self.check_cdir(children[0], meta, return_int=False),
          'delay': int(children[1]) if len(children) > 1 else None,
          'meta': fix(meta)
          }
    
    @inline
    def symmetried_aux(self, meta, symmetries, *auxiliaries):
        self._tbl.add_sym_type(symmetries)
        symmetries = symutils.get_sym_type(symmetries)
        for aux in auxiliaries:
            aux.symmetries = symmetries
        return auxiliaries
    
    @inline
    def aux_bare(self, meta, cdir_info, val):
        cdir_to, delay = cdir_info['cdir'], cdir_info['delay']
        return Auxiliary(self._tbl, cdir_to, delay, self.kill_string(val, meta), context=meta)
    
    @inline
    def aux_bind_self(self, meta, cdir_info, cdir_from):
        cdir_from = self.check_cdir(cdir_from, meta, return_int=False, enforce_int=True)
        cdir_to, delay = cdir_info['cdir'], cdir_info['delay']
        return Auxiliary(self._tbl, cdir_to, delay, Binding(cdir_from, context=(meta[0], meta[1]+len(cdir_to), meta[2])), context=meta)
    
    @inline
    def aux_map_self(self, meta, cdir_info, val):
        cdir_to, delay = cdir_info['cdir'], cdir_info['delay']
        return Auxiliary(self._tbl, cdir_to, delay, Mapping(cdir_to, self.kill_string(val, meta), context=(meta[0], meta[1]+len(cdir_to), meta[2])), context=meta)
    
    @inline
    def aux_map_other(self, meta, cdir_info, cdir_from, val):
        cdir_to, delay = cdir_info['cdir'], cdir_info['delay']
        cdir_from = self.check_cdir(cdir_from, (meta[0], meta[1] + cdir_info['meta'][1] + 1, len(cdir_from)), return_int=False, enforce_int=True)
        return Auxiliary(self._tbl, cdir_to, delay, Mapping(cdir_from, self.kill_string(val, meta), context=(meta[0], meta[1]+len(cdir_to), meta[2])), context=meta)
    
    @inline
    def range(self, meta, start, stop):
        return tuple(range(int(start), 1+int(stop)))
    
    @inline
    def range_step(self, meta, step, start, stop):
        return tuple(range(int(start), 1+int(stop), int(step)))
    
    @inline
    def noref_repeat_int(self, meta, num, multiplier):
        return self.noref_var([num], meta) * int(multiplier)
    
    @inline
    def noref_int_to_var_length(self, meta, num, var):
        return self.noref_var([num], meta) * len(self.kill_string(var, meta))
    
    @inline
    def noref_repeat_var(self, meta, var, num):
        return self.kill_string(var, meta) * int(num)
    
    @inline
    def noref_subt(self, meta, minuend, subtrhnd):
        return tuple(i for i in self.kill_string(minuend, meta) if i not in self.kill_string(subtrhnd, meta, li=True))
    
    @inline
    def noref_live_except(self, meta, subtrhnd):
        return self.noref_subt(('live', subtrhnd), meta)
    
    @inline
    def noref_all_except(self, meta, subtrhnd):
        return self.noref_subt(('any', subtrhnd), meta)
    
    def noref_var(self, children, meta):
        ret = []
        m = fix(meta)
        for val in map(self.kill_string, children, repeat(m)):
            if isinstance(val, (tuple, StateList)):
                ret.extend(val)
            elif isinstance(val, int):
                ret.append(int(val))
            else:
                raise NutshellException(fix(meta), val)
        return StateList(ret, context=fix(meta))
    
    def var(self, children, meta):
        m = fix(meta)
        return StateList(self.kill_strings(children, m), context=m)
    
    @inline
    def repeat_int(self, meta, a, b):
        return RepeatInt(self.kill_string(a, meta), int(b), context=meta)
    
    @inline
    def leave_alone_mult(self, meta, underscore, mult):
        return RepeatInt([None], self.kill_string(mult, meta), context=meta)
    
    @inline
    def int_to_var_length(self, meta, num, var):
        return IntToVarLength(int(num), self.kill_string(var, meta), context=meta)
    
    @inline
    def repeat_var(self, meta, var, num):
        return RepeatVar(self.kill_string(var, meta), int(num), context=meta)
    
    @inline
    def subt(self, meta, var, subtrhnd):
        return Subt(self.kill_string(var, meta), StateList(self.kill_string(subtrhnd, meta), context=meta), context=meta)
    
    @inline
    def live_except(self, meta, subtrhnd):
        return self.subt(('live', subtrhnd), meta)
    
    @inline
    def all_except(self, meta, subtrhnd):
        return self.subt(('any', subtrhnd), meta)
    
    @inline
    def mapping(self, meta, cdir, map_to):
        if hasattr(self._tbl.symmetries, 'special') and not cdir.isdigit():
            raise SyntaxErr(
              meta,
              f"Compass directions have no meaning under {self.directives['symmetries']} symmetry. "
              f'Instead, refer to previous states using numbers 0..8: here, {cdir} would be {self._tbl.neighborhood[cdir]}'
              )
        cdir = self.check_cdir(cdir, meta, return_int=False)
        return Mapping(cdir, self.kill_string(map_to, meta), context=meta)
    
    @inline
    def binding(self, meta, cdir):
        if hasattr(self._tbl.symmetries, 'special') and not cdir.isdigit():
            raise SyntaxErr(
              meta,
              f"Compass directions have no meaning under {self.directives['symmetries']} symmetry.\n  "
              f'Instead, refer to previous states using numbers 0..8: here, {cdir} would be {self._tbl.neighborhood[cdir]}'
              )
        cdir = self.check_cdir(cdir, meta, return_int=False)
        return Binding(cdir, context=meta)
