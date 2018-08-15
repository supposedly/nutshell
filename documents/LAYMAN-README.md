## What the heck is a ruel? A rule? What?

So you've likely heard of Conway's Game of Life at some point or other, yes? In case that's a "no", google it and then let's define some terms real quick:

- Generation: One discrete step of time, during which a bunch of interactions can happen between different "cells"
- Cell: A discrete point on a regular grid
- Neighbor: Another cell within a given cell's "neighborhood"
- Neighborhood: The set of cells able to influence & interact with a given cell

Conway's Game of Life operates within a "range-1 Moore neighborhood", which simply describes the eight cells surrounding a given square on a regular
2D grid.

Life, then, is a *cellular automaton* where a cell "survives" to the next generation if it has either two or three living neighbors,
and where a "dead" (unoccupied) cell is "born" (becomes occupied) if it has precisely three live neighbors. There is a simple notation for this
type of CA devised long ago that just tells us the amount of neighbors a dead cell requires to be born and the amount of neighbors a live
cell requires to survive; for CGoL, as I'll call it from here on, this notation can express it as "B3/S23". Birth on 3, survival on 2 or 3.

Many other interesting "rules", cellular automata whose cells undergo a definable set of transitions, can be notated in this manner...
and, tragically, just as many can't. Some rules are nondeterministic and unpredictable, but even without going that far we can find rules that don't
necessarily rely on the total amount of neighbors (irrespective of their positions) but are interesting nonetheless, or rules that require
more than two states (OFF/dead and ON/alive) to function. So what do we do?

