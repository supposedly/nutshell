# CA rules “in a nutshell”
A transpiler from a reimagined Golly ruletable language to the traditional format. See [`examples/`](/examples) for examples, and if none
of this makes any sense to you and you aren't sure how you got here, check out the [layman's README](documents/LAYMAN-README.md).

## Setup
1. [Download & install Python 3.6](https://www.python.org/downloads/release/python-365/) or higher (support for < 3.6 hopefully coming soon)
2. Either:
  1. Execute the terminal command `pip install -U git+git://github.com/eltrhn/ergo.git` (or whichever of the
    pip command's variations works for you; you may need to try `python -m pip install`, `python3 -m pip install`,
    on Windows `py -m pip install`, ...)
  2. `git clone` this project, then `cd` to its directory and execute `pip install -U .` (or the correct one of
    the variations discussed above)
4. Write your own "nutshell" rule file, then continue with the **Usage** section below.

## Usage
The `pip install` will add a command `nutshell-ca` for use in terminal. If this for any reason does
not work for you, you may instead `git clone` Nutshell as in step 2.ii above and then run `to_ruletable.py`
from its root directory as a substitute for `nutshell-ca`.

```bash
$ nutshell-ca [infile] [outdir] [-v | -q | -s | -p | -t | -f]
```
The output file will be written to `outdir` with a .rule extension and the same filename as `infile`.  
Supported flags, though there's more info in `--help`:
  - `-v`: Verbose. Can be repeated up to four times, causing more info to be displayed each time.
  - `-s`: Source. Writes each original nutshell line, as a comment, above the line(s) it compiles
          to in the final ruletable output.
  - `-p`: Preview. "Compiles" a single nutshell transition, and prints out a Golly-equivalent
          preview. Flag is mutually exclusive with `-t`, `-f`, and `outdir`.
  - `-t [HEADER]`: Change the "COMPILED FROM NUTSHELL" header that is added by default to transpiled
                   rules. (If `-t` is given no argument the header will be removed)
  - `-f TRANSITION`: Find a certain transition defined within a table section; requires, of course, that
                     the rule have a `@TABLE` segment to search within. If a certain cell isn't behaving
                     the way it's supposed to, you can `-f` the transition it's undergoing, and nutshell
                     will find the offending transition for you (rather than you having to guess at what
                     you typo'd).  
                     Transition should be given in the standard Golly form `C,N,...,C'` -- that is, state of the
                     current center cell, then its neighborhood, and finally the state it transitions into
                     on the next tick. Example [here](https://user-images.githubusercontent.com/32081933/39951382-2b37fca0-553e-11e8-87b5-69685dfe4881.png)!

## What's new
- All variables always unbound, because needing to define eight "any state" vars is ridiculous.
- Support for `{}` literals, usable directly in transitions, as 'on-the-spot' variables. (Parentheses are also allowed. I personally prefer them to braces.)
- Support for cellstate *ranges* in variables, via double..dots as in `(0..8)` -- interspersible with state-by-state specification,
  so you can do `(0, 1, 4..6, 9)` to mean `(0, 1, 4, 5, 6, 9)`.  
  Ranges also accept a step, so you can also do `(0, 1-10..50, 102)` to mean `(0, 1, 11, 21, 31, 41, 102)`.
- A variable is made 'bound' by referring to its *index* in the transition, wrapped in [brackets]:  
```py
# current (barC repeats)
foo,barA,barB,barC,barD,barE,barF,barG,barH,barC
# new
foo,bar,bar,bar,bar,bar,bar,bar,bar,[3]

# current (barA repeats)
foo,barA,barB,barC,barA,barD,barE,barF,barG,baz
# new
foo,bar,bar,bar,[1],bar,bar,bar,bar,baz
```  
Transitions are zero-indexed from the input state and must refer to a previous index.
- To make binding even simpler, the reserved names `N NE E ... NW` are provided as symbolic constants for what the direction's index would be
  in the specified neighborhood. (The remainder of this document assumes the use of these constants rather than the raw indices,
  but they are interchangeable.)
- For example, in a rule with `neighborhood: vonNeumann`, the names `N E S W` are provided for `1 2 3 4`.
- This means that, above, the first 'new' transition can be rewritten as `foo,bar,bar,bar,bar,bar,bar,bar,bar,[E]` (E meaning east, because
  the 3rd `bar` represented the eastern cell), and the second as `foo,bar,bar,bar,[N],bar,bar,bar,bar,baz`.  
  (Note that the input state is still referred to as `[0]` — no symbolic name)
- Repetition can be cut down on even more by specifying directions directly before each state, which then allows
  *ranges* of directions (which of course ultimately map to their respective numbers). This means that the
  transitions above can be further rewritten to:
```py
# current (barC repeats)
foo,barA,barB,barC,barD,barE,barF,barG,barH,barC
# new
foo, N..NW bar, [E]

# current (barA repeats)
foo,barA,barB,barC,barA,barD,barE,barF,barG,baz
# new
foo, N..E bar, [N], S..NW bar, baz # could also be "..., SE [N], ..."
```
- With this indexing, we can introduce "mapping" one variable to another. For instance, `foo, N..NW (0, 1, 2), [E: (1, 3, 4)]`
(meaning *map the eastern cell, being any of `(0, 1, 2)`, to the states `(1, 3, 4)`: if it's 0 return 1, if 1 return 3, if 2 return 4*) can
replace what would otherwise require a separate transition for each of `0`...`1`, `1`...`3`, and `2`...`4`.  
  Mapping of course works with named variables as well.
- If a variable literal is too small to map to, an error will be raised that can be rectified by either (a) filling it out with explicit transitions,
or (b) using the `...` operator to say *"fill the rest out with whatever value preceded the `...`"*.
  If the "map-to" is instead *larger* than its "map-from", extraneous values will simply be ignored.
- Transitions can be started on a direction other than north if explicitly specified. Under vonNeumann, `0, W..E 1, S 0, 2` becomes `0, W 1, N 1, E 1, S 0, 2`
  which is equivalent to `0, 1, 1, 0, 1, 2` or `0, N..E 1, 0, 1, 2`. A single direction (`W`) rather than a range (`W..E`) can also be specified to the same effect.
  Bindings and mappings to "forward" indices are automatically resolved when reordering these non-north-initial transitions.
- A Golly-ruletable transition such as von-Neumann `0,a,a,a,a,1` might be inefficiently compacted to `0, a, [N], [N], [N], 1`, or worse
  `0, a, E..W [N], 1`. In such cases, where successive variables need all to be bound to the first, the shorthand `direction..direction [var]` can be used.
  Here it would look like `0, N..W [a], 1`, expanding during transpilation to `0, a, [1], [1], [1], 1`.
- Support for negation and subtraction of variables via the `-` and `--` operators:
```py
0, foo-bar, bar-2, bar-(2, 3), -1, --1, -bar, --(3, 4), (foo, bar), baz

# foo-bar says "All states in foo that are not in bar"
# foo-2 says "All states in foo that are not 2"
# bar-(2, 3) says "All states in bar that are not in (2, 3)"
# -1 says "All *live* states that are not 1" (expands to {2, 3, 4} assuming n_states==5)
# --1 says "*All* states (including 0) that are not 1" (expands to {0, 2, 3, 4} assuming the same)
# -bar and --(3, 4) say the same but with multiple states enclosed in a variable
``` 
"Addition" of two variables can be accomplished by placing them in a variable literal, as in the `(foo, bar)` state above.
- The `*` operator within a variable literal acts as something like multiplication. It repeats or truncates the left-hand operand until its
  length matches the right-hand operand's -- if the latter is a variable -- or until the former's length equals the right-hand operand itself
  if the latter is a number.  
  - `0*5` expands to `(0, 0, 0, 0, 0)`
  - `any*5`, assuming `any = (0, 1, 2)`, expands to `(0, 1, 2, 0, 1)` -- note the new length, 5
  - `5*any`, assuming the same, expands to `(5, 5, 5)`
  - `live*any`, assuming as well that `live = (1, 2)`, expands to `(1, 2, 1)`
- Live cells can be treated as moving objects: a cardinal direction to travel in and resultant cell state are specifiable post transition.
```py
foo, N..NW bar, baz -> S:2  E[(2, 3)]  SE[wutz]  N[NE: (2, 3)]  NE[E]

# S:2 says "spawn a state-2 cell to my south"

# E[(2, 3)] and SE[wutz] say "map this cell (E or SE) to this variable"

# N[NE: (2, 3)] says "spawn a cell to my north
# that maps the *northeastern* state variable to the (2, 3) literal."

# N[NE] is identical to N[NE: bar], or N[NE: [N]] if nested binding/mapping were supported
# "spawn a cell to my north that maps the *northeastern* state variable to the one currently
# north of me."

# Be careful with the syntax presented in these last two bits! You cannot, for example, write
# NW[S] or N[SE: (2, 3)] -- these imply a violation of the speed of light, and will raise an eror
# (or, if you're unlucky, fail silently)
```
- Within these "output specifiers", the `_` keyword says "leave the cell as is".   
    - (formerly "PTCDs", from "**p**ost-**t**ransition **c**ompass-**d**irection specifier**s**")
- The `->` arrow here says to, during transpiling, place the "main" transition (the one preceding the arrow) *before* the ones created by the output specifiers.
  This causes it to, when the transpiled result is interpreted by Golly, override their behavior should they conflict.  
  If the opposite behavior is instead desired, where the main transition comes last and is overridden by the output-specifier transitions, one can use the `~>` arrow
  (with a tilde rather than a hyphen) instead.
- Transitions under permutational symmetry can make use of a shorthand syntax, specifying only the quantity of cells in each state. For example, `0,2,2,2,1,1,1,0,0,1`
  in a Moore+permute rule can be compacted to `0, 2 ** 3, 1 ** 3, 0 ** 2, 1`.  
  Unmarked states will be filled in to match the number of cells in the transition's neighborhood, meaning
  that this transition can also be written as `0, 0 ** 2, 1, 2, 1` or `0, 1 ** 3, 2 ** 3, 0, 1`.  
  - If the number of cells to fill is not divisible by the number of unmarked states, precedence will
    be given to those that appear earlier; `2,1,0`, for instance, will also expand into `2,2,2,1,1,1,0,0`, but `0,1,2` will expand into `0,0,0,1,1,1,2,2`.
- You're allowed to switch symmetries partway through via the `symmetries:` directive. (When parsing, this results in all transitions being expanded to the 'lowest'
  symmetry type specified overall.) Speaking of which...

### Custom symmetry types
The implementation of the aforementioned symmetry-switching (in short: expansion of a transition into its representation under `symmetries: none`, then re-compression of
it into a different symmetry by eliminating duplicates) allows, conveniently, for non-Golly-supported symmetries to be defined and then simply expanded by Nutshell into
one of Golly's symmetry types. Provided by Nutshell is a small "standard library" of sorts with the following:

- `symmetries: nutshell.AlternatingPermute`: Permutational symmetry, like `symmetries: permute`, but only between every *second* cell in a napkin. Under the Moore neighborhood,
  this means that cellstates are permuted between orthogonal neighbors and, separately, between diagonal neighbors; under vonNeumann, that cellstates are permuted between opposing
  pairs of neighbors; and, though *possible* to apply under hexagonal symmetry (where permutation would occur between (N, SE, W) and (E, S, NW)), it would be meaningless so only the
  former two are supported.
- `symmetries: nutshell.Rotate2`: Identical to Golly's `rotate2` in a hexagonal neighborhood, but allows Moore and vonNeumann as well. (Use `rotate2` instead of this for a hexagonal
  rule)
- `symmetries: nutshell.ReflectVertical`: Vertical reflection.

In addition, although the API for it is somewhat clunky at present, you as the user are allowed to define your own custom symmetries. To do so, create a `.py` file and within it a class
that inherits from Nutshell's exposed `Napkin` class (alternatively, `OrthNapkin` or `HexNapkin`):

```py
from nutshell import Napkin

class MySymmetries(Napkin):
    lengths = ...
    fallback = ...

    @property
    def expanded(self):
       ...
```

As shown by the ellipses, there are three things that you need to define within your class.
- `lengths`: a tuple containing the *length* of each neighborhood that your symmetries support. For example, in a symmetry type meant for the Moore and vonNeumann neighborhoods, one would
  have `lengths = 4, 8` (mapping to vonNeumann & Moore because a cell under vonNeumann has 4 neighbors and a cell in Moore has 8).
  **If you want to support all neighborhoods Golly offers**, write `lengths = None` instead.
- `fallback`: the name, as a string, of a Golly symmetry which is a superset of (or perhaps equivalent to) yours and thus can be expanded to during transpilation. For example, the class for
  `nutshell.AlternatingPermute` above has `fallback = 'rotate4reflect'`, because that is the "highest" (most expressive) Golly symmetry in which multiple transitions are able to express a
  single AlternatingPermute transition.  
  When in doubt, use `fallback = 'none'`.
- `expanded`: To explain this, it should first be mentioned that `Napkin` is a subclass of Python's built-in `tuple` type; the reason it's called Napkin and not something like Symmetries
  is that a single Napkin instance *represents* the neighbor states of a given transition. That is, when expanding symmetries, an instance of the pertinent Napkin class is constructed from
  the neighbor states of the current transition to determine how to treat its symmetries.  
  Instances of napkins under your custom symmetries are constructed as `MySymmetries((0, 1, 2, 3, 4, 5, 6,7))` (assuming Moore neighborhood), i.e. with the sequence of neighbor states
  it has to represent. The job of `expanded`, given that, is to provide a representation of what a single napkin in your symmetry type looks like *when expanded into `symmetries: none`*,
  and (importantly!!) returning this representation in the *exact same order* for any equivalent napkin. For example, `ReflectHorizontal((0, 1, 2, 3, 4, 5, 6, 7)).expanded` and
  `ReflectHorizontal((0, 7, 6, 5, 4, 3, 2, 1)).expanded` **both** return the exact list `[(0, 1, 2, 3, 4, 5, 6, 7), (0, 7, 6, 5, 4, 3, 2, 1)]` (and both in that order), because the
  two Moore-neighborhood napkins are equivalent under ReflectHorizontal symmetry.   
  Similarly, `ReflectHorizontal((2, 4, 6, 8)).expanded` returns `[(2, 4, 6, 8), (2, 8, 6, 4)]`, **as does** `ReflectHorizontal((2, 8, 6, 4)).expanded`, because the vonNeumann-neighborhood napkin
  `2,4,6,8` reflected horizontally is `2,8,6,4` and so both are equivalent under reflect_horizontal symmetry.  
  (The sequence type that `expanded` returns doesn't matter as long as it's some iterable -- but (a) its individual elements must all be hashable, and (b) it must not contain any occurrences
  of itself. It's hence probably best to have `expanded` return a sequence of tuples.)  
  After that, save your file in a directory accessible from the directory of the nutshell file you wish to use the symmetry type from -- and you're done! It'll be accessible from a Nutshell
  rule as `<import path to containing file>.<class name>`. For instance, the symmetry type above will be accessible as `symmetries: custom_symmetries.MySymmetries` if it's saved in a file called
  `custom_symmetries.py` in the same directory as the nutshell file it's used from.  
  The custom-symmetry-type API will be simplified in the future to make it more accessible.


## Non-table-related changes
- The preferred file extension is `.ruel`, both a holdover from when this project was named `rueltabel` and a simple-but-recognizable variant
  of "rule" to distinguish nutshell files from standard `.rule` files. This obviously isn't enforced anywhere, however, and might also be subject to
  change later.
- Comments in every segment (barring `@NUTSHELL`, where everything after the first word is a comment) start with `#` and stretch to the end of a line.
- The `@COLORS` segment in nutshells allows multiple states with the same color to be defined
  on the same line as each other, and for a color to be written as either a hexadecimal color code or a
  group of base-10 `R G B` values. As a result of its allowing multiple colors, the "key/value" order, if you will, has been switched: the color now
  goes first on a line, followed by all the states it's assigned to. A range can be used here identically to that found in variable literals.  
  For instance: `FFF: 1 10` says to assign the color `#FFFFFF` to states 1 and
  10, and can also be written as `FFFFFF: 1 10` or `255 255 255: 1 10`.
- The `@ICONS` segment is based around RLEs instead of Gollyesque XPM data. See [this post](http://conwaylife.com/forums/viewtopic.php?f=7&t=3361&p=59944#p59944)
  for an explanation + example. Ranges are also supported in icon state specifiers.
- The `@NUTSHELL` segment allows *constants*, which carry over to and are usable in the `@TABLE` segment, to be
  defined alongside a description of each state. Take the following example:

```rb
@NUTSHELL foo

1: Stationary data {DATA}
3: Signal over data
4: Signal over vacuum {SIGNAL}

@TABLE
...
```
  The names `DATA` and `SIGNAL` will be usable within the `@TABLE` segment as aliases for, respectively, states `1` and `4`.  
  It is recommended but nowhere required that constant names be written in `UPPERCASE` or at least `PascalCase` and normal
  variable names in `lowercase` or `camelCase`; the initial capitals help visually distinguish constants from multi-state variables.  
  For the actual registering of a constant, all that matters is that its line in `@NUTSHELL` start with `<number>:` and contain anywhere a pair
  of `{braces}` that enclose the constant's name. The braced part and any whitespace separating it from the previous word will be removed
  from the final `@RULE` segment in the output file.
- **All segments are optional**. The parser will in addition transcribe "non-special" segments *as is*, meaning that
  a file can have a `@RULE` segment rather than `@NUTSHELL` and it will be transcribed into the output file untouched.
- The other "special" nutshell segments like `@TABLE` and `@ICONS` and `@COLORS`, none of whose names differ from
  their Golly-format counterparts, will still be ignored by the parser if their header is immediately followed by
  the comment `#golly` -- either on the same line (after whitespace) or on the line immediately below.

## To do
- DOCS! Or at least a proper introductory writeup.
- Do something (???) to attempt to simplify permutationally-symmetric transitions such as in TripleLife.
