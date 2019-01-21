# Changelog

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)'s.

## [0.6.0] - In progress?
### Planned
- A complete overhaul of symmetries and neighborhoods such that:
  - Such transformations as reflection and rotation are handled from the *neighborhood* rather than the symmetry type
  - Nutshell, given the compass directions composing a neighborhood, automatically determines what standard transformations
    it can undergo
  - Symmetry types simply have to call, for instance, neighborhood.rotate4() -- rather than themselves reordering the napkin
  - Symmetry types can be composed from within Nutshell without my having to define a new Python class for each basic combination
    of symmetries
  - Also, apgsearch-like symmetry notation...?
- Neighborhood-switching, a la symmetry-switching
- A `prune` macro
- More modifiers, e.g. Langton's Ant and Deficient/genext -- also hex (although hex symmetries are scary)

## [0.5.6] 2019-01-20
### Fixed
- The previous version's sole change had an unintended side effect: before it, with mixed r4r and permute transitions being
  default, B08 and S08 were treated as permute transitions and only processed as such. With the removal of permute, however,
  these were being ignored by the r4r-transition generator (because of their not having letters). Fixed by having it address
  0 and 8 explicitly.

## [0.5.5] - 2018-12-24
### Changed
- Permute in inline rulestrings was transpiling wrong, and it was annoying to have to `force-r4r` with Brew, so that's out --
  r4r is now the default
### Fixed
- Bug having to do with the above

## [0.5.4] - 2018-12-21
### Changed
- The output of `!expression` in `@TABLE` now includes the original expression alongside its result.
### Fixed
- Unrecognized symmetries now raise a Nutshell error rather than an uglier Python one.
- Import-time esrrors in Python extension files, eg macros and symmetries, now do the same.
- `TableSegment.__iter__()` no longer gives extraneous empty final lines when there are no variables/transitions.
  (This had been half-implemented prior, but it failed to consider the case where there *are* variables defined,
  just not used in the final Golly table)
- Gradients in `@COLORS` now include the end color (I'd forgotten that I'd made my `ColorRange` class exclusive thereof)

## [0.5.3] - 2018-12-20
### Changed
- `@ICONS` now obeys the "preserve comments" flag.
### Fixed
- Unrecognized segments are now once again transpiled as is, not with a single character on each line.
  (Bug introduced in v0.5.0)
- `@ICONS` no longer substitutes cellstates for constants' names that occur *before* a final pre-RLE comment.

## [0.5.2] - 2018-12-19
### Changed
- Made `TableSegment.comments` store its values as strings rather than as Lark's Token objects
- Made an error message having to do with `[inline binding]` clearer
### Fixed
- Text at the top of a Nutshell not tied to a particular segment is now silently ignored (tentative behavior) and no longer
  raises a Python exception
- In light of v0.5.1's changes, `@TABLE`'s wrapper class now no longer mutates itself (popping keys/values from an internal
  dict) when iterated over, meaning that can now be done more than once

## [0.5.1] - 2018-12-19
Making Nutshell a bit friendlier to use as a Python module rather than a CLI tool.
### Changed
- No more special-casing of `@TABLE` -- it now follows the `__iter__()` API that all the other segments use.  
  Externally this means that `@TABLE` may not end up at the top of a transpiled rulefile anymore. No biggie, though.
- Some error names: `ValueErr` to `Error` and `ReferenceErr` to `UndefinedErr`. This is the only outwardly-visible change.
- Names of segment-wrapping classes, so that they all follow the format "SomethingSegment".
- No change in CLI output, but SystemExit subclasses are no longer raised internally: they now are Exception subclasses,
  only turning into SystemExits if allowed to bubble up to the command line.
### Fixed
- The `dep` kwarg of segment-wrapping classes' `__init__()`s is now given a proper default (tuple of `None`s, not just one `None`)
  to avoid TypeError-None-is-not-iterable errors on external instantiation.

## [0.5.0] - 2018-12-17
General upgrades. The biggest changes were to `@ICONS` and `@COLORS`' handling of... everything, but
other updates happened too.
### Added
- Inline rulestrings now accept modifiers (which are extensible in the same way as symmetries).
- Automatic filling-in of omitted terms with `any`&nbsp;-- only, however, if every given term was accompanied by a compass-direction
  tag (to make sure that the omissions were intentional)
