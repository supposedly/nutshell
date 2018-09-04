from importlib import import_module

from nutshell.common import symmetries as ext_symmetries
from . import _napkins as napkins

NAMES = napkins.NAMES.copy()


def find_min_sym_type(symmetries, tr_len):
    min_cls = min(symmetries, key=lambda cls: cls.sym_lens[tr_len])
    golly_cls = min_cls if not hasattr(min_cls, 'fallback') else min_cls.fallback.get(tr_len, min_cls.fallback[None])
    min_syms, min_sym_len = golly_cls.symmetries[tr_len], golly_cls.sym_lens[tr_len]
    failures = [
      napkin_set for napkin_set in
        (cls.symmetries[tr_len] for cls in symmetries if cls is not min_cls and cls is not golly_cls)
      if not all(napkin in napkin_set for napkin in min_syms)
      ]
    if failures:
        to_test = [min_syms, *failures]
        return next(
          cls
          for cls in (cls for cls, v in napkins.GOLLY_SYMS[tr_len] if v < min_sym_len)
          if all(napkin in napkin_set for napkin in cls.symmetries[tr_len] for napkin_set in to_test)
          )
    return golly_cls


def get_sym_type(sym):
    if sym not in NAMES:
        name, clsname = sym.rsplit('.', 1)
        module = ext_symmetries if name == 'nutshell' else import_module(name.lstrip('_'))
        NAMES[sym] = getattr(module, clsname)
    return NAMES[sym]
