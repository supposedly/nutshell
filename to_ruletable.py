"""Facilitates conversion of a ruelfile into a Golly-compatible .rule file."""
import os

from argv_parse import ARGS
from magic import parser, compiler


def transpile(fp):
    """
    Parses and compiles the given ruelfile into an equivalent .rule.
    """
    print('\nParsing...')
    parsed = parser.parse(fp)
    if ARGS.match:
        raise SystemExit(parsed['@TABEL'].match(match) or 'No match\n')
    if ARGS.preview:
        raise SystemExit('\n'.join(', '.join(tr) for _, tr in parsed['@TABEL'].transitions))
    print('Complete!', 'Compiling...', sep='\n\n')
    return compiler.compile(parsed)


if __name__ == '__main__':
    fname, *_ = os.path.split(ARGS.infile)[-1].split('.')
    with open(ARGS.infile) as infp:
        finished = transpile(infp)
    with open(f'{os.path.join(ARGS.outdir, fname)}.rule', 'w') as outfp:
        outfp.write(finished)
        print('Complete!', f'Created {os.path.realpath(outfp.name)}', sep='\n\n')
