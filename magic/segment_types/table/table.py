"""Facilitates parsing of a rueltabel file into an abstract, compiler.py-readable format."""
import re
from itertools import cycle, islice, zip_longest

import bidict

from ...common.errors import *
from ...common.utils import print_verbose
from . import _napkins as napkins, _utils as utils
from ._classes import TabelRange, SpecialVar, VarName, PTCD


class Bidict(bidict.bidict):
    """Just so I can modify on_dup_x without messing with the base bidict cls"""
    on_dup_val = bidict.OVERWRITE


class AbstractTable:
    """
    An abstract, Golly-transferrable representation of a ruelfile's @TABEL section.
    """
    __rCARDINALS = 'NE|NW|SE|SW|N|E|S|W'
    __rRANGE = r'\d+(?:\+\d+)?\s*\.\.\s*\d+'
    __rVAR = (
      r'[({](?:(?:\[?[\w\-]+]?'
      r'(?:\s*\*\s*[\w\-])?|'  # multiplication
     rf'{__rRANGE})*,\s*)*(?:\[?[\w\-*\s]+]?|{__rRANGE}|\.\.\.)'
      r'[})]'
      )
    __rSMALLVAR = (
      r'[({](?:(?:\[?[\w\-]+]?(?:\s*\*\s*[\w\-])?|'
     rf'{__rRANGE})*,\s*)*(?:\[?[\w\-*\s]+]?|{__rRANGE})'
      r'[})]'
      )
    
    _rASSIGNMENT = re.compile(rf'\w+?\s*=\s*-?-?(?:{__rSMALLVAR}|\d+|[A-Za-z]+)(?:--?-?(?:[A-Za-z]+|\d+|{__rSMALLVAR}))?')
    _rBINDMAP = re.compile(rf'\[[0-8](?::\s*?(?:{__rVAR}|[^_][\w\-]+?))?\]')
    _rCARDINAL = re.compile(rf'\b(\[)?({__rCARDINALS})((?(1)\]))\b')
    _rPTCD = re.compile(rf'\b({__rCARDINALS})(?::(\d+)\b|:?\[(?:(0|{__rCARDINALS})\s*:)?\s*(\w+|{__rVAR})\s*]\B)')
    _rTRANSITION = re.compile(
       r'(?<!-)'                                     # To avoid minuends being counted as segments (regardless of comma's presence)
      rf'((?:(?:\d|{__rCARDINALS})'                  # Purely-cosmetic cardinal direction before state (like ", NW 2,")
      rf'(?:\s*\.\.\s*(?:\d|{__rCARDINALS}))?\s+)?'  # Range of cardinal directions (like ", N..NW 2,")
      rf'(?:(?:{__rSMALLVAR}'                        # Variable literal (like ", (1, 2..3, 4),") with no ellipsis allowed at end
       r'|[\w\-]+)+'                                 # Variable name (like ", aaaa,"), some subtraction operation, or a normal numeric state (ad indefiniteness bc subtraction)
      rf'|\[(?:(?:\d|{__rCARDINALS})\s*:\s*)?'       # Or a mapping, which starts with either a number or the equivalent cardinal direction
      rf'(?:{__rVAR}|[0A-Za-z\-]+)]))'               # ...and then has (or only has, in which case it's a binding) either a variable name or literal (like ", [S: (1, 2, ...)]," or ", [0],")
       r'(?:\s*\*\s*[1-8])?'                         # Optional permute-symmetry shorthand...
       r'(,)?\s*'                                    # Then finally, an optional comma + whitespace after it. (Optional because last term has no comma.)
      )
    _rRANGE = re.compile(__rRANGE)
    _rVAR = re.compile(__rVAR)
    
    CARDINALS = {
      'Moore': {'N': 1, 'NE': 2, 'E': 3, 'SE': 4, 'S': 5, 'SW': 6, 'W': 7, 'NW': 8},
      'vonNeumann': {'N': 1, 'E': 2, 'S': 3, 'W': 4},
      'hexagonal': {'N': 1, 'E': 2, 'SE': 3, 'S': 4, 'W': 5, 'NW': 6}
      }
    
    def __init__(self, tbl, start=0, *, dep: '@RUEL'):
        self._src = tbl
        self._start = start
        
        self.vars = Bidict()  # {Variable(name) | str(name) :: tuple(value)}
        self.directives = {}
        self.transitions = []
        self._symmetry_lines = []
        self._constants = {}
        
        if dep is not None:
            self._extract_constants(dep)
        
        _assignment_start = self._extract_directives()
        if self.directives['states'] == '?':
            self._resolve_n_states(_assignment_start)
        self.cardinals = self._parse_directives()
        
        _transition_start = self._extract_initial_vars(_assignment_start)
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
        return iter(self._src)
    
    def __getitem__(self, item):
        return self._src[item]
    
    def __setitem__(self, item, value):
        self._src[item] = value
    
    def match(self, tr):
        """
        Finds the first transition in self.transitions matching tr.
        """
        print('Complete!\n\nSearching for match...')
        sym_cls = napkins.NAMES[self.directives['symmetries']]
        input_tr = utils.unbind_vars(tr, rebind=False)
        start, end = input_tr.pop(0), input_tr.pop(-1)
        in_napkins = sym_cls(input_tr)
        _trs_no_names = enumerate(
          (lno, [
            self.vars.get(state, state)
            for state in utils.unbind_vars(int(i) if isinstance(i, int) or i.isdigit() else i for i in tr)
            ])
          for lno, tr in self.transitions
          )
        target_len = len(tr)
        for idx, (lno, tr) in _trs_no_names:
            for in_tr in ((start, *napkin, end) for napkin in in_napkins.expand()):
                for cur_len, (in_state, tr_state) in enumerate(zip(in_tr, tr), 1):
                    while isinstance(tr_state, str):  # handle lingering bindings
                        tr_state = tr[int(tr_state)]
                    if in_state != '*' and not (in_state == tr_state if isinstance(tr_state, int) else in_state in tr_state):
                        if cur_len == target_len:
                            return (
                              'No match\n\n'
                              f'Impossible match; overridden on line {1+self._start+lno} by "{self[lno]}"\n'
                              f'(compiled line "{", ".join(map(str, self.transitions[idx][1]))}")'
                              )
                        break
                else:
                    return (
                      'Found!\n\n'
                      f'Line {1+self._start+lno}: "{self[lno]}"\n'
                      f'(compiled line "{", ".join(map(str, self.transitions[idx][1]))}")'
                      )
        if start == end:
            return 'No match\nThis transition is the result of default behavior'
        return 'No match'
    
    def _cardinal_sub(self, match):
        try:
            return f"{match[1] or ''}{self.cardinals[match[2]]}{match[3]}"
        except KeyError:
            raise KeyError(match[2])
    
    def _multiply_var(self, a, b, lno):
        a = [int(a)] if a.isdigit() else self._parse_variable(a, lno)
        if b.isdigit():
            return a * int(b)
        return islice(cycle(a), len(self._parse_variable(b, lno)))
    
    def _subtract_var(self, subt, minuend, lno):
        """
        subt: subtrahend
        minuend: minuend
        """
        try:
            match = int(minuend)
        except ValueError:
            match = tuple(i for i in subt if i not in self._parse_variable(minuend, lno))
        else:
            if match > int(self.directives['n_states']):
                raise TabelValueError(lno, f'Minuend -{match} greater than n_states')
            match = tuple(i for i in subt if i != match)
        return match
    
    def __var_loop(self, var, lno, *, mapping=False, ptcd=False, tr=None):
        new = []
        for state in map(str.strip, var.strip('{()}').split(',')):
            if state.isdigit():
                new.append(int(state))
            elif self._rRANGE.match(state):
                try:
                    new.extend(TabelRange(state))
                except ValueError as e:
                    bound = str(e).split("'")[1]
                    raise TabelSyntaxError(lno, f"Bound '{bound}' of range {state} is not an integer")
            elif (mapping or ptcd) and state in ('...', '_'):  # should maybe restrict '_' to only ptcd?
                new.append(state)
                continue
            elif ptcd and '_' == state.split('*')[0].strip():  # eh
                b = state.split('*')[1].strip()
                new.extend('_' * int(b) if b.isdigit() else len(self._parse_variable(b, lno)))
            elif (mapping or ptcd) and self._rBINDMAP.match(state):
                if ':' in state:
                    raise TabelFeatureUnsupported(
                        lno,
                        f"Nested mappings (as with '{state}' in '{var}') "
                        'are not currently supported. Use multiple transitions '
                        'instead'
                        )
                try:
                    new.append(tr[int(state.strip('[]'))])
                except IndexError:
                    raise TabelValueError(lno,
                        f'Nested binding {state} does not refer to a previous index'
                        )
            elif state in self._constants:
                new.append(self._constants[state])
            elif state.startswith('--'):
                # Negation (from all states)
                new.extend(self._subtract_var(self.vars['any'], state[2:], lno))
            elif '-' in state:
                # Subtraction & negation (from live states)
                subt, minuend = state.split('-', 1)  # Actually don't *think* I need to strip bc can't have spaces anyway
                subt = self._parse_variable(subt, lno) if subt else self.vars['live']
                new.extend(self._subtract_var(subt, minuend, lno))
            elif '*' in state:
                new.extend(self._multiply_var(*map(str.strip, state.split('*', 1)), lno))
            else:
                try:
                    new.extend(self.vars[state])
                except KeyError as e:
                    current = 'Output specifier' if ptcd else 'Transition'
                    raise TabelReferenceError(lno, f"{current} references undefined name '{e}'")
        return new
    
    def _parse_variable(self, var: str, lno: int, **kwargs):
        """
        var: a variable literal

        return: var, but as a tuple with any references substituted for their literal values
        """
        if var.isalpha() or var.startswith('_'):
            return self.vars[var]
        if var in self._constants:
            return self._constants[var]
        if var.startswith('--'):
            # Negation (from all states)
            return self._subtract_var(self.vars['any'], var[2:], lno)
        if '-' in var and not self._rVAR.fullmatch(var):  # top-level subtraction
            # Subtraction & negation (from live states)
            subt, minuend = var.split('-', 1)
            subt = self._parse_variable(subt, lno) if subt else self.vars['live']
            return self._subtract_var(subt, minuend, lno)
        return tuple(self.__var_loop(var, lno, **kwargs))
    
    def _fix_symmetries(self):
        transitions, self.directives['symmetries'] = utils.desym(
          [(lno, utils.unbind_vars(tr, bind_keep=True)) for lno, tr in self.transitions],
          self._symmetry_lines
          )
        self.transitions = [(lno, utils.bind_vars(tr, second_pass=True, return_reps=False)) for lno, tr in transitions]
    
    def _resolve_n_states(self, start):
        """
        Absolutely disgusting.
        But sorta neatish.
        """
        r_int = re.compile(r'(?<!\w|\[)\d+(?!\w|])')  # Fails if the user decides to put [ 0 ] spaces inside their binding brackets...
        self.directives['states'] = 1 + max(
          int(match.group().strip())
          for line in self[start:]
          for match in r_int.finditer(line.split('#')[0])
          )
        print_verbose(['Found n_states:', self.directives['states']])
    
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
            if not directive.isalpha():
                break
            self.directives[directive] = value.replace(' ', '')
        return lno
    
    def _parse_directives(self):
        """
        Parse extracted directives to translate their values.
        Also initialize the "any" and "live" variables.
        """
        if self.directives['symmetries'] is not None:
            self._symmetry_lines.append((-1, self.directives['symmetries']))
        try:
            self.vars[VarName('any')] = SpecialVar(range(int(self.directives['states'])))
            cardinals = self.CARDINALS.get(self.directives['neighborhood'])
            if cardinals is None:
                raise TabelValueError(None, f"Invalid neighborhood {self.directives['neighborhood']!r} declared")
        except KeyError as e:
            name = str(e).split("'")[1]
            raise TabelReferenceError(None, f'{name!r} directive not declared')
        self.vars[VarName('live')] = SpecialVar(self.vars['any'][1:])
        self.directives['n_states'] = self.directives.pop('states')
        return cardinals
    
    def _extract_constants(self, dep):
        """
        Extract constants from @RUEL section, defined as follows:

            <state>: <...> {<name>} <...>
        
        Where <name> is the constant's name.
        Additionally, {<name>} is removed from final @RUEL output.
        """
        r_const = re.compile(r'(\s*)(\d+):(.*?)\s*\{\s*(.+)\s*}(.*)')
        found = False
        for lno, line in enumerate(dep):
            match = r_const.match(line)
            if match is not None:
                _0, state, _1, name, _2 = match.groups()
                self._constants[name] = int(state)
                dep[lno] = f'{_0}{state}:{_1}{_2}'
                found = True
        if found:
            r_consts = re.compile(r'\b' + r'\b|\b'.join(self._constants) + r'\b')
            for idx, line in enumerate(self):
                self[idx] = r_consts.sub(lambda m: str(self._constants[m[0]]), line)
    
    def _extract_initial_vars(self, start):
        """
        start: line number to start from
        
        Iterate through table and gather all explicit variable declarations.
        
        return: line number at which transition declaration starts
        """
        lno = start
        tblines = ((idx, stmt.strip()) for idx, line in enumerate(self[start:], start) for stmt in line.split('#')[0].split(';'))
        _live, _any = self.vars['live'], self.vars['any']
        for lno, decl in tblines:
            if utils.globalmatch(self._rTRANSITION, decl.split('->')[0].strip()):
                break
            if not decl:
                continue
            if not self._rASSIGNMENT.fullmatch(decl):
                raise TabelSyntaxError(lno, f'Invalid syntax in variable declaration')
            name, value = map(str.strip, decl.split('='))
            
            if value.isdigit():
                self._constants[name] = int(value)
                continue
            
            try:
                var = self._parse_variable(value, lno)
            except TabelReferenceError as e:
                bad = str(e).split("'")[1]
                if not bad:  # Means two consecutive commas, or a comma at the end of a literal
                    raise TabelSyntaxError(lno, 'Invalid comma placement in variable declaration')
                adjective = 'undefined' if bad.isalpha() else 'invalid'
                raise TabelReferenceError(lno, f'Declaration of variable {name!r} references {adjective} name {bad!r}')
            
            if not name.isalpha():
                raise TabelSyntaxError(
                  lno,
                  f'Variable name {name!r} contains nonalphabetical character {next(i for i in name if not i.isalpha())!r}',
                  )
            try:
                self.vars[VarName(name)] = var
            except bidict.ValueDuplicationError:  # Deprecated currently
                raise TabelValueError(lno, f"Value {value} is already assigned to variable '{self.vars.inv[var]}'")
        # bidict devs, between the start of this project and 5 May 2018,
        # decided to make bidict().on_dup_val a read-only property
        # so this was formerly just `self.vars.on_dup_val = bidict.IGNORE`
        self.vars.__class__.on_dup_val = bidict.IGNORE
        return lno
    
    def _parse_transitions(self, start):
        """
        start: line number to start on
        
        Parse all the ruel's transitions into a list in self.transitions.
        """
        # They can change, but an initial set of symmetries needs to be declared before transitions
        try:
            start = next(lno for lno, line in enumerate((i.split('#')[0].strip() for i in self[start:]), start) if line)
        except StopIteration:
            # No transitions
            return
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
                  f"Invalid cardinal direction {e} for {self.directives['neighborhood']!r} neighborhood"
                  )
            try:
                napkin = utils.expand_tr(napkin)
            except ValueError as e:
                group, expected, got = e.args
                raise TabelValueError(lno, f'Expected lower value of {expected} in group {group}, got {got}')
            # Parse napkin into proper range of ints
            for idx, elem in enumerate(napkin):
                if elem.isdigit():
                    napkin[idx] = int(elem)
                elif self._rVAR.match(elem) or '-' in elem and not self._rBINDMAP.match(elem):
                    self.vars[VarName.random()] = napkin[idx] = self._parse_variable(elem, lno)
                elif not self._rBINDMAP.match(elem):  # leave mappings and bindings untouched for now
                    try:
                        napkin[idx] = self.vars[elem] if elem in self.vars else self._constants[elem]
                    except KeyError:
                        raise TabelReferenceError(lno, f'Transition references undefined name {elem!r}')
            ptcds = [(lno, tr) for ptcd in self._rPTCD.finditer(ptcds) for tr in PTCD(self, napkin, ptcd, lno=lno)]
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
              (val[0], list(self._parse_variable(val[1], lno)), list(self._parse_variable(val[2], lno, tr=tr, mapping=True)))
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
                    self.vars[VarName.random()] = new = tuple(map_from[len(map_to)-2:])
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
            self.transitions[tr_idx:1+tr_idx] = None, *zip_longest([lno], new, fillvalue=lno)
        self.transitions = list(filter(None, self.transitions))
