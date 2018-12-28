from collections import OrderedDict
from functools import lru_cache, reduce, partial
from math import ceil
from operator import and_ as bitwise_and

from nutshell.common.utils import multisplit
from ._neighborhoods import Neighborhood
from ._classes import Coord, InlineBinding


class Napkin(tuple):
    _hash_func = None
    nbhd = None
    transformations = None
    nested_transformations = None
    tilde = None
    _RECENTS = {}

    def __init__(self, _):
        self._expanded = None
        self._hash = None
    
    # 3.6-only: pep 487
    def __init_subclass__(cls):
        # if cls.nbhd is None:
        #    raise NotImplementedError('Please override class attribute `nbhd` in Napkin subclass')
        if cls.transformations is None:
            raise NotImplementedError('Please override class attribute `transformations` in Napkin subclass')
        cls._RECENTS = {}
        cls.test_nbhd()
    
    def __hash__(self):
        if self._hash is None:
            self._hash = hash(tuple(sorted(self.expanded)))
        return self._hash
    
    def __eq__(self, other):
        return isinstance(other, tuple) and any(map(other.__eq__, self.expanded))
    
    def __repr__(self):
        return f'{self.__class__.__name__}{super().__repr__()}'
    
    def expand(self, cls=None):
        if cls is None:
            cls = self.__class__
        searchable = cls._hash_func(self)
        if searchable not in cls._RECENTS:
            cls._RECENTS[searchable] = cls._expand(self)
        return cls._RECENTS[searchable]
    
    def _expand(self):
        raise NotImplementedError('Please override method `_expand()` in Napkin subclass')
    
    @property
    def expanded(self):
        if self._expanded is None:
            self._expanded = frozenset(self._expand())
        return self._expanded
    
    @property
    def cdir_map(self):
        return dict(zip(self.nbhd, self))
    
    @classmethod
    def compose(cls, other):
        if cls.nbhd != other.nbhd:
            raise TypeError(f'Cannot compose symmetries of different neighborhoods {cls.nbhd!r} and {other.nbhd!r}')
        return new_sym_type(
          cls.nbhd,
          f'{cls.__name__}+{other.__name__}',
          cls.transformations + other.transformations,
          lambda self: [j for i in other.expand(self, other) for j in cls.expand(self.__class__(i), cls)],
          nested_transformations=cls.nested_transformations | other.nested_transformations
          )
    
    @classmethod
    def combine(cls, other):
        if cls.nbhd != other.nbhd:
            raise TypeError(f'Cannot combine symmetries of different neighborhoods {cls.nbhd!r} and {other.nbhd!r}')
        return new_sym_type(
          cls.nbhd,
          f'{cls.__name__}/{other.__name__}',
          cls.transformations + other.transformations,
          lambda self: [*other.expand(self, other), *cls.expand(self, cls)],
          nested_transformations=frozenset((cls.nested_transformations, other.nested_transformations))
          )
    
    @classmethod
    def test_nbhd(cls):
        if not cls.nbhd.supports(cls):
            raise ValueError(f'Neighborhood does not support {cls.__name__} symmetries')
    
    def _convert(self, iterable):
        cdir_map = self.cdir_map
        return [tuple(cdir_map[j] for j in i) for i in iterable]
    
    def reflections_across(self, *args):
        return self._convert(self.nbhd.reflections_across(*args, as_cls=False))
    
    def rotations_by(self, *args):
        return self._convert(self.nbhd.rotations_by(*args, as_cls=False))
    
    def permutations(self, *args):
        return self._convert(self.nbhd.permutations(*args, as_cls=False))


def find_golly_sym_type(symmetries, nbhd):
    dummy = range(len(nbhd))
    result = reduce(
      bitwise_and,
      [cls(dummy).expanded for cls in symmetries]
      )
    if result not in _GOLLY_NAMES:
        # Pretty sure this is 100% wrong for the general case.
        # it works for alternatingpermute->rotate4reflect, at least.
        HighestSupportedSym = (
          compose(rotate(len(nbhd)), reflect('N'))
          if nbhd.supports_transformations([['reflect_across', 'N']])
          else rotate(len(nbhd))
        )(nbhd)
        result &= HighestSupportedSym(dummy).expanded
    if result in _GOLLY_NAMES:
        name = _GOLLY_NAMES[result]
        return (PRESETS.get(name) or FUNCS[name]())(nbhd), name
    return none(nbhd), 'none'


def get_sym_type(nbhd, string):
    current = []
    all_syms = [[]]
    for token in multisplit(string, (None, *'(),')):
        if token == '/':
            if current:
                all_syms[-1].append(current)
            if all_syms[-1]:
                all_syms.append([])
            current = []
            continue
        if token in PRESETS or token in FUNCS:
            if current:
                all_syms[-1].append(current)
            current = []
        current.append(token)
    if current:
        all_syms[-1].append(current)
    resultant_sym = None
    for compose_group in all_syms:
        composed_sym = None
        for name, *args in compose_group:
            cur_sym = PRESETS[name](nbhd) if name in PRESETS else FUNCS[name](*args)(nbhd)
            composed_sym = cur_sym if composed_sym is None else composed_sym.compose(cur_sym)
        resultant_sym = composed_sym if resultant_sym is None else resultant_sym.combine(composed_sym)
    return resultant_sym


