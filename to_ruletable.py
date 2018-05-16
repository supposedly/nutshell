"""Facilitates conversion of a ruelfile into a Golly-compatible .rule file."""
import argparse
import os

from arg_parser import args
from magic import parser, compiler
from magic.common import utils

utils.VERBOSITY = args.verbosity


def transpile(fp, *, match=None):
    """
    Parses and compiles the given ruelfile into an equivalent .rule.
    """
    print('\nParsing...')
    parsed = parser.parse(fp)
    if match is not None:
        raise SystemExit(parsed['@TABEL'].match(match) or 'No match\n')
    print('Complete!', 'Compiling...', sep='\n\n')
    return compiler.compile(parsed)


if __name__ == '__main__':
    fname, *_ = os.path.split(args.infile)[-1].split('.')
    with open(args.infile) as infp:
        finished = transpile(infp, match=args.match)
    with open(f'{os.path.join(args.outdir, fname)}.rule', 'w') as outfp:
        outfp.write(finished)
        print('Complete!', f'Created {os.path.realpath(outfp.name)}', sep='\n\n')
