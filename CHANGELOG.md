# Changelog

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)'s.

## [0.4.3] - In progress
### Added
- `-V`/`--version` flag

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
