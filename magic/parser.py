import re
import sys
from collections import defaultdict

from common import classes, utils


rCMT = re.compile(r'#.*=.*$') # comments
rBRK = re.compile(r'[{}()]')  # brackets for var literals

def parse(fp):
    parsed = defaultdict(list)
    variables = classes.VarDict()
    segment = None
    for line in fp:
        if line.startswith('@'):
            # @RUEL, @TABEL, @COLORS, ...
            segment, *name = line.split(None, 1)
            if segment == '@RUEL' and name:
                # Could be written either '@RUEL name' or '@RUEL\nname'
                # Either way, the first element of @RUEL's dict entry
                # should be the rulename
                parsed[segment] = name
            continue
        parsed[segment].append(line)
    # TODO: Figure out how to interface such that the variables can be
    # properly replaced in transitions...? (going by the parser spec)
