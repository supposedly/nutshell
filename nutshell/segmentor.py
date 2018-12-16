import inspect

from .segment_types import NutshellSegment, Table, ColorSegment, IconArray
from .common import errors, utils


def seg(name, modifiers, cls=None, *, include_bare=True):
    name = f'@{name}'
    if cls is None:
        # then modifiers holds cls
        return [(name, modifiers)]
    base = [(name, cls)] if include_bare else []
    return base + [(f'{name}:{modifier}', cls) for modifier in modifiers]


Table.hush = False  # a little bit eh but :shrug:
CONVERTERS = [
  *seg('NUTSHELL', NutshellSegment),
  *seg('TABLE', Table),
  *seg('COLORS', ColorSegment),
  *seg('ICONS', (7, 15, 31), IconArray),
  ]


def parse(fp):
    """
    fp: file obj pointing to a full rulefile
    
    return: file, segmented into dict
    """
    segments, lines = {}, {}
    seg = None
    
    # Gather all @-headed segments
    for lno, line in enumerate(map(str.strip, fp), 1):
        if line.startswith('@'):
            # Splat operator ensures that a list will always be placed
            # under the `seg` key, and that if it's phrased (as can be
            # done in @RULE) with the segment's first "argument" on the
            # same line, then it will still be the list's first element
            seg, *name = line.split(None, 1)
            segments[seg], lines[seg] = name, lno
            continue
        segments[seg].append(line)
    
    # Parse and operate on gathered segments
    for label, converter in CONVERTERS:
        try:
            seg, seg_lno = segments[label], lines[label]
        except KeyError:
            continue
        # The comment `# golly` can be used segment-initially to
        # indicate that that particular segment should not be touched
        if seg[0].translate(utils.KILL_WS).lower() == '#golly':
            if label == '@TABLE':
                # Sentinel of sorts, understood by compiler.py to mean
                # "don't touch" (special-casing required because @TABLE
                # is itself a special case)
                seg[0] = None
            else:
                segments[label] = seg[1:]
            continue
        # If the converter requires another segment/other segments to work, it'll have
        # a kwarg called 'dep' annotated with a list of the name/s of said segment/s
        annot = getattr(inspect.signature(converter).parameters.get('dep'), 'annotation', None) or {}
        try:
            # Converter classes' constructors should all have the
            # signature `__init__(data, line_number=0)` with optional
            # `dep` kwarg as explained above
            segments[label] = converter(seg, seg_lno, **(annot and {'dep': [segments.get(i) for i in annot]}))
        except errors.NutshellException as e:
            if e.lno is None:
                # Note, `seg` is not passed in this branch
                raise e.__class__(None, e.msg, label)
            raise e.__class__(e.lno, e.msg, label, seg, shift=e.shift or seg_lno)
    
    for name in list(segments):
        if ':' in name:
            segments.setdefault(name.split(':')[0], []).append(segments[name])
            del segments[name]
    return segments
