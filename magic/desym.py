from magic.common.utils import print_verbose
from magic.common.classes.napkins import *


NAMES = {
  'none': NoSymmetry,
  'reflect': ReflectHorizontal,
  'reflect_horizontal': ReflectHorizontal,
  'rotate2': Rotate2,
  'rotate3': Rotate3,
  'rotate4': Rotate4,
  'rotate4reflect': Rotate4Reflect,
  'rotate6': Rotate6,
  'rotate6reflect': Rotate6Reflect,
  'rotate8': Rotate8,
  'rotate8reflect': Rotate8Reflect,
  'permute': Permute
  }


def normalize(transitions, sym_lines):
    if len(sym_lines) < 2:
        return transitions, sym_lines[0][1]
    print('Complete!\n\nNormalizing symmetries...')
    built = []
    lowest_sym, lowest_sym_cls = min(((sym, NAMES[sym]) for _, sym in sym_lines), key=lambda sym_cls: sym_cls[1].order)
    print_verbose(f'lowest symmetry: {lowest_sym}\n')
    for sym_idx, (after, cur_sym) in enumerate(sym_lines):
        try:
            before = sym_lines[1+sym_idx][0]
        except IndexError:
            before = 1 + transitions[-1][0]
        cur_sym_cls = NAMES[cur_sym]
        trs = [tr for tr in transitions if after < tr[0] < before]
        print_verbose(
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
            print_verbose(None, ['converting...', f'  {cur}', f'...to {lowest_sym}'], sep='\n', start='\n', end='\n\n')
            exp = {*map(lowest_sym_cls, cur_sym_cls(map(str, tr[1:-1])).expand())}
            print_verbose(None, None, f'(1 transition -> {len(exp)} transitions)\n', start='\n')
            built.extend((lno, [tr[0], *new_tr, tr[-1]]) for new_tr in exp)
    print_verbose([f'FROM {len(transitions)} original transitions\n', f'\bTO {len(built)} transitions total\n'], start='')
    return built, lowest_sym
