from itertools import filterfalse


class PlaceholderMeta(type):
    def __call__(cls, *args):
        return args


class Icon:
    KEY = None
    def __init__(self, rle):
        self._rle = rle


class IconArray(metaclass=PlaceholderMeta):
    pass
