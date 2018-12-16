import re
from collections import defaultdict
from itertools import chain, filterfalse, takewhile, repeat

import bidict

from ._classes import ColorRange
from ._utils import maybe_double, SAFE_CHARS, SYMBOL_MAP
from nutshell.common.classes import TableRange, ColorMixin
from nutshell.common.utils import random, multisplit
from nutshell.common.errors import *

TWO_STATE = str.maketrans('bo', '.A')


class IShouldntHaveToDoThisBidict(bidict.bidict):
    """Why is this not an __init__ parameter"""
    on_dup_val = bidict.OVERWRITE


class Icon:
    _rRUNS = re.compile(r'(\d*)([$.A-Z]|[p-y][A-O])')
    
    def __init__(self, rle, height, x, y):
        if height not in (7, 15, 31):
            raise ValueError(f"Need to declare valid height (not '{height!r}')")
        self.height = height
        self._fill = ['..' * height]
        self._rle = rle
        _split = ''.join(
          maybe_double(val) * int(run_length or 1)
          for run_length, val in
            self._rRUNS.findall(self._rle)
          ).split('$$')
        self._split = [i + '..' * (x - len(i) // 2) for i in _split]
        self._split += repeat('..'*x, y-len(_split))
        self.ascii = self._pad()
    
    def __iter__(self):
        yield from self.ascii

    @classmethod
    def solid_color(cls, color, height):
        return [maybe_double(color) * height] * height
    
    @staticmethod
    def _fix_two(s):
        if not any('.' in i and i != ('.', '.') for i in zip(*[iter(s)]*2)):
            return s
        return s[1:] + '.'
    
    def _pad(self):
        # Horizontal padding
        max_len = max(map(len, self._split))
        # Vertical padding
        pre = (self.height - len(self._split)) // 2
        post = (self.height - len(self._split)) - pre
        return self._fill * pre + [self._fix_two(f"{f'{line:.<{max_len}}':.^{2*self.height}}") for line in self._split] + self._fill * post


class IconArray:
    _rDIMS = re.compile(r'\s*x\s*=\s*(\d+),\s*y\s*=\s*(\d+)')
    _rCOLOR = re.compile(r'(\d+:\s*|[.A-Z]\s+|[p-y][A-O]\s+)(\d{0,3}\s+\d{0,3}\s+\d{0,3}|[0-9A-Fa-f]{6}|[0-9A-Fa-f]{3}).*')
    
    def __init__(self, segment, start=0, *, dep: ['@COLORS', '@TABLE', '@NUTSHELL'] = None):
        self._src = segment
        self._set_states = None
        self._fill_gradient = None
        self._height = None
        
        _colors, _table, _nutshell = dep
        self._n_states = _table and _table.n_states
        self._vars = _table and _table.vars
        self._color_segment = None if isinstance(_colors, list) else _colors
        self._nutshell = _nutshell
        
        self.colormap, _start_state_def = self._parse_colors()
        self._states, self._comments, dims = self._sep_states(_start_state_def)
        
        self.set_height(dims.values())
        self.icons = {
          state: list(Icon(''.join(rle), self._height, *dims[state]))
          for state, rle in self._states.items()
          }
        self._fill_missing_states()
    
    def __iter__(self):
        yield 'XPM'
        # /* width height num_colors chars_per_pixel */
        yield f'"{self._height} {len(self.icons)*self._height} {len(self.colormap)} 2"'
        # /* colors */
        for symbol, color in self.colormap.items():
            yield f'"{maybe_double(symbol)} c #{color}"'
        # /* icons */
        for state in sorted(self.icons):
            yield from map('/* {} */'.format, self._comments.get(state, []))
            yield f'/* icon for state {state} */'
            yield from map('"{}"'.format, self.icons[state])
    
    def set_height(self, dims=None, max_dim=None):
        if max_dim is None:
            max_dim = max(map(max, zip(*dims)))
        self._height = min(filter(max_dim.__le__, (7, 15, 31)), key=lambda x: abs(max_dim - x))

    def _make_color_symbol(self):
        name = ''.join(random.sample(SAFE_CHARS, 2))
        while name in self.colormap.values():
            name = ''.join(random.sample(SAFE_CHARS, 2))
        return name
    
    def _parse_colors(self, start=1):
        colormap = IShouldntHaveToDoThisBidict()
        lno = start
        last_valid_lno = start
        for lno, line in enumerate((i.split('#')[0].strip() for i in self._src), 1):
            if line.startswith('?'):
                # Can put n_states in brackets if no TABLE section to grab it from
                pre, *post = map(str.strip, line.split('[', 1))
                # Below *_ allows for an arbitrary separator like `000 ... FFF` between the two colors
                _, start, *_, end = pre.split()
                # If available, get n_states from said n_states-containing [comment]
                self._set_states = int(post[0].strip(']').strip()) if post else self._n_states
                # Construct ColorRange from states and start/end values
                self._fill_gradient = ColorRange(int(self._set_states), start.upper(), end.upper())
                continue
            match = self._rCOLOR.match(line)
            if match is None:
                if line:
                    break
                continue
            last_valid_lno = lno
            state, color = match[1].strip().strip(':'), match[2].upper()
            colormap[SYMBOL_MAP[int(state)] if state.isdigit() else maybe_double(state)] = ColorMixin.pack(color).upper()
        return colormap, last_valid_lno
    
    def _sep_states(self, start) -> dict:
        states, comments, dims = {}, {}, {}
        cur_states, cur_comments = set(), []
        last_comment, last_comment_lno = None, 0
        seq = self._src[start-1:] if self._nutshell is None else self._nutshell.replace_iter(self._src[start-1:])
        for lno, line in enumerate(map(str.strip, seq), start):
            if not line:
                continue
            if line.startswith('#'):
                cur_comments.append(line)
                last_comment_lno = lno
                continue
            if last_comment_lno:
                *cur_comments, last_comment = cur_comments
                cur_states = set()
                for word in multisplit(last_comment, (None, ',')):
                    if word.isdigit():
                        state = int(word)
                        if not 0 < state < 256:
                            raise ValueErr(last_comment_lno, f'Icon declared for invalid state {state}')
                        if state in states:
                            raise ValueErr(last_comment_lno, f'State {state} was already assigned an icon')
                        cur_states.add(state)
                    elif word in self._vars:
                        cur_states.update(self._vars[word])
                    elif TableRange.check(word):
                        cur_states.update(TableRange(word))
                last_comment_lno = 0
            if cur_states:
                line = line.translate(TWO_STATE)
                for state in cur_states:
                    states.setdefault(state, []).append(line)
                    comments.setdefault(state, []).extend(cur_comments)
                cur_comments = []
        for state, rle in states.items():
            states[state] = rle[1:]
            dims[state] = list(map(int, chain.from_iterable(self._rDIMS.findall(rle[0]))))
        return states, comments, dims
    
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
            self.icons[state] = Icon.solid_color(symbol, self._height)
