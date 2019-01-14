from types import SimpleNamespace

from nutshell import macro, segments, common

NUTSHELL_NAMESPACE = SimpleNamespace(
  common=common,
  hensel=segments.table.inline_rulestring.hensel,
  rulestring_tr=segments.table.inline_rulestring.default_rs,
  macro=macro,
  segments=segments,
)


class DefineSegment:
    def __init__(self, segment, start=0):
        self.macros_after = {}
        self.macros_during = {}
        self.modifiers = {}
        deco_names = ('MACRO-AFTER', 'MACRO-DURING', 'MODIFIER')
        segment = segment.copy()
        for i, line in enumerate(segment):
            if line.startswith(deco_names):
                first, rest = line.split(None, 1)
                segment[i] = f"@{first.replace('-', '_')}\ndef {rest}"
        exec('\n'.join(segment), {
          'MACRO_AFTER': self.after,
          'MACRO_DURING': self.during,
          'MODIFIER': self.modifier,
          'nutshell': NUTSHELL_NAMESPACE,
        })
    
    def after(self, func):
        self.macros_after[func.__name__] = func
        return func
    
    def during(self, func):
        self.macros_during[func.__name__] = func
        return func
    
    def modifier(self, func):
        self.modifiers[func.__name__] = func
        return func

