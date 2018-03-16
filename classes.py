import re
from math import ceil

import napkin
import utils

rCARDINALS = re.compile(' (NE|SE|SW|NW|N|E|S|W)')

class TransitionBase:
    def __init__(self, tr):
        if isinstance(tr, str):
            tr = tr.split(',')
        tr = [i.strip() for i in tr]
        self.init, self.final = tr.pop(0), tr.pop(-1)
        self.napkin = napkin.guess(tr)
    
    def __iter__(self):
        return iter([self.init, *self.napkin, self.final])
    
    def __repr__(self):
        qualname = self.__class__.__qualname__
        if self.__module__ != '__main__':
            qualname = f'{self.__module__}.{qualname}'
        return f'{qualname}({str(self)!r})'
    
    def __str__(self):
        return ','.join(self)

class Transition(TransitionBase):
    """
    Given a new-style transition, return an abstract representation
    of a traditional statement.
    """
    def __init__(self, tr):
        tstring, *self.post = rCARDINALS.split(tr)
        self.post = {k: v.strip('[]') for k, v in zip(*[iter(self.post)]*2)}
        super().__init__(self._bound_vars(tstring.split(',')))
    
    @staticmethod
    def _bound_vars(tr: (list, tuple)):
        """
        Given a new-style unbound transition like the following:
            a,1,2,[0],a,a,6,7,8,[4]
        Unbind its variables to work with the old style:
            a1,1,2,a1,a2,a3,6,7,8,a2
        """
        built = []
        suffix = 0
        for i, v in enumerate(tr):
            if v.isdigit():
                built.append(v)
                continue
            if v.startswith('[') and v.endswith(']'):
                try:
                    built.append(built[int(v.strip('[]'))])
                except IndexError:
                    raise ValueError('Bound variables must refer to a previous index')
            else:
                suffix += 1
                built.append(f'{v}{suffix}')
        return built

