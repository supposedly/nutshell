from nutshell.common.errors import NutshellException


class CoordOutOfBounds(NutshellException):
    pass


class InvalidSymmetries(NutshellException):
    pass


class NeighborhoodError(Exception):
    pass


class Reshape(Exception):
    def __init__(self, cdir, backup=None):
        self.cdir = cdir
        self.backup = backup


class Ellipse(Exception):  # the imperative verb 'ellipse'
    def __init__(self, cdir, split, value, map_to=None):
        self.cdir = cdir
        self.split = split
        self.val = value
        self.map_to = map_to


class CoordOutOfBoundsError(Exception):
    """
    Raised when |one of a coord's values| > 1
    """
    def __init__(self, coord):
        self.coord = coord
