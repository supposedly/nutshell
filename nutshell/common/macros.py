from itertools import chain, zip_longest as zipln

def weave(transitions, chunk):
    # Consolidate transitions by line number
    lnos = {}
    for tr in transitions:
        lnos.setdefault(tr.ctx.lno, []).append(tr)
    # End result is a list of
    # [[transitions with line number A], [transitions with line number B], ...]
    transitions = [lnos[i] for i in sorted(lnos)]

    chunk = int(chunk)
    return [
      j for i in
      # Flattens list of `chunk`-sized chunks from each group of transition
      map(chain.from_iterable, zip(*[zipln(*[iter(trs)]*chunk) for trs in transitions]))
      # And this acts like a second chain(), but I also get to...
      for j in i
      # ...do this without needing to filter(lambda x: x is not None, ...)
      if j is not None
      ]
