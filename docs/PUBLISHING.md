# Publishing: releases, the project page, and the QGIS plugin repository

Three audiences receive this software, and a release serves all of
them at once: people who install the zip, people who read the project
page, and (eventually) people who find the plugin from inside QGIS
itself. What follows is the procedure and the state of preparation for
the third.

Sections cut back to their procedure carry an id (P-2) whose full
account is in `PUBLISHING-archived.md` -- what the first CI rounds cost,
what a release stopped doing and why. See docs/DOC-ARCHIVING.md.

## How to add to this file

This is a RUNBOOK: every section is a procedure, and a procedure keeps
every step. When a step changes, change it where it stands, in the
command block and the sentence that explains it. When a release or a
CI round teaches something, the RULE it taught goes into the section
it belongs to as one sentence, and the ACCOUNT -- what it cost, the
timings, the rounds -- goes to docs/PUBLISHING-archived.md under an id
minted with `python3 tools/doc_archive.py --mint P "title"`, quoted at
the rule. An entry past thirty lines or a paragraph that opens with a
date fails `tools/check_standards.py` with the fix in the message.

## Two machines at once: Linux CI beside the local gates

**The platform questions are answered first.** Every leg that runs the
suite -- Windows, macOS and the Linux matrix -- runs
`tools/platform_probe.py` before it. That is a handful of tests whose
answers belong to the MACHINE rather than to the code: the window's
width against its ceiling, the same under a German and an
right-to-left locale, the table at the largest element count, and the
tooltip rule. They take seconds, and they fail the job before its hour
is spent rather than after.

It exists for the Windows leg, where the suite is seventy-five
minutes of a job that could have answered in fifteen, and where a
window-width regression once cost two full rounds (P-13).

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
every platform CI can reach: the functional suite, the visual gallery
and the colourspace comparison, since `compat.py` exists because QGIS
moves its APIs and a leg that only proves the plugin loads has been
smoke-tested. Feasibility is the only ground for divergence and cost
is not one, standard runners being free on a public repository and
jobs running in parallel. When the Mac gains a stage the runners gain
it in the SAME COMMIT, and a divergence lives as an exemption with its
reason in `tools/check_standards.py`, read at every push. The rule
binds in CLAUDE.md; what the macOS leg found on its first complete
run, and the months Windows ran nothing but an install-and-load:
P-14.

### Before the branch exists: is Linux still running what we run?

    python3 tools/check_standards.py     # a second, and it answers this

The pre-candidate push happens BEFORE the local gates start, so
anything wrong with the Linux workflow is found on a runner fifty
minutes later -- or never, because a job that was quietly dropped fails
nothing and reports success. So the question is asked here, in the
second before the push, by the command that already guards the tree.
What it asks, and none of it is a list somebody has to maintain by hand:
**Every stage `release.py` runs is either covered on Linux or exempt
WITH A REASON.** The stage list is read out of `release.py` itself, so
the Mac and the workflow cannot drift apart quietly: add a stage and the
check demands you say which CI job runs it, or why a second machine
cannot answer that question. (P-1.)

### A captured stage must never be able to wedge, and must leave a record

`run_sharded` once started every shard with `stdout=PIPE` and drained
them one at a time, so a shard writing past 64 KB blocked until the
loop reached it -- fifty minutes at a fixed CPU figure -- and a run
killed part-way left no stage log at all, since captured text reached
disk only when the stage ended. Each shard now writes to its own file,
named for the RUN rather than the shard so a relaunch cannot land in a
live run's file; guarded by
`test_no_shard_waits_on_a_pipe_nobody_is_reading`. Ask of any captured
child whether it can outrun a pipe buffer while nobody reads, and
whether its output survives the run being killed. (P-6.)

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
`windows` and `macos` jobs, and both then provision the stack and run
the functional suite and the gallery, since what Linux cannot answer
is everything that turns on the platform being itself: path
separators, the long-path ceiling, a file still locked by whatever
wrote it, code signing, an app bundle's own interpreter. The Windows
leg installs QGIS through Chocolatey's `qgis` package rather than
`qgis-ltr`, whose 3.44 is below the floor `metadata.txt` declares,
prints the version rather than pinning it, caches nothing, and does
NOT run `tools/ci_provision.py`, since `classFactory`, `initGui` and
`unload` touch no geopandas. (P-7, P-15.)

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
avoidable and the avoidable parts have a pattern. **Read the whole log
before diagnosing.** The first round's write-up named two failing tests
as "two real platform failures" and sent the next session after a
QApplication property that was never involved. (P-2.)

