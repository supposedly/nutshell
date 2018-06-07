"""Facilitates conversion of a ruelfile into a Golly-compatible .rule file."""
import os
import sys
from inspect import cleandoc

from argv_parse import ARGS
from magic import parser, compiler


def transpile(fp, *, preview=False):
    """
    Parses and compiles the given ruelfile into an equivalent .rule.
    """
    print('\nParsing...')
    parsed = parser.parse(fp)
    if preview:
        return '\n'.join(', '.join(map(str, tr)) for _, tr in parsed['@TABEL'].transitions)
    if ARGS.find:
        raise SystemExit(parsed['@TABEL'].match(ARGS.find) + '\n')
    print('Complete!', 'Compiling...', sep='\n\n')
    return compiler.compile(parsed)


def _preview(args):
    mock = f'''
      @TABEL
      states: {args.states}
      symmetries: none
      neighborhood: {args.neighborhood}
      {args.transition}
    '''
    parsed = transpile(cleandoc(mock).splitlines(), preview=True)
    return ('Complete! Transpiled preview:\n', parsed, '')


def _transpile(args):
    if args.infile == '-':
        return ('', transpile(sys.stdin.read().splitlines(True)))
    with open(args.infile) as infp:
        finished = transpile(infp)
    with open(f'{os.path.join(args.outdir, fname)}.rule', 'w') as outfp:
        outfp.write(finished)
        return ('Complete!', '', f'Created {os.path.realpath(outfp.name)}')


if __name__ == '__main__':
    try:
        fname, *_ = os.path.split(ARGS.infile)[-1].split('.')
    except AttributeError:
        res = _preview(ARGS.preview)
    else:
        res = _transpile(ARGS)
    print(*res, sep='\n')
