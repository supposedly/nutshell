from itertools import permutations, chain, repeat

from nutshell.segment_types.table._napkins import *
from .utils import LazyProperty


class ReflectVertical(Napkin):
    neighborhoods = vonNeumann, hexagonal, Moore
    fallback = NoSymmetry
    
    _rotation_amounts = {vonNeumann: 1, hexagonal: 4, Moore: 3}  # these values seem to be arbitrary, dunno
    
    @property
    def expanded(self):
        return tuple(self), self.rotate_by(self._rotation_amounts[len(self)])[::-1]


class Rotate2(OrthNapkin):
    """
    Rotate2 allowing Moore and vonNeumann (and 1D, but...).
    """
    neighborhoods = range(2, 9)  # neighborhood of size 1 can't be rotated by 2
    fallback = {Any: NoSymmetry, hexagonal: Rotate2}  # the Rotate2 is Golly's, not this one
    
    @property
    def expanded(self):
        return sorted(self.rotate(2))


class AlternatingPermute(Permute):
    """
    Permutational symmetry, but only between cells perpendicular to one
    another in the Moore neighborhood. (both orthogonal and diag cells)
    e.g. `0,1,2,3,4,5,6,7` is "symmetric" to `2,5,0,1,4,7,6,3`

    More specifically, this is permutational symmetry between two groups
    of cells, one group being every second cell in a napkin and the other
    the rest.
    
    In vonNeumann neighborhood, permutes between opposing cells.
    """
    RECENTS = {}
    HASHES = {}
    neighborhoods = Any
    fallback = {Any: Rotate4Reflect, hexagonal: NoSymmetry}
    
    @LazyProperty
    def expanded(self):
        t = orth, diag = map(tuple, map(sorted, (self[::2], self[1::2])))
        if t in self.RECENTS:
            self._hash = self.HASHES[t]
            return self.RECENTS[t]
        self.RECENTS[t] = ret = [tuple(chain.from_iterable(zip(i, j))) for i in permutations(orth) for j in permutations(diag)]
        self.HASHES[t] = self._hash = hash(tuple(sorted(ret)))
        return ret
    
    @staticmethod
    def special(values, length):
        permute_sp, length = Permute.special, length // 2
        orth, diag = values[::2], values[1::2]
        return chain.from_iterable(zip(permute_sp(orth, length), permute_sp(diag, length)))
