"""With the pytest-cov plugin installed, run this using `py.test test.py --cov=magic/ --cov-report html`"""
import os
import sys

ARGV = sys.argv.copy() + [None, None][len(sys.argv):]
sys.argv = 3 * ['-'] + ['-q']  # just to shut the CLI up

from types import SimpleNamespace
from to_ruletable import transpile, _transpile as write_rule


def test_codecov():
    for fname in list(os.walk('./examples/nutshells'))[0][2]:
        with open('./examples/nutshells/' + fname) as fp:
            transpile(fp)


if __name__ == '__main__' and ARGV[1] in ('run', 'test'):
    if ARGV[1] == 'run':
        for fname in list(os.walk('./examples/nutshells'))[0][2]:
            if len(ARGV) < 3 or fname.split('.')[0] in ARGV[2:]:
                write_rule(SimpleNamespace(infile='./examples/nutshells/' + fname, outdir='./examples/compiled_ruletables/'))
    else:
        for fname in list(os.walk('./examples/nutshells'))[0][2]:
            if len(ARGV) < 3 or fname.split('.')[0] in ARGV[2:]:
                with open('./examples/nutshells/' + fname) as fp:
                    transpile(fp)
