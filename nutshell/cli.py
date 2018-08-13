from ergo import CLI, Group

DEFAULT_HEADER = '''\
********************************
**** COMPILED FROM NUTSHELL ****
********************************\
'''

cli = CLI("A transpiler from the 'Nutshell' rule-table format to Golly's", default_command='transpile')
transpile = cli.command('transpile', XOR='preview|transpile', OR='not nothing')
preview = cli.command('preview', XOR='preview|transpile', OR='not nothing')
transpile.main_grp = Group(XOR='find|normal')


@cli.clump(XOR='verbose|quiet')
@cli.flag('verbosity', namespace={'count': 0}, default=0)
def verbose(nsp):
    """Repeat for more verbosity; max x4"""
    if nsp.count < 4:
        nsp.count += 1
    return nsp.count


@cli.clump(XOR='verbose|quiet')
@cli.flag(default=False)
def quiet():
    return True


@transpile.main_grp.clump(AND='infiles|outdirs')
@transpile.arg()
def infiles(path: str.split):
    """
    Nutshell-formatted input file(s)
    Separate different files with a space, and use - (no more than once) for stdin.
    If you have a file in the current directory named -, use ./- instead.
    """
    if '-' in path:
        hyphen_idx = 1 + path.index('-')
        return path[:hyphen_idx] + [i for i in path[hyphen_idx:] if i != '-']
    return path


@transpile.clump(OR='preview|normal')
@transpile.main_grp.clump(AND='infiles|outdirs')
@transpile.main_grp.arg()
def outdirs(path: str.split):
    """
    Directory/ies to create output file in
    Separate dirnames with a space, and use - (no more than once) for stdout.
    If you have a directory under the current one named -, use -/ instead.
    """
    if '-' in path:
        hyphen_idx = 1 + path.index('-')
        return path[:hyphen_idx] + [i for i in path[hyphen_idx:] if i != '-']
    return path


@transpile.main_grp.flag(short='t', default=DEFAULT_HEADER)
def header(text=''):
    """Change or hide 'COMPILED FROM NUTSHELL' header"""
    return text or DEFAULT_HEADER


@transpile.main_grp.flag(short='s', default=False)
def comment_src():
    """Comment each tabel source line above the final table line(s) it transpiles to"""
    return True


@transpile.clump(XOR='find|preview|normal')
@transpile.flag(short='f', default=None)
def find(transition):
    """Locate first transition in `infile` that matches"""
    return tuple(s if s == '*' else int(s) for s in map(str.strip, transition.split(',')))


@preview.arg(required=True)
def transition(tr):
    """nutshell-formatted transition to preview"""
    return tr


@preview.flag(short='n', default='Moore')
def neighborhood(value):
    """Neighborhood to consider transition part of"""
    if value.replace(' ', '') not in ('Moore', 'vonNeumann', 'hexagonal'):
        raise ValueError("Invalid preview-transition neighborhood (must be one of 'Moore', 'vonNeumann', 'hexagonal')")
    return value


@preview.flag(short='o', default='?')
def states(num):
    """Number of states to include in transition (default: guess)"""
    if not num.isdigit() and num != '?':
        raise ValueError('Preview n_states must be ? or an integer')
    return str(num)


ARGS = cli.parse(strict=True, require_main=4, systemexit=False)
