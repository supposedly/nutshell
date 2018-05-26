import textwrap

from ergo import Parser


DEFAULT_HEADER = '''\
*********************************
**** COMPILED FROM RUELTABEL ****
*********************************\
'''


parser = Parser()
parser.group('grp_0', XOR=0)
preview = parser.command('preview', XOR=0)


@parser.grp_0.clump(AND=1)
@parser.arg()
def infile(path):
    """rueltabel-formatted input file"""
    return path


@parser.grp_0.clump(OR=0, AND=1)
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
@parser.flag(short='f')
def find(transition):
    """Locate first transition in `infile` that matches"""
    return tuple(int(i.strip()) for i in transition.split(','))


@parser.flag(short='v', namespace={'count': 0})
def verbose(nsp):
    """Repeat for more verbosity; max x4"""
    if nsp.count < 4:
        nsp.count += 1
    return nsp.count


@preview.arg(required=True)
def transition(tr):
    return tr


ARGS = parser.parse()
