# Python extensions
Certain aspects of Nutshell are extensible via user-defined Python classes or functions. These are enumerated below.


## Custom symmetry types
In addition to Nutshell's "standard library" of symmetries, it accepts custom user-defined ones. To do so,
create a `.py` file and within it a class that inherits from Nutshell's exposed `Napkin` class
(alternatively, `OrthNapkin` or `HexNapkin`):

```py
from nutshell import Napkin
from nutshell.napkin import oneDimensional, vonNeumann, hexagonal, Moore, Any

class MySymmetries(Napkin):
    neighborhoods = ...
    fallback = ...

    @property
    def expanded(self):
       ...
    
    # OPTIONAL!!!
    def special(self, ...):
        ...
```

As shown by the ellipses, there are at least three things you need to define within your class.
- `neighborhoods`: a tuple containing the *length* of each neighborhood that your symmetries support. These are ultimately just integers, but Nutshell has the constants `oneDimensional`,
  `vonNeumann`, `hexagonal`, and `Moore` defined respectively as `2`, `4`, `6`, and `8` for clarity.  
  For example, on a symmetry type meant for the Moore and vonNeumann neighborhoods, one would assign `neighborhoods = vonNeumann, Moore` (with no particular ordering required).  
  **If you want to support all potential range-1 neighborhoods**, write `neighborhoods = Any` instead; `Any` is another Nutshell constant name, aliased to the Python value `None`.
- `fallback`: Either the name, as a string, of a Golly symmetry which is a superset of (or perhaps equivalent to) yours and thus can be expanded to during transpilation... or,
  if your symmetry type supports more than one neighborhood for which different appropriate Golly symmetries are available, a dictionary of {`neighborhood length`: `Golly symmetry`}.
  to the same effect. (`Any`, aka Python `None`, can be used in this dict as well.)  
  For example, the class for `nutshell.AlternatingPermute` above has `fallback = 'rotate4reflect'`, because that is the "highest"
  (most-expressive) Golly symmetry in which multiple transitions are able to express a single AlternatingPermute transition.  
  The class for `nutshell.Rotate2` above has `fallback = {Any: 'none', hexagonal: 'rotate2'}`, because Golly already has rotate2 support
  for hexagonal neighborhoods, so we don't want to unnecessarily expand `nutshell.Rotate2` to None if used there&nbsp;-- but for other
  neighborhoods, the only way to express Rotate2 in Golly is via `none` symmetry.
  When in doubt, use `fallback = 'none'`.
- `expanded`: To explain this, it should first be mentioned that `Napkin` is a subclass of Python's built-in `tuple` type; the reason it's
  called Napkin and not something like Symmetries is that a single Napkin instance *represents* the neighbor states of a given transition.
  That is, when expanding symmetries, an instance of the pertinent Napkin class is constructed from the neighbor states of the current
  transition to determine how to treat its symmetries.  
  Instances of napkins under your custom symmetries are constructed as `MySymmetries((0, 1, 2, 3, 4, 5, 6,7))`
  (assuming Moore neighborhood), i.e. with the sequence of neighbor states it has to represent. The job of `expanded`, then, is to
  provide a representation of what a single napkin in your symmetry type looks like *when expanded into `symmetries: none`*,
  and (importantly!!) returning this representation in the *exact same order* for any equivalent napkin. For example,
  `ReflectHorizontal((0, 1, 2, 3, 4, 5, 6, 7)).expanded` and `ReflectHorizontal((0, 7, 6, 5, 4, 3, 2, 1)).expanded` **both**
  return the exact list `[(0, 1, 2, 3, 4, 5, 6, 7), (0, 7, 6, 5, 4, 3, 2, 1)]` (and both in that order), because the
  two Moore-neighborhood napkins are equivalent under ReflectHorizontal symmetry.  
  Similarly, `ReflectHorizontal((2, 4, 6, 8)).expanded` returns `[(2, 4, 6, 8), (2, 8, 6, 4)]`, **as does**
  `ReflectHorizontal((2, 8, 6, 4)).expanded`, because the vonNeumann-neighborhood napkin `2,4,6,8` reflected horizontally is `2,8,6,4` and
  so both are equivalent under reflect_horizontal symmetry.  
  (The sequence type that `expanded` returns doesn't matter as long as it's some iterable&nbsp;-- but (a) its individual elements must
  all be hashable, and (b) it must not contain any occurrences of itself. For this reason it's probably best to have `expanded` return a
  sequence of tuples.)  
  After that, save your file in a directory accessible from the directory of the nutshell file you wish to use the symmetry type
  from&nbsp;--
  and you're done! It'll be accessible from a Nutshell rule as `<import path to containing file>.<class name>`. For instance, the symmetry
  type above will be accessible as `symmetries: custom_symmetries.MySymmetries` if it's saved in a file called
  `custom_symmetries.py` in the same directory as the nutshell file it's used from.  
  The custom-symmetry-type API will be simplified in the future to make it more accessible.

#### "special" syntax
As mentioned in the main README, certain symmetry types can use the tilde operator to their liking -- intended for permute-like
symmetries, but it is in fact applicable to any symmetry type that defines a `special()` method. It should take any or all of
the following parameters (Nutshell inspects its signature and passes arguments appropriately):

- `length`: Expected length of a transition napkin under the current neighborhood
- `values`: The current transition napkin (whose length may not match `length`)
- `initial`: The initial cellstate of the current transition
- `resultant`: The final term of the current transition

...and its job is to return a list, whose length should match `length`, representing a new transition napkin. (The initial
and resultant cellstates cannot be modified.)

## Macros
**Macros** are Python functions that operate on spans of Nutshell transitions, explained in some depth within the main README.
They are defined as follows:
- A single initial argument, preferably named `transitions`, that is passed a list of transitions the macro is to modify
- As many subsequent positional-argument parameters as necessary, which will be populated from Nutshell (consider the 1 in `weave: 1`)
- A series of KEYWORD-ONLY parameters with one of the following names, to which arguments will be passed 'on demand':
    - `n_states`: The number of cellstates used by the current rule
    - `variables`: The [bidict](https://github.com/jab/bidict) of {StateList :: VarName} representing the current rule's variables
    - `directives`: A dict of directive->value for the current rule
    - `table`: The whole Table object itself, from which all of the above are accessible (more roundaboutily, though)
Additionally, macro functions are run through the same `typecast()` function used by [ergo](https://github.com/eltrhn/ergo)
(mentioned under "Typecasting goodies" in the README), which means they can be type-hinted to convert an argument from one
datatype (typically `str`) to a more-useful one.

The `transitions` argument will be passed a list of `FinalTransition` objects. `FinalTransition` is a `list` subclass (meaning
it's almost identical to a list) with two extra attributes, only the latter of which is important: `ctx` holds the
position of the original Nutshell transition that created this one, being a tuple of `(lno, start_column, end_column)`,
but since the `lno` is the only pertinent thing it is exposed by itself as `FinalTransition.lno`.  
A macro function is expected to also return a list of `FinalTransition` objects; this class is exposed from `nutshell.macro`,
and can be instantiated as `FinalTransition((iterable), lno=some_line_number)`.

`nutshell.macro` also provides a function `consolidate(transitions)` that takes a list of `FinalTransition`s and returns a dict
of `{line number: FinalTransitions from this line number}`. The standard-library `weave` macro, for an example,
resembles the following:

```py
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
```