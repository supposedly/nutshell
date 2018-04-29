from magic.common.classes.napkins import *

NAMES = {
  'none': NoSymmetry,
  'reflect': ReflectHorizontal,
  'reflect_horizontal': ReflectHorizontal,
  'rotate4': Rotate4,
  'rotate4reflect': Rotate4Reflect,
  'rotate8': Rotate8,
  'rotate8reflect': Rotate8Reflect,
  'permute': Permute
  }

def normalize(transitions, sym_lines):
    if len(sym_lines) < 2:
        return transitions, sym_lines[0][1]
    print('Complete!\n\nExpanding symmetries...')
    built = []
    lowest_sym, lowest_sym_cls = min(((sym, NAMES[sym]) for _, sym in sym_lines), key=lambda tupl: tupl[1].order)
    for sym_idx, (after, cur_sym) in enumerate(sym_lines):
        try:
            before = sym_lines[1+sym_idx][0]
        except IndexError:
            before = 1 + transitions[-1][0]
        cur_sym_cls = NAMES[cur_sym]
        trs = [tr for tr in transitions if after < tr[0] < before]
        if cur_sym_cls is lowest_sym_cls:
            built.extend(trs)
            continue
        for lno, tr in trs:
            built.extend((lno, [tr[0], *new_tr, tr[-1]]) for new_tr in {*map(lowest_sym_cls, cur_sym_cls(map(str, tr[1:-1])).expand())})
    return built, lowest_sym
