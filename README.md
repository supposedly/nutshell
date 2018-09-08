
# CA rules “in a nutshell”

[![Discord](https://img.shields.io/badge/Chat-on%20Discord-7289da.svg?logo=discord&logoWidth=17)](https://discord.gg/BV6zxM9)  
A transpiler from a reimagined Golly ruletable language to the traditional format. See [`examples/`](/examples) for examples, and if none
of this makes any sense to you and you aren't sure how you got here, check out the [layman's README](documents/LAYMAN-README.md).

## Contents
* [Setup](#setup)
* [Usage](#usage)
* [Glossary](#glossary-of-nutshell-specific-terms)
* [What's new](#whats-new)
    - [Directives](#directives)
    - [Transitions](#transitions)
    - [Variables](#variables)
      <!--
      - [Variable names](#variable-names)
      -->
    - [Operations](#operations)
        <!--
        - ["Multiplication"](#n--m-multiplication)
        - ["Subtraction"](#n---m-subtraction)
        - ["Negation"](#-n---n-negation)
        - [Ranges](#ranges)
        -->
    - [References](#references)
        <!--
        - [Bindings](#bindings)
        - [Mappings](#mappings)
        -->
    - [Auxiliary transitions](#auxiliary-transitions)
        <!--
        - [Precedence and "hoisting"](#precedence-and-hoisting)
        -->
    - [Custom symmetry types](#custom-symmetry-types)
* [Non-table-related changes](#non-table-related-changes)
    - [The `@NUTSHELL` segment](#the-nutshell-segment)
    - [The `@COLORS` segment](#the-colors-segment)
    - [The `@ICONS` segment](#the-icons-segment)

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
$ nutshell-ca transpile [infile] [outdir] [-v | -q | -s | -p | -t | -f]
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
                     Transition should be given in the standard Golly form `C,N,...,C'`&nbsp;-- that is, state of the
                     current center cell, then its neighborhood, and finally the state it transitions into
                     on the next tick. Use `*` as an "any state" wildcard. Old example [here](https://user-images.githubusercontent.com/32081933/39951382-2b37fca0-553e-11e8-87b5-69685dfe4881.png)!

## Glossary of Nutshell-specific terms
- **variable**: Either a literal statelist or a name referring to one. 
- **expression**: Anything that resolves to a statelist, including varnames and operations.
- **state list** (or state-list, statelist): An ordered sequence of cellstates or expressions (written literally).
  This is referred to as a "variable" in Golly, but here it's better to distinguish it from the prior terms. 
- **directive**: A declaration following the form `name: value` that describes anything about a ruletable.
- **term**: One individual element of a transition napkin.
- **napkin** (or transition napkin): Referring to the cells in another's neighborhood, including their states. Coined by
  conwaylife forum contributor 83bismuth38. (In contrast, the term "neighborhood" refers only to the positions of these cells)

## What's new
### Directives
The `n_states` directive's name has been changed to `states` (though the former can still be used),
and all directives ignore whitespace in their values&nbsp;-- so one may write, say, `symmetries: rotate 4` or
`neighborhood: von Neumann`. The `symmetries` directive can take a Python import path for *custom symmetry types*;
this will be elaborated upon later on.
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
Semicolons are allowed alongside commas to separate different terms, and as a visual aid their use as a "final" separator
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

Transitions, whose terms are listed in clockwise order,
by default use the Golly-canonical ordering&nbsp;-- usually `C, N, ..., C'`
(center cellstate, northern cellstate, ..., new center)&nbsp;--
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

Under certain symmetries, however, compass directions have no meaning&nbsp;-- these symmetry types utilize a different,
tilde-based shorthand. Nutshell's implementation of Golly's `permute` symmetry uses it like so:
```rb
# Nutshell
symmetries: permute

0, 1 ~ 3, 2 ~ 5; 9   # Specifying amount of each term (three 1s and five 2s)
0, any ~ 2, 2, 6; 9  # Specifying some amounts (two "any"s) and leaving the rest to be distributed evenly (three 2s, three 6s)
0, 1, 2; 9           # Specifying nothing and letting all terms be distributed evenly (four 1s, four 2s)
any, any; 0          # Ditto above (8 "any"s)
```
```rb
# Golly
0, 1, 1, 1, 2, 2, 2, 2, 2, 9
0, any.0, any.1, 2, 2, 2, 6, 6, 6, 9
0, 1, 1, 1, 1, 2, 2, 2, 2, 9
any.0, any.1, any.2, any.3, any.4, any.5, any.6, any.7, any.8, 0
```
If the "unspecified" terms cannot be distributed perfectly into the table's neighborhood, precedence will be given to those
that appear earlier; `2, 1, 0` under Moore, for instance, will expand into `2,2,2,1,1,1,0,0`, but `0, 1, 2` will expand into
`0,0,0,1,1,1,2,2`.

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

Also allowed is the use of state-list literals directly in transitions as 'on-the-spot' variables; no need to define them prior.
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
The varnames "live" and "any" are predefined in Nutshell, assigned respectively to a rule's *nonzero cellstates* and *all* of its cellstates.
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

As in Golly, variables do not nest; placing a variable or state-list inside another simply unpacks it thereinto.

#### Variable names
Varnames are alphanumeric (and case-sensitive) with three exceptions:
- Underscores are allowed.
- The first character of the name must be alphabetical.
- The name as a whole cannot match one of the eight compass directions: `N`, `E`, `S`, `W`, `NE`, `SE`, `SW`, `NW`.

### Operations
Variables can contain or be represented by "operations", with the binary `*` and `-` operators & the unary `-` and `--` operators.

These operations don't have to be assigned to variable names beforehand, by the way. All of what's described below is perfectly
valid if used directly in a transition, just like the "on-the-spot" state-lists mentioned above.

Note: the precedence rules can be skirted by placing operations in their own single-element statelists such as in `(any-3)*2`.

#### n * m ("Multiplication")
Left-associative and not commutative. Has the highest precedence.
```rb
# Nutshell
a = (1, 2) * 2  # variable 'times' integer (repeats the variable m times)
b = 2 * (1, 2)  # cellstate 'times' variable (repeats the cellstate to match the variable's length)
c = 0 * 3       # cellstate 'times' integer (repeats the cellstate m times)
d = b * 3 * 2   # operations can be chained if needed (probably won't be needed)
e = (2*b, 1*(1,2), 0*3)  # ...and, like all expressions, can be placed inside a literal statelist
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
a = (1, 2, 3, 1) - 1    # variable 'minus' cellstate (removes the cellstate from the variable)
b = (1, 2, 3) - (2, 3)  # variable 'minus' variable (removes common elements from the former)
c = (3, 4, 5) - 5 - 4   # chaining again
d = (a-2, (3, 4)-3)     # again, operations can be placed inside statelists
```
```rb
# Golly
var a.0 = {2, 3}
var b.0 = {1}
var c.0 = {3}
var d.0 = {3, 4}
```

#### -n, --n ("Negation")
These are shorthand for, respectively, `live-n` and `any-n`. Has higher precedence than the above.
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
They can be chained indefinitely as well; `-----3` is a syntactically-valid expression that will be parsed
as `--(--(-3))`, as is `some_varname-------5` (subtracting `--(--(--5)))`). This is probably not too useful
in practice, but... you never know.

#### Ranges
Though not exactly an operation, a range of cellstates can be expressed as two numbers (lower and upper bound) separated by double..dots,
with an optional step included.
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
Ranges differ from the expressions described above in that they cannot be used "bare"&nbsp;-- you always have to surround them with
parentheses or curly brackets as shown in `a = (3..6)` as they're only allowed within a statelist.

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

Nutshell's key innovation (and the only thing, in fact, that it mandates be done differently than in Golly besides also eschewing
the `var` keyword) is in noting that the *name* of a variable doesn't need to hold any particular meaning, only its value within
a given transition. Thus, rather than binding to a variable's name, we can simply use... some other way of referring to nothing except
the value it holds at a given point.

#### Bindings
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

Note that in symmetry types where compass directions have no meaning&nbsp;-- the same symmetry types mentioned in
[Transitions](#transitions), in fact, that use `~` as a shorthand rather than specifying
compass-direction ranges&nbsp;-- Nutshell enforces the use of numbers, not compass directions, to bind to.
For instance, under `permute` symmetry, the Golly transition `0, some_var, 0, 0, 0, 0, 0, 0, 0, some_var` is
replicated as `0, some_var ~ 1, 0; [1]` and not `0, some_var ~ 1, 0; [N]`.

#### Mappings
Now that we've introduced binding by compass-direction index rather than by name, we can extend the concept into a second
type of reference: *mapping* one variable to another.
For example, "mapping" the variable (0, 1, 2) to the variable (2, 3, 4) says if the former is 0 to return 2, if 1 then to
return 3, and if 2 then to return 4; this single mapping can therefore replace what would otherwise require a separate transition
for each of 0->1, 1->2, and 3->4. The syntax is `[compass direction: expression]`, like an extension to the binding syntax:
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

A statelist used in a mapping can end with an ellipsis, `...`, which indicates that any remaining cellstates are to be
mapped to the last value:
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
If a variable is too small to map to, an error will be raised that can be rectified by either (a) filling it out with more
cellstates, or (b) using the `...` as above.
However, if the "map-to" is *larger* than its "map-from", extraneous values will simply be ignored.

References are in essence single cellstates, so **they can be used anywhere a cellstate would**&nbsp;-- not just
as their own whole transition state. This means references can be used as operands of the `*`, `-`, & `--` operators and as
cellstates in variables (including in statelists of mappings, meaning they can be nested indefinitely).
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
var _random_name_C.1 = _random_name_C.0
var _random_name_D.0 = {4, 5}
var _random_name_D.1 = _random_name_D.0

1, _random_name_A.0, _random_name_C.0, _random_name_C.1, _random_name_A.0; 0
2, _random_name_B.0, _random_name_D.0, _random_name_D.1, _random_name_D.0; 0
```

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
And these are the Moore neighborhoods of a cell A and the cell to its north B, where @ represents a shared cell:
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
for the `NE:0` auxiliary&nbsp;--
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
is a binding rather than a single state. An error will be raised if the cells in each compass direction specified do not
share any neighbors.

An example: `(1, 2, 3), N..NW any; 0 -> S[0]  E[E]` says that cells of state (1, 2, 3) should be sent south (the `[0]`
in `S[0]` refers to the input state) and that, when this happens, the cell to their east should stay as is (for instance,
to override a later transition).

The third type of auxiliary, given the relationship established above between bindings and mappings, is a natural extension
of the previous binding-like form into what's essentially a mapping. It uses the syntax
`compass direction[compass direction: expression]`:
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
Anything valid in a mapping statelist is also valid here (references too), with one addition: an underscore, `_`, says not to make
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
`compass direction[expression]`&nbsp;-- `S[(1, 2, 3)]`, for instance, will be understood as `S[S: (1, 2, 3)]`.

#### Precedence and "hoisting"
As you may have noticed, auxiliary transitions are output in the order of their Nutshell specifiers. This plays into
Golly's transition-precedence rules, where the first matching transition from the top down for a given napkin is selected,
meaning that earlier transitions always override later ones&nbsp;-- likewise, an auxiliary will (should an appropriate situation
arise) always override any that follow it.

In some cases, auxiliaries will need to override the main transition and not just each other, meaning that (unlike in the
examples above) they'll have to be output before it. This can be indicated using the arrow `=>` rather than `->`, with
an otherwise-thoroughly-identical syntax:
```rb
# Nutshell
0, 1, 2, 3, 4, 5, 6, 7, 8, 9 => S:1

0, (0, 1), 2, 3, 4, 5, 6, 7, 8, 9 => S:1  E[N] -> N:0  # can also be ` -> N:0 => S:2  E[N]`
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

#### Symmetries
Auxiliaries can be assigned a different set of symmetries than their main transition:
```rb
# Nutshell
symmetries: none

0, NE 0, E..N any; 1 -> E:3  rotate4(NE[E: (1, 2, 3, 4, 5)]  N:0  NE[N])
```
```rb
# Golly
0, any.0, 0, any.1, any.2, any.3, any.4, any.5, any.6, 1  # main transition

any.0, 0, any.1, any.2, any.3, any.4, any.5, 0, any.6, 3  # E:3

any.0, 0, any.1, 0, any.2, any.3, any.4, any.5, any.6, 0  # N:0
any.0, any.1, any.2, any.3, any.4, 0, any.5, 0, any.6, 0  # N:0
any.0, any.1, any.2, 0, any.3, 0, any.4, any.5, any.6, 0  # N:0
any.0, 0, any.1, any.2, any.3, any.4, any.5, 0, any.6, 0  # N:0

0, any.0, 0, any.1, any.2, any.3, any.4, any.5, any.6, any.0  # NE[N]
0, any.0, any.1, any.2, 0, any.3, any.4, any.5, any.6, any.2  # NE[N]
0, any.0, any.1, any.2, any.3, any.4, 0, any.5, any.6, any.4  # NE[N]
0, any.0, any.1, any.2, any.3, any.4, any.5, any.6, 0, any.6  # NE[N]
```
Symmetry-specifier groups cannot be nested.

...handy as that is, though, it's still missing something. Consider the following transition:
```rb
# Nutshell
states: 5
neighborhood: von Neumann

symmetries: none  # Forcing expansion into `none` symmetry
symmetries: rotate4

0, live, 2, 3, 4; [N] -> N[N]
```
```rb
# Golly

# 0, live, 2, 3, 4; [N]
0, 2, 3, 4, live.0, live.0
0, 3, 4, live.0, 2, live.0
0, 4, live.0, 2, 3, live.0
0, live.0, 2, 3, 4, live.0
# N[N]
live.0, 0, any.0, any.1, any.2, live.0
live.0, any.0, any.1, 0, any.2, live.0
live.0, any.0, 0, any.1, any.2, live.0
live.0, any.0, any.1, any.2, 0, live.0
```
Though the `N[N]` auxiliary *appears* to be saying _"keep to the north whatever's there"_, what it actually says is
_"keep the `live` cell where it is, even though it won't always be to the north thanks to `rotate4`"_. This may seem
to be rectifiable by placing the `N[N]` under `none` symmetry, like so:
```rb
# Nutshell
states: 5
neighborhood: von Neumann

symmetries: none
symmetries: rotate4

0, live, 2, 3, 4; [N] -> none(N[N])
```
```rb
# Golly

# 0, live, 2, 3, 4; [N]
0, 2, 3, 4, live.0, live.0
0, 3, 4, live.0, 2, live.0
0, 4, live.0, 2, 3, live.0
0, live.0, 2, 3, 4, live.0
# N[N]
live.0, any.0, any.1, 0, any.2, live.0
```
...but what that actually results in, as shown in the second codeblock, is the auxiliary's being applied in the
exact same fashion, just *only* to the north. To actually change this behavior, include an exclamation mark after
the symmetry type's name:
```rb
# Nutshell
states: 5
neighborhood: von Neumann

symmetries: none
symmetries: rotate4

0, live, 2, 3, 4; [N] -> none!(N[N])
```
```rb
# Golly

# 0, live, 2, 3, 4; [N]
0, 2, 3, 4, live.0, live.0
0, 3, 4, live.0, 2, live.0
0, 4, live.0, 2, 3, live.0
0, live.0, 2, 3, 4, live.0
# N[N]
live.0, any.0, any.1, 0, any.2, live.0
2, any.0, any.1, 0, any.2, 2
3, any.0, any.1, 0, any.2, 3
4, any.0, any.1, 0, any.2, 4
```
This indicates to Nutshell that the auxiliary should remain "stationary" while the main transition's symmetries are applied.
If it were written here as `rotate4!(N[N])` instead of `none!(N[N])`, the Golly output would contain a rotate4 expansion of
each of the final four lines.

### Custom symmetry types
The implementation of the above-mentioned symmetry-switching allows, conveniently, for nonstandard symmetries to be defined and
then simply expanded by Nutshell into one of Golly's symmetry types. Provided by Nutshell is a small "standard library" of sorts
that comes with the following:

- `symmetries: nutshell.AlternatingPermute`: Permutational symmetry, like `symmetries: permute`, but only between every *second* cell in
  a napkin. Under the Moore neighborhood, this means that cellstates are permuted between orthogonal neighbors and, separately, between
  diagonal neighbors; under vonNeumann, that cellstates are permuted between opposing pairs of neighbors; and, under hexagonal, between [N, SE, W] and [E, S, NW].  
  This symmetry type supports the tilde-based shorthand, but it only spreads terms out within their permute space (as in,
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
  (The sequence type that `expanded` returns doesn't matter as long as it's some iterable&nbsp;-- but (a) its individual elements must all be
  hashable, and (b) it must not contain any occurrences of itself. It's thus probably best to have `expanded` return a sequence of
  tuples.)  
  After that, save your file in a directory accessible from the directory of the nutshell file you wish to use the symmetry type from&nbsp;--
  and you're done! It'll be accessible from a Nutshell rule as `<import path to containing file>.<class name>`. For instance, the symmetry
  type above will be accessible as `symmetries: custom_symmetries.MySymmetries` if it's saved in a file called
  `custom_symmetries.py` in the same directory as the nutshell file it's used from.  
  The custom-symmetry-type API will be simplified in the future to make it more accessible.

## Non-table-related changes
- The preferred file extension is `.ruel`, both a holdover from when this project was named `rueltabel` and a simple-but-recognizable
  variant of "rule" to distinguish nutshell files from standard `.rule` files. This obviously isn't enforced anywhere, however, and may
  also be subject to change.
- Comments in every segment (barring `@NUTSHELL`, where everything after the first word is a comment) start with `#` and stretch to the end
  of a line.
- **All segments are optional**. Nutshell will in addition transcribe "non-special" segments *as is*, meaning that
  a file can have a `@RULE` segment rather than `@NUTSHELL` and it will be transcribed into the output file untouched.
- The other "special" nutshell segments like `@TABLE` and `@ICONS` and `@COLORS`, none of whose names differ from
  their Golly-format counterparts, will still be ignored if their header is immediately followed by
  the comment `# golly`&nbsp;-- either on the same line (after whitespace) or on the very next.

### The `@NUTSHELL` segment
This segment replaces Golly's `@RULE`.
It allows *constants*, which carry over to and are usable in the `@TABLE`, `@COLORS`, and `@ICONS` segments, to be defined alongside a
description of each state. Take the following example:

```rb
@NUTSHELL foo

1: Stationary data {DATA}
3: Signal-transferring data
4: Signal over vacuum {SIGNAL}

@TABLE
...
```

The names `DATA` and `SIGNAL` will be usable within the aforementioned segments as aliases for, respectively, cellstates `1` and `4`.  
It is strongly recommended albeit nowhere required that constant names be written in `UPPERCASE` or at least `PascalCase` and normal
variable names in `lowercase`, `camelCase`, or `snake_case`; the initial capitals help visually distinguish constants from multi-state variables.

For the actual registration of a constant, all that matters is that its line in `@NUTSHELL` start with `<number>:` and contain anywhere a
pair of `{braces}` that enclose the constant's name. The braced part and any whitespace separating it from the previous word will be removed
from the final `@RULE` segment in the output file.

### The `@COLORS` segment
This segment allows multiple states with the same color to be defined on the same line as each other, and for a color to be
written either as a triplet of base-10 `R G B` values, like in Golly, or as a hexadecimal color code.
As a result of its allowing multiple colors, the "key/value" order, if you will, has been switched: the color now
goes first on a line, followed by all the states it's assigned to. A [range](#ranges) sans parentheses/curly brackets can
be used here as well.  

For instance: `FFF: 2 4 6 8 10` says to assign the color `#FFFFFF` to states 2, 4, 6, 8, and 10, and can also be written
as `FFF: 2+2..10` or `FFFFFF: 2+2..10` or `255 255 255: 2+2..10`.

### The `@ICONS` segment
This segment is based around Golly's RLE format instead of XPM data; the idea is that you're likely going to be in Golly anyway
when you're fiddling with a rule, so it'll be easier to quickly copy/paste an RLE in and out of a blank Golly tab than it'd be to
edit XPM images in your text editor. Non-normalized icons are automatically centered & uniformly resized to the nearest Golly icon
dimensions (7x7/15x15/31x31).

Each individual XRLE pattern listed represents one icon, and to assign this icon to some cellstate,
include the state or its `@NUTSHELL`-defined constant in a comment immediately above the icon's RLE pattern.
Multiple cellstates can be assigned to by listing them individually (as long as each cellstate appears either
with whitespace on both sides or with whitespace before and a comma after) or by describing them with a
[range literal](#ranges) sans parentheses/curly brackets.

Before further explanation, here's a simple example:

```rb
@NUTSHELL IconTest

@COLORS
FFF: 3

@ICONS       # Alternatively:
0: 303030    # .  303030
1: D0D0D0    # A  D0D0D0
2: 9CF       # B  9CF

#C Up arrow 1 2
x = 10, y = 9, rule = //10
I2A4.I2A$I2A4.I2A$.I2A2.I2A$.I2A2.I2A$2.I2AI2A$2.I2AI2A$3.I3A$3.I3A$
4.IA!

#C Down arrow: 4, 5
x = 10, y = 9, rule = //10
4.AI$3.3AI$3.3AI$2.2AI2AI$2.2AI2AI$.2AI2.2AI$.2AI2.2AI$2AI4.2AI$2AI4.
2AI!
```

Pixel colors in an icon are determined by those directive-like lines before the XRLEs. `0: 303030`, for instance, says
that state 0 (symbol `.`) in an icon should represent the hex color #303030 (Golly's default background color), `1: D0D0D0`
says that state 1 (the symbol `A`) represents the hex color #D0D0D0, and so on.
The cellstate's symbol also can be written instead of its number, as in `. 303030` / `A D0D0D0` / `B 9CF` (notice, no colon)
if it's easier to read.  
Nutshell comes with a utility to aid in creating these icons
(accessible as `nutshell-ca icon genrule <nutshell file> <outdir>`)
that generates a B/S012345678 ruletable whose `@COLORS` segment mirrors the colors in the nutshell file's `@ICONS`.

The rule of each RLE is ignored; just choose one with enough cellstates for its pattern to be pastable into Golly.
Note that the icons don't have to be in sequence or even present (the pre-icon comments determine ordering); if a certain state's
icon is omitted, like state 3's above, and it doesn't come *after* the highest-numbered state with an icon (in which case it
can & will be safely ignored), it will be made as a solid square colored according to what's assigned to that state in `@COLORS`.

If a missing cellstate is not addressed in `@COLORS` or if there is no `@COLORS` to use, an error will be raised&nbsp;-- but to
mitigate this, you can define a gradient with which to fill missing states. The syntax for this is
`? <hex color> <optional separator, ignored> <hex color>` (spaces required), where the first hex color is the
gradient's start and the second its end; this goes with the other color definitions before the RLEs.  
The gradient relies on the `states:` or `n_states:` directive in @TABLE to compute its medial colors, but if there is no
`@TABLE` or if it's written as `@TABLE #golly` (i.e. marked as "don't touch, Nutshell") then the `n_states` won't be available.
In this case you may append to the gradient line a bracketed number indicating the rule's "n_states" value, as in
`?  <hex color> <optional separator> <hex color> [<n_states>]`.

`@COLORS` colors will always take precedence over the gradient, except when the cellstate in `@COLORS` has an \*asterisk before it.

**Additionally:** If you have a Golly ruletable with its own `@ICONS` and do not wish to convert it to the Nutshell format manually,
there is a tool `nutshell-ca icon convert <rulefile> <outdir>` that can do it for you.
