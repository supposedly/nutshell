"""Facilitates conversion of a nutshell file into a Golly-compatible .rule file."""
import os
import sys
from inspect import cleandoc

from ergo.misc import ErgoNamespace

from nutshell import segmentor, compiler, tools
from nutshell.common.utils import printq
from nutshell.common.errors import NutshellException
from nutshell.cli import cli


def transpile(fp, *, find=None):
    """
    Performs the parsing process from start to finish
    """
    printq('\nParsing...')
    parsed = segmentor.parse(fp)
    if find:
        print(parsed['@TABLE'].match(find) + '\n')
        return
    printq('Complete!', 'Compiling...', sep='\n\n')
    return compiler.compile(parsed)


def _transpile(args):
    for infile in args.infiles:
        if infile == '-':
            finished = transpile(sys.stdin.read().splitlines(True), find=args.find)
        else:
            with open(infile) as infp:
                finished = transpile(infp, find=args.find)
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


def _main():
    inp = cli \
      .prepare(strict=True, propagate_unknowns=True) \
      .set_defaults(quiet=False) \
      .result
    if inp is None:
        return
    if 'transpile' in inp:
        res = _transpile(inp.transpile)
    elif 'icon' in inp:
        res = tools.dispatch(inp.icon)
    for val in res:
        printq(*val, sep='\n')


def main():
    try:
        _main()
    except NutshellException as e:
        raise SystemExit(e.code)
