# Archive: PUBLISHING.md

The full accounts cut out of `PUBLISHING.md` by the archiving pass
(docs/DOC-ARCHIVING.md). Nothing here is a rule you must read
before working: `PUBLISHING.md` carries every rule and the headline
of every lesson. This file carries the episode each one came
out of -- what was measured, what was tried first, what the
superseded form of a rule was.

READ IT WHEN `PUBLISHING.md` points you here by id (P-1,
P-2, ...), when a rule surprises you and you want to
know what it cost, or when you are about to change a rule and
need to know what it was built to prevent. Ids are stable:
quote them, do not renumber them.

## Index

- **P-1** — Before the branch exists: is Linux still running what we run?  <sub>Publishing: the accounts behind the procedure</sub>
- **P-2** — What the first three CI rounds cost, so the next one is cheaper  <sub>Publishing: the accounts behind the procedure</sub>
- **P-3** — What a release stopped doing, and why that is not a weakening  <sub>Publishing: the accounts behind the procedure</sub>
- **P-4** — A TEST REPAIR SPENDS A CANDIDATE NUMBER, AND THAT IS NOT A WASTE  <sub>Publishing: the accounts behind the procedure</sub>
- **P-5** — Release bodies wrap; the changelog does not  <sub>Publishing: the accounts behind the procedure</sub>


## Publishing: the accounts behind the procedure

### P-1 — Before the branch exists: is Linux still running what we run?

<sub>Cut from `PUBLISHING.md`, lines 88–240 of the
2026-09-05 revision.</sub>

### Before the branch exists: is Linux still running what we run?

    python3 tools/check_standards.py     # a second, and it answers this

The pre-candidate push happens BEFORE the local gates start, so
anything wrong with the Linux workflow is found on a runner fifty
minutes later -- or never, because a job that was quietly dropped
fails nothing and reports success. So the question is asked here, in
the second before the push, by the command that already guards the
tree.

What it asks, and none of it is a list somebody has to maintain by
hand:

**Every stage `release.py` runs is either covered on Linux or exempt
WITH A REASON.** The stage list is read out of `release.py` itself,
so the Mac and the workflow cannot drift apart quietly: add a stage
and the check demands you say which CI job runs it, or why a second
machine cannot answer that question. The exemptions are the
interesting part -- each is a claim, and each has been wrong before.
The visual gallery sat exempt for months on a belief about fonts
that turned out to be false, and the day it was tested it passed on
three QGIS versions.

**Every harness under `tests/` is run by CI or exempt with a
reason**, so a new one cannot sit outside the workflow measuring this
machine alone, which is exactly how the gallery was lost.

**Every script the workflow names exists.** A moved file only fails
on a clean checkout, which is the one thing this machine can never
be.

**The six jobs are present**: standards, suite, install, gallery,
windows, macos. They answer questions none of the others can -- the
rules, the behaviour, what a USER receives, whether the map is drawn
right, whether the artefact survives a filesystem with the other
separator, and what happens on the package a macOS user downloads in
a profile nobody has seeded. And each must still be running a command the check can
recognise: a job that goes quiet is indistinguishable from a job that
passes, which is the same fault the mutation catalogue turned up in
seven of its entries.

When it complains, the fix is to change the workflow or to write the
reason down. Silencing it by deleting the stage from `release.py` is
the one response that is never correct.

The branch is named for the candidate it precedes -- `pre-0.24.0rc5`
for the run that will build `0.24.0rc5` -- so the name says which
artefact the CI result belongs to. A bare `pre-release` tells nobody
which release, and two of them at once tell nobody anything.

**AND THAT RULE HOLDS ONLY WHILE A BRANCH CARRIES ONE CANDIDATE, which
is the condition nobody wrote down.** 0.24.4's line was cut as
`pre-0.24.4rc7` and then built rc7 through rc15 from it, so for nine
candidates the name said which artefact a CI result belonged to and was
WRONG about it -- and being wrong is worse than being silent, since a
reader has no way to tell. Renamed on 2026-09-05 to `pre-0.24.4`, which
names the VERSION and cannot go stale before 0.24.5.

Nothing here parses a branch name, which is what makes either choice
safe: `ci.yml` triggers on `pre-**`, and `mutation.yml` resolves the
baseline it diffs against from the newest TAG the commit descends from
-- deliberately, after a run failed in August on a default that was a
branch name and not a tag. The artefact a CI result belongs to is
carried by the commit and by the tag (`v0.24.4rc15`), which are exact;
the branch name was only ever a convenience.

**THE MAINTAINER'S RULING, 2026-09-05: A FRESH `pre-<version>rc<N>` PER
CANDIDATE.** The original rule stands and the branch-per-candidate cost
is accepted, so a name goes on saying which artefact a CI result
belongs to -- which was the point of it. The alternative considered and
declined was naming the line for the VERSION: the name could not go
stale, and the price was a CI result naming its candidate only by its
tag.

