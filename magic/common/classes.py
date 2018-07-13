import re
import struct


class TableRange:
    """Proxy for a range object."""
    def __init__(self, span, *, shift=0, step=1):
        lower, upper = map(str.strip, span.split('..'))
        if '-' in lower:
            lower, step = map(int, map(str.strip, lower.split('-')))
        self.bounds = (shift+int(lower), 1+shift+int(upper))
        self._range = range(*self.bounds, step)
    
    def __iter__(self):
        yield from self._range
    
    def __contains__(self, item):
        return item in self._range
    
    def __getitem__(self, item):
        return self._range[item]
    
    def __repr__(self):
        return repr(self._range).replace('range', 'TabelRange')
    
    @classmethod
    def check(cls, string):
        # return string.fullmatch(r'\d+(?:\+\d+)?\s*\.\.\s*\d+')
        try:
            cls(string)
        except Exception:
            return False
        return True
    
    @classmethod
    def try_iter(cls, states):
        for state in states:
            if cls.check(state):
                yield from map(str, cls(state))
            else:
                yield state


class ColorMixin:
    _rGOLLY_COLOR = re.compile(r'\s*(\d{0,3})\s+(\d{0,3})\s+(\d{0,3})\s*.*')
    
    def _unpack(self, color):
        if isinstance(color, (list, tuple)):
            return color
        m = self._rGOLLY_COLOR.fullmatch(color)
        if m is not None:
            # Color is already golly
            return m.groups()
        if len(color) == 3:  # three-char shorthand
            color *= 2
        return struct.unpack('BBB', bytes.fromhex(color))
    
    def _pack(self, color):
        if isinstance(color, str):
            m = self._rGOLLY_COLOR.fullmatch(color)
            if m is None:
                # Color is already hex
                return color if len(color) == 6 else color * 2
            color = map(int, m.groups())
        return struct.pack('BBB', *color).hex().upper()
