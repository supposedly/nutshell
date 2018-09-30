import re
from itertools import count
from collections.abc import MutableSequence

from nutshell.common.errors import ValueErr


class NutshellSegment(MutableSequence):
    _rCONST = re.compile(r'(\s*)(\d+)?:(.*?)\s*\{\s*(.+)\s*}(.*)')
    _rSTATE = re.compile(r'(\s*)(\d+)?:(.*?)()(.*)')  # allow states to be 'reserved' even with no {CONSTANT} name
    
    def __init__(self, segment, start=0):
        self.constants = {}
        self._src = segment
        self._extract_constants()
        self.regex = re.compile(r'\b' + r'\b|\b'.join(self.constants) + r'\b') if self.constants else None
    
    def __getitem__(self, name):
        return self._src.__getitem__(name)
    
    def __setitem__(self, name, value):
        return self._src.__setitem__(name, value)
    
    def __delitem__(self, name):
        return self._src.__delitem__(name)
    
    def __len__(self):
        return self._src.__len__()
    
    def insert(self, index, item):  # for MutableMapping abc
        return self._src.insert(index, item)
    
    def _extract_constants(self, ignore=frozenset({'N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'})):
        """
        Extract constants from @NUTSHELL segment, defined as follows:

            <state>: <...> {<name>} <...>
        
        Where <name> is the constant's name.
        Additionally, {<name>} is removed from final @RULE output.
        """
        taken = set()
        later = {}
        for lno, match in enumerate(self._rCONST.match(i) or self._rSTATE.match(i) for i in self):
            if match is not None:
                _0, state, _1, name, _2 = match.groups()
                if not name:
                    # technically needs a None check...
                    # but state's not going to have any other falsey val
                    if state:
                        taken.add(int(state))
                    continue
                if name in self.constants:
                    raise ValueErr(lno, f'Duplicate constant {name!r}')
                if name in ignore:
                    self[lno] = f'{_0}{state}:{_1}{_2}  (BAD CONSTANT NAME {name!r})'
                else:
                    if state:
                        self.constants[name] = int(state)
                        self[lno] = f'{_0}{state}:{_1}{_2}'
                    else:
                        self.constants[name] = None
                        later[lno] = (_0, name, _1, _2)
        taken.update(i for i in self.constants.values() if i is not None)
        nums = count(1)
        for k, v in self.constants.items():
            if v is None:
                v = self.constants[k] = next(i for i in nums if i not in taken)
                taken.add(v)
        for lno, (_0, name, _1, _2) in later.items():
            self[lno] = f'{_0}{self.constants[name]}:{_1}{_2}'
    
    def _get_constant(self, match):
        return str(self.constants[match[0]])
    
    def replace(self, iterable):
        if self.regex is not None:
            for idx, line in enumerate(iterable):
                iterable[idx] = self.regex.sub(self._get_constant, line)
    
    def replace_iter(self, iterable):
        yield from iterable if self.regex is None else (self.regex.sub(self._get_constant, line) for line in iterable)
    
    def replace_line(self, line):
        return line if self.regex is None else self.regex.sub(self._get_constant, line)
