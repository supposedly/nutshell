from contextlib import suppress
from functools import partial
from itertools import count
from collections import Iterable

from ._exceptions import Ellipse, Reshape, Unpack, CoordOutOfBoundsError
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
        self._expanded = None
    
    def __getitem__(self, item):
        if isinstance(item, str):
            return self._tr_dict.__getitem__(item)
        return self._tr.__getitem__(item)
    
    def __iter__(self):
        return self._tr.__iter__()
    
    def __repr__(self):
        return f'TG[{self._tr[0]}, {self._tr[-1]}]'
    
    @classmethod
    def from_seq(cls, tr, tbl, **kw):
        return cls(tbl, tr[0], dict(enumerate(tr[1:-1], 1)), tr[-1], **kw)
    
    def expand(self):
        trs = []
        current = []
        for orig_idx, val in enumerate(self._tr):
            print(self, val)
            if isinstance(val, Expandable):
                try:
                    current.append(val.within(self))
                    print(val.within(self))
                except Ellipse as e:
                    idx = e.cdir != '0' and self.tbl.neighborhood[e.cdir]
                    tethered_var = self[e.cdir].within(self)
                    individuals, combine = tethered_var[:e.split], tethered_var[e.split:]
                    trs.extend(
                      new_tr for tr in
                      ([*self[:idx], value, *self[1+idx:]] for value in individuals)
                      for new_tr in
                      TransitionGroup.from_seq(tr, self.tbl, context=self.ctx).expand()
                      )
                    if combine:
                        tr = self[:]
                        tr[idx], tr[orig_idx] = Variable(combine, e.split, context=tethered_var.ctx), e.val
                        trs.extend(TransitionGroup.from_seq(tr, self.tbl, context=self.ctx).expand())
                    break
                except Reshape as e:
                    idx = e.cdir != '0' and self.tbl.neighborhood[e.cdir]
                    var = self[e.cdir]
                    trs.extend(
                      new_tr for tr in
                      ([*self[:idx], individual, *self[1+idx:]] for individual in var.within(self))
                      for new_tr in
                      TransitionGroup.from_seq(tr, self.tbl, context=self.ctx).expand()
                      )
                    break
            else:
                current.append(val)
        else:
            return [Transition(current, self.tbl, context=self.ctx)]
        return trs
    
    def apply_ptcds(self, ptcds, top=True):
        if ptcds is None:
            return []
        new = []
        for i in ptcds:
            try:
                new.extend(i.within(self))
            except CoordOutOfBoundsError as e:
                raise CoordOutOfBounds(
                  i.ctx,
                  'Auxiliary-transition specifier implies invalid transformation '
                  f'{e.coord.tuple}; the cells in directions {i.initial_cdir} & '
                  f"{i.resultant.cdir} are not in each other's range-1 Moore neighborhood "
                  'and cannot be mapped to one another.'
                  )
            except Ellipse as e:
                var = self[e.cdir].within(self)
                idx = e.cdir != '0' and self.tbl.neighborhood[e.cdir]
                individuals, combine = var[:e.split], var[e.split:]
                if individuals:
                    ptcd = PTCD(self.tbl, i.initial_cdir, None, Mapping(e.cdir, e.map_to, context=i.ctx), context=i.ctx)
                    new.extend(
                      new_tr for tr in
                      ([*self[:idx], val, *self[1+idx:]] for val in individuals if val.value is not None)
                      for new_tr in
                      TransitionGroup.from_seq(tr, self.tbl, context=self.ctx).apply_ptcds([ptcd], False)
                      )
                if combine and e.val is not None:
                    ptcd = PTCD(self.tbl, i.initial_cdir, None, e.val, context=i.ctx)
                    new.extend(TransitionGroup.from_seq(
                      [*self[:idx], Variable(combine, e.split, context=i.ctx), *self[1+idx:]],
                      self.tbl, context=self.ctx
                      ).apply_ptcds([i], False))
            except Reshape as e:
                var = self[e.cdir]
                idx = e.cdir != '0' and self.tbl.neighborhood[e.cdir]
                new.extend(
                  new_tr for tr in
                  ([*self[:idx], val, *self[1+idx:]] for val in var.within(self))
                  for new_tr in
                  TransitionGroup.from_seq(tr, self.tbl, context=self.ctx).apply_ptcds([i], False)
                  )
        return new


