"""Facilitates conversion of a ruelfile into a Golly-compatible .rule file."""
import os
import sys

from magic import parser, compiler
from magic.common import utils

utils.VERBOSITY = sys.argv.count('-v') + sys.argv.count('--verbose')


def transpile(fp):
    """
    Parses and compiles the given ruelfile into an equivalent .rule.
    """
    print('\nParsing...')
    parsed = parser.parse(fp)
    print('Complete!\n\nCompiling...')
    return compiler.compile(parsed)


if __name__ == '__main__':
    infile, outdir, *_ = sys.argv[1:]
    fname, *_ = os.path.split(infile)[-1].split('.')
    with open(infile) as infp, open(f'{os.path.join(outdir, fname)}.rule', 'w') as outfp:
        outfp.write(transpile(infp))
    print('Complete!')
