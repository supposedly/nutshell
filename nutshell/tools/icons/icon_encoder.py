"""
Helps encode Golly-style XPM icons into nutshell's RLE-icon format.
"""
import sys
import traceback
from collections import defaultdict
from itertools import chain, groupby, takewhile
from pathlib import Path
from math import ceil

from nutshell.cli import cli, icon as _icon
from nutshell.tools.common import StreamProxy


cmd = _icon.command(
  'convert',
  'Golly-XPM-icon-to-nutshell-RLE-icon converter',
  aliases=['encode'],
  OR='not nothing'
  )
SYMBOL_MAP = [
  '.',
  *(chr(64 + num) for num in range(1, 25)),
  *(chr(110 + ceil(num/24)) + chr(64 + (num % 24 or 24)) for num in range(25, 256))
  ]


@cmd.arg(required=True)
def infile(path: Path):
    """Path to a file that defines @ICONS. Hyphen for stdin."""
    with StreamProxy(path, alternate=sys.stdin, use_alternate=(path.name == '-')) as f:
        return [i.strip() for i in f if i]


@cmd.arg(required=True)
def outdir(path: Path):
    """Directory to place output file in. Hyphen for stdout."""
    # TODO: Once the awaitable shenanigans are implemented in ergo,
    # make this `await ctx.arg('infile')` to be used in the output filename
    # (could be done after parsing ofc but that's more annoying)
    return StreamProxy(path / 'conv_icons.txt', alternate=sys.stdout, use_alternate=(path.name == '-'))


def encode(strs):
     """
     Encode given strings into Golly-compatible RLE.
     """
     ret = '$'.join(
       ''.join(
         '{}{}'.format(len(s), s[0]) if len(s) > 1 else ''.join(s)
         for s in (
           list(g)
           for _, g in groupby(i)
           )
         )
       for i in strs
       )
     return encode([ret]) if '$$' in ret else ret.rstrip('$23456789') + '!'

def main(args):
    infile = args.infile[args.infile.index('@ICONS'):]
    icons = [
      i[i.startswith('"') : -i.endswith('"') or None]
      for i in takewhile(lambda s: not s.startswith('@'), infile[1:])
      if not i.startswith('/*')
      ]
    if icons[0] != 'XPM':
        raise ValueError('Bad XPM segment descriptor')
    
    width, height, n_colors, chars_per = map(int, icons[1].split())  # immediately after the XPM descriptor thing
    # similarly, start the icons[...] slice at 2 to skip "XPM" and the above line
    # add 2 to n_colors (the slice's stop) for the same reason
    symbols = {symbol: color for symbol, _, color, *_ in map(str.split, icons[2:n_colors+2])}
    new_colors = {color: symbol for color, symbol in zip(symbols.values(), SYMBOL_MAP)}
    icons = icons[n_colors+2:]
    
    if not all(map(chars_per.__eq__, map(len, symbols))):
        raise ValueError('Bad XPM chars-per-color value')
    
    if len(symbols) > 255:
        raise ValueError(
          'Too many colors to be represented via RLE. '
          'If you cannot remove any, you may still use your '
          'icons within a nutshell file via the segment header '
          '"@ICONS #golly" instead of "@ICONS".'
          )
    
    with args.outdir as out:
        out.write('@ICONS\n')
        for color, symbol in new_colors.items():
            out.write(f"{symbol}  {color.lstrip('#')}\n")
        out.write('\n')
        new_icons = [[
            [new_colors[symbols[symbol]] for symbol in map(''.join, zip(*[iter(line)] * chars_per))]
            for line in icon
            # Replace old symbols with new RLE-based ones by splitting line into
            # `chars_per_color`-sized chunks with the zip() idiom
            # (also convert cur line from a string to a list of new symbols,
            # which is effective bc multiple-character symbols within a string
            # rather than a list can't be handled by encode())
            ]
          for icon in zip(*[iter(icons)] * width)
          # Each iteration exposes one single icon block
          # (because the XPM data is w/ zip() split up into
          # equal `height`-sized chunks, each of which of
          # course contains an icon)
          ]
        inv_icons = defaultdict(set)
        # Find duplicate icons and consolidate them
        for state_no, new_icon in enumerate(map(encode, new_icons), 1):  # Start at 1, because state 0 can't be given an icon in Golly
            inv_icons[new_icon].add(state_no)
        all_states = list(chain.from_iterable(inv_icons.values()))
        for states in inv_icons.values():
            if len(states) > 2:
                states[:] = {states[0], *chain.from_iterable((a, b) for a, b in zip(states, states[1:]) if b-a > 1), states[-1]}
            if 1 + max(states) in all_states:
                # Golly automatically assigns the last defined icon to undefined states
                # so we don't need to explicitly name them all
                states.remove[max(states)]
        for new_icon, states in inv_icons.items():
            out.write(f"#C {' '.join(map(str, states))}\n")  # states to be assigned this icon
            out.write(f'x={height}, y={height}, rule=//{n_colors}\n')  # icon's height/width info
            out.write(new_icon + '\n\n')  # icon RLE data