class Transition:
    def __init__(self, tr, tbl, *, context):
        self.ctx = context
        self.tr = tr
        self.initial, *self.napkin, self.resultant = tr
        nbhd = tbl.neighborhood.inv
        self._tr_dict = {'0': self.initial, **{nbhd[k]: v for k, v in enumerate(self.napkin, 1)}}
        self.symmetries = tbl.symmetries
        self.tbl = tbl
    
    def __repr__(self):
        return f'T{self.tr!r}'
    
    def __getitem__(self, item):
        if isinstance(item, str):
            return self._tr_dict.__getitem__(item)
        return self.tr.__getitem__(item)
    
    def in_symmetry(self, sym):
        ...


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
        # So in the case that the binding cannot be left on its own, the
        # surrounding environment must raise Reshape on its behalf.
        return tr[self.cdir]
    
    def __repr__(self):
        return f'Binding[{self.cdir}]'


class Mapping(Reference):
    def __init__(self, cdir, map_to, **kw):
        super().__init__(cdir, **kw)
        self.map_to = Variable(map_to)
        if len(self.map_to) == 1:
            raise ValueErr(self.ctx, 'Mapping to a single cellstate')
    
    def __repr__(self):
        return f'Mapping[{self.cdir}: {self.map_to}]'
    
    def within(self, tr):
        val = tr[self.cdir]
        if isinstance(val, VarValue):
            map_to = self.map_to.within(tr)
            # XXX: necessary?
            # if val.index + 1 >= len(map_to) and map_to[-1].value is Ellipsis:
            #    return map_to[-2]
            try:
                return map_to[val.index]
            except IndexError:
                raise ValueErr(
                  self.ctx,
                  f'Variable with length {len(val.parent)} mapped to smaller '
                  f'variable with length {len(self.map_to)}. '
                  'Maybe add a ... to fill the latter out?'
                  )
        if isinstance(val, Reference):
            if val.cdir == self.cdir:
                return 
            return val.within(tr)
        if isinstance(val, int):
            raise ValueErr(self.ctx, 'Mapping from single cellstate')
        if isinstance(val, Variable):
            map_to = self.map_to.within(tr)
            if map_to[-1].value is Ellipsis:
                raise Ellipse(self.cdir, len(map_to)-2, map_to[-2].value, map_to)
            raise Reshape(self.cdir)
        if isinstance(val, Operation):
            return val.within(tr)
        raise ValueErr(self.ctx, f'Unknown map-from value: {val}')


class Operation(Expandable):
    def __init__(self, a, b, **kw):
        super().__init__(**kw)
        self.a = a
        self.b = b
    
    def __repr__(self):
        return f'{self.__class__.__name__}<{self.a}, {self.b}>'


class RepeatInt(Operation):
    def within(self, tr):
        if isinstance(self.a, Reference):
            if not isinstance(tr[self.a.cdir], VarValue):
                raise Reshape(self.a.cdir)
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
    def __init__(self, t, start=0, **kw):
        Expandable.__init__(self, **kw)
        self._tuple = self.unpack_varnames_only(t) if isinstance(t, Iterable) else (t,)
        self._set = set(self._tuple)
        self.start = start
    
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
        return TetheredVar(self.unpack(self._tuple, tr, count(self.start)), self.start, context=self.ctx).within(tr)
    
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
    """
    Contains VarValue objects only.
    """
    def __init__(self, t, start=0, **kw):
        Expandable.__init__(self, **kw)
        self._tuple = self.unpack_varnames_only(t) if isinstance(t, Iterable) else (t,)
        self._set = {i.value for i in self._tuple}
        self.tag = None
        self.bound = False
        self.start = start
    
    def __eq__(self, other):
        if self.bound:
            return super().__eq__(other) and self.tag == getattr(other, 'tag', None)
        return super().__eq__(other)
    
    def __hash__(self):
        if self.bound:
            return hash((*self._tuple, self.tag))
        return super().__hash__()
    
    def within(self, tr):
        return TetheredVar(self.unpack(self._tuple, tr, count(self.start)), context=self.ctx)


