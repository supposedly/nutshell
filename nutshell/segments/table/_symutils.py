from collections import OrderedDict
from functools import lru_cache, reduce, partial
from math import ceil
from operator import and_ as bitwise_and, or_ as bitwise_or

from nutshell.common.utils import multisplit
from ._errors import NeighborhoodError
from ._neighborhoods import Neighborhood
from ._classes import Coord, InlineBinding


class Napkin(tuple):
    permute_hash_indices = None
    nbhd = None
    transformation_names = None
    transformations = None
    tilde = None
    _RECENTS = {}

    def __init__(self, _):
        self.cdir_map = dict(zip(self.nbhd, self))
        self._expanded = None
        self._hash = None
    
    # 3.6-only: pep 487
    def __init_subclass__(cls):
        # if cls.nbhd is None:
        #    raise NotImplementedError('Please override class attribute `nbhd` in Napkin subclass')
        if cls.transformation_names is None:
            raise NotImplementedError('Please override class attribute `transformation_names` in Napkin subclass')
        if cls.transformations is None and cls.nbhd is not None:
            if len(cls.transformation_names) > 1:
                raise NotImplementedError('Please override class attribute `transformations` in Napkin subclass')
            func, *args = cls.transformation_names[0]
            cls.transformations = frozenset(getattr(cls.nbhd, func)(*args, as_cls=False))
        cls._RECENTS = {}
        if not cls.test_nbhd():
            raise NeighborhoodError(f'Symmetry type {cls.__name__!r} is not supported by its neighborhood {cls.nbhd.cdirs}')
    
    def __hash__(self):
        if self._hash is None:
            self._hash = hash(tuple(sorted(self.expanded)))
        return self._hash
    
    def __eq__(self, other):
        return isinstance(other, tuple) and any(map(other.__eq__, self.expanded))
    
    def __repr__(self):
        return f'{self.__class__.__name__}{super().__repr__()}'
    
    @classmethod
    def with_neighborhood(cls, nbhd):
        return new_sym_type(
          nbhd,
          cls.__name__,
          cls.transformation_names,
          transformations=cls.transformations,
          tilde=cls.tilde,
          permute_hash_indices=cls.permute_hash_indices
        )
    
    @classmethod
    def compose(cls, other):
        if cls.nbhd != other.nbhd:
            raise TypeError(f'Cannot compose symmetries of different neighborhoods {cls.nbhd!r} and {other.nbhd!r}')
        if cls.permute_hash_indices is None or other.permute_hash_indices is None:
            hash_indices = None
        else:
            # Make sure we can compose them w/o headache
            cls_stationary, cls_permutable = cls.permute_hash_indices
            other_stationary, other_permutable = other.permute_hash_indices
            both_stationary = cls_stationary | other_stationary
            both_permutable = reduce(bitwise_or, cls_permutable) | reduce(bitwise_or, other_permutable)
            
            if reduce(bitwise_and, cls_permutable) or reduce(bitwise_and, other_permutable) \
            or both_permutable & both_stationary:
                hash_indices = None
            else:
                hash_indices = (
                  {i for i in both_stationary if i not in both_permutable},
                  cls_permutable + other_permutable
                )
        nbhd = cls.nbhd
        return new_sym_type(
          nbhd,
          f'{cls.__name__}+{other.__name__}',
          cls.transformation_names + other.transformation_names,
          # I don't actually get why this works but not frozenset([j for i in cls.transformations for j in other(i).expanded])
          transformations=frozenset([tuple(a[nbhd[i]-1] for i in b) for a in cls.transformations for b in other.transformations]),
          permute_hash_indices=hash_indices
          )
    
    @classmethod
    def combine(cls, other):
        if cls.nbhd != other.nbhd:
            raise TypeError(f'Cannot combine symmetries of different neighborhoods {cls.nbhd!r} and {other.nbhd!r}')
        return new_sym_type(
          cls.nbhd,
          f'{cls.__name__}/{other.__name__}',
          cls.transformation_names + other.transformation_names,
          transformations=cls.transformations|other.transformations
          )
    
    @classmethod
    def test_nbhd(cls):
        if cls.nbhd is None:
            return
        return cls.nbhd.supports(cls)
    
    @property
    def expanded(self):
        if self._expanded is None:
            cls = self.__class__
            if cls.permute_hash_indices is None:
                self._expanded = frozenset(self._expand())
            else:
                hashable = self._get_hashable()
                if hashable not in cls._RECENTS:
                    cls._RECENTS[hashable] = frozenset(self._expand())
                self._expanded = cls._RECENTS[hashable]
        return self._expanded
    
    def _get_hashable(self):
        stationary, permutables = self.__class__.permute_hash_indices
        return (
          tuple([self[i] for i in stationary]),
          tuple([frozenset([self[i] for i in permutable]) for permutable in permutables])
          )
    
    def _expand(self):
        cdir_map = self.cdir_map
        return {tuple(cdir_map[i] for i in transformation) for transformation in self.transformations}
    
    def _expand_other(self, iterable):
        cdir_map = self.cdir_map
        return [tuple(cdir_map[j] for j in i) for i in iterable]
    
    def reflections_across(self, *args):
        return self._expand_other(self.nbhd.reflections_across(*args, as_cls=False))
    
    def rotations_by(self, *args):
        return self._expand_other(self.nbhd.rotations_by(*args, as_cls=False))
    
    def permutations(self, *args):
        return self._expand_other(self.nbhd.permutations(*args, as_cls=False))


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


def new_sym_type(nbhd, name, transformation_names, *, transformations=None, tilde=None, permute_hash_indices=None):
    return type(name, (Napkin,), {
      'transformation_names': transformation_names,
      'transformations': transformations,
      'nbhd': nbhd,
      'tilde': tilde,
      'permute_hash_indices': permute_hash_indices
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
      [('reflections_across', (first, second))]  # lambda self: self.reflections_across((first, second))
    ))


@lru_cache()
def rotate(n):
    return lru_cache()(lambda nbhd: new_sym_type(
      nbhd,
      f'Rotate({n})',
      [('rotations_by', int(n))]  # lambda self: self.rotations_by(int(n))
    ))


@lru_cache()
def permute(*cdirs, explicit=False):
    @lru_cache()
    def _(nbhd):
        not_cdirs = [i for i in nbhd if i not in cdirs]
        return new_sym_type(
          nbhd,
          f"Permute({' '.join(cdirs) if cdirs else 'All'})",
          [('permutations', cdirs or None)],  # lambda self: self.permutations(cdirs or None)
          tilde=permute_tilde_explicit if explicit or cdirs and len(cdirs) < len(nbhd) else permute_tilde,
          permute_hash_indices=({nbhd[i] - 1 for i in cdirs}, [{nbhd[i] - 1 for i in not_cdirs}])
        )
    return _


@lru_cache()
def none(nbhd):
    return new_sym_type(nbhd, 'NoSymmetry', [('identity',)])


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
