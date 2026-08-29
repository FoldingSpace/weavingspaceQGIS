# Publishing: releases, the project page, and the QGIS plugin repository

Three audiences receive this software, and a release serves all of
them at once: people who install the zip, people who read the project
page, and (eventually) people who find the plugin from inside QGIS
itself. What follows is the procedure and the state of preparation for
the third.

## Two machines at once: Linux CI beside the local gates

**The platform questions are answered first.** Every leg that runs the
suite -- Windows, macOS and the Linux matrix -- runs
`tools/platform_probe.py` before it. That is a handful of tests whose
answers belong to the MACHINE rather than to the code: the window's
width against its ceiling, the same under a German and an
right-to-left locale, the table at the largest element count, and the
tooltip rule. They take seconds, and they fail the job before its hour
is spent rather than after.

The Windows leg is the one this is really for: about seventy-five
minutes, of which the suite is nearly all, against roughly fifteen to
install QGIS and hear the same answer. On 2026-08-29 a window-width
regression cost one full round to discover and another to confirm the
fix, which is what the probe exists to stop happening twice.


The candidate's gates take about ninety minutes on this Mac; GitHub's
amd64 runners finish the Linux matrix in about twenty. Run them in
SERIES and you learn about a Linux fault ninety minutes after you
could have. Run them in PARALLEL and both sets of problems arrive
together.

Before any of it, TWO GATES that come before the branch exists,
because a push is the one step this project cannot take back:

- **`python3 tools/check_no_secrets.py` must pass FIRST, and pass on
  exactly the files a commit would carry.** Not after branching, not
  after pushing: a secret that reaches a public branch is public
  even if the branch is deleted a minute later, and history is
  recoverable long after. It is the same reason `release.py` runs the
  check twice. (User instruction, 2026-08-10.)
- **Nothing goes up that CI does not need.** The Linux matrix
  consumes the plugin package, `tests/`, the four `tools/` checkers
  it runs, `.github/`, and the generated documents the standards
  check compares against. It has no use for candidates, reports or
  working notes -- and in this repository those are already outside
  git (`dev/`, `dist/` and `reports/` are gitignored, so none of the
  campaign notes or dossiers can travel). Before pushing, look at
  `git ls-files` and ask what each top-level entry is doing for a
  Linux test run; anything that is only for a human reading the
  repository is fine to keep, anything that is neither is a mistake
  to fix before it is public rather than after.

### The runners are kept AS CLOSE TO THE LOCAL SUITE AS PRACTICAL

The standard is parity of coverage with what this machine runs, on
every platform: Linux, Windows and macOS. A platform that only proves
the plugin loads has been smoke-tested rather than tested, and
`compat.py` exists precisely because QGIS moves its APIs -- so the
functional suite, the visual gallery and the colourspace comparison
belong on every platform CI can reach. Windows carried an
install-and-load alone until 2026-08-15, which meant the module
written to absorb QGIS's API changes had never run on the platform
most of this plugin's users are on.

The macOS leg is the one that measures the package a user downloads
rather than a container image, in a profile nobody has seeded, and it
repaid the whole exercise on its first complete run: three faults
this development machine is constitutionally unable to show, one of
which had left QGIS with no colour ramps at all for months.

Feasibility is the only ground for divergence, and it is narrow: a
limit the platform imposes that no amount of code gets round. COST IS
NOT ONE. The repository is public, so GitHub's standard runners are
free -- `windows-latest` included, with the 2x multiplier billing
only against private repositories -- and jobs run in parallel, so a
leg that finishes inside the slowest one adds nothing to the wall
clock. "Not done yet" is not a reason either; it is a gap.

When the Mac gains a stage, the runners gain it in the SAME COMMIT.
A parity rule that waits for somebody to remember has already
drifted, which is the same argument this project makes for
regenerating the derived documents in the commit that changes the
suite. Where a divergence is genuinely right, it lives as an
exemption with its reason in `tools/check_standards.py`, and that
list is read at every push.

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

### A captured stage must never be able to wedge, and must leave a record

