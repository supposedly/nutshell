import re
import sys
from collections import defaultdict

from common import classes, utils

rASSIGNMENT = re.compile(r'.+? *?= *?[({][\w,]+?[})]')
rRANGE = re.compile(r'\d+? *?\.\. *?\d+?')


def initial_vars(tbl):
    vars_ = {}
    for decl in (statement.strip() for line in tbl for statement in line.split('#')[0].split(';')):
        if not decl or not rASSIGNMENT.match(decl):
            continue
        name, value = map(str.strip, decl.split('='))
        value = [i.strip() for i in value[1:-1].split(',')]
        
        if name.startswith('_'):
            raise ValueError(f"Variable name '{name}' starts with an underscore")
        if any(i.isdigit() for i in name):
            raise ValueError(f"Variable name '{name}' contains a digit")
        
        for index, cellstate in enumerate(value):
            if cellstate.isdigit():
                value[index] = int(cellstate)
            elif rRANGE.match(cellstate):
                cellstate = [i+int(v.strip()) for i, v in enumerate(cellstate.split('..'))]
                value[index:1+index] = range(*cellstate)
            try:
                value[index:1+index] = vars_[cellstate]
            except KeyError:
                raise NameError(f"Declaration of variable '{name}' contains reference to undefined variable '{cellstate}'") from None
        vars_[name] = value
    return vars_


def tabelparse(tbl):
    vars_ = initial_vars(tbl)
    


def parse(fp):
    parts = defaultdict(list)
    segment = None
    for line in map(str.strip, fp):
        if not line or line.startswith('#'):
            continue
        if line.startswith('@'):
            # @RUEL, @TABEL, @COLORS, ...
            segment, *name = line.split(None, 1)
            if segment == '@RUEL' and name:
                # Can be written as either '@RUEL name' or '@RUEL\nname'
                # Either way, the first element of @RUEL's dict
                # entry should be the rule name
                # (XXX: is the conditional even necessary, btw? probably not --
                # making this block unconditional would also de-necessitate
                # defaultdict, I think, because it'd make sure there's always a list)
                parts[segment] = name
            continue
        parts[segment].append(line)
    parts['@TABEL'] = tabelparse(parts['@TABEL'])
    parts['@COLORS'] = colorparse(parts['@COLORS'])
    return parts
