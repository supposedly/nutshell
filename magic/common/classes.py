import re
import struct


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
