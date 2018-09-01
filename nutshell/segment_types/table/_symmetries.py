from operator import itemgetter
from importlib import import_module

from nutshell.common import utils, symmetries as ext_symmetries
from . import _napkins as napkins

NAMES = napkins.NAMES.copy()


def _clearables(sym_clses):
    clearables = [cls for cls in sym_clses if callable(getattr(cls, 'clear', None))]
    def clear():
        for cls in clearables:
            cls.clear()
    return clear


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


def desym(transitions, sym_lines, transition_length):
    """
    Normalize symmetries if a table has multiple.
    """
    if len(sym_lines) < 2:
        # if it's a non-standard/non-golly symmetry, assume it must have a golly-symmetry fallback defined
        if not sym_lines or not hasattr(get_sym_type(sym_lines[0][1]), 'fallback'):
            return transitions, sym_lines[0][1]
    utils.printq('Complete!\n\nNormalizing symmetries...')
    sym_clses = [get_sym_type(sym) for _, sym in sym_lines]
    
    clear_caches = _clearables(sym_clses)
    min_sym_cls = find_min_sym_type(sym_clses, transition_length)
    min_sym = getattr(min_sym_cls, 'name', [min_sym_cls.__name__.lower()])[0]
    utils.printv(f'lowest symmetry: {min_sym}\n')
    
    built = []
    for sym_idx, (after, cur_sym) in enumerate(sym_lines):
        try:
            before = sym_lines[1+sym_idx][0]
        except IndexError:
            before = 1 + transitions[-1][0]
        cur_sym_cls = NAMES[cur_sym]
        trs = [tr for tr in transitions if after < tr[0] < before]
        utils.printv(
            f'...{cur_sym}...',
            None,
            [f'after: line {after}', f'before: line {before}'],
            trs,
            accum=True, end='\n\n', start='', sep='\n'
            )
        if cur_sym_cls is min_sym_cls:
            built.extend(trs)
            continue
        for lno, tr in trs:
            cur = cur_sym_cls(map(str, tr[1:-1]))
            utils.printv(None, ['converting...', f'  {cur}', f'...to {min_sym}'], sep='\n', start='\n', end='\n\n')
            expanded = set(map(min_sym_cls, cur.expand()))
            utils.printv(None, None, f'(1 transition -> {len(expanded)} transitions)\n', start='\n')
            built.extend((lno, [tr[0], *new_tr, tr[-1]]) for new_tr in expanded)
        clear_caches()
    
    utils.printv([f'FROM {len(transitions)} original transitions\n', f'\bTO {len(built)} transitions total\n'], start='')
    return built, min_sym
