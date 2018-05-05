"""Facilitates parsing of a rueltabel file into an abstract, computer-readable format."""
import re
import struct
from itertools import zip_longest as zipln

import bidict

from . import desym
from .common import utils
from .common.classes import napkins, Coord, TabelRange, Variable
from .common.classes.errors import TabelNameError, TabelSyntaxError, TabelValueError, TabelException
from .common.utils import print_verbose
from .icon_fixer import IconArray


class AbstractTable:
    """
    An abstract, Golly-transferrable representation of a ruelfile's @TABEL section.
    """
    __rCARDINALS = 'NE|NW|SE|SW|N|E|S|W'
    __rVAR = r'[({](?:\w*\s*(?:,|\.\.)\s*)*(?:\w|(?:\.\.\.)?)*[})]'
    
    _rASSIGNMENT = re.compile(rf'\w+?\s*=\s*{__rVAR}')
    _rBINDMAP = re.compile(rf'\[[0-8](?::\s*?(?:{__rVAR}|[^_]\w+?))?\]')
    _rCARDINAL = re.compile(rf'\b(\[)?({__rCARDINALS})((?(1)\]))\b')
    _rPTCD = re.compile(rf'\b({__rCARDINALS})(?::(\d+)\b|:?\[(?:(0|{__rCARDINALS})\s*:)?\s*(\w+|{__rVAR})\s*]\B)')
    _rRANGE = re.compile(r'\d+? *?\.\. *?\d+?')
    _rTRANSITION = re.compile(
       r'(?<!-)'                                     # To avoid minuends being counted as segments (regardless of comma's presence)
      rf'((?:(?:\d|{__rCARDINALS})'                  # Purely-cosmetic cardinal direction before state (like ", NW 2,")
      rf'(?:\s*\.\.\s*(?:\d|{__rCARDINALS}))?\s+)?'  # Range of cardinal directions (like ", N..NW 2,")
       r'(?:-?-?\d+|'                                # Normal state (like ", 2,")
       r'-?-?(?:[({](?:\w*\s*(?:,|\.\.)\s*)*\w+[})]' # Variable literal (like ", (1, 2..2, 3),") with no ellipsis allowed at end
       r'|[A-Za-z]+)'                                # Variable name (like ", aaaa,")
      rf'|\[(?:(?:\d|{__rCARDINALS})\s*:\s*)?'       # Or a mapping, which starts with either a number or the equivalent cardinal direction
      rf'(?:{__rVAR}|[A-Za-z]+)])'                   # ...and then has either a variable name or literal (like ", [S: (1, 2, ...)],")
      r'(?:-(?:(?:\d+|(?:[({](?:\w*\s*(?:,|\.\.)\s*)*\w+[})]|[A-Za-z]+)|)))?)'  # Subtrahends can't be bindings/mappings
       r'(?:\s*:\s*[1-8])?'                          # Optional permute-symmetry shorthand...
       r'(,)?(?(2)\s*)'                              # Then finally, an optional comma + whitespace after it. Last term has no comma.
      )
    _rSEGMENT = re.compile(
      r'(?:((?:\d|{__rCARDINALS})(?:\s*\.\.\s*(?:\d|{__rCARDINALS}))?)\s+)?([A-Za-z]+|[({](?:\w*\s*(?:,|\.\.)\s*)*\w+[})])'
      )
    _rVAR = re.compile(__rVAR)
    
    CARDINALS = {
      'Moore': {'N': 1, 'NE': 2, 'E': 3, 'SE': 4, 'S': 5, 'SW': 6, 'W': 7, 'NW': 8},
      'vonNeumann': {'N': 1, 'E': 2, 'S': 3, 'W': 4},
      'hexagonal': {'N': 1, 'E': 2, 'SE': 3, 'S': 4, 'W': 5, 'NW': 6}
      }
    
    def __init__(self, tbl, start=0):
        self._tbl = tbl
        self._start = start
        
        self.vars = bidict.bidict()  # {Variable(name) | str(name) :: tuple(value)}
        self.var_all, self.var_all_rep = (), 0  # instead of self.vars['__all__']
        self.directives = {}
        self.transitions = []
        self._symmetry_lines = []
        
        _assignment_start = self._extract_directives()
        _transition_start = self._extract_initial_vars(_assignment_start)
        
        self.cardinals = self._parse_directives()
        print_verbose(
          '\b'*4 + 'PARSED directives & var assignments',
          ['\b\bdirectives:', self.directives, '\b\bvars:', self.vars],
          pre='    ', sep='\n', end='\n'
          )
        
        self._parse_transitions(_transition_start)
        print_verbose(
          '\b'*4 + 'PARSED transitions & output specifiers',
          ['\b\btransitions (before binding):', *self.transitions, '\b\bvars:', self.vars],
          pre='    ', sep='\n', end='\n'
          )
        
        self._disambiguate()
        print_verbose(
          '\b'*4 + 'DISAMBIGUATED variables',
          ['\b\btransitions (after binding):', *self.transitions, '\b\bvars:', self.vars],
          pre='    ', sep='\n', end='\n\n'
          )
        
        self._expand_mappings()
        print_verbose(
          '\b'*4 + 'EXPANDED mappings',
          ['\b\btransitions (after expanding):', *self.transitions, '\b\bvars:', self.vars],
          pre='    ', sep='\n', end='\n\n'
          )
        
        self._fix_symmetries()
    
    def __iter__(self):
        return iter(self._tbl)
    
    def __getitem__(self, item):
        return self._tbl[item]
    
    def match(self, tr):
        """
        Finds the first transition in self.transitions matching tr.
        """
        print('Complete!\n\nSearching for match...')
        sym_cls = napkins.NAMES[self.directives['symmetries']]
        in_tr = utils.unbind_vars(tr, rebind=False)
        start, end = in_tr.pop(0), in_tr.pop(-1)
        in_napkins = sym_cls(in_tr)
        _trs_no_names = enumerate(
          (lno, [
            self.vars.get(state, self.var_all if state == '__all__' else state)
            for state in utils.unbind_vars(int(i) if isinstance(i, int) or i.isdigit() else i for i in tr)
            ])
          for lno, tr in self.transitions
          )
        for idx, (lno, tr) in _trs_no_names:
            for in_tr in ((start, *napkin, end) for napkin in in_napkins.expand()):
                for in_state, tr_state in zip(in_tr, tr):
                    while isinstance(tr_state, str):
                        tr_state = tr[int(tr_state)]
                    if not (in_state == tr_state if isinstance(tr_state, int) else in_state in tr_state):
                        break
                else:
                    return f'Found!\n\nLine {1+self._start+lno}: "{self[lno]}"\n(compiled line "{", ".join(map(str, self.transitions[idx][1]))}")\n'
        return None
    
    def _cardinal_sub(self, match):
        try:
            return f"{match[1] or ''}{self.cardinals[match[2]]}{match[3]}"
        except KeyError:
            raise KeyError(match[2])
    
    def _subtract_var(self, subt, minuend):
        """
        subt: subtrahend
        minuend: minuend
        """
        try:
            match = int(minuend)
        except ValueError:
            match = tuple(i for i in subt if i not in self._parse_variable(minuend))
        else:
            if match > int(self.directives['n_states']):
                raise ValueError('negated value greater than n_states hm')
            match = tuple(i for i in subt if i != match)
        self.vars[Variable.random_name()] = match
        return match
    
    def _parse_variable(self, var: str, *, mapping=False, ptcd=False):
        """
        var: a variable literal

        return: var, but as a tuple with any references substituted for their literal values
        """
        if var.isalpha() or var.startswith('_'):
            return self.vars[var]
        if var.startswith('--'):
            # Negation (from all states)
            return self._subtract_var(self.var_all, var[2:])
        if '-' in var:
            # Subtraction & negation (from live states)
            subt, minuend = map(str.strip, var.split('-'))  # Actually don't *think* I need to strip bc can't have spaces anyway
            subt = self._parse_variable(subt) if subt else self.vars['live']
            return self._subtract_var(subt, minuend)
        cop = []
        for state in map(str.strip, var.strip('{()}').split(',')):
            if state.isdigit():
                cop.append(int(state))
            elif self._rRANGE.match(state):
                try:
                    cop.extend(TabelRange(state))
                except ValueError as e:
                    raise SyntaxError((str(e).split("'")[1], state)) from None
            elif mapping and state == '...' or ptcd and state in ('...', '_'):
                cop.append(state)
            else:
                try:
                    cop.extend(self.vars[state])
                except KeyError:
                    raise NameError(state) from None
        return tuple(cop)
    
    def _fix_symmetries(self):
        transitions, self.directives['symmetries'] = desym.normalize(
          [(lno, utils.unbind_vars(tr, bind_keep=True)) for lno, tr in self.transitions],
          self._symmetry_lines
          )
        self.transitions = [(lno, utils.bind_vars(tr, second_pass=True, return_reps=False)) for lno, tr in transitions]
    
    def _extract_directives(self, start=0):
        """
        Get directives from top of ruelfile.
        
        return: the line number at which var assignment starts.
        """
        self.directives['symmetries'] = None
        lno = start
        for lno, line in enumerate((i.split('#')[0].strip() for i in self), start):
            if not line:
                continue
            try:
                directive, value = map(str.strip, line.split(':'))
            except ValueError:
                break
            self.directives[directive] = value.replace(' ', '')
        return lno
    
    def _parse_directives(self):
        """
        Parse extracted directives to translate their values.
        Also initialize the "__all__" and "any" variables.
        """
        if self.directives['symmetries'] is not None:
            self._symmetry_lines.append((-1, self.directives['symmetries']))
        try:
            self.var_all = tuple(range(int(self.directives['states'])))
            cardinals = self.CARDINALS.get(self.directives['neighborhood'])
            if cardinals is None:
                raise TabelValueError(None, f"Invalid neighborhood {self.directives['neighborhood']!r} declared")
        except KeyError as e:
            name = str(e).split("'")[1]
            raise TabelNameError(None, f'{name!r} directive not declared')
        self.directives['n_states'] = self.directives.pop('states')
        self.vars[Variable('any')] = self.var_all  # Provided beforehand
        self.vars[Variable('live')] = self.var_all[1:]  # Ditto^, all living states
        return cardinals
    
    def _extract_initial_vars(self, start):
        """
        start: line number to start from
        
        Iterate through table and gather all explicit variable declarations.
        
        return: line number at which transition declaration starts
        """
        lno = start
        tblines = ((idx, stmt.strip()) for idx, line in enumerate(self[start:], start) for stmt in line.split('#')[0].split(';'))
        for lno, decl in tblines:
            if utils.globalmatch(self._rTRANSITION, decl.split('->')[0].strip()):
                break
            if not decl:
                continue
            if not self._rASSIGNMENT.fullmatch(decl):
                raise TabelSyntaxError(lno, f'Invalid syntax in variable declaration (please let Wright know ASAP if this is incorrect)')
            name, value = map(str.strip, decl.split('='))

            try:
                var = self._parse_variable(value)
            except NameError as e:
                if not str(e):  # Means two consecutive commas, or a comma at the end of a literal
                    raise TabelSyntaxError(lno, 'Invalid comma placement in variable declaration')
                adj = 'undefined' if str(e).isalpha() else 'invalid'
                raise TabelNameError(lno, f"Declaration of variable {name!r} references {adj} name '{e}'")
            except SyntaxError as e:
                bound, range_ = e.msg
                raise TabelSyntaxError(lno, f"Bound '{bound}' of range {range_} is not an integer")
            
            if name == '__all__':  # the special var
                self.var_all = var
                continue
            if not name.isalpha():
                raise TabelSyntaxError(
                  lno,
                  f'Variable name {name!r} contains nonalphabetical character {next(i for i in name if not i.isalpha())!r}',
                  )
            try:
                self.vars[Variable(name)] = var
            except bidict.ValueDuplicationError:
                raise TabelValueError(lno, f"Value {value} is already assigned to variable '{self.vars.inv[var]}'")
        # bidict devs, between the start of this project and 5 May 2018,
        # decided to make bidict().on_dup_val a read-only property
        # so this was formerly just `self.vars.on_dup_val = bidict.IGNORE`
        self.vars.__class__.on_dup_val = bidict.IGNORE
        return lno
    
    def __make_center_tr(self, tr, initial, result, orig, source_cd):
        """
        Handles making a transition from PTCD iff the source and copy-to cells happen to be the same.
        """
        new_tr = [initial, *['__all__']*len(self.cardinals), result]
        # Get adjacent cells to original cell (diagonal to current)
        try:
            new_tr[self.cardinals[orig.name]] = tr[0]
        except KeyError:
            pass
        try:
            new_tr[self.cardinals[orig.cw.name]] = utils.of(tr, self.cardinals[orig.cw.move(source_cd).name])
        except KeyError:
            pass
        try:
            new_tr[self.cardinals[orig.ccw.name]] = utils.of(tr, self.cardinals[orig.ccw.move(source_cd).name])
        except KeyError:
            pass
        # If we're orthogonal to orig, we have to count for the cells adjacent to us too
        if not orig.diagonal():
            try:
                new_tr[self.cardinals[orig.cw(2).name]] = utils.of(tr, self.cardinals[orig.cw(3).name])
            except KeyError:
                pass
            try:
                new_tr[self.cardinals[orig.ccw(2).name]] = utils.of(tr, self.cardinals[orig.ccw(3).name])
            except KeyError:
                pass
        return new_tr
    
    def _make_transition(self, tr: list, source_cd: str, cd_to: str, initial, result):
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
        new_tr = self.__make_center_tr(tr, initial, result, orig, source_cd)
        if cd_to is None:
            return new_tr
        # Otherwise, we have to fiddle with the values at the initial and new_relative indices
        try:
            new_tr[0] = tr[self.cardinals[cur.name]]
        except KeyError:
            pass
        new_relative = orig if cd_to == '0' else orig.move(cd_to)  # position of "copy_to" cell relative to current
        # new_relative == South (which is West moved SouthEast) | [CENTER] (which is West moved East)
        if new_relative.center():
            return new_tr
        try:
            new_tr[self.cardinals[new_relative.name]] = initial
        except KeyError:
            pass
        return new_tr
    
    def _extract_ptcd_vars(self, tr, match, lno):
        """
        tr: a transition
        match: matched output specifier (regex match object)
        lno: current line number
        
        Parse the 'variable' segments of an output specifier.
        
        return: Output specifier's variables
        """
        copy_to = tr[self.cardinals[match[1]]] if match[3] is None else tr[match[3] != '0' and self.cardinals[match[3]]]
        if match[2] is not None:  # Means it's a simple "CD:state" instead of a "CD[variable]"
            return match[1], copy_to, map(int, match[2])
        if match[4] in ('0', *self.cardinals) and match[3] is None:
            index = match[4] != '0' and self.cardinals[match[4]]
            return match[1], match[4], tr[index], tr[index]
        try:
            _map_to, map_to = [], self._parse_variable(match[4], ptcd=True)
        except NameError as e:
            raise TabelNameError(lno, f"Output specifier references undefined name '{e}'")
        except SyntaxError as e:
            bound, range_ = e.msg
            raise TabelSyntaxError(lno, f"Bound '{bound}' of range {range_} is not an integer")
        for idx, state in enumerate(map_to):
            if state == '_':  # Leave as is (indicated by a None value)
                state = None
            if state == '...':  # Fill out with preceding element (this should be generalized to all mappings actually)
                # TODO: Allow placement of ... in the middle of an expression (to be filled in from both sides)
                _map_to.append(range(idx, len(copy_to)))  # Check isinstance(range) to determine whether to generate anonymous variable
                break
            _map_to.append(state)
        if len(copy_to) > sum(len(i) if isinstance(i, range) else 1 for i in _map_to):
            raise TabelValueError(
              lno,
              f"Variable at index {int(match[1] != '0') and self.cardinals[match[1]]} in output specifier (direction {match[1]})"
              " mapped to a smaller variable. Maybe add a '...' to fill the latter out?"
              )
        return match[1], match[3], copy_to, _map_to

    def _parse_ptcd(self, tr, match, lno):
        """
        tr: a fully-parsed transition statement
        ptcd: a output specifier
        variables: global dict of variables
        
        output specifiers can be
            CD[(var_literal)]
            CD[variable]
        Or
            CD[CD: (var_literal)]
            CD[CD: variable]
        
        return: output specifier expanded into its full transition(s)
        """
        cd_idx, copy_idx, copy_to, map_to = self._extract_ptcd_vars(tr, match, lno)
        # Start expanding to transitions
        transitions = []
        while isinstance(copy_to, str) and copy_to.startswith('['):
            copy_idx = int(utils.rBINDING.match(copy_to)[1])
            copy_to = tr[copy_idx]
        if copy_to == map_to:
            transitions.append(self._make_transition(tr, cd_idx, copy_idx, copy_to, f'[{self.cardinals[Coord.from_name(cd_idx).inv.name]}]'))
            return transitions
        for idx, (initial, result) in enumerate(zip(copy_to, map_to)):
            if result is None:
                continue
            # If the result is an ellipsis, fill out
            if isinstance(result, range):
                if map_to[idx-1] is None:  # Nothing more to add
                    break
                new_initial = copy_to[result[0]:]
                transitions.append(self._make_transition(tr, cd_idx, copy_idx, new_initial, map_to[idx-1]))
                self.vars[Variable.random_name()] = new_initial
                break
            transitions.append(self._make_transition(tr, cd_idx, copy_idx, initial, result))
        return transitions
    
    def _parse_transitions(self, start):
        """
        start: line number to start on
        
        Parse all the ruel's transitions into a list in self.transitions.
        """
        # They can change, but an initial set of symmetries needs to be declared before transitions
        start = next(lno for lno, line in enumerate((i.split('#')[0].strip() for i in self[start:]), start) if line)
        if self.directives['symmetries'] is None:
            raise TabelSyntaxError(start, "Transition before initial declaration of 'symmetries' directive")
        lno = start
        for lno, line in enumerate((i.split('#')[0].strip() for i in self[start:]), start):
            if line.startswith('symmetries:'):
                sym = line.split(':')[1].strip().replace(' ', '')
                self._symmetry_lines.append((lno, sym))
                self.directives['symmetries'] = sym
                continue
            if not line:
                continue
            if self._rASSIGNMENT.match(line):
                raise TabelSyntaxError(lno, 'Variable declaration after first transition')
            napkin, ptcds = map(str.strip, line.partition('->')[::2])
            if self.directives['symmetries'] == 'permute':
                napkin = utils.conv_permute(napkin, len(self.cardinals))
            try:
                napkin = [self._rCARDINAL.sub(self._cardinal_sub, i.strip()) for i, _ in self._rTRANSITION.findall(napkin)]
            except KeyError as e:
                raise TabelValueError(
                  lno,
                  f"Invalid cardinal direction {e} for {self.directives['symmetries']!r} symmetry"
                  )
            napkin = utils.expand_tr(napkin)
            # Parse napkin into proper range of ints
            for idx, elem in enumerate(napkin):
                if elem.isdigit():
                    napkin[idx] = int(elem)
                elif self._rVAR.match(elem) or '-' in elem:
                    self.vars[Variable.random_name()] = napkin[idx] = self._parse_variable(elem)
                elif not self._rBINDMAP.match(elem):  # leave mappings and bindings untouched for now
                    try:
                        napkin[idx] = self.vars[elem]
                    except KeyError:
                        raise TabelNameError(lno, f'Transition references undefined name {elem!r}')
            ptcds = [(lno, tr) for ptcd in self._rPTCD.finditer(ptcds) for tr in self._parse_ptcd(napkin, ptcd, lno=lno)]
            self.transitions.extend([(lno, napkin), *ptcds])
    
    def _disambiguate(self):
        """
        Properly disambiguate variables in transitions, then resolve
        [bracketed bindings] and convert mappings to Python tuples.
        """
        print_verbose(None, None, '...disambiguating variables...', pre='')
        for idx, (lno, tr) in enumerate(self.transitions):
            print_verbose(*[None]*3, [tr, '->'], start='', sep='', end='')
            try:
                reps, tr = utils.bind_vars(
                  self.vars.inv[val].name
                  if val in self.vars.inv
                    else val
                  for val in tr
                  )
            except SyntaxError as e:
                raise TabelSyntaxError(lno, e.msg)
            except ValueError as e:
                raise TabelValueError(lno, e.args[0])
            
            self.transitions[idx] = lno, [
              # list() because we're need to mutate it if it has an ellipsis
              (val[0], list(self._parse_variable(val[1])), list(self._parse_variable(val[2], mapping=True)))
              if isinstance(val, tuple)
                else val
              for val in tr
              ]
            
            # filter out everything except mappings, so we can expand their ellipses if applicable
            for i, (tr_idx, map_from, map_to) in ((j, t) for j, t in enumerate(self.transitions[idx][1]) if isinstance(t, tuple)):
                if map_to[-1] == '...':
                    map_to[-1] = map_to[-2]
                    # Replace the extra states in map_to with a variable name
                    # Could be a new variable or it could be one with same value
                    self.vars[Variable.random_name()] = new = tuple(map_from[len(map_to)-2:])
                    map_from[len(map_to)-2:] = [self.vars.inv[new].name]
                if len(map_from) > len(map_to):
                    raise TabelValueError(
                      lno,
                      f"Variable with value {map_from} mapped to a smaller variable with "
                      f"value {tuple(map_to)}. Maybe add a '...' to fill the latter out?"
                      )
                self.transitions[idx][1][i] = (tr_idx, tuple(map_from), tuple(map_to))
            
            print_verbose(*[None]*3, [tr, '->', self.transitions[idx], '\n  reps:', reps], sep='', end='\n\n')
            for name, rep in reps.items():
                if name == '__all__':
                    self.var_all_rep = max(rep, self.var_all_rep)
                    continue
                var = self.vars[name]
                if rep > self.vars.inv[var].rep:
                    self.vars.inv[var].rep = rep
    
    def _expand_mappings(self):
        """
        Iteratively expand mappings in self.transitions, starting from
        earlier ones and going down the branches.
        """
        print_verbose(None, None, '...expanding mappings...', pre='')
        for tr_idx, (lno, tr) in enumerate(self.transitions):
            try:
                # The only tuples left are mappings because we replaced var values w their names
                # ...that also happens to be why it's hard for me (at this stage) to collapse
                # redundant ellipsis mappings into their own anonymous variables -- because
                # we've already disambiguated and hmmmm
                sub_idx, (idx, froms, tos) = next((i, t) for i, t in enumerate(tr) if isinstance(t, tuple))
            except StopIteration:
                continue
            print_verbose(*[None]*3, [tr, '\n', '->'], start='', sep='', end='\n')
            new = []
            for map_from, map_to in zip(froms, tos):
                reps, built = utils.bind_vars(
                  [map_from if v == tr[idx] else map_to if v == (idx, froms, tos) else v for i, v in enumerate(tr)],
                  second_pass=True
                  )
                new.append(built)
                for name, rep in reps.items():  # Update self.vars with new info
                    var = self.vars[name]
                    if rep > self.vars.inv[var].rep:
                        self.vars.inv[var].rep = rep
            print_verbose(*[None]*3, new, start='', sep='\n', end='\n\n')
            # We need to add an extraneous pre-value in order for the loop to catch the next "new"
            # because we're mutating the list while we iterate over it
            # (awful, I know)
            self.transitions[tr_idx:1+tr_idx] = None, *zipln([lno], new, fillvalue=lno)
        self.transitions = list(filter(None, self.transitions))