Found 2026-08-16, in the machinery rather than the plugin, while a
candidate sat at seventy minutes on a stage that usually takes
fourteen. `run_sharded` started every shard with `stdout=PIPE` and
then called `communicate()` on them ONE AT A TIME. A shard nobody is
draining keeps writing into a pipe; at 64 KB the buffer fills and its
`write()` blocks. Measured: shard 2 sat at exactly 20:00.99 CPU for
over fifty minutes while the other two ran on, with 2374 of 2374
stack samples in `__write_nocancel` beneath GDAL's error handler.

It was never a deadlock -- the blocked shard resumes when the loop
reaches it -- which is what made it invisible: the stage completes,
eventually, and the only symptom is that sharding quietly stops
buying anything whenever output is heavy. THE SECOND HALF WAS WORSE.
Because the captured text only reached disk when the stage ENDED, a
run killed part-way left no stage log at all, so seventy minutes of
suite output bought exactly nothing.

Each shard now writes to its own file, named for the RUN (a timestamp
and pid) rather than the shard number, so a relaunch cannot land in a
live run's file -- the rule this project already learned when two
runs of one shard appended to `shard0.log` and the counts stopped
making sense. Guarded by
`test_no_shard_waits_on_a_pipe_nobody_is_reading`, whose stand-in
shards each write about 1.3 MB and then wait for each other, so the
old code stands still rather than merely running slowly.

TWO THINGS TO CHECK OF ANY CAPTURED CHILD, and neither is exotic: can
it produce more output than a pipe buffer holds while nobody is
reading, and does its output survive the run being killed? A
long-running child whose log appears only at the end is one you cannot
diagnose and cannot interrupt.

### What CI checks about the ARTEFACT, not the source

Three of the jobs ask about the thing a user receives rather than the
tree it came from, and they are cheap enough to run on every push:

**The zip is built** in the standards job. `build.py` is stdlib only,
so it needs no container, and it proves `shipped_files()` still
resolves and the archive keeps the shape the plugin repository
requires -- one top-level folder carrying `__init__.py` and
`metadata.txt`.

**The zip is installed and loaded**, in its own job over all three
QGIS versions. `tools/install_and_load.py` unpacks it into a profile
the way the plugin manager does, imports the package BY NAME from
there, calls `classFactory`, `initGui` and `unload`, and requires
unload to have taken back the menu entry and the toolbar icon. It is
a separate job because GitHub runs jobs concurrently: four minutes
beside the suite's fifty-four costs nothing, where a step inside the
suite legs would add to every one of them. The matrix is deliberate --
`metadata.txt` PROMISES QGIS 4.0, and a plugin that will not load on
the floor it declares is a promise broken at install time.

**The zip is installed and loaded ON WINDOWS AND ON MACOS**, in the
`windows` and `macos` jobs, and neither stops there any more: both
provision the stack and run the functional suite and the gallery, so
each platform is as close to what this machine runs as GitHub
permits. The paragraph that used to stand here said install-and-load
"is the whole of the Windows leg", which was true for a few hours on
2026-08-15 and is kept only as the shape to argue against: a leg that
proves the plugin loads has been smoke-tested, and what Linux cannot
answer is everything that turns on the platform being itself -- path
separators, the long-path ceiling, a file still locked by whatever
wrote it, code signing, an app bundle's own interpreter, and whether
the archive's layout survives that unpacking. `compat.py` exists
because QGIS moves its APIs and had never run on either platform.

QGIS arrives through Chocolatey's `qgis` package, which installs the
standalone installer's QGIS -- the same thing a Windows user
downloads from qgis.org, with its own Python and the
`python-qgis*.bat` shims. That is the one route somebody was found
actually driving for this purpose: GispoCoding's plugin template
runs its tests through that shim on `windows-latest`. The OSGeo4W
network installer is the other credible route and is used on GitHub
runners (GRASS drives it, 89 seconds for 22 packages), but no
workflow was found installing QGIS ITSELF that way, so taking it
would have meant guessing at installer flags on a job that costs a
quarter of an hour to retry. conda-forge has a win-64 QGIS and no
Windows CI using it, and is a different build with a different
Python besides.

