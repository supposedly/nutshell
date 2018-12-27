from itertools import takewhile, permutations
from ._classes import Coord

NBHD_SETS = (
  # for containment-checking
  (frozenset({'E', 'W'}), 'oneDimensional'),
  (frozenset({'N', 'E', 'S', 'W'}), 'vonNeumann'),
  (frozenset({'N', 'E', 'SE', 'S', 'W', 'NW'}), 'hexagonal'),
  (frozenset({'N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'}), 'Moore'),
)

ORDERED_NBHDS = {
  'oneDimensional': ('E', 'W'),
  'vonNeumann': ('N', 'E', 'S', 'W'),
  'hexagonal': ('N', 'E', 'SE', 'S', 'W', 'NW'),
  'Moore': ('N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'),
}


class Neighborhood:
    GOLLY_NBHDS = {
      'oneDimensional': ('W', 'E'),
      'vonNeumann': ('N', 'E', 'S', 'W'),
      'hexagonal': ('N', 'E', 'SE', 'S', 'W', 'NW'),
      'Moore': ('N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW')
    }
    
    def __init__(self, cdirs):
        if isinstance(cdirs, str):
            cdirs = self.GOLLY_NBHDS[cdirs]
        self.cdirs = tuple(cdirs)
        self.coord_cdirs = tuple(map(Coord.from_name, cdirs))
        self._inv = dict(enumerate(cdirs, 1))
        self.idxes = {v: k for k, v in self._inv.items()}
        self.symmetrical = all(c.inv.name in self for c in self.coord_cdirs)
    
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
    
    def to_list(self, blank='.'):
        return [[str(self.get(cdir, blank)) for cdir in row] for row in (('NW', 'N', 'NE'), ('W', 'C', 'E'), ('SW', 'S', 'SE'))]
    
    def cdir_at(self, idx):
        if idx < 1:  # like negative access on python sequences
            return self._inv[len(self) + idx]
        return self._inv[idx]
    
    def gollyizer_for(self, tbl):
        return get_gollyizer(tbl, self.cdirs)
    
    def supports(self, sym_type):
        for method, *args in sym_type.transformations:
            if method == 'rotations_by':
                amt, = args
                if len(self) % int(amt) or not self.symmetrical:
                    return False
            if method == 'reflections_across':
                try:
                    self.reflect_across(*args)
                except Exception:
                    return False
            # if method == 'permute':
            #     True
        return True
    
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
            raise ValueError('Neighborhood is asymmetrical across the requested line of reflection')
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
            raise ValueError(f'Neighborhood does not contain {e}')
        r = {cdir: self[orig_cdir] for orig_cdir, cdir in d.items()}
        if as_cls:
            return Neighborhood(sorted(r, key=r.get))
        return tuple(sorted(r, key=r.get))
    
    def reflections_across(self, endpoint, as_cls):
        if as_cls:
            return (self, self.reflect_across(endpoint))
        return [self.cdirs, self.reflect_across(endpoint, as_cls=as_cls)]
    
    def rotate_by(self, offset, *, as_cls=True):
        if as_cls:
            return Neighborhood(self.cdirs[offset:] + self.cdirs[:offset])
        return self.cdirs[offset:] + self.cdirs[:offset]
    
    def rotations_by(self, amt, *, as_cls=True):
        if len(self) % amt:
            raise ValueError(f'Neighborhood cannot be rotated evenly by {amt}')
        if not self.symmetrical:
            raise ValueError('Neighborhood is asymmetrical, cannot be rotated except by 1')
        return [self.rotate_by(offset, as_cls=as_cls) for offset in range(0, len(self), len(self) // amt)]
    
    def permutations(self, cdirs=None, *, as_cls=True):
        if cdirs is None:
            return [Neighborhood(i) for i in permutations(self.cdirs)] if as_cls else list(permutations(self.cdirs))
        permuted_cdirs = set(cdirs)
        cls = Neighborhood if as_cls else tuple
        return [cls(next(permute) if c in permuted_cdirs else c for c in self) for permute in map(iter, permutations(cdirs))]


def get_gollyizer(tbl, nbhd):
    nbhd_set = set(nbhd)
    for s, name in NBHD_SETS:
        if nbhd_set <= s:
            tbl.directives['neighborhood'] = name
            if nbhd_set < s:
                return fill.__get__(ORDERED_NBHDS[name])
            return lambda tbl, napkin, _anys: reorder(ORDERED_NBHDS[name], tbl, napkin)
    raise ValueError('Invalid (non-Moore-subset) neighborhood {nbhd_set}}')


def reorder(ordered_nbhd, tbl, napkin):
    cdir_at = tbl.neighborhood.cdir_at
    d = {cdir_at(k): v for k, v in enumerate(napkin, 1)}
    return [d[cdir] for cdir in ordered_nbhd]


def fill(ordered_nbhd, tbl, napkin, anys):  # anys == usages of `any`
    if isinstance(anys, int):
        anys = set(range(anys))
    cdir_at = tbl.neighborhood.cdir_at
    d = {cdir_at(k): v for k, v in enumerate(napkin, 1)}
    available_tags = [i for i in range(10) if i not in anys]
    # (ew, but grabbing VarName object)
    tbl.vars.inv[tbl.vars['any']].update_rep(
      max(anys) + len(ordered_nbhd) - len(tbl.neighborhood) - sum(takewhile(max(anys).__gt__, available_tags))
      )
    tagged_names = (f'any.{i}' for i in available_tags)
    # `or` because this needs lazy evaluation
    return [d.get(cdir) or next(tagged_names) for cdir in ordered_nbhd]
