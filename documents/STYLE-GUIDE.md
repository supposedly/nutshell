# Nutshell style guidelines

Please follow Golly/common-sense conventions except where an item below applies.

- Use spaces.
  - **Replace:**
    - `symmetries:rotate8`
    - `0,<2cek3ain/live/0>,1`
    - `0,1,any,any,any,[SE],[SE],5,any,4->N:3`
  - **With:**
    - `symmetries: rotate8`
    - `0, <2cek3ain / live / 0>, 1`
    - `0, 1, any, any, any, [SE], [SE], 5, any, 4 -> N:3`

  Ruletables and readers' eyes need to breathe.  Don't use spaces, however, where they'd cause a syntax error and/or
  make things less readable, such as immediately preceding a comma or touching the "mouth" of some sort of bracket.

- Use semicolons at the end of a transition.
  - **Replace:** `0, 1, any, any, any, [SE], [SE], 5, any, 4`
  - **With:** `0, 1, any, any, any, [SE], [SE], 5, any; 4`

- Compact transition terms wherever possible.
  - **Replace:** `0, 1, any, any, any, [SE], [SE], 5, any; 4`
  - **With:** `0, 1, NE..SE any, S..SW [SE], 5, any; 4`
  - **With:** `0, 1, NE..E any, SE..SW [any], 5, any; 4`

  This includes starting a transition with a non-north compass direction if it aids in compression.

- Be consistent with things that there's more than one way to do.
  - **Replace:** `(0, 1), {2, 3, 4}, 5; 6`
  - **With:** `(0, 1), (2, 3, 4), 5; 6`
  - **Or:** `{0, 1}, {2, 3, 4}, 5; 6`

  Also be consistent regarding the use of:
  - Golly-style decimal RGB versus hex-code RGB in `@COLORS` + `@ICONS`
  - Letters vs. numbers for icon-pixel colors in `@ICONS`

- Use separate naming conventions for multistate variables and single-state constants.
  - **Replace:**
    - `: {constant_name} some description` in `@NUTSHELL`
    - `variable_name = (1, 2, 3)` in `@TABLE`
  - **With:**
    - `: {ConstantName} some description`
    - `variable_name = (1, 2, 3)`
  - **Or:**
    - `: {CONSTANT_NAME} some description`
    - `variableName = (1, 2, 3)`
  - ...or anything reasonable.

  Names that conflict with one of Nutshell's ten reserved keywords&nbsp;-- `FG`, `BG`, and eight
  uppercased compass directions&nbsp;-- should be set off with some disambiguating symbol, such as
  `_NE` or `$NE`.
