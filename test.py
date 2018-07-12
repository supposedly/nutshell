"""With the pytest-cov plugin installed, run this using `py.test test.py --cov=magic/ --cov-report html`"""
import os
import sys
ARGV = sys.argv.copy()
sys.argv = 3 * ['-'] + ['-q']  # just to shut the CLI up

from types import SimpleNamespace
from to_ruletable import transpile, _transpile as transpile_and_write


def test_codecov():
    for file in list(os.walk('./examples/nutshells'))[0][2]:
        with open('./examples/nutshells/' + file) as fp:
            transpile(fp)


if __name__ == '__main__' and ARGV[1] == 'run':
    for file in list(os.walk('./examples/nutshells'))[0][2]:
        transpile_and_write(SimpleNamespace(infile='./examples/nutshells/' + file, outdir='./examples/compiled_ruletables/'))