`qgis` and not `qgis-ltr`: the LTR is 3.44, below the 4.0 floor
`metadata.txt` declares, so the plugin would refuse to load and the
job would be red about nothing -- the same reason the Linux matrix
avoids the `latest` image. The version is otherwise whatever
Chocolatey serves that week, so it is printed every run rather than
pinned. Nothing is cached: a stale cache key would leave this green
against a QGIS nobody runs.

It does NOT run `tools/ci_provision.py`. `classFactory` calls
`deps.add_paths` and imports Qt, `initGui` builds a QAction, and
nothing on that path touches geopandas -- measured by running the
same script under macOS QGIS with none of the stack present. A
provisioning step would buy a download and a second failure surface
in front of the one question this job asks.

**The published claims are audited**, with `--check`, which asks only
the questions whose answer is somebody's words: a missing changelog
entry, a stale image, a broken relative link, a vendored version
claimed in prose, a repository URL. The citation's version is skipped
because a release mends it itself, and gating a push on something the
release fixes would be red by design.

None of this replaces the local gates. It moves the failures that
have nothing to do with rendering -- packaging, metadata, links --
from eighty minutes into a release to the push that caused them.

### CI needs geopandas; the plugin must never take it unasked

These two pull in opposite directions and the resolution is worth
stating, because getting it wrong would cost the plugin its place in
the QGIS plugin repository.

**The problem.** The official `qgis/qgis` images ship QGIS and its own
Python and nothing else -- no geopandas, shapely, pandas or networkx.
The suite imports them directly, so the first Linux run reported
seventy failures of which sixty-nine were one missing package wearing
different costumes (2026-08-11). CI cannot test anything until they
are there.

**Why the obvious fix is forbidden.** The plugin can already fetch
those packages: `deps.py` downloads wheels from PyPI. But it does so
only after `plugin.dependency_consent_box` has named the packages,
the source and the exact destination and waited for a click. Fetching
code at runtime is the single thing a plugin repository reviewer
examines hardest, and rightly. So the tempting shortcut -- a flag, or
an environment variable, that lets CI skip the dialogue -- is
precisely what must not exist: it would put a consent-free download
path into the SHIPPED plugin, where a reviewer would find it and be
right to refuse it. What CI needs cannot be paid for out of what a
user is promised.

**How it is squared.** `tools/ci_provision.py` calls
`deps.provision_from_pypi` directly, and `tools/` is not in
`build.shipped_files()`. Nothing in it reaches a user's machine, and
the plugin gains no new path at all. The distinction is not a
technicality: a maintainer running a program that installs packages
is consent, and software installing them unasked is not. The consent
gate remains the only route from shipped code to PyPI, and
`test_pypi_provisioning_is_reached_only_through_consent` asserts that
across every file that ships -- exactly one such call, inside the
function that raises the dialogue, after the refusal returns. It is
in the mutation catalogue as `consent-gates-the-download`, so the day
somebody weakens the gate a test fails rather than a reviewer
noticing.

**And it is a gain, not a tax.** Running the plugin's own provisioner
is the Linux path this CI exists for. Wheel-tag matching, the numpy
1.x floor that must never become 2.x, the support-package fetch and
the pyproj data redirection are all plugin code that a Mac whose QGIS
already carries every package can never execute. `pip install
geopandas` in the workflow would make the suite run and would
exercise none of it. So the provisioning step is a test in its own
right: when it fails, `deps.py` is broken for every Linux user, and
we learn it here rather than from an issue.

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

## After a release: which version comes next

**The default is the PATCH: after N.X.Y, work toward N.X.(Y+1).** So
0.24.2 is followed by a branch named `pre-0.24.3rc1` and a version
bumped to 0.24.3, not 0.25.0. The maintainer says otherwise when a
release earns a minor bump, and that is the only thing that moves it.

