# Parser/compiler specification

Compilation will occur in five passes total.

## Pass 0

1. Raise an error if two differently-named variables have the same value. (This could change if I end up changing how variables are stored during compiling)
2. Enumerate all variables and store them in a `{(state1, state2, ...): Variable(name=str, reps=int)}` dictionary.  
   - Raise an error if:
     - A nonexistent variable is referred to.
     - A variable is duplicated. (There should be no reason to do this thanks to their unbindedness, correct?)
     - A variable other than `__all__` is declared with a name beginning with an underscore/period or containing a digit.
     - A variable is declared with the (reserved) name of a cardinal direction: any of `N`, `NE`, `E`, `SE`, `S`, `SW`, `W`, `NW`

   - The reason for the "no underscores" rule is that (1) the name `_` holds a special meaning in PTCDs -- see spec -- and (2) the parser will compile anonymous 'on-the-spot'
   literals into variables prefixed with an underscore so they can be told apart from 'normal' variables (should the need to reverse-compile
   ever arise).
   - The reason for "no digits" rule is that (1) the compiler will suffix unbound variable names with numbers to make them "unbound" in the Golly ruletable format, and
   (2) variables are unbound regardless so there should be less of a need to group similar variables by placing a number at their end.

   - The special variable `__all__` is where the user can define the states the PTCDs refer to when expanded. (By default, it is declared with every state in the rule.)

3. If under permutational symmetry, expand each statement (which might use the shorthand syntax) using `conv_permute()`.
4. Take note of the declared neighborhood (Moore, vonNeumann, hexagonal) and then replace any instances of cardinal directions with their appropriate number.
   Raise an error if an unsupported direction is used (e.g. `NW` in a von-Neumann neighborhood)

## Pass 1

1. Substitute out variable names in transitions with their literal value.
2. Generate random, underscore-prefixed names for anonymous variables (being literals and also `...`s in variable mappings).
3. Add these anonymous variables into the dict above.
4. Expand PTCDs into their own transitions.
5. Build a list of all transition statements, each element of which will be a tuple(str) containing the transition's original parts, from north to east/northwest.

The original file will not be referred to after step 5.

## Pass 2

1. Expand single-transition `[mappings: (to, variables)]` into separate transition statements, which are inserted into the above transition list.
2. Raise an error if a map-from is larger than its map-to, suggesting the user add a `...` to fill it out.

## Pass 3

Looking at variables in transitions:
1. Variables in transitions (of the transition list) are represented as `(literal values)` from step 1-1. Replace these literals again with their `name` from the dict.
2. After completing the above step for a single transition, cycle through it again and affix sequential numbers to repeated names (which stops them from becoming bound).
   If a variable appears more times in the transition than its `reps` value in the dict, increment its `reps`.
3. Now that variables are properly disambiguated, replace `[bound references]` with the now-bound name of the variable at the index they refer to.

(`reps` is used to keep track of how many times this variable should be defined in the compiled Golly ruletable)

## Pass 4

1. Write the appropriate header text and variable declarations into a Golly-compatible @TABLE-formatted file.
2. Write the now-converted transitions into the same file, perhaps with parseable #comments serving to help up-compile back into a rueltabel.
