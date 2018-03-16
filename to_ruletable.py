import os
import sys

from magic import parser, transpiler


def compile_(fp):
    return transpiler.transpile(parser.parse(fp))

if __name__ == '__main__':
    flip, (infile, outdir, *_) = '--reverse' in sys.argv, sys.argv[1:]
    fname, _ = os.path.split(infile)[-1].split('.', 1)
    
    with open(infile) as infp, open(f'{os.path.join(outdir, fname)}.rule') as outfp:
        outfp.write(compile_(infp))
