from itertools import repeat
from operator import itemgetter

from nutshell.common.classes import ColorMixin, TableRange
from nutshell.common.errors import ValueErr


class ColorSegment(ColorMixin):
    """
    Parse a rulefile's color format into something abstract &
    transferrable into Golly syntax.
    """
    
    def __init__(self, colors, start=0, *, dep: ['@NUTSHELL'] = None):
        dep, = dep
        self._packed_dict = None
        self._src = [i.split('#')[0].strip() for i in colors]
        self.colors = list(enumerate((k.split(':' if ':' in k else None, 1) for k in self._src if k), 1))
        if dep is not None:
            self.colors = [(i, (v[0], dep.replace_line(v[1]))) for i, v in self.colors]
        try:
            self.states = {
              int(state.lstrip('*')): self.unpack(color.strip(), lno)
              for lno, (color, states) in self.colors
              for state in TableRange.try_iter(states.split())
              }
        except ValueError:
            lno, state = next(
              (i, state)
              for i, (_, states) in self.colors
              for state in TableRange.try_iter(states.split())
              if not state.lstrip('*').isdigit()
              )
            raise ValueErr(lno, f'State {state} is not an integer')
        except TypeError as e:
            raise ValueErr(*e.args)
    
    def __iter__(self):
        return (f"{state} {r} {g} {b}" for state, (r, g, b) in self.states.items())
    
    def __getitem__(self, item):
        if self._packed_dict is None:
            # Asterisk is workaround to allow non-icon-gradient-overriding colors
            # (i.e. [*2 *3: FFF] vs [2 3: FFF] -- latters will take precedence
            # over icon fill gradient, but the formers will not bc it's kept str
            # and so won't be accessible by ColorSegment[int-type cellstate])
            try:
                self._packed_dict = {
                  int(st) if st.isdigit() else st.lstrip('*'): self.pack(color.strip(), lno)
                  for lno, (color, states) in self.colors
                  for st in TableRange.try_iter(states.split())
                  }
            except TypeError as e:
                raise ValueErr(*e.args)
        return self._packed_dict[item]
