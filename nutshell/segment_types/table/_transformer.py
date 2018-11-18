from collections import namedtuple
from functools import wraps
from inspect import signature
from itertools import chain, repeat
from operator import attrgetter
from pkg_resources import resource_filename

import bidict
from .lark_assets.parser import Transformer, Tree, Discard, v_args

from nutshell.common.utils import KILL_WS
from nutshell.common.errors import *
from ._classes import *
from . import _symutils as symutils, _neighborhoods as nbhoods

SPECIALS = {'...', '_', 'N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'}
ROTATE_4_REFLECT = symutils.get_sym_type('rotate4reflect')
PERMUTE = symutils.get_sym_type('permute')
Meta = namedtuple('Meta', ['lno', 'start', 'end'])

try:
    with open(resource_filename('nutshell', 'segment_types/table/lark_assets/grammar.lark')) as f:
        NUTSHELL_GRAMMAR = f.read()
except FileNotFoundError:
    with open('nutshell/segment_types/table/lark_assets/grammar.lark') as f:
        NUTSHELL_GRAMMAR = f.read()


def fix(meta):
    if isinstance(meta, tuple):
        return meta
    return Meta(meta.line, meta.column, meta.end_column)


def inline(func):
    @wraps(func)
    def wrapper(self, children, meta):
        return func(self, fix(meta), *children)
    return wrapper


def _add_mod(modulus, index, add, start=1):
    index += add - start
    return index % modulus + start


# I don't know where to put these two functions
def get_rs_cdir(reference, nb_count, letter, meta, *, idx=None):
    if idx is None:
        idx = reference.idx
    if letter is None:
        if nb_count == '0':
            if idx == 'FG':
                raise ValueErr(meta, 'Reference to FG, but given rulestring includes 0, which has no foreground states')
            return 'N'
        if nb_count == '8':
            if idx == 'BG':
                raise ValueErr(meta, 'Reference to BG, but given rulestring includes 8, which has no background states')
            return 'N'
        return 'N' if idx == 'FG' else nbhoods.CDIRS[int(nb_count)] if idx == 'BG' else '0'
    if idx == 'BG':
        return nbhoods.BG_LOCATIONS[nb_count][letter]
    if idx == 'FG':
        return nbhoods.FG_LOCATIONS[nb_count][letter]
    return '0'


