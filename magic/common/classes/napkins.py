from abc import ABCMeta, abstractmethod
from itertools import permutations

NoSymmetry = tuple


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
        self._hash = None
    
    def __eq__(self, other):
        return isinstance(other, tuple) and any(i == other for i in self._expanded)
    
    def __hash__(self):
        if self._hash is None:
            self._hash = hash(tuple(self._expanded))
        return self._hash
    
    def __repr__(self):
        return f'{type(self).__name__}({super().__repr__()})'
    
    @LazyProperty
    def permute(self):
        return tuple(map(type(self), self._permute))
    
    @property
    def _permute(self):
        return permutations(sorted(self))
    
    @staticmethod
    def reflect(seq):
        return tuple(sorted((seq, (seq[0], *reversed(seq[1:])))))

    def _rotate(self, i):
        return self[i:]+self[:i]

    def expand(self):
        return map(type(self), self._expanded)

    def rotate4(self):
        return tuple(sorted(map(self._rotate, range(0, 8, 2))))
    
    def rotate8(self):
        return tuple(sorted(map(self._rotate, range(8))))
    

class ReflectHorizontal(Napkin):
    def __init__(self, iterable):
        super().__init__(iterable)
    
    @property
    def _expanded(self):
        return Napkin.reflect(tuple(self))


class Rotate4(Napkin):
    def __init__(self, iterable):
        super().__init__(iterable)
    
    @property
    def _expanded(self):
        return self.rotate4()


class Rotate4Reflect(Napkin):
    def __init__(self, iterable):
        super().__init__(iterable)
    
    @property
    def _expanded(self):
        return (tup for i in self.rotate4() for tup in Napkin.reflect(i))


class Rotate8(Napkin):
    def __init__(self, iterable):
        super().__init__(iterable)
    
    @property
    def _expanded(self):
        return (self.rotate8())


class Rotate8Reflect(Napkin):
    def __init__(self, iterable):
        super().__init__(iterable)
    
    @property
    def _expanded(self):
        return (tup for i in self.rotate8() for tup in Napkin.reflect(i))


class Permute(Napkin):
    def __init__(self, iterable):
        super().__init__(iterable)
    
    @property
    def _expanded(self):
        return self._permute
