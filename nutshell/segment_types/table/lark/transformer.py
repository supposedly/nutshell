from itertools import count
from functools import wraps

from lark import Transformer, Tree, Discard, v_args

from .._classes import SpecialVar


def inline(func):
    @wraps(func)
    def wrapper(self, children, meta):
        return func(self, meta, *children)
    return wrapper


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
        if not isinstance(var, tuple):
            var = self.vars[var]
        print(var)
        raise Discard
    
    @inline
    def directive(self, meta, name, val):
        self.directives[str(name)] = val.replace(' ', '')
        if name == 'states':
            self._tbl.vars['any'] = SpecialVar()
        raise Discard
    
    @inline
    def var_decl(self, meta, name, var):
        self.vars[str(name)] = self.noref_var(var, meta)
        raise Discard
    
    @inline
    def range(self, meta, start, stop):
        return tuple(range(int(start), 1 + int(stop)))
    
    @inline
    def range_step(self, meta, step, start, stop):
        return tuple(range(int(start), 1 + int(stop), int(step)))
    
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
        if not isinstance(minuend, tuple):
            minuend = self.vars[minuend]
        if not isinstance(subtrhnd, tuple):
            subtrhnd = [int(subtrhnd)] if subtrhnd.isdigit() else self.vars[subtrhnd]
        return tuple(i for i in minuend if i not in subtrhnd)
    
    @inline
    def noref_live_except(self, meta, subtrhnd):
        return self.noref_subt((tuple(range(1, int(self.directives['states']))), subtrhnd), meta)
    
    @inline
    def noref_all_except(self, meta, subtrhnd):
        return self.noref_subt((tuple(range(int(self.directives['states']))), subtrhnd), meta)
    
    def main(self, children, meta):
        initial, resultant = children.pop(0), children.pop(-1)
        napkin = {}
        idx = 0
        for tr_state in children:
            if tr_state.data == 'permute_shorthand':
                ...
                continue
            first, *rest = tr_state.children
            if first.data == 'cdir':
                cdir = first.children[0]
                napkin[cdir] ,= rest
                if self._tbl.neighborhood[cdir] != idx:
                    if idx:
                        raise Exception('bad cdir')
                    else:  # if idx == 0:
                        idx = self._tbl.neighborhood[cdir]
            elif first.data == 'crange':
                crange = range(*map(self._tbl.neighborhood.get, first.children))
                if idx != crange[0]:
                    if idx == 0:
                        idx == crange[0]
                    else:
                        raise Exception('bad group')
                for i in crange:
                    napkin[i] ,= rest
                    idx += 1
            else:
                napkin[idx] = tr_state.children
        if len(napkin) != self._tbl.trlen:
            raise Exception('invalid transition length for neighborhood')
        return TransitionGroup(self._tbl, initial, napkin, resultant)
    
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
                raise Exception(vars(meta), val)
        return Variable(self._tbl, ret)
    
    def var(self, children, meta):
        ret = []
        for val in children:
            if isinstance(val, int) or val.isdigit():
                ret.append(int(val))
            else:
                ret.append(val)
        return Variable(self._tbl, ret)
    
    @inline
    def repeat_int(self, meta, a, b):
        if isinstance(a, str):
            a = int(a)
        return RepeatInt(a, int(b))
    
    @inline
    def int_to_var_length(self, meta, num, var):
        if isinstance(num, str):
            num = int(num)
        return IntToVarLength(num, var)
    
    @inline
    def repeat_var(self, meta, var, num):
        return RepeatVar(var, int(num))
    
    @inline
    def subt(self, meta, var, subtrhnd):
        # Really this only works because Variable does the "if isinstance(t, str)" thing
        # It also means that the isinstance(..., int) check in Subt.within() won't ever be triggered
        return Subt(var, Variable(self._tbl, subtrhnd))
    
    def mapping(self, children, meta):
        return Mapping(self._tbl, *children)
    
    def binding(self, children, meta):
        return Binding(*children)


class Reshape(Exception):
    def __init__(self, cdir):
        self.cdir = cdir


class Unpack(Exception):
    def __init__(self, index, value):
        self.idx = index
        self.val = value


class TransitionGroup:
    def __init__(self, tbl, initial, napkin, resultant):
        self.tbl = tbl
        self.symmetries = tbl.symmetries
        self._tr = [initial, *map(napkin.get, range(len(napkin))), resultant]
        self._tr_dict = {tbl.neighborhood.inv[k]: v for k, v in napkin.items()}
        self.gollies = self.convert()
    
    def __getitem__(self, item):
        if isinstance(item, str):
            return self._tr_dict[item]
        return self._tr[item]
    
    def convert(self):
        trs = []
        current = []
        for val in self._tr:
            if isinstance(val, Expandable):
                try:
                    current.append(val.within(self))
                except Reshape as e:
                    var = self[e.cdir]
                    idx = self.tbl.neighborhood[cdir]
                    trs.extend([*self[:idx], val, *self[idx:]] for val in var)
                    break
        else:
            trs.append(current)
        ## TODO: symmetries?
        ## TODO: ptcds
        return trs


