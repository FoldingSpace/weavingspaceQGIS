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

**DECIDED 2026-08-13, and mostly done.** The maintainer's answer:
preserve the row across a save where we can, and where we cannot,
reload the classes, count them, and call the row Custom. Implemented
the same day — the ramp and the class count are read back off the
renderer QGIS saved, which stores nothing new and treats the layer as
the authority exactly as opacity does; where no library ramp draws
what the layer draws, the class colours are recovered positionally
and the row reads Custom, which it already meant. The class count
also gained the per-element store every other control in that table
has had since the settled decision; it alone had been riding on a
widget property, which survives a rebuild and not a reopen.

What is LEFT is Reverse, and it is smaller than it looks. Reversing
produces a ramp clone matching no name in the library, so the flag
cannot be recognised from a renderer — but such an element comes back
as Custom carrying its actual class colours, so the map is exactly
preserved and no control claims a ramp that is not what is drawn.
Only the knowledge that those colours came from reversing is lost.
Closing it properly means teaching `_ramp_name_matching` to spot a
reversed clone; worth doing, not urgent, and the canary in
`test_a_project_round_trip_changes_nothing_a_user_chose` names it.
The scheme (Quantiles against Natural breaks) cannot be recovered
from breaks at all and is not attempted.

**The original question, kept for the reasoning.**
Measured 2026-08-13, with a canary now holding the answer in
`test_a_project_round_trip_changes_nothing_a_user_chose`: the ramp,
the reverse flag and the class count do NOT come back. They live in
session dictionaries nothing persists, while the layer carries all
three inside a renderer QGIS saves faithfully — so a reopened
project shows a table describing a map that is not on screen, and
since `_adopt_existing_group` leaves `_last_signatures` empty, the
next Generate re-seeds from the table and OVERWRITES the map. That
is the opacity defect fixed the same morning, one column to the
left, which is why it is a decision rather than a bug report: the
same reasoning applied to opacity says fix it, and it was found by
making three axes of that test live for the first time.

Three ways to go, and the choice is the maintainer's because it
settles what the plugin promises a saved project means:

- **Read it back off the renderer**, as opacity now is. Stores
  nothing new and became cheap the moment categorized renderers
  started recording their source ramp (also 2026-08-13). Recovers
  the ramp and the class count. Reverse needs ramp matching to
  recognise a reversed clone first, which it cannot do today; a
  scheme cannot be recovered from breaks at all.
- **Stamp the row** onto the layer as a custom property, like the
  hand-picked colours. Recovers everything including the scheme, at
  the cost of a second store of a fact the renderer already holds —
  which is the shape that produced today's other three defects.
- **Say it plainly instead**: the design tool starts fresh and the
  styling lives on the layers. Defensible, and already half the
  contract for variables, but then the table must not be allowed to
  overwrite the map on the next Generate, so `_last_signatures`
  needs adopting too.

Whichever way it goes, remove the names from `NOT_YET_RESTORED` so
the test starts requiring them.

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

## 0.24.2 — next

### Branch-backed

### Wanted, no code yet

**The changelog entry for 0.24.2 is DRAFTED and awaits review.** It
describes the live-update change that actually shipped in 0.24.1
whose notes said nothing else had changed, and says so plainly rather
than quietly. `metadata.txt` is in the text-review queue now, so it
is the maintainer's to approve.

**Triage whatever the incremental mutation run returns.** Dispatched
against `pre-0.24.1rc1` on 2026-08-12 after the candidate was built;
it had failed three times that day for three unrelated reasons, all
since fixed. Its findings belong here rather than to anything
shipped.

**Six of the nine assignment-lookup copies were never sampled**, and
the three that were each hid a real fault until a mutant happened to
land on that copy. `_assignment_for` now holds the lookup, so a
future mutant has one place to land -- but nothing has re-sampled
those sites since the refactor.

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


**A "two views of one truth" differential campaign.** Recorded here
rather than started, because it is a session's work and the case for
it is an argument about where effort pays rather than a defect
waiting to be fixed.

The plugin describes the same state in several places that must agree
-- the table, the design preview, the generated map, the colour
editor, and the saved project. Drive random designs, snapshot every
view, and require them to agree. A disagreement is a defect by
construction, so it needs no oracle and does not depend on the suite
being any good.

The case for it, in the record rather than in principle: nearly every
real defect this project has found came from comparing two
independent descriptions of the same thing (docs/TESTING.md, "What has
actually found defects here"), and the defect found on 2026-08-13 was
precisely a table-against-map disagreement that survived because
nothing compares those views systematically. Most of the machinery
exists already in `tools/equivalence_scenarios.py`, which was built
for mutation triage and dumps most of those views; pointing it at
random designs instead of at mutants is the whole change.

The pairs, and what a disagreement would MEAN, which is the part that
needs deciding rather than coding:

- the ramp cell against the element layer's actual renderer. A
  disagreement means the table is lying about the map. This is where
  the 2026-08-13 defect lived, and the cell read Custom while the map
  wore a clean ramp;
- the row's assignment (variable, style, class count) against the
  renderer's field and classes. A disagreement means the chooser
  describes a map the plugin did not draw, which is the failure
  "a quantitative style never stands on text" already guards at one
  point only;
- the design preview's colours against the element layers'. A
  disagreement means somebody judged a design from a picture the map
  does not honour;
- the colour editor's listing against the renderer's categories. A
  disagreement means the editor offers values the map lacks, or hides
  values it has;
- a saved project reloaded against the state before saving. A
  disagreement means stored work was lost or altered in the round
  trip;
- a GeoPackage reopened against the layers in the project. A
  disagreement means what a colleague receives is not what you see,
  which is the whole promise of the export.

Note what is NOT on that list: anything requiring an oracle. Every
pair is two descriptions the software itself produces, so the test
needs no expected value, no fixture of correct answers, and no
judgement about what a good map looks like. That is what makes it
cheap to run over random designs and what makes a failure
unambiguous.

Two cheaper differentials worth doing alongside, both nearly free now:
re-run the claims audit mechanically over the whole tree, since stale
prose reliably marks where behaviour drifted and that is where both of
2026-08-12's product defects came from; and a save-reload-compare,
because stored state is where hostile stored properties live.

**Badges on the README**, and the "minimalist faux 3d" button styling
the user mentioned. Both cosmetic, neither designed.

**The custom ("this") weave type**, with its tie-up, treadling and
threading matrices. Deprioritised rather than rejected: it needs a
matrix-entry UI and its own documentation.
