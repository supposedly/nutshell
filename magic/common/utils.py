"""Utility functions to be used during rueltabel parsing."""
import re
import json
import pprint
from math import ceil

from . import classes

rSHORTHAND = re.compile(r'(\d+\s*\.\.\s*\d+)\s+(.+)')
rRANGE = re.compile(r'\d\s*\.\.\s*\d?')
rSEGMENT = re.compile(
  r'(?:([0-8](?:\s*\.\.\s*[0-8])?)\s+)?(-?-?\d+|-?-?(?:[({](?:\w*\s*(?:,|\.\.)\s*)*\w+[})]|\[?[A-Za-z]+]?)|\[[0-8]]|\[(?:[0-8]\s*:\s*)?(?:[({](?:\w*\s*(?:,|\.\.)\s*)*(?:\w|(?:\.\.\.)?)*[})]|[A-Za-z]+)])(?:-(?:(?:\d+|(?:[({](?:\w*\s*(?:,|\.\.)\s*)*\w+[})]|[A-Za-z]+)|)))?(?::([1-8]))?'
  )
rBINDING = re.compile(r'\[(\d+)')
rALREADY = re.compile(r'(.+)_(\d+)$')

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
    # Balance unspecified values
    seq = [(match[2], match[3]) for match in rSEGMENT.finditer(tr)]
    start, end = seq.pop(0), seq.pop(-1)
    # How many cells filled
    tally = total - sum(int(i) for _, i in seq if i)
    # And how many empty slots left to fill
    empties = sum(1 for _, i in seq if not i)
    # filler algo courtesy of Thomas Russell on math.stackexchange
    # https://math.stackexchange.com/a/1081084
    filler = (ceil((tally-k+1)/empties) for k in range(1, 1+empties))
    gen = ((st, num or str(next(filler))) for st, num in seq)
    return f"{start[0]},{','.join(classes.AdditiveDict(gen).expand())},{end[0]}"


def _unbind(name):
    """
    Quick & dirty. 'foo_342' -> 'foo', and '__all__0' -> '__all__'
    """
    return '__all__' if name.startswith('__all__') else name.rsplit('_', 1)[0]


def bind_vars(tr: (list, tuple), *, second_pass=False):
    """
    Given an unbound ruel transition like the following:
        a,1,2,[0],a,a,6,7,8,[4]
    Bind its variables in Golly style:
        a_0,1,2,a_0,a_1,a_2,6,7,8,a_1
    Also resolve mappings into Python tuples.
    """
    seen, built = {}, []
    if second_pass:  # Find current numbers before adding more
        for state in tr:
            try:
                m = rALREADY.match(state)
                seen[m[1]] = int(m[2])
            except TypeError:
                continue
    for state in tr:
        if not isinstance(state, str) or state.isdigit() or rALREADY.match(state):
            built.append(state)
        elif state.startswith('['):
            val = state[1:-1]  # strip brackets
            try:
                ref = int(val.split(':')[0].strip())
            except ValueError:
                raise SyntaxError(f"Invalid attempted variable binding '{val}'")
            try:
                built.append(
                  (ref, _unbind(built[ref]), val[1+val.find(':'):].strip())
                  if ':' in val else
                  built[ref]
                  )
            except IndexError:
                raise ValueError(f"Binding in '{val}' does not refer to a previous index")
        else:
            seen[state] = 1 + seen.get(state, -1)
            built.append(f"{state}{'' if state.endswith('_') else '_'}{seen[state]}")
    return seen, built


def unbind_vars(tr: (list, tuple), bind=True):
    """Inverse of bind_vars(), ish, and w/o mapping-handling."""
    seen, built = {}, []
    for idx, state in enumerate(tr):
        if state in seen and bind:
            built.append(f'{seen[state]}')
        else:
            built.append(_unbind(state) if isinstance(state, str) else state)
            seen[state] = idx
    return built

def expand_tr(tr: (list, tuple)):
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
        match = rSEGMENT.fullmatch(val)
        if match is None:
            idx += 1
            cop.append(val)
            continue
        group, state = match[1], match[2]
        if group is None or not rRANGE.fullmatch(group):
            idx += 1
            cop.append(state)
            continue
        lower, upper = classes.TabelRange.bounds(group)
        if lower != idx:
            raise ValueError(group, state, {'lower': lower, 'idx': idx})
        span = upper - lower
        if all((state.startswith('['), ':' not in state, state[1:-1].isalpha())):  # if it's a binding with a var name inside
            group = [state[1:-1]]
            group.extend(f'[{idx}]' for _ in range(1, span))
        else:
            group = [state] * span
        idx += span
        cop.extend(group)
    return cop


def of(tr, idx):
    """
    Acts like tr[idx], but accounts for that the item
    at that index might be a binding reference to a previous
    index.
    XXX: Maybe put this in parser.py or something who knows
    """
    val = tr[idx]
    if not isinstance(val, str):
        return val
    while isinstance(val, str) and val.startswith('['):
        val = tr[int(rBINDING.match(val)[1])]
    return val


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
    return start >= match.start() and (end == len(string) or globalmatch(regex, string, end))


def _vprint(val, *, pre='  ', **kwargs):
    """
    val: Thing to print.
    pre: What to prepend to val on print.
    **kwargs: Passed to print()
    """
    if val is not None:
        print(*(f'{pre}{i}' for i in (val if type(val) is list else [val])), **kwargs)


def print_verbose(*args, start='\n', end=None, accum=True, **kwargs):
    """
    *args: Things to print, ordered by level of verbosity. Group items using a list.
    start: What to print before anything else.
    accum: Whether to print everything up to VERBOSITY or just the item at VERBOSITY
    **kwargs: Passed to _vprint()
    """
    if not VERBOSITY:
        return
    if any(args[:VERBOSITY]):
        print(start, end='')
    if accum:
        for val in args[:VERBOSITY-1]:
            _vprint(val, **kwargs)
    try:
        _vprint(args[VERBOSITY-1], end=end, **kwargs)
    except IndexError:
        pass
