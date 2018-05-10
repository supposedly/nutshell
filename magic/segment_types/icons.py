class Icon:
    def __init__(self, rle):
        self._rle = rle


class IconArray:
    def __init__(self, seg, start=0, parts=None):
        self._src, self._colors = seg, parts['@COLORS']
        self._widths = []
        
        self._states = self._sep_states()
        self.icons = list(map(Icon, self._states.items()))
    
    def __iter__(self):
        return iter(self.icons)
    
    def _sep_states(self) -> dict:
        states = {}
        for line in map(str.strip, self._src):
            if not line:
                continue
            if line.startswith('#'):
                cur_state = int(filter(str.isdigit, line))
            states[cur_state] = line
        return states
