from functools import partial
from itertools import count

from ._exceptions import Reshape, Special, Unpack
from nutshell.common.errors import *


class TransitionGroup:
    def __init__(self, tbl, initial, napkin, resultant, *, context=None):
        self.ctx = context
        self.tbl = tbl
        self.symmetries = tbl.symmetries
        nbhd = tbl.neighborhood.inv
        self._tr_dict = {'0': initial, **{nbhd[k]: v for k, v in napkin.items()}}
        self._tr = [initial, *map(napkin.get, range(1, 1+len(napkin))), resultant]
        self.gollies = self.convert()
    
    def __getitem__(self, item):
        if isinstance(item, str):
            return self._tr_dict[item]
        return self._tr[item]
    
    @classmethod
    def from_seq(cls, tbl, tr, **kw):
        return cls(tbl, tr[0], dict(enumerate(tr[1:-1], 1)), tr[-1], **kw)
    
    def _extract_trs(self, trs):
        'print(trs)'
    
    def convert(self):
        trs = []
        current = []
        for val in self._tr:
            if isinstance(val, Expandable):
                try:
                    current.append(val.within(self))
                except Reshape as e:
                    var = self[e.cdir]
                    idx = e.cdir != '0' and self.tbl.neighborhood[e.cdir]
                    trs.extend(
                      TransitionGroup.from_seq(self.tbl, tr, context=self.ctx).gollies
                      for tr in
                      ([*self[:idx], val, *self[1+idx:]] for val in var.within(self))
                      )
                    break
            else:
                current.append(val)
        else:
            return current
        self._extract_trs(trs)
        return trs


class Expandable:  # should be an ABC but eh
    def __init__(self, *, context=None):
        self.ctx = context


class Reference(Expandable):
    def __init__(self, cdir, **kw):
        super().__init__(**kw)
        self.cdir = str(cdir)


class Binding(Reference):
    def within(self, tr):
        # Since bindings can be their own entire transition state,
        # in which case they can be expressed in Golly with simply
        # a variable name rather than a repeated collection of transitions,
        # we have no reason to raise Reshape here.
        # So in the case that the binding is actually an operand of * or -, 
        # those operators must raise Reshape themselves.
        val = tr[self.cdir]
        if isinstance(val, VarValue):
            val = val.value
        return val


class Mapping(Reference):
    def __init__(self, tbl, cdir, map_to, **kw):
        super().__init__(cdir, **kw)
        self.map_to = Variable(tbl, map_to)
        if len(self.map_to) == 1:
            raise ValueErr(
              self.ctx,
              'Mapping to single cellstate'
              )
    
    def within(self, tr):
        val = tr[self.cdir]
        if isinstance(val, VarValue):
            map_to = self.map_to.within(tr)
            if val.index >= len(map_to) - 1 and map_to[-1] is Ellipsis:
                return map_to[-2]
            try:
                return map_to[val.index]
            except IndexError:
                if isinstance(val, VarValue):
                    val = val.parent
                raise ValueErr(
                  self.ctx,
                  f'Variable {val!r} mapped to smaller variable {self.map_to._tuple}. '
                  'Maybe add a ... to fill the latter out?'
                  )
        if isinstance(val, Reference):
            if val.cdir == self.cdir:
                return 
            return val.within(tr)
        if isinstance(val, int) or isinstance(val, str) and val.isdigit():
            raise ValueErr(self.ctx, 'Mapping to single cellstate')
        if isinstance(val, (Variable, str)):
            raise Reshape(self.cdir)
        raise ValueErr(self.ctx, f'Unknown map-from value: {val}')


class Operation(Expandable):
    def __init__(self, a, b, **kw):
        super().__init__(**kw)
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
        if isinstance(self.b, int):
            return self.a.within(tr) - self.b
        if isinstance(self.b, Reference):
            if not isinstance(tr[self.b.cdir], VarValue):
                raise Reshape(self.b.cdir)
        return self.a.within(tr) - self.b.within(tr)


class Variable(Expandable):
    def __init__(self, tbl, t, **kw):
        self._tbl = tbl
        self._tuple = (t,) if isinstance(t, int) else self.unpack_varnames_only(t)
        try:
            self._set = {i.value for i in self._tuple}
        except AttributeError:
            self._set = set(self._tuple)
        super().__init__(**kw)
    
    def __contains__(self, item):
        if isinstance(item, VarValue):
            return self._set.__contains__(item.value)    
        return self._set.__contains__(item)
    
    def __eq__(self, other):
        return self._tuple.__eq__(other)
    
    def __getitem__(self, item):
        return self._tuple.__getitem__(item)
    
    def __hash__(self):
        return self._tuple.__hash__()
    
    def __iter__(self):
        return self._tuple.__iter__()
    
    def __len__(self):
        return self._tuple.__len__()
    
    def __repr__(self):
        return f'Variable{self._tuple.__repr__()}'
    
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
        return Variable(self._tbl, self.unpack(self._tuple, tr, count()))
    
    def unpack(self, t, tr, counter, start=None, new=None):
        if new is None:
            new = []
        for val in t:
            try:
                new.append(VarValue(next(counter) if start is None else start, val, tr, self))
            except Special as e:
                new.append(e.value)
            except Unpack as e:
                self.unpack(e.val, tr, counter, e.idx, new)
            if start is not None:
                start = None
        return new
    
    def unpack_varnames_only(self, t, new=None):
        if new is None:
            new = []
        for val in t:
            if isinstance(val, Variable):
                self.unpack_varnames_only(val, new)
            else:
                new.append(val)
        return tuple(new)


class VarValue:
    SPECIALS = {'_': None, '...': Ellipsis}

    def __init__(self, index, value, tr, parent=None):
        self.parent=parent
        self.index = index
        self.value = value
        if value in self.SPECIALS:
            raise Special(self.SPECIALS[value])
        elif isinstance(value, Reference):
            self.value = value.within(tr)
        elif isinstance(value, VarValue):
            self.value = value.value
        elif isinstance(value, (Operation, Variable)):
            raise Unpack(index, value.within(tr))
    
    def __rmul__(self, other):
        return other * self.value
    
    def __rsub__(self, other):
        return other - self.value
    
    def __repr__(self):
        return f'{self.value!r}<{self.index}>'
    
    def __str__(self):
        return str(self.value)

