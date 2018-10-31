import sys
from itertools import chain, takewhile, zip_longest
from math import ceil
from pathlib import Path

from nutshell.cli import cli, icon as _icon
from nutshell.common.classes import ColorMixin
from nutshell.tools.common import StreamProxy

cmd = _icon.command(
  'genrule',
  "Generate a rule whose cellstates' colors match the colors defined in a Nutshell's @ICONS",
  aliases=['makerule', 'gen-rule', 'make-rule'],
  OR='not nothing'
  )

# Map from Golly-RLE symbol to numerical state value
CHR_MAP = {
    '.': 0,
  **{chr(64+num): num for num in range(1, 25)},
  **{chr(110 + ceil(num/24)) + chr(64 + (num % 24 or 24)): num for num in range(25, 256)}
  }
# Color-definition lines in a Nutshell's @ICONS will begin with one of those symbols,
# so collate them into a tuple to check via str.startswith
STARTS = tuple(chain(*zip(*((f'{symbol} ', f'{num}:') for symbol, num in CHR_MAP.items()))))

def multisplit(string, *vals, amts=(), filter_bool=False):
    """
    string: string to split
    vals: delimiters to split on
    filter_bool: whether to filter out strings that
      don't pass a filter(bool, ...) check
    return: split string
    
    Split a string on more than one value simultaneously.
    """
    it = [string]
    for v, n in zip_longest(vals, amts, fillvalue=-1):
        it = chain.from_iterable([i.split(v, n) for i in it])
    it = list(it)
    return [i for i in it if i] if filter_bool else list(it)


@cmd.arg(required=True, default=[])
def infile(path: Path):
    """Path to a file that defines @ICONS. Hyphen for stdin."""
    with StreamProxy(path, alternate=sys.stdin, use_alternate=(path.name == '-')) as f:
        file = f.readlines()
    it = iter(file)
    # seek to @ICONS
    for i in iter(lambda: next(it).strip(), '@ICONS'):
        pass
    # Return line of and line after @RULE header (to extract rulename from),
    # as well as the lines on which icon colors are defined
    return (
      next(((a.split(), b) for a, b in zip(*[map(str.strip, file)]*2) if a.startswith(('@RULE', '@NUTSHELL'))), None),
      [
        multisplit(i.split('#')[0].strip(), ' ', ':', amts=(1, 1), filter_bool=True)
        for i in
        takewhile(lambda s: not s.startswith('@'), it)
        if i.startswith(STARTS)
      ]
      )


@cmd.arg(required=True, default=None)
def outdir(path: Path):
    """Directory to place output file in. Hyphen for stdout."""
    # path will be added to
    return StreamProxy(path, 'w', alternate=sys.stdout, use_alternate=(path.name == '-'))


@cmd.flag(default=False)
def different_name():
    return True


def main(args):
    name, lines = args.infile
    # normalize to numerical values (so that states can be copied right into the Golly table)
    ins = {CHR_MAP.get(state, state): ColorMixin.unpack(value) for state, value in lines}
    if name is None:
        name = 'nutshell_generated'
    else:
        header, next_line = name
        if len(header) == 1:
            name = next_line.strip()[0]
        else:
            name = header[1]
    args.outdir.path /= name + '.rule'
    with args.outdir as f:
        if args.different_name:
            f.write(f'@RULE {name}_icon_dev\n')
        else:
            f.write(f'@RULE {name}\n\n')
            f.write(
              'To stop this rule from overriding your normal one, pass -d\n'
              "or --different-name to Nutshell's `icon genrule` command.\n"
              '(This way, however, it does stop these icon-dev rules from\n'
              "clogging up Golly's Rules folder.)\n\n")
        f.write('@TABLE\n')
        f.write(f'neighborhood:Moore\nsymmetries:none\nn_states:{len(ins)}\n\n')
        f.write('@COLORS\n')
        for state, color in ins.items():
            f.write(f"{state} {' '.join(map(str, color))}\n")
