from itertools import permutations
from functools import lru_cache


__all__ = 'NoSymmetry', 'ReflectHorizontal', 'Rotate2', 'Rotate3', 'Rotate4', 'Rotate4Reflect', 'Rotate6', 'Rotate6Reflect', 'Rotate8', 'Rotate8Reflect', 'Permute'


class LazyProperty:
    """
    Allows definition of properties calculated once and once only.
    From user Cyclone on StackOverflow; modified slightly to look more
    coherent for my own benefit.
    """
    def __init__(self, method):
        self.method = method
    
    def __get__(self, obj, cls):
        if not obj:
            return None
        ret = self.method(obj)
        setattr(obj, self.method.__name__, ret)
        return ret


class Napkin(tuple):
    """
    Term "napkin" by 83bismuth38.
    Represents the 'neighborhood' segment of a transition.
    """
    def __init__(self, iterable):
        self.__unique_expanded = None
        self._hash = None
    
    def __eq__(self, other):
        return isinstance(other, tuple) and any(i == other for i in self._expanded)
    
    def __hash__(self):
        if self._hash is None:
            self._hash = hash(tuple(sorted(self._expanded_unique)))
        return self._hash
    
    def __repr__(self):
        return f'{type(self).__name__}({super().__repr__()})'

    def _rotate(self, i):
        return self[i:]+self[:i]
    
    @LazyProperty
    def _expanded_unique(self):
        return set(self._expanded)

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
    order = 0
    def expand(self):
        return self,


# Hexagonal napkins
class Rotate2(HexNapkin):
    order = 1
    @property
    def _expanded(self):
        return self.rotate2()


class Rotate3(HexNapkin):
    order = 2
    @property
    def _expanded(self):
        return self.rotate3()


class Rotate6(HexNapkin):
    order = 3
    @property
    def _expanded(self):
        return self.rotate6()


class Rotate6Reflect(HexNapkin):
    order = 4
    @property
    def _expanded(self):
        return (tup for i in self.rotate6() for tup in HexNapkin.reflect(i))


# Orthogonal napkins
class ReflectHorizontal(OrthNapkin):
    order = 1
    @LazyProperty
    def _expanded(self):
        return OrthNapkin.reflect(tuple(self))


class Rotate4(OrthNapkin):
    order = 2
    @LazyProperty
    def _expanded(self):
        return self.rotate4()


class Rotate4Reflect(OrthNapkin):
    order = 3
    @property
    def _expanded(self):
        return (tup for i in self.rotate4() for tup in OrthNapkin.reflect(i))


class Rotate8(OrthNapkin):
    order = 4
    @LazyProperty
    def _expanded(self):
        return self.rotate8()


class Rotate8Reflect(OrthNapkin):
    order = 5
    @property
    def _expanded(self):
        return (tup for i in self.rotate8() for tup in OrthNapkin.reflect(i))


# General
class Permute(Napkin):
    order = 6
    RECENTS = {}
    HASHES = {}

    def __hash__(self):
        if self._hash is None:
            self._hash = self.HASHES[tuple(sorted(self))]
        return self._hash

    @LazyProperty
    def _expanded(self):
        t = tuple(sorted(self))
        if t in self.RECENTS:
            return self.RECENTS[t]
        self.RECENTS[t] = list(permutations(sorted(self)))
        self.HASHES[t] = hash(tuple(sorted(self.RECENTS[t])))
        return self.RECENTS[t]
    
    @classmethod
    def clear(cls):
        cls.RECENTS.clear()
        cls.HASHES.clear()
