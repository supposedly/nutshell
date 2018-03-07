from itertools import chain

class AdditiveDict(dict):
    def __init__(self, it):
        for key, val in it:
            self[str(key)] = self.get(key, 0) + int(val or 1)
    
    def expand(self):
        return chain(*(k*v for k, v in self.items()))

class Variable:
    __slots__ = 'name', 'reps'
    def __init__(self, name):
        self.name = name
        self.reps = 0

def conv_permute(tr, total):
    """
    Given a new-style permutationally-symmetric transition:
        total=8 (Moore neighborhood)
        -------
        1,0
        1:4,0:4
        1:4,0
        1:3,1,0,0
    Return its old-style representation:
        1,1,1,1,0,0,0,0
    Order is not preserved.
    """
    if isinstance(tr, str):
        tr = tr.split(',')
    # Balance unspecified values
    seq = [i.partition(':')[::2] for i in map(str.strip, tr)]
    # How many cells filled
    tally = total - sum(int(i) for _, i in seq if i)
    # And how many empty slots left to fill
    empties = sum(1 for _, i in seq if not i)
    # filler algo courtesy of Thomas Russell on math.stackexchange
    # https://math.stackexchange.com/a/1081084
    filler = (ceil((tally-k+1)/empties) for k in range(1, 1+empties))
    gen = ((st, num if num else str(next(filler))) for st, num in seq)
    return ','.join(utils.AdditiveDict(gen).expand())

