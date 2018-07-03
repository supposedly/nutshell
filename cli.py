from ergo import Parser, Group


DEFAULT_HEADER = '''\
*********************************
**** COMPILED FROM RUELTABEL ****
*********************************\
'''


parser = Parser()
parser.grp_0 = Group(XOR=0)
preview = parser.command('preview', XOR=0, OR=0)


@parser.grp_0.clump(AND=0)
@parser.arg()
def infile(path):
    """rueltabel-formatted input file"""
    return path


@parser.clump(OR=0)
@parser.grp_0.clump(AND=0)
@parser.grp_0.arg()
def outdir(path):
    """Directory to create output file in"""
    return path


@parser.grp_0.flag(short='t', default=DEFAULT_HEADER)
def header(text=''):
    """Change or hide 'COMPILED FROM RUELTABEL' header"""
    return text or DEFAULT_HEADER


@parser.grp_0.flag(short='s', default=False)
def comment_src():
    """Comment each tabel source line above the final table line(s) it transpiles to"""
    return True


@parser.clump(XOR=0)
@parser.flag(short='f', default=None)
def find(transition):
    """Locate first transition in `infile` that matches"""
    return tuple(s if s == '*' else int(s) for s in map(str.strip, transition.split(',')))


@parser.clump(XOR='v')
@parser.flag('verbosity', namespace={'count': 0}, default=0)
def verbose(nsp):
    """Repeat for more verbosity; max x4"""
    if nsp.count < 4:
        nsp.count += 1
    return nsp.count


@parser.clump(XOR='v')
@parser.flag(default=False)
def quiet():
    return True


@preview.arg(required=True)
def transition(tr):
    """rueltabel-formatted transition to preview"""
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


ARGS = parser.parse(strict=True)
