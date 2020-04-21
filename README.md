
# CA rules “in a nutshell”

[![Discord](https://img.shields.io/badge/chat-on%20Discord-7289da.svg?logo=discord&logoWidth=17&logoColor=white)](https://discord.gg/BV6zxM9)
｜
[![Conwaylife.com](https://img.shields.io/badge/discuss-on%20Conwaylife.com-000.svg?logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA8AAAAPCAYAAAA71pVKAAAABmJLR0QABgAMABkbch97AAAACXBIWXMAAC4jAAAuIwF4pT92AAAAB3RJTUUH4gkOBRobRhT0twAAABl0RVh0Q29tbWVudABDcmVhdGVkIHdpdGggR0lNUFeBDhcAAABTSURBVCjPY/z//z8DuYAFixg+0xiROUwMFAAWXBLsvFJw9s/Pz0jTjAMge4mRImczYgnt/0R6gZGFiBDGCagX2sjOo7nNVAltcgKMkSoBxkiOZgAGwxRNuTqWVQAAAABJRU5ErkJggg==)](http://conwaylife.com/forums/viewtopic.php?f=7&t=3361)  
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
        - ["Rotation"](#n--m-n--m-rotation)
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
    - [Inline-rulestring transitions](#inline-rulestring-transitions)
    - [Custom neighborhoods](#custom-neighborhoods)
    - [Custom symmetry types](#custom-symmetry-types)
    - [Macros](#macros)
* [Non-table-related changes](#non-table-related-changes)
    - [The `@NUTSHELL` segment](#the-nutshell-segment)
    - [The `@COLORS` segment](#the-colors-segment)
    - [The `@ICONS` segment](#the-icons-segment)

## Setup
1. [Download & install Python 3.6](https://www.python.org/downloads/release/python-365/) or higher (support for < 3.6 hopefully coming soon)
2. Either:
    1. Execute the terminal command `pip install -U git+git://github.com/supposedly/nutshell.git` (or whichever of the
       pip command's variations works for you; you may need to try `python -m pip install`, `python3 -m pip install`,
       on Windows `py -m pip install`, ...) to install via pip directly,
    2. **OR** `git clone` this project, then `cd` to its directory and execute `pip install -U .` (using the correct one of
       the `pip install` variations discussed above)
4. Write your own "nutshell" rule file, then continue with the **Usage** section below.

## Usage
The `pip install` will add a command `nutshell-ca` for use in terminal. If this for any reason does
not work for you, you may instead either:
1. Run `python -m nutshell` instead of `nutshell-ca`, or
2. `git clone` Nutshell as in step 2.ii above, and then run `to_ruletable.py`
   from its root directory as a substitute for `nutshell-ca`.

```
$ nutshell-ca transpile [infile] [outdir] [-v | -q | -s | -c | -p | -t | -f]
(alternatively, `nutshell-ca t ...')
```
The output file will be written to `outdir` with a .rule extension and the same filename as `infile`.  
Supported flags, though there's more info in `--help` (note that `-v` and `-q` can come either
after or before the keyword `transpile`/`t` with no difference):
  - `-v`: Verbose. Can be repeated up to four times, causing more info to be displayed each time.
  - `-q`: Quiet. Opposite of the above, but only has one level.
  - `-s`: Source. Writes each Nutshell `@TABLE` line, as a comment, above the line(s) it compiles
          to in the final ruletable output. (If the compiled line is from an auxiliary-transition
          specifier, the specifier is printed instead along with its line number as normal.)
  - `-c`: Preserve comments. Causes comments in the Nutshell's `@TABLE` to be copied into the final
          output as faithfully as possible (i.e. as closely as possible to their original positions).
  - `-t [HEADER]`: Change the "COMPILED FROM NUTSHELL" header that is added by default to transpiled
                   rules. (If `-t` is given no argument the header will be removed)
  - `-f TRANSITION`: Find a certain transition defined within a table section; requires, of course, that
                     the rule have a `@TABLE` segment to search within. If a certain cell isn't behaving
                     the way it's supposed to, you can `-f` the transition it's undergoing, and nutshell
                     will find the offending transition for you (rather than you having to guess at what
                     you typo'd).  
                     Transition should be given in the standard Golly form `C,N,...,C'`&nbsp;-- that is, state of the
                     current center cell, then its neighborhood, and finally the state it transitions into
                     on the next tick.  
                     Use `*` and `?` as "any state" wildcards, difference being that `?`
                     will tell you what state(s) can be used in its position.  
                     Old example [here](https://user-images.githubusercontent.com/32081933/39951382-2b37fca0-553e-11e8-87b5-69685dfe4881.png)!

## Glossary of Nutshell-specific terms
- **variable**: Either a literal statelist or a name referring to one. 
- **expression**: Anything that resolves to a statelist: statelists themselves, varnames, and/or operations.
- **statelist** (or state-list, state list): An ordered sequence of cellstates or expressions, written literally.
  This is referred to as a "variable" in Golly, but in Nutshell it's more important to distinguish it from the prior terms. 
- **directive**: A declaration following the form `name: value` that describes something about a ruletable.
- **term**: One individual element of a transition napkin.
- **napkin** (or transition napkin): Refers to the cells in another cell's neighborhood *including* each one's state.
  In contrast, the term "neighborhood" refers only to the positions of these cells. (Originally coined by Conwaylife
  forum member 83bismuth38, with the long form "bowling napkin", to refer to a table that visualizes all possible transitions
  in a given neighborhood; a misconstrual of this coinage led to the term's Nutshell sense.)

## What's new
### Directives
First off: no directive is mandatory in Nutshell. Here is each directive's default value (i.e. the value it's
initialized to before `@TABLE` is parsed):

- `neighborhood: Moore`
- `symmetries: none`
- `states: ?`

Two things to note regarding the final item: first, that the `n_states` directive <!-- (though still usable by that name) -->
has been changed to `states`, and second that it accepts a value of `?`, which tells Nutshell to infer the amount
of cellstates in a rule by checking the maximum cellstate value referred to -- be it in a statelist, constant declaration,
or a literal number in a transition napkin. This means that the writer needn't bother keeping track of how many cellstates
a rule uses, and because `?` is `states`'s default value, it also means that a rule doesn't have to specify `states:` at all.

Additionally, all directives ignore whitespace in their values&nbsp;-- so one may write, say, `symmetries: rotate 4` or
`neighborhood: von Neumann`. The `symmetries` directive can take a Python import path for *custom symmetry types*, and
the `neighborhood` directive a series of compass directions for a *custom neighborhood*; these will be elaborated upon later on.
```rb
# Nutshell
@TABLE
states: 5
symmetries: rotate4 reflect
neighborhood: von Neumann
```
```rb
# Golly
@TABLE
neighborhood: vonNeumann
n_states: 5
symmetries: rotate4reflect
```

Lastly, the `symmetries` directive can be used multiple times within a file, allowing the writer to switch symmetries
partway through a rule. During transpilation, differently-symmetried transitions will be expanded into the "lowest"
(least-expressive) Golly symmetry type specified overall. (There is also, unlike in Golly, no enforced ordering of
the `neighborhood` and `symmetries` directives; either can come before the other.)

### Transitions
Semicolons are allowed alongside commas to separate different terms, and as a visual aid their use as a "final" separator
(that is, separating a transition's napkin from its resultant cellstate) is strongly encouraged.
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

Additionally, if **all** given terms of a transition have a compass-direction tag, any omitted ones will be filled in with the variable
`any` (introduced below). Note that, to ensure intent, this is **only** valid if there is not a single term given without a compass direction.

```rb
# Nutshell
neighborhood: von Neumann

0, N 1, S 2; 3
```
```rb
# Golly
neighborhood: vonNeumann

0, 1, any.0, 2, any.1, 3
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
The varnames "live" and "any" are predefined in Nutshell, assigned respectively to a rule's *nonzero* cellstates and *all* of its
cellstates.
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
Variables can contain or be represented by "operations", with the binary operators `*`, `-`, and `<<`/`>>` or the
unary operators `-` and `--`.

These operations also don't need to be assigned to variable names beforehand. All of the expressions below are perfectly
valid if used directly in a transition, just like the "on-the-spot" state-lists mentioned above.

Note: The binary operators are left-associative. Precedence rules can be skirted by placing operations in their own
single-element statelists, like `(any-3)*2`.

An exclamation mark followed by an expression (as a whole line) will cause the expression's result to be printed: `!(1, 2, 3)-(3, 4)`
will print `(1, 2)`, for instance, and `!any` will print the contents of variable `any`. This can help in debugging complex,
multi-operation variable expressions if need be.

#### n * m ("Multiplication")
Not commutative. Has the highest precedence.
```rb
# Nutshell
a = (1, 2) * 2  # variable 'times' integer (repeats the variable m times)
b = 2 * (1, 2)  # cellstate 'times' variable (repeats the cellstate to match the variable's length)
c = 0 * 3       # cellstate 'times' integer (repeats the cellstate m times)
d = b * 3 * 2   # operations can be chained if needed
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
Acts as a difference operation does between two sets. Has the lowest precedence.
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

#### n >> m, n << m ("Rotation")
Rotates a statelist in either direction. `m` is modulo'd by the statelist's length.
```rb
# Nutshell
a = (1, 2, 3)
b = a << 1

0, N..W 0, NW a; [NW: a >> 1]
```
```rb
# Golly
var a.0 = {1, 2, 3}
var b.0 = {2, 3, 1}

0, 0, 0, 0, 0, 0, 0, 0, 1, 3
0, 0, 0, 0, 0, 0, 0, 0, 2, 1
0, 0, 0, 0, 0, 0, 0, 0, 3, 2
```
Be aware that ordering is unlikely to be reflected / preserved in Golly output, because variables are converted
into Python [set objects](https://en.wikipedia.org/wiki/Set_%28abstract_data_type%29) just before being written
to the Golly rulefile; this means that it's just as likely for the above to result in `var a.0 = {1, 2, 3}` and
`var b.0 = {1, 2 3}`. The Nutshell-enforced ordering can always be observed, however, in the result of an operation
(like mapping) that spreads a variable out over multiple transitions.

#### -n, --n ("Negation")
These are shorthand for, respectively, `live-n` and `any-n`. Has higher precedence than "subtraction".
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
optionally with a step greater than 1.
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

Nutshell's key innovation (and the only supra-syntactical thing, in fact, that it mandates be done differently than in Golly's `@TABLE`)
is in noting that the *name* of a variable doesn't need to hold any particular meaning, only its value within
a given transition. Thus, rather than binding to a variable's name, we can simply use... some other way of referring to nothing
except the value it holds at a given point.

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

Multiple successive bindings to a previous term, as long as it is an expression, can be compressed like so:
```rb
# Nutshell
neighborhood: von Neumann

0, N..W [any]; 1
```
```rb
# Golly
0, any.0, any.0, any.0, any.0, 1
```
```rb
# Nutshell
symmetries: permute
neighborhood: von Neumann

0, [(1, 2)] ~ 3, [any]; [1]
```
```rb
# Golly
var _random_name.0 = {1, 2}

0, _random_name.0, _random_name.0, any.0, any.0, _random_name.0
```
The first transition is equivalent to `0, any, E..W [N]; [N]` and the other to `0, (1, 2) ~ 1, [1] ~ 2, any ~ 1, [3]; [1]`.

#### Mappings
Now that we've introduced binding by compass-direction index rather than by name, we can extend the concept into a second
type of reference: *mapping* one variable to another.
For example, "mapping" the variable (0, 1, 2) to the variable (2, 3, 4) says if the former is 0 to return 2, if 1 then to
return 3, and if 2 then to return 4; this single mapping can thus replace what would otherwise require a separate transition
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
(1, 2, 3, 4, 5), [0: (3, 5, ...)], NE..NW 0; 1
```
```rb
# Golly
var _random_name.0 = {2, 3, 4, 5}

1, 3, 0, 0, 0, 0, 0, 0, 0, 1
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

### Inline-rulestring transitions
In addition to those normal Golly-style transitions, Nutshell allows the use of rulestring segments (either Hensel-style or totalistic)
to specify a transition napkin.

These transitions' syntax is `initial, <rulestring / foreground state(s) / background states>; resultant`. Consider the
[isotropic non-totalistic](http://conwaylife.com/wiki/Isotropic_non-totalistic_Life-like_cellular_automaton)
rule _[tlife](http://conwaylife.com/forums/viewtopic.php?f=11&t=1831)_:
```rb
# Nutshell
0, <3 / 1 / 0>; 1
1, <2-i34q / 1 / 0>; 1

symmetries: permute
any, any; 0
```
[Its output file](https://gist.github.com/supposedly/078db47f6b05199b8fbe349ef5f91fed) is a touch too big to paste, but it:
1. Interprets `0, <3 / 1 / 0>; 1` as _"a state-`0` cell surrounded by `3` state-`1` cells (and otherwise state-`0` cells)
   will turn into state `1`,"_ then expands this into the permute-symmetry transition `0, 1, 1, 1, 0, 0, 0, 0, 0, 1`.
2. Interprets `1, <2-i34q / 1 / 0>; 1` as _"a state-`1` cell surrounded by a configuration matching `2-i`, `3`, or `4q`
   of state-`1` cells (and state-`0` cells otherwise) will remain state `1`,"_ then expands this into the appropriate
   rotate4reflect-symmetry transitions.
3. Proceeds as though the user had typed these expanded transitions out themself.

Each of the inline-rulestring lines comes with an implicit "transition-local" switch to `rotate4reflect` symmetry
(if using a Hensel-exclusive rulestring with letters and whatnot) or to `permute` symmetry (if using a totalistic rulestring),
but **other transitions are not affected**! This means that, in the Life table, the transition `any, N..NW any; 0` is actually
still under `symmetries: none` and will thus cause the whole table to be normalized thereinto; the tlife table, on the other hand,
has `symmetries: permute` to prevent this. In general, an inline-rulestring transition can be read as being preceded by a switch to
either `symmetries: rotate4reflect` or `symmetries: permute` (whichever is appropriate) and being followed by a switch back to the
previous symmetries.

For another example, WireWorld could be expressed as follows:
```py
# Nutshell
@NUTSHELL WireworldTest
: {Head} Electron head
: {Tail} Electron tail
: {Wire} Conductor/wire

@COLORS
0080FF: Head
FFF: Tail
FF8000: Wire

@TABLE
symmetries: permute
(Head, Tail), any; [0: (Tail, Wire)]
Wire, <12 / Head / (0, Tail, Wire)>; Head
```
...which takes advantage of some things described below, namely the [`@NUTSHELL`](#the-nutshell-segment) &
[`@COLORS`](#the-colors-segment) segments.

[References](#references) can be used here as well, but they look a little bit different: rather than referring
to a compass direction, they must refer to either `0` , `BG`, or `FG`. Respectively, those are the input, background,
and foreground state(s).  
For instance, the resultant state of `0, <23 / (0, 1) / (1, 2, 3)>; [FG: (3, 2, 1)]` is a mapping from the variable
`(1, 2, 3)`. If it were instead `[BG]`, then it would be a binding to the variable `(0, 1)`. Note that references are
valid within the `<>` section as well, as is the "inline binding" syntax.  
Lastly, the same inline-binding syntax that allows `[expression] ~ 5` and `N..NW [expression]` to be shorthand for,
respectively, `expression, [1] ~ 4` and `N [expression], NE..NW [N]` is usable here:
```rb
# Nutshell
0, <2 / (1, 2) / 0>; 3
0, <2 / [(1, 2)] / 0>; 3
```
```rb
# Golly
var _a0.0 = {1, 2}

0, _a0.0, _a0.1, 0, 0, 0, 0, 0, 0, 3
0, _a0.0, _a0.0, 0, 0, 0, 0, 0, 0, 3
```
Note that binding to a Hensel-notation napkin is tricky business, because unlike in a permute-symmetry napkin,
positions *do* matter -- in these cases `FG` and `BG` will give you the first available cell from the northmost one, which may
not be a fine-enough level of control. In such cases it's probably best *not* to bind at all to the foreground/background
states, but if one *must*, then compass directions can be used to refer to the cell at that position in a neighborhood's
[canonical orientation](http://www.ibiblio.org/lifepatterns/neighbors2.html).  
Note, this is only an issue with a rotate4reflect-requiring Hensel-notation rulestring, as in `0, <2-i34q / (1, 2) / 0>; [FG]`.
It is **not** an issue with a permute-symmetry rulestring as in `0, <23 / (1, 2) / 0>; [FG]`, and it even is a non-issue with
Hensel rulestrings **if** the bound-to term is guaranteed to be the same cellstate everywhere: `0, <2-i34q / [(1, 2)] / 0>; [FG]`.

#### Modifiers
The rulestrings do not strictly have to be Hensel rulestrings -- that's just the default. Placing a "modifier" name
after the rulestring will cause it to be interpreted differently. Currently-available modifiers:
- `hensel`, which is an alias for the default behavior.
- `!hensel`, which turns the rulestring into its *complement*. `<012345-i6 !hensel / 1 / 0>` is `<5i78 / 1 / 0>`
- `force-r4r`, which makes `<3 force-r4r / 1 / 0>` expand into a series of B3 rotate4reflect transitions *rather than*
  a single B3 permute transition as with `<3 / 1 / 0>`. Needed for [Brew.ruel](examples/nutshells/Brew.ruel),
  and likely in a lot of cases where a macro needs to apply to some inline-rulestring transitions.
- `b0-odd`, which applies Golly's odd-generation B0-rule transformation to the given rulestring. See
[`examples/BeeZero`](examples/nutshells/BeeZero.ruel) for usage.

These are user-creatable in the exact same manner as symmetries, although the API for this has not yet been
made user-friendly. A currently-indefinitely-postponed future release will remove `force-r4r` and `b0-odd` from the
"standard library", so to speak, and instead allow modifiers to be defined in a Python-code segment within a Nutshell
file itself. This will make it easier to transport Nutshell files along with their requisite modifiers.

### Custom neighborhoods
The `neighborhood` directive can be given a comma-delimited list of compass directions rather than a name, which makes
the CA use those compass directions (in the listed order) as its neighborhood. Nutshell will then expand all transitions
into the smallest encompassing Golly neighborhood.

```rb
# Nutshell
neighborhood: N, SE, SW
0, 1, 2, 3; 4
2, N 4, SE 2, SW any; 1
```
```rb
# Golly
neighborhood: Moore

0, 1, any.0, any.1, 2, any.2, 3, any.3, any.4, 4
2, 4, any.0, any.1, 2, any.3, any.4, any.5, any.6, 1
```

### Custom symmetry types
The implementation of the above-mentioned symmetry-switching also allows, conveniently, for nonstandard symmetries to be defined and
then simply expanded by Nutshell into one of Golly's symmetry types. Provided by Nutshell is a small "standard library" of sorts
that comes with the following:

- `symmetries: nutshell.ExplicitPermute`: Permute symmetry, but differs in that it does *not* attempt to infer the desired amounts of
  its given terms: if a term is given with no tilde, it is treated as `~ 1` rather than being spread out across the transition like
  `symmetries: permute` would do.
- `symmetries: nutshell.AlternatingPermute`: Permutational symmetry, like `symmetries: permute`, but only between every *second* cell in
  a napkin. Under the Moore neighborhood, this means that cellstates are permuted between orthogonal neighbors and, separately, between
  diagonal neighbors; under vonNeumann, that cellstates are permuted between opposing pairs of neighbors; and, under hexagonal, between [N, SE, W] and [E, S, NW].  
  This symmetry type supports the tilde-based shorthand in the same manner as `symmetries: nutshell.ExplicitPermute`,
  but it only spreads terms out __within their permute space__ (as in, `0, 1, 2; 0` results in the Moore transition
  `0, 1, 2, 1, 2, 1, 2, 1, 2; 0` because the 1 and 2 are distributed into alternating slots).
- `symmetries: nutshell.Rotate2`: Identical to Golly's hexagonal `rotate2`, but allows Moore and vonNeumann as well.
- `symmetries: nutshell.ReflectVertical`: Vertical reflection.
- `symmetries: nutshell.\ReflectDiagonal`: Reflection about the NW-SE diagonal axis.
- `symmetries: nutshell./ReflectDiagonal`: Reflection about the SE-NW diagonal axis.
- `symmetries: nutshell.XReflectDiagonal`: Reflection about both diagonal axes.
- `symmetries: nutshell.ExplicitPermute`: Permute symmetries, but there is no automatic expansion of tilde-omitted terms; omission of a tilde
  here is equivalent to `~ 1`. An error will be raised if an incorrect amount of terms results.

In addition, although the API for it is somewhat clunky at present, you as the user are allowed to define your own custom symmetries
via Python classes. See [documents/PYTHON-EXTENSIONS.md](documents/PYTHON-EXTENSIONS.md) for more detail.

### Macros
Nutshell's occasional concision, usually by compression of many similar Golly transitions into just a few, can also mean
that the user does not get as fine-grained a level of control over those transitions' ordering. Consider, for
example, [Brew](http://www.conwaylife.com/forums/viewtopic.php?f=11&t=3558): it and its higher-statecount
variants ostensibly have a three-line Nutshell representation, but this representation actually produces the following...

```
any.0, 1, 1, 1, _a0.0, _a0.1, _a0.2, _a0.3, _a0.4, 1
any.0, 2, 2, 2, _b0.0, _b0.1, _b0.2, _b0.3, _b0.4, 2
any.0, 3, 3, 3, _c0.0, _c0.1, _c0.2, _c0.3, _c0.4, 3

1, 1, 1, _a0.0, _a0.1, _a0.2, _a0.3, _a0.4, _a0.5, 1
2, 2, 2, _b0.0, _b0.1, _b0.2, _b0.3, _b0.4, _b0.5, 2
3, 3, 3, _c0.0, _c0.1, _c0.2, _c0.3, _c0.4, _c0.5, 3
```
...whereas the real Brew matches the following.
```
any.0, 1, 1, 1, _a0.0, _a0.1, _a0.2, _a0.3, _a0.4, 1
1, 1, 1, _a0.0, _a0.1, _a0.2, _a0.3, _a0.4, _a0.5, 1

any.0, 2, 2, 2, _b0.0, _b0.1, _b0.2, _b0.3, _b0.4, 2
2, 2, 2, _b0.0, _b0.1, _b0.2, _b0.3, _b0.4, _b0.5, 2

any.0, 3, 3, 3, _c0.0, _c0.1, _c0.2, _c0.3, _c0.4, 3
3, 3, 3, _c0.0, _c0.1, _c0.2, _c0.3, _c0.4, _c0.5, 3
```
Notice that these are the exact same transitions, only intertwined, and this crucial difference prevents the Nutshell version
from behaving as it should.

Nutshell 0.4.0 introduced *macros*, Python functions invoked from Nutshell that can modify spans of resultant transitions.
The `weave` macro that comes with Nutshell, for example, can be used in Brew.ruel as follows:

```rb
@NUTSHELL Brew
From 83bismuth38.

@TABLE
symmetries: permute
states: 4

weave: 1
any, [live] ~ 3, --[1]; [1]
live, [0] ~ 2, --[0]; [0]
weave: \

live, any; [0: (any-1) << 1]

@COLORS
000: 0
F00: 1
0F0: 2
00F: 3
```
It will operate here on the two lines flanked by `weave:` directives, ending when the macro is invoked with a backslash
(as if that is the end of a block; imagine curly braces from `weave: 1 {` to `weave: \ }`). Macros can also be passed additional
arguments: here, `weave: 1` passes the value `1` to the function behind the macro. (Multiple arguments, if necessary,
are separated by whitespace.)

At transpile-time, the `weave` macro is passed (a) a list of transitions that corresponds to the first codeblock above
(having out-of-order transitions), and (b) the value `1` from the `weave: 1` invocation. It then returns a new list
corresponding to the second codeblock above (with correctly-ordered transitions), and this is what is written to the
final output file.

Nested macros are applied innermost first, and all macros *must* have a `macro_name: \` end line or else they will not be run.
`weave` doesn't show it, but macros of course aren't limited to just reordering transitions&nbsp;-- they can also add or
remove them as needed.

The current "standard library" of macros currently consists of two:
- **weave**: With chunk_size = 1:  
      Given a group of Nutshell transitions `[a, b, c]` producing
      the Golly transitions `[a0, a1, a2, ..., b0, b1, b2, ..., c0, c1, c2, ...]`,
      reorder the Golly transitions as `[a0,b0,c0, a1,b1,c1, a2,b2,c2, ...]` --
      in other words, "weaving" groups of transitions together.  
    With chunk_size = 2, produces  
      `[a0,a1,b0,b1,c0,c1, a2,a3,b2,b3,c2,c3, ...]`  
    And so on for higher chunk_size values. Extraneous transitions (ones that
    don't divide evenly into chunk_size) are left at the end rather than discarded.  
    Note that `weave` will appropriately order transitions resulting from inline rulestrings,
    despite their being from the same line.
- **reorder**: For when *really* fine control is necessary.
    Takes a series of numbers corresponding to the Nutshell
    transitions covered by this macro, where 1 is the first
    transition and 2 the second and so on, and reorders the
    resultant Golly transitions according to their ordering.

    For instance, given a series of numbers `1 1 2 3 1 4 2`
    and operating over the sequence of Nutshell transitions  
      `[a, b, c, d, e]`  
    corresponding to the following set of Golly transitions  
      `[a0, a1, a2, a3, b0, b1, c0, c1, d0, d1, e0]`  
    The macro will return:  
      `[a0, a1, b0, c0, a2, d0, b1, a3, c1, d1, e0]`
    
    Notice how, after the last specified transition (b1), extras
    are tacked on to the end- in as close to their original
    order as possible.

    If an input ends with a bracketed sequence of numbers,
    that sequence is repeated ad infinitum. That is to say
    that `1 [2 3 4]` is interpreted as  `1 2 3 4 2 3 4...`.

See [documents/PYTHON-EXTENSIONS.md](documents/PYTHON-EXTENSIONS.md) for details regarding implementation of custom macros.

As with modifiers, a currently-indefinitely-postponed future release of Nutshell will remove `weave` from the standard library
(as its only application is in Brew) and instead allow ruletable-specific macros to be defined within their Nutshell file
itself. Additionally, a `prune` macro will be added that takes a pattern and removes individual output transitions that match
it.

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
1: Data
2: Signal over empty space {SIGNAL}
: {DATA_SIGNAL} Signal moving through data
3: {GUN} Gun, releases one signal every other tick
: {GUN_2} "Dormant" gun in between signals

@TABLE
...
```

Notice the following few things:
- There is no curly-bracketed {NAME} on the first line, but it does have a number + colon at the start.
- The second and fourth lines have both a number + colon at the start *and* a curly-bracketed {NAME}.
- The third and fifth lines have an initial colon and a bracketed {NAME}, but no number before the colon.

What they mean:
- There will be no named constant aliased to the cellstate "1", but that state will be 'reserved'. (Stay
  tuned for this term's definition.)
- The names SIGNAL and GUN will be usable in later segments as aliases for, respectively, cellstates
  2 and 3. The literal numbers 2 and 3 can also be used, and they'll refer to the same cellstates;
  they are also 'reserved'.
- The names DATA_SIGNAL and GUN_2 will be usable in later segments, but we don't intend to use their
  numerical cellstate values at all.  
  During transpilation, these names will be given cellstates in sequential order, starting from 1 and
  *skipping* any previously-'reserved' cellstates.

The above will transpile to this, also stripping the {NAME}s:

```rb
@RULE foo
1: Data
2: Signal over empty space
4: Signal moving through data
3: Gun, releases one signal every other tick
5: "Dormant" gun in between signals
```
...and all references to constants will be replaced with their appropriate cellstate value. **Note that
Nutshell does not stop you from using the cellstate of an "auto-numbered" constant**, so if you accidentally
or purposely refer to `4` and `5` in your `@TABLE` or elsewhere there won't be an error thrown -- make
sure you can keep track of your constants!

Also: it is *strongly* recommended that constant names start with an uppercase letter and variable names with
a lowercase one. The initial capital helps visually distinguish the former from the latter.

### The `@COLORS` segment
This segment allows multiple states with the same color to be defined on the same line as each other, and for a color to be
written either as a triplet of base-10 `R G B` values, like in Golly, or as a hexadecimal color code.
As a result of its allowing multiple colors, the "key/value" order, if you will, has been switched: the color now
goes first on a line, followed by all the states it's assigned to. A [range](#ranges) sans parentheses/curly brackets can
be used here as well.  

For instance: `FFF: 2 4 6 8 10` says to assign the color `#FFFFFF` to states 2, 4, 6, 8, and 10, and can also be written
as `FFF: 2+2..10` or `FFFFFF: 2+2..10` or `255 255 255: 2+2..10`.

The state listing can also contain `@NUTSHELL`-defined constant names -- which substitute for one cellstate each -- **or**
`@TABLE`-defined variable names, which cause the color to be applied to every state within the variable.

The color can additionally be expressed as a gradient rather than a single color. If this is done, the gradient will distribute
itself across all given cellstates rather than applying a single color to each. See the following example:

```rb
# Nutshell
@COLORS
FF0..00FFF0: 3, 4, 6
```
```rb
# Golly
@COLORS
3 255 255 0
4 170 255 80
5 85 255 160
```

### The `@ICONS` segment
This segment is based around Golly's RLE format instead of XPM data; the idea is that you're likely going to be in Golly anyway
when you're fiddling with a rule, so it'll be easier to quickly copy/paste an RLE in and out of a blank Golly tab than it'd be to
edit XPM images in your text editor. Non-normalized icons are automatically centered & uniformly resized to the nearest Golly icon
dimensions (7x7/15x15/31x31).

Each individual XRLE pattern listed represents one icon, and to assign this icon to some cellstate,
include the state or its `@NUTSHELL`-defined constant in a comment immediately above the icon's RLE pattern.
**`@ICONS` can additionally take here a varname defined in `@TABLE`**, in which case it will apply the icon
to every cellstate within that variable.
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

Multiple icon sizes can be indicated by repeating the `@ICONS` segment -- if you wish to do this, place your differently-sized icons
under `@ICONS:7`, `@ICONS:15`, and `@ICONS:31` respectively. Note that the numbers are not checked, so one could totally place 15x15
icons under `@ICONS:7` -- they're just there to distinguish the multiple segments before coalescing them into a single `@ICONS` in
the Golly table.
