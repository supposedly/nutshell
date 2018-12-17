from itertools import permutations
from math import ceil

from nutshell.common.utils import LazyProperty
from ._setutils import IndexedSet
from ._classes import InlineBinding

oneDimensional, vonNeumann, hexagonal, Moore = 2, 4, 6, 8
Any = None


class _NapkinMeta(type):
    def __init__(cls, name, bases, attrs):
        if 'expanded' not in attrs or 'symmetries' in attrs:
            # if it's some sort of base class like Napkin or OrthNapkin
            # or has symmetries preimplemented itself
            return
        if isinstance(attrs.get('fallback'), (str, _NapkinMeta)):
            cls.fallback = {Any: NAMES[cls.fallback] if isinstance(cls.fallback, str) else cls.fallback}
        if isinstance(attrs.get('fallback'), dict):
            cls.fallback = {k: NAMES[v] if isinstance(v, str) else v for k, v in cls.fallback.items()}
            if Any in cls.fallback and cls.neighborhoods is not Any:
                cls.fallback = {
                  **{k: cls.fallback[Any] for k in cls.neighborhoods},
                  # We do want the user-set ones to override the
                  # cls.fallback[Any]s where possible, so this goes 2nd
                  **{k: v for k, v in cls.fallback.items() if k is not Any}
                  }
        cls.symmetries = {
          n: set(cls(range(n)).expanded)
          for n in
          (range(1, 9) if cls.neighborhoods is Any else cls.neighborhoods)
          }
        cls.sym_lens = {n: len(v) for n, v in cls.symmetries.items()}
        if 'clear' in attrs:
            cls.clear()


class Napkin(tuple, metaclass=_NapkinMeta):
    """
    Term "napkin" by 83bismuth38.
    Represents the 'neighborhood' segment of a transition.
    """
    def __init__(self, iterable=None):
        self._hash = None
    
    def __eq__(self, other):
        return isinstance(other, tuple) and any(map(other.__eq__, self.expanded))
    
    def __hash__(self):
        if self._hash is None:
            self._hash = hash(tuple(sorted(self.expanded_unique)))
        return self._hash
    
    def __repr__(self):
        return f'{type(self).__name__}({super().__repr__()})'
    
    def rotate_by(self, offset):
        return self[offset:] + self[:offset]
    
    def rotate(self, n):
        return map(self.rotate_by, range(0, len(self), len(self) // n))
    
    @LazyProperty
    def expanded_unique(self):
        return IndexedSet(self.expanded)
    
    def expand(self):
        return map(type(self), self.expanded_unique)


class OrthNapkin(Napkin):
    """Moore & vonNeumann"""
    @staticmethod
    def reflection_of(seq):
        return sorted((seq, (seq[0], *seq[:0:-1])))
    
    def rotated4(self):
        return sorted(self.rotate(4))
    
    def rotated8(self):
        return sorted(self.rotate(8))


class HexNapkin(Napkin):
    @staticmethod
    def reflection_of(seq):
        return sorted((seq, tuple(seq[i] for i in (4, 2, 3, 1, 0, 5))))
    
    def rotated2(self):
        return sorted(self.rotate(2))
    
    def rotated3(self):
        return sorted(self.rotate(3))
    
    def rotated6(self):
        return sorted(self.rotate(6))


class NoSymmetry(tuple, metaclass=_NapkinMeta):
    neighborhoods = Any
    name = ['none']
    
    def expand(self):
        return self,
    
    expanded = property(expand)


# Hexagonal napkins
class Rotate2(HexNapkin):
    neighborhoods = hexagonal,
    @property
    def expanded(self):
        return self.rotated2()


class Rotate3(HexNapkin):
    neighborhoods = hexagonal,
    @property
    def expanded(self):
        return self.rotated3()


class Rotate6(HexNapkin):
    neighborhoods = hexagonal,
    @property
    def expanded(self):
        return self.rotated6()


class Rotate6Reflect(HexNapkin):
    neighborhoods = hexagonal,
    @property
    def expanded(self):
        return (tup for i in self.rotated6() for tup in self.reflection_of(i))


# Orthogonal napkins
class ReflectHorizontal(OrthNapkin):
    neighborhoods = vonNeumann, Moore
    name = ['reflect', 'reflect_horizontal']
    @LazyProperty
    def expanded(self):
        return self.reflection_of(tuple(self))


class Rotate4(OrthNapkin):
    neighborhoods = vonNeumann, Moore
    @LazyProperty
    def expanded(self):
        return self.rotated4()


class Rotate4Reflect(OrthNapkin):
    neighborhoods = vonNeumann, Moore
    @property
    def expanded(self):
        return (tup for i in self.rotated4() for tup in self.reflection_of(i))


class Rotate8(OrthNapkin):
    neighborhoods = Moore,
    @LazyProperty
    def expanded(self):
        return self.rotated8()


class Rotate8Reflect(OrthNapkin):
    neighborhoods = Moore,
    @property
    def expanded(self):
        return (tup for i in self.rotated8() for tup in self.reflection_of(i))


# General
class Permute(Napkin):
    neighborhoods = Any
    RECENTS = {}
    HASHES = {}
    
    def __hash__(self):
        if self._hash is None:
            self._hash = self.HASHES[tuple(sorted(self))]
        return self._hash
    
    @LazyProperty
    def expanded(self):
        t = tuple(sorted(self))
        if t in self.RECENTS:
            self._hash = self.HASHES[t]
            return self.RECENTS[t]
        self.RECENTS[t] = ret = list(permutations(t))
        self.HASHES[t] = self._hash = hash(tuple(ret))
        return ret
    
    @classmethod
    def clear(cls):
        cls.RECENTS.clear()
        cls.HASHES.clear()
    
    @staticmethod
    def special(values, length):
        """
        Given a shorthand permutationally-symmetric transition:
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
        # filler algo courtesy of Thomas Russell on math.stackexchange
        # https://math.stackexchange.com/a/1081084
        filler = Permute._fill(
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
    
    @staticmethod
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


NAMES = {
  name: cls
  for cls in (i for i in globals().values() if hasattr(i, 'expanded'))
  for name in getattr(cls, 'name', [cls.__name__.lower()])
  }
GOLLY_SYMS = {
  # tuples sorted in order of expansion amount (listing it as well)
  oneDimensional: ((Permute, 2), (NoSymmetry, 1)),
  vonNeumann: ((Permute, 24), (Rotate4Reflect, 8), (Rotate4, 4), (ReflectHorizontal, 2), (NoSymmetry, 1)),
  hexagonal: ((Permute, 720), (Rotate6Reflect, 12), (Rotate6, 6), (Rotate3, 3), (Rotate2, 2), (NoSymmetry, 1)),
  Moore: ((Permute, 40320), (Rotate8Reflect, 16), (Rotate8, 8), (Rotate4Reflect, 8), (Rotate4, 4), (ReflectHorizontal, 2), (NoSymmetry, 1))
  }
