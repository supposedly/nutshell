import re

# rough validation
rHENSEL_RULESTRING = re.compile(r'(?:[0-8]-?[cekainyqjrtwz]*)+')

R4R_LETTERS = 'cekainyqjrtwz'
CDIRS = ('N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW')
R4R_NBHDS = {
  k: dict(zip(R4R_LETTERS, ({cdir for cdir, c in zip(CDIRS, napkin) if c == '1'} for napkin in v))) for k, v in (
    ('0', ()),
    ('1', ('00000001', '10000000')),
    ('2', ('01000001', '10000010', '00100001', '10000001', '10001000', '00010001')),
    ('3', ('01000101', '10100010', '00101001', '10000011', '11000001', '01100001', '01001001', '10010001', '10100001', '10001001')),
    ('4', ('01010101', '10101010', '01001011', '11100001', '01100011', '11000101', '01100101', '10010011', '10101001', '10100011', '11001001', '10110001', '10011001')),
    ('5', ('10111010', '01011101', '11010110', '01111100', '00111110', '10011110', '10110110', '01101110', '01011110', '01110110')),
    ('6', ('10111110', '01111101', '11011110', '01111110', '01110111', '11101110')),
    ('7', ('11111110', '01111111')),
    ('8', ())
    )
  }
FG_LOCATIONS = {
  **{count:
      {k: next(i for i in CDIRS if i in v)
      for k, v in letters.items()
      }
    for count, letters in R4R_NBHDS.items()
    },
  '0': None,
  '8': 'N'
  }
BG_LOCATIONS = {
  **{count:
      {k: next(i for i in CDIRS if i not in v)
      for k, v in letters.items()
      }
    for count, letters in R4R_NBHDS.items()
    },
  '0': 'N',
  '8': None
  }


def validate(rulestring):
    nbhds = {}
    cur_key = None
    if rHENSEL_RULESTRING.match(rulestring) is None:
        return False
    for letter in rulestring:
        if letter.isdigit():
            if letter not in R4R_NBHDS:
                return False
            cur_key = letter
            nbhds[letter] = set()
        elif letter != '-' and (cur_key is None or letter not in R4R_NBHDS[cur_key]):
            return False
        else:
            nbhds[cur_key].add(letter)
    for key, letter_set in nbhds.items():
        if not letter_set:
            nbhds[key] = set(R4R_NBHDS[key])
        if '-' in letter_set:
            # XXX: this doesn't validate that the hyphen is first /shrug
            if len(letter_set) == 1:
                return False
            nbhds[key] = set(R4R_NBHDS[key]) - letter_set
    return nbhds  # bool()s to True


def check_within(rulestring, current_nbhd, *, rulestring_nbhds=None):
    current_nbhd = set(current_nbhd)
    if rulestring_nbhds is None:
        rulestring_nbhds = validate(rulestring)
    if not rulestring_nbhds or '8' in rulestring_nbhds and current_nbhd != set(CDIRS):
        return False
    return all(
      nbhd <= current_nbhd
      for neighbor_count, letters in rulestring_nbhds.items()
      for nbhd in map(R4R_NBHDS[neighbor_count].get, letters)
      )


def find_invalids(nbhds, current_nbhd):
    current_nbhd = set(current_nbhd)
    invalids = set()
    if '8' in nbhds and current_nbhd != set(CDIRS):
        invalids.add('8')
    invalids.update(
      f'{neighbor_count}{letter}'
      for neighbor_count, letters in nbhds.items()
      for letter in letters
      if not R4R_NBHDS[neighbor_count][letter] <= current_nbhd
      )
    return invalids
