"""Facilitates conversion of a ruelfile into a Golly-compatible .rule file."""
import os
import sys

from magic import parser, compiler


def transpile(fp):
    """
    Parses and compiles the given ruelfile into an equivalent .rule.
    """
    print('Parsing...', end='\n\n')
    parsed = parser.parse(fp)
    print('Complete!\nCompiling...', end='\n\n')
    return compiler.compile(parsed)


if __name__ == '__main__':
    infile, outdir, *_ = sys.argv[1:]
    fname, *_ = os.path.split(infile)[-1].split('.')
    with open(infile) as infp, open(f'{os.path.join(outdir, fname)}.rule', 'w') as outfp:
        outfp.write(transpile(infp))
    print('Complete!')
