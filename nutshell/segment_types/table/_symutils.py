from functools import reduce
from importlib import import_module

from nutshell.common import symmetries as ext_symmetries, utils
from ._classes import Coord
from . import _napkins as napkins


PRESETS = {
  'rotate8reflect': lambda *_: compose(rotate(8), reflect('W')),
  'rotate8': lambda *_: rotate(8),
  'rotate4reflect': lambda *_: compose(rotate(4), reflect('W')),
  'rotate4': lambda *_: rotate(4),
  'reflect_horizontal': lambda *_: reflect('W'),
  'reflect_vertical': lambda *_: reflect('N'),
  'none': lambda *_: lambda nbhd: _new_sym_type(nbhd, 'NoSymmetry', _none),
  ####
  'permute': lambda *args: permute(*args),
  'reflect': lambda *args: reflect(*args),
  'rotate': lambda *args: rotate(*args),
}


class Napkin(tuple):
    def __new__(cls, iterable, *_):
        return super().__new__(cls, iterable)
    
    def __init__(self, _):
        self._cdir_map = dict(zip(self.nbhd, self))
        self._expanded = None
        self._hash = None
    
    def __hash__(self):
        if self._hash is None:
            self._hash = hash(tuple(sorted(self.expanded)))
        return self._hash
    
    def __repr__(self):
        return f'{self.__class__.__name__}{super().__repr__()}'
    
    def _expand(self):
        raise NotImplementedError("Please override method `_expand()` in Napkin subclass")
    
    @property
    def nbhd(self):
        raise NotImplementedError("Please override static variable `nbhd` in Napkin subclass")
    
    @property
    def expanded(self):
        if self._expanded is None:
            self._expanded = frozenset(self._expand())
        return self._expanded
    
    @classmethod
    def compose(cls, other):
        if cls.nbhd != other.nbhd:
            raise TypeError(f'Cannot compose symmetries of differing neighborhoods {cls.nbhd} and {other.nbhd}')
        return _new_sym_type(
          cls.nbhd,
          f'{cls.__name__}+{other.__name__}',
          lambda self: [j for i in other(self).expanded for j in cls(i).expanded]
          )
    
    def _convert(self, iterable):
        return [tuple(map(self._cdir_map.get, i)) for i in iterable]
    
    def reflections_across(self, *args):
        return self._convert(self.nbhd.reflections_across(*args))
    
    def rotations_by(self, *args):
        return self._convert(self.nbhd.rotations_by(*args))
    
    def permutations(self, *args):
        return self._convert(self.nbhd.permutations(args))


def find_min_sym_type(symmetries, tr_len):
    dummy = range(tr_len)
    return permute()(dummy) & reduce(set.__and__, [cls(dummy).expanded for cls in symmetries])


def get_sym_type(nbhd, string):
    all_syms = []
    current = []
    for token in utils.multisplit(string, (None, *'(),')):
        if token in PRESETS:
            if current:
                all_syms.append(current)
            current = []
        current.append(token)
    all_syms.append(current)
    resultant_sym = None
    for name, *args in all_syms:
        cur_sym = PRESETS[name](*args)(nbhd)
        resultant_sym = cur_sym if resultant_sym is None else resultant_sym.compose(cur_sym)
    return resultant_sym


def _new_sym_type(nbhd, name, func):
    return type(name, (Napkin,), {
      '_expand': func,
      'nbhd': nbhd
    })


def compose(*funcs):
    return lambda nbhd: reduce(lambda a, b: a.compose(b), [f(nbhd) for f in funcs])


def reflect(first, second=None):
    first = Coord.from_name(first)
    second = first if second is None else Coord.from_name(second)
    return lambda nbhd: _new_sym_type(
      nbhd,
      f'Reflect_{first.name}_{second.name}',
      lambda self: self.reflections_across((first, second))
      )


def rotate(n):
    return lambda nbhd: _new_sym_type(
      nbhd,
      f'Rotate_{n}',
      lambda self: self.rotations_by(int(n))
    )


def permute(*cdirs):
    return lambda nbhd: _new_sym_type(
      nbhd,
      f"Permute_{'_'.join(cdirs)}",
      lambda self: self.permutations(cdirs or None)
    )

def _none(self):
    return [self]
