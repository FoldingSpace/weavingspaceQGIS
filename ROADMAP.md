# Roadmap

What is going into which version, and what is merely wanted. Two
kinds of entry live here and the difference matters:

**Branch-backed** — the work exists, on a branch named
`for-<version>/<slug>`. The release process finds those branches by
name and refuses to build a candidate for a version while any of them
is unmerged, so nothing written for a release can be forgotten out of
it. Merging is the act that closes the entry.

**Wanted** — no code, sometimes no design. Recorded so that a good
idea survives the session that had it, which is the failure this file
exists to prevent: the ones that were only ever mentioned in a
conversation are gone.

Both kinds are checked before a candidate. An entry under the version
being released must be DONE, MERGED, or deliberately moved to a later
section — and moving it is a decision for the maintainer, not
something the release script may do on anyone's behalf.

Delete an entry when it lands. This file describes what is still
owed, and an entry nobody removes turns it into a diary.

## How to use this file

**WHEN.** The moment you notice something you are not doing now. That
is the whole discipline, and the failure it prevents is specific:
the ideas this project has actually lost are the ones that were
mentioned once, in a conversation, while somebody was busy with
something else. An entry costs thirty seconds and does not need to be
good.

**A thing you are NOT going to build yet** goes under the version you
think it belongs to, as a bold-titled paragraph saying what it is and
why it is not being done now. No branch, no design, no estimate.

**A thing you have BUILT for a later version** gets a branch:

    git branch for-0.24.1/<short-slug>          # name it for its version
    # work on it, or cherry-pick what is already written

then a paragraph naming that branch. Say what must be TRUE BEFORE IT
MERGES if anything must -- a verification, a measurement, a decision
somebody owes. That sentence is the reason the entry exists rather
than the branch alone: a branch cannot tell you it is unfinished.

**Deferring** is moving an entry to a later section. It is the
maintainer's decision and no tool will make it, which is why
`tools/check_roadmap.py` refuses rather than reschedules.

**Deleting** is what you do when it lands. A roadmap nobody prunes
turns from a statement of what is owed into a diary of what once was.

**The phrase the checker reads is "nothing outstanding"**, in the
version's own section, and it means nothing outstanding IN CODE. A
section may still list process items underneath -- an account
somebody must register, a setting in a web UI, a conversation with
another project -- and those do not block a candidate, because a zip
should not be held up by a GitHub Pages setting. Work that would
CHANGE THE SOFTWARE does block, and belongs above that line or on a
branch.

**Every version with a branch must have a section.** The checker
enforces it: a `for-<version>/*` branch whose version is not
described here is work parked with nothing to say what it is, which
is how a branch becomes archaeology.

---

## 0.24.0 — the release in progress

Nothing outstanding in CODE. Everything written for this version is
merged, and the checker reads this line rather than the list below,
which is process rather than work.

What remains is the release sequence itself: rc5 builds, somebody
makes a map with it, then promotion (`python3 release.py`), the tag,
and `--push` for the GitHub Release with the zip, testing report and
comparison PDF attached. Built in full, without `--quick`, so the
artefact that is promoted carries every measurement including the
coverage report.

## Needs the maintainer, not the assistant

**Enable GitHub Pages**, once: Settings -> Pages -> Deploy from a
branch -> main, folder `/docs`. Until then the project page 404s and
the README links to nothing.

**An OSGeo user ID**, for submitting to plugins.qgis.org. It belongs
to a person rather than to the software; register at id.osgeo.org and
the plugin is owned by that account.

**Two things to say out loud in that submission**, both already true
and both better disclosed than discovered: the vendored MIT-licensed
library under `weavingspace_qgis/vendor/`, and `deps.py` fetching
wheels from PyPI when QGIS lacks them. Plugins get rejected for
hiding the second, not for doing it. Full detail in
docs/PUBLISHING.md.

**Two conversations with the upstream repository.** Whether the corrected
large-plain-weave note was sent (dev/upstream-note-large-plain-weaves.md
supersedes the first, which blamed a commit wrongly). And the
element-id ceiling below, which is upstream's decision rather than
ours.

