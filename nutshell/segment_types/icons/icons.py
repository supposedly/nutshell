import re
from collections import defaultdict
from itertools import chain, filterfalse, takewhile, repeat

import bidict

from ._classes import ColorRange
from ._utils import lazylen, maybe_double, SAFE_CHARS, SYMBOL_MAP
from nutshell.common.classes import TableRange, ColorMixin
from nutshell.common.utils import random
from nutshell.common.errors import *

TWO_STATE = str.maketrans('bo', '.A')


class IShouldntHaveToDoThisBidict(bidict.bidict):
    """Why is this not an __init__ parameter"""
    on_dup_val = bidict.OVERWRITE


class Icon:
    HEIGHT = None
    _rRUNS = re.compile(r'(\d*)([$.A-Z]|[p-y][A-O])')
    
    def __init__(self, rle):
        if self.HEIGHT not in (7, 15, 31):
            raise ValueError(f"Need to declare valid height (not '{self.HEIGHT!r}')")
        self._fill = ['..' * self.HEIGHT]
        self._rle = rle
        self._split = ''.join(
          maybe_double(val) * int(run_length or 1)
          for run_length, val in
            self._rRUNS.findall(self._rle)
          ).split('$$')
        self.ascii = self._pad()
    
    def __iter__(self):
        yield from self.ascii

    @classmethod
    def set_height(cls, dims=None, max_dim=None):
        if max_dim is None:
            max_dim = max(map(max, zip(*dims)))
        cls.HEIGHT = min(filter(max_dim.__le__, (7, 15, 31)), key=lambda x: abs(max_dim - x))
    
    @classmethod
    def solid_color(cls, color):
        return [maybe_double(color) * cls.HEIGHT] * cls.HEIGHT
    
    @staticmethod
    def _fix_two(s):
        if not any('.' in i and i != ('.', '.') for i in zip(*[iter(s)]*2)):
            return s
        return s[1:] + '.'
    
    def _pad(self):
        # Horizontal padding
        earliest = min(lazylen(takewhile('.'.__eq__, line)) for line in self._split)
        max_len = max(map(len, self._split))
        # Vertical padding
        pre = (self.HEIGHT - len(self._split)) // 2
        post = (self.HEIGHT - len(self._split)) - pre
        return self._fill * pre + [self._fix_two(f"{f'{line[earliest:]:.<{max_len}}':.^{2*self.HEIGHT}}") for line in self._split] + self._fill * post


class IconArray:
    _rDIMS = re.compile(r'\s*x\s*=\s*(\d+),\s*y\s*=\s*(\d+)')
    _rCOLOR = re.compile(r'(\d+:\s*|[.A-Z]\s+|[p-y][A-O]\s+)(\d{0,3}\s+\d{0,3}\s+\d{0,3}|[0-9A-F]{6}|[0-9A-F]{3}).*')
    
    def __init__(self, segment, start=0, *, dep: ['@COLORS', '@TABLE', '@NUTSHELL'] = None):
        self._src = segment
        self._set_states = None
        self._fill_gradient = None
        
        _colors, _table, _nutshell = dep
        self._n_states = _table and _table.n_states
        self._color_segment = None if isinstance(_colors, list) else _colors
        self._nutshell = _nutshell
        
        self.colormap, _start_state_def = self._parse_colors()
        self._states = self._sep_states(_start_state_def)
        
        # this just constructs a series of (x, y) dimensions to pass to set_height(), grabbed from the RLEs in self._states.values()
        Icon.set_height(
          map(int, chain.from_iterable(self._rDIMS.findall(i)))
          for i in
          filter(self._rDIMS.match, chain.from_iterable(self._states.values()))
          )
        
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
    
    def _parse_colors(self, start=1):
        colormap = IShouldntHaveToDoThisBidict()
        lno = start
        for lno, line in enumerate((i.split('#')[0].strip() for i in self._src), 1):
            if line.startswith('?'):
                # Can put n_states in brackets if no TABLE section to grab it from
                pre, *post = map(str.strip, line.split('[', 1))
                # Below *_ allows for an arbitrary separator like `000 ... FFF` between the two colors
                _, start, *_, end = pre.split()
                # If available, get n_states from said n_states-containing comment
                self._set_states = int(post[0].strip(']').strip()) if post else self._n_states
                # Construct ColorRange from states and start/end values
                self._fill_gradient = ColorRange(int(self._set_states), start, end)
                continue
            match = self._rCOLOR.match(line)
            if match is None:
                if line:
                    break
                continue
            state, color = match[1].strip().strip(':'), match[2]
            colormap[SYMBOL_MAP[int(state)] if state.isdigit() else maybe_double(state)] = ColorMixin.pack(color).upper()
        return colormap, lno-1  # -1 because lno is potentially a cellstate-containing comment
    
    def _sep_states(self, start) -> dict:
        states = defaultdict(list)
        cur_states = set()
        _last_comment = 0
        seq = self._src[start-1:] if self._nutshell is None else self._nutshell.replace_iter(self._src[start-1:])
        for lno, line in enumerate(map(str.strip, seq), start):
            if not line:
                continue
            if line.startswith('#'):
                cur_states = {
                  int(state)
                  for split in map(str.split, line.split(','))
                  for state in TableRange.try_iter(split)
                  if state.isdigit()
                  }
                if not all(0 < state < 256 for state in cur_states):
                    raise ValueErr(lno, f'Icon declared for invalid state {next(i for i in cur_states if not 0 < i < 256)}')
                if cur_states.intersection(states):
                    raise ValueErr(lno, f'States {cur_states.intersection(states)} were already assigned an icon')
                _last_comment = lno
                continue
            line = line.translate(TWO_STATE)
            for state in cur_states:
                states[state].append(line)
        return states
    
    def _fill_missing_states(self):
        # Account for that some/all cellstates may be expressed as non-numeric symbols rather than their state's number
        max_state = 1 + (self._set_states or max(SYMBOL_MAP.inv.get(state, state) for state in self.icons))
        for state in filterfalse(self.icons.__contains__, range(1, max_state)):
            try:
                color = self._color_segment[state]
            except (KeyError, TypeError):  # (state not present, @COLORS is None)
                if self._fill_gradient is None:
                    raise ReferenceErr(None,
                      f'No icon available for state {state}. '
                      'To change this, either (a) define an icon for it in @ICONS, '
                      '(b) define a color for it in non-golly @COLORS to be filled in as a solid square, '
                      "or (c) add a '?' ('missing' states) specifier to the initial @ICONS "
                      'color declarations, followed by two colors: the start and end of a gradient.'
                      )
                color = self._fill_gradient[state]
            symbol = self.colormap.inv.get(color, self._make_color_symbol())
            self.colormap[symbol] = color
            self.icons[state] = Icon.solid_color(symbol)
