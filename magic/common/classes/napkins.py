from itertools import permutations


__all__ = 'NoSymmetry', 'ReflectHorizontal', 'Rotate2', 'Rotate3', 'Rotate4', 'Rotate4Reflect', 'Rotate6', 'Rotate6Reflect', 'Rotate8', 'Rotate8Reflect', 'Permute'


class Napkin(tuple):
    """
    Term "napkin" by 83bismuth38.
    Represents the 'neighborhood' segment of a transition.
    """
    def __init__(self, iterable):
        self._hash = None
    
    def __eq__(self, other):
        return isinstance(other, tuple) and any(i == other for i in self._expanded)
    
    def __hash__(self):
        if self._hash is None:
            self._hash = hash(tuple(sorted(self._expanded)))
        return self._hash
    
    def __repr__(self):
        return f'{type(self).__name__}({super().__repr__()})'

    def _rotate(self, i):
        return self[i:]+self[:i]

    def expand(self):
        return map(type(self), self._expanded)


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
    @property
    def _expanded(self):
        return OrthNapkin.reflect(tuple(self))


class Rotate4(OrthNapkin):
    order = 2
    @property
    def _expanded(self):
        return self.rotate4()


class Rotate4Reflect(OrthNapkin):
    order = 3
    @property
    def _expanded(self):
        return (tup for i in self.rotate4() for tup in OrthNapkin.reflect(i))


class Rotate8(OrthNapkin):
    order = 4
    @property
    def _expanded(self):
        return (self.rotate8())


class Rotate8Reflect(OrthNapkin):
    order = 5
    @property
    def _expanded(self):
        return (tup for i in self.rotate8() for tup in OrthNapkin.reflect(i))


# General
class Permute(Napkin):
    order = 6
    @property
    def _expanded(self):
        return permutations(sorted(self))
