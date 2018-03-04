__all__ = 'Moore', 'VonNeumann'

class Napkin:
    def __init__(self, **flags):
        self._flags = flags
        for i in self._neighborhood:
            setattr(self, i, flags[i])
    
    def __str__(self):
        """
        Returns the napkin's values as a transition rule.
        """
        # Could also just do ','.join(self._flags.values()), but dicts
        # *technically* aren't yet ordered by default, so this at least
        # ensures the desired ordering
        return ','.join(self._flags[i] for i in self._neighborhood)

class Moore(Napkin):
    _neighborhood = ['n', 'ne', 'e', 'se', 's', 'sw', 'w', 'nw']

class VonNeumann(Napkin):
    _neighborhood = ['n', 'e', 's', 'w']