## After the release, agreed sequence

**Dispatch the mutation instruments remotely** and triage what they
find into `pre-0.24.1rc1`. They report rather than gate, so nothing
here holds a release:

    bash tools/watch_remote_mutation.sh <branch> both v0.24.0

**Run the gallery experiment**, which is coded and has never been
run. It answers whether the visual gallery's Delta-E thresholds
survive a different font stack; if they do, the rendered report
becomes available on three QGIS versions instead of one.

    bash tools/watch_remote_mutation.sh <branch> gallery

## 0.24.1 — next

### Branch-backed

**`for-0.24.1/coverage-dedupe`** — stop measuring coverage twice.
`coverage_report.py` and `coverage_per_test.py` used the same
mechanism (`sys.monitoring`) and differed only in attribution, so the
suite ran under monitoring twice: about forty minutes and fifty, for
two views of one measurement. The per-test recorder now collects
branch events too, and `coverage_report --from-record` writes the
same report from what is already on disk.

BEFORE MERGING: run a candidate both ways and compare the derived
report against the directly-measured one. A derivation that is nearly
right is worse than the duplication it replaces, because it looks
like a saving while quietly misreporting. The line half can be
checked against any candidate that produced both artefacts; the
branch half needs a run with the new recorder.

**`for-0.24.1/publish-from-main`** — stop a release being published
from the wrong branch. `release.py --push` runs `git push origin
HEAD`, so it sends whatever branch you are standing on, and a tag
does not care what branch it is on. Promote from a pre-candidate
branch and you get a perfectly real GitHub Release beside a project
page and a README that still describe the previous version, because
Pages serves `docs/` from `main`. Nothing in git objects. The branch
adds a refusal naming the exact fast-forward, a test, and the
sequence written out end to end in docs/PUBLISHING.md.

BEFORE MERGING: nothing outstanding. It was written and verified
while 0.24.0 was still building, so it is parked rather than
unfinished — merging it into 0.24.0 would have meant editing the
release script during its own release, which is how three candidates
died that evening. If 0.24.0 is published before this lands, do the
checkout by hand: `git checkout main && git merge --ff-only
pre-0.24.0rc5`, which is exactly what the gate would have told you.

### Wanted, no code yet

**Write the tests for the ten survivors the guard found before it was
stopped.** This is the work that the incremental guard moving out of
the release path hands to 0.24.1, and it is the reason that move is
not a weakening. Measured 2026-08-11 against `pre-0.24.0`, 28 of 80
mutants judged, 16 killed:

    bridge.py:520    compare <= -> <      (6 covering tests)
    catalog.py:295   number 0 -> 1        (221)
    catalog.py:307   number 37 -> 38      (221)
    dialog.py:3068   number 0 -> 1        (3)
    dialog.py:3200   number 7 -> 8        (1)
    dialog.py:3345   compare == -> !=     (20)
    dialog.py:3391   compare == -> !=     (1)
    dialog.py:3508   call removed         (1)
    dialog.py:3630   compare == -> !=     (4)
    dialog.py:4385   number 1 -> 2        (153)

Read them as a FAMILY before writing anything, exactly as
docs/TESTING.md says: several are a default or a constant nobody
pinned, and the answer to those is one table-driven test over the
whole family rather than ten example tests. And each one still has to
pass the two questions — name the harm a user would suffer, and would
we have wanted this test anyway — or be accepted with the reason
written down. `bridge.py:520` is the one to look at first: a boundary
comparison in code that decides what a map draws is a different
animal from a spacing default.

**Resume does not understand a stage whose product is a FILE.**
`skip_if_already_done` reads back a stage's captured text, so it can
honestly skip the suite or the gallery. It cannot skip the per-test
coverage record, because that stage's value is the shard files the
merge consumes — and the merge deletes them on success. Skipping the
record therefore leaves the merge with nothing and aborts the run,
which is a trap rather than a saving. Give a stage an optional
declared ARTEFACT, and let it be skipped only when the artefact is
present; record and merge would then share
`reports/per-test-coverage.json` and skip or run as a pair. Found the
same night resume was built, by nearly falling into it.

