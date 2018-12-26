from functools import reduce
from importlib import import_module
from operator import and_ as bitwise_and

from nutshell.common import symmetries as ext_symmetries, utils
from ._classes import Coord
# from ._neighborhoods import Neighborhood
    

class Napkin(tuple):
    nbhd = None
    transformations = None

    def __init__(self, _):
        self._expanded = None
        self._hash = None
    
    def __init_subclass__(cls):
        if cls.nbhd is None:
            raise NotImplementedError('Please override class attribute `nbhd` in Napkin subclass')
        if cls.transformations is None:
            raise NotImplementedError('Please override class attribute `transformations` in Napkin subclass')
        cls.test_nbhd()
    
    def __hash__(self):
        if self._hash is None:
            self._hash = hash(tuple(sorted(self.expanded)))
        return self._hash
    
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
            raise TypeError('Cannot compose symmetries of different neighborhoods {cls.nbhd!r} and {other.nbhd!r}')
        return _new_sym_type(
          cls.nbhd,
          f'{cls.__name__}+{other.__name__}',
          cls.transformations + other.transformations,
          lambda self: [j for i in other.expand(self) for j in cls.expand(self.__class__(i))]
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
    superset = permute()(dummy)
    return superset(dummy).expanded & reduce(
      bitwise_and,
      [cls(dummy).expanded for cls in symmetries]
      )


def get_sym_type(nbhd, string):
    all_syms = []
    current = []
    for token in utils.multisplit(string, (None, *'(),')):
        if token in PRESETS or token in FUNCS:
            if current:
                all_syms.append(current)
            current = []
        current.append(token)
    all_syms.append(current)
    resultant_sym = None
    for name, *args in all_syms:
        _cur_sym = PRESETS[name](nbhd) if name in PRESETS else FUNCS[name](*args)
        cur_sym = _cur_sym(nbhd)
        resultant_sym = cur_sym if resultant_sym is None else resultant_sym.compose(cur_sym)
    return resultant_sym


def _new_sym_type(nbhd, name, transformations, func=None):
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


def compose(*funcs):
    return lambda nbhd: reduce(Napkin.compose.__func__, [f(nbhd) for f in funcs])


def reflect(first, second=None):
    first = Coord.from_name(first)
    second = first if second is None else Coord.from_name(second)
    return lambda nbhd: _new_sym_type(
      nbhd,
      f'Reflect_{first.name}_{second.name}',
      ('reflections_across', (first, second))  # lambda self: self.reflections_across((first, second))
      )


def rotate(n):
    return lambda nbhd: _new_sym_type(
      nbhd,
      f'Rotate_{n}',
      ('rotations_by', int(n))  # lambda self: self.rotations_by(int(n))
    )


def permute(*cdirs):
    return lambda nbhd: _new_sym_type(
      nbhd,
      f"Permute_{'_'.join(cdirs) if cdirs else 'All'}",
      ('permutations', cdirs or None)  # lambda self: self.permutations(cdirs or None)
    )

def _none(nbhd):
    return _new_sym_type(nbhd, 'NoSymmetry', lambda self: [self])


PRESETS = {
  'rotate8reflect': compose(rotate(8), reflect('W')),
  'rotate8': rotate(8),
  'rotate4reflect': compose(rotate(4), reflect('W')),
  'rotate4': rotate(4),
  'reflect_horizontal': reflect('W'),
  'reflect_vertical': reflect('N'),
  'none': _none
}

FUNCS = {
  'permute': permute,
  'reflect': reflect,
  'rotate': rotate,
}
