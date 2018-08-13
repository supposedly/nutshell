"""Facilitates conversion of a nutshell file into a Golly-compatible .rule file."""
import os
import sys
from inspect import cleandoc

from ergo.misc import ErgoNamespace

from nutshell.cli import ARGS
from nutshell.common.utils import printq
from nutshell import parser, compiler


def transpile(fp, *, preview=False, find=False):
    """
    Parses and compiles the given nutshell file into an equivalent .rule.
    """
    printq('\nParsing...')
    parsed = parser.parse(fp)
    if preview:
        return '\n'.join(', '.join(map(str, tr)) for _, tr in parsed['@TABLE'].transitions)
    if find:
        print(parsed['@TABLE'].match(ARGS.find) + '\n')
        return
    printq('Complete!', 'Compiling...', sep='\n\n')
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
            finished = transpile(sys.stdin.read().splitlines(True), find=args.find)
        else:
            with open(infile) as infp:
                finished = transpile(infp)
        fname = os.path.split(infile)[-1].split('.')[0]
        for directory in args._.get('outdirs', ()):
            if directory == '-':
                yield finished.splitlines()
                continue
            with open(f'{os.path.join(directory, fname)}.rule', 'w') as outfp:
                outfp.write(finished)
                yield ('Complete!', '', f'Created {os.path.realpath(outfp.name)}')


def write_rule(**kwargs):
    for _ in _transpile(ErgoNamespace(**kwargs)):
        pass


def main():
    if ARGS is None:
        return
    if 'transpile' in ARGS:
        res = _transpile(ARGS.transpile)
    else:
        res = _preview(ARGS.preview)
    for val in res:
        printq(*val, sep='\n')


if __name__ == '__main__':
    main()
