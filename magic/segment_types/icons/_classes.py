from magic.common.classes import ColorMixin

class ColorRange(ColorMixin):
    def __init__(self, n_states, start=(255, 0, 0), end=(255, 255, 0)):
        self.n_states = n_states
        self.start, self.end = map(self.unpack, (start, end))
        self.avgs = [(final-initial)/n_states for initial, final in zip(self.start, self.end)]
    
    def __getitem__(self, state):
        if not 0 <= state <= self.n_states:
            raise IndexError('Requested state out of range')
        if not isinstance(state, int):
            raise TypeError('Not a state value')
        return self.pack(int(initial+level*state) for initial, level in zip(self.start, self.avgs))