**One watcher, not a fresh script each time.** Five separate watcher
faults in one day (2026-08-11), all in scripts written while
attention was on the thing being watched: one repeated itself, one
read a stale log after a restart, two matched the wrong process for
their CPU field, one reported the previous run's CI result. Each was
individually trivial and the pattern is not. A single supervised
watcher — resolve the log freshly, report change rather than state,
name the process it is measuring, stop when the thing it watches
ends — would have prevented all five.

**Ceilings sized from measurement rather than belief.** Three were
set wrong in one day, each producing a red result that meant nothing:
a forty-minute CI job limit against 52-54 minute legs, a
600-second per-test watchdog against a test that legitimately takes
855 under coverage, and the same watchdog against a suite whose costs
multiply by six when monitored. There is a general fix available:
have the suite record each test's duration and size the ceiling from
the slowest observed run rather than from a constant somebody chose.

**Element ids past 26.** Blocked upstream rather than here. Weaves are
specified as strings with one character per element (`abcdef-|ghijk-`),
so doubled letters have nowhere to go, and case-distinguished ids
collide on every path that folds case — GeoPackage table names,
case-insensitive filesystems, saved layer properties. Going further
means changing the weave string format upstream and in every stored
design. Worth raising with the weavingspace project before anyone
attempts it.

**Antivirus cost on the macOS suite, measured rather than assumed.**
Cisco Secure Endpoint was using ~26% of a core across two processes
while the suite ran, and this suite creates and deletes thousands of
short-lived files. One timed run with the scratch directory excluded
against one without would settle whether that is a real tax or
background noise.

**Audit the docstrings and inline comments across the whole
codebase.** The documentation standard says every reachable function
carries a docstring naming its inputs, its outputs and what was
mutated, and that comments sit at the points a reader would otherwise
stop and wonder. `check_standards.py` enforces the PRESENCE of those
things; nobody has read them for TRUTH since they were written.

That distinction matters here more than in most projects, because
this one's standard makes stale documentation actively harmful: a
docstring is the only account of why a line takes the shape it does,
and a wrong one is followed with confidence. A previous audit of a
much smaller surface found three outright lies -- libs "appended",
live update "after first Generate", a box that had been removed --
and the code has moved a great deal since.

What to look for, in order of harm: a docstring describing behaviour
that changed; a comment citing a measurement that has since been
re-measured (several dates and figures were revised today alone); a
"why" that names a bug now fixed, or a workaround now removed; and an
Args block that has drifted from the signature. Doing it per module
with the tests open beside it is the only way it stays honest.

**The note line is asserted NEGATIVELY in at least one place, and a
cleared note passes that trivially.** `_note_after_a_run` fixed the
two positive assertions that read the note after a run; the negative
one near it -- "categories" must NOT appear -- is satisfied just as
well by a note the plugin cleared a moment earlier, which is the
vacuous-test shape this project produces at about one in five. Sweep
every read of `live_note` and decide, per site, whether it needs the
sampling helper, a recorded message-bar assertion, or nothing.

**The progress chart draws stages the run will not execute.** Under
`--quick` it still lists the 31-minute coverage report among the
stages to come and adds it to the estimate, so the finishing time it
prints is about half an hour pessimistic. It misled twice on
2026-08-11. Display only -- no measurement is affected -- which is
why it was not fixed in the middle of a release.

**Backfill discovery shapes on the 33 bug-register entries** that
predate the convention.

## Later, or never

**Badges on the README**, and the "minimalist faux 3d" button styling
the user mentioned. Both cosmetic, neither designed.

**The custom ("this") weave type**, with its tie-up, treadling and
threading matrices. Deprioritised rather than rejected: it needs a
matrix-entry UI and its own documentation.
