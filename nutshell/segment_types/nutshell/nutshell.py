import re
from collections.abc import MutableSequence

class NutshellSegment(MutableSequence):
    _rCONST = re.compile(r'(\s*)(\d+):(.*?)\s*\{\s*(.+)\s*}(.*)')
    
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
        for lno, match in enumerate(map(self._rCONST.match, self)):
            if match is not None:
                _0, state, _1, name, _2 = match.groups()
                if name in ignore:
                    self[lno] = f'{_0}{state}:{_1}{_2}  (BAD CONSTANT NAME {name!r})'
                else:
                    self.constants[name] = int(state)
                    self[lno] = f'{_0}{state}:{_1}{_2}'
    
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
