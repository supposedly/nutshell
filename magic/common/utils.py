from itertools import chain
from math import ceil

import classes


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
    gen = ((st, num if num else str(next(filler))) for st, num in seq)
    return ','.join(classes.AdditiveDict(gen).expand())

def bind_vars(tr: (list, tuple)):
    """
    Given an unbound ruel transition like the following:
        a,1,2,[0],a,a,6,7,8,[4]
    Bind its variables as in Golly style:
        a_0,1,2,a_0,a_1,a_2,6,7,8,a_1
    """
    built = []
    suffix = 0
    for i, v in enumerate(tr):
        if v.isdigit():
            built.append(v)
            continue
        if v.startswith('[') and v.endswith(']'):
            try:
                built.append(built[int(v.strip('[]'))])
            except IndexError:
                raise ValueError(f"Variable binding '{v}' does not refer to a previous index")
            except ValueError:
                raise ValueError(f"Invalid attempted variable binding '{v}'")
        else:
            built.append(f'{v}_{suffix}')
            suffix += 1
    return built
