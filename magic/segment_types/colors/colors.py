from ...common.classes import ColorMixin, TableRange

class ColorSegment(ColorMixin):
    """
    Parse a rulefile's color format into something abstract &
    transferrable into Golly syntax.
    """
    
    def __init__(self, colors, start=0):
        self._packed_dict = None
        self._src = colors
        self.colors = [k.split('#')[0].split(':' if ':' in k else None, 1) for k in self._src if k]
        self.states = {
          int(state.lstrip('*')):
          self._unpack(color.strip())
          for color, states in self.colors
          for state in TableRange.try_iter(states.split())
          }
    
    def __iter__(self):
        return (f"{state} {r} {g} {b}" for state, (r, g, b) in self.states.items())
    
    def __getitem__(self, item):
        if self._packed_dict is None:
            # Asterisk is workaround to allow non-icon-gradient-overriding colors
            # (i.e. [*2 *3: FFF] vs [2 3: FFF] -- latters will take precedence
            # over icon fill gradient, but the formers will not bc it's kept str
            # and so won't be accessible by ColorSegment[int-type cellstate])
            self._packed_dict = {
              int(j) if j.isdigit() else j.lstrip('*'):
              self._pack(color.strip())
              for color, state in self.colors
              for j in state.split()
              }
        return self._packed_dict[item]
