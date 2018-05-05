import argparse

from magic import compiler

def argtuple(s):
    return tuple(int(i.strip()) for i in s.split(','))

parser = argparse.ArgumentParser()
parser.add_argument('infile', help='rueltabel-formatted input file')
parser.add_argument('outdir', nargs='?', help='Directory to create output file in')
parser.add_argument('-f', '--find', dest='match', type=argtuple, required=False, help='Locate first transition in `infile` that matches')
parser.add_argument('-v', '--verbose', dest='verbosity', action='count', default=0, help='Repeat for more verbosity; max x4')
parser.add_argument('-t', '--header', nargs='?', default=None, const='', help="Change or hide 'COMPILED FROM RUELTABEL' header")

args = parser.parse_args()

if args.header is not None:
    compiler.HEADER = args.header

if not args.match and not args.outdir:
    parser.error("Must include either [outdir] or [-f | --find MATCH]")

if args.match and (args.outdir or args.header):
    parser.error("[-f | --find MATCH] is mutually exclusive with [outdir] and [-t | --header HEADER]")
