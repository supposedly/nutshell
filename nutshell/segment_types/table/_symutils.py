from importlib import import_module

from nutshell.common import symmetries as ext_symmetries, utils
from ._classes import Coord
from . import _napkins as napkins


PRESETS = {
  'rotate8reflect': lambda nbhd: compose(rotate(nbhd, 8), reflect_multiple(nbhd, 'W', 'NW', 'N', 'NE')),
  'rotate8': lambda nbhd: rotate(nbhd, 8),
  'rotate4reflect': lambda nbhd: compose(rotate(nbhd, 4), reflect_multiple(nbhd, 'W', 'N')),
  'rotate4': lambda nbhd: rotate(nbhd, 4),
  'reflect_horizontal': lambda nbhd: reflect(nbhd, 'W'),
  'reflect_vertical': lambda nbhd: reflect(nbhd, 'N'),
  'none': lambda nbhd: none(nbhd),
  ####
  'permute': lambda nbhd, *cdirs: permute(nbhd, cdirs),
  'reflect': lambda nbhd, *endpoint: reflect(nbhd, *endpoint),
  'rotate': lambda nbhd, amt: rotate(nbhd, int(amt)),
}


def find_min_sym_type(symmetries, tr_len):
    """
    Find the "minimum" common symmetry type between all given symmetries.
    For instance:
      none, permute            =>  none
      rotate8, permute         =>  rotate8
      rotate4reflect, rotate8  =>  rotate4
    The last one resolves to a wholly-different symmetry type. This is
    because rotate4reflect cannot express the fact that rotate8 does
    not include reflection, so it cannot resolve to rotate4reflect.
    
    Algorithmically, this is calculated by:
    (1) finding the symmetry type whose symmetries:none expansion (when
        all terms are unique) is the smallest
    (2) checking whether this symmetry type is comprised entirely by all
        the others
    (3) if (2), returning that minimum symmetry type, but otherwise:
    (4) finding the first Golly symmetry type that is comprised entirely
        by both the minimum symmetry type and all the rest
    """
    # Find smallest symmetries:none-expanded sym type
    # (sym_lens holds precalculated lengths of these 'none expansions')
    min_cls = min(symmetries, key=lambda cls: cls.sym_lens[tr_len])
    # If it's a custom symmetry type, use its Golly fallback
    golly_cls = min_cls if not hasattr(min_cls, 'fallback') else min_cls.fallback.get(tr_len, min_cls.fallback[None])
    min_syms, min_sym_len = golly_cls.symmetries[tr_len], golly_cls.sym_lens[tr_len]
    # All symmetry types used which do not comprise min_syms
    failures = [
      napkin_set for napkin_set in
        [c.symmetries[tr_len] for c in symmetries if min_cls is not c is not golly_cls]
      if not all(map(napkin_set.__contains__, min_syms))
      ]
    if not failures:
        return golly_cls
    to_test = [min_syms, *failures]
    # Largest Golly symmetry type that comprises both min_syms and everything else used
    return next(
      cls
      for cls, v in napkins.GOLLY_SYMS[tr_len]
      if v < min_sym_len
      and all(napkin in napkin_set for napkin in cls.symmetries[tr_len] for napkin_set in to_test)
      )


def get_sym_type(nbhd, string):
    all_syms = []
    current = []
    for token in utils.multisplit(string, (None, *'(),_')):
        if token in PRESETS:
            if current:
                all_syms.append(current)
            current = []
        current.append(token)
    all_syms.append(current)
    resultant_sym = None
    for name, *args in all_syms:
        cur_sym = PRESETS[name](nbhd, *args)
        resultant_sym = cur_sym if resultant_sym is None else compose(resultant_sym, cur_sym)
    return resultant_sym
# get_sym_type(Neighborhood(('N', 'NE', 'E', 'S', 'SW', 'W')), 'rotate(2) reflect(N, NE))').expanded
# for example


def _new_sym_type(name, expanded):
    return type(name, (list,), {
      'expanded': expanded
    })


def compose(*symmetries):
    print([i.expanded for i in symmetries])
    return _new_sym_type(
      '+'.join([s.__name__ for s in symmetries]),
      sorted({t for s in symmetries for t in s.expanded})
      )


def reflect_multiple(nbhd, *coords):
    return compose(reflect(nbhd, c) if isinstance(c, str) else reflect(nbhd, *c) for c in coords)


def reflect(nbhd, first, second=None):
    first = Coord.from_name(first)
    second = first if second is None else Coord.from_name(second)
    return _new_sym_type(
      f'Reflect_{first}_{second}',
      sorted([nbhd.cdirs, nbhd.reflect_across((first, second)).cdirs])
      )


def rotate(nbhd, n):
    return _new_sym_type(
      f'Rotate_{n}',
      sorted([i.cdirs for i in nbhd.rotations_by(int(n))])
    )


def permute(nbhd, cdirs=None):
    return _new_sym_type(
      f"Permute_{'_'.join(cdirs)}",
      sorted(nbhd.permutations(cdirs or None))
    )

def none(nbhd, cdirs=None):
    return _new_sym_type(
      f'NoSymmetry',
      [nbhd.cdirs]
    )