- An "explicit permute" symmetry in the stdlib w/ no automatic expansion (omitted tilde = `~ 1` and that's it)
- Allow bindings directly to compass directions rather than FG/BG with inline rulestrings, which kindasorta addresses the issue of
  Hensel r4r neighborhoods' positions mattering (more than just "FG" and "BG" can provide), but it's really more of a bad band-aid
- Support for Golly's multiple icon sizes by allowing segments with "modifiers" a la `@ICONS:7` and `@ICONS:15` -- these modifiers
  have no intrinsic meaning, so you could totally put 15x15 icons under `@ICONS:7` and vice versa, but their purpose is to all
  coalesce into the Golly table's `@ICONS` once transpiled
- The `@ICONS` and `@COLORS` segments can now use `@TABLE`-defined varnames to help specify their cellstates
- The `@COLORS` segment can now take a gradient (rather than a single color) which distributes itself over all given cellstates
### Changed
- `symmetries: nutshell.AlternatingPermute` now no longer attempts to infer amounts of terms, because that was *really* messy.
  It now behaves like `symmetries: nutshell.ExplicitPermute`
- The `@ICONS` segment now copies RLE comments over, except for the final comment before an RLE (because that one should be reserved
  for state definitions)
- Brew.ruel is now extensible to 2-state isotropic rules!!
### Fixed
- `symmetries: permute` now raises an error when given too many terms rather than simply telling some values to show up 0 times
- Undefined variables in the initial/resultant terms of a transition no longer cause an ugly Python error (was passing just a
  line-number `int` into an error-handling function that instead expected the object from which the line number came)
- The `@ICONS` segment no longer alters a recieved icon (by removing state-0 empty space) before centering it; it now
  assumes the icon it gets, including its RLE dimensions and empty space, is what should be centered
- The `@ICONS` segment, while being parsed, can no longer raise "invalid cellstate" errors on numbers it encounters
  in comments that *don't* immediately precede an RLE (because the comment immediately preceding an RLE is the only
  one that should contain cellstates)
- `consolidate_extra()`, plus the "extra" meta-information attribute to transition-y, objects in order to address
  `consolidate()`'s line-number problem with inline-rulestring transitions. Changed the `weave` macro to use this new
  function, ensuring it handles IRSes correctly.
- Permute transitions no longer expand into an arbitrary ordering when there are multiple symmetries in the same table --
  they instead follow the original ordering and are sorted.

## [0.4.10] - 2018-11-25
Really just floundering now while I figure out 0.5.0.
### Fixed
- The previous fix didn't account for something important, which caused a lot of fatal and erroneous errors. Should have
  run test.py before pushing!
### Changed
- Released a couple updates to ergo that finally streamline the whole "CLI-centric project" idea: console-invocation
  default values can now be distinguished from imported-as-module default values. For Nutshell, this means that the script
  no longer prints "Parsing...", "Compiling...", and "Complete!" if it's been imported as a Python module, but it does
  show those messages when it's invoked as a command-line script.

## [0.4.9] - 2018-11-24
### Changed
- Using a variable in the resultant term of a transition now causes an error on Nutshell's end rather than Golly's.

## [0.4.8] - 2018-11-28
### Added
- `__main__.py` to allow Nutshell to be run as `python -m nutshell ...`.
### Fixed
- The shebang in `to_ruletable.py` requested `python3.6` rather than just `python3`, causing
  it to show `Requested Python version (3.6) is not installed` when run with 3.7+; changed
  to `python3`.

## [0.4.7] - 2018-11-23
### Added
- A generic `Error` NutshellException type
### Fixed
- References no longer affect the value of `states:?` (e.g. `[8]` no longer sets `n_states` to 8), which
  should not have been happening in the first place but an oversight + odd Lark behavior made it so.
- A formal error is now raised when n_states < 2 (as opposed to the prior behavior of letting it crash).
- `@NUTSHELL` can now handle non-word characters at the start/end of constant names.
### Changed
- Exceptions from tilde-notation-handling functions are now caught and formatted prettily.
- Style guide has been heavily updated to focus only on what's necessary.
- In anticipation of v0.5.0, inline-rulestring transitions are now only restricted to Hensel
  rulestrings during postprocessing rather than lexing/parsing.

## [0.4.6] - 2018-11-19
### Fixed
- Operations can now be referenced without a bad error
- The `weave` macro was discarding some leftovers rather than leaving them at the end as documented
- Hopefully the last of the `states: ?` issue. Nutshell was presetting it based on the highest
  cellstate referred to in `@NUTSHELL`'s constant-state definitions, but this needs a +1.

## [0.4.5] - 2018-11-17
### Changed
- Formatting of comments/source when using `-c` and/or `-s`.
- The `reorder` macro now supports repetition of a sequence of line numbers.
### Fixed
- Inline-rulestring transitions now properly recurse when handling foreground/background references,
  which means you can include a reference in an operation or statelist or anything and it will be
  expanded appropriately.