## After a release: which version comes next

**The default is the PATCH: after N.X.Y, work toward N.X.(Y+1).** So
0.24.2 is followed by a branch named `pre-0.24.3rc1` and a version
bumped to 0.24.3, not 0.25.0. The maintainer says otherwise when a
release earns a minor bump, and that is the only thing that moves it.

The reason: what follows a release is patch-shaped by construction,
and reaching for X+1 by default claims a release is bigger than it
is, a claim made by whoever types the branch name at the end of a
long session (maintainer's instruction, 2026-08-14; P-16).

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

**AND YET A RED `mutation` WORKFLOW DOES STOP A CANDIDATE, WHICH IS
NOT A CONTRADICTION.** Every measuring step in `mutation.yml` is
`continue-on-error`, so no mutation MEASUREMENT can redden it; what can
is provisioning, the baseline check, an artefact upload, or the
coverage leg, which runs the WHOLE SUITE three ways under the per-test
recorder and refuses a partial record. That leg has stopped two
candidates and been right both times, and neither was a survivor. The
split question this paragraph once carried was measured moot (R-31).
(P-8.)

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

`--resume` exists because three candidates were once abandoned in one
evening, each after most of the gates had passed, on faults none of
which was in the plugin (P-17).

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

(The coverage example above left `STAGE_DEPENDS` with its stage on
2026-08-18; the SHAPE is what the flag is for, P-9.)

**A skip is honest or it does not happen.** Three stages' output is
USED -- the testing report quotes the suite test by test -- so only
those three carry a `STAGE_DEPENDS` entry, only they may be skipped,
and only where their output survives in `reports/stage-logs/`, the
saved text being handed to the caller. Every skip announces itself
with the time the stage originally passed, because a gate that did
not run is a thing a reader must be told rather than left to infer
from a short log. (P-18.)

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

Three stages left the release path within a day of each other, about
eighty minutes of every candidate: the new-code mutation guard, the
per-test coverage record and the coverage report, each because nobody
read its output before the artefact shipped. WHAT DID NOT LEAVE IS THE
CONTRAST: the visual gallery at 7 seconds and the colourspace
comparison at 16, both of which catch a WRONG MAP, this software's
characteristic failure. THE TEST TO APPLY TO ANY STAGE IN A RELEASE
PATH: who reads its output, and what would they do differently? If
the honest answer is nobody, or nothing before the artefact ships, it
belongs on demand or on somebody else's machine, reporting. (P-3,
P-19.)

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

One exception: the candidate MENDS `CITATION.cff` to the version being
built, so `git status` shows that one file modified. CITATION.cff does
not ship, so the receipt is unaffected, and the promotion would make
the same edit. The number counts up from the candidates already in
`dist/`. (P-10.)

The candidate declares itself as `<version>rc<n>` in QGIS's plugin
manager, though the version in `metadata.txt` on disk is untouched:
the substitution happens inside the archive only. A tester can
therefore see at a glance which build they are looking at, which
matters when the feedback arrives days later.

A candidate also installs itself into every QGIS profile that ALREADY
has the plugin -- never into one that does not -- preserving `libs/`
and replacing everything else, so a dropped file cannot linger.
Restart QGIS or use Plugin Reloader afterwards. Skipping the install is
`build.py --no-install`, since `release.py` forwards nothing to it.
(P-11.)

## READING CI: three ways the reading itself fails

Each looks like an answer rather than a broken instrument. `gh api
.../jobs/<id>/logs` returns zero bytes and exit 1 without
`--allow-escape-sequences`, so a grep over it reads exactly like a
clean log: pass the flag and strip the codes. A RUNNING job's log is
404 while a completed job's is readable at once, which is why
`tools/platform_probe.py` runs first. And `gh --jq` takes a filter
and not jq's own flags, so `--jq --arg` is silently no filter at all:
pipe to `jq` proper. (P-20.)

## What the legs take

