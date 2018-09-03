# CA rules “in a nutshell”
A transpiler from a reimagined Golly ruletable language to the traditional format. See [`examples/`](/examples) for examples, and if none
of this makes any sense to you and you aren't sure how you got here, check out the [layman's README](documents/LAYMAN-README.md).

## Setup
1. [Download & install Python 3.6](https://www.python.org/downloads/release/python-365/) or higher (support for < 3.6 hopefully coming soon)
2. Either:
    1. Execute the terminal command `pip install -U git+git://github.com/eltrhn/nutshell.git` (or whichever of the
       pip command's variations works for you; you may need to try `python -m pip install`, `python3 -m pip install`,
       on Windows `py -m pip install`, ...) to install via pip directly,
    2. **OR** `git clone` this project, then `cd` to its directory and execute `pip install -U .` (using the correct one of
       the variations discussed above)
4. Write your own "nutshell" rule file, then continue with the **Usage** section below.

## Usage
The `pip install` will add a command `nutshell-ca` for use in terminal. If this for any reason does
not work for you, you may instead `git clone` Nutshell as in step 2.ii above and then run `to_ruletable.py`
from its root directory as a substitute for `nutshell-ca`.

```
$ nutshell-ca [-v | -q] transpile [infile] [outdir] [-s | -p | -t | -f]
(alternatively, `nutshell-ca t ...')
```
The output file will be written to `outdir` with a .rule extension and the same filename as `infile`.  
Supported flags, though there's more info in `--help` (note that `-v` and `-q` can come either
after or before the keyword `transpile`/`t` with no difference):
  - `-v`: Verbose. Can be repeated up to four times, causing more info to be displayed each time.
  - `-q`: Quiet. Opposite of the above, but only has one level.
  - `-s`: Source. Writes each original nutshell line, as a comment, above the line(s) it compiles
          to in the final ruletable output. (If the compiled line is from an auxiliary-transition
          specifier, the specifier is printed instead along with its line number as normal.)
  - `-t [HEADER]`: Change the "COMPILED FROM NUTSHELL" header that is added by default to transpiled
                   rules. (If `-t` is given no argument the header will be removed)
  - `-f TRANSITION`: Find a certain transition defined within a table section; requires, of course, that
                     the rule have a `@TABLE` segment to search within. If a certain cell isn't behaving
                     the way it's supposed to, you can `-f` the transition it's undergoing, and nutshell
                     will find the offending transition for you (rather than you having to guess at what
                     you typo'd).  
                     Transition should be given in the standard Golly form `C,N,...,C'` -- that is, state of the
                     current center cell, then its neighborhood, and finally the state it transitions into
                     on the next tick. Use `*` as an "any state" wildcard. Example [here](https://user-images.githubusercontent.com/32081933/39951382-2b37fca0-553e-11e8-87b5-69685dfe4881.png)!

## What's new
### Directives
The `n_states` directive's name has been changed to `states`, and all directives ignore whitespace in their values -- so one may
write, say, `symmetries: rotate 4` or `neighborhood: von Neumann`.
The `symmetries` directive can take a Python import path for *custom symmetry types*; this will be elaborated upon later on.
```rb
# Nutshell
@TABLE
states: 5
symmetries: rotate 4 reflect
neighborhood: von Neumann
```
```rb
# Golly
@TABLE
neighborhood: vonNeumann
n_states: 5
symmetries: rotate4reflect
```
In addition, the `symmetries` directive can be used multiple times within a file, allowing the writer to switch symmetries
partway through a rule. During transpilation, differently-symmetried transitions will be expanded into the "lowest"
(least-expressive) Golly symmetry type specified overall.

### Transitions
Semicolons are allowed alongside commas to separate different cellstates, and as a visual aid their use as a "final" separator
(that is, separating a transition from its resultant cellstate) is strongly encouraged.
```rb
# Nutshell
neighborhood: von Neumann

0, 1, 2, 3, 4; 5
```
```rb
# Golly
0, 1, 2, 3, 4, 5
```

Individual cellstates of a transition may be prefixed with a compass direction for clarity, and a *range* of compass directions
can be indicated using double..dots; this can displace repetition of a given cellstate.
```rb
# Nutshell
neighborhood: von Neumann

0, N 1, E..S 3, W 1; 4
```
```rb
# Golly
0, 1, 3, 3, 1, 4
```
Transitions by default use the Golly-canonical ordering -- usually `C, N, ..., C'`
(center cellstate, northern cellstate, ..., new center) --
but they are allowed to start on a different compass direction if explicitly specified.
```rb
# Nutshell
neighborhood: von Neumann

0, E..S 3, W..N 1; 4
```
```rb
# Golly
0, 1, 3, 3, 1, 4
```

Under certain symmetries, however, compass directions have no meaning -- these symmetry types utilize a different,
tilde-based shorthand. Nutshell's implementation of Golly's `permute` symmetry uses it like so:
```rb
# Nutshell
symmetries: permute

0, 1 ~ 3, 2 ~ 5; 9   # Specifying amount of each cellstate (three 1s and five 2s)
0, any ~ 2, 2, 6; 9  # Specifying some amounts (two "any"s) and leaving the rest to be distributed evenly (three 2s, three 6s)
0, 1, 2; 9           # Specifying nothing and letting each be distributed evenly (four 1s, four 2s)
any, any; 0          # Ditto above (8 "any"s)
```
```rb
# Golly
0, 1, 1, 1, 2, 2, 2, 2, 2, 9
0, any.0, any.1, 2, 2, 2, 6, 6, 6, 9
0, 1, 1, 1, 1, 2, 2, 2, 2, 9
any.0, any.1, any.2, any.3, any.4, any.5, any.6, any.7, any.8, 0
```

### Variables
All variable names are unbound, always, because needing to define eight separate "any state" vars is ridiculous.
```rb
# Nutshell
variable = (1, 2, 3, 4)

0, variable, variable, 0, 1, 2, 0, 2, 0; 1
```
```rb
# Golly
var variable.0 = {1, 2, 3, 4}
var variable.1 = variable.0

0, variable.0, variable.1, 0, 1, 2, 0, 2, 0, 1
```
That's not to say, however, that there is no concept of binding variables in Nutshell! Rather, it's that the variable
names themselves are not intrinsically bound by anything. Nutshell's idea of binding is explained later on.

Also allowed is the use of `{}` literals directly in transitions as 'on-the-spot' variables; no need to define them prior.
(Parentheses are also acceptable in place of curly brackets, as shown above and later... I personally prefer them.)
```rb
# Nutshell
(0, 1, 2), 3, (4, 5), 6, 7, 8, 9, 0, 1; 10
```
```rb
# Golly
var _random_name_A.0 = {0, 1, 2}
var _random_name_B.0 = {4, 5}

_random_name_A.0, 3, _random_name_B.1, 6, 7, 8, 9, 0, 1, 10
```
The var names "live" and "any" are predefined in Nutshell, assigned respectively to a rule's *live cellstates* and *all* of its cellstates.
```rb
# Nutshell
states: 5

a = live
b = any
```
```rb
# Golly
var a.0 = {1, 2, 3, 4}
var b.0 = {0, 1, 2, 3, 4}
```

As in Golly, variables are not nested; placing a variable inside another simply unpacks it thereinto.

### Operations
Variables can contain or be represented by "operations", with the binary `*` and `-` operators & the unary `-` and `--` operators.

These operations don't have to be assigned to variable names beforehand, by the way. All of what's described below is perfectly
valid if used directly in a transition, just like the 'on-the-spot' var literal mentioned above.

#### n * m ("Multiplication")
Not commutative.
```rb
# Nutshell
a = (1, 2) * 2  # variable 'times' integer (repeats the variable m times)
b = 2 * (1, 2)  # integer 'times' variable (repeats the integer to match the variable's length)
c = 0 * 3       # integer 'times' integer (repeats the first integer m times)
d = b * 3 * 2   # operations can be chained if needed (probably won't be needed)
e = (2*b, 1*(1,2), 0*3)  # ...and, like all expressions, can be placed inside a var literal
```
```rb
# Golly
var a.0 = {1, 2, 1, 2}
var b.0 = {2, 2}
var c.0 = {0, 0, 0}
var d.0 = {2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2}
var e.0 = {2, 2, 2, 2, 1, 1, 0, 0, 0}
```

#### n - m ("Subtraction")
Acts as a difference operation does between two sets.
```rb
# Nutshell
a = (1, 2, 3, 1) - 1    # variable 'minus' integer (removes the integer from the variable)
b = (1, 2, 3) - (2, 3)  # variable 'minus' variable (removes common elements from the former)
c = (3, 4, 5) - 5 - 4   # chaining again
d = (a-2, (3, 4)-3)     # again, operations can be placed inside var literals
```
```rb
# Golly
var a.0 = {2, 3}
var b.0 = {1}
var c.0 = {3}
var d.0 = {3, 4}
```

#### -n, --n ("Negation")
These are shorthand for, respectively, `live-n` and `any-n`.
```rb
# Nutshell
states: 4

a = -2
b = --2

c = live-2
d = any-2
```
```rb
# Golly
var a.0 = {1, 3}
var b.0 = {0, 1, 3}

var c.0 = {1, 3}
var d.0 = {0, 1, 3}
```
These can be chained indefinitely as well; `------------3` is a syntactically-valid expression, as is `some_varname----------5`
(subtraction then negation).
This is probably not too useful in practice, but... you never know.

#### Ranges
Though not exactly an operation, a range of cellstates can be expressed as two numbers (lower and upper bound) separated by double..dots.
```rb
# Nutshell
a = (3..6)         # lower..upper
b = (0, 2..5, 10)  # ranges and normal states can be interspersed normally
c = (1, 2+4..10)   # step+lower..upper
```
```rb
# Golly
var a.0 = {3, 4, 5, 6}
var b.0 = {0, 2, 3, 4, 5, 10}
var c.0 = {1, 4, 6, 8, 10}
```
Ranges differ from the expressions described above in that they cannot be used "bare" -- you always have to surround them with
parentheses or curly brackets as shown in `a = (3..6)` as they're only allowed within a variable.

### References
In a Golly table, variables are what we might call "name-bound": a variable name used once in a transition can refer to any of the
states it comprises, but from then on that same name can only refer to the first state it matched, like how back-referring to a
regex group matches the exact same text rather than applying the group's pattern anew.
In other words, with `var a={1,2}`, the sequence `a,a` can match `1,1` and `2,2` but **not** `1,2` or `2,1`, because the name `a` is
*bound* to the first cellstate it matches.

This behavior is intentional, but it comes with a side-effect: if the writer *should* wish for the above sequence to match `1,2` or
`2,1` without any of the binding, then they must define two separate variables, `var a={1,2}` and `var b=a`, writing the sequence as
`a,b`.

This doesn't seem bad at all on a small scale. It's convenient to be able to do it both ways, after all. However, in nearly any
large project, this forces each variable definition to be duplicated up to nine times (depending on the neighborhood, of
course) which gets messy and tedious to keep track of, making it an easy source of headaches and bugs and often both.

Nutshell's key innovation (and the only thing, in fact, that it mandates be done differently than in Golly) is in noting
that the *name* of a variable doesn't need to hold any particular meaning, only its value within a given transition.
Thus, rather than binding to a variable's name, we can simply use... some other way of referring to nothing except the value it
holds at a given point.

### Bindings
This is handled in a straightforward manner by using compass directions as "indices" of a transition.
To bind to a previous variable, just refer to the compass direction it appeared at by wrapping it in [brackets]
(and by referring to the origin cellstate as [0] since, being at the center, it has no nameable compass direction):
```rb
# Nutshell
any, any, any, [0], [NE], 0, 1, 3, 2; [N]
any, N..E [0], SW..W any, 0; [W]
(1, 2), N..NW 0; [0]
```
```rb
# Golly
var _random_name.0 = {1, 2}

any.0, any.1, any.2, any.0, any.2, 0, 1, 3, 2, any.1
any.0, any.0, any.0, any.0, any.1, any.2, any.3, any.4, 0, any.4
_random_name.0, 0, 0, 0, 0, 0, 0, 0, 0, _random_name.0
```
The eight compass directions, by the way, are not allowed to be used as variable names.

### Mappings
Now that we've introduced binding by compass-direction index rather than by name, we can extend the concept into a second
type of reference: *mapping* one variable to another.
For example, "mapping" the variable (0, 1, 2) to the variable (2, 3, 4) says if the former is 0 to return 2, if 1 then to
return 3, and if 2 then to return 4; this single mapping can therefore replace what would otherwise require a separate transition
for each of 0->1, 1->2, and 3->4. The syntax is `[compass direction: variable expression]`, like an extension to the binding syntax:
```rb
# Nutshell
a = (2, 3)
b = (4, 1)

0, (1, 2), E..NW 0; [N: (3, 4)]  #1
a, a, [N], [0], E..W 0, NW [0: b]; 10  #2
(1, 2, 3), N..NW 0, [0: (a, 1)]  #3
```
```rb
# Golly
var a.0 = {0, 1}

0, 1, 0, 0, 0, 0, 0, 0, 0, 3  #1
0, 2, 0, 0, 0, 0, 0, 0, 0, 4  #1

2, a.0, a.0, 2, 0, 0, 0, 0, 0, 4, 10  #2
3, a.0, a.0, 3, 0, 0, 0, 0, 0, 1, 10  #2

1, 0, 0, 0, 0, 0, 0, 0, 0, 2  #3
2, 0, 0, 0, 0, 0, 0, 0, 0, 3  #3
3, 0, 0, 0, 0, 0, 0, 0, 0, 1  #3
```

A variable literal used in a mapping can end with an ellipsis, `...`, which indicates that any remaining cellstates are to be
mapped to the value it follows.
```rb
# Nutshell
(1, 2, 3, 4, 5), [0: (3, 5, ...)], NE..NW any; 1
```
```rb
# Golly
var _random_name.0 = {2, 3, 4, 5}

1, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0
_random_name.0, 5, 0, 0, 0, 0, 0, 0, 0, 1
```

References are in essence single cellstates, so **they can be used anywhere a cellstate would** -- not just
as their own whole transition state. This means references can be used as operands of the `*`, `-`, & `--` operators and as
cellstates in variables (including variable literals in mappings).
```rb
# Nutshell
neighborhood: von Neumann
states: 6

(1, 2), --[0], (3, 4, 5)-[0: (3, 4)], ([0: (4, 3)], 5); [0: ([N], [E])]
```
```rb
# Golly
var _random_name_A.0 = {0, 2, 3, 4, 5}
var _random_name_B.0 = {0, 1, 3, 4, 5}
var _random_name_C.0 = {3, 5}
var _random_name_C.1 = _random_name_B.0
var _random_name_D.0 = {4, 5}
var _random_name_D.1 = _random_name_C.0

1, _random_name_A.0, _random_name_C.0, _random_name_C.1, _random_name_A.0; 0
2, _random_name_B.0, _random_name_B.0, _random_name_B.1, _random_name_B.0; 0
```
*(Note that Nutshell is for some reason unable to optimize its output here, so it renders the above with 20 transitions
and only the variables for (3, 5) & (4, 5); this result is, however, equivalent to the two transitions shown. It's all
the same to Golly, in any case.)*

### Auxiliary transitions
In general, the motion of a *moving* cell can only be described in Golly through two disconnected steps: first, a cell dies,
and an independent, dead cell is born in the next tick with the other's cellstate. This, though logical in the context of
a cellular automaton, is hard to describe as intuitive to the human writer; Nutshell for this reason provides a way of
describing *auxiliary* transitions affecting other cells in the neighborhood than the central one, sharing as
much of the same napkin as possible.

Auxiliaries are set off from the main transition with an arrow, and each individual auxiliary-transition specifier can take one of
four forms. First, the simplest syntax `compass direction:cellstate` indicates that a single cell of state `cellstate` should be birthed in
the specified direction:
```rb
# Nutshell
neighborhood: von Neumann

0, N 1, E 2, S 3, W 4; 5 -> N:3  S:2  # Birth a state-3 cell to the north and a state-2 cell to the south
```
```rb
# Golly
0, 1, 2, 3, 4, 5
1, any.0, any.1, 0, any.2, 3
3, 0, any.0, any.1, any.2, 2
```
`N:3` says to birth a state-3 cell to the north; the northern cell here was originally in state 1 and the center cell in
state 0. The transition implied by this auxiliary, then, is that any state-1 cell with a state-0 cell to its south should turn into
state 3 come the next generation, and similarly, `S:2` states that any state-3 cell to whose north is a state-0 cell should become of
state 2.

More of the transition napkin is shared in fuller neighborhoods:
```rb
# Nutshell
0, 1, 2, 3, 4, 5, 6, 7, 8, 9; 10 -> N:3  NE:0
```
```rb
# Golly
0, 1, 2, 3, 4, 5, 6, 7, 8, 9
1, any.0, any.1, 2, 3, 0, 7, 8, any.2, 3
2, any.0, any.1, any.2, any.3, 3, 0, 1, any.3; 0
```
Just to run through what's happening, let's take a graphical look at the main cell's Moore napkin:
```hs
8 1 2
7 0 3
6 5 4
```
These are the Moore neighborhoods of a cell A and the cell to its north B, where @ represents a shared cell:
```hs
b b b
@ B @
@ A @
a a a
```
Superimposing the above napkin and replacing the @ symbols gets us:
```hs
b b b
8 B 2
7 0 3
a a a
```

So in the `N:3` auxiliary, the cells shared between the main cell and the cell to its north in clockwise order are 2, 3, 0
(the A cell itself), 7, and 8. These values are reflected in the second Golly-output transition, and it's a similar process
for the `NE:0` auxiliary --
```hs
  b b b          b b b
a @ B b        a 1 B b
a A @ b        a 0 3 b
a a a          a a a  
```
-- where the shared cells in B's neighborhood are 3, 0 (the A cell itself), and 1, as shown in the third Golly transition above.

As a simple practical example, the transition `1, N..NW any; 0 -> NW:1` describes (under `symmetries: none`) a signal that travels
to its northwest at all costs, or (under another set of symmetries, say `symmetries: rotate4`) a cell that acts as a two-dimensional
spacefilling replicator.

A second type of auxiliary takes the form `compass direction[compass direction]` and, as the brackets suggest, is
analogous to a binding. It indicates that the cellstate that appeared toward the second compass direction should be
birthed toward the first:

```rb
# Nutshell
# compass directions E and S shown for clarity but, of course, not required
1, 0, 0, E (1, 2, 3), 0, S 4, 0, 0, 0; 2 -> S[E]
```
```rb
# Golly
var _random_name.0 = {1, 2, 3}

1, 0, 0, _random_name.0, 0, 4, 0, 0, 0, 2
4, 1, _random_name.0, 0, any.0, any.1, any.2, 0, 0, _random_name.0
```
The transition napkin is copied in the exact same manner as described before, but the resultant cellstate (`_random_name.0`)
is a binding rather than a single cellstate. An error will be raised if the cells in each compass direction specified do not
share any neighbors.

An example: `(1, 2, 3), N..NW any; 0 -> S[0]  E[E]` says that cells of state (1, 2, 3) should be sent south (the `[0]`
in `S[0]` refers to the input state) and that, when this happens, the cell to their east should stay as is (for instance,
to override a later transition).

The third type of auxiliary, given the relationship established above between bindings and mappings, is a natural extension
to that binding-like form. It uses the syntax `compass direction[compass direction: variable or other expression]`:
```rb
1, 0, 0, E (1, 2, 3), 0, S 4, 0, 0, 0; 2 -> S[E: (5, 6, 7)]
```
```rb
var _random_name.0 = {1, 2, 3}

1, 0, 0, _random_name.0, 0, 4, 0, 0, 0, 2  # main transition
4, 1, 1, 0, any.0, any.1, any.2, 0, 0, 5   # S:5
4, 1, 2, 0, any.0, any.1, any.2, 0, 0, 6   # S:6
4, 1, 3, 0, any.0, any.1, any.2, 0, 0, 7   # S:7
```
Anything valid in a mapping var literal is also valid here (references too), with one addition: an underscore, `_`, says not to make
an auxiliary transition at all for its cellstate.
```rb
# Nutshell
1, 0, 0, E (1, 2, 3), 0, S 4, 0, 0, 0; 2 -> S[E: (_, 6, 7)]

1, 0, 0, E (1, 2, 3), 0, S 4, 0, 0, 0; 2 -> S[E: (5, _, ...)]  # Underscores can be extended with the ellipsis as well
```
```rb
# Golly
var _random_name.0 = {1, 2, 3}

1, 0, 0, _random_name.0, 0, 4, 0, 0, 0, 2  # main transition
4, 1, 2, 0, any.0, any.1, any.2, 0, 0, 6   # S:6
4, 1, 3, 0, any.0, any.1, any.2, 0, 0, 7   # S:7

1, 0, 0, _random_name.0, 0, 4, 0, 0, 0, 2  # main transition
4, 1, 1, 0, any.0, any.1, any.2, 0, 0, 5   # S:5
```

Finally, as a shorthand for this last form in cases where both compass directions are the same, one can simply write
`compass direction[variable or other expression]` -- `S[(1, 2, 3)]`, for instance, will be interpreted as `S[S: (1, 2, 3)]`.

#### Precedence and "hoisting"
As you may have noticed, auxiliary transitions are output in the order of their Nutshell specifiers. This plays into
Golly's transition-precedence rules, where the first matching transition from the top down for a given napkin is selected,
meaning that earlier transitions always override later ones -- likewise, an auxiliary will (should an appropriate situation
arise) always override the ones it precedes.

In some cases, auxiliaries will need to override the main transition and not just each other, meaning that (unlike in the
examples above) they'll have to be output before it. This can be indicated using the arrow `=>` rather than `->`, with
thoroughly-identical syntax otherwise:
```rb
# Nutshell
0, 1, 2, 3, 4, 5, 6, 7, 8, 9 => S:1

0, (0, 1), 2, 3, 4, 5, 6, 7, 8, 9 => S:1  E[N] -> N:0  # can also be ` -> N:0 => S:2  E2`
```
```rb
# Golly
var _random_name.0 = {1, 2}

5, 0, 3, 4, any.0, any.1, any.2, any.3, 6, 7, 1  # S:1
0, 1, 2, 3, 4, 5, 6, 7, 8, 9  # main transition

5, 0, 3, 4, any.0, any.1, any.2, any.3, 6, 7, 1  # S:1
3, 2, any.0, any.1, any.2, 5, 6, 0, _random_name.0, _random_name.0  # E[N]
0, _random_name.0, 2, 3, 4, 5, 6, 7, 8, 9  # main transition
_random_name.0, any.0, any.1, 2, 3, 0, 7, 8, any.2, 0  # N:0
```

- custom symmetry types
- non-table-related changes

- - - - - - -

- If a variable literal is too small to map to, an error will be raised that can be rectified by either (a) filling it out with more cellstates,
  or (b) using the `...` operator to say *"fill the rest out with whatever value preceded the `...`"*.
  However, If the "map-to" is *larger* than its "map-from", extraneous values will simply be ignored.

### Custom symmetry types
The implementation of the above-mentioned symmetry-switching allows, conveniently, for non-Golly-supported symmetries to be defined and then simply expanded by Nutshell into
one of Golly's symmetry types. Provided by Nutshell is a small "standard library" of sorts that comes with the following:

- `symmetries: nutshell.AlternatingPermute`: Permutational symmetry, like `symmetries: permute`, but only between every *second* cell in
  a napkin. Under the Moore neighborhood, this means that cellstates are permuted between orthogonal neighbors and, separately, between
  diagonal neighbors; under vonNeumann, that cellstates are permuted between opposing pairs of neighbors; and, though *possible* to apply
  under hexagonal symmetry (where permutation would occur between (N, SE, W) and (E, S, NW)), it would be meaningless so only the
  former two are supported.  
  This symmetry type supports the tilde-based shorthand, but it only spreads cellstates out within their permute space (i.e.
  `0, 1, 2; 0` results in the Moore transition `0, 1, 2, 1, 2, 1, 2, 1, 2; 0` because the 1 and 2 are distributed into alternating slots).
- `symmetries: nutshell.Rotate2`: Identical to Golly's hexagonal `rotate2`, but allows Moore and vonNeumann as well.
- `symmetries: nutshell.ReflectVertical`: Vertical reflection.

In addition, although the API for it is somewhat clunky at present, you as the user are allowed to define your own custom symmetries. To do so, create a `.py` file and within it a class
that inherits from Nutshell's exposed `Napkin` class (alternatively, `OrthNapkin` or `HexNapkin`):

```py
from nutshell import Napkin
from nutshell.napkins import oneDimensional, vonNeumann, hexagonal, Moore, Any

class MySymmetries(Napkin):
    neighborhoods = ...
    fallback = ...

    @property
    def expanded(self):
       ...
```

As shown by the ellipses, there are three things you need to define within your class.
- `neighborhoods`: a tuple containing the *length* of each neighborhood that your symmetries support. These are ultimately just integers, but Nutshell has the constants `oneDimensional`,
  `vonNeumann`, `hexagonal`, and `Moore` defined respectively as `2`, `4`, `6`, and `8` for clarity.  
  For example, on a symmetry type meant for the Moore and vonNeumann neighborhoods, one would assign `neighborhoods = vonNeumann, Moore` (with no particular ordering required).  
  **If you want to support all neighborhoods Golly offers**, write `neighborhoods = Any` instead; `Any` is another Nutshell constant name, aliased to the Python value `None`.
- `fallback`: Either the name, as a string, of a Golly symmetry which is a superset of (or perhaps equivalent to) yours and thus can be expanded to during transpilation... or,
  if your symmetry type supports more than one neighborhood for which different appropriate Golly symmetries are available, a dictionary of {`neighborhood length`: `Golly symmetry`}.
  to the same effect. (`Any`, aka Python `None`, can be used in this dict as well.)  
  For example, the class for `nutshell.AlternatingPermute` above has `fallback = 'rotate4reflect'`, because that is the "highest" (most expressive) Golly symmetry in which multiple
  transitions are able to express a single AlternatingPermute transition.  
  The class for `nutshell.Rotate2` above has `fallback = {Any: 'none', hexagonal: 'rotate2'}`, because Golly already has rotate2 support for hexagonal neighborhoods, so we don't want
  to unnecessarily expand `nutshell.Rotate2` to None if used there -- but for other neighborhoods, the only way to express Rotate2 in Golly is via `none` symmetry.
  When in doubt, use `fallback = 'none'`.
- `expanded`: To explain this, it should first be mentioned that `Napkin` is a subclass of Python's built-in `tuple` type; the reason it's
  called Napkin and not something like Symmetries is that a single Napkin instance *represents* the neighbor states of a given transition.
  That is, when expanding symmetries, an instance of the pertinent Napkin class is constructed from the neighbor states of the current
  transition to determine how to treat its symmetries.  
  Instances of napkins under your custom symmetries are constructed as `MySymmetries((0, 1, 2, 3, 4, 5, 6,7))`
  (assuming Moore neighborhood), i.e. with the sequence of neighbor states it has to represent. The job of `expanded`, given that, is to
  provide a representation of what a single napkin in your symmetry type looks like *when expanded into `symmetries: none`*,
  and (importantly!!) returning this representation in the *exact same order* for any equivalent napkin. For example,
  `ReflectHorizontal((0, 1, 2, 3, 4, 5, 6, 7)).expanded` and `ReflectHorizontal((0, 7, 6, 5, 4, 3, 2, 1)).expanded` **both**
  return the exact list `[(0, 1, 2, 3, 4, 5, 6, 7), (0, 7, 6, 5, 4, 3, 2, 1)]` (and both in that order), because the
  two Moore-neighborhood napkins are equivalent under ReflectHorizontal symmetry.  
  Similarly, `ReflectHorizontal((2, 4, 6, 8)).expanded` returns `[(2, 4, 6, 8), (2, 8, 6, 4)]`, **as does**
  `ReflectHorizontal((2, 8, 6, 4)).expanded`, because the vonNeumann-neighborhood napkin `2,4,6,8` reflected horizontally is `2,8,6,4` and
  so both are equivalent under reflect_horizontal symmetry.  
  (The sequence type that `expanded` returns doesn't matter as long as it's some iterable -- but (a) its individual elements must all be
  hashable, and (b) it must not contain any occurrences of itself. It's thus probably best to have `expanded` return a sequence of
  tuples.)  
  After that, save your file in a directory accessible from the directory of the nutshell file you wish to use the symmetry type from --
  and you're done! It'll be accessible from a Nutshell rule as `<import path to containing file>.<class name>`. For instance, the symmetry
  type above will be accessible as `symmetries: custom_symmetries.MySymmetries` if it's saved in a file called
  `custom_symmetries.py` in the same directory as the nutshell file it's used from.  
  The custom-symmetry-type API will be simplified in the future to make it more accessible.

## Non-table-related changes
- The preferred file extension is `.ruel`, both a holdover from when this project was named `rueltabel` and a simple-but-recognizable variant
  of "rule" to distinguish nutshell files from standard `.rule` files. This obviously isn't enforced anywhere, however, and might also be subject to
  change later.
- Comments in every segment (barring `@NUTSHELL`, where everything after the first word is a comment) start with `#` and stretch to the end of a line.
- The `@COLORS` segment in nutshells allows multiple states with the same color to be defined
  on the same line as each other, and for a color to be written as either a triplet of base-10 `R G B` values, as in Golly, or a
  hexadecimal color code. As a result of its allowing multiple colors, the "key/value" order, if you will, has been switched: the color now
  goes first on a line, followed by all the states it's assigned to. A range can be used here identically to that found in variable
  literals.  
  For instance: `FFF: 1 10` says to assign the color `#FFFFFF` to states 1 and
  10, and can also be written as `FFFFFF: 1 10` or `255 255 255: 1 10`.
- The `@ICONS` segment is based around RLEs instead of Gollyesque XPM data. See [this post](http://conwaylife.com/forums/viewtopic.php?f=7&t=3361&p=59944#p59944)
  for an explanation + example. Ranges are also supported in icon state specifiers.
- The `@NUTSHELL` segment allows *constants*, which carry over to and are usable in the `@TABLE`, `@COLORS`, and `@ICONS` segments, to be
  defined alongside a description of each state. Take the following example:

```rb
@NUTSHELL foo

1: Stationary data {DATA}
3: Signal over data
4: Signal over vacuum {SIGNAL}

@TABLE
...
```
  The names `DATA` and `SIGNAL` will be usable within the aforementioned segments as aliases for, respectively, states `1` and `4`.  
  It is recommended but nowhere required that constant names be written in `UPPERCASE` or at least `PascalCase` and normal
  variable names in `lowercase`, `camelCase`, or `snake_case`; the initial capitals help visually distinguish constants from multi-state variables.  
  For the actual registration of a constant, all that matters is that its line in `@NUTSHELL` start with `<number>:` and contain anywhere a pair
  of `{braces}` that enclose the constant's name. The braced part and any whitespace separating it from the previous word will be removed
  from the final `@RULE` segment in the output file.
- **All segments are optional**. The parser will in addition transcribe "non-special" segments *as is*, meaning that
  a file can have a `@RULE` segment rather than `@NUTSHELL` and it will be transcribed into the output file untouched.
- The other "special" nutshell segments like `@TABLE` and `@ICONS` and `@COLORS`, none of whose names differ from
  their Golly-format counterparts, will still be ignored by the parser if their header is immediately followed by
  the comment `#golly` -- either on the same line (after whitespace) or on the line immediately below.