## [0.4.4] - 2018-11-17
### Changed
- Directives are now included in `-c` (`--preserve-comments`)
- Directives can now handle line's-end comments; as a result, directives and macros can no longer
  take values containing the `#` character
### Fixed
- A niche bug: permute-symmetry transitions resulting in an internal representation containing
  multiple hash-equivalent objects (e.g. transitions that referred to a named variable more than once,
  resulting in the same StateList object's being used) would have their terms reordered, because values for
  tilde-notation expansion were kept in a `dict` subclass. A dict cannot have duplicate keys, so a transition
  like `..., varname, ..., varname, ...` would have been storing `{varname: 2}` rather than
  `{varname: 1, ..., varname: 1}`, and would thus have transpiled to `..., varname, varname, ..., ...`;
  this did not bode well for positional references.

## [0.4.3] - 2018-11-12
### Added
- `-V`/`--version` flag
- `\`, `/`, and `X` diagonally-reflectional symmetries

## [0.4.2] - 2018-11-07
### Added
- `reorder` macro
- ExtendedX.ruel to examples/
### Fixed
- Inline bindings in inline-rulestring transitions under permute symmetry
  were raising a dumb error related to using numbers for bindings instead
  of compass directions

## [0.4.1] - 2018-11-05
### Added
- Documentation of macros (and also of `special()` on symmetry types).
- "Special parameters" for macro functions.
### Changed
- Docs for Python extensions no longer share the main README with strictly-Nutshell stuff; instead, they're in their own
  [examples/PYTHON-EXTENSIONS.md](examples/PYTHON-EXTENSIONS.md) file.
- Expose `FinalTransition` via `nutshell.macro` (rather than keeping it all the way down the import-path road) for macros.
- FinalTransition.ctx is no longer expected to be a three-number tuple; it can just be `(lno, None, None)` if need be.

## [0.4.0] - 2018-11-04
Macros!
### Added
- Support for Python-defined "macros", operating on spans of resultant transitions.
### Changed
- `Brew.ruel` in `examples/` now demonstrates macros.

## [0.3.2] - 2018-11-04
### Added
- Version number now appears in the output file's "COMPILED FROM NUTSHELL" header.

## [0.3.1] - 2018-11-03
### Fixed
- A single instance of `raise SyntaxError` where `raise SyntaxErr` was intended. (`SyntaxError` is an inbuilt
  Python-language exception; `SyntaxErr` is Nutshell's)
- An oversight that caused references contained within statelists not to be properly expanded within
  inline-rulestring transitions.

## [0.3.0] - 2018-11-03
Primarily focused on the functionality of inline-rulestring transitions.
### Added
- Transitions now allow forward references, meaning the initial term of a transition can refer or contain
  a reference to a later one. (For instance, this means you can have `(0, [N]), (1, 2, 3), ...`)
- Inline-rulestring transitions now allow references in all terms, not just the resultant. Part of this
  is a consequence of the above, but allowing mappings/bindings in the foreground/background states is
  new.
- Inline-rulestring transitions now also allow inline bindings (an admittedly-confusing intersection of
  two unrelated uses of "inline"), meaning that the foreground/background can all be forced to stay the same state.
- `FG` and `BG` are now reserved words, bringing the total up to 10 (where it will stay).
- XHistory.ruel in the examples/ subdirectory, showcasing 'inline rulestrings'.
- This changelog.
### Changed
- Inline-rulestring transitions are now ordered as `<rulestring / foreground / background>` rather than placing
  the background first; new ordering feels a lot more intuitive.
- "Inline-rulestring references" are no longer differentiated from "normal references" on a syntactical level
  (that is, they are now lumped together in the grammar), which means that (a) mistaken reference symbols will
  be caught at 'transform-time' rather than parse-time, and (b) that the grammar now contains three rather than
  four duplications of what's almost the same set of rules.
- Nutshell's version number will be updated according to Semantic Versioning for every significant commit from now on.
### Fixed
- A noteworthy bug had been present in multiply-symmetric tables: transitions with at least two distinct instances
  of the same variable, each being bound to at least once, would coalesce them into one Golly varname. (e.g.
  vonNeumann `any, [N], any, [S]` would become `any.0, any.0, any.0, any.0` rather than `any.0, any.0, any.1, any.1`)
- The README had had an erroneous explanation of inline-rulestring-transition syntax (as if assuming foreground first,
  even though, until this commit, they had been ordered background-first).
