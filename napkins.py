__all__ = 'Moore', 'VonNeumann'


class Napkin:
    def __init__(self, nap: (list, tuple)):
        if isinstance(nap, str):
            nap = nap.split(',')
        self._flags = dict(zip(self._nhood, map(str.strip, nap)))
        for k, v in self._flags.items():
            setattr(self, k, v)
    
    def __getitem__(self, item):
        return getattr(self, item)
    
    def __setitem__(self, item, value):
        return setattr(self, item, value)
    
    def __iter__(self):
        # Dicts are ordered in 3.6
        return iter(self._flags.values())
    
    def __repr__(self):
        qualname = self.__class__.__qualname__
        if self.__module__ != '__main__':
            qualname = f'{self.__module__}.{qualname}'
        return f'{qualname}({str(self)!r})'
    
    def __str__(self):
        """
        Returns the napkin's values as a transition line.
        """
        return ','.join(self)

class Moore(Napkin):
    _nhood = ['n', 'ne', 'e', 'se', 's', 'sw', 'w', 'nw']

class VonNeumann(Napkin):
    _nhood = ['n', 'e', 's', 'w']


def guess(tr):
    counts = {4: VonNeumann, 8: Moore}
    return counts[len(tr)](tr)