def resolve_rs_ref(term, nb_count, letter, meta):
    if isinstance(term, StateList):
        if any(isinstance(i, (InlineRulestringBinding, InlineRulestringMapping)) for i in term):
            return term.__class__((
              resolve_rs_ref(i, nb_count, letter, meta)
                if isinstance(i, (InlineRulestringBinding, InlineRulestringMapping))
                else i
                for i in term
                ),
              context=term.ctx
              )
    if not isinstance(term, (InlineRulestringBinding, InlineRulestringMapping)):
        return term
    new_cdir = get_rs_cdir(term, nb_count, letter, meta)
    if isinstance(term, InlineRulestringBinding):
        return Binding(new_cdir, context=term.ctx)
    if isinstance(term, InlineRulestringMapping):
        return Mapping(new_cdir, term.map_to, context=term.ctx)
    return term


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
        self._nbhd_assigned = False
    
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
                  fix(meta),
                  f'Undefined variable {val}'
                  )
        return val
    
    def kill_strings(self, val, meta):
        return [self.kill_string(i, meta) for i in val]
    
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
        raise Exception('unexpected branch')
    
    #-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#
    
    def table(self, transitions, meta):
        return list(chain.from_iterable(transitions))
    
    @inline
    def transition(self, meta, main, aux_first=None, aux_second=None):
        if aux_first is not None and aux_first.meta == 'normal':
            # then aux_second must be 'hoisted', so apply it first
            return list(chain(main.apply_aux(aux_second), main.expand(), main.apply_aux(aux_first)))
        return list(chain(main.apply_aux(aux_first), main.expand(), main.apply_aux(aux_second)))
    
    @inline
    def print_var(self, meta, var):
        print(self.kill_string(var, meta))
        raise Discard
    
    @inline
    def comment(self, meta, text):
        self._tbl.comments[meta[0]] = text
        raise Discard
    
    @inline
    def end_bs(self, meta, text):
        if text.lstrip().startswith('#'):
            self._tbl.comments[meta[0]] = text
        raise Discard
    
    @inline
    def directive(self, meta, name, val):
        if '#' in val:  # since comments not handled otherwise
            val = val[:val.index('#')].rstrip()
        if name == 'macros':
            self._tbl.add_macros(val.translate(KILL_WS))
            raise Discard
        if name in self._tbl.available_macros:
            self._tbl.set_macro(meta, name, val)
            raise Discard
        val = val.translate(KILL_WS)
        self.directives[str(name)] = val
        if name in ('n_states', 'states'):
            self._tbl.update_special_vars(val)
        elif name == 'neighborhood':
            if self._nbhd_assigned:
                raise ValueErr(meta, '`neighborhood` directive cannot be reassigned')
            try:
                self._tbl.neighborhood = val
            except ValueError as e:
                raise ValueErr(meta, e.args[0])
            self._nbhd_assigned = True
        else:
            # directives are more like comments than they are source
            self._tbl.comments[meta[0]] = f'#{name}: {val}'
        if name == 'symmetries':
            self._tbl.add_sym_type(val)
        raise Discard
    
    @inline
    def var_decl(self, meta, name, var):
        self.vars[VarName(name)] = self.noref_var(var, meta)
        raise Discard
    
    def permute_shorthand(self, children, meta):
        state, *permute = children
        if not hasattr(self._tbl.symmetries, 'special'):
            if permute:
                raise SyntaxErr(
                  fix(meta),
                  f"Cannot use tilde-based shorthand under {self.directives['symmetries']} symmetry.\n  "
                  '(Try a range of compass directions instead)'
                  )
            # XXX: this is suspect (cryptic message and i'm not sure it's raised in the right situation)
            raise SyntaxErr(
              fix(meta),
              f"Cannot use inline-binding shorthand with no implication of multiple states"
              )
        return MetaTuple(meta, (self.kill_string(state, meta), str(permute[0]) if permute else None))
    
    def main(self, children, meta):
        if not self._tbl.default_sym_used and self.directives['symmetries'] == 'none':
            self._tbl.default_sym_used = True
            self._tbl.add_sym_type('none')
        
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
                    cdir = self._tbl.check_cdir(first.children[0], fix(first.meta))
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
                    int_a = self._tbl.check_cdir(a, (first.meta.line, first.meta.column, len(a) + first.meta.column))
                    int_b = self._tbl.check_cdir(b, (first.meta.line, first.meta.end_column - len(b), first.meta.end_column))
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
                    
                    rest, = rest
                    if isinstance(rest, InlineBinding):
                        rest.set(idx)
                        napkin[crange[0]] = rest.give()
                        crange = range(1+crange[0], 1+crange[-1])
                        idx = add_mod(idx, 1)
                        rest = rest.give()
                    
                    for i in crange:
                        if i in napkin:
                            raise ValueErr(
                              fix(first.meta),
                              'Compass-direction range contains duplicate '
                              '(i.e. contains at least one compass direction used elsewhere in this transition)'
                              )
                        napkin[i] = rest
                        idx = add_mod(idx, 1)
                else:
                    napkin[idx], = self.kill_strings(tr_state.children, m)
                    idx = add_mod(idx, 1)
            if len(napkin) != self._tbl.trlen:
                raise ValueErr(
                  (meta.line, children[0].meta.column, children[-1].meta.end_column),
                  f"Bad transition length for {self.directives['neighborhood']} neighborhood "
                  f'(expected {2+self._tbl.trlen} terms, got {2+len(napkin)})'
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
          'cdir': self._tbl.check_cdir(children[0], fix(meta), return_int=False),
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
    def stationary_symmetried_aux(self, meta, symmetries, *auxiliaries):
        self._tbl.add_sym_type(symmetries)
        symmetries = symutils.get_sym_type(symmetries)
        for aux in auxiliaries:
            aux.symmetries = symmetries
            aux.stationary = True
        return auxiliaries
    
    @inline
    def aux_bare(self, meta, cdir_info, val):
        cdir_to, delay = cdir_info['cdir'], cdir_info['delay']
        return Auxiliary(self._tbl, cdir_to, delay, self.kill_string(val, meta), context=meta)
    
    @inline
    def aux_bind_self(self, meta, cdir_info, cdir_from):
        cdir_from = self._tbl.check_cdir(cdir_from, fix(meta), return_int=False, enforce_int=True)
        cdir_to, delay = cdir_info['cdir'], cdir_info['delay']
        return Auxiliary(self._tbl, cdir_to, delay, Binding(cdir_from, context=(meta[0], meta[1]+len(cdir_to), meta[2])), context=meta)
    
    @inline
    def aux_map_self(self, meta, cdir_info, val):
        cdir_to, delay = cdir_info['cdir'], cdir_info['delay']
        return Auxiliary(self._tbl, cdir_to, delay, Mapping(cdir_to, self.kill_string(val, meta), context=(meta[0], meta[1]+len(cdir_to), meta[2])), context=meta)
    
    @inline
    def aux_map_other(self, meta, cdir_info, cdir_from, val):
        cdir_to, delay = cdir_info['cdir'], cdir_info['delay']
        cdir_from = self._tbl.check_cdir(cdir_from, (meta[0], meta[1] + cdir_info['meta'][1] + 1, len(cdir_from)), return_int=False, enforce_int=True)
        return Auxiliary(self._tbl, cdir_to, delay, Mapping(cdir_from, self.kill_string(val, meta), context=(meta[0], meta[1]+len(cdir_to), meta[2])), context=meta)
    
    @inline
    def range(self, meta, start, stop):
        return StateList(range(int(start), 1+int(stop)))
    
    @inline
    def range_step(self, meta, step, start, stop):
        return StateList(range(int(start), 1+int(stop), int(step)))
    
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
        return StateList(i for i in self.kill_string(minuend, meta) if i not in self.kill_string(subtrhnd, meta, li=True))
    
    @inline
    def noref_live_except(self, meta, subtrhnd):
        return self.noref_subt(('live', subtrhnd), meta)
    
    @inline
    def noref_all_except(self, meta, subtrhnd):
        return self.noref_subt(('any', subtrhnd), meta)
    
    @inline
    def noref_rot_right(self, meta, statelist, amt):
        amt = int(amt) % len(statelist)
        statelist = self.kill_string(statelist, meta)
        return statelist[-amt:] + statelist[:-amt]
    
    @inline
    def noref_rot_left(self, meta, statelist, amt):
        amt = int(amt) % len(statelist)
        statelist = self.kill_string(statelist, meta)
        return statelist[amt:] + statelist[:amt]
    
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
    def rot_right(self, meta, var, amt):
        return RotateRight(self.kill_string(var, meta), int(amt), context=meta)
    
    @inline
    def rot_left(self, meta, var, amt):
        return RotateLeft(self.kill_string(var, meta), int(amt), context=meta)
    
    @inline
    def live_except(self, meta, subtrhnd):
        return self.subt(('live', subtrhnd), meta)
    
    @inline
    def all_except(self, meta, subtrhnd):
        return self.subt(('any', subtrhnd), meta)
    
    @inline
    def inline_binding(self, meta, val):
        return InlineBinding(self.kill_string(val, meta), self._tbl, context=meta)
    
    @inline
    def binding(self, meta, cdir):
        if cdir in ('FG', 'BG'):
            return self.rs_binding((cdir,), meta)
        return Binding(self._tbl.check_cdir(cdir, meta, return_int=False, enforce_int=True), context=meta)
    
    @inline
    def mapping(self, meta, cdir, map_to):
        if cdir in ('FG', 'BG'):
            return self.rs_mapping((cdir, map_to), meta)
        return Mapping(self._tbl.check_cdir(cdir, meta, return_int=False, enforce_int=True), self.kill_string(map_to, meta), context=meta)
    
    @inline
    def rs_binding(self, meta, idx):
        # No longer part of the grammar, but
        # should only be called when idx in {'FG', 'BG'}.
        #if idx == '0':
        #    return Binding('0', context=meta)
        return InlineRulestringBinding(str(idx), context=meta)
    
    @inline
    def rs_mapping(self, meta, idx, map_to):
        # No longer part of the grammar, but
        # should only be called when idx in {'FG', 'BG'}.
        #if idx == '0':
        #    return Mapping('0', self.kill_string(map_to, meta), context=meta)
        return InlineRulestringMapping(str(idx), self.kill_string(map_to, meta), context=meta)
    
    @inline
    def hensel_rulestring(self, meta, rulestring):
        nbhds = nbhoods.validate_hensel(rulestring)
        if not nbhds:
            raise SyntaxErr(meta, 'Invalid Hensel-notation rulestring')
        if not nbhoods.check_hensel_within(rulestring, self._tbl.neighborhood, rulestring_nbhds=nbhds):
            raise SyntaxErr(
              meta,
              f"Hensel-notation rulestring exceeds neighborhood {self.directives['neighborhood']!r}; "
              f'in particular, {nbhoods.find_invalids(nbhds, self._tbl.neighborhood)!r}'
              )
        return nbhds
    
    def _get_getter(self, val, kind):
        def get_val(*_):
            return val
        
        if isinstance(val, InlineBinding):
            used = set()
            def get_val(nb_count, letter, meta):
                if (nb_count, letter) not in used:
                    val.reset()
                    used.add((nb_count, letter))
                if val.bind is None:
                    val.set(self._tbl.neighborhood[get_rs_cdir(val, nb_count, letter, meta, idx=kind.upper())])
                return val.give()
        
        if isinstance(val, (InlineRulestringBinding, InlineRulestringMapping)):
            def get_val(*args):
                return resolve_rs_ref(val, *args)
        
        if isinstance(val, StateList):
            if any(isinstance(i, (InlineRulestringBinding, InlineRulestringMapping)) for i in val):
                def get_val(*args):
                    return val.__class__((
                      resolve_rs_ref(i, *args)
                      if isinstance(i, (InlineRulestringBinding, InlineRulestringMapping))
                      else i
                      for i in val
                      ),
                    context=val.ctx)
        
        return get_val
    
    @inline
    def rulestring_tr(self, meta, initial, rulestring_nbhds, foreground, background, resultant):
        initial = self.kill_string(initial, meta)
        resultant = self.kill_string(resultant, meta)
        
        fg = self.kill_string(foreground, meta)
        bg = self.kill_string(background, meta)
        if isinstance(foreground, StateList):
            self.vars[self._tbl.new_varname(-1)] = foreground
        if isinstance(background, StateList):
            self.vars[self._tbl.new_varname(-1)] = background
        
        r4r_nbhds, permute_nbhds = {}, set()
        for nb_count, letters in rulestring_nbhds.items():
            if len(letters) == len(nbhoods.R4R_NBHDS[nb_count]):
                permute_nbhds.add(nb_count)
            else:
                r4r_nbhds[nb_count] = letters
        
        if permute_nbhds:
            self._tbl.add_sym_type('permute')
        if r4r_nbhds:
            self._tbl.add_sym_type('rotate4reflect')
        
        get_fg, get_bg = self._get_getter(fg, 'fg'), self._get_getter(bg, 'bg')
        ret = [
          TransitionGroup(
            self._tbl,
            resolve_rs_ref(initial, nb_count, letter, meta),
            {
              num: get_fg(nb_count, letter, meta)
              # XXX: probably suboptimal performance b/c [dot attr access] -> [getitem] -> [getitem]
              if cdir in nbhoods.R4R_NBHDS[nb_count][letter]
              else get_bg(nb_count, letter, meta)
              for cdir, num in self._tbl.neighborhood.items()
            },
            resolve_rs_ref(resultant, nb_count, letter, meta),
            context=meta, symmetries=ROTATE_4_REFLECT
            )
          for nb_count, letters in r4r_nbhds.items()
          for letter in letters
        ]
        ret.extend(
          TransitionGroup(
            self._tbl,
            resolve_rs_ref(initial, nb_count, None, meta),
            {
              num: get_fg(nb_count, None, meta)
              if num <= nb_count
              else get_bg(nb_count, None, meta)
              for num in self._tbl.neighborhood.values()
            },
            resolve_rs_ref(resultant, nb_count, None, meta),
            context=meta, symmetries=PERMUTE
            )
          for nb_count in map(int, permute_nbhds)
          )
        return ret
    
    @inline
    def rulestring_transition(self, meta, trs, aux_first=None, aux_second=None):
        ret = []
        if aux_first is not None and aux_first.meta == 'normal':
            # then, as above, aux_second is either hoisted or nonexistent
            # but in the interest of not doing this conditional every iteration
            # of the below loop, we'll just switch them around here
            aux_second, aux_first = aux_first, aux_second
        for tr in trs:
            ret.extend(chain(tr.apply_aux(aux_first), tr.expand(), tr.apply_aux(aux_second)))
        return ret
    
    def special_rulestring_tr(self, children, meta):
        raise UnsupportedFeature(fix(meta), 'Hensel-rulestring transition napkins with modifiers are currently not supported')
