import re
import sys
from collections import defaultdict

from common import classes, utils

rTRANSITION = re.compile('[^,]+?(?:,[^,]+)+')
rASSIGNMENT = re.compile(r'.+? *?= *?[({][\w,]+?[})]')
rRANGE = re.compile(r'\d+? *?\.\. *?\d+?')


def initial_vars(tbl):
    vars_ = {}
    for lno, decl in ((idx, stmt.strip()) for idx, line in enumerate(tbl) for stmt in line.split('#')[0].split(';')):
        if not decl or not rASSIGNMENT.match(decl):
            continue
        if rTRANSITION.match(decl):
            break
        
        name, value = map(str.strip, decl.split('='))
        value = [i.strip() for i in value[1:-1].split(',')]
        if name.startswith('_'):
            raise ValueError(f"Variable name '{name}' starts with an underscore")
        if any(i.isdigit() for i in name):
            raise ValueError(f"Variable name '{name}' contains a digit")
        
        for idx, cellstate in enumerate(value):
            if cellstate.isdigit():
                value[idx] = int(cellstate)
            elif rRANGE.match(cellstate):
                cellstate = [i+int(v.strip()) for i, v in enumerate(cellstate.split('..'))]
                value[idx:1+idx] = range(*cellstate)
            try:
                value[idx:1+idx] = vars_[cellstate]
            except KeyError:
                raise NameError(f"Declaration of variable '{name}' references undefined variable '{cellstate}'") from None
        vars_[name] = value
    return lno, vars_


def tabelparse(tbl):
    start, vars_ = initial_vars(tbl)
    for line in (i.split('#')[0].strip() for i in tbl[start:]):
        if not line:
            continue
        # TODO: parse transitions and whatever else
        


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
