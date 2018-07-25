#!/usr/bin/env python3.6
"""With the pytest-cov plugin installed, run this using `py.test test.py --cov=magic/ --cov-report html`"""
import os
import sys

import pytest

ARGV = sys.argv.copy() + [None, None][len(sys.argv):]
sys.argv = 3 * ['-'] + ['-q']  # just to shut the CLI up

from types import SimpleNamespace
from to_ruletable import transpile, write_rule


def test_codecov():
    for fname in list(os.walk('./examples/nutshells'))[0][2]:
        with open('./examples/nutshells/' + fname) as fp:
            transpile(fp)


if __name__ == '__main__':
    main = ARGV[1]
    if main is None:
        pytest.main('test.py --cov=magic/ --cov-report=html'.split())
    elif main in ('run', 'test'):
        walk = list(os.walk('./examples/nutshells'))[0][2]
        if main == 'run':
            for fname in walk:
                if len(ARGV) < 3 or fname.split('.')[0] in ARGV[2:]:
                    d = {'infiles': ['./examples/nutshells/' + fname], 'outdirs': ['./examples/compiled_ruletables/']}
                    write_rule(SimpleNamespace(**d, __=d))
        else:
            for fname in walk:
                if len(ARGV) < 3 or fname.split('.')[0] in ARGV[2:]:
                    with open('./examples/nutshells/' + fname) as fp:
                        transpile(fp)
