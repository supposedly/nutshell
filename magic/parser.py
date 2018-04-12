import random
import re

from .common import classes, utils
from .common.classes import Variable, TabelRange
from .common.classes.errors import TabelNameError, TabelSyntaxError, TabelValueError, TabelFeatureUnsupported


def rep_adding_handler(self, key, value):
    """
    Replaces default ConflictHandlingBiDict conflict_handler.
    Instead of raising exception, appends to var's reps
    """
    (key if isinstance(key, Variable) else value).reps += 1
    return key, value


class AbstractTabel:
    """
    Creates an abstract, Golly-transferable representation of a rueltabel.
    """
    __rCARDINALS = 'N|NE|E|SE|S|SW|W|NW'
    __rVAR = r'[({](?:\w+,\s*)+\w+[})]'
    
    rASSIGNMENT = re.compile(r'.+? *?= *?')
    rBINDMAP = re.compile(rf'\[[0-8](?::\s*?(?:{__rVAR}|[^_]\w+?))?\]')
    rCARDINAL = re.compile(rf'\b(\[)?({__rCARDINALS})((?(1)\]))\b')
    rPTCD = re.compile(rf'((?:{__rCARDINALS})+)\[((?:{__rCARDINALS})+:)?\s*(\w+|{__rVAR})')
    rRANGE = re.compile(r'\d+? *?\.\. *?\d+?')
    rTRANSITION = re.compile('[^,]+?(?:,[^,]+)+')
    rVAR = re.compile(__rVAR)
    
    CARDINALS = {
      'Moore': {'N': 1, 'NE': 2, 'E': 3, 'SE': 4, 'S': 5, 'SW': 6, 'W': 7, 'NW': 8},
      'vonNeumann': {'N': 1, 'E': 2, 'S': 3, 'W': 4},
      'hexagonal': {'N': 1, 'E': 2, 'SE': 3, 'S': 4, 'W': 5, 'NW': 6}
      }
    
    def __init__(self, tbl):
        self._tbl = tbl
        
        self.vars = classes.ConflictHandlingBiDict()
        self.directives = {}
        self.transitions = []
        
        _assignment_start = self.extract_directives()
        _transition_start = self.extract_initial_vars(_assignment_start)
        
        self.cardinals = self.parse_directives()
        self.parse_transitions(_transition_start)
    
    def __iter__(self):
        return iter(self._tbl)
    
    def __getitem__(self, item):
        return self._tbl[item]
    
    def _cardinal_sub(self, match):
        try:
            return f"{match[1] or ''}{self.cardinals[match[2]]}{match[3]}"
        except KeyError:
            raise KeyError(match[2])
    
    def _parse_variable(self, var, *, ptcd=False):
        """
        var :str: a variable literal
        
        return: var, but as a tuple with any references substituted for their literal values
        """
        cop = set()
        for state in map(str.strip, var[1:-1].split(',')): # var[1:-1] cuts out (parens)/{braces}
            if state.isdigit():
                cop.add(int(state))
            elif self.rRANGE.match(state):
                cop.update(TabelRange(state))
            elif state == '...' or ptcd and state == '_':
                cop.update(state)
            else:
                try:
                    cop.update(self.vars[state])
                except KeyError:
                    raise NameError(state) from None
        return tuple(cop)
    
    def extract_directives(self):
        """
        Gets directives from top of ruelfile.

        return: the line number at which var assignment starts.
        """
        for lno, line in enumerate(i.split('#')[0].strip() for i in self):
            if not line:
                continue
            if self.rASSIGNMENT.match(line):
                break
            directive, value = map(str.strip, line.split(':'))
            self.directives[directive] = value
        return 1 + lno
    
    def parse_directives(self):
        """
        Parses extracted directives to understand their values.
        """
        try:
            self.vars['__all__'] = tuple(range(1+int(self.directives['n_states'])))
            cardinals = self.CARDINALS.get(self.directives['neighborhood'])
            if cardinals is None:
                raise TabelValueError(None, f"Invalid neighborhood '{self.directives['neighborhood']}' declared")
            if 'symmetries' not in self.directives:
                raise KeyError("'symmetries'")
        except KeyError as e:
            name = str(e).split("'")[1]
            raise TabelNameError(None, f"'{name}' directive not declared") from None
        return cardinals
    
    def extract_initial_vars(self, start):
        """
        start: line number to start from
        
        Iterates through tabel and gathers all explicit variable declarations.
        
        return: line number at which transition declaration starts
        """
        tblines = ((idx, stmt.strip()) for idx, line in enumerate(self[start:], start) for stmt in line.split('#')[0].split(';'))
        for lno, decl in tblines:
            if self.rTRANSITION.match(decl):
                break
            if not decl or not self.rASSIGNMENT.match(decl):
                continue
            name, value = map(str.strip, decl.split('='))
            if name == '__all__':  # the special var
                self.vars['__all__'] = self._parse_variable(value)
                continue
            if not name.isalpha():
                raise TabelSyntaxError(
                  lno,
                  self._tbl,
                  f"Variable name '{name}' contains nonalphabetical character '{next(i for i in name if not i.isalpha())}'",
                  )
            try:
                self.vars[name] = self._parse_variable(value)
            except NameError as e:
                raise TabelNameError(lno, self._tbl, f"Declaration of variable '{name}' references undefined name '{e}'")
            except classes.errors.KeyConflict:
                raise TabelValueError(lno, self._tbl, f"Value {value} is already assigned to variable {self.vars.inv[value]}")
        self.vars.set_handler(rep_adding_handler)
        return 1 + lno
    
    def parse_ptcd(tr, ptcd, *, lno):
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
        _ = self.rPTCD.match(ptcd)
        copy_to, copy_from = self.cardinals[_[1]], self.cardinals.get(_[2])
        if copy_from is not None:
            raise TabelFeatureUnsupported(lno, self._tbl, 'PTCDs that copy neighbor states are not yet supported')
        map_from = self.vars.inv[tr[copy_to]]  # Catch this IndexError/KeyError
        _map_to, map_to = [], self._parse_variable(_[3], ptcd=True)
        for idx, state in enumerate(map_to):
            if state == '_':  # Leave as is (to be indicated by a None value)
                state = None
            if state == '...':  # Fill out with preceding element (this should be generalized to all mapping actually)
                # TODO: Allow placement of ... in the middle of an expression (it'll be filled in from both sides)
                back = '_' == map_to[idx-1]
                _map_to.append(range(len(map_from)-idx))  # Check isinstance(range) to determine whether to generate anonymous variable
                break
            _map_to.append(state)
        if len(map_from) > len(map_to):
            raise TabelValueError(
                lno,
                self._tbl,
                f"Variable '{copy_to}' (direction {_[1]}) in PTCD mapped to larger variable. Maybe add a '...' to the latter?"
                )
        # Start transition expansion
        transitions = []
        for state in map_to:
            if state is None:
                continue
            if isinstance(state, range):
                ...
            transitions.append(...)
        return transitions
    
    def parse_transitions(self, start):
        for lno, line in enumerate((i.split('#')[0].strip() for i in self[start:]), start):
            if not line:
                continue
            if self.rASSIGNMENT.match(line):
                raise TabelSyntaxError(lno, self._tbl, 'Variable declaration after transitions')
            napkin, ptcd = map(str.strip, line.split('->'))
            try:
                napkin = [self.rCARDINAL.sub(self._cardinal_sub, i.strip()) for i in napkin.split(',')]
            except KeyError as e:
                raise TabelValueError(
                  lno,
                  self._tbl,
                  f"Invalid cardinal direction '{e}' for {self.directives['symmetries']} symmetry"
                  ) from None
            # Parse napkin into proper range of ints
            for idx, elem in enumerate(napkin):
                if elem.isdigit():
                    napkin[idx] = int(elem)
                elif self.rVAR.match(elem):
                    var = self._parse_variable(elem)
                    if var in self.vars.inv:  # conflict handler can't be relied upon; bidict on_dup_val interferes
                        self.vars.inv[var].reps += 1
                    else:  # it's an anonymous (on-the-spot) variable
                        self.vars[Variable.random_name()] = var
                elif not self.rBINDMAP.match(elem):  # leave mappings and bindings untouched for now
                    try:
                        napkin[idx] = self.vars[elem]
                    except KeyError:
                        raise TabelNameError(lno, self._tbl, f"Undefined name '{elem}'")
            self.transitions.extend([napkin, [ptcd]])
        # TODO: step 0.2, step 1.4, step 2.1


class AbstractColors:
    pass


def parse(fp):
    """
    fp: file pointer to a full .ruel file

    return: file, sectioned into dict with tabel and
    colors as convertable representations
    """
    parts = {}
    segment = None
    for line in map(str.strip, fp):
        if not line or line.startswith('#'):
            continue
        if line.startswith('@'):
            # @RUEL, @TABEL, @COLORS, ...
            segment, *name = line.split(None, 1)
            parts[segment] = name
            continue
        parts[segment].append(line)
    parts['@TABEL'] = AbstractTabel(parts['@TABEL'])
    parts['@COLORS'] = AbstractColors(parts['@COLORS'])
    return parts
