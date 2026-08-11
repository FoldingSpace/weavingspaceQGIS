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

   Edit, run single tests there (`dev/run_some.py` derives its own
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

The one thing that cannot be parallelised is a MEASUREMENT beside
another measurement: the sweep, the census and the suite each want
the machine to themselves, and contention inflates per-unit times by
15-50%. CI is on somebody else's hardware, which is exactly why it
composes.

## What to do BEFORE a candidate, and what not to

Not much, and less than instinct suggests. The gates run
cheapest-first -- standards, secrets, then the functional suite --
so a broken suite stops a candidate about twenty-four minutes in.
Running the suite (or coverage, or the gallery) standalone first
gives no earlier warning and doubles the wait. Iterate with
`dev/run_some.py` on the tests you are actually changing, then go to
`python3 release.py --rc`.

Two things DO belong first, because the gates check them rather than
produce them:

    python3 tools/test_map.py
    python3 tools/bug_register.py

and a settled text-review queue (`python3 tools/text_review.py`,
reviewed and applied by the USER). A stale generated document stops
the build on a count mismatch, and no gate can approve prose on
somebody's behalf.

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

