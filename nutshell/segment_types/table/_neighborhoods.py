from itertools import count, takewhile

NBHD_SETS = (
  # for containment-checking
  ({'E', 'W'}, 'oneDimensional'),
  ({'N', 'E', 'S', 'W'}, 'vonNeumann'),
  ({'N', 'E', 'SE', 'S', 'W', 'NW'}, 'hexagonal'),
  ({'N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'}, 'Moore'),
)

ORDERED_NBHDS = {
  'oneDimensional': ('E', 'W'),
  'vonNeumann': ('N', 'E', 'S', 'W'),
  'hexagonal': ('N', 'E', 'SE', 'S', 'W', 'NW'),
  'Moore': ('N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'),
}


def get_gollyizer(tbl, nbhd):
    nbhd_set = set(nbhd)
    for s, name in NBHD_SETS:
        if nbhd_set <= s:
            tbl.directives['neighborhood'] = name
            if nbhd_set < s:
                return fill.__get__(ORDERED_NBHDS[name])
            return lambda tbl, napkin, _: reorder(ORDERED_NBHDS[name], tbl, napkin)
    raise ValueError('Invalid (non-Moore-subset) neighborhood {nbhd_set}}')


def reorder(ordered_nbhd, tbl, napkin):
    nbhd = tbl.neighborhood.inv
    d = {nbhd[k]: v for k, v in enumerate(napkin, 1)}
    return [d[cdir] for cdir in ordered_nbhd]


def fill(ordered_nbhd, tbl, napkin, anys):  # anys == usages of `any`
    if isinstance(anys, int):
        anys = set(range(anys))
    nbhd = tbl.neighborhood.inv
    d = {nbhd[k]: v for k, v in enumerate(napkin, 1)}
    available_tags = [i for i in range(10) if i not in anys]
    # (ew, but grabbing VarName object)
    tbl.vars.inv[tbl.vars['any']].update_rep(
      max(anys) + len(ordered_nbhd) - len(nbhd) - sum(takewhile(max(anys).__gt__, available_tags))
      )
    tagged_names = (f'any.{i}' for i in available_tags)
    # `or` because this needs lazy evaluation
    return [d.get(cdir) or next(tagged_names) for cdir in ordered_nbhd]
