# rueltabel
A reimagined Golly ruletable format, compiling to the traditional syntax. See [`examples/`](/examples) for examples.
 
## Spec
- All variables unbound by default, because needing to define eight "any state" vars is ridiculous.
- Support for `{}` literals, usable directly in transitions, as 'on-the-spot' variables. (Parentheses are also allowed. I personally prefer them to braces.)
- Support for cellstate *ranges* in variables, via double..dots as in `(0..8)` -- interspersible with state-by-state specification,
  so you can do `(0, 1, 4..6, 9)` to mean `(0, 1, 4, 5, 6, 9)`.
- Allow a variable to be made 'bound' by referring to its *index* in the transition, wrapped in [brackets]:  
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
- A Golly-ruletable transition such as von-Neumann `0,a,a,a,a,1` might be inefficiently compacted to `0, a, [N], [N], [N], 1`, or worse
  `0, a, E..W [N], 1`. In such cases, where successive variables need all to be bound to the first, the shorthand `direction..direction [var]` can be used.
  Here it would look like `0, N..W [a], 1`, expanding during compilation to `0, a, [1], [1], [1], 1`.
- With this indexing, we can introduce "mapping" one variable to another. For instance, `foo, N..NW (0,1,2), [E: (1,3,4)]`
(meaning *map the eastern cell, being any of `(0,1,2)`, to the states `(1,3,4)`: if it's 0 return 1, if 1 return 3, if 2 return 4*) can
replace what would otherwise require a separate transition for each of `0`...`1`, `1`...`3`, and `2`...`4`.  
  Mapping of course works with named variables as well.
- If a variable literal is too small to map to, an error will be raised that can be rectified by either (a) filling it out with explicit transitions,
or (b) using the `...` operator to say *"fill the rest out with whatever value preceded the `...`"*.
- If the "map-to" is instead *larger* than its "map-from", extraneous values will simply be ignored.
- Transitions under permutational symmetry can make use of a shorthand syntax, specifying only the quantity of cells in each state. For example, `0,2,2,2,1,1,1,0,0,1`
  in a Moore+permute table can be compacted to `0, 2:3, 1:3, 0:2, 1`.  
  Unmarked states will be filled in to match the number of cells in the transition's neighborhood, meaning
  that this transition can also be written as `0, 0:2, 1, 2, 1` or `0, 1:3, 2:3, 0, 1`.  
- If the number of cells to fill is not divisible by the number of unmarked states, precedence will
  be given to those that appear earlier; `2,1,0`, for instance, will also expand into `2,2,2,1,1,1,0,0`, but `0,1,2` will expand into `0,0,0,1,1,1,2,2`.
- Treat live cells as moving objects: allow a cardinal direction to travel in and resultant cell state to be specified post transition.
```py
foo, N..NW bar, baz -> S:2 E[2, 3] SE[wutz] N[NE: (2, 3)] NE[E]

# S:2 says "spawn a state-2 cell to my south"

# E[2, 3] and SE[wutz] say "map this cell (E or SE) to this variable"
# Parentheses/braces aren't really needed for the variable literal in E[2, 3], but
# it *could* if desired be written E[{2,3}] or E[(2,3)].

# N[NE: (2, 3)] is a TENTATIVE syntax that, if implemented, would spawn a cell to the north
# that maps the *northeastern* state variable to the (2, 3) literal.
# NE[E] would, similarly, spawn a cell to the north that maps the eastern state variable
# to the northeastern cell's current state.
# Tentative because it's ... weird, and inconsistent because you can't do something like
# N[SE: (2, 3)] unless you were to exceed the speed of light
```
- Within these "post-transition cardinal direction specifiers" (PTCDs), the `_` keyword says "leave the cell as is".

## Unimplemented / Dropped
- "Later transitions override earlier ones, bc the current switched system feels unintuitive"  
(It felt even more unintuitive doing it CSS-style)
- The original spec entry for PTCDs had a number of holes in it:

> - treat live cells as objects: allow a cardinal direction to be specified within/after the last term of a transition
> ```py
> foo,bar,bar,bar,bar,bar,bar,bar,bar,0 NW:2 NE[4] S[6:{2,6,9}]
> 
> # the final 0 says "I turn into a state-0 cell"
> 
> # NW:2 says "I then spawn a state-2 cell to the northwest"
> #      (colon optional but prettier than NW2)
> 
> # NE[4] says "Whatever was in the fourth 'bar' spawns to the northeast"
> 
> # S[6:{2,6,9}] says "The sixth 'bar', mapped to states {2,6,9}, spawns to the south"
> ```
> which would be equivalent to cutting this off at 0 then defining a `0...X` transition for the other directions

## To do
- Support switching symmetries partway through via the `symmetries:` directive. (When parsing, this will result in all transitions being expanded to the 'lowest'
symmetry type specified overall).
- Do something (???) to attempt to simplify permutationally-symmetric transitions such as in TripleLife.
