#!/usr/bin/env python3.6
"""Facilitates conversion of a nutshell file into a Golly-compatible .rule file."""
import os
import sys
from inspect import cleandoc

from ergo import CLI, Group

###### TWO EXTRA LOCAL IMPORTS DOWN AT THE BOTTOM ######


DEFAULT_HEADER = '''\
********************************
**** COMPILED FROM NUTSHELL ****
********************************\
'''

cli = CLI("A transpiler from the 'Nutshell' rule-table format to Golly's")
cli.main_grp = Group(XOR='find|preview|normal')
preview = cli.command('preview', XOR='find|preview|normal', OR='preview|normal')


@cli.main_grp.clump(AND='infiles|outdirs')
@cli.arg()
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


@cli.clump(OR='preview|normal')
@cli.main_grp.clump(AND='infiles|outdirs')
@cli.main_grp.arg()
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


@cli.main_grp.flag(short='t', default=DEFAULT_HEADER)
def header(text=''):
    """Change or hide 'COMPILED FROM NUTSHELL' header"""
    return text or DEFAULT_HEADER


@cli.main_grp.flag(short='s', default=False)
def comment_src():
    """Comment each tabel source line above the final table line(s) it transpiles to"""
    return True


@cli.clump(XOR='find|preview|normal')
@cli.flag(short='f', default=None)
def find(transition):
    """Locate first transition in `infile` that matches"""
    return tuple(s if s == '*' else int(s) for s in map(str.strip, transition.split(',')))


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


def transpile(fp, *, preview=False):
    """
    Parses and compiles the given nutshell file into an equivalent .rule.
    """
    utils.printq('\nParsing...')
    parsed = parser.parse(fp)
    if preview:
        return '\n'.join(', '.join(map(str, tr)) for _, tr in parsed['@TABLE'].transitions)
    if ARGS.find:
        print(parsed['@TABLE'].match(ARGS.find) + '\n')
        return
    utils.printq('Complete!', 'Compiling...', sep='\n\n')
    return compiler.compile(parsed)


def _preview(args):
    mock = f'''
      @TABLE
      states: {args.states}
      symmetries: none
      neighborhood: {args.neighborhood}
      {args.transition}
    '''
    parsed = transpile(cleandoc(mock).splitlines(), preview=True)
    yield ('Complete! Transpiled preview:\n', parsed, '')


def _transpile(args):
    for infile in args.infiles:
        if infile == '-':
            finished = transpile(sys.stdin.read().splitlines(True))
        else:
            with open(infile) as infp:
                finished = transpile(infp)
        fname = os.path.split(infile)[-1].split('.')[0]
        for directory in args.__.get('outdirs', ()):
            if directory == '-':
                yield finished.splitlines()
                continue
            with open(f'{os.path.join(directory, fname)}.rule', 'w') as outfp:
                outfp.write(finished)
                yield ('Complete!', '', f'Created {os.path.realpath(outfp.name)}')


def write_rule(args):
    for _ in _transpile(args):
        pass


ARGS = cli.defaults

# If these aren't down here I'll get a "can't import name ARGS" because it'll be as-yet undefined
# And I can't put them + the ARGS assignment up top because cli.defaults won't be anything until the CLI functions
# are defined
# AND THEN I can't even put them underneath the `if __name__ == '__main__'` (which would at least be somewhat
# excusable) because they're used by the above importable functions so they need to be defined!

from magic.common import utils
from magic import parser, compiler

if __name__ == '__main__':
    ARGS = cli.parse(strict=True)
    if hasattr(ARGS, 'infiles'):
        res = _transpile(ARGS)
    else:
        res = _preview(ARGS.preview)
    for val in res:
        utils.printq(*val, sep='\n')
