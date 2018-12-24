from importlib import import_module

from nutshell.common import symmetries as ext_symmetries
from ._classes import Coord
from . import _napkins as napkins

NAMES = napkins.NAMES.copy()


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


def get_sym_type(sym):
    if sym not in NAMES:
        if '.' not in sym:
            raise ImportError(f'No symmetry type {sym!r} found')
        name, clsname = sym.rsplit('.', 1)
        module = ext_symmetries if name == 'nutshell' else import_module(name.lstrip('_'))
        NAMES[sym] = getattr(module, clsname)
    return NAMES[sym]


def compose(symmetries):
    expanded = sorted([t for s in symmetries for t in s.expanded])
    names = [s.__name__ for s in symmetries]
    return type('+'.join(names), (object,), {
      'expanded': property(lambda self: expanded)
    })


def reflect(nbhd, first, second=None):
    first = Coord.from_name(first)
    second = first if second is None else Coord.from_name(second)
    expanded = sorted([nbhd.cdirs, nbhd.reflect_across((first, second)).cdirs])
    # TODO: inherit from napkin
    return type(f'Reflect_{first}_{second}', (object,), {
      'expanded': property(lambda self: expanded),
    })


def rotate(nbhd, n):
    expanded = sorted([i.cdirs for i in nbhd.rotations_by(int(n))])
    return type(f'Rotate_{n}', (object,), {
      'expanded': property(lambda self: expanded),
    })


def permute(nbhd, cdirs=None):
    expanded = sorted(nbhd.permutations(cdirs))
    return type(f"Permute_{'_'.join(cdirs)}", (object,), {
        'expanded': property(lambda self: expanded)
    })
