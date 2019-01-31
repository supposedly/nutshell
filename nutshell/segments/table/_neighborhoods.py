from collections import OrderedDict
from functools import partial
from itertools import takewhile, permutations

from bidict import bidict

from nutshell.common.utils import LazyProperty
from ._classes import Coord
from ._errors import NeighborhoodError

NBHD_SETS = OrderedDict(
  # for containment-checking
  oneDimensional=frozenset({'E', 'W'}),
  vonNeumann=frozenset({'N', 'E', 'S', 'W'}),
  hexagonal=frozenset({'N', 'E', 'SE', 'S', 'W', 'NW'}),
  Moore=frozenset({'N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'}),
)

ORDERED_NBHDS = {
  'oneDimensional': ('E', 'W'),
  'vonNeumann': ('N', 'E', 'S', 'W'),
  'hexagonal': ('N', 'E', 'SE', 'S', 'W', 'NW'),
  'Moore': ('N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'),
}


class Neighborhood:
    GOLLY_NBHDS = bidict({
      'oneDimensional': ('W', 'E'),
      'vonNeumann': ('N', 'E', 'S', 'W'),
      'hexagonal': ('N', 'E', 'SE', 'S', 'W', 'NW'),
      'Moore': ('N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW')
    })
    
    def __init__(self, cdirs):
        if isinstance(cdirs, str):
            cdirs = self.__class__.GOLLY_NBHDS[cdirs]
        self.cdirs = tuple(cdirs)
    
    @LazyProperty
    def coord_cdirs(self):
        return tuple(map(Coord.from_name, self.cdirs))
    
    @LazyProperty
    def _inv(self):
        return dict(enumerate(self.cdirs, 1))
    
    @LazyProperty
    def idxes(self):
        return {v: k for k, v in self._inv.items()}
    
    @LazyProperty
    def is_golly_nbhd(self):
        return self.cdirs in self.__class__.GOLLY_NBHDS.inv
    
    @LazyProperty
    def _gollyizers(self):
        return {}
    
    def __contains__(self, item):
        return item in self.idxes
    
    def __getitem__(self, item):
        return self.idxes[item]
    
    def __iter__(self):
        yield from self.cdirs
    
    def __len__(self):
        return len(self.cdirs)
    
    def __repr__(self):
        return f'Neighborhood({self.cdirs!r})'
    
    def __str__(self):
        return '\n'.join(map(' '.join, self.to_list()))
    
    def __eq__(self, other):
        if isinstance(other, tuple):
            return self.cdirs.__eq__(other)
        if isinstance(other, Neighborhood):
            return self.cdirs.__eq__(other.cdirs)
        return NotImplemented
    
    def __hash__(self):
        return self.cdirs.__hash__()
    
    def get(self, item, default=None):
        return self.idxes.get(item, default)
    
    def items(self):
        return self.idxes.items()
    
    def to_list(self, blank='.'):
        return [[str(self.get(cdir, blank)) for cdir in row] for row in (('NW', 'N', 'NE'), ('W', 'C', 'E'), ('SW', 'S', 'SE'))]
    
    def cdir_at(self, idx):
        if idx < 1:  # like negative access on python sequences
            return self._inv[len(self) + idx]
        return self._inv[idx]
    
    def converter_to(self, other):
        _golly_nbhds_inv = self.__class__.GOLLY_NBHDS.inv
        if other not in self._gollyizers:
            self._gollyizers[other] = (
              get_gollyizer(self, other, golly_nbhd=_golly_nbhds_inv[other.cdirs])
              if other.cdirs in _golly_nbhds_inv
              else get_gollyizer(self, other)
            )
        return self._gollyizers[other]
    
    def supports_transformations(self, transformations):
        for method, *args in transformations:
            if method == 'rotations_by':
                amt, = args
                if len(self) % int(amt):
                    return False
            if method == 'reflections_across':
                try:
                    self.reflect_across(*args)
                except Exception:
                    return False
            # 'permute' -> True
        return True
    
    def supports(self, sym_type):
        return self.supports_transformations(sym_type.transformations)
    
    def reflect_across(self, endpoint, *, as_cls=True):
        if not isinstance(endpoint, tuple):
            raise TypeError('Endpoint of line of reflection should be given as tuple of compass directions')
        a, b = endpoint
        if isinstance(a, str):
            a = Coord.from_name(a)
        if isinstance(b, str):
            b = Coord.from_name(b)
        if a != b and a.cw(1) != b:
            raise ValueError('Endpoint compass directions of a line of reflection must be both adjacent and given in clockwise order')
        to_check = [cdir for cdir in self.coord_cdirs if cdir not in {a, b, a.inv, b.inv}]
        if len(to_check) % 2 or any(c.inv.name not in self for c in to_check):
            raise NeighborhoodError('Neighborhood is asymmetrical across the requested line of reflection')
        if a == b:
            # i think the naive approach is the only way to go :(
            while a.name not in self:
                a = a.ccw(1)
            while b.name not in self:
                b = b.cw(1)
        d = {}
        try:
            for cdir in self.coord_cdirs:
                d[cdir.name] = a.cw(b.ccw_distance(cdir, self), self).name
        except KeyError as e:
            raise NeighborhoodError(f'Neighborhood does not contain {e}')
        r = {cdir: self[orig_cdir] for orig_cdir, cdir in d.items()}
        if as_cls:
            return Neighborhood(sorted(r, key=r.get))
        return tuple(sorted(r, key=r.get))
    
    def reflections_across(self, endpoint, *, as_cls=True):
        if as_cls:
            return (self, self.reflect_across(endpoint))
        return [self.cdirs, self.reflect_across(endpoint, as_cls=as_cls)]
    
    def rotate_by(self, offset, *, as_cls=True):
        if as_cls:
            return Neighborhood(self.cdirs[offset:] + self.cdirs[:offset])
        return self.cdirs[offset:] + self.cdirs[:offset]
    
    def rotations_by(self, amt, *, as_cls=True):
        if len(self) % amt:
            raise NeighborhoodError(f'Neighborhood cannot be rotated evenly by {amt}')
        #if not self.symmetrical:
        #    raise ValueError('Neighborhood is asymmetrical, cannot be rotated except by 1')
        return [self.rotate_by(offset, as_cls=as_cls) for offset in range(0, len(self), len(self) // amt)]
    
    def permutations(self, cdirs=None, *, as_cls=True):
        if cdirs is None:
            return [Neighborhood(i) for i in permutations(self.cdirs)] if as_cls else list(permutations(self.cdirs))
        permuted_cdirs = set(cdirs)
        cls = Neighborhood if as_cls else tuple
        return [cls(next(permute) if c in permuted_cdirs else c for c in self) for permute in map(iter, permutations(cdirs))]
    
    def identity(self, *, as_cls=True):
        if as_cls:
            return (self,)
        return (self.cdirs,)


def find_golly_neighborhood(nbhds):
    common = {cdir for nbhd in nbhds for cdir in nbhd.cdirs}
    for name, s in NBHD_SETS.items():
        if common <= s:
            return name
    raise ValueError(f'Invalid (non-Moore-subset) common neighborhood {common}')


def get_gollyizer(nbhd, other, *, golly_nbhd=None):
    nbhd_set = set(nbhd)
    if golly_nbhd is not None:
        golly_set = NBHD_SETS[golly_nbhd]
        return partial(fix, ORDERED_NBHDS[golly_nbhd], nbhd)
    for name, s in NBHD_SETS.items():
        if nbhd_set <= s:
            return partial(fix, ORDERED_NBHDS[name], nbhd)
    raise ValueError(f'Invalid (non-Moore-subset) neighborhood {nbhd_set}')


def fix(cdirs_to, nbhd_from, napkin):
    tagged_names = (f'any.{i}' for i in range(10))
    print(cdirs_to)
    print(nbhd_from)
    return [napkin[nbhd_from[i]-1] if i in nbhd_from else next(tagged_names) for i in cdirs_to]
