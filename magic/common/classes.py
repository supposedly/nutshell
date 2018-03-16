import re

import utils

rCARDINALS = re.compile(' (NE|SE|SW|NW|N|E|S|W)')

class Transition(list):
    """
    A list with a "to" string as attr
    (for PTCDs)
    """
    def __init__(self, seq, to):
        self.to = to
    
class AdditiveDict(dict):
    def __init__(self, it):
        for key, val in it:
            self[str(key)] = self.get(key, 0) + int(val or 1)
    
    def expand(self):
        return chain(*(k*v for k, v in self.items()))

class VarDict(dict):
    """
    A dict that forbids value overwriting.
    """
    def __init__(self, seq=None, **kwargs):
        self.update(seq, **kwargs)
    
    def __setitem__(self, key, value):
        if key in self:
            raise ValueError(f'Key {key} already has a value')
        super().__setitem__(key, value)
    
    def update(self, seq=None, **kwargs):
        if seq:
            for key, value in dict(seq).items():
                self[key] = value
        for key, value in kwargs.items():
            self[key] = value
    
    def setdefault(self, key, default=None):
        if key not in self:
            self[key] = default
        return self[key]

class Variable:
    __slots__ = 'name', 'reps'
    def __init__(self, name):
        self.name = name
        self.reps = 0