def new_sym_type(nbhd, name, transformations, func=None, *, tilde=None, nested_transformations=None, hash_func=tuple):
    if func is None:
        method = getattr(Napkin, transformations[0])
        method_args = transformations[1:]
        func = lambda self: method(self, *method_args)
        transformations = (transformations,)
    if nested_transformations is None:
        nested_transformations = frozenset(transformations)
    return type(name, (Napkin,), {
      '_expand': func,
      'transformations': transformations,
      'nested_transformations': nested_transformations,
      'nbhd': nbhd,
      'tilde': tilde,
      '_hash_func': hash_func
    })


@lru_cache()
def compose(*funcs):
    return lru_cache()(lambda nbhd: reduce(Napkin.compose.__func__, [f(nbhd) for f in funcs]))


@lru_cache()
def combine(*funcs):
    return lru_cache()(lambda nbhd: reduce(Napkin.combine.__func__, [f(nbhd) for f in funcs]))


@lru_cache()
def reflect(first=None, second=None):
    if first is None:
        first = second = 'N'
    first = Coord.from_name(first)
    second = first if second is None else Coord.from_name(second)
    return lru_cache()(lambda nbhd: new_sym_type(
      nbhd,
      f'Reflect({first.name} {second.name})',
      ('reflections_across', (first, second))  # lambda self: self.reflections_across((first, second))
    ))


@lru_cache()
def rotate(n):
    return lru_cache()(lambda nbhd: new_sym_type(
      nbhd,
      f'Rotate({n})',
      ('rotations_by', int(n))  # lambda self: self.rotations_by(int(n))
    ))


@lru_cache()
def permute(*cdirs, explicit=False):
    return lru_cache()(lambda nbhd: new_sym_type(
      nbhd,
      f"Permute({' '.join(cdirs) if cdirs else 'All'})",
      ('permutations', cdirs or None),  # lambda self: self.permutations(cdirs or None)
      tilde=permute_tilde_explicit if explicit or len(cdirs) == len(nbhd) else permute_tilde,
      hash_func=frozenset
    ))


@lru_cache()
def none(nbhd):
    return new_sym_type(nbhd, 'NoSymmetry', (), lambda self, **_: [tuple(self)])


def permute_tilde_explicit(self, values):
    new = []
    for v, count in values:
        if count is None:
            count = '1'
        if not count.isdigit():
            raise Exception(f"{v} ~ {count}; '{count}' is not a number")
        new.extend([v] * int(count))
    if len(new) < len(self.nbhd):
        raise Exception(f'Expected {len(self.nbhd)} terms, got {len(new)}')
    return new


def permute_tilde(self, values):
    """
    Given a shorthand permutationally-symmetrical transition:
        length=8 (Moore neighborhood)
        -------
        1, 0
        1~4, 0~4
        1~4, 0
        1~3, 1, 0, 0
    Return its expanded representation:
        1, 1, 1, 1, 0, 0, 0, 0
    Order is not preserved.
    """
    length = len(self.nbhd)
    # filler algo courtesy of Thomas Russell on math.stackexchange
    # https://math.stackexchange.com/a/1081084
    filler = _fill(
        length,
        # How many cells filled
        length - sum(int(i) for _, i in values if i),
        # And how many empty slots left to fill
        sum(1 for _, i in values if not i)
        )
    return list(_AccumulativeContainer(
        (val.set(idx) if isinstance(val, InlineBinding) else val, next(filler) if num is None else int(num))
        for idx, (val, num) in enumerate(values, 1)
    ))


def _fill(length, tally, empties):
    """Only in its own function to be able to raise error on 0"""
    for k in range(1, 1 + empties):
        v = ceil((tally - k + 1) / empties)
        if v == 0:
            raise ValueError(f'Too many terms given (expected no more than {length})')
        yield v


class _AccumulativeContainer(list):
    def __init__(self, it):
        for thing, count in it:
            self.append((thing, 1 if count is None else count))
    
    def __iter__(self):
        return (i.give() if isinstance(i, InlineBinding) else i for k, v in super().__iter__() for i in [k]*v)


_hex = Neighborhood('hexagonal')
# 3.6-only: pep 468
PRESETS = OrderedDict(
  none=none,
  reflect_vertical=reflect('W'),
  reflect_horizontal=reflect('N'),
  rotate2=rotate(2),
  rotate3=rotate(3),
  rotate4=rotate(4),
  rotate4reflect=compose(rotate(4), reflect('N')),
  rotate6=rotate(6),
  rotate6reflect=compose(rotate(6), reflect('N')),
  rotate8=rotate(8),
  rotate8reflect=compose(rotate(8), reflect('N'))
)
_GOLLY_NAMES = {}

FUNCS = {
  'permute': permute,
  'explicit_permute': partial(permute, explicit=True),
  'reflect': reflect,
  'rotate': rotate,
}

_permute = permute()
_FORBIDDEN = {('hexagonal', 'reflect'), ('Moore', 'rotate2'), ('vonNeumann', 'rotate2'), ('oneDimensional', 'rotate2')}
for nbhd_name in Neighborhood.GOLLY_NBHDS:
    nbhd = Neighborhood(nbhd_name)
    dummy = range(len(nbhd))
    for sym_name, func in PRESETS.items():
        if sym_name == 'reflect_horizontal':
            sym_name = 'reflect'
        if sym_name == 'reflect_vertical' or (nbhd_name, sym_name) in _FORBIDDEN:
            continue
        try:
            sym = func(nbhd)
        except Exception:
            continue
        _GOLLY_NAMES[sym(dummy).expanded] = sym_name
    _GOLLY_NAMES[_permute(nbhd)(dummy).expanded] = 'permute'
