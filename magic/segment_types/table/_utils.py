"""Utility functions to be used during nutshell parsing."""
import re
from collections import defaultdict
from itertools import count
from math import ceil

from . import _classes as classes, _napkins as napkins
from ...common.utils import printv, printq

rSHORTHAND = re.compile(r'(\d+\s*\.\.\s*\d+)\s+(.+)')
rRANGE = re.compile(r'\d+(?:\+\d+)?\s*\.\.\s*\d+')
rSEGMENT = re.compile(
  # ugh
  r'\s*(?:([0-8](?:\s*\.\.\s*[0-8])?)\s+)?(-?-?(?:[({](?:[\w\-*\s]*\s*(?:,|\.\.)\s*)*[\w\-*\s]+[})]|[\w\-]+)|\[(?:[0-8]\s*:\s*)?(?:[({](?:(?:\[?[\w\-]+]?(?:\s*\*\s*[\w\-])?|\d+(?:\+\d+)?\s*\.\.\s*\d+)*,\s*)*(?:\[?[\w\-]+]?|\d+(?:\+\d+)?\s*\.\.\s*\d+|(?:\.\.\.)?)[})]|[\w\-*\s]+)])(?:-(?:(?:\d+|(?:[({](?:[\w\-]*\s*(?:,|\.\.)\s*)*[\w\-]+[})]|[A-Za-z\-]+))))?(?:\s*\*\s*([1-8]))?'
  )
rBINDING = re.compile(r'\[(\d+)')
rALREADY = re.compile(r'(.+)_(\d+)$')
VERBOSITY = 0


class AdditiveDict(dict):
    def __init__(self, it):
        for key, val in it:
            self[str(key)] = self.get(key, 0) + int(val or 1)
    
    def __iter__(self):
        return (i for k, v in self.items() for i in [k]*v)


def conv_permute(tr: str, total: int):
    """
    Given a shorthand permutationally-symmetric transition:
        total=8 (Moore neighborhood)
        -------
        1,0
        1*4,0*4
        1*4,0
        1*3,1,0,0
    Return its expanded representation:
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
    gen = ((val, num or str(next(filler))) for val, num in seq)
    return f"{start[0]},{','.join(AdditiveDict(gen))},{end[0]}"


def suffix_num(num):
    suffix = ['th', 'st', 'nd', 'rd', *['th']*6][int(str(num)[-1])]
    return f'{num}{suffix}'


def bind_vars(tr: (list, tuple), *, second_pass=False, return_reps=True):
    """
    Given an unbound rule transition like the following:
        a,1,2,[0],a,a,6,7,8,[4]
    Bind its variables in Golly style:
        a_0,1,2,a_0,a_1,a_2,6,7,8,a_1
    Also resolve mappings into Python tuples.
    """
    seen, built = defaultdict(set), []
    if second_pass:  # Find current numbers before adding more
        for state in tr:
            try:
                m = rALREADY.match(state)
                seen[m[1]].add(int(m[2]))
            except TypeError:
                continue
    for idx, state in enumerate(tr):
        if not isinstance(state, str) or state.isdigit() or rALREADY.match(state):
            built.append(state)
        elif state.startswith('['):
            val = state[1:-1]  # strip brackets
            try:
                ref = int(val.split(':')[0].strip())
            except ValueError:
                raise SyntaxError(f"Invalid attempted variable binding '{val}'")
            try:
                while isinstance(built[ref], tuple):
                    ref = built[ref][0]
                built.append(
                  (ref, built[ref].rsplit('_', 1)[0], val[1+val.find(':'):].strip())
                  if ':' in val else
                  built[ref]
                  )
            except IndexError:
                raise ValueError(f"Binding '{state}' ({suffix_num(1+idx)} state) does not refer to a previous index")
        else:
            this_num = next(i for i in count() if i not in seen[state])
            seen[state].add(this_num)
            built.append(f"{state}{'' if state.endswith('_') else '_'}{this_num}")
    return ({k: max(v) for k, v in seen.items()}, built) if return_reps else built


def unbind_vars(tr: (list, tuple), rebind=True, bind_keep=False):
    """Inverse of bind_vars(), ish, and w/o mapping-handling."""
    seen, built = {}, []
    for idx, state in enumerate(tr):
        if state not in seen:
            built.append(state.rsplit('_', 1)[0] if isinstance(state, str) else state)
            seen[state] = idx
        elif bind_keep:
            built[seen[state]] = state
            built.append(state)
        elif rebind:
            built.append(f'{seen[state]}')
        else:
            built.append(state)
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
        lower, upper = classes.TableRange(group).bounds
        if lower != idx:
            raise ValueError(group, lower, idx)
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
    XXX: Maybe put this in a class or something who knows
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


def desym(transitions, sym_lines):
    """
    Normalize symmetries if a table has multiple.
    """
    if len(sym_lines) < 2:
        return transitions, sym_lines[0][1]
    printq('Complete!\n\nNormalizing symmetries...')
    built = []
    lowest_sym, lowest_sym_cls = min(((sym, napkins.NAMES[sym]) for _, sym in sym_lines), key=lambda sym__cls: sym__cls[1].order)
    printv(f'lowest symmetry: {lowest_sym}\n')
    for sym_idx, (after, cur_sym) in enumerate(sym_lines):
        try:
            before = sym_lines[1+sym_idx][0]
        except IndexError:
            before = 1 + transitions[-1][0]
        cur_sym_cls = napkins.NAMES[cur_sym]
        trs = [tr for tr in transitions if after < tr[0] < before]
        printv(
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
            printv(None, ['converting...', f'  {cur}', f'...to {lowest_sym}'], sep='\n', start='\n', end='\n\n')
            exp = set(map(lowest_sym_cls, cur.expand()))
            printv(None, None, f'(1 transition -> {len(exp)} transitions)\n', start='\n')
            built.extend((lno, [tr[0], *new_tr, tr[-1]]) for new_tr in exp)
        napkins.Permute.clear()
    printv([f'FROM {len(transitions)} original transitions\n', f'\bTO {len(built)} transitions total\n'], start='')
    return built, lowest_sym