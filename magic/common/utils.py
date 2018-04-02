import re
from math import ceil

from . import classes

rSHORTHAND = re.compile(r'(\d+\s*\.\.\s*\d+)\s+(.+)')


def conv_permute(tr: str, total: int):
    """
    Given a new-style permutationally-symmetric transition:
        total=8 (Moore neighborhood)
        -------
        1,0
        1:4,0:4
        1:4,0
        1:3,1,0,0
    Return its old-style representation:
        1,1,1,1,0,0,0,0
    Order is not preserved.
    """
    if isinstance(tr, str):
        tr = tr.split(',')
    # Balance unspecified values
    seq = [i.partition(':')[::2] for i in map(str.strip, tr)]
    # How many cells filled
    tally = total - sum(int(i) for _, i in seq if i)
    # And how many empty slots left to fill
    empties = sum(1 for _, i in seq if not i)
    # filler algo courtesy of Thomas Russell on math.stackexchange
    # https://math.stackexchange.com/a/1081084
    filler = (ceil((tally-k+1)/empties) for k in range(1, 1+empties))
    gen = ((st, num or str(next(filler))) for st, num in seq)
    return ','.join(classes.AdditiveDict(gen).expand())


def bind_vars(tr: (list, tuple)):
    """
    Given an unbound ruel transition like the following:
        a,1,2,[0],a,a,6,7,8,[4]
    Bind its variables in Golly style:
        a_0,1,2,a_0,a_1,a_2,6,7,8,a_1
    """
    built = []
    seen = {}
    for v in tr:
        if v.isdigit():
            built.append(v)
        elif v.startswith('['):
            v = v[1:-1]  # strip brackets
            ref = v.split(':')[0].strip()
            try:
                built.append(
                  (built[int(ref)], v[1+v.find(':'):].strip())
                  if ':' in v else
                  built[int(ref)]
                  )
            except IndexError:
                raise ValueError(f"Variable binding '{v}' does not refer to a previous index") from None
            except ValueError:
                raise SyntaxError(f"Invalid attempted variable binding '{v}'") from None
        else:
            seen[v] = 1 + seen.get(v, -1)
            built.append(f'{v}_{seen[v]}')
    return built


def expand_tr(tr: (list, ..., tuple)):
    """
    Given a transition like
      foo, 1..3 bar, baz, 5..8 wutz, kieu
    Expand into this.
      foo, bar, bar, bar, baz, wutz, wutz, wutz, kieu
    
    Also expand
      0, 1..4 [a], 1
    Into this.
      0, a, [1], [1], [1], 1
    """
    cop = {}
    for state in map(str.strip, tr):
        match = rSHORTHAND.match(state)
        if not match:
            continue
        shand, val = match[1], match[2]
        # same as used in parser.py
        span = range(*(off+int(v.strip()) for off, v in enumerate(shand.split('..'))))
        if val.startswith('['):
            start, *rest = span
            cop[start] = val
            for i in span:
                cop[i] = f'[{start}]'
        else:
            for i in span:
                cop[i] = val

