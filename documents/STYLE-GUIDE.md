# Nutshell style guide

There are five degrees of approval indicated in the examples below.
- **Yes**: This is always acceptable and furthermore is actually the best way to do this. Knock yourself out.
- **Sure**: If written after a **Yes**, isn't *always* preferable but it's still adequate;
  otherwise, means that this is just one of a few perfectly-acceptable ways to write this.
- **OK**: Neither good nor bad. If there are **Sure**s or **Yes**es listed, prefer them to this.
- **Perhaps not**: This isn't plain awful, but do try to avoid it if it makes things look worse.
- **No**: No.

Also, feel free not to follow anything in this document.
It's just here for reference, and perhaps eventually to establish consistency if Nutshell does manage to find a foothold.

## The guidelines

### General

- `@NUTSHELL` or `@RULE` can technically go anywhere, but they really should always be at the top of your file.
- Separate different segments with at least one newline -- maybe two.

### @NUTSHELL, @TABLE

- Give your rulefiles some breathing room! The usual Golly convention is to omit whitespace wherever possible,
  but this definitely hurts readability sometimes.
  - One space should be used after commas/semicolons in a variable or transition, and after the colon in a mapping.
    - **Yes**: `0, any, (3, 4), [E: (5, 6)]; 1`
    - **No**: `0,any,(3,4),[E:(5,6)];1`
  - No whitespace, however, should be used immediately adjacent to parenthesis/square bracket nor before a comma/(semi-)colon, though.
    (In some cases this also might not be parsed correctly)
    - **No**: `0 , any ,( 3 ,4 ) ,[ E :( 5 ,6 ) ] ;1`
    - **No**: `x = (1 , 2 ,3)`
  - Hash signs for comments should be preceded by one or two spaces and followed by one fewer.
    - **Yes**: `(...); 1  # Helpful comment`  (Some markdown renderers, strangely, coalesce multiple spaces into one inside an `inline codeblock`... be aware that there are two spaces before the # here)
    - **OK**: `(...); 1 #Helpful comment`
    - **No**: `(...); 1#Helpful comment`
  - The output-specifier arrow, `->`, should be surrounded by one or two spaces (same amount) on each side,
    and individual compass-direction specifiers after it should be separated by two spaces.
    - **Yes**: `(...); 1 -> S:3  N[aVariable]  SE[anotherVar]` (Same note as above about spaces being coalesced)
    - **No**: `(...); 1->S:3 N[aVariable] SE[anotherVar]`
  - "Operators" -- currently, `-` for "subtraction" and `*` for "multiplication" -- should be surrounded by one space if at the "top level"
    of a transition or var assignment, and preferably-but-not-mandatorily surrounded by the same if located within a variable literal.
    - **Yes**: `varA - varB, [0: (2, varC * 3)], (varD - varE) * 3; 1`
    - **Sure**: `varA - varB, [0: (2, varC*3)], (varD-varE) * 3; 1`
    - **Perhaps not**: `varA-varB, [0: (2, varC*3)], (varD-varE)*3; 1`
  - The double dots `..` signifying a range should be flanked by whitespace only if their two "operands" are long-ish constant names.
    - **Yes**: `(1..3)`
    - **Yes**: `(LONG_CONSTANT_NAME_1 .. LONG_CONSTANT_NAME_2)`
    - **Sure**: `(LONG_CONSTANT_NAME_1..LONG_CONSTANT_NAME_2)`
    - **Perhaps not**: `(1 .. 3)`
- Semicolons should be preferred as a separator preceding the final cellstate in a transition, and perhaps following the input state as well.
  - **Sure**: `0, 1, 2, 3; 4`
  - **Sure**: `0; 1, 2, 3; 4`
  - **OK**: `0, 1, 2, 3, 4`
  - **Perhaps not**: `0; 1, 2, 3, 4`
- Use the compass-direction cellstate prefix for clarity when a transition is complex or maybe when the cellstate in question
  is long. Consider omitting it otherwise, especially when the prefix clarifies nothing or can be inferred easily by the reader.
  - **Sure**: `0, N..S 1, W 2; 3`
  - **Sure**: `0, N (1, 2, 3), 2, E [N: (2, 3, 4)], 4, 1`
  - **Perhaps not**: `0, N 1, E 2, S 3, W 4, 1`
- For consistency's sake: constants, whether declared in the `@NUTSHELL` of a file or as single-cellstate "variable" assignments,
  should at the very least start with a capital letter (with the rest of the name in PascalCase) and furthermore should perhaps
  also be in full SCREAMING\_SNAKE\_CASE.  
  Normal variables should start with a lowercase letter and be either in camelCase or lowercase.
  - **Sure**:
  ```py
  @NUTSHELL
  1: A description of state 1 {CONSTANT_NAME}

   @TABLE
  # [directives omitted...]
  OTHER_CONSTANT_NAME = 2
  normalVarName = (1, 2, 3)
  ```
  - **Sure**:
  ```py
  @NUTSHELL
  1: A description of state 1 {ConstantName}
  
  @TABLE
  # [directives...]
  OtherConstantName = 2
  normalvarname = (1, 2, 3)
  ```
  - **No**:
  ```py
  @NUTSHELL
  1: A description of state 1 {constantName}

  @TABLE
  # [directives...]
  otherconstantname = 2
  VarName = (1, 2, 3)
  OTHER_VAR_NAME = (3, 4)
  ```
- There is no distinction, as far as either Nutshell or this document is concerned, between {} and () for variables. Just be consistent.
  - **Sure**:
  ```py
  a = {1, 2, 3}
  b = {1, 2, 3}

  a, [0: {1, 2}], 3, b, {1, 3}; 5
  ```
  - **Sure**:
  ```py
  a = (1, 2, 3)
  b = (1, 2, 3)

  a, [0: (1, 2)], 3, b, (1, 3); 5
  ```
  - **Sure**:
  ```py
  a = {1, 2, 3}

  # using different brackets for anonymous and "normal" vars is fine,
  # so long as there's consistency
  a, [0: (1, 2)], 3, b, (1, 3); 5
  ```
  - **No**:
  ```py
  a = (1, 2, 3)
  b = {1, 2, 3}

  a, [0: (1, 2)], 3, b, {1, 3}; 5
  ```
- Prefer the symbolic compass-direction constants (`N`, `NE`, `E`, ..., `NW`) over their raw numbers (`0`, ...). Within output specifiers, 
  in fact, the numbers cannot be used at all.

### @COLORS/@ICONS

- Avoid using ranges-with-step rather than specifying individual states unless there's a clear regularity or relationship in the states
  indicated by the range. (See [readme](../README) for "range with step")
- No preference in `@ICONS` between specifying RLE-state colors using `. A B C ...` vs. `0 1 2 3 ...`, but don't mix the two. Use two
  spaces after single-character symbols of the former variant and one space otherwise.
  - **Sure**:
  ```py
  @ICONS
  .  FFF
  A  5000AA
  B  00D0FF
  ```
  - **Sure**:
  ```py
  @ICONS
  0: FFF
  1: 5000AA
  2: 00D0FF
  ```
  - **No**:
  ```py
  @ICONS
  . FFF
  1: 5000AA
  B 00D0FF
  ```
- The same applies to specifying colors using `RRGGBB` (hex) vs. `RRR GGG BBB` (dec).