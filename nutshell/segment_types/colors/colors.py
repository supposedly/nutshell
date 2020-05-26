from itertools import repeat
from operator import itemgetter

from nutshell.common.classes import ColorMixin, ColorRange, TableRange
from nutshell.common.utils import multisplit
from nutshell.common.errors import Error


class ColorSegment(ColorMixin):
    """
    Parse a rulefile's color format into something abstract &
    transferrable into Golly syntax.
    """
    
    def __init__(self, colors, start=0, *, dep: ['@NUTSHELL', '@TABLE'] = (None, None)):
        _nutshell, _table = dep
        self._vars = _table.vars if _table else {}
        self._packed_dict = None
        self._src = [i.split('#')[0].strip() for i in colors]
        self.colors = list(enumerate((k.split(':', 1) for k in self._src if k), 1))
        if _nutshell is not None:
            self.colors = [(i, (v[0], _nutshell.replace_line(v[1]))) for i, v in self.colors]
        d = {}
        self.non_override_colors = set()
        for lno, (color, states) in self.colors:
            states = self._sep_states(multisplit(states, (None, ',')))
            if '..' in color:
                states = list(states)
                if len(states) == 1:
                    d[states[0]] = self.unpack(color.split('..')[0].strip(), lno)
                else:
                    crange = ColorRange(len(states)-1, *(self.unpack(c.strip(), lno) for c in color.split('..')))
                    for state, color in zip(states, crange):
                        d[state] = self.unpack(color, lno)
                continue
            color = self.unpack(color.strip(), lno)
            for term in states:
                try:
                    state = int(term.lstrip('*'))
                except ValueError:
                    raise Error(lno, f'State {term} is not an integer')
                d[state] = color
                if term.startswith('*'):
                    self.non_override_colors.add(state)
        self.states = d
    
    def __iter__(self):
        return (f"{state} {r} {g} {b}" for state, (r, g, b) in self.states.items())
    
    def __getitem__(self, item):
        if item in self.non_override_colors:
            raise KeyError(item)
        return self.pack(self.states[item])
    
    def _sep_states(self, states):
        for term in states:
            it = None
            no_star = term.lstrip('*')
            valid_range = TableRange.check(no_star)
            
            if valid_range:
                it = valid_range
            elif no_star in self._vars:
                it = self._vars[no_star]
            
            if it is None:
                yield str(term)
            else:
                yield from (f'*{i}' for i in it) if term.startswith('*') else map(str, it)
