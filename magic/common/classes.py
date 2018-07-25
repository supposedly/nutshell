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
        # return re.fullmatch(r'\d+(?:\+\d+)?\s*\.\.\s*\d+', string)
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


class ColorMixin:  # XXX: this feels weird being a class? But it's also a mixin, so (????)
    _rGOLLY_COLOR = re.compile(r'\s*(\d{0,3})\s+(\d{0,3})\s+(\d{0,3})\s*.*')
    
    @staticmethod
    def expand(color):
        if len(color) == 6:
            return color
        return ''.join([f'{c}{c}' for c in color])  # fwiw, measurably faster than c * 2
    
    @classmethod
    def unpack(cls, color):
        if isinstance(color, (list, tuple)):
            return color
        m = cls._rGOLLY_COLOR.fullmatch(color)
        if m is not None:
            # Color is already golly
            return m.groups()
        return struct.unpack('BBB', bytes.fromhex(cls.expand(color)))
    
    @classmethod
    def pack(cls, color):
        if isinstance(color, str):
            m = cls._rGOLLY_COLOR.fullmatch(color)
            if m is None:
                # Color is already hex
                return cls.expand(color)
            color = map(int, m.groups())
        return struct.pack('BBB', *color).hex().upper()
