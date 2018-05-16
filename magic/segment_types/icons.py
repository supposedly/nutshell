import re
import random
import string
from collections import defaultdict
from itertools import chain, filterfalse, groupby, takewhile
from math import ceil

import bidict

from ..common.classes import ColorRange
from ..common.classes.errors import TabelReferenceError, TabelValueError


SYMBOL_MAP = bidict.frozenbidict({
    0: '.',
  **{num: chr(64+num) for num in range(1, 25)},
  **{num: chr(110 + ceil(num/24)) + chr(64 + (num % 24 or 24)) for num in range(25, 256)}
  })

SAFE_CHARS = string.ascii_lowercase + string.digits + string.punctuation.replace('.', '')


def lazylen(iterable):
    return sum(1 for _ in iterable)


def maybe_double(symbol: str):
    if len(symbol.encode()) < 2:
        return symbol * 2
    return symbol


class Icon:
    HEIGHT = None
    _FILL = None
    _rRUNS = re.compile(r'(\d*)([$.A-Z]|[p-y][A-O])')
    
    def __init__(self, rle):
        if self.HEIGHT not in (7, 15, 31):
            raise ValueError(f"Need to declare valid height (not '{self.HEIGHT!r}')")
        if self._FILL is None:
            self.__class__._FILL = ['..' * self.HEIGHT]
        self._rle = rle
        self._split =''.join(
          maybe_double(val) * int(run_length or 1)
          for run_length, val in
            self._rRUNS.findall(self._rle)
          ).split('$$')
        self.ascii = self._pad()
    
    def __iter__(self):
        return iter(self.ascii)

    @classmethod
    def set_height(cls, dims):
        max_dim = max(map(max, zip(*dims)))
        cls.HEIGHT = min(filter(max_dim.__le__, (7, 15, 31)), key=lambda x: abs(max_dim-x))
    
    @classmethod
    def solid_color(cls, color):
        return [maybe_double(color) * cls.HEIGHT] * cls.HEIGHT
    
    @staticmethod
    def _fix_two(s):
        if not any('.' in i != ('.', '.') for i in zip(*[iter(s)]*2)):
            return s
        return s[1:] + '.'
    
    def _pad(self):
        # Horizontal padding
        earliest = min(lazylen(takewhile('.'.__eq__, line)) for line in self._split)
        max_len = max(map(len, self._split))
        # Vertical padding
        pre = (self.HEIGHT - len(self._split)) // 2
        post = (self.HEIGHT - len(self._split)) - pre
        return self._FILL * pre + [self._fix_two(f"{f'{line[earliest:]:.<{max_len}}':.^{2*self.HEIGHT}}") for line in self._split] + self._FILL * post


class IconArray:
    _rDIMS = re.compile(r'\s*x\s*=\s*(\d+),\s*y\s*=\s*(\d+)')
    _rCOLOR = re.compile(r'(\d+|[.A-Z]|[p-y][A-O])\s+([0-9A-F]{6}|[0-9A-F]{3}).*')
    
    def __init__(self, seg, start=0, *, dep: ['@COLORS', '@TABEL']):
        self._src = seg
        self._start = start
        self._parsed_color_segment, _tabel = dep
        self._n_states = _tabel and _tabel.directives['n_states']
        self._set_states = None
        self._missing = None
        
        self.colormap, _start_state_def = self._parse_colors(start)
        self._states = self._sep_states(_start_state_def)
        
        # this mess just constructs a "sequence" of (x, y) coords to pass to set_height(), grabbed from the RLEs in self._states.values()
        Icon.set_height(map(lambda x: map(int, chain.from_iterable(self._rDIMS.findall(x))), filter(self._rDIMS.match, chain.from_iterable(self._states.values()))))
        
        self.icons = {state: list(Icon(''.join(rle))) for state, (_dims, *rle) in self._states.items()}
        self._fill_missing_states()
    
    def __iter__(self):
        yield 'XPM'
        # /* width height num_colors chars_per_pixel */
        yield f'"{Icon.HEIGHT} {len(self.icons)*Icon.HEIGHT} {len(self.colormap)} 2"'
        # /* colors */
        yield from (f'"{maybe_double(symbol)} c #{color}"' for symbol, color in self.colormap.items())
        # /* icons */
        yield from (f'"{line}"' for icon in (self.icons[key] for key in sorted(self.icons)) for line in icon)
    
    def _make_color_symbol(self):
        name = ''.join(random.sample(SAFE_CHARS, 2))
        while name in self.colormap.values():
            name = ''.join(random.sample(SAFE_CHARS, 2))
        return name
    
    def _parse_colors(self, start=0):
        lno, colormap = start, {}
        for lno, line in enumerate(map(str.strip, self._src)):
            if line.startswith('?'):
                # Can put n_states in a comment if no TABEL section to grab it from
                pre, *post = line.split('#', 1)
                # The *_ allows for an arbitrary separator like `000 ... FFF` between the two colors
                _, start, *_, end = pre.split()
                # If available, get n_states from said n_states-containing comment
                self._set_states = post and int(''.join(filter(str.isdigit, post[0]))) or self._n_states
                # Construct ColorRange from states and start/end values
                self._missing = ColorRange(int(self._set_states), start, end)
                continue
            match = self._rCOLOR.match(line)
            if match is None:
                if line:
                    break
                continue
            state, color = match.groups()
            if len(color) < 6:
                color *= 2
            colormap[SYMBOL_MAP[int(state)] if state.isdigit() else maybe_double(state)] = color.upper()
        return colormap, lno

    def _sep_states(self, start) -> dict:
        states = defaultdict(list)
        for lno, line in enumerate(map(str.strip, self._src[start:]), start):
            if not line:
                continue
            if line.startswith('#'):
                cur_state = int(''.join(filter(str.isdigit, line)))
                if not 0 < cur_state < 256:
                    raise TabelValueError(lno, f'Icon declared for invalid state {cur_state}')
                continue
            states[cur_state].append(line)
        return states
    
    def _fill_missing_states(self):
        # Account for that some/all cellstates may be expressed as non-numeric symbols rather than their state's number
        max_state = 1 + (self._set_states or max(SYMBOL_MAP.inv.get(state, state) for state in self.icons))
        _colormap_inv = {v: k for k, v in self.colormap.items()}
        for state in filterfalse(self.icons.__contains__, range(1, max_state)):
            try:
                color = self._parsed_color_segment[state]
            except (KeyError, TypeError):  # (not present, no @COLORS)
                if self._missing is None:
                    raise TabelReferenceError(self._start,
                      f'No icon available for state {state}. '
                      'To change this, either (a) define an icon for it in @ICONS, '
                      '(b) define a color for it in non-golly @COLORS to be filled in as a solid square, '
                      "or (c) add a '?' ('missing' states) specifier to the initial @ICONS "
                      'color declarations, followed by two colors: the start and end of a gradient.'
                      )
                color = self._missing[state]
            symbol = _colormap_inv.get(color, self._make_color_symbol())
            self.colormap[symbol] = color
            self.icons[state] = Icon.solid_color(symbol)
