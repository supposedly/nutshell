import string
from math import ceil

import bidict


SYMBOL_MAP = bidict.frozenbidict({
    0: '.',
  **{num: chr(64+num) for num in range(1, 25)},
  **{num: chr(110 + ceil(num/24)) + chr(64 + (num % 24 or 24)) for num in range(25, 256)}
  })

SAFE_CHARS = string.ascii_lowercase + string.digits + string.punctuation.replace('.', '')


def maybe_double(symbol: str):
    if len(symbol.encode()) < 2:
        return symbol * 2
    return symbol
