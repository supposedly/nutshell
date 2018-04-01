import random
import re
from collections import namedtuple

from .common import classes, utils
from .common.classes import Variable

rASSIGNMENT = re.compile(r'.+? *?= *?[({][\w,]+?[})]')
rBINDMAP = re.compile(r'\[[0-8](?::\s*?(?:[({][\[\]\w,]+?[})]|[^_]\w+?))?\]')
rCARDINAL = re.compile(r'\b(\[)?(N|NE|E|SE|S|SW|W|NW)((?(1)\]))\b')
rRANGE = re.compile(r'\d+? *?\.\. *?\d+?')
rTRANSITION = re.compile('[^,]+?(?:,[^,]+)+')
rVAR = re.compile(r'[({][\w,]+?[})]')

CARDINALS = {
  'Moore': {'N': 1, 'NE': 2, 'E': 3, 'SE': 4, 'S': 5, 'SW': 6, 'W': 7, 'NW': 8},
  'vonNeumann': {'N': 1, 'E': 2, 'S': 3, 'W': 4}
  }
Transition = namedtuple('Transition', ('napkin', 'to'))


def rep_adding_handler(self, key, value):
    """
    Replaces default ConflictHandlingBiDict conflict_handler.
    Instead of raising exception, appends to var's reps
    """
    (key if isinstance(key, Variable) else value).reps += 1
    return key, value


def parse_variable(var, variables):
    """
    var: string, formatted like a variable literal
    variables: the global dict of tabel's variables

    return: var, but as a list with any references substituted for their literal values
    """
    var = [i.strip() for i in var[1:-1].split(',')]  # var[1:-1] cuts out (parens)/{braces}
    for idx, state in enumerate(var):
        if state.isdigit():
            var[idx] = int(state)
        elif rRANGE.match(state):
            # There will only ever be two numbers in the range; `i`
            # will be 0 on first pass and 1 on second, so adding
            # it to the given integer will account for python's
            # ranges being exclusive of the end value (it adds
            # 1 on the second pass)
            var[idx:1+idx] = range(*(i+int(v.strip()) for i, v in enumerate(state.split('..'))))
        else:
            try:
                var[idx:1+idx] = variables[state]
            except KeyError:
                raise NameError(state)
    return var
    

def extract_initial_vars(start, tbl, variables=None):
    """
    start: line number to start from
    tbl: the tabel to parse
    variables: the global dict of tabel's variables

    Iterates through the table and gathers all explicit variable declarations.

    return: a bidict of said variables
    {Variable(name, reps): (state1, state2, ..., staten)}
    """
    if variables is None:
        variables = classes.ConflictHandlingBiDict()
    tblines = ((idx, stmt.strip()) for idx, line in enumerate(tbl, start) for stmt in line.split('#')[0].split(';'))
    for lno, decl in tblines:
        if rTRANSITION.match(decl):
            break
        if not decl or not rASSIGNMENT.match(decl):
            continue
        
        name, value = map(str.strip, decl.split('='))
        if name == '__all__':  # a special var
            variables['__all__'] = parse_variable(value, variables)
            continue
        if not name.isalpha():
            raise ValueError(f"Variable name '{name}' contains nonalphabetical characters")
        
        try:
            variables[name] = parse_variable(value, variables)
        except NameError as e:
            raise NameError(f"Declaration of variable '{name}' references undefined variable '{e}'") from None
        except classes.errors.KeyConflict:
            raise ValueError(f"Value {value} is already assigned to variable {variables.inv[value]}") from None
    
    variables.set_handler(rep_adding_handler)
    return tbl[lno:], lno, variables


def extract_directives(tbl, variables=None):
    """
    tbl: the tabel to parse
    variables: the global dict of tabel's variables

    return: a list of all directives (symmetries, nhood, n_states, ...)
    declared at the top of a tabel.
    """
    directives = {}
    for lno, line in enumerate(i.split('#')[0].strip() for i in tbl):
        if not line:
            continue
        if rASSIGNMENT.match(line):
            break
        directive, value = map(str.strip, line.split(':'))
        directives[directive] = value
    return lno, tbl[lno:], directives


def tabelparse(tbl):
    """
    tbl: tabel to parse

    The main func. Parses everything in the @TABEL section.

    return: abstract representation of tbl
    """
    transitions = []
    variables = classes.ConflictHandlingBiDict()
    start_assn, tbl, directives = extract_directives(tbl)
    try:
        variables['__all__'] = tuple(range(1+int(directives['n_states'])))
        cardinals = CARDINALS.get(directives['nhood'])
        if cardinals is None:
            raise ValueError(f"Invalid neighborhood '{directives['nhood']}' declared")
        if 'symmetries' not in directives:
            raise KeyError("'symmetries'")
    except KeyError as e:
        var = str(e).split("'")[1]
        raise NameError(f'{var} directive was never declared') from None
    
    def cardinal_sub(m):
        try:
            return f"{m[1] or ''}{cardinals[m[2]]}{m[3]}"
        except KeyError:
            raise KeyError(m[2])
    
    start_trs, tbl, variables = extract_initial_vars(start_assn, tbl, variables)
    for lno, line in enumerate((i.split('#')[0].strip() for i in tbl), start_trs):
        if not line:
            continue
        if rASSIGNMENT.match(line):
            raise SyntaxError(f"Variable declaration on line {lno} after transitions")
        napkin, to = map(str.strip, line.split('->'))
        try:
            napkin = [rCARDINAL.sub(cardinal_sub, i.strip()) for i in napkin.split(',')]
        except KeyError as e:
            raise ValueError(
              f"Invalid cardinal direction for {directives['symmetries']} on line {lno}: '{e}''"
              ) from None
        # Parse napkin into proper range of ints
        for idx, elem in enumerate(napkin):
            if elem.isdigit():
                napkin[idx] = int(elem)
            elif rVAR.match(elem):
                var = parse_variable(elem, variables)
                if var in variables.inv:  # conflict handler can't be relied upon; bidict on_dup_val interferes
                    variables.inv[var].reps += 1
                else:  # it's an anonymous (on-the-spot) variable
                    variables[f'_{random.randrange(10**15)}'] = var
            elif not rBINDMAP.match(elem):  # leave mappings and bindings untouched for now
                try:
                    napkin[idx] = variables[elem]
                except KeyError:
                    raise NameError(f"Invalid or undefined name '{elem}' at line {lno}")
        transitions.append(Transition(napkin, to))
    # TODO: step 0.2, step 1.4, step 2.1


def colorparse(colors):
    pass


def parse(fp):
    """
    fp: file pointer to a full .ruel file

    return: file, sectioned into dict with tabel
            and colors converted to convertable representations
    """
    parts = {}
    segment = None
    for line in map(str.strip, fp):
        if not line or line.startswith('#'):
            continue
        if line.startswith('@'):
            # @RUEL, @TABEL, @COLORS, ...
            segment, *name = line.split(None, 1)
            parts[segment] = name if name[0] else []
            continue
        parts[segment].append(line)
    parts['@TABEL'] = tabelparse(parts['@TABEL'])
    parts['@COLORS'] = colorparse(parts['@COLORS'])
    return parts

