from itertools import permutations, chain

from magic.segment_types.table._napkins import *
from .utils import LazyProperty


class PermutePerpendiculars(Permute):
    """
    Permutational Moore symmetry, but only between perpendicular cells.
    (both orthogonals and diagonals)
    e.g. `0,1,2,3,4,5,6,7` is "symmetric" to `2,5,0,1,4,7,6,3`
    
    For vonNeumann symmetry, permutes between opposing cells.
    """
    RECENTS = {}
    HASHES = {}
    order = 5.5
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
