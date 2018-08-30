from contextlib import suppress
from functools import partial
from itertools import count

from ._exceptions import Reshape, Unpack
from nutshell.common.errors import *


class TransitionGroup:
    def __init__(self, tbl, initial, napkin, resultant, *, context=None):
        self.ctx = context
        self.tbl = tbl
        self.symmetries = tbl.symmetries
        nbhd = tbl.neighborhood.inv
        self._tr_dict = {'0': initial, **{nbhd[k]: v for k, v in napkin.items()}}
        self._tr = [initial, *map(napkin.get, range(1, 1+len(napkin))), resultant]
        self._n = napkin
    
    def __getitem__(self, item):
        if isinstance(item, str):
            return self._tr_dict[item]
        return self._tr[item]
    
    @classmethod
    def from_seq(cls, tbl, tr, **kw):
        return cls(tbl, tr[0], dict(enumerate(tr[1:-1], 1)), tr[-1], **kw)
    
    def expand(self, ptcds=None):
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
                      TransitionGroup.from_seq(self.tbl, tr, context=self.ctx).expand()
                      for tr in
                      ([*self[:idx], val, *self[1+idx:]] for val in var.within(self))
                      )
                    break
            else:
                current.append(val)
        else:
            return Transition(current, self.tbl, self.symmetries, ptcds, context=self.ctx)
        return trs


class Transition:
    def __init__(self, tr, tbl, symmetries, ptcds, *, context):
        self.ctx = context
        self.initial, *self.napkin, self.resultant = tr
        nbhd = tbl.neighborhood.inv
        self._tr_dict = {'0': self.initial, **{nbhd[k]: v for k, v in self.napkin.items()}}
        self.tr = tr
        self.symmetries = symmetries
        self.ptcds = ptcds
    
    def __repr__(self):
        return f'T{self.tr!r}'
    
    def __iter__(self):
        return self.tr.__iter__()
    
    def __getitem__(self, item):
        if isinstance(item, str):
            return self._tr_dict.__getitem__(item)
        return self.tr.__getitem__(item)

    def apply_ptcds(self):
        return [tr for i in self.ptcds for tr in i.within(self)]


class Expandable:
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
            return val.value
        return val


class Mapping(Reference):
    def __init__(self, cdir, map_to, **kw):
        super().__init__(cdir, **kw)
        self.map_to = Variable(map_to)
        if len(self.map_to) == 1:
            raise ValueErr(
              self.ctx,
              'Mapping to single cellstate'
              )
    
    def within(self, tr):
        val = tr[self.cdir]
        if isinstance(val, VarValue):
            map_to = self.map_to.within(tr)
            if val.index >= len(map_to) - 1 and map_to[-1].value is Ellipsis:
                return map_to[-2]
            try:
                return map_to[val.index]
            except IndexError:
                if isinstance(val, VarValue):
                    val = val.parent
                raise ValueErr(
                  self.ctx,
                  f'Variable {val!r} mapped to smaller variable {self.map_to}. '
                  'Maybe add a ... to fill the latter out?'
                  )
        if isinstance(val, Reference):
            if val.cdir == self.cdir:
                return 
            return val.within(tr)
        if isinstance(val, int):
            raise ValueErr(self.ctx, 'Mapping to single cellstate')
        if isinstance(val, Variable):
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
    def __init__(self, t, **kw):
        super().__init__(**kw)
        self._tuple = (t,) if isinstance(t, int) else self.unpack_varnames_only(t)
        self._set = set(self._tuple)
    
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
        return f"{''.join(filter(str.isupper, self.__class__.__name__))}{self._tuple.__repr__()}"
    
    def __mul__(self, other):
        if isinstance(other, int):
            return self.__class__(self._tuple*other)
        return NotImplemented
    
    def __rmul__(self, other):
        if isinstance(other, int):
            return self.__class__([other]*len(self._tuple))
        return NotImplemented
    
    def __sub__(self, other):
        if type(other) is type(self):
            return self.__class__([i for i in self if i not in other])
        if isinstance(other, int):
            return self.__class__([i for i in self if i != other])
        return NotImplemented
    
    def within(self, tr):
        return TetheredVar(self.unpack(self._tuple, tr, count()))
    
    def unpack(self, t, tr, counter, start=None, new=None):
        if new is None:
            new = []
        for val in t:
            try:
                new.append(VarValue(next(counter) if start is None else start, val, tr, self))
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


class TetheredVar(Variable):  # Tethered == bound to a transition
    def __init__(self, t, **kw):
        Expandable.__init__(self, **kw)
        self._tuple = (t,) if isinstance(t, int) else self.unpack_varnames_only(t)
        self._set = {i.value for i in self._tuple}
        self.tag = None
        self.bound = False
    
    def __eq__(self, other):
        if self.bound:
            return super().__eq__(other) and self.tag == getattr(other, 'tag', None)
        return super().__eq__(other)
    
    def __hash__(self):
        if self.bound:
            return hash((*self._tuple, self.tag))
        return super().__hash__()