WHAT THAT MAKES A DUTY rather than a habit: **cut the next candidate's
branch before building it, not after.** The condition the rule rests on
is one candidate per branch, and it was broken by omission rather than
by decision -- nobody cut a branch for rc8, and the eight that followed
inherited rc7's name. Nothing enforces this; it is a step in the
procedure, and its absence is invisible until somebody reads a name and
believes it.

THE TRANSITION IS RECORDED SO IT IS NOT READ AS THE RULE. `pre-0.24.4`
carries the work between rc15 and the next candidate, and it is named
for the version because the rename that produced it came first and the
ruling second. The candidate branch is cut from it under the rule.

AND IT MAY ALREADY EXIST, pointing at the commit that OPENED the
version. `pre-<version>rc1` is usually created the moment the version
does, so the push at this stage is a fast-forward rather than a
creation -- and `git branch -f` refuses it, because that branch is
checked out in the main worktree. Move it THERE, with `git merge
--ff-only <the work branch>`, and push from there; forcing it from
another worktree is not available and would be the wrong instinct
anyway, since a fast-forward is exactly what this is. (Met 2026-08-27,
cutting 0.24.4rc1.)

The sequence runs WITHOUT stopping to ask. It is one process, not
a series of decisions: the pre-candidate push is a step in it,
like the secrets check or the gates. Stop for the user only when
something INTERRUPTS it -- a red gate, a CI failure needing a
judgement, or a tree that is not in the state assumed here.
(User instruction, 2026-08-10.)

The sequence:

1. **Push the branch first** (never `main`): `git push -u origin
   pre-<version>rc<n>`. CI starts immediately. `gh run watch` follows it, or
   `gh run list --branch <branch>` for the URL.
2. **Arm the CI watcher in the same breath as the push** -- not after,
   and not by checking back by hand. It polls the branch and reports
   exactly twice: when a run APPEARS (with its URL) and when it
   COMPLETES (with the overall conclusion AND each job's verdict, so
   you learn which QGIS version failed rather than merely that
   something did). It then exits rather than polling on.

       gh run list --branch pre-<version>rc<n> --limit 1 \
         --json databaseId,status,conclusion,url

   Two properties matter and both are deliberate. It reports every
   terminal state, not just success -- a watcher that matches only
   good news is indistinguishable from one that has died. And its
   SILENCE is itself a signal: if nothing appears within a minute of
   the push, the run is not merely slow, it was never created, and
   the usual cause is the organisation's Actions policy (Settings ->
   Actions -> General), which no token here can read. Do not wait
   twenty minutes to discover that.

3. **Start the local candidate**: `python3 release.py --rc`. It reads
   the working tree for an hour and a half, so from this moment the
   working tree is FROZEN.
4. **Fix what CI reports WHILE that runs -- in a worktree, never in
   the frozen tree**:

       git worktree add ../ws-ci-fixes -b ci-fixes

   Edit, run single tests there (`tools/run_some.py` derives its own
   checkout, so it exercises the worktree), prove any mutation entry
   there, and commit on that branch.
5. **Merge when both have answered.** A candidate is promoted only
   when the local gates are green AND the Linux matrix is green; if
   either turned something up, merge the worktree's fixes into the
   branch and start the pair again.

Why a worktree rather than a second clone: it shares the object
store, so branches and history are the same repository, and the fix
merges as an ordinary commit. Why not the same tree: a release's
gates and a differential sweep both read the working tree, and
editing under them produced two spoiled measurements in one night
(2026-08-10) -- a suite whose result described a tree that no longer
existed, and a census baselining source that had changed underneath
it.

### P-2 — What the first three CI rounds cost, so the next one is cheaper

<sub>Cut from `PUBLISHING.md`, lines 401–464 of the
2026-09-05 revision.</sub>

### What the first three CI rounds cost, so the next one is cheaper

Seventy failures, then nine, then three, over three rounds of about
fifty minutes each. Worth recording because most of the cost was
avoidable and the avoidable parts have a pattern.

**Read the whole log before diagnosing.** The first round's write-up
named two failing tests as "two real platform failures" and sent the
next session after a QApplication property that was never involved.
The log said 3 passed, 70 failed, and sixty-nine of the seventy were
one missing package. A summary of a log is not the log.

**Expect the first rounds to find the ENVIRONMENT, not the code.**
One real plugin defect came out of three rounds -- ramp names
colliding by case -- against a dozen faults in tests and tooling that
had quietly encoded one machine. That ratio is normal for a first CI
and is not an argument against it: those assumptions were invisible
until something else ran them.

**Fix in the worktree, and push only when a round can answer
something new.** Each push starts a fifty-minute round, so a fix
landed while a round is in flight buys nothing and throws away the
answer the round was about to give. Batch the certain fixes, and let
an open question keep its round.