class VarValue:
    SPECIALS = {'_': None, '...': ...}
    
    def __init__(self, index, value, tr, parent=None):
        self.parent = parent
        self.index = index
        self.value = self.SPECIALS.get(value, value)
        while isinstance(self.value, VarValue):  # lollll rip
            self.value = self.value.value
        else:
            if isinstance(value, Reference):
                self.value = value.within(tr)
                if isinstance(self.value, Expandable):
                    raise Reshape(value.cdir)
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
    def __init__(self, tbl, initial_cdir, delay, resultant, *, context):
        self.ctx = context
        self.tbl = tbl
        self.initial_cdir = initial_cdir
        self.orig = Coord.from_name(initial_cdir, tbl).inv
        self.resultant = resultant
        if isinstance(resultant, Mapping):
            if resultant.cdir != '0' and not self.orig.toward(resultant.cdir).valid():
                nbhd = tbl.directives['neighborhood']
                raise CoordOutOfBounds(
                  self.ctx,
                  f'Auxiliary-transition specifier implies invalid {nbhd} transformation '
                  f'{self.orig.toward(resultant.cdir).tuple}; the cells in directions '
                  f"{initial_cdir} & {resultant.cdir} are not in each other's range-1 "
                  f'{nbhd} neighborhood and cannot be mapped to one another.'
                  )
        self.hoist = False
        self.within = {
          int: self.from_int,
          Binding: self.from_binding,
          Mapping: self.from_mapping
        }[type(resultant)]
        if delay is not None:
            raise UnsupportedFeature(
              self.ctx,
              f'Delayed auxiliaries (as in "{initial_cdir}+{delay}") are not supported as of yet'
              )
    
    def _make_tr(self, tr, resultant):
        new_tr = [tr[self.initial_cdir], *[self.tbl.vars['any']]*self.tbl.trlen, resultant]
        orig = self.orig
        # Adjacent cells to original cell (diagonal to current)
        with suppress(KeyError):
            new_tr[orig.idx] = tr[0]
        with suppress(KeyError):
            new_tr[orig.cw.idx] = tr[orig.cw.toward(self.initial_cdir).idx]
        with suppress(KeyError):
            new_tr[orig.ccw.idx] = tr[orig.ccw.toward(self.initial_cdir).idx]
        # If we're orthogonal to orig, we have to account for the cells adjacent to us too
        if not orig.diagonal():
            # In this case orig.cw(2).toward(self.initial_cdir) happens to be equivalent
            # to orig.cw(3), which is also shorter, but in the interest of remaining
            # consistent with the general technique I'll write it the longer way
            with suppress(KeyError):
                new_tr[orig.cw(2).idx] = tr[orig.cw(2).toward(self.initial_cdir).idx]
            with suppress(KeyError):
                new_tr[orig.ccw(2).idx] = tr[orig.ccw(2).toward(self.initial_cdir).idx]
        return new_tr
    
    def from_int(self, tr):
        return [self._make_tr(tr, self.resultant)]
    
    def from_binding(self, tr):
        if isinstance(self.resultant.within(tr), Variable):
            raise Reshape(self.resultant.cdir)
        return [self._make_tr(tr, self.resultant.within(tr).value)]
    
    def from_mapping(self, tr):
        within = self.resultant.within(tr)  # always raises Reshape unless already a VarValue
        return [] if within.value is None else [self._make_tr(tr, within.value)]


class Coord(tuple):
    """
    Represents a 'unit coordinate'.
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
        return super().__new__(cls, it)
    
    def __init__(self, tup, tbl=None):
        self.tbl = tbl
        self.tuple = tuple(super().__iter__())
        if not (-2 < self.x < 2 and -2 < self.y < 2):
            raise CoordOutOfBoundsError(self)
    
    def __repr__(self):
        return f'Coord({super().__repr__()})'
    
    @classmethod
    def from_name(cls, cdir, tbl=None):
        return cls(cls._OFFSETS[cdir], tbl)
    
    @property
    def name(self):
        return self._NAMES[self]
    
    @property
    def idx(self):
        return self.tbl.neighborhood[self.name]
    
    @property
    def inv(self):
        return Coord((-self.x, -self.y), self.tbl)
    
    @property
    def cw(self):
        idx = 1 + self._DIRMAP[self.name]
        return _MaybeCallableCW(self._OFFSETS[self._DIRS[idx % 8]], self.tbl)
    
    @property
    def ccw(self):
        idx = self._DIRMAP[self.name]
        return _MaybeCallableCCW(self._OFFSETS[self._DIRS[idx-1]], self.tbl)
    
    @property
    def x(self):
        return self[0]
    
    @property
    def y(self):
        return self[1]
    
    def valid(self):
        return self.center() or self.tbl and self.name in self.tbl.neighborhood
    
    def diagonal(self):
        return all(self)
    
    def center(self):
        return self == (0, 0)
    
    def toward(self, cd):
        return self.move(*self._OFFSETS[cd.upper()])
    
    def move(self, x=0, y=0):
        return Coord((x + self.x, y + self.y), self.tbl)


class _MaybeCallableCW(Coord):
    """
    Allows Coord.cw.cw.cw.cw to be replaced by Coord.cw(4), and so on.
    (The former will still work, however.)
    """
    def __call__(self, num):
        return Coord(self.cw(num-1) if num > 1 else self, self.tbl)


class _MaybeCallableCCW(Coord):
    """
    Ditto above, but counterclockwise.
    """
    def __call__(self, num):
        return Coord(self.ccw(num-1) if num > 1 else self, self.tbl)
