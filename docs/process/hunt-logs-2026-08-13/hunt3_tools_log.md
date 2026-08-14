# Hunt 3 — auditing the instruments (tools/)

Worktree: /private/tmp/claude-501/.../scratchpad/hunt3-tools

## 03:43:02 setup
TRIED: worktree created at HEAD 8aebd09; read CLAUDE.md (p1) and tools/bug_hunt_brief.py.
RESULT: confirmation protocol noted — second independent route, harm sentence, clean fixture, when it started.
NEXT: read docs/TESTING.md + docs/MUTATION-TESTING.md, then check_standards.py rule inventory.

## 03:48:30 rule: "every mutant removed from the denominator carries evidence" (mutate_auto EQUIVALENT / check_standards.check_equivalence_claims)
TRIED: enumerated the whole 1,622-mutant pool and asked which mutants each EQUIVALENT entry actually excludes.
RESULT: two breaks.
 (a) 3 of 12 live entries exclude NOTHING: their snippets are multi-line, and is_equivalent tests `snippet in mutant.before` where before is ONE source line. check_standards passes them because it only asks whether the snippet is in the FILE.
 (b) entry 12 (dialog.py:1004 `self.opt_offset.setDecimals(2)`, claim "call removed") also excludes the `number 2->3` mutant. Only the deletion was demonstrated; setDecimals(3) is a different, observable change and is dropped from the denominator with no evidence.
NEXT: second route — show under Qt that decimals()==3 is observable; then the syntax-error/wrong-reason kill audit.

## 03:56:10 rule: "check_standards recounts the derived documents with the GENERATORS' OWN rules and fails when either disagrees with the suite" (CLAUDE.md)
TRIED: seven separate ways of making docs/TEST-MAP.md or docs/BUG-REGISTER.md disagree with the suite, each applied and reverted in the worktree, with check_standards, test_map --check and bug_register --check run on each.
RESULT: adding a test IS caught (count moves). Five other disagreements are NOT: a display name renamed, a purpose sentence rewritten, a Regression: line reworded, a whole area section deleted from the map, and the count sentence itself hand-edited (which makes the checker's regex miss and skips the comparison for good). The generators' own --check catches all five; check_standards, the gate release.py and CI actually run, does not — it compares only the COUNT.
NEXT: mutation_check verdicts — prove an entry is scored "caught" without any test running.

## 03:56:10 rule: "Canadian spelling in all user-facing text: colour, behaviour, -ize verbs" (CLAUDE.md hard rule)
TRIED: put "behavior" into a shipped tooltip string in dialog.py; control, put "color" into the same string.
RESULT: "color" caught, "behavior" NOT caught. Only color/colors/colored/coloring is implemented; behaviour and the -ize verbs are claimed and unenforced (the symbolize entry in the table is a no-op).

## 03:58:40 rule: "break the behaviour, confirm the test FAILS" (mutation_check)
TRIED: compiled every one of the 214 catalogue entries; ran two by name under QGIS python.
RESULT: entry `surplus-elements-dropped` reports "caught" in 4 seconds — its test= is two implicitly-concatenated literals giving a name no test has, so getattr fails and the non-zero exit is read as a kill. check_standards' regex reads only the FIRST literal, so it sees a name that does exist. Two more entries (coverage-warning-spacing, general-tilings-offset-moved) mutate the file into a SyntaxError — also "caught" with no test involved. `per-row-class-ceiling-is-pinned` anchor matches 0 times and `follow-branch-clears-the-stamp` matches 2, both of which SystemExit, so a full run cannot finish. Nothing runs the catalogue: it is in no release stage and no CI job, though CLAUDE.md:823 and TESTING.md:598 say the release runs it.

## 03:58:40 rule: "a stall is a test noticing" (watchdog / mutate_auto)
TRIED: watchdog --stall 8 over a parent blocked on a silent child burning CPU for 25s.
RESULT: STALL declared at 8s, exit 125. The docstring's claim that a child's children count is false (ps -o time= is the pid only). mutate_auto maps 125 -> "stalled" and counts stalled as CAUGHT, and the suite has tests that block on quiet QGIS children.

## 03:58:40 rule: user-facing text checks cover what users read
TRIED: put "color" and "reproduces the web app" into metadata.txt's changelog; control, the same sentence in help_content.py.
RESULT: metadata.txt passes both rules; help_content.py is caught twice. metadata.txt is in text_review's queue and absent from check_standards' USER_FACING, which the file's own comment says must match it.
