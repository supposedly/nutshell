"""With the pytest-cov plugin installed, run this using `py.test test.py --cov=magic/ --cov-report html`"""
import os
import sys
sys.argv = 3 * ['-'] + ['-q']  # just to shut the CLI up

from to_ruletable import transpile


def test_codecov():
    for file in list(os.walk('./examples/rueltabels'))[0][2]:
        with open('./examples/rueltabels/' + file) as fp:
            transpile(fp)