class ColorSegment:
    """
    Parse a ruelfile's color format into something abstract &
    transferrable into Golly syntax.
    """
    _rGOLLY_COLOR = re.compile(r'\s*(\d{0,3})\s+(\d{0,3})\s+(\d{0,3})\s*.*')
    
    def __init__(self, colors, start=0):
        self._src = colors
        self.colors = [k.split(':') for k in self._src if k]
    
    def __iter__(self):
        return (f'{state} {r} {g} {b}' for d in self.states for state, (r, g, b) in d.items())
    
    def _unpack(self, color):
        m = self._rGOLLY_COLOR.fullmatch(color)
        if m is not None:
            return m[1], m[2], m[3]
        if len(color) % 2:  # three-char shorthand
            color *= 2
        return struct.unpack('BBB', bytes.fromhex(color))
    
    @property
    def states(self):
        return ({int(j.strip()): self._unpack(color.strip())} for state, color in self.colors for j in state.split())

CONVERTERS = {
  '@ICONS': IconArray,
  '@COLORS': ColorSegment,
  '@TABEL': AbstractTable
  }

def parse(fp):
    """
    fp: file pointer to a full .ruel file
    
    return: file, sectioned into dict with table and
    colors as convertable representations
    """
    parts, lines = {}, {}
    segment = None
    
    for lno, line in enumerate(map(str.strip, fp), 1):
        if line.startswith('@'):
            # @RUEL, @TABEL, @COLORS, ...
            sep = (None, ':')[':' in line]
            segment, *name = map(str.strip, line.split(sep))
            parts[segment], lines[segment] = name, lno
            continue
        parts[segment].append(line)
    
    for lbl, converter in CONVERTERS.items():
        try:
            segment, seg_lno = parts[lbl], lines[lbl]
        except KeyError:
            continue
        if segment[0] == 'golly':
            parts[lbl] = segment[1:]
            continue
        try:
            parts[lbl] = converter(segment, seg_lno)
        except TabelException as exc:
            if exc.lno is None:
                raise exc.__class__(exc.lno, exc.msg)
            raise exc.__class__(exc.lno, exc.msg, segment, seg_lno)
    
    return parts
