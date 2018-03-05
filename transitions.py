import re

import napkins

rCARDINALS = re.compile(' (NE|SE|SW|NW|N|E|S|W)')

class Transition:
    def __init__(self, tr):
        if isinstance(tr, str):
            tr = tr.split(',')
        tr = [i.strip() for i in tr]
        self.init, self.final = tr.pop(0), tr.pop(-1)
        self.napkin = napkins.guess(tr)
    
    def __iter__(self):
        return iter([self.init, *self.napkin, self.final])
    
    def __repr__(self):
        qualname = self.__class__.__qualname__
        if self.__module__ != '__main__':
            qualname = f'{self.__module__}.{qualname}'
        return f'{qualname}({str(self)!r})'
    
    def __str__(self):
        return ','.join(self)

class OldTransition(Transition):
    """
    A traditional transition, pastable directly into a Golly ruletable.
    """
    def __init__(self, tr):
        super().__init__(tr)
        self.napkin = napkins.guess(self._tr)
        self.vars = {i: v for i, v in enumerate(self) if not v.isdigit()}
    
    @classmethod
    def from_new(cls, new):
        """
        A single new-style transition can hold multiple old-style ones,
        so this returns a list of the latter.
        """
        pass

class NewTransition(Transition):
    def __init__(self, tr):
        tstring, *self.post = rCARDINALS.split(tr)
        self.post = {k: v.strip('[]') for k, v in zip(self.post[::2], self.post[1::2])}
        super().__init__(self._bound_vars(tstring.split(',')))
    
    @staticmethod
    def _bound_vars(tr: (list, tuple)):
        """
        Given a new-style unbound transition like the following:
            'a,1,2,[0],a,a,6,7,8,[4]'.split(',')
        Unbind its variables to work with the old style:
            'a,1,2,a,a1,a2,6,7,8,a1'.split(',')
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
    
    @property
    def old(self):
        return OldTransition.from_new(self)

