import random

import bidict

from . import _utils as utils
from ...common.errors import TableValueError
from ...common.classes import TableRange  # this is exposed externally, I guess

class CoordOutOfBoundsError(Exception):
    """
    Raised when |one of a coord's values| > 1
    """
    pass


class Coord(tuple):
    """
    Represents a 'unit coordinate' of a cell.
    """
    _NAMES = bidict.bidict({
      'N': (0, 1),
      'NE': (1, 1),
      'E': (1, 0),
      'SE': (1, -1),
      'S': (0, -1),
      'SW': (-1, -1),
      'W': (-1, 0),
      'NW': (-1, 1)
      })
    _DIRS = ('N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW')
    
    def __init__(self, _):
        if not all(-2 < i < 2 for i in self):
            raise CoordOutOfBoundsError(self)
    
    def __repr__(self):
        return f'Coord({tuple(self)!r})'
    
    @classmethod
    def from_name(cls, cd):
        return cls(cls._NAMES[cd])
    def diagonal(self):
        return all(self)
    def center(self):
        return not any(self)
    def move(self, cd):
        return getattr(self, cd.lower())
    
    @property
    def name(self):
        return self._NAMES.inv[self]
    @property
    def inv(self):
        return Coord(-i for i in self)
    @property
    def cw(self):
        idx = (1 + self._DIRS.index(self.name)) % 8
        return _MaybeCallableCW(self._NAMES[self._DIRS[idx]])
    @property
    def ccw(self):
        idx = self._DIRS.index(self.name) - 1
        return _MaybeCallableCCW(self._NAMES[self._DIRS[idx]])
    
    @property
    def n(self):
        return Coord((self[0], 1+self[1]))
    @property
    def ne(self):
        return Coord((1+self[0], 1+self[1]))
    @property
    def e(self):
        return Coord((1+self[0], self[1]))
    @property
    def se(self):
        return Coord((1+self[0], self[1]-1))
    @property
    def s(self):
        return Coord((self[0], self[1]-1))
    @property
    def sw(self):
        return Coord((self[0]-1, self[1]-1))
    @property
    def w(self):
        return Coord((self[0]-1, self[1]))
    @property
    def nw(self):
        return Coord((self[0]-1, 1+self[1]))


class _MaybeCallableCW(Coord):
    """
    Allows Coord.cw.cw.cw.cw to be replaced by Coord.cw(4), and so on.
    (The former will still work, however.)
    """
    def __call__(self, num):
        return Coord(self.cw(num-1) if num > 1 else self)


class _MaybeCallableCCW(Coord):
    """
    Ditto above, but counterclockwise.
    """
    def __call__(self, num):
        return Coord(self.ccw(num-1) if num > 1 else self)


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


