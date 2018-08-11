from importlib import import_module

from magic.common import utils, napkins as ext_napkins
from . import _napkins as napkins


def _clearables(sym_clses):
    clearables = [cls for cls in sym_clses if callable(getattr(cls, 'clear', None))]
    def clear():
        for cls in clearables:
            cls.clear()
    return clear


def get_symmetry(sym):
    try:
        return napkins.NAMES[sym]
    except KeyError:
        pass
    name, cls = sym.rsplit('.', 1)
    module = ext_napkins if name == 'nutshell' else import_module(name)
    return getattr(module, cls)


def desym(transitions, sym_lines, nondefault_symmetry=False):
    """
    Normalize symmetries if a table has multiple.
    """
    if len(sym_lines) < 2:
        # if it's a non-standard/non-golly symmetry, assume it must have a golly-symmetry fallback defined
        if not sym_lines or not hasattr(get_symmetry(sym_lines[0][1]), 'fallback'):
            return transitions, sym_lines[0][1]
    utils.printq('Complete!\n\nNormalizing symmetries...')
    sym_clses = [(sym, get_symmetry(sym)) for _, sym in sym_lines]
    clear_caches = _clearables(sym_clses)
    
    lowest_sym, lowest_sym_cls = min(sym_clses, key=lambda sym__cls: sym__cls[1].order)
    if hasattr(lowest_sym_cls, 'fallback'):
        lowest_sym_cls = lowest_sym_cls.fallback
        lowest_sym = getattr(lowest_sym_cls, 'name', [lowest_sym_cls.__name__.lower()])[0]
    utils.printv(f'lowest symmetry: {lowest_sym}\n')
    
    built = []
    for sym_idx, (after, cur_sym) in enumerate(sym_lines):
        try:
            before = sym_lines[1+sym_idx][0]
        except IndexError:
            before = 1 + transitions[-1][0]
        cur_sym_cls = get_symmetry(cur_sym)
        trs = [tr for tr in transitions if after < tr[0] < before]
        utils.printv(
            f'...{cur_sym}...',
            None,
            [f'after: line {after}', f'before: line {before}'],
            trs,
            accum=True, end='\n\n', start='', sep='\n'
            )
        if cur_sym_cls is lowest_sym_cls:
            built.extend(trs)
            continue
        for lno, tr in trs:
            cur = cur_sym_cls(map(str, tr[1:-1]))
            utils.printv(None, ['converting...', f'  {cur}', f'...to {lowest_sym}'], sep='\n', start='\n', end='\n\n')
            expanded = set(map(lowest_sym_cls, cur.expand()))
            utils.printv(None, None, f'(1 transition -> {len(expanded)} transitions)\n', start='\n')
            built.extend((lno, [tr[0], *new_tr, tr[-1]]) for new_tr in expanded)
        clear_caches()
    
    utils.printv([f'FROM {len(transitions)} original transitions\n', f'\bTO {len(built)} transitions total\n'], start='')
    return built, lowest_sym
