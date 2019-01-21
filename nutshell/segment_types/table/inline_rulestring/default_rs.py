from itertools import count

from nutshell.segment_types.table._classes import *
from nutshell.common.errors import *

from . import hensel
from .. import _symutils as symutils

ROTATE_4_REFLECT = symutils.get_sym_type('rotate4reflect')
PERMUTE = symutils.get_sym_type('permute')
FOUR_NEIGHBOR = {
  'c': 'e',
  'e': 'c',
  'k': 'k',
  'a': 'a',
  'i': 't',
  'n': 'r',
  'y': 'j',
  'q': 'w',
  'j': 'y',
  'r': 'n',
  't': 'i',
  'w': 'q',
  'z': 'z',
}


def standard(meta, initial, fg, bg, resultant, rulestring, variables, table):
    # r4r only, permute's a headache for some reason
    if isinstance(rulestring, str):
        rulestring = parse_rulestring(rulestring, meta, table)
    if isinstance(fg, StateList):
        variables[table.new_varname(-1)] = fg
    if isinstance(bg, StateList):
        variables[table.new_varname(-1)] = bg
    
    r4r_nbhds = {}
    for nb_count, letters in rulestring.items():
        r4r_nbhds[nb_count] = letters
    
    if r4r_nbhds:
        table.add_sym_type('rotate4reflect')
    
    get_fg, get_bg = _get_getter(table, fg, 'FG'), _get_getter(table, bg, 'BG')
    get_initial, get_resultant = _get_getter(table, initial, None), _get_getter(table, resultant, None)
    counter = count(1)
    ret = []
    if '0' in r4r_nbhds:
        ret.append(TransitionGroup(
          table,
          get_initial('0', None, meta),
          dict.fromkeys(table.neighborhood.values(), get_bg('0', None, meta)),
          get_resultant('0', None, meta),
          context=meta, extra=next(counter),
          symmetries=ROTATE_4_REFLECT
        ))
    ret += [
        TransitionGroup(
          table,
          get_initial(nb_count, letter, meta),
          {
            num: get_fg(nb_count, letter, meta)
            # XXX: probably suboptimal performance b/c [dot attr access] -> [getitem] -> [getitem]
            if cdir in hensel.R4R_NBHDS[nb_count][letter]
            else get_bg(nb_count, letter, meta)
            for cdir, num in table.neighborhood.items()
          },
          get_resultant(nb_count, letter, meta),
          context=meta, extra=next(counter),
          symmetries=ROTATE_4_REFLECT
        )
        for nb_count, letters in r4r_nbhds.items()
        for letter in letters
    ]
    if '8' in r4r_nbhds:
        ret.append(TransitionGroup(
          table,
          get_initial('8', None, meta),
          dict.fromkeys(table.neighborhood.values(), get_fg('8', None, meta)),
          get_resultant('8', None, meta),
          context=meta, extra=next(counter),
          symmetries=ROTATE_4_REFLECT
        ))
    return ret


def inverted(meta, initial, fg, bg, resultant, rulestring, variables, table):
    nbhds = parse_rulestring(rulestring, meta, table)
    to_add = set()
    if '8' not in nbhds:
        to_add.add('8')
    if '0' not in nbhds:
        to_add.add('0')
    for count, letters in hensel.R4R_NBHDS.items():
        nbhds[count] = set(letters).difference(nbhds.get(count, set()))
        if not nbhds[count]:
            del nbhds[count]
    for v in to_add:
        nbhds[v] = set()
    return standard(meta, initial, fg, bg, resultant, nbhds, variables, table)


def odd_invert(meta, initial, fg, bg, resultant, rulestring, variables, table):
    max_neighbors = table.trlen
    nbhds = parse_rulestring(rulestring, meta, table)
    new_nbhds = {}
    for count, letters in nbhds.items():
        count = int(count)
        new_count = max_neighbors - count
        new_key = str(new_count)
        if count == 4:
            new_letters = {FOUR_NEIGHBOR[i] for i in letters}
        else:
            new_letters = letters.intersection(hensel.R4R_NBHDS[new_key])
        if new_letters or new_count == max_neighbors:
            new_nbhds[new_key] = new_letters
    return standard(meta, initial, fg, bg, resultant, new_nbhds, variables, table)


def parse_rulestring(rs, meta, table):
    nbhds = hensel.validate(rs)
    if not nbhds:
        raise SyntaxErr(meta, 'Invalid Hensel-notation rulestring')
    if not hensel.check_within(rs, table.neighborhood, rulestring_nbhds=nbhds):
        raise SyntaxErr(
          meta,
          f"Hensel-notation rulestring exceeds neighborhood {table.directives['neighborhood']!r}; "
          f'in particular, {hensel.find_invalids(nbhds, table.neighborhood)!r}'
          )
    return nbhds


def get_rs_cdir(reference, nb_count, letter, meta, *, idx=None):
    if idx is None:
        idx = reference.idx
    if idx not in ('FG', 'BG', '0'):
        return idx
    if letter is None:
        if nb_count == '0':
            if idx == 'FG':
                raise Error(meta, 'Reference to FG, but given rulestring includes 0, which has no foreground states')
            return 'N'
        if nb_count == '8':
            if idx == 'BG':
                raise Error(meta, 'Reference to BG, but given rulestring includes 8, which has no background states')
            return 'N'
        return 'N' if idx == 'FG' else hensel.CDIRS[int(nb_count)] if idx == 'BG' else '0'
    if idx == 'BG':
        return hensel.BG_LOCATIONS[nb_count][letter]
    if idx == 'FG':
        return hensel.FG_LOCATIONS[nb_count][letter]
    return '0'


def resolve_rs_ref(term, nb_count, letter, meta):
    if isinstance(term, StateList):
        if any(isinstance(i, (InlineRulestringBinding, InlineRulestringMapping)) for i in term):
            return term.__class__((
              resolve_rs_ref(i, nb_count, letter, meta)
                if isinstance(i, (InlineRulestringBinding, InlineRulestringMapping))
                else i
                for i in term
                ),
              context=term.ctx
              )
    if not isinstance(term, (InlineRulestringBinding, InlineRulestringMapping)):
        return term
    new_cdir = get_rs_cdir(term, nb_count, letter, meta)
    if isinstance(term, InlineRulestringBinding):
        return Binding(new_cdir, context=term.ctx)
    if isinstance(term, InlineRulestringMapping):
        return Mapping(new_cdir, term.map_to, context=term.ctx)
    return term


def _get_getter(table, val, kind):
    def get_val(*_):
        return val
    
    if isinstance(val, InlineBinding):
        used = set()
        def get_val(nb_count, letter, meta):
            if (nb_count, letter) not in used:
                val.reset()
                used.add((nb_count, letter))
            if val.bind is None:
                val.set(table.neighborhood[get_rs_cdir(val, nb_count, letter, meta, idx=kind)])
            return val.give()
    
    if isinstance(val, (InlineRulestringBinding, InlineRulestringMapping)):
        def get_val(*args):
            return resolve_rs_ref(val, *args)
    
    if isinstance(val, StateList):
        getters = [_get_getter(table, i, kind) for i in val]
        def get_val(*args):
            return val.__class__(
                (getter(*args) for getter in getters),
                context=val.ctx
                )
    
    if isinstance(val, Operation):
        get_a, get_b = _get_getter(table, val.a, kind), _get_getter(table, val.b, kind)
        def get_val(*args):
            return val.__class__(
                a=get_a(*args),
                b=get_b(*args),
                context=val.ctx
                )
    return get_val
