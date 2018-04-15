"""Utility functions to be used during rueltabel parsing."""
import re
import json
import pprint
from math import ceil

from . import classes

rSHORTHAND = re.compile(r'(\d+\s*\.\.\s*\d+)\s+(.+)')
rRANGE = re.compile(r'\d+? *?\.\. *?\d+?')

VERBOSITY = 0


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
    cop, idx = [], 0
    for val in tr:
        if not rRANGE.match(val):
            idx += 1
            cop.append(val)
            continue
        group, state = val.split()
        lower, upper = classes.TabelRange.bounds(group)
        if lower != idx:
            raise ValueError({'lower': lower, 'idx': idx})
        span = upper - lower
        if state.startswith('['):
            group = [state[1:-1]]
            group.extend(f'[{idx}]' for _ in range(span))
        else:
            group = [state] * span
        idx += span
        cop.extend(group)
    return cop


def globalmatch(regex: re.compile, string: str, start: int = 0) -> bool:
    """
    regex: a regex object
    string: a string to match
    start: starting position for regex
    
    Determines whether regex, when applied globally, covers *every*
    character in string.
    Differs from re.fullmatch in that it checks for more than one
    recursively-applied iteration of the regex.
    
    return: whether every character in string is covered by regex
    """
    match = regex.search(string, pos=start)
    try:
        end = match.end()
    except AttributeError:  # match == None
        return False
    return end == len(string) or start == match.start() and globalmatch(regex, string, end)


def _vprint(val, *, pre='  ', **kwargs):
    """
    val: Thing to print.
    pre: What to prepend to val on print.
    **kwargs: Passed to print()
    """
    if val is not None:
        val = [f'{pre}{i}' for i in (val if type(val) is list else [val])]
        print(*val, **kwargs)


def print_verbose(*args, start='\n', end=None, accum=True, **kwargs):
    """
    *args: Things to print, ordered by level of verbosity. Group items using a list.
    start: What to print before anything else.
    accum: Whether to print everything up to VERBOSITY or just the thing at VERBOSITY
    **kwargs: Passed to _vprint()
    """
    print(start, end='')
    if accum:
        for val in args[:VERBOSITY-1]:
            _vprint(val, **kwargs)
    _vprint(args[VERBOSITY-1], end=end, **kwargs)
