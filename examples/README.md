# Examples

`nutshells/` contains example nutshell files, and `compiled_ruletables/` contains their transpiled Golly-ruletable output;
filenames are shared between the two directories, so e.g. [nutshells/bct.ruel](nutshells/bct.ruel) transpiles to the file
under [examples/bct.rule](examples/bct.rule).  
Transpilation is done with the `-s` and `-c` options, so the files in the latter directory have comments preceding each group of
`@TABLE` lines showing what Nutshell line (and specific snippet thereof) it came from as well as preserving the original Nutshell
file's comments where applicable.

Notable examples:
- [Brainfuck](nutshells/bf.ruel); for more info, see [here](https://gist.github.com/eltrhn/f2b4e931418cf8369efefca0fd233a0f).
  This is a full implementation of Brainfuck as a cellular automaton, and it is in fact the rule that motivated Nutshell's
  existence in the first place.
- [BCT](nutshells/bct.ruel), short for [Bitwise Cyclic Tag](https://esolangs.org/wiki/Bitwise_Cyclic_Tag). Initially implemented
  as [a normal Golly ruletable](https://gist.github.com/eltrhn/80cb82bc8fb139317b166baef9256efc), but it lends itself well
  (while being much less complex than Brainfuck) to representation in this manner too.
- [BML](nutshells/bml.ruel), or
  "[Biham–Middleton–Levine traffic model](https://en.wikipedia.org/wiki/Biham%E2%80%93Middleton%E2%80%93Levine_traffic_model)";
  the very first Nutshell file ever written, transpiled initially [by hand](https://gist.github.com/eltrhn/1db740cf85b614156904b3d63826a15e)
  (to prove whether the ideas worked on a general level) then later used as a sanity check for various iterations of the
  transpiler. Note the `@RUEL` and `@TABEL` segment headers in that Gist; Nutshell was named 'rueltabel' in its early stages.
- [XHistory](nutshells/XHistory.ruel), a demo of inline-rulestring transitions and also a template that can produce a History ruletable
  for *any* rule expressible via Hensel rulestring.
- [Brew](nutshells/Brew.ruel), notable for that it compresses+generalizes
  [the original](http://www.conwaylife.com/forums/viewtopic.php?f=11&t=3558)&nbsp;-- might in this regard be the best example of
  Nutshell's strengths. Extensible to any count of states by changing the value of the `staes:` directive, and demos the use of
  macros as well (with `weave1`).
