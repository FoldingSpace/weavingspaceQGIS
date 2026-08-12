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

## Needs the maintainer, not the assistant

**An OSGeo user ID**, for submitting to plugins.qgis.org. It belongs
to a person rather than to the software; register at id.osgeo.org and
the plugin is owned by that account.

**Two things to say out loud in that submission**, both already true
and both better disclosed than discovered: the vendored MIT-licensed
library under `weavingspace_qgis/vendor/`, and `deps.py` fetching
wheels from PyPI when QGIS lacks them. Plugins get rejected for
hiding the second, not for doing it. Full detail in
docs/PUBLISHING.md.

## 0.24.1 — next

### Branch-backed

### Wanted, no code yet

nothing outstanding.

The docstring audit was done on 2026-08-12 and is deleted rather than
marked done, as this file says to do. What it found is worth one line
each, because the pattern will recur: two PRODUCT defects, not just
stale prose -- 0.24.1's only user-visible change never reached a
user, and two modal dialogs sat on a path that forbids them -- plus a
rule in check_standards.py that asserted its own enforcement and had
none.

The mechanisable quarter of it is now permanent:
check_args_blocks_match_signatures runs with the other standards
checks, and found a gap in its first run. The other three kinds --
behaviour that changed, a measurement since re-measured, a why naming
a bug now fixed -- need reading, and were read.

## 0.24.2 — waiting on somebody else

Everything here is blocked on the upstream weavingspace project
rather than on this repository, which is why it is not 0.24.1: a
release should not wait on a conversation we do not control. Moved
here 2026-08-12 at the maintainer's instruction.

### Wanted, no code yet

**Element ids past 26.** Blocked upstream rather than here. Weaves are
specified as strings with one character per element (`abcdef-|ghijk-`),
so doubled letters have nowhere to go, and case-distinguished ids
collide on every path that folds case — GeoPackage table names,
case-insensitive filesystems, saved layer properties. Going further
means changing the weave string format upstream and in every stored
design. Worth raising with the weavingspace project before anyone
attempts it.

**Two conversations with the upstream repository.** Whether the corrected
large-plain-weave note was sent (dev/upstream-note-large-plain-weaves.md
supersedes the first, which blamed a commit wrongly). And the
element-id ceiling below, which is upstream's decision rather than
ours.

## Later, or never

**Deriving the aggregate coverage from the per-test record** (was
`for-0.24.1/coverage-dedupe`, commit 34dab50bd0cd, branch deleted
2026-08-12). It made `coverage_report --from-record` write the
aggregate from what the per-test recorder already collected, so the
suite would not run twice under monitoring.

Dropped because its premise went away the same week it would have
landed: both coverage stages left the release path, so nothing
automatic measures twice any more. What remains is a saving for
somebody who deliberately wants the per-test record AND the aggregate
report in one sitting, which is rare and chosen. Against that it
needed a rebase across three files that were rewritten the night
before -- the recorder now writes only what a shard ran and survives
the suite's os._exit, the merger now salvages an empty-duplicate set
-- and a careless rebase would have silently undone one of those. Its
own precondition, a derived report compared against a measured one,
was never met either.

The commit is recoverable by hash if the premise returns, which it
would if the aggregate report ever went back into an automatic
process.


**Badges on the README**, and the "minimalist faux 3d" button styling
the user mentioned. Both cosmetic, neither designed.

**The custom ("this") weave type**, with its tie-up, treadling and
threading matrices. Deprioritised rather than rejected: it needs a
matrix-entry UI and its own documentation.