The corollary, learned on 2026-08-12 by ignoring the rule above:
CANCEL the rounds that can no longer answer anything. Nine pushes in
an hour left six overlapping rounds, every one of them doomed by a
fault already fixed in a later commit, each holding a container for
fifty minutes and each reporting a red result that meant nothing.
`gh run cancel <id>` on the superseded ones costs a second and gets
the one round that matters to the front. A queue of failures nobody
should read is worse than no queue: it trains whoever is watching to
stop reading them.

**"CAN NO LONGER ANSWER ANYTHING" IS THE TEST, AND IT IS NOT THE SAME
AS "SUPERSEDED".** An older round is FURTHER THROUGH: the suite takes
about fifty minutes, so a round begun three pushes ago is reaching the
late tests while the newest one is still in its first hundred. Where
the fixes since are known and narrow, that older round is the only
thing that will report a failure deep in the suite today rather than
tomorrow, and duplicated effort on free runners is a cheap price for
it. Deliberate practice as of 2026-08-15, and the reason several
rounds are often left in flight here.

What that costs is that EVERY EXCERPT FROM A LOG MUST BE DATED before
it is read, and on the day this was written two failures were
investigated twice over because a pasted traceback carried nothing to
say which commit produced it. They were dated in the end by the LINE
NUMBER in the traceback, which works and should not be necessary. So
`tests/run_tests.py` now prints `tree <sha>` as its second line, and
the question to ask of any red result is which tree it describes
before asking what it means.

**Instrument rather than guess when a round costs fifty minutes.** A
failure that says only which assertion it reached will be guessed at
twice. One here spent two rounds looking like a locale defect before
its message was made to report what it had actually found.

The one thing that cannot be parallelised is a MEASUREMENT beside
another measurement: the sweep, the census and the suite each want
the machine to themselves, and contention inflates per-unit times by
15-50%. CI is on somebody else's hardware, which is exactly why it
composes.

### P-3 — What a release stopped doing, and why that is not a weakening

<sub>Cut from `PUBLISHING.md`, lines 659–701 of the
2026-09-05 revision.</sub>

## What a release stopped doing, and why that is not a weakening

Three stages left the release path within a day of each other, and
together they were about eighty minutes of every candidate. The
argument was the same each time, and it is worth keeping because it
will apply again.

**The new-code mutation guard** ran fifty minutes and reached 61.5%
against its own 70% bar. It quoted a blended figure over changed
lines, which docs/MUTATION-TESTING.md says never to do; it could not
finish inside the window it gated, two mutants timing out at
twenty-one minutes each; and its red meant "write tests over the next
few days", which is a work list rather than a gate. It reports
remotely now, and its survivors are the next release's test-writing.

**The per-test coverage record** (22 minutes) followed it, because
its only consumer is `tools/mutate_auto.py`, which left. A stage kept
in the critical path to feed something that has gone is habit rather
than evidence.

**The coverage report** (24 to 31 minutes) followed both. It gates
nothing by its own docstring, it is a map of untested ground, and it
is useful when somebody is deciding where to write tests -- which is
a question you ask deliberately, not one you ask at four in the
morning because the release script did. Six candidates were built in
one night and it was read zero times.

    <qgis python> tools/coverage_report.py reports/v<version>

`--quick` was retired with it, having nothing left to skip.

**What did NOT leave, and the contrast is the point.** The visual
gallery costs 7 seconds and the colourspace comparison 16, and both
catch a WRONG MAP -- this software's characteristic failure, because
a wrong map looks exactly like a right one. Twenty-three seconds
against eighty minutes. Those two are worth more per second than
anything else in the process, and a release that dropped them to save
time would be saving the wrong time.

The test to apply to any stage in a release path: **who reads its
output, and what would they do differently?** If the honest answer is
nobody, or nothing before the artefact ships, it belongs somewhere
else -- on demand, or on somebody else's machine, reporting.

### P-4 — A TEST REPAIR SPENDS A CANDIDATE NUMBER, AND THAT IS NOT A WASTE

<sub>Cut from `PUBLISHING.md`, lines 796–836 of the
2026-09-05 revision.</sub>

## A TEST REPAIR SPENDS A CANDIDATE NUMBER, AND THAT IS NOT A WASTE

2026-08-31: three candidates were built and two thrown away to publish
one, and not a byte of the plugin changed between them. Measured
member by member, `weavingspace_qgis-0.24.4rc7.zip`, `...rc8.zip` and
`...rc9.zip` differ in exactly ONE file, `metadata.txt`, which carries
the candidate label. What changed twice was a TEST.

