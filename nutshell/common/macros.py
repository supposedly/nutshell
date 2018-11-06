from itertools import chain, zip_longest as zipln

from nutshell.macro import consolidate


def weave(transitions, chunk_size: int):
    """
    With chunk_size = 1:
      Given a group of Nutshell transitions [a, b, c] producing
      the Golly transitions [a0, a1, a2, ..., b0, b1, b2, ..., c0, c1, c2, ...] ,
      reorder the Golly transitions as [a0,b0,c0, a1,b1,c1, a2,b2,c2, ...] --
      in other words, "weaving" groups of transitions together.
    With chunk_size = 2, produces
      [a0,a1,b0,b1,c0,c1, a2,a3,b2,b3,c2,c3, ...]
    And so on for higher chunk_size values. Extraneous transitions (ones that
    don't divide evenly into chunk_size) are left at the end rather than discarded.
    """
    lnos = consolidate(transitions)
    transitions = [lnos[i] for i in sorted(lnos)]
    return [
      j for i in
      # Flattens list of `chunk_size`-sized chunks from each group of transitions
      map(chain.from_iterable, zip(*[zipln(*[iter(trs)]*chunk_size) for trs in transitions]))
      # And this acts like a second chain(), but I also get to...
      for j in i
      # ...do this without needing to filter(lambda x: x is not None, ...)
      if j is not None
      ]
