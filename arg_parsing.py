import argparse

def argtuple(s):
    return tuple(int(i.strip()) for i in s.split(','))

parser = argparse.ArgumentParser()
parser.add_argument('infile', help='rueltabel-formatted input file')
parser.add_argument('outdir', nargs='?', help='Directory to create output file in')
parser.add_argument('-f', '--find-transition', dest='match', type=argtuple, required=False, help='Locate first transition in `infile` that matches')
parser.add_argument('-v', '--verbose', dest='verbosity', action='count', default=0, help='Up to four levels; repeated flag == more verbose')

args = parser.parse_args()
if args.match and args.outdir:
    parser.error("`-f|--find' and `outdir' are mutually exclusive")