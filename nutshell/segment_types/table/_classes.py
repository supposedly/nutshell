import random

from . import _utils as utils
from nutshell.common.errors import ValueErr
from nutshell.common.utils import random


class VarName:
    """
    Represents a variable and how many times it should be
    redefined (to avoid binding) in a Golly table.
    
    Also overrides __hash__ and __eq__ in order to
    allow a Variable in a dict to be referred to by its name.
    """
    __slots__ = 'name', 'rep'
    
    def __init__(self, name, rep=0):
        self.name = str(name)
        self.rep = rep
    
    def __hash__(self):
        return hash(self.name)
    
    def __eq__(self, other):
        return self.name == other
    
    def __str__(self):
        return self.name
    
    def __repr__(self):
        return f'{type(self).__name__}({self.name!r}, rep={self.rep})'
    
    def __getattr__(self, attr):
        return getattr(self.name, attr)
    
    @classmethod
    def random(cls):
        """
        Generates a Variable with a random name.
        Method of random generation liable to change.
        """
        return cls(f'_{random.randrange(10**15)}')


class SpecialVar(tuple):
    """Non-overwritable."""
    def __eq__(self, other):
        return type(other) is type(self) and super().__eq__(other)
    def __hash__(self):
        return super().__hash__()
    def __repr__(self):
        return f'SpecialVar({super().__repr__()})'
