# ruletable-format
A compiler (transpiler?) from my new-and-improved Golly ruletable syntax to the traditional format.

## The original spec:

OK here's what's been going round my head w/r/t new ruletable syntax


- later transitions override earlier ones, bc the current switched system feels unintuitive

- support for cellstate *ranges* in variables, via hyphen or double..dots (`{0-8}` or `{0..8}`) -- interspersible with state-by-state specification, so you can do like `{0,1,4-6,9}` or whatever

- all variables unbound by default, because needing to define eight "any state" vars is ridiculous

- support for `{}` literals, usable directly in transitions

- allow a variable to be made 'bound' by referring to its *index* in the transition, wrapped in [brackets]:  
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
Transitions are zero-indexed from the input state.

- with this we can introduce "mapping" one variable to another: if `bar` is `{0,1,2}` & `baz` is `{1,3,4}`, then a `foo,bar,bar,bar,bar,bar,bar,bar,bar,[3:baz]` can replace what would otherwise require a separate transition for each of `0...1`, `1...3`, and `2...4`.

- mapping ofc works with variable literals as well. `[3:{3,4,6}]` is valid above

- treat live cells as objects: allow a cardinal direction to be specified within/after the last term of a transition
```py
foo,bar,bar,bar,bar,bar,bar,bar,bar,0 NW:2 NE[4] S[6:{2,6,9}]

# the final 0 says "I turn into a state-0 cell"

# NW:2 says "I then spawn a state-2 cell to the northwest"
#      (colon optional but prettier than NW2)

# NE[4] says "Whatever was in the fourth 'bar' spawns to the northeast"

# S[6:{2,6,9}] says "The sixth 'bar', mapped to states {2,6,9}, spawns to the south"
```
which would be equivalent to cutting this off at 0 then defining a `0...X` transition for the other directions
