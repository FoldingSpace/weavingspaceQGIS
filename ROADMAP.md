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

---

## 0.24.0 — the release in progress

Nothing outstanding. Everything written for this version is merged.

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

### Wanted, no code yet

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
design. Worth raising with David before anyone attempts it.

**Antivirus cost on the macOS suite, measured rather than assumed.**
Cisco Secure Endpoint was using ~26% of a core across two processes
while the suite ran, and this suite creates and deletes thousands of
short-lived files. One timed run with the scratch directory excluded
against one without would settle whether that is a real tax or
background noise.

**Backfill discovery shapes on the 33 bug-register entries** that
predate the convention.

## Later, or never

**Badges on the README**, and the "minimalist faux 3d" button styling
the user mentioned. Both cosmetic, neither designed.

**The custom ("this") weave type**, with its tie-up, treadling and
threading matrices. Deprioritised rather than rejected: it needs a
matrix-entry UI and its own documentation.
