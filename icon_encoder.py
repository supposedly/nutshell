"""
Helps encode Golly-style XPM icons into rueltabel's RLE-icon format.
"""
import pathlib
import sys
import traceback
from collections import defaultdict
from itertools import chain, groupby, takewhile
from math import ceil

from ergo import Parser


SYMBOL_MAP = [
  '.',
  *(chr(64+num) for num in range(1, 25)),
  *(chr(110 + ceil(num/24)) + chr(64 + (num % 24 or 24)) for num in range(25, 256))
  ]

parser = Parser()


class _StreamProxy:
    def __init__(self, path, *, alternate=None, use_alternate=False):
        self.path = path
        self._using_alternate = use_alternate
        self._alternate = alternate
        self._opened = alternate if use_alternate else None
    def __enter__(self):
        if self._opened is None:
            self._opened = open(self.path)
        return self._opened
    def __exit__(self, etype, value, tb):
        if not self._using_alternate:
            self._opened.close()
            self._opened = None
        if etype is not None:
            traceback.print_tb(tb)
            raise etype(value)  # from None


@parser.arg(required=True)
def infile(path):
    """Path to a file that defines @ICONS. Hyphen for stdin."""
    with _StreamProxy(path, alternate=sys.stdin, use_alternate=(path == '-')) as f:
        return [i.strip() for i in f if i]

@parser.arg(required=True)
def outdir(path):
    """Directory to place output file in. Hyphen for stdout."""
    # TODO: Once the awaitable shenanigans are implemented in ergo,
    # make this await ctx.arg('infile') to be used in the output filename
    # (could be done after parsing ofc but more annoying)
    return _StreamProxy(pathlib.Path(path) / 'conv_icons.txt', alternate=sys.stdout, use_alternate=(path == '-'))


def encode(strs):
     """
     Encode given strings into Golly-compatible RLE.
     """
     ret = '$'.join(
       ''.join(
         '{}{}'.format(len(s), s[0]) if len(s) > 1 else s
         for s in (
           ''.join(g)
           for _, g in groupby(i)
           )
         )
       for i in strs
       )
     return encode([ret]) if '$$' in ret else ret.rstrip('$23456789') + '!' 


args = parser.parse('- -')
infile = args.infile[args.infile.index('@ICONS'):]
_ = list(takewhile(lambda s: not s.startswith('@'), infile[1:]))
icons = [i[i.startswith('"'):-i.endswith('"') or None] for i in _ if not i.startswith('/*')]


if icons[0] != 'XPM':
    raise ValueError('Bad XPM icon descriptor')


width, height, n_colors, chars_per = map(int, icons[1].split())  # after the XPM thing
# start icons[...] at 2 to skip XPM and the above
# add 2 to n_colors (end) for same reason
symbols = {symbol: color for symbol, _, color, *_ in map(str.split, icons[2:n_colors+2])}
new_colors = {color: symbol for color, symbol in zip(symbols.values(), SYMBOL_MAP)}
icons = icons[n_colors+2:]
icons_ = icons.copy()


if not all(map(chars_per.__eq__, map(len, symbols))):
    raise ValueError('Bad XPM chars-per-color value')
# chars-per-char is now going to be 2
if len(symbols) > 255:
    raise ValueError(
      'Too many colors to be represented via RLE. '
      'If you cannot remove any colors, you may still '
      'use your icons within a rueltabel by using the '
      'header "@ICONS #golly" instead of "@ICONS".'
      )


with args.outdir as out:
    out.write('@ICONS\n')
    for color, symbol in new_colors.items():
        out.write(f"{symbol}  {color.lstrip('#')}\n")
    out.write('\n')
    # Each iteration will expose one single icon block
    # (because the XPM data is being split up into
    # equal and `height`-sized chunks, each of which
    # of course contains an icon)
    #
    # TODO: This really could all be one flat-nested listcomp;
    # see if it's not too visually-gross to do it that way
    new_icons = []
    for start, icon in enumerate(zip(*[iter(icons_)]*width)):
        # Each iteration of this will expose one line of current icon
        icons[start] = []
        for idx, line in enumerate(icon, start):
            # Replace old symbols with new RLE-based ones by splitting line into
            # `chars_per_color`-sized chunks
            # (also convert this line from a string to a list of new symbols,
            # which is effective bc multiple-character symbols within a string
            # rather than a list can't be handled by encode())
            icons[start].append([new_colors[symbols[symbol]] for symbol in map(''.join, zip(*[iter(line)]*chars_per))])
    icons = icons[:1+start]
    inv_icons = defaultdict(list)
    # Find duplicate icons and consolidate them (hopefully they can be recognized this way?)
    for state_no, new_icon in enumerate(map(encode, icons), 1):  # Start at 1; state 0 can't be given an icon in Golly
        inv_icons[new_icon].append(state_no)
    for new_icon, states in inv_icons.items():
        out.write(f"#C {' '.join(map(str, states))}\n")
        out.write(new_icon + '\n\n')


