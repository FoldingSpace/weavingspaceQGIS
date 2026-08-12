# Publishing: releases, the project page, and the QGIS plugin repository

Three audiences receive this software, and a release serves all of
them at once: people who install the zip, people who read the project
page, and (eventually) people who find the plugin from inside QGIS
itself. What follows is the procedure and the state of preparation for
the third.

## Two machines at once: Linux CI beside the local gates

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

The branch is named for the candidate it precedes -- `pre-0.24.0rc5`
for the run that will build `0.24.0rc5` -- so the name says which
artefact the CI result belongs to. A bare `pre-release` tells nobody
which release, and two of them at once tell nobody anything.

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

**Instrument rather than guess when a round costs fifty minutes.** A
failure that says only which assertion it reached will be guessed at
twice. One here spent two rounds looking like a locale defect before
its message was made to report what it had actually found.

The one thing that cannot be parallelised is a MEASUREMENT beside
another measurement: the sweep, the census and the suite each want
the machine to themselves, and contention inflates per-unit times by
15-50%. CI is on somebody else's hardware, which is exactly why it
composes.

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

**A skip is honest or it does not happen.** Four stages' output is
USED -- the testing report quotes the suite test by test -- so those
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

## --quick, and why it needs asking for

    python3 release.py --rc --quick    # only with the maintainer's say-so

`--quick` skips the coverage report: 31 minutes, and it gates
nothing, being informational by its own docstring. It does NOT skip
the visual gallery or the colourspace comparison. Those cost 7 and 16
seconds (measured 2026-08-11) and are the two stages that catch a map
drawn WRONGLY, which is this software's characteristic failure -- a
wrong map looks exactly like a right one.

The flag used to mean the opposite, dropping the gallery and the
comparison while keeping the report. That was not wrong when it was
written: the gallery was then the slow stage. Nobody re-measured
after it became fast, so a flag meaning "skip the expensive stuff"
had come to mean "skip the cheap valuable stuff and keep the
expensive useless stuff". Re-measure a grouping like this whenever
the costs move.

**It is never the default, and the assistant does not choose it.**
Using it is the maintainer's call, asked for each time. Two reasons.
A candidate carries less evidence with it, and the person who has to
weigh "less evidence, sooner" against "more evidence, later" is the
one who will hand the build to somebody. And a shortcut that becomes
habitual stops being a shortcut and becomes the process, which is how
a gate quietly leaves a project without anyone deciding to remove it.

A candidate you intend to PROMOTE is built without it.

## A release candidate, first

    python3 release.py --rc       # gates, then a numbered candidate

Every check in this project answers whether the plugin is CORRECT.
None of them answers whether it is any good to use, and that answer
only comes back from somebody making a map with it. So a substantial
release goes out as a candidate first, to whoever will try it, and
waits for what they say.

`--rc` runs the same correctness gates as a release and then stops,
writing `dist/weavingspace_qgis-<version>rc<n>.zip`. Nothing is
committed, nothing is tagged, no image or document is rewritten, and
`git status` is as clean afterwards as before. The number counts up
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
imported stay imported. `--no-install` skips this.

To send the candidate to somebody else, attach the zip; they install
it the same way as a release, through Plugins > Manage and Install
Plugins... > Install from ZIP.

When the feedback is in and acted on, cut the release proper.

## A release

    python3 release.py            # everything, staying local
    python3 release.py --push     # the same, then publish

The stages run in a deliberate order. The project's own standards and
the secrets audit come first, so a release that breaks a rule fails in
seconds rather than after the visual gallery. Then the functional
suite, coverage, the visual gallery, and the colourspace comparison
against the original renderer, each gating. Then the testing report,
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

A release is a promotion, not a rebuild. The sequence is:

    python3 release.py --rc        # gates, packages, writes a receipt
    # install the zip, make a map with it, collect feedback
    python3 release.py             # promotes that exact artefact
    python3 release.py --push      # ...and publishes it

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

