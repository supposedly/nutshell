from functools import reduce
from importlib import import_module

from nutshell.common import symmetries as ext_symmetries, utils
from ._classes import Coord
from . import _napkins as napkins


# pretty sure this is a hacky observer-pattern implementation
class NapkinMeta(type):
    def __init__(cls, *_):
        cls.__tested = False
    
    @property
    def nbhd(cls):
        if not hasattr(cls, '_nbhd'):
            cls._nbhd = None
        if cls._nbhd is not None and not cls.__tested:
            cls.__tested = True
            cls.test_nbhd()
        return cls._nbhd
    
    @nbhd.setter
    def nbhd(cls, neighborhood):
        old, cls._nbhd = cls._nbhd, neighborhood
        try:
            cls.test_nbhd()
        except:
            cls._nbhd = old
            raise
    
    def test_nbhd(cls):
        cls(range(len(cls.nbhd))).expanded


class Napkin(tuple, metaclass=NapkinMeta):
    def __new__(cls, iterable):
        return super().__new__(cls, iterable)
    
    def __init__(self, _):
        self._expanded = None
        self._hash = None
    
    def __hash__(self):
        if self._hash is None:
            self._hash = hash(tuple(sorted(self.expanded)))
        return self._hash
    
    def __repr__(self):
        return f'{self.__class__.__name__}{super().__repr__()}'
    
    def expand(self):
        raise NotImplementedError("Please override method `expand()` in Napkin subclass")
    
    @property
    def expanded(self):
        if self._expanded is None:
            self._expanded = frozenset(self.expand())
        return self._expanded
    
    @property
    def cdir_map(self):
        return dict(zip(self._neighborhood, self))
    
    @property
    def _neighborhood(self):
        return self.__class__.nbhd
    
    @classmethod
    def compose(cls, other):
        def _not_lambda(self):
            # why bother with .__get__() rather than just iterating through .expanded?
            # because (1) each class's nbhd may not yet have been initialized, which will
            # make .expanded error, and (2) when we're composing, we don't really care about
            # the method as relating to a specific class -- we only care about the *transformation*
            # provided by the pure, unbound method
            return [j for i in other.expand.__get__(self)() for j in cls.expand.__get__(self.__class__(i))()]
        return _new_sym_type(
          f'{cls.__name__}+{other.__name__}',
          _not_lambda
          )
    
    def _convert(self, iterable):
        cdir_map = self.cdir_map
        return [tuple(cdir_map[j] for j in i) for i in iterable]
    
    def reflections_across(self, *args):
        return self._convert(self._neighborhood.reflections_across(*args))
    
    def rotations_by(self, *args):
        return self._convert(self._neighborhood.rotations_by(*args))
    
    def permutations(self, *args):
        return self._convert(self._neighborhood.permutations(*args))


def find_min_sym_type(symmetries, nbhd):
    dummy = range(len(nbhd))
    # `return permute_under_nbhd(dummy) & ...` for non-golly symmetries too
    return reduce(frozenset.__and__, [cls(dummy).expanded for cls in symmetries])


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
        cur_sym = PRESETS[name] if name in PRESETS else FUNCS[name](*args)
        resultant_sym = cur_sym if resultant_sym is None else resultant_sym.compose(cur_sym)
    resultant_sym.nbhd = nbhd
    return resultant_sym


def _new_sym_type(name, func):
    return type(name, (Napkin,), {
      'expand': func,
      '_nbhd': None
    })


def compose(*funcs):
    return reduce(lambda a, b: a.compose(b), funcs)


def reflect(first, second=None):
    first = Coord.from_name(first)
    second = first if second is None else Coord.from_name(second)
    return _new_sym_type(
      f'Reflect_{first.name}_{second.name}',
      lambda self: self.reflections_across((first, second))
      )


def rotate(n):
    return _new_sym_type(
      f'Rotate_{n}',
      lambda self: self.rotations_by(int(n))
    )


def permute(*cdirs):
    return _new_sym_type(
      f"Permute_{'_'.join(cdirs) if cdirs else 'All'}",
      lambda self: self.permutations(cdirs or None)
    )

def _none(self):
    return [self]


PRESETS = {
  'rotate8reflect': compose(rotate(8), reflect('W')),
  'rotate8': rotate(8),
  'rotate4reflect': compose(rotate(4), reflect('W')),
  'rotate4': rotate(4),
  'reflect_horizontal': reflect('W'),
  'reflect_vertical': reflect('N'),
  'none': _new_sym_type('NoSymmetry', _none)
}

FUNCS = {
  'permute': permute,
  'reflect': reflect,
  'rotate': rotate,
}
