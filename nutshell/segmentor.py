import inspect

from .segment_types import NutshellSegment, Table, ColorSegment, IconArray
from .common import errors, utils


Table.hush = False  # a little bit eh but :shrug:
CONVERTERS = {
  '@NUTSHELL': NutshellSegment,
  '@TABLE': Table,
  '@COLORS': ColorSegment,
  '@ICONS': IconArray,
  }


def parse(fp):
    """
    fp: file obj pointing to a full rulefile
    
    return: file, sectioned into dict with table and
    colors as convertable representations
    """
    parts, lines = {}, {}
    segment = None
    
    for lno, line in enumerate(map(str.strip, fp), 1):
        if line.startswith('@'):
            # @NUTSHELL, @TABLE, @COLORS, ...
            segment, *name = line.split(None, 1)
            parts[segment], lines[segment] = name, lno
            continue
        parts[segment].append(line)
    
    for label, converter in CONVERTERS.items():
        try:
            segment, seg_lno = parts[label], lines[label]
        except KeyError:
            continue
        if segment[0].translate(utils.KILL_WS).lower() == '#golly':
            if label == '@TABLE':
                segment[0] = None
            else:
                parts[label] = segment[1:]
            continue
        # If the converter requires another segment/s to work, it'll have
        # a kwarg called 'dep' annotated with a list of the name/s of said segment/s
        annot = getattr(inspect.signature(converter).parameters.get('dep'), 'annotation', None) or {}
        try:
            parts[label] = converter(segment, seg_lno, **(annot and {'dep': [parts.get(i) for i in annot]}))
        except errors.NutshellException as exc:
            if exc.lno is None:
                raise exc.__class__(None, exc.msg, label)
            raise exc.__class__(exc.lno, exc.msg, label, segment, seg_lno)
    
    return parts
