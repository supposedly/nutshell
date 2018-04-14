"""Facilitates parsing of a rueltabel file into an abstract, computer-readable format."""
import re

from bidict import bidict

from .common import classes, utils
from .common.classes import Coord, TabelRange, Variable
from .common.classes.errors import TabelNameError, TabelSyntaxError, TabelValueError, TabelFeatureUnsupported, TabelException


def rep_adding_handler(_, key, value):
    """
    Replaces default ConflictHandlingBiDict's conflict_handler.
    Instead of raising exception, appends to var's reps.
    """
    # XXX: I actually need to do this per appearance per transition, not per appearance in general
    (key if isinstance(key, Variable) else value).reps += 1
    return key, value


class AbstractTabel:
    """
    Creates an abstract, Golly-transferrable representation of a ruelfile's @TABEL section.
    """
    __rCARDINALS = 'N|NE|E|SE|S|SW|W|NW'
    __rVAR = r'[({](?:\w+\s*(?:,|\.\.)\s*)+(?:\w|(?:\.\.\.)?)+[})]'
    
    _rASSIGNMENT = re.compile(rf'\w+?\s*=\s*{__rVAR}')
    _rBINDMAP = re.compile(rf'\[[0-8](?::\s*?(?:{__rVAR}|[^_]\w+?))?\]')
    _rCARDINAL = re.compile(rf'\b(\[)?({__rCARDINALS})((?(1)\]))\b')
    _rPTCD = re.compile(rf'((?:{__rCARDINALS})+)\[((?:{__rCARDINALS})+:)?\s*(\w+|{__rVAR})')
    _rRANGE = re.compile(r'\d+? *?\.\. *?\d+?')
    _rTRANSITION = re.compile(
      rf'(?:\s*((?:[A-Z]\s*\.\.[A-Z])?\s*(?:[\w\s]+|\[(?:(?:\d|{__rCARDINALS})\s*:\s*)?(?:{__rVAR}|[A-Za-z]+)\])),?)+?\s*'
      )
    _rVAR = re.compile(__rVAR)
    
    CARDINALS = {
      'Moore': {'N': 1, 'NE': 2, 'E': 3, 'SE': 4, 'S': 5, 'SW': 6, 'W': 7, 'NW': 8},
      'vonNeumann': {'N': 1, 'E': 2, 'S': 3, 'W': 4},
      'hexagonal': {'N': 1, 'E': 2, 'SE': 3, 'S': 4, 'W': 5, 'NW': 6}
      }
    POSITIONS = bidict({
      'E': Coord((1, 0)),
      'N': Coord((0, 1)),
      'NE': Coord((1, 1)),
      'NW': Coord((-1, 1)),
      'S': Coord((0, -1)),
      'SE': Coord((1, -1)),
      'SW': Coord((-1, -1)),
      'W': Coord((-1, 0))
       })
    
    def __init__(self, tbl, start=0):
        self._tbl = tbl
        
        self.vars = classes.ConflictHandlingBiDict()  # {Variable(name) | str(name) :: tuple(value)}
        self.var_all = ()  # replaces self.vars['__all__']
        self.directives = {}
        self.transitions = []
        
        _assignment_start = self._extract_directives(start)
        _transition_start = self._extract_initial_vars(_assignment_start)
        
        self.cardinals = self._parse_directives()
        self._parse_transitions(_transition_start)

    def __iter__(self):
        return iter(self._tbl)
    
    def __getitem__(self, item):
        return self._tbl[item]
    
    def _cardinal_sub(self, match):
        try:
            return f"{match[1] or ''}{self.cardinals[match[2]]}{match[3]}"
        except KeyError:
            raise KeyError(match[2])
    
    def _parse_variable(self, var: str, *, ptcd=False):
        """
        var: a variable literal
        
        return: var, but as a tuple with any references substituted for their literal values
        """
        if var.isalpha():
            return self.vars[var]
        cop = []
        for state in map(str.strip, var[1:-1].split(',')):  # var[1:-1] cuts out (parens)/{braces}
            if state.isdigit():
                cop.append(int(state))
            elif self._rRANGE.match(state):
                cop.extend(TabelRange(state))
            elif state == '...' or ptcd and state == '_':
                cop.append(state)
            else:
                try:
                    cop.extend(self.vars[state])
                except KeyError:
                    raise NameError(state) from None
        return tuple(cop)
    
    def _extract_directives(self, start):
        """
        Gets directives from top of ruelfile.

        return: the line number at which var assignment starts.
        """
        lno = start
        for lno, line in enumerate((i.split('#')[0].strip() for i in self), start):
            if not line:
                continue
            if self._rASSIGNMENT.fullmatch(line):
                break
            directive, value = map(str.strip, line.split(':'))
            self.directives[directive] = value.replace(' ', '')
        return lno
    
    def _parse_directives(self):
        """
        Parses extracted directives to understand their values.
        """
        try:
            self.var_all = tuple(range(int(self.directives['n_states'])))
            cardinals = self.CARDINALS.get(self.directives['neighborhood'])
            if cardinals is None:
                raise TabelValueError(None, f"Invalid neighborhood '{self.directives['neighborhood']}' declared")
            if 'symmetries' not in self.directives:
                raise KeyError("'symmetries'")
        except KeyError as e:
            name = str(e).split("'")[1]
            raise TabelNameError(None, f"'{name}' directive not declared") from None
        return cardinals
    
    def _extract_initial_vars(self, start):
        """
        start: line number to start from
        
        Iterates through tabel and gathers all explicit variable declarations.
        
        return: line number at which transition declaration starts
        """
        lno = start
        tblines = ((idx, stmt.strip()) for idx, line in enumerate(self[start:], start) for stmt in line.split('#')[0].split(';'))
        for lno, decl in tblines:
            if utils.globalmatch(self._rTRANSITION, decl):
                break
            if not decl or not self._rASSIGNMENT.match(decl):
                continue
            name, value = map(str.strip, decl.split('='))
            if name == '__all__':  # the special var
                self.var_all = self._parse_variable(value)
            elif not name.isalpha():
                raise TabelSyntaxError(
                  lno,
                  f"Variable name '{name}' contains nonalphabetical character '{next(i for i in name if not i.isalpha())}'",
                  )
            try:
                self.vars[Variable(name)] = self._parse_variable(value)
            except NameError as e:
                raise TabelNameError(lno, f"Declaration of variable '{name}' references undefined name '{e}'")
            except classes.errors.KeyConflict:
                raise TabelValueError(lno, f"Value {value} is already assigned to variable {self.vars.inv[value]}")
        self.vars.set_handler(rep_adding_handler)
        return lno
    
    def _extract_ptcd_var(self, tr, match, lno):
        """
        tr: a transition
        match: matched PTCD (regex match object)
        lno: current line number
        
        Parses the 'variable' segment of a PTCD.
        
        return: PTCD's variable in variable format
        """
        cdir = match[1]
        copy_to = tr[self.cardinals[cdir]]
        _map_to, map_to = [], self._parse_variable(match[3], ptcd=True)
        for idx, state in enumerate(map_to):
            if state == '_':  # Leave as is (indicated by a None value)
                state = None
            if state == '...':  # Fill out with preceding element (this should be generalized to all mappings actually)
                # TODO: Allow placement of ... in the middle of an expression (it'll be filled in from both sides)
                _map_to.append(range(idx, len(copy_to)))  # Check isinstance(range) to determine whether to generate anonymous variable
                break
            _map_to.append(state)
        if len(copy_to) > sum(len(i) if isinstance(i, range) else 1 for i in _map_to):
            raise TabelValueError(
              lno,
              f"Variable '{copy_to}' "
              f"(direction {cdir}, index {self.cardinals[cdir]})"
              " in PTCD mapped to smaller variable. Maybe add a '...' to the latter?"
              )
        return match[1], copy_to, _map_to
    
    def _make_transition(self, tr, source_cd, initial, result):
        curtr = ['__all__'] * len(tr)
        curtr[0] = initial
        curtr[-1] = result
        orig = Coord(self.POSITIONS[source_cd]).opp  # creates S -> N, E -> W, etc.
        try:
            curtr[self.cardinals[orig.name]] = tr[0]
        except KeyError:
            pass
        try:
            curtr[self.cardinals[orig.cw.name]] = tr[self.cardinals[orig.cw.move(source_cd).name]]
        except KeyError:
            pass
        try:
            curtr[self.cardinals[orig.ccw.name]] = tr[self.cardinals[orig.ccw.move(source_cd).name]]
        except KeyError:
            pass
        if not all(orig):  # will execute if the PTCD is orthogonal & not diagonal
            try:
                curtr[self.cardinals[orig.cw(2).name]] = tr[self.cardinals[orig.cw(3).name]]
            except KeyError:
                pass
            try:
                curtr[self.cardinals[orig.ccw(2).name]] = tr[self.cardinals[orig.ccw(3).name]]
            except KeyError:
                pass
        return curtr
        
    def _parse_ptcd(self, tr, ptcd, lno):
        """
        tr: a fully-parsed transition statement
        ptcd: a PTCD
        variables: global dict of variables
        
        PTCDs can be
            CD[(var_literal)]
            CD[variable]
        Or
            CD[CD: (var_literal)]
            CD[CD: variable]
        
        return: PTCD expanded into its full transition(s)
        """
        match = self._rPTCD.match(ptcd)
        if match[2] is not None:
            raise TabelFeatureUnsupported(lno, 'PTCDs that copy neighbor states are not yet supported')
        cd_idx, copy_to, map_to = self._extract_ptcd_var(tr, match, lno)
        # Start expansion to transitions
        transitions = []
        for idx, (initial, result) in enumerate(zip(copy_to, map_to)):
            if result is None:
                continue
            # If the destination is a "..."
            if isinstance(result, range):
                if map_to[idx-1] is None:
                    # Nothing more to add
                    break
                new = copy_to[result[0]:result[-1]]
                self.vars[Variable.random_name()] = new
                transitions.append(self._make_transition(tr, cd_idx, new, result))
                break
            transitions.append(self._make_transition(tr, cd_idx, initial, result))
        return transitions
    
    def _parse_transitions(self, start):
        """
        start: line number to start on
        Parses all the ruel's transitions into a list in self.transitions.
        """
        lno = start
        for lno, line in enumerate((i.split('#')[0].strip() for i in self[start:]), start):
            if not line:
                continue
            if self._rASSIGNMENT.match(line):
                raise TabelSyntaxError(lno, 'Variable declaration after transitions')
            napkin, ptcd = map(str.strip, line.partition('->')[::2])
            try:
                napkin = [self._rCARDINAL.sub(self._cardinal_sub, i.strip()) for i in self._rTRANSITION.findall(napkin)]
            except KeyError as e:
                raise TabelValueError(
                  lno,
                  f"Invalid cardinal direction '{e}' for {self.directives['symmetries']} symmetry"
                  ) from None
            napkin = utils.expand_tr(napkin)
            # Parse napkin into proper range of ints
            for idx, elem in enumerate(napkin):
                if elem.isdigit():
                    napkin[idx] = int(elem)
                elif self._rVAR.match(elem):
                    var = self._parse_variable(elem)
                    self.vars[Variable.random_name()] = var
                elif not self._rBINDMAP.match(elem):  # leave mappings and bindings untouched for now
                    try:
                        napkin[idx] = self.vars[elem]
                    except KeyError:
                        raise TabelNameError(lno, f"Invalid or undefined name '{elem}'")
            if ptcd:
                ptcd = self._parse_ptcd(napkin, ptcd, lno=lno)
            self.transitions.extend([napkin, *ptcd])
        # TODO: step 0.2, step 1.4, step 2.1


class AbstractColors:
    """
    Parses a ruelfile's color format into something abstract &
    transferrable into Golly syntax.
    """
    def __init__(self, *args, **kwargs):
        pass


def parse(fp):
    """
    fp: file pointer to a full .ruel file

    return: file, sectioned into dict with tabel and
    colors as convertable representations
    """
    parts, lines = {}, {}
    segment = None
    
    for lno, line in enumerate(map(str.strip, fp), 1):
        if line.startswith('@'):
            # @RUEL, @TABEL, @COLORS, ...
            segment, *name = line.split(None, 1)
            parts[segment], lines[segment] = name, lno
            continue
        parts[segment].append(line)
    
    try:
        parts['@TABLE'] = AbstractTabel(parts['@TABEL'])
    except KeyError:
        raise TabelNameError(None, "No '@TABEL' segment found")
    except TabelException as exc:
        raise exc.__class__(exc.lno, exc.msg, parts['@TABEL'], lines['@TABEL'])
    
    try:
        parts['@COLORS'] = AbstractColors(parts['@COLORS'])
    except KeyError:
        pass
    except TabelException as exc:
        raise exc.__class__(exc.lno, exc.msg, parts['@COLORS'], lines['@COLORS'])
    return parts
