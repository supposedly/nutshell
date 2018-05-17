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
    fp: file obj pointing to a full ruelfile
    
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
    
    for label, converter in CONVERTERS.items():
        try:
            segment, seg_lno = parts[label], lines[label]
        except KeyError:
            continue
        if segment[0].replace(' ', '').lower() == '#golly':
            parts[label] = segment[1:]
            continue
        # If the converter requires another segment/s to work, it'll have
        # a kwarg called 'dep' annotated with the name of said segment(s)
        annot = getattr(inspect.signature(converter).parameters.get('dep'), 'annotation', {})
        # This used to be so elegant but then I had to allow multiple deps
        dep = parts.get(annot or None) if not isinstance(annot, (list, tuple)) else [parts.get(i) for i in annot]
        try:
            parts[label] = converter(segment, seg_lno, **(annot and {'dep': dep}))
        except TabelException as exc:
            if exc.lno is None:
                raise exc.__class__(None, exc.msg, label)
            raise exc.__class__(exc.lno, exc.msg, label, segment, seg_lno)
    
    return parts
