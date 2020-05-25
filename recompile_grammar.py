###{standalone
#
#
#   Lark Stand-alone Generator Tool
# ----------------------------------
# Generates a stand-alone LALR(1) parser with a standard lexer
#
###
# Modified: github/supposedly
###
#
# Git:    https://github.com/erezsh/lark
# Author: Erez Shinan (erezshin@gmail.com)
#
#
#    >>> LICENSE
#
#    This tool and its generated code use a separate license from Lark,
#    and are subject to the terms of the Mozilla Public License, v. 2.0.
#    If a copy of the MPL was not distributed with this
#    file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
#    If you wish to purchase a commercial license for this tool and its
#    generated code, you may contact me via email or otherwise.
#
#    If MPL2 is incompatible with your free or open-source project,
#    contact me and we'll work it out.
#
#

import os
from io import open
###}

import codecs
import sys
import os
from pprint import pprint
from os import path
from collections import defaultdict

import lark
from lark import Lark
from lark.parsers.lalr_analysis import Reduce


from lark.grammar import RuleOptions, Rule
from lark.lexer import TerminalDef

_dir = path.dirname(lark.__file__)
_larkdir = path.join(_dir)
BASE = 'parser_base.py'


EXTRACT_STANDALONE_FILES = [
    'tools/standalone.py',
    'exceptions.py',
    'utils.py',
    'tree.py',
    'visitors.py',
    'indenter.py',
    'grammar.py',
    'lexer.py',
    'common.py',
    'parse_tree_builder.py',
    'parsers/lalr_parser.py',
    'parsers/lalr_analysis.py',
    'parser_frontends.py',
    'lark.py',
]

def extract_sections(lines):
    section = None
    text = []
    sections = defaultdict(list)
    for l in lines:
        if l.startswith('###'):
            if l[3] == '{':
                section = l[4:].strip()
            elif l[3] == '}':
                sections[section] += text
                section = None
                text = []
            else:
                raise ValueError(l)
        elif section:
            text.append(l)

    return {name:''.join(text) for name, text in sections.items()}


def main(fobj, start, out=None):
    lark_inst = Lark(fobj, parser="lalr", lexer="contextual", start=start, propagate_positions=True)

    with open(BASE) as base:
        print(base.read(), file=out)

    data, m = lark_inst.memo_serialize([TerminalDef, Rule])
    print( 'DATA = (' , file=out)
    print(data, file=out)
    print(')', file=out)
    print( 'MEMO = (', file=out)
    print(m, file=out)
    print(')', file=out)


    print('Shift = 0', file=out)
    print('Reduce = 1', file=out)
    print("def Lark_StandAlone(transformer=None, postlex=None, *, tbl):", file=out)
    print("  return Lark._load_from_dict(DATA, MEMO, transformer=transformer, postlex=postlex, tbl=tbl)", file=out)



if __name__ == '__main__':
    with codecs.open('nutshell/segment_types/table/lark_assets/grammar.lark', encoding='utf8') as f, \
         codecs.open('nutshell/segment_types/table/lark_assets/parser.py', 'w', encoding='utf8') as out:
        main(f, 'table', out=out)
