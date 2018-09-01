class Reshape(Exception):
    def __init__(self, cdir, fasdfsfa=None):
        self.cdir = cdir
        self.fsadfasfa = fasdfsfa


class Ellipse(Exception):  # the imperative verb 'ellipse'
    def __init__(self, cdir, split, value, map_to=None):
        self.cdir = cdir
        self.split = split
        self.val = value
        self.map_to = map_to


class Unpack(Exception):
    def __init__(self, index, value):
        self.idx = index
        self.val = value


class CoordOutOfBoundsError(Exception):
    """
    Raised when |one of a coord's values| > 1
    """
    def __init__(self, coord):
        self.coord = coord
