import re
import sys
from collections import defaultdict

from common import classes, utils

rTRANSITION = re.compile('[^,]+?(?:,[^,]+)+')
rASSIGNMENT = re.compile(r'.+? *?= *?[({][\w,]+?[})]')
rRANGE = re.compile(r'\d+? *?\.\. *?\d+?')


def _conflict_handler(self, key, value):
    """
    Replaces default ConflictHandlingDict conflict_handler.
    Instead of raising exception, turns value into a list.
    """
    new = self[key] if isinstance(self[key], list) else [self[key]]
    return key, new + [value]


def extract_initial_vars(tbl):
    vars_ = classes.ConflictHandlingDict()
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
        
        for idx, state in enumerate(value):
            if state.isdigit():
                value[idx] = int(state)
            elif rRANGE.match(state):
                # There will only ever be two numbers in the range; `i`
                # will be 0 on first pass and 1 on second, so adding
                # it to the given integer will account for python's
                # ranges being exclusive of the end value
                value[idx:1+idx] = range(*(i+int(v.strip()) for i, v in enumerate(state.split('..'))))
            else:
                try:
                    value[idx:1+idx] = vars_[state]
                except KeyError:
                    raise NameError(f"Declaration of variable '{name}' references undefined variable '{state}'") from None  # noqa
        try:
            vars_[value] = name
        except classes.KeyConflict:
            raise ValueError(f"Value {value} is already assigned to variable {vars_[value]}")
    vars_.conflict_handler = _conflict_handler
    return tbl[lno:], vars_, lno


def colorparse(colors):
    pass


def tabelparse(tbl):
    tbl, vars_, start = extract_initial_vars(tbl)
    for lno, line in enumerate((i.split('#')[0].strip() for i in tbl), start):
        if not line:
            continue
        if rASSIGNMENT.match(line):
            raise ValueError(f"Variable declaration on line {lno} does not precede transitions")
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
