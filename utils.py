from itertools import chain

class AdditiveDict(dict):
    def __init__(self, it):
        for key, val in it:
            self[str(key)] = self.get(key, 0) + int(val or 1)
    
    def expand(self):
        return chain(*(k*v for k, v in self.items()))

class AutoAppendDict(dict):
    def __init__(self, it):
        for key, val in it:
            self[key] = val
    
    def __setitem__(self, key, val):
        super().__setitem__(key, self[key] + [val])
    
    def __missing__(self, key=None):
        return []

