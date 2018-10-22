from itertools import count

# Makes them easier to write/read
N, NE, E, SE, S, SW, W, NW = 'N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'

F = frozenset
NBHD_SETS = {
  # for containment-checking
  F({E, W}): 'oneDimensional',
  F({N, E, S, W}): 'vonNeumann',
  F({N, E, SE, S, W, NW}): 'hexagonal',
  F({N, NE, E, SE, S, SW, W, NW}): 'Moore',
}
del F

ORDERED_NBHDS = {
  'oneDimensional': (E, W),
  'vonNeumann': (N, E, S, W),
  'hexagonal': (N, E, SE, S, W, NW),
  'Moore': (N, NE, E, SE, S, SW, W, NW),
}


def gollyize(tbl, napkin, anys):  # anys == usages of `any`
    if isinstance(anys, int):
        anys = set(range(anys))
    nbhd = tbl.neighborhood.inv
    d = {nbhd[k]: v for k, v in enumerate(napkin, 1)}
    nbhd_set = set(tbl.neighborhood)
    for s, name in NBHD_SETS.items():
        if nbhd_set == s:
            tbl.directives['neighborhood'] = name
            return [d[dir] for dir in ORDERED_NBHDS[name]]
        if nbhd_set < s:
            break
    tbl.directives['neighborhood'] = name
    new_nbhd = ORDERED_NBHDS[name]
    # (ew, but grabbing VarName object)
    tbl.vars.inv[tbl.vars['any']].update_rep(len(new_nbhd) - len(nbhd))
    tag_counter = count()
    return [d.get(cdir, f'any.{next(i for i in tag_counter if i not in anys)}') for cdir in new_nbhd]