class Expandable:
    pass


class Reference(Expandable):
    pass


class Binding(Reference):
    def __init__(self, cdir):
        self.cdir = str(cdir)
    
    def within(self, tr):
        # Since bindings can be their own entire transition state,
        # in which case they can be expressed in Golly with simply
        # a variable name rather than a repeated collection of transitions,
        # we have no reason to raise Reshape in here.
        # So in the case that the binding is actually an operand of * or -, 
        # those operators must themselves raise Reshape.
        val = tr[self.cdir]
        if isinstance(val, VarValue):
            val = int(val)
        if isinstance(val, (Variable, tuple)):
            return val


class Mapping(Reference):
    def __init__(self, tbl, cdir, map_to):
        self.cdir = str(cdir)
        if isinstance(map_to, str):
            map_to = tbl.vars[map_to]
        self.map_to = map_to
    
    def within(self, tr):
        val = tr[self.cdir]
        if isinstance(val, int):
            raise Exception('map to single cellstate')
        if isinstance(val, Variable):
            raise Reshape(self.cdir)
        if isinstance(val, VarValue):
            return self.map_to[val.index]
        else:
            raise Exception('unknown map-from value', val)


class Operation(Expandable):
    def __init__(self, a, b):
        self.a = a
        self.b = b


class RepeatInt(Operation):
    def within(self, tr):
        if isinstance(self.a, Reference):
            return self.a.within(tr) * self.b
        return self.a * self.b


class IntToVarLength(Operation):
    def within(self, tr):
        if isinstance(self.a, Reference):
            if not isinstance(tr[self.a.cdir], VarValue):
                raise Reshape(self.a.cdir)
            return self.a.within(tr) * self.b.within(tr)
        return self.a * self.b.within(tr)


class RepeatVar(Operation):
    def within(self, tr):
        return self.a.within(tr) * self.b


class Subt(Operation):
    def within(self, tr):
        if isinstance(self.b, Reference):
            if not isinstance(tr[self.b.cdir], VarValue):
                raise Reshape(self.b.cdir)
        if isinstance(self.b, int):
            return self.a.within(tr) - self.b
        return self.a.within(tr) - self.b.within(tr)


class Variable(Expandable):
    def __init__(self, tbl, t):
        self._tbl = tbl
        self._tuple = (str(t),) if isinstance(t, str) else tuple(t)
        self._set = set(self._tuple)
    
    def __contains__(self, item):
        return self._set.__contains__(item)
    
    def __eq__(self, other):
        return self._tuple.__eq__(other)
    
    def __getitem__(self, item):
        return self._tuple.__getitem__(item)
    
    def __hash__(self):
        return self._tuple.__hash__()
    
    def __iter__(self):
        return self._tuple.__iter__()
    
    def __mul__(self, other):
        if isinstance(other, int):
            return Variable(self._tbl, self._tuple * other)
        return NotImplemented
    
    def __rmul__(self, other):
        if isinstance(other, int):
            return Variable(self._tbl, [other] * len(self._tuple))
        return NotImplemented
    
    def __sub__(self, other):
        if type(other) is type(self):
            return Variable(self._tbl, [i for i in self if i not in other])
        if isinstance(other, int):
            return Variable(self._tbl, [i for i in self if i != other])
        return NotImplemented
    
    def within(self, tr):
        new = []
        self.unpack(new, self._tuple, tr, count())
        return Variable(self._tbl, new)
    
    def unpack(self, new, t, tr, counter, start=None):
        for val in t:
            try:
                new.append(VarValue(next(counter) if start is None else start, val, tr))
            except Unpack as e:
                self.unpack(new, e.val, tr, counter, e.idx)
            if start is not None:
                start = None


class VarValue:
    def __init__(self, index, value, tr):
        self.index = index
        self.value = value
        if isinstance(value, str):
            if value.isdigit():
                self.value = int(value)
                return
            raise Unpack(index, tr.tbl.vars[value])
        elif isinstance(value, (Operation, Variable)):
            raise Unpack(index, value.within(tr))
        elif isinstance(value, Reference):
            ref = tr[value.cdir]
            if isinstance(ref, int):
                raise Exception('map to single cellstate')
            if isinstance(ref, (str, Variable)):
                raise Reshape(value.cdir)
            self.value = ref
    
    def __rmul__(self, other):
        return other * self.value
    
    def __rsub__(self, other):
        return other - self.value
    
    def __repr__(self):
        return f'VarValue({self.value})[{self.index}]'
    
    def __str__(self):
        return str(self.value)
