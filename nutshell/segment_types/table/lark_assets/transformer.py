from functools import wraps

import bidict
import lark
from lark import Transformer, Tree, Discard, v_args

from nutshell.common.errors import *
from ._classes import *
from .._classes import VarName

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
    
    @inline
    def print_var(self, meta, var):
        if not isinstance(var, (tuple, Variable)):
            var = self.vars[var]
        print(var)
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
        if not isinstance(var, tuple):
            var = self.vars[var]
        return self.noref_var([num], meta) * len(var)
    
    @inline
    def noref_repeat_var(self, meta, var, num):
        if not isinstance(var, tuple):
            var = self.vars[var]
        return var * int(num)
    
    @inline
    def noref_subt(self, meta, minuend, subtrhnd):
        if isinstance(minuend, str):
            minuend = self.vars[minuend]
        if isinstance(subtrhnd, str):
            subtrhnd = [int(subtrhnd)] if subtrhnd.isdigit() else self.vars[subtrhnd]
        return tuple(i for i in minuend if i not in subtrhnd)
    
    @inline
    def noref_live_except(self, meta, subtrhnd):
        return self.noref_subt(('live', subtrhnd), meta)
    
    @inline
    def noref_all_except(self, meta, subtrhnd):
        return self.noref_subt(('any', subtrhnd), meta)
    
    def main(self, children, meta):
        idx = 0
        napkin = {}
        initial, resultant = children.pop(0), children.pop(-1)
        add_mod = partial(_add_mod, self._tbl.trlen)
        offset_initial = False  # whether it starts on a compass dir other than the "first"
        
        for tr_state in children:
            first, *rest = tr_state.children
            first_data = getattr(first, 'data', None)
            if first_data == 'cdir':
                cdir = first.children[0]
                if cdir not in self._tbl.neighborhood:
                    raise SyntaxErr(
                      fix(first.meta),
                      f"Compass direction {cdir} does not exist in {self.directives['neighborhood']} neighborhood"
                      )
                
                napkin[cdir], = rest
                if self._tbl.neighborhood[cdir] != idx:
                    if idx == 0:
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
                if a not in self._tbl.neighborhood:
                    raise SyntaxErr(
                      (first.meta.line, first.meta.column, len(a) + first.meta.column),
                      f"Compass direction {a} does not exist in {self.directives['neighborhood']} neighborhood"
                      )
                if b not in self._tbl.neighborhood:
                    raise SyntaxErr(
                      (first.meta.line, first.meta.end_column - len(b), first.meta.end_column),
                      f"Compass direction {b} does not exist in {self.directives['neighborhood']} neighborhood"
                      )
                
                crange = range(self._tbl.neighborhood[a], 1+self._tbl.neighborhood[b])
                if len(crange) == 1 or not crange and not offset_initial:
                    raise ValueErr(
                      fix(first.meta),
                      f'Invalid compass-direction range ({b} does not follow {a} going clockwise)'
                      )
                
                if not crange and offset_initial:
                    crange = *range(self._tbl.neighborhood[a], 1+self._tbl.trlen), *range(1, 1+self._tbl.neighborhood[b])
                
                if idx != crange[0]:
                    if idx == 0:
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
                          (first.meta.line, first.meta.end_column - len(b) - 2, first.meta.end_column),
                          'Compass-direction range'
                          )
                    napkin[i], = rest
                    idx = add_mod(idx, 1)
            else:
                napkin[idx] = tr_state.children
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
        for val in children:
            if isinstance(val, (list, tuple)):
                ret.extend(val)
            elif isinstance(val, int) or val.isdigit():
                ret.append(int(val))
            elif val in self.vars:
                ret.extend(self.vars[val])
            else:
                raise NutshellException(fix(meta), val)
        return Variable(self._tbl, ret, context=fix(meta))
    
    def var(self, children, meta):
        ret = []
        for val in children:
            if isinstance(val, int) or isinstance(val, str) and val.isdigit():
                ret.append(int(val))
            else:
                ret.append(val)
        return Variable(self._tbl, ret, context=fix(meta))
    
    @inline
    def repeat_int(self, meta, a, b):
        if isinstance(a, str):
            a = int(a)
        return RepeatInt(a, int(b), context=fix(meta))
    
    @inline
    def int_to_var_length(self, meta, num, var):
        if isinstance(num, str):
            num = int(num)
        return IntToVarLength(num, var, context=fix(meta))
    
    @inline
    def repeat_var(self, meta, var, num):
        return RepeatVar(var, int(num), context=fix(meta))
    
    @inline
    def subt(self, meta, var, subtrhnd):
        # Really this only works because Variable does the "if isinstance(t, str)" thing
        # It also means that the isinstance(..., int) check in Subt.within() won't ever be triggered
        return Subt(var, Variable(self._tbl, subtrhnd, context=fix(meta)))
    
    def mapping(self, children, meta):
        return Mapping(self._tbl, *children, context=fix(meta))
    
    def binding(self, children, meta):
        return Binding(*children, context=fix(meta))