The reason to write this down rather than leave it to judgement: what
follows a release is usually the triage of what the release did not
fix, plus whatever the hunts and the remote instruments turned up, and
that is patch-shaped work by construction. Reaching for X+1 by default
quietly claims a release is bigger than it is, and the claim is made
by whoever happens to type the branch name at the end of a long
session. (Maintainer's instruction, 2026-08-14.)

The first act on that branch is the version bump in `metadata.txt`,
which immediately makes `sync_release_content --check` fail for want
of a changelog entry. That is the gate working. Write a placeholder
that says plainly it is one and names the command that replaces it --
`git diff v<previous>..HEAD -- weavingspace_qgis/` -- so a stub cannot
ship unnoticed, and put it through text review like any other sentence
a user meets.

## After a candidate ships: the instruments that run remotely

A candidate's gates answer whether the plugin is correct. Two other
questions -- how good the suite is, and whether a refactor has
quietly stopped an old test reaching the behaviour it names -- are
answered by the mutation instruments, and both want a machine to
themselves for hours. Running them here blocks the development
machine; running them on GitHub costs nothing anybody is waiting for:

    bash tools/watch_remote_mutation.sh <branch> both v0.24.0

They REPORT rather than gate, and their findings belong to the NEXT
candidate. The sequence that follows from that:

1. a candidate passes its gates locally and the Linux matrix, and is
   promoted to a release;
2. the mutation runs are dispatched against the release's branch and
   watched from here;
3. what they find is triaged into the next pre-candidate branch --
   `pre-0.24.1rc1` after 0.24.0 -- because a survivor is a finding
   about the tests rather than a fault in the artefact already
   through its gates.

Do not hold a release for them. That is the whole reason they are
not gates: a mutation survivor is an argument for the next round of
test-writing, and treating it as a blocker would either delay every
release or teach everybody to wave it through.

Full reasoning, including what deliberately did NOT move to CI, in
docs/MUTATION-LOOP.md.

## Work for later versions, and the roadmap

Anything written now for a LATER release lives on a branch named
`for-<version>/<slug>`, and everything a version owes is listed in
`ROADMAP.md`, including what has no code yet.

`tools/check_roadmap.py --merge` runs as the first stage of every
release, before the standards check and long before the suite,
because both failures it catches cost a second to find and ninety
minutes to discover afterwards:

- a branch written for THIS version and never merged. It is merged
  here. A conflict aborts the release instead of being resolved,
  since a conflict is a question about intent;
- an entry in this version's roadmap section that nobody did. The
  release stops and names it.

Closing an entry means doing it or DEFERRING it, and deferring is the
maintainer's call, made by moving the entry to a later section. No
tool moves one. When a section is genuinely clear it says so, in the
words the checker quotes back.

Two habits keep it honest. Delete an entry when it lands, or the file
turns from a statement of what is owed into a diary of what once was.
And put the thing with no code in it anyway: the ideas this project
has lost were the ones mentioned only in conversation.

## Resuming a run that was stopped by the machinery

    python3 release.py --rc --resume

A release is ninety minutes of gates, and not every failure is about
the software. On 2026-08-11 three candidates were abandoned in one
evening, each after most of the gates had passed, and none of the
three faults was in the plugin: a coverage recorder that wrote
nothing because the suite exits through `os._exit`, a recorder that
logged every registration rather than every run, and a test whose
timing had been tuned in a different harness. Each cost a full
re-run of work that had already answered.

`--resume` skips a stage that passed before against EXACTLY the
inputs it has now. Nothing is skipped without the flag: a full run
is what a release means, and the saving is worth asking for
deliberately rather than inheriting by accident.

**What counts as unchanged is declared, not guessed.**
`STAGE_DEPENDS` in release.py names what each stage's answer turns
on. It is deliberately narrower than the whole tree and wider than
the files that ship: editing `tests/run_tests.py` retires the
suite's answer although no shipped byte moved, and a fix to
`tools/coverage_per_test.py` retires the coverage record AND NOTHING
ELSE, which is the case the flag was built for. The documents the
suite reads are in that list too, because
`test_every_documented_command_still_exists` opens them and has
failed twice on prose; a documentation edit really can break a test,
and it is exactly the kind of change that feels as though it cannot.

THAT EXAMPLE NOW DESCRIBES NOTHING, and `release.py` says so at the
map itself: the coverage stage left the release path and its entry
left `STAGE_DEPENDS` with it. Kept here because the SHAPE is what the
flag is for -- a change to machinery that retires one stage's answer
and no other -- and because a document quietly dropping its own
worked example loses the reason as well as the example. (Noted
2026-08-18.)

**A skip is honest or it does not happen.** Three stages' output is
USED (four until the per-test coverage record left the release path;
`skip_if_already_done`'s own docstring notes the sentence had only
ever named three, and only three carry a `STAGE_DEPENDS` entry, so
only three are skippable at all) -- the testing report quotes the suite test by test -- so those
may only be skipped when the output survives in
`reports/stage-logs/`, and the saved text is handed to the caller.
A skip that returned nothing would produce a report describing
nothing, which is worse than the hour it saved. Every skip announces
itself with the time the stage originally passed, because a gate
that did not run is a thing a reader must be told rather than left
to infer from a suspiciously short log.

**When NOT to use it.** A candidate for promotion is built by a run
that measured this tree, and `--resume` is for getting back to that
point after an interruption, not for avoiding measurement. If you
cannot say which stages it skipped and why each was still true, run
it again without the flag.

## What to do BEFORE a candidate, and what not to

Not much, and less than instinct suggests. The gates run
cheapest-first -- standards, secrets, then the functional suite --
so a broken suite stops a candidate about twenty-four minutes in.
Running the suite (or coverage, or the gallery) standalone first
gives no earlier warning and doubles the wait. Iterate with
`tools/run_some.py` on the tests you are actually changing, then go to
`python3 release.py --rc`.

Two things DO belong first, because the gates check them rather than
produce them:

    python3 tools/test_map.py
    python3 tools/bug_register.py

and a settled text-review queue (`python3 tools/text_review.py`,
reviewed and applied by the USER). A stale generated document stops
the build on a count mismatch, and no gate can approve prose on
somebody's behalf.

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

## A release candidate, first

    python3 release.py --rc       # gates, then a numbered candidate

Every check in this project answers whether the plugin is CORRECT.
None of them answers whether it is any good to use, and that answer
only comes back from somebody making a map with it. So a substantial
release goes out as a candidate first, to whoever will try it, and
waits for what they say.

`--rc` runs the same correctness gates as a release and then stops,
writing `dist/weavingspace_qgis-<version>rc<n>.zip`. Nothing is
committed and nothing is tagged.

One exception to "and the tree is untouched", found on 2026-08-14 and
recorded rather than tidied away: the candidate MENDS `CITATION.cff`
to the version being built, so `git status` afterwards shows that one
file modified. It is harmless -- CITATION.cff does not ship, so the
receipt digest is unaffected, and the promotion would make the same
edit -- but the sentence that used to stand here said the tree was as
clean afterwards as before, and it was not. The number counts up
from the candidates already in `dist/`, so a new one can never
overwrite the one somebody is testing.

The candidate declares itself as `<version>rc<n>` in QGIS's plugin
manager, though the version in `metadata.txt` on disk is untouched:
the substitution happens inside the archive only. A tester can
therefore see at a glance which build they are looking at, which
matters when the feedback arrives days later.

A candidate also installs itself, into every QGIS profile on this
machine that ALREADY has the plugin, so it can be tried without going
through the plugin manager. Profiles that do not have it are left
alone: putting a plugin into a profile nobody asked about leaves a
user something to discover and remove, and a testing profile exists
precisely so that what is in it is deliberate. A `libs/` folder is
preserved, since those wheels belong to that machine and are not in
the zip; everything else is replaced, so a file dropped from the
plugin cannot linger in an installed copy and go on being imported.
Restart QGIS or use Plugin Reloader afterwards — modules already
imported stay imported. Skipping the install is `build.py`'s
`--no-install` rather than a flag on the command above:
`release.py` declares only `--push`, `--resume` and `--rc`, and
invokes `build.py` without forwarding anything, so
`release.py --rc --no-install` is an argparse error. Corrected
2026-08-18, having documented a flag the command could not take.

## Publishing a candidate

Every candidate goes to GitHub as a PRE-RELEASE, and has since ten of
them had gone out by hand:

```bash
python3 tools/publish_candidate.py --notes dist/CANDIDATE-<label>.notes.md
```

That tags `v<version>rcN` on the candidate's own commit, creates a
release titled `<version>rcN — release candidate` marked pre-release,
and attaches the zip, the testing report and the comparison PDF. It
refuses without a receipt matching the tree, on a tag already taken,
while CI on that commit is not green, or without notes saying what
changed since the last candidate. `--dry-run` prints the body it would
publish; `--despite-ci <reason>` publishes past a red or unfinished CI
and prints the reason in the release itself.

A pre-release never becomes Latest, so `main` and the project page go
on describing the last real version. Promotion is still `release.py`,
still from `main`, and still the maintainer's call.

To send the candidate to somebody else directly, attach the zip; they install
it the same way as a release, through Plugins > Manage and Install
Plugins... > Install from ZIP.

When the feedback is in and acted on, cut the release proper.

## A release

    python3 release.py            # everything, staying local
    python3 release.py --push     # the same, then publish

The stages run in a deliberate order. The project's own standards and
the secrets audit come first, so a release that breaks a rule fails in
seconds rather than after the visual gallery. Then the functional
suite, the visual gallery and the colourspace comparison against
the original renderer, each gating. Coverage is NOT among them
any more (see what a release stopped doing, above). Then the testing report,
which lists every test with its result and measured values.

After that come the publication steps. The images in README.md and
docs/index.html are retaken from this release's gallery, including a
fresh grab of the dialog, because those pictures are claims about how
the plugin looks now. The published-content audit then checks the
claims that are not pictures: that CITATION.cff names this version
(it mends this itself), that metadata.txt carries a changelog entry
for it, that every referenced image exists and was actually
regenerated, that relative links resolve, that the vendored library
version claimed in prose matches the stamp
`weavingspace_qgis/vendor/VENDOR-VERSION.txt` written by the vendoring
tool, and that the repository and page URLs agree with metadata.txt.
Anything mechanical is corrected; anything needing words stops the
release, because rewriting prose automatically at release time is how
documentation turns to mush.

Only then is the zip built, and only then does git see anything. The
commit and the tag are unconditional, since both are local and undone
with one command, and the repository should never disagree with the
zip just built. The push and the GitHub Release happen only with
`--push`. An existing tag is never moved: bump the version instead.

The project page needs no separate step. It is served by GitHub Pages
from `docs/` on the main branch, so the same push that publishes the
code publishes the page, usually within a minute.

## Before promoting: re-read the changelog against the diff

The changelog is approved once and then goes stale under you. On
2026-08-12 it was approved in the morning, said "Nothing else about
the plugin has changed", and shipped after an afternoon that changed
something else about the plugin -- a modal dialog on the live-update
path, removed by the documentation audit hours after the sentence was
signed off.

So the last thing before `release.py` is not a gate, it is a reading:
put `git diff <previous tag>..HEAD -- weavingspace_qgis/` beside the
changelog entry and check the entry still describes it. Two minutes,
and it is the only step that catches prose falsified by later work.

`metadata.txt` is in the text-review queue as of that day, so a
CHANGED entry re-enters review. What the queue cannot do is notice
that an unchanged entry has stopped being true, which is exactly the
case that shipped.

## Release notes: two halves, one written and one measured

A release page has two readers and one document usually serves
neither. Somebody deciding whether to upgrade wants a paragraph.
Somebody evaluating the project wants to know what was measured and
to be able to check it. So the notes are composed rather than
written, by `tools/release_notes.py`, and `release.py` puts them in
the release BODY:

**The concise half is the `changelog=` entry in metadata.txt** for
this version. A person writes it, it goes through
`tools/text_review.py` like every other sentence a user meets, and it
is already what QGIS's plugin manager shows -- so the release page
and the plugin manager cannot drift, being the same words. Write it
as what a user can now do, or no longer has to worry about, rather
than as a list of commits.

**Open each version with a summary sentence, then CATEGORIZED detail.**
The two readers of a release page are also the two readers of a
changelog entry: one is deciding whether to upgrade and wants a
sentence, the other has upgraded and wants to know what moved. A
single undifferentiated paragraph serves the first badly, because
the decision is buried in the specifics. So the first sentence
says what the release is for, and what follows is grouped under
short category labels drawn from what actually changed -- Colour,
Setup, Warnings, Preview -- so a reader finds the part that
concerns them instead of scanning a paragraph for it. The
categories are not a fixed set: a fixed set produces empty
headings, and empty headings are how a changelog starts looking
like a form. (Maintainer's instruction, 2026-08-13; the entries for
0.23.0 through 0.24.2 were rewritten to this shape at the same
time, so the convention has examples rather than only a rule.)

**A changelog says what a user CAN now do, not what the software now
always does.** 0.24.3's summary was drafted as "a colour means the
same thing everywhere it appears on the map", and the maintainer
struck it out: the class count, the scheme and the pinned bounds are
all per element, so two elements agree only when somebody has set them
up to. What the release changed is that they CAN. The corrected line
reads "a colour can now mean the same thing everywhere it appears on
the map, if that is what you want", and the difference is not
politeness. A capability written as a guarantee is a promise the
settings can break, and the reader who finds it broken has been told
something untrue by the plugin rather than by their own configuration.
When a sentence describes a behaviour, ask what has to be true for it
to hold; if the answer is anything at all, the sentence needs the
condition in it. (Maintainer's correction, 2026-08-14.)

**The comprehensive half is generated**: how many tests ran and how
many guard a defect that actually happened, what is attached and what
each attachment is for, where the process documents are, and the
`**Full changelog**` compare link a GitHub reader looks for. Every
line is omitted rather than guessed when its source is missing, so
notes assembled early are shorter rather than wrong.

**It refuses when the changelog entry is missing.** That half is the
part a person has to write, and a release whose notes were generated
is a release nobody described.

The testing report stays ATTACHED rather than being the body. It used
to be the body, which meant the announcement was a per-test listing:
excellent evidence, unreadable as news.

## What the published images must show

Every image in README.md and on the project page shows REAL DATA
DISPLAYED AS A MAP: a named place, recognisable geography, region
outlines, and a legend where the classes need one. Not an abstract
pattern, however handsome.

The reason is what a reader is actually asking. Someone who lands on
the page wants to know what they could produce at the end of an
afternoon with their own data, and a field of coloured hexagons
answers a different question — it shows the technique's mechanics
rather than its output. The plugin's whole claim is that several
attributes of real places can be read from one map; images that omit
the places and the attributes argue against it.

Practically: prefer the packaged Auckland deprivation data or another
real dataset over synthetic grids, keep the region outlines on, show
a legend, and size the image so the pattern is legible rather than
decorative. Where a figure from the published article can be used
under its licence, that is better still, since those figures were made
to carry exactly this argument — attribute them in the caption and
record the licence beside the file.

## The QGIS plugin repository

The plugin is not yet submitted to plugins.qgis.org. What is already
in place: `metadata.txt` carries name, version, description, about,
author and email, `qgisMinimumVersion` and `qgisMaximumVersion`,
`supportsQt6`, tags, category, icon, a changelog, and
`experimental=True`, which is honest and should stay until the
prototype stops being one. The tracker, repository and homepage fields
point at this repository and its page. The zip that `build.py`
produces already has the shape the repository requires: a single
top-level folder containing `__init__.py` and `metadata.txt`.

Three things to settle before submitting.

An OSGeo user ID is needed to upload, and it belongs to a person
rather than to the software; register at id.osgeo.org and the plugin
is then owned by that account.

The bundled library needs to be visible rather than discovered.
`weavingspace_qgis/vendor/weavingspace/` is a copy of an MIT-licensed
library, which is permitted, and LICENSE.md reproduces its notice in
full. Say so in the submission rather than leaving a reviewer to find
a vendor directory and wonder.

The dependency download needs the same treatment. `deps.py` fetches
wheels from PyPI when geopandas, pandas or shapely are missing, which
on QGIS 4 mostly means Linux. Reviewers look closely at plugins that
fetch code at runtime, and rightly so. The behaviour is disclosed in
the metadata, the README and the project page: the plugin asks first,
downloads into its own folder, and changes nothing else in the QGIS
installation. Disclosing it plainly is both the honest course and the
faster one; plugins get rejected for hiding this, not for doing it.

Two smaller matters. The plugin's name must be unique in the
repository, and "WeavingSpace" appears to be free. And a submitted
plugin acquires users who upgrade through the plugin manager, so the
changelog stops being a formality: from that point on, every release
needs an entry a user can act on.

## From candidate to release

A release is a promotion, not a rebuild. The whole sequence, from a
green candidate to a published release, is:

    python3 release.py --rc        # gates, packages, writes a receipt
    # install the zip, make a map with it, collect feedback

    git checkout main              # a release is published FROM main
    git merge --ff-only pre-<version>rc<n>

    python3 release.py             # promotes that exact artefact
    python3 release.py --push      # ...and publishes it

**Why the checkout is in the middle of that, and is not optional.**
`release.py --push` runs `git push origin HEAD`, which pushes
whatever branch you are standing on, and a tag does not care what
branch it is on. Promote from the pre-candidate branch and you get a
perfectly real GitHub Release sitting beside a project page and a
README that still describe the PREVIOUS version -- because Pages
serves `docs/` from `main` and the repository's front page is
`main`'s README. Nothing in git objects to this; the only person who
finds out is somebody who visits the page.

So `release.py` refuses to commit or tag anywhere but `main`, and
says which fast-forward to run. It refuses rather than merging on
your behalf, because merging is a decision. `--ff-only` is the guard
in that command: if it will not fast-forward, something reached
`main` that this candidate never saw, and that is a question rather
than a merge.

The fast-forward leaves the tree byte-identical, so the candidate
receipt still matches and nothing is re-measured. Guarded by
`test_a_release_publishes_from_the_branch_the_page_is_served_from`.

**And the page needs switching on, once, by a person.** Settings ->
Pages -> Deploy from a branch -> `main`, folder `/docs`. Until that
is done the project page 404s and every README link to it points at
nothing, which no gate here can detect.

**What the candidate leaves behind.** A zip, a dossier (the page a
reviewer reads) and a receipt recording a digest of exactly the files
that ship. The receipt is written last, after every gate, so its
existence is the proof that this tree passed.

**What the release does with it.** It recomputes the digest and looks
for a receipt of this version that matches. Without one it refuses,
and says whether no candidate was ever built or whether one was built
from a different tree. With one it skips the suite, gallery, coverage
record and reference comparison — they measured this artefact
already — and goes straight to the zip, the commit, the tag and, with
`--push`, the GitHub release.

**What invalidates a candidate.** Any change to a file that ships:
the plugin package, the vendored library, `LICENSE.md`. Changes to
tests, tooling or documentation do not, because they cannot alter
what a reviewer installed.

**Numbering.** Candidate numbers are never reused. Every artefact
bearing a number spends it — zip, dossier, receipt — so deleting one
does not hand its number back.

**Naming.** EVERY ARTEFACT CARRIES ITS VERSION, in `dist/` and on the
release page alike. Candidates always did —
`weavingspace_qgis-<version>rc<n>.zip` — and the release path did not,
attaching a bare `weavingspace_qgis.zip`; the convention existed and
had been applied to half the process. The prose that names the
download follows the artefact rather than the artefact being held
still for the prose, so README.md, docs/index.html and the attachment
line `tools/release_notes.py` composes all move with it, through text
review like any other sentence a user meets. Releases already
published keep the asset names they went out with: rewriting those
would break links people already hold.

**And no CHECK writes into `dist/`.** `check_before_push` replays the
`standards` job, one of whose steps runs `build.py` — so the push gate
was rebuilding an artefact into the directory that holds the gated
ones, from whatever tree it happened to be run against. A packaging
check only asks whether the archive still forms, which a temporary
directory answers just as well. What made this worth a rule rather
than a tidy-up: on 2026-08-29 the newest file in a `dist/` holding
three versioned candidates and their receipts was an unversioned zip
an hour younger than the published candidate and three bytes different
from it.


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
