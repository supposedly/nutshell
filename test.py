"""With the pytest-cov plugin installed, run this using `py.test test.py --cov=magic/ --cov-report html`"""
import os
import sys
sys.argv = 3 * ['-'] + ['-q']  # just to shut the CLI up

import to_ruletable as rueltabel


def test_codecov():
    for path in list(os.walk('./examples/rueltabels'))[0][2]:
        with open('./examples/rueltabels/' + path) as fp:
            rueltabel.transpile(fp)
