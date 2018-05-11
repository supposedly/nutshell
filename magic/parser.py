import inspect

from .segment_types import AbstractTable, ColorSegment, IconArray
from .common.classes.errors import TabelException


CONVERTERS = {
  '@TABEL': AbstractTable,
  '@COLORS': ColorSegment,
  '@ICONS': IconArray,
  }


def parse(fp):
    """
    fp: file pointer to a full .ruel file
    
    return: file, sectioned into dict with table and
    colors as convertable representations
    """
    parts, lines = {}, {}
    segment = None
    
    for lno, line in enumerate(map(str.strip, fp), 1):
        if line.startswith('@'):
            # @RUEL, @TABEL, @COLORS, ...
            segment, *name = line.split()
            parts[segment], lines[segment] = name, lno
            continue
        parts[segment].append(line)
    
    for lbl, converter in CONVERTERS.items():
        try:
            segment, seg_lno = parts[lbl], lines[lbl]
        except KeyError:
            continue
        if segment[0].replace(' ', '').lower() == '#golly':
            parts[lbl] = segment[1:]
            continue
        dep = inspect.signature(converter).parameters.get('dep', {})
        try:
            parts[lbl] = converter(segment, seg_lno, **(dep and {'dep': parts.get(dep.annotation)}))
        except TabelException as exc:
            if exc.lno is None:
                raise exc.__class__(None, exc.msg)
            raise exc.__class__(exc.lno, exc.msg, segment, seg_lno)
    
    return parts
