# Nutshell style guidelines

Please follow Golly / common-sense conventions except where something below applies.

- Use spaces.
  - **Replace:** `symmetries:rotate8`, `0,<2cek3ain/live/0>,1`, `0,1,any,any,any,[SE],[SE],5,any,4->N:3`
  - **With:** `symmetries: rotate8`, `0, <2cek3ain / live / 0>, 1`, `0, 1, any, any, any, [SE], [SE], 5, any, 4 -> N:3`
  Seriously -- ruletables and readers' eyes need to breathe.  Don't use spaces where they'd cause a syntax error and/or
  make things less readable, such as immediately preceding a comma or within the "mouth" of some sort of bracket.
- Use semicolons at the end of a transition.
  - **Replace:** `0, 1, any, any, any, [SE], [SE], 5, any, 4`
  - **With:** `0, 1, any, any, any, [SE], [SE], 5, any; 4`
- Compact transition terms wherever possible.
  - **Replace:** `0, 1, any, any, any, [SE], [SE], 5, any; 4`
  - **With:** `0, 1, NE..SE any, S..SW [SE], 5, any; 4`
  - **With:** `0, 1, NE..E any, SE..SW [any], 5, any; 4`
  This includes starting a transition with a non-north compass direction if it aids in compression.
- Be consistent with things there's more than one way to do.
  - **Replace:** `(0, 1), {2, 3, 4}, 5; 6`
  - **With:** `(0, 1), (2, 3, 4), 5; 6`
  - **Or:** `{0, 1}, {2, 3, 4}, 5; 6`
  Also be consistent regarding the use of Golly-style decimal RGB versus hex-code RGB in `@COLORS`+`@ICONS`,
  and regarding the use of letters vs. numbers for icon-pixel colors in `@ICONS`.