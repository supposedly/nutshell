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


def reorder(transitions, *ordering: int):
    """
    For when *really* fine control is needed.
    Takes a series of numbers corresponding to the Nutshell
    transitions covered by this macro, where 1 is the first
    transition and 2 the second and so on, and reorders the
    resultant Golly transitions according to their ordering

    For instance, given a series of numbers `1 1 2 3 1 4 2`
    and operating over the sequence of Nutshell transitions
      [a, b, c, d, e]
    corresponding to the following set of Golly transitions
      [a0, a1, a2, a3, b0, b1, c0, c1, d0, d1, e0]
    The macro will return:
      [a0, a1, b0, c0, a2, d0, b1, a3, c1, d1, e0]
    
    Notice how, after the last specified transition, extras
    are tacked on to the end- in as close to their original
    order as possible.
    """
    lnos = consolidate(transitions)
    transitions = [lnos[i][::-1] for i in sorted(lnos)]
    new = []
    for lno in ordering:
        if transitions[lno-1]:
            new.append(transitions[lno-1].pop())
    for leftover in transitions:
        new.extend(leftover[::-1])
    return new
