import re

class ColorSegment:
    """
    Parse a ruelfile's color format into something abstract &
    transferrable into Golly syntax.
    """
    _rGOLLY_COLOR = re.compile(r'\s*(\d{0,3})\s+(\d{0,3})\s+(\d{0,3})\s*.*')
    
    def __init__(self, colors, start=0, *_):
        self._src, self._dict = colors, None
        self.colors = [k.split('#')[0].split(':' if ':' in k else None, 1) for k in self._src if k]
    
    def __iter__(self):
        return (f'{state} {r} {g} {b}' for d in self.states for state, (r, g, b) in d.items())
    
    def __getitem__(self, item):
        if self._dict is None:
            self._dict = {k: v for d in self.states for k, v in d.items()}
        return self._dict[item]
    
    def _unpack(self, color):
        m = self._rGOLLY_COLOR.fullmatch(color)
        if m is not None:
            return m[1], m[2], m[3]
        if len(color) % 2:  # three-char shorthand
            color *= 2
        return struct.unpack('BBB', bytes.fromhex(color))
    
    @property
    def states(self):
        return ({int(j.strip()): self._unpack(color.strip())} for state, color in self.colors for j in state.split())