Compare a running job against THE SAME JOB ON THE PREVIOUS ROUND,
never against a figure in prose, which is true until somebody adds a
test: this project has had that both ways round, a ceiling sized from
a stale number and a healthy run read as over-running (P-21).
Measured across three rounds of one day at 727 tests:

    Linux suite legs   60, 66, 68 minutes
    macOS              78, 79 minutes
    Windows            97, 105, 133 minutes
    mutation coverage  41 (failing), 47 (passing)

The `windows` and `macos` jobs carry 300-minute limits with 180 on
the suite step, so none of those was in danger.

## A TEST REPAIR SPENDS A CANDIDATE NUMBER, AND THAT IS NOT A WASTE

Three candidates were built and two thrown away to publish one
(2026-08-31), and not a byte of the plugin changed between them. Measured member
by member, `weavingspace_qgis-0.24.4rc7.zip`, `...rc8.zip` and
`...rc9.zip` differ in exactly ONE file, `metadata.txt`, which carries
the candidate label. What changed twice was a TEST -- and rc16's first
build went the same way on 2026-09-06, on a test premise the
even-count ruling had made false hours earlier, the number surviving
only because no zip, dossier or receipt had been written (T-143). WHY A TEST FIX COSTS
A NUMBER. `publish_candidate` requires every CI workflow to be green ON
THE CANDIDATE'S OWN COMMIT, and no later fix turns an earlier commit's
history green. (P-4.)

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

The changelog is approved once and then goes stale under you: 0.24.1's
was signed off in the morning saying nothing else had changed, and
shipped after an afternoon that changed something else (P-22). So
the last thing before `release.py` is a reading, not a gate: put `git
diff <previous tag>..HEAD -- weavingspace_qgis/` beside the entry and
check it still describes the diff. `metadata.txt` is in the
text-review queue, so a CHANGED entry re-enters review; what the queue
cannot notice is an unchanged entry that has stopped being true.

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

**Open each version with a summary sentence, then CATEGORIZED detail**
under short labels drawn from what actually changed -- Colour, Setup,
Warnings, Preview -- never a fixed set, since a fixed set produces
empty headings and a changelog that looks like a form. The two readers
of a release page are the two readers of an entry. (Maintainer's
instruction, 2026-08-13; the entries from 0.23.0 on are the examples;
P-23.)

**A changelog says what a user CAN now do, not what the software now
always does.** A capability written as a guarantee is a promise the
settings can break: 0.24.3's "a colour means the same thing everywhere
it appears" became "can now mean ... if that is what you want", since
two elements agree only when somebody has set them up to. When a
sentence describes a behaviour, ask what has to be true for it to
hold; if the answer is anything at all, the sentence needs the
condition in it. (Maintainer's correction, 2026-08-14; P-24.)

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
outlines, and a legend where the classes need one -- never an
abstract pattern, which shows the technique's mechanics rather than
its output and argues against the plugin's own claim that several
attributes of real places can be read from one map. Practically:
prefer the packaged Auckland deprivation data or another real dataset
over synthetic grids, keep the region outlines on, show a legend, and
size the image so the pattern is legible rather than decorative. A
figure from the published article is better still where its licence
allows; attribute it in the caption and record the licence beside the
file. (User instruction, 2026-08-08; P-25.)

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
release page alike, and the prose that names the download follows the
artefact; releases already published keep the asset names they went
out with. **And no CHECK writes into `dist/`**: `check_before_push`
replays the packaging step, so it builds into a temporary directory,
having once left an unversioned zip in `dist/` three bytes different
from the published candidate. (P-12.)

## Release bodies wrap; the changelog does not

**A GITHUB RELEASE BODY PRESERVES SINGLE NEWLINES.** Notes
hard-wrapped at the usual 72 columns therefore arrive as literal line
breaks, and on a phone a sentence snaps mid-clause: "nothing is
promoted," ending one line while `main` begins the next. The renderer is
never allowed to wrap to the reader's width. So **write each paragraph
of a release body as ONE long line**, and keep hard newlines only where
the markup needs them -- headings, list items, tables, block quotes.
**AND metadata.txt IS THE OPPOSITE, deliberately.** QGIS's plugin
manager shows that text AS IT STANDS, so a long line runs off the panel
and the entry must stay wrapped. (P-5.)
