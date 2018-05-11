import re
import struct

class ColorSegment:
    """
    Parse a ruelfile's color format into something abstract &
    transferrable into Golly syntax.
    """
    _rGOLLY_COLOR = re.compile(r'\s*(\d{0,3})\s+(\d{0,3})\s+(\d{0,3})\s*.*')
    
    def __init__(self, colors, start=0):
        self._src, self._packed_dict = colors, None
        self.colors = [k.split('#')[0].split(':' if ':' in k else None, 1) for k in self._src if k]
        self.states = {int(j.strip()): self._unpack(color.strip()) for state, color in self.colors for j in state.split()}
    
    def __iter__(self):
        return (f'{state} {r} {g} {b}' for state, (r, g, b) in self.states.items())
    
    def __getitem__(self, item):
        if self._packed_dict is None:
            self._packed_dict = {int(j.strip()): self._pack(color.strip()) for state, color in self.colors for j in state.split()}
        return self._packed_dict[item]
    
    def _unpack(self, color):
        m = self._rGOLLY_COLOR.fullmatch(color)
        if m is not None:
            return m.groups()
        if len(color) % 2:  # three-char shorthand
            color *= 2
        return struct.unpack('BBB', bytes.fromhex(color))
    
    def _pack(self, color):
        m = self._rGOLLY_COLOR.fullmatch(color)
        if m is None:
            return color if len(color) == 6 else color * 2
        return struct.pack('BBB', *map(int, m.groups())).hex().upper()