Well, occasionally, a concept or rule paradigm becomes popular enough that it gets its own concise notation and people start using it. Such is the
case with "Generations", a cellular-automaton algorithm that behaves like a normal B/S rule except that it requires each "died" cell to remain stationary
and interactionless for a set number of generations before truly dying; its notation flips the B/S conditions and adds a third "C" parameter, said
number of pre-death stationary generations, to the end. (Conway's Game of Life with nine extra death generations, for instance, would be notated as
23/3/10 -- survival on 2 or 3, birth on 3, and 10 pre-death states) There are also "non-totalistic rules" or specifically "isotropic non-totalistic rules",
where the term "non-totalistic" refers to the fact that they consider the *positions* of individual neighbors rather than merely the total quantity of
neighborhing cells; these are expressed with an alphabetic extension to the B/S notation, described [here](http://www.ibiblio.org/lifepatterns/neighbors2.html).

Still, even those aren't everything. What about all the other deterministic types of rules?  
Well, we can't account for *all* of them, but there has been some very very nice work put into settling for a large majority. Some smart folks
have gotten together (as they do) and created a cellular-automata explorer named [Golly](https://golly.sourceforge.net), now the de-facto tool
for exploring many types of CA; more importantly, they've also given it a whole domain-specific language for describing different kinds of
non-standard CA rules, ones that can't be expressed via the sort of concise notations seen above.

## Ruletables

```py
@RULE Life
Conway’s Game of Life.
@TABLE
n_states:2
neighborhood:Moore
symmetries:permute

var anyA={0, 1}
var anyB=anyA
var anyC=anyA
var anyD=anyA
var anyE=anyA
var anyF=anyA
var anyG=anyA
var anyH=anyA
var anyI=anyA

# Survival on 2 neighbors
1,1,1,0,0,0,0,0,0,1
# Birth, survival on 3 neighbors
anyA,1,1,1,0,0,0,0,0,1
# Death in all other cases
anyA,anyB,anyC,anyD,anyE,anyF,anyG,anyH,anyI,0
```

So what's this?! Well, as we can see from that description at the top, this is Conway's Game of Life, B3/S23, expressed as a rule-table. We can also see that
there are "segments" to the file denoted by @ and then a label; we'll call these @ lines "headers". The only thing that matters in the `@RULE` segment
is the first word after the header (whether it be on the same line or the next) -- this is the rule's *name*, used to refer to it from within Golly, but
anything after it in this segment is ignored (which makes it handy for comments or explanations!).

Next, the `@TABLE` segment. It starts off with three sorts of directives: first, the number of cell states in our rule (2, which are the OFF/"dead" state and the ON/"living" state),
then the neighborhood (Moore, a.k.a. all eight cells surrounding a given one), and finally symmetries, going into which isn't too important but suffice it to say that
they specify what "implicit" transitions can be inferred from the ones declared explicitly below.

After these directives come variable declarations; a variable is a container for more than one cell state, but that'll make more sense as soon as
transitions, the long comma-delimited segments at the very bottom, are explained.

Transitions are declared in the form `center cell, northern cell, northeastern cell, eastern cell, ..., northwestern cell, new center cell`,
or less-verbosely ``C, N, NE, E, SE, S, SW, W, NW, C` ``. For example, the second transition -- `1,1,1,0,0,0,0,0,0,1` -- says that the center cell in this
configuration...

```
. o o
. o .
. . .
```

...where `o` represents a live cell ('1') and `.` a dead cell ('0'), will survive to the next generation (i.e. remain a '1' cell). But! Since we specified
`symmetries: permute` in the directives up top, what this actually does is apply the specified transition to *all permutations* of a neighborhood containing two '1' cells
and six '0' cells... so, in effect, this fulfills the `S2` part of CGoL's `B3/S23` by saying that any live cell with two neighbors surrounding it in any configuration will
survive.

Survival is actually the default behavior in a ruletable, but specifying it explicitly serves to override the very next line,
`anyA,anyB,anyC,anyD,anyE,anyF,anyG,anyH,anyI,0`. The `anyX` variables contain states 0 and 1 both, so this line effectively says that *any* cell
with *any* configuration of live/dead neighbors will die (become state `0`) -- **unless** its specific configuration was already covered in an earlier transition.

So that was transitions and variables in a... nutshell. But why does the same variable need to be reassigned so many times in a row, as in `anyA`/`anyB`/`anyC`/.../`anyI`?
That'd be because the format's designers chose to make variables "bound", or more-specifically "name-bound": once a variable name appears once in a transition, it can only
refer to the same value from then on, much like how back-referring to a regex group matches the exact same text rather than reapplying the group's pattern. So if the
rule-writer desires that a single variable appear multiple times in a transition *while* retaining its "variability", they must assign its value to multiple distinct
names, using a different name for each separate desired occurrence.
More info can be found [here](GollyGang/ruletablerepository/wiki/TheFormat) and [here](http://golly.sourceforge.net/Help/formats.html#table).

This format is powerful, clearly, and works well enough for many cases. But it's rather primitive alongside its being powerful, and while this generally can be tolerated
or worked around, there are times when it gets *tedious* to keep track of the repetition it imposes -- as well as times when certain abstractions would be quite handy,
I've found.

Enter this project.

## Nutshell

I won't go as far in depth as I did above, because this repo's README explains the major additions in good detail -- but, for comparison, here's the same
CGoL rule as above as a "nutshell" file:

```py
@NUTSHELL Life
@TABLE
states: 2
symmetries: permute
neighborhood: Moore

# Survival on 2 neighbors
1, 1 * 2, 0; 1
# Birth, survival on 3 neighbors
any, 1 * 3, 0; 1
# Death in all other cases
any, any, 0
```

Or even this, if you want to go hard:

```py
@NUTSHELL Life
@TABLE
states: 2
symmetries: permute
neighborhood: Moore

# Birth, survival on 3 neighbors
# and survival on 2
any, 1 * 2, [0: (0, 1)], 0 * 5; 1
# Death in all other cases
any, any, 0
```

A bit easier on the eyes! Note in particular the compression achieved by allowing a single variable name to be used multiple times in a transition (with a different
syntax for "binding" to a previous value), and other things like the `*` shorthand for permutate-symmetry transitions and a "mapping" syntax to complement the new way
of binding.  
That may sound a bit abstruse, but this repo's main README.md does again contain an in-depth explanation of the additions and their uses -- which will hopefully be
more-understandable or at least -accessible after reading this intro.