class PTCD:
    def __init__(self, tbl, tr, match, lno):
        """
        tr: a fully-parsed transition statement
        ptcd: an output specifier
        variables: global dict of variables
        
        output specifiers can be
            CD[(var_literal)]
            CD[variable]
        Or
            CD[CD: (var_literal)]
            CD[CD: variable]
        
        return: output specifier expanded into its full transition(s)
        """
        self.tbl = tbl
        self.match = match
        self.lno = lno
        self.tr = tr
        self._orig_tr = tr.copy()
        
        self.transitions = self._parse()
    
    def __iter__(self):
        yield from self.transitions
    
    def _parse(self):
        cd_idx, cd_to, copy_to, map_to = self._extract_vars()
        try:
            self.tr, map_to, _ = self._resolve_chain(map_to)
        except ValueError:
            pass
        if cd_to == '_None':  # i mean ...
            return [self._make_transition(cd_idx, None, copy_to, map_to)]
        # Start expanding to transitions
        transitions = []
        try:
            self.tr, copy_to, copy_idx = self._resolve_chain(copy_to)
        except ValueError:
            pass
        else:
            cd_to = next(k for k, v in self.tbl.cardinals.items() if v == copy_idx) if copy_idx else '0'
        if copy_to == map_to:
            transitions.append(self._make_transition(cd_idx, cd_to, copy_to, f'[{self.tbl.cardinals[Coord.from_name(cd_idx).inv.name]}]'))
            return transitions
        for idx, (initial, result) in enumerate(zip(copy_to, map_to)):
            if result is None:
                continue
            # If the result is an ellipsis, fill out
            if isinstance(result, range):
                if map_to[idx-1] is None:  # Nothing more to add
                    break
                new_initial = copy_to[result[0]:]
                transitions.append(self._make_transition(cd_idx, cd_to, new_initial, map_to[idx-1]))
                self.tbl.vars[VarName.random()] = new_initial
                break
            transitions.append(self._make_transition(cd_idx, cd_to, initial, result))
        return transitions
    
    def __make_center_tr(self, initial, result, orig, source_cd):
        """
        Handles making a transition from PTCD iff the source and copy-to cells happen to be the same.
        """
        new_tr = [initial, *['any']*len(self.tbl.cardinals), result]
        # Get adjacent cells to original cell (diagonal to current)
        try:
            new_tr[self.tbl.cardinals[orig.name]] = self.tr[0]
        except KeyError:
            pass
        try:
            new_tr[self.tbl.cardinals[orig.cw.name]] = utils.of(self.tr, self.tbl.cardinals[orig.cw.move(source_cd).name])
        except KeyError:
            pass
        try:
            new_tr[self.tbl.cardinals[orig.ccw.name]] = utils.of(self.tr, self.tbl.cardinals[orig.ccw.move(source_cd).name])
        except KeyError:
            pass
        # If we're orthogonal to orig, we have to count for the cells adjacent to us too
        if not orig.diagonal():
            try:
                new_tr[self.tbl.cardinals[orig.cw(2).name]] = utils.of(self.tr, self.tbl.cardinals[orig.cw(3).name])
            except KeyError:
                pass
            try:
                new_tr[self.tbl.cardinals[orig.ccw(2).name]] = utils.of(self.tr, self.tbl.cardinals[orig.ccw(3).name])
            except KeyError:
                pass
        return new_tr
    
    def _make_transition(self, source_cd: str, cd_to: str, initial, result):
        """
        tr: Original transition
        source_cd: Cardinal direction as a letter or pair thereof. (N, S, SW, etc)
        initial: initial state value
        
        Build a transition from segments of an output specifier.
        """
        # source_cd == East | East
        # cd_to == SouthEast | East
        cur = Coord.from_name(source_cd)  # position of current cell relative to original
        # cur == East | East
        orig = cur.inv  # position of original cell relative to current
        # orig == West | West
        new_tr = self.__make_center_tr(initial, result, orig, source_cd)
        if cd_to is None:
            return new_tr
        # Otherwise, we have to fiddle with the values at the initial and new_relative indices
        try:
            new_tr[0] = self.tr[self.tbl.cardinals[cur.name]]
        except KeyError:
            pass
        new_relative = orig if cd_to == '0' else orig.move(cd_to)  # position of "copy_to" cell relative to current
        # new_relative == South (which is West moved SouthEast) | [CENTER] (which is West moved East)
        if new_relative.center():
            return new_tr
        try:
            new_tr[self.tbl.cardinals[new_relative.name]] = initial
        except KeyError:
            pass
        return new_tr
    
    def _extract_vars(self):
        """
        tr: a transition
        match: matched output specifier (regex match object)
        lno: current line number
        
        Parse the 'variable' segments of an output specifier.
        
        return: Output specifier's variables
        """
        m = self.match
        copy_to = self.tr[self.tbl.cardinals[m[1]]] if m[3] is None else self.tr[m[3] != '0' and self.tbl.cardinals[m[3]]]
        if m[2] is not None:  # Means it's a simple "CD:state" instead of a "CD[variable]"
            return m[1], '_None', copy_to, int(m[2])
        if m[4] in {'0', *self.tbl.cardinals} and m[3] is None:
            idx = m[4] != '0' and self.tbl.cardinals[m[4]]
            return (m[1], m[4], *[self.tr[idx]]*2)
        _map_to = []
        for idx, state in enumerate(self.tbl.parse_variable(m[4], self.lno, tr=self.tr, ptcd=True)):
            if state == '_':  # Leave as is (indicated by a None value)
                state = None
            if state == '...':  # Fill out with preceding element (this should be generalized to all mappings actually)
                # TODO: Allow placement of ... in the middle of an expression (to be filled in from both sides)
                _map_to.append(range(idx, len(copy_to)))  # Check isinstance(range) later to determine whether to generate anonymous variable
                break
            _map_to.append(state)
        if len(copy_to) > sum(len(i) if isinstance(i, range) else 1 for i in _map_to):
            raise TableValueError(
              self.lno,
              f"Variable at index {int(m[1] != '0') and self.tbl.cardinals[m[1]]} in output specifier (direction {m[1]})"
              " mapped to a smaller variable. Maybe add a '...' to fill the latter out?"
              )
        return m[1], m[3], copy_to, _map_to
    
    def _resolve_chain(self, current):
        """
        Returns chain's final link and the tr without any chain
        """
        chained = {self._orig_tr.index(current)}
        tr = self.tr.copy()
        while isinstance(current, str) and current.startswith('['):
            cur_idx = int(utils.rBINDING.match(current)[1])
            chained.add(cur_idx)
            current = tr[cur_idx]
        for idx in chained:
            tr[idx] = current
        try:
            return tr, current, cur_idx
        except UnboundLocalError:
            raise ValueError  # fffffffff
