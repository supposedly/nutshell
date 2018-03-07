# Parser specification

First, enumerate all variables and store them in a `{(state1, state2, ...): ['name']}` dictionary.  
Raise an error if a variable starts with an `\_underscore` or is nonexistent but referred to.  
Variables will be stored as a `Variable(name=str, reps=int)` object.

A 'special' variable `_all_` will also be accepted, and is exempt to the 'no initial underscores' rule; it is where the user can define the states they consider important
to the post-transition cardinal direction specifiers.

If under permutational symmetry, expand each statement (which might use the shorthand syntax) using conv_permute().

Next, the first pass of the parser will be dedicated to:

1. Substituting out variable names with their {value}.
2. Expanding post-transition cardinal direction specifiers into their own transitions.
3. Generating new names (prefixed with an `\_underscore`) for 'raw' variables, ones defined on-the-spot using the `{literal}` syntax and not given a name.
4. Building an ordered list of transition statements, each of which will be its own split list.

The second pass of the parser will be dedicated to:

1. Expanding single-transition `[mappings: {to, variables}]` into separate transition statements, which are inserted into the above list.
2. Raising errors if a map-from is larger than its map-to.

The third pass will be dedicated to:

1. Affixing numbers to formerly-unbound single variable names in order to replicate this unbound behavior when compiling to traditional Golly format.
2. Incrementing the `reps` value of each variable in the aforementioned dict.

The fourth pass will be dedicated to:

1. Replacing `[binding references]`, now that variables are properly disambiguated by pass 3, with the variable they refer to.

The fifth and final pass will be dedicated to:

1. Writing the appropriate variable declarations and header text into a Golly-compatible @TABLE-formatted file.
2. Writing each transition into the same file.
