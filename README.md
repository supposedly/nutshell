# rueltabel-format
 A compiler (transpiler?) from my new Golly ruletable syntax to the traditional format.
 
## The spec

- All variables unbound by default, because needing to define eight "any state" vars is ridiculous.
- Support for `{}` literals, usable directly in transitions. (Parentheses are also supported as variable-literal
containers, and are my preference).
- Support for cellstate *ranges* in variables, via double..dots (as in `(0..8)`) -- interspersible with state-by-state specification, so you can do like `(0, 1, 4..6, 9)` or whatever.
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
- To make binding even simpler, the cardinal directions `N NE E ... NW` are reserved names provided as symbolic constants for what the direction's index would be in a
traditional Golly table. For example, in a rule with `neighborhood: vonNeumann`, the names `N E S W` are provided
for `1 2 3 4`.
- This means that, above, the first 'new' transition can be rewritten as `foo,bar,bar,bar,bar,bar,bar,bar,bar,[E]`
(E meaning east, because the 3rd `bar` represented the eastern cell), and the second as `foo,bar,bar,bar,[N],bar,bar,bar,bar,baz`.
- The above repetition can be cut down on even more by specifying directions directly before each state, which then allows
*ranges* of directions (which of course simply map to their respective numbers). This means that the
transitions above can be further rewritten to:
```py
# current (barC repeats)
foo,barA,barB,barC,barD,barE,barF,barG,barH,barC
# new
foo, N..NW bar, [E]

# current (barA repeats)
foo,barA,barB,barC,barA,barD,barE,barF,barG,baz
# new
foo, N..E bar, [N], S..NW bar, baz # could also be "blah, SE [N], blah"
```
- With this, we can introduce "mapping" one variable to another: if `bar` is `{0,1,2}` & `baz` is `{1,3,4}`, then a `foo, N..NW bar, [E:baz]` (meaning *'map the eastern cell, being a `bar`, to `baz` -- so if it's 0 return 1, if 1 return 3, if 2 return 4'*) can
replace what would otherwise require a separate transition for each of `0...1`, `1...3`, and `2...4`.
- Mapping of course works with variable literals as well. `[3: (3,4,6)]` is valid above
- If a variable literal is too small to map to, an error will be raised that can be rectified by either  
(a) filling it out with explicit transitions, or (b) using the `...` keyword to say *"fill the rest out
with whatever value preceded the `...`"*.
- Treat live cells as objects: allow a cardinal direction to be specified within/after the last term of a transition.
```py
foo, N..NW bar, baz -> S:2 E[2, 3] SE[quux] N[NE: (2, 3)] NE[E]

# S:2 says "spawn a state-2 cell to my south"

# E[2, 3] and SE[quux] say "map this cell (E or SE) to this variable"
# Parentheses/braces aren't really needed for the variable literal in E[2, 3], but
# it *could* if necessary for some reason be written as E[{2,3}] or E[(2,3)].

# N[NE: (2, 3)] is a TENTATIVE syntax that, if implemented, would spawn a cell to the north
# that maps the *northeastern* state variable to the (2, 3) literal.
# NE[E] would, similarly, spawn a cell to the north that maps the eastern state variable
# to the northeastern cell's current state.
# Tentative because it's ... weird, and inconsistent because you can't do something like
# N[SE: (2, 3)] unless you were to exceed C
```
- Within these post-transition cardinal direction specifiers (PTCDs), the `_` variable says "leave as is".

# Unimplemented / Dropped
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