class VarValue:
    SPECIALS = {'_': None, '...': ...}
    
    def __init__(self, index, value, tr, parent=None):
        self.parent = parent
        self.index = index
        self.value = value
        if value in self.SPECIALS:
            self.value = self.SPECIALS[value]
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


class PTCD:
    def __init__(self, tbl, initial_cdir, resultant, *, context):
        self.ctx = context
        self.tbl = tbl
        self.initial_cdir = initial_cdir
        self.resultant = resultant
        self.within = {
          int: self.from_int,
          Binding: self.from_binding,
          Mapping: self.from_mapping
        }[type(resultant)]
    
    def _make_tr(self, tr, resultant):
        new_tr = [tr[self.initial_cdir], *[self.tbl.vars['any']]*self.tbl.trlen, resultant]
        orig = Coord.from_name(self.initial_cdir, self.tbl)
        # Adjacent cells to original cell (diagonal to current)
        with suppress(KeyError):
            new_tr[orig.idx] = tr[0]
        with suppress(KeyError):
            new_tr[orig.cw.idx] = tr[orig.cw.toward(self.initial_cdir).idx]
        with suppress(KeyError):
            new_tr[orig.ccw.idx] = tr[orig.ccw.toward(self.initial_cdir).idx]
        # If we're orthogonal to orig, we have to count for the cells adjacent to us too
        if not orig.diagonal():
            with suppress(KeyError):
                new_tr[orig.cw(2).idx] = tr[orig.cw(3).idx]
            with suppress(KeyError):
                new_tr[orig.ccw(2).idx] = tr[orig.ccw(3).idx]
        return new_tr
    
    def __make_transition_old(self, tr, source_cd: str, cd_to: str, initial, result):
        ...
        # # Otherwise, we have to fiddle with the values at the initial and new_relative indices
        # with suppress(KeyError):
        #     new_tr[0] = tr[cur.idx]
        # new_relative = orig if cd_to == '0' else orig.toward(cd_to)  # position of "copy_to" cell relative to current
        # if new_relative.center():
        #     return new_tr
        # with suppress(KeyError):
        #     new_tr[new_relative.idx] = initial
        # return new_tr
    
    def from_int(self, tr):
        return [self._make_tr(tr, self.resultant)]
    
    def from_binding(self, tr):
        return [self._make_tr(tr, val) for val in self.resultant.within(tr)]
    
    def from_mapping(self, tr):
        ...  # how to handle Reshape?


class _CoordOutOfBoundsError(Exception):
    """
    Raised when |one of a coord's values| > 1
    """


class CoordOutOfBounds(ValueErr):
    """
    Raised when |one of a coord's values| > 1
    """


class Coord(tuple):
    """
    Represents a 'unit coordinate' of a cell.
    """
    _DIRS = ('N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW')
    _OFFSETS = {
       'N': (0, 1),
      'NE': (1, 1),
       'E': (1, 0),
      'SE': (1, -1),
       'S': (0, -1),
      'SW': (-1, -1),
       'W': (-1, 0),
      'NW': (-1, 1)
      }
    _DIRMAP = dict(zip(_DIRS, range(8)))
    _NAMES = {v: k for k, v in _OFFSETS.items()}
    
    def __new__(cls, it, tbl=None):
        return super().__new__(tuple, it)
    
    def __init__(self, _, tbl=None):
        self.tbl = tbl
        if not all(-2 < i < 2 for i in self):
            raise _CoordOutOfBoundsError(self)
    
    def __repr__(self):
        return f'Coord({tuple(self)!r})'
    
    @classmethod
    def from_name(cls, cdir, tbl=None):
        return cls(cls._OFFSETS[cdir], tbl)
    
    @property
    def name(self):
        return self._NAMES[self]
    
    @property
    def idx(self):
        return self.tbl.neighborhood[self._NAMES[self]]
    
    @property
    def inv(self):
        return Coord((-i for i in self), self.tbl)
    
    @property
    def cw(self):
        idx = 1 + self._DIRMAP[self.name]
        return _MaybeCallableCW(self._OFFSETS[self._DIRS[idx % 8]], self.tbl)
    
    @property
    def ccw(self):
        idx = self._DIRMAP[self.name]
        return _MaybeCallableCCW(self._OFFSETS[self._DIRS[idx - 1]], self.tbl)
    
    def diagonal(self):
        return all(self)
    
    def center(self):
        return self == (0, 0)
    
    def toward(self, cd):
        return self.move(*self._OFFSETS[cd.upper()])
    
    def move(self, x=0, y=0):
        return Coord((x+self[0], y+self[1]))


class _MaybeCallableCW(Coord):
    """
    Allows Coord.cw.cw.cw.cw to be replaced by Coord.cw(4), and so on.
    (The former will still work, however.)
    """
    def __call__(self, num):
        return Coord(self.cw(num-1) if num > 1 else self)


class _MaybeCallableCCW(Coord):
    """
    Ditto above, but counterclockwise.
    """
    def __call__(self, num):
        return Coord(self.ccw(num-1) if num > 1 else self)