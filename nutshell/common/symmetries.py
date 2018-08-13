from itertools import permutations, chain

from nutshell.segment_types.table._napkins import *
from .utils import LazyProperty


class ReflectVertical(Napkin):
    lengths = 4, 6, 8
    fallback = NoSymmetry
    _rotation_amounts = {4: 1, 6: 4, 8: 3}  # these values seem to be arbitrary, dunno
    
    @property
    def expanded(self):
        return tuple(self), self.rotate_by(self._rotation_amounts[len(self)])[::-1]


_GollyRotate2 = Rotate2
class Rotate2(OrthNapkin):
    """
    Rotate2 allowing Moore and vonNeumann (and 1D, but...).
    """
    lengths = None
    fallback = {None: NoSymmetry, 6: _GollyRotate2}  # don't actually need that alias but it makes things clearer
    
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
    lengths = 4, 8
    fallback = Rotate4Reflect
    
    @LazyProperty
    def expanded(self):
        t = orth, diag = map(tuple, map(sorted, (self[::2], self[1::2])))
        if t in self.RECENTS:
            self._hash = self.HASHES[t]
            return self.RECENTS[t]
        self.RECENTS[t] = ret = [tuple(chain.from_iterable(zip(i, j))) for i in permutations(orth) for j in permutations(diag)]
        self.HASHES[t] = self._hash = hash(tuple(sorted(ret)))
        return ret
# Deprecation sorta thing
PermutePerpendiculars = AlternatingPermute
