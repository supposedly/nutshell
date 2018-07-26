_VERBOSITY = 0  # modified by ../../to_ruletable.py because I'm not sure how else to handle changing these vars
_QUIET = False  # (if I instead `from cli import ARGS` and use ARGS.verbosity/.quiet, it'll fail when some dependent file is imported outside of the CLI)
RAND_SEED = 83_523


def _printv(*stuff, pre='  ', **kwargs):
    """
    val: Thing to print.
    pre: What to prepend to val on print.
    **kwargs: Passed to printq()
    """
    for val in filter(None, stuff):
        printq(*(f'{pre}{i}' for i in (val if type(val) is list else [val])), **kwargs)


def printv(*args, start='\n', end=None, accum=True, **kwargs):
    """
    *args: Things to print, ordered by level of verbosity. Group items using a list.
    start: What to print before anything else.
    accum: Whether to print everything up to _VERBOSITY or just the item at _VERBOSITY
    **kwargs: Passed to _printv()
    """
    if not _VERBOSITY:
        return
    if any(args[:_VERBOSITY]):
        printq(start, end='')
    if accum:
        _printv(*args[:_VERBOSITY-1], **kwargs)
    try:
        _printv(args[_VERBOSITY-1], end=end, **kwargs)
    except IndexError:
        pass


def printq(*args, **kwargs):
    if _QUIET:
        return
    print(*args, **kwargs)