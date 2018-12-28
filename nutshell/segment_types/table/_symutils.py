from collections import OrderedDict
from functools import reduce, lru_cache
from importlib import import_module
from operator import and_ as bitwise_and

from nutshell.common import symmetries as ext_symmetries, utils
from ._neighborhoods import Neighborhood
from ._classes import Coord


class Napkin(tuple):
    nbhd = None
    transformations = None
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
    
    def expand(self):
        raise NotImplementedError('Please override method `expand()` in Napkin subclass')
    
    @property
    def expanded(self):
        if self._expanded is None:
            self._expanded = frozenset(self.expand())
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
          lambda self: [j for i in other.expand(self) for j in cls.expand(self.__class__(i))]
          )
    
    @classmethod
    def combine(cls, other):
        if cls.nbhd != other.nbhd:
            raise TypeError(f'Cannot combine symmetries of different neighborhoods {cls.nbhd!r} and {other.nbhd!r}')
        return new_sym_type(
          cls.nbhd,
          f'{cls.__name__}/{other.__name__}',
          cls.transformations + other.transformations,
          lambda self: [*other.expand(self), *cls.expand(self)]
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


def find_min_sym_type(symmetries, nbhd):
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
    for token in utils.multisplit(string, (None, *'(),')):
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


def new_sym_type(nbhd, name, transformations, func=None):
    if func is None:
        method = getattr(Napkin, transformations[0])
        args = transformations[1:]
        func = lambda self: method(self, *args)
        transformations = [transformations]
    return type(name, (Napkin,), {
      'expand': func,
      'transformations': transformations,
      'nbhd': nbhd
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
      f'Reflect_{first.name}_{second.name}',
      ('reflections_across', (first, second))  # lambda self: self.reflections_across((first, second))
    ))


@lru_cache()
def rotate(n):
    return lru_cache()(lambda nbhd: new_sym_type(
      nbhd,
      f'Rotate_{n}',
      ('rotations_by', int(n))  # lambda self: self.rotations_by(int(n))
    ))


@lru_cache()
def permute(*cdirs):
    return lru_cache()(lambda nbhd: new_sym_type(
      nbhd,
      f"Permute_{'_'.join(cdirs) if cdirs else 'All'}",
      ('permutations', cdirs or None)  # lambda self: self.permutations(cdirs or None)
    ))


@lru_cache()
def none(nbhd):
    return new_sym_type(nbhd, 'NoSymmetry', (), lambda self: [tuple(self)])


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
