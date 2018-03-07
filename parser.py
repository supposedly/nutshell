import re
import sys

from utils import Variable, conv_permute

rCMT = re.compile(r'#.*=.*$')
rBRK = re.compile(r'[{}]')

variables = {}

with open(sys.argv[1]) as f:
    for line in f:
        line = rCMT.sub('', line)
        if line.startswith('n_states:'):
            _all_ = tuple(range(int(line.split(':')[1])))
            continue
        name, _, val = map(str.strip, line.partition('='))
        val = tuple(rBRK.sub(val, '').split(','))
        if name == '_all_':
            _all_ = val
            continue
        variables[val] = Variable(name)
    f.seek(0)
    
