from itertools import permutations

from magic.common.utils import LazyProperty


__all__ = 'NAMES', 'NoSymmetry', 'ReflectHorizontal', 'Rotate2', 'Rotate3', 'Rotate4', 'Rotate4Reflect', 'Rotate6', 'Rotate6Reflect', 'Rotate8', 'Rotate8Reflect', 'Permute'


class Napkin(tuple):
    """
    Term "napkin" by 83bismuth38.
    Represents the 'neighborhood' segment of a transition.
    """
    def __init__(self, iterable=None):
        self.__unique_expanded = None
        self._hash = None
    
    def __eq__(self, other):
        return isinstance(other, tuple) and any(i == other for i in self.expanded)
    
    def __hash__(self):
        if self._hash is None:
            self._hash = hash(tuple(sorted(self._expanded_unique)))
        return self._hash
    
    def __repr__(self):
        return f'{type(self).__name__}({super().__repr__()})'
    
    def _rotate(self, i):
        return self[i:] + self[:i]
    
    @LazyProperty
    def _expanded_unique(self):
        return set(self.expanded)
    
    def expand(self):
        return map(type(self), self._expanded_unique)


class OrthNapkin(Napkin):
    """Moore & vonNeumann"""
    @staticmethod
    def reflect(seq):
        return sorted((seq, (seq[0], *reversed(seq[1:]))))
    
    def rotate4(self):
        # ternary is to account for Moore/vonNeumann differences
        return sorted(map(self._rotate, range(4) if len(self) < 8 else range(0, 8, 2)))
    
    def rotate8(self):
        return sorted(map(self._rotate, range(8)))


class HexNapkin(Napkin):
    @staticmethod
    def reflect(seq):
        """
        Golly devs chose to anchor reflection on upper-right cell instead of upper
        cell -- so we can't just reverse seq[1:] :(
        """
        return sorted((seq, tuple(seq[i] for i in (4, 2, 3, 1, 0, 5))))
    
    def rotate2(self):
        return sorted(map(self._rotate, range(0, 6, 3)))
    
    def rotate3(self):
        return sorted(map(self._rotate, range(0, 6, 2)))
    
    def rotate6(self):
        return sorted(map(self._rotate, range(6)))


class NoSymmetry(tuple):
    expanded = None
    name = ['none']
    order = 0
    def expand(self):
        return self,


# Hexagonal napkins
class Rotate2(HexNapkin):
    order = 1
    @property
    def expanded(self):
        return self.rotate2()


class Rotate3(HexNapkin):
    order = 2
    @property
    def expanded(self):
        return self.rotate3()


class Rotate6(HexNapkin):
    order = 3
    @property
    def expanded(self):
        return self.rotate6()


class Rotate6Reflect(HexNapkin):
    order = 4
    @property
    def expanded(self):
        return (tup for i in self.rotate6() for tup in HexNapkin.reflect(i))


# Orthogonal napkins
class ReflectHorizontal(OrthNapkin):
    name = ['reflect', 'reflect_horizontal']
    order = 1
    @LazyProperty
    def expanded(self):
        return OrthNapkin.reflect(tuple(self))


class Rotate4(OrthNapkin):
    order = 2
    @LazyProperty
    def expanded(self):
        return self.rotate4()


class Rotate4Reflect(OrthNapkin):
    order = 3
    @property
    def expanded(self):
        return (tup for i in self.rotate4() for tup in OrthNapkin.reflect(i))


class Rotate8(OrthNapkin):
    order = 4
    @LazyProperty
    def expanded(self):
        return self.rotate8()


class Rotate8Reflect(OrthNapkin):
    order = 5
    @property
    def expanded(self):
        return (tup for i in self.rotate8() for tup in OrthNapkin.reflect(i))


# General
class Permute(Napkin):
    RECENTS = {}
    HASHES = {}
    order = 6
    
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
        self.HASHES[t] = self._hash = hash(tuple(sorted(ret)))
        return ret
    
    @classmethod
    def clear(cls):
        cls.RECENTS.clear()
        cls.HASHES.clear()


NAMES = {
  name: cls
  for cls in (i for i in globals().values() if hasattr(i, 'expanded'))
  for name in getattr(cls, 'name', [cls.__name__.lower()])
  }
