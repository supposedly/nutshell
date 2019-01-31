from itertools import chain, zip_longest as zipln
from random import Random
from string import whitespace

from nutshell.cli import cli

RAND_SEED = 83_523
random = Random(RAND_SEED)

KILL_WS = str.maketrans('', '', whitespace)


class LazyProperty:
    """
    Allows definition of properties calculated once and once only.
    From user Cyclone on StackOverflow & modified slightly
    """
    def __init__(self, func):
        self.func = func
    
    def __get__(self, obj, cls):
        if obj is None:
            return self
        ret = self.func(obj)
        setattr(obj, self.func.__name__, ret)
        return ret


def _printv(*stuff, pre='  ', **kwargs):
    """
    val: Thing to print.
    pre: What to prepend to val on print.
    **kwargs: Passed to printq()
    """
    for val in filter(None.__ne__, stuff):
        printq(*(f'{pre}{i}' for i in (val if type(val) is list else [val])), **kwargs)


def printv(*args, start='\n', end=None, accum=True, **kwargs):
    """
    *args: Things to print, ordered by level of verbosity. Group items using a list.
    start: What to print before anything else.
    accum: Whether to print everything up to VERBOSITY or just the item at VERBOSITY
    **kwargs: Passed to _printv()
    """
    if not cli.result.verbosity:
        return
    if any(args[:cli.result.verbosity]):
        printq(start, end='')
    if accum:
        _printv(*args[:cli.result.verbosity-1], **kwargs)
    try:
        _printv(args[cli.result.verbosity-1], end=end, **kwargs)
    except IndexError:
        pass


def printq(*args, **kwargs):
    if cli.result.quiet:
        return
    print(*args, **kwargs)


def multisplit(string, delims, *, amounts=(), filter_bool=True):
    """
    string: string to split
    delims: delimiters to split on
    amounts: what to pass to second arg of str.split() for
      each given delimiter
    filter_bool: whether to filter out strings that
      don't pass a filter(bool, ...) check
    return: split string
    
    Split a string on more than one delimiter simultaneously.
    """
    ret = [string]
    for delim, amount in zipln(delims, amounts, fillvalue=-1):
        ret = [j for i in ret for j in i.split(delim, amount)]
    if filter_bool:
        return [i for i in ret if i]
    return ret


def distinct(iterable):
    seen = set()
    record = seen.add  # minor speed thing
    for i in iterable:
        if i not in seen:
            record(i)
            yield i
