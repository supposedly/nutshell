from functools import wraps

import bidict
import lark
from lark import Transformer, Tree, Discard, v_args

from nutshell.common.errors import *
from ._classes import *
from .._classes import VarName

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
    
    @inline
    def print_var(self, meta, var):
        print(self.kill_string(var, meta))
        raise Discard
    
    @inline
    def directive(self, meta, name, val):
        self.directives[str(name)] = val.replace(' ', '')
        if name == 'states':
            self._tbl.n_states = val.replace(' ', '')
        raise Discard
    
    @inline
    def var_decl(self, meta, name, var):
        self.vars[VarName(name)] = self.noref_var(var, meta)
        raise Discard
    
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
    
    def main(self, children, meta):
        idx = 1
        napkin = {}
        initial, resultant = children.pop(0), children.pop(-1)
        try:
            initial = self.kill_string(initial, meta.line)
        except ReferenceErr as e:
            raise ReferenceErr((meta.line, meta.column, meta.column + len(str(initial))), e.msg)
        try:
            resultant = self.kill_string(resultant, meta.line)
        except ReferenceErr as e:
            raise ReferenceErr((meta.line, meta.end_column - len(str(resultant)), meta.end_column), e.msg)
        add_mod = partial(_add_mod, self._tbl.trlen)
        offset_initial = False  # whether it starts on a compass dir other than the "first"
        
        for tr_state in children:
            m = fix(tr_state.meta)
            first, *rest = tr_state.children
            first_data = getattr(first, 'data', None)
            rest = self.kill_strings(rest, m)
            
            if first_data == 'cdir':
                cdir = first.children[0]
                try:                
                    napkin[self._tbl.neighborhood[cdir]], = rest
                except KeyError:
                    raise SyntaxErr(
                      fix(first.meta),
                      f"Compass direction {cdir} does not exist in {self.directives['neighborhood']} neighborhood"
                      )
                if self._tbl.neighborhood[cdir] != idx:
                    if idx == 1:
                        idx = self._tbl.neighborhood[cdir]
                        offset_initial = True
                    else:
                        raise SyntaxErr(
                          fix(first.meta),
                          'Out-of-sequence compass direction '
                          f'(expected {self._tbl.neighborhood.inv[idx]}, got {cdir})'
                          )
                idx = add_mod(idx, 1)
            elif first_data == 'crange':
                a, b = first.children
                try:
                    crange = range(self._tbl.neighborhood[a], 1+self._tbl.neighborhood[b])
                except KeyError:
                    if a not in self._tbl.neighborhood:
                        raise SyntaxErr(
                          (first.meta.line, first.meta.column, len(a) + first.meta.column),
                          f"Compass direction {a} does not exist in {self.directives['neighborhood']} neighborhood"
                          )
                    raise SyntaxErr(
                      (first.meta.line, first.meta.end_column - len(b), first.meta.end_column),
                      f"Compass direction {b} does not exist in {self.directives['neighborhood']} neighborhood"
                      )
                if len(crange) == 1 or not crange and not offset_initial:
                    raise ValueErr(
                      fix(first.meta),
                      f'Invalid compass-direction range ({b} does not follow {a} going clockwise)'
                      )
                
                if not crange and offset_initial:
                    crange = *range(self._tbl.neighborhood[a], 1+self._tbl.trlen), *range(1, 1+self._tbl.neighborhood[b])
                
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
                napkin[idx] = self.kill_strings(tr_state.children, m)
                idx = add_mod(idx, 1)
        if len(napkin) != self._tbl.trlen:
            raise ValueErr(
              (meta.line, children[0].meta.column, children[-1].meta.end_column),
              f"Bad transition length for {self.directives['neighborhood']!r} neighborhood "
              f'(expected {self._tbl.trlen} napkin states, got {len(napkin)})'
              )
        return TransitionGroup(self._tbl, initial, napkin, resultant, context=fix(meta))
    
    def noref_var(self, children, meta):
        ret = []
        m = fix(meta)
        for val in map(self.kill_string, children, [m]*len(children)):
            if isinstance(val, (tuple, Variable)):
                ret.extend(val)
            elif isinstance(val, int):
                ret.append(int(val))
            else:
                raise NutshellException(fix(meta), val)
        return Variable(self._tbl, ret, context=fix(meta))
    
    def var(self, children, meta):
        m = fix(meta)
        return Variable(self._tbl, self.kill_strings(children, m), context=m)
    
    @inline
    def repeat_int(self, meta, a, b):
        return RepeatInt(self.kill_string(a, meta), int(b), context=meta)
    
    @inline
    def int_to_var_length(self, meta, num, var):
        return IntToVarLength(self.kill_string(num, meta), var, context=meta)
    
    @inline
    def repeat_var(self, meta, var, num):
        return RepeatVar(self.kill_string(var, meta), int(num), context=meta)
    
    @inline
    def subt(self, meta, var, subtrhnd):
        # Really this only works because Variable does the "if isinstance(t, str)" thing
        # It also means that the isinstance(..., int) check in Subt.within() won't ever be triggered
        return Subt(self.kill_string(var, meta), Variable(self._tbl, self.kill_string(subtrhnd, meta), context=meta))
    
    @inline
    def mapping(self, meta, cdir, map_to):
        return Mapping(self._tbl, cdir, self.kill_string(map_to, meta), context=meta)
    
    def binding(self, children, meta):
        m = fix(meta)
        return Binding(*children, context=m)