WHY A TEST FIX COSTS A NUMBER. `publish_candidate` requires every CI
workflow to be green ON THE CANDIDATE'S OWN COMMIT, and no later fix
turns an earlier commit's history green. So a red leg means a repair,
a repair means a new commit, and a candidate built from the old commit
can never be published however correct the software is.

    rc7  92cfaab  mutation red (Linux coverage leg), tests red
                  (macos and windows) -- one test, three runners
    rc8  ce61686  tests red (windows only) -- a different test
    rc9  2a63e7d  every job green -- published

THE ALTERNATIVE IS WORSE AND IS AVAILABLE: `--despite-ci <reason>`
publishes past a red and prints the reason in the release body. It was
not taken here, and the bar for taking it should stay high -- a
candidate exists to be trusted by somebody who did not watch it being
built, and "we knew about that one" is exactly the sentence that
erodes it.

WHAT TO DO INSTEAD OF ECONOMISING. Expect the numbers to run ahead of
the versions, and do not let that push you into batching repairs to
save a candidate: each of these two repairs was verified separately,
and the second was found only because the first had been cut and
pushed on its own. A gap in the sequence confuses nobody, which this
project already says about candidate numbering from the other side.

AND THE HONEST NOTE FOR TESTERS. Where the candidates really are the
same software, SAY SO in the notes -- rc9's open with "if you have
already installed rc7 or rc8 you have this software, since every file
in the three archives is identical bar the version label". It is one
sentence and it stops somebody re-installing to chase a difference
that does not exist. Verify it rather than assuming it: compare the
archives member by member, since the claim is cheap to check and
embarrassing to get wrong.

### P-5 — Release bodies wrap; the changelog does not

<sub>Cut from `PUBLISHING.md`, lines 1134–1192 of the
2026-09-05 revision.</sub>

## Release bodies wrap; the changelog does not

**A GITHUB RELEASE BODY PRESERVES SINGLE NEWLINES.** Notes hard-wrapped
at the usual 72 columns therefore arrive as literal line breaks, and on
a phone a sentence snaps mid-clause: "nothing is promoted," ending one
line while `main` begins the next. The renderer is never allowed to
wrap to the reader's width.

So **write each paragraph of a release body as ONE long line**, and
keep hard newlines only where the markup needs them -- headings, list
items, tables, block quotes.

**AND metadata.txt IS THE OPPOSITE, deliberately.** QGIS's plugin
manager shows that text AS IT STANDS, so a long line runs off the
panel and the entry must stay wrapped. Two surfaces, opposite rules,
and the question that decides it is always whether the RENDERER
REFLOWS. This is the same lesson as the one about a changelog shown by
two renderers, arriving from the other side.

**CHECK A RELEASE PAGE NARROW BEFORE BELIEVING IT READS** -- a phone,
or a half-width window. Found on rc9, 2026-08-18, by a maintainer on a
phone after I had looked only at a wide one.

**AND THE PART THAT STAYED WRAPPED WAS THE PART NOBODY WRITES.**
(2026-08-27, ledger row 32.) Everything above was known, written down
here, and obeyed by every candidate's own notes -- while
`publish_candidate.py`'s `CLOSING` constant, the section asking a
tester what to report back, was hard-wrapped at 72 columns from the
day it was written. It is appended to every body the tool composes, so
every candidate published since 2026-08-21 carried a paragraph that
snaps mid-clause on a phone. Nobody reread it because nobody wrote it
that day: a constant is invisible in the way a sentence you have just
typed is not.
IT IS GUARDED NOW, inside
`test_a_candidate_is_published_only_when_it_is_gated`, which already
drove the tool with `--dry-run` and read the body it composes.
Structurally rather than by width: in Markdown a paragraph ends at a
blank line, so two consecutive prose lines ARE a wrapped paragraph
whatever they measure, and a length rule fires on a legitimately short
paragraph while missing a wrap whose last line runs long. Catalogue
entry `a-release-body-paragraph-is-one-long-line`, judged caught.
FOUND BY READING THE LIVE PAGE, which is the rule this section already
carries and the reason it was found at all: the local notes file was
perfectly well formed, and the defect lived in what the tool added on
the way past.

**AND ONCE A CANDIDATE IS PUBLISHED, THE TOOL WILL NOT COMPOSE ITS
BODY AGAIN.** `--dry-run` refuses on a tag that is already taken,
exactly as it should, so a correction cannot be made by regenerating:
read the LIVE body back, edit it, and put it up with `gh release edit
--notes-file`, which leaves the tag, the URL and the attachments where
they are. The refusal prints its reason and produces no body, so a
pipeline that greps the output for the body gets nothing -- and an
empty result there means refused, not composed-and-empty.

When fixing a published page, EDIT IT IN PLACE (`gh release edit
--notes-file`) so the tag, the URL and the attachments are untouched,
then read the live body back and measure it. A local file that looks
right proves nothing about the page somebody opens.
