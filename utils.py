from itertools import chain
from operator import add

class AdditiveDict(dict):
    def __init__(self, it):
        for key, val in it:
            self[key] = self.get(key, 0) + (int(val) if val else 1)
    
    def expand(self):
        return chain(*(k*v for k, v in self.items()))
