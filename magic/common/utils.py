from cli import ARGS

def _vprint(*stuff, pre='  ', **kwargs):
    """
    val: Thing to print.
    pre: What to prepend to val on print.
    **kwargs: Passed to print()
    """
    for val in filter(None, stuff):
        print(*(f'{pre}{i}' for i in (val if type(val) is list else [val])), **kwargs)


def print_verbose(*args, start='\n', end=None, accum=True, **kwargs):
    """
    *args: Things to print, ordered by level of verbosity. Group items using a list.
    start: What to print before anything else.
    accum: Whether to print everything up to VERBOSITY or just the item at VERBOSITY
    **kwargs: Passed to _vprint()
    """
    if not ARGS.verbosity:
        return
    if any(args[:ARGS.verbosity]):
        print(start, end='')
    if accum:
        _vprint(*args[:ARGS.verbosity-1], **kwargs)
    try:
        _vprint(args[ARGS.verbosity-1], end=end, **kwargs)
    except IndexError:
        pass
