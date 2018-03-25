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


class KeyConflict(ValueError):
    pass

class ConflictHandlingDict(dict):
    """
    A dict allowing for key-conflict handling.
    """
    @staticmethod
    def __conflict_handler(self, key, value):
        """
        Meant to be overwritten.
        A function replacing this needs to have a type signature of:
        
        self, key, value
        
        It also needs to return a (key, value) tuple or if not then
        raise some fatal exception.
        """
        raise KeyConflict(f"Key '{key}' already has a value of {value!r}")
    
    def __init__(self, seq=None, **kwargs):
        self.conflict_handler = self.__conflict_handler
        self.update(seq, **kwargs)
    
    def __setitem__(self, key, value):
        if key in self:
            key, value = self.conflict_handler(self, key, value)
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
    
    def reset_handler(self):
        self.conflict_handler = self.__conflict_handler

    
class Variable:
    __slots__ = 'name', 'reps'
    def __init__(self, name):
        self.name = name
        self.reps = 0
