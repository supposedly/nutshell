import os
import sys

from magic import parser, compiler


def transpile(fp):
    return compiler.compile(parser.parse(fp))


if __name__ == '__main__':
    infile, outdir, *_ = sys.argv[1:]
    fname, *_ = os.path.split(infile)[-1].split('.')
    
    with open(infile) as infp, open(f'{os.path.join(outdir, fname)}.rule') as outfp:
        outfp.write(transpile(infp))
