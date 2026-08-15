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

## 0.24.3 — next

Work done straight on `pre-0.24.3rc1` rather than on a `for-` branch,
because it is this version's work and not a parking place. Delete each
entry as it lands.

### Wanted

Nothing outstanding. The three measurement entries that stood here
were deferred to 0.24.4 by the maintainer on 2026-08-15: none is a
defect, and one of them -- the certification batch -- cannot honestly
run against this version at all, because a mutation score is a
property of a suite and this suite changed a dozen times on the day
the release was prepared.

## 0.24.4 — after this one

### Wanted

Deferred from 0.24.3 on 2026-08-15. All three are MEASUREMENT: they
say how good the suite is rather than whether the plugin is right,
so none of them blocks an artefact.

**Sampling the six unsampled assignment-lookup copies.** Deferred here
from 0.24.2 deliberately: it is measurement rather than
defect-finding, and the night of 2026-08-13 put mutation sampling at
zero product defects across 128 survivors. `_assignment_for` now holds
the lookup, so a future mutant has one place to land.

**Three things the 2026-08-13 instruments audit left undone**, all of
them about tools that produce numbers people then believe. (The
fourth landed on 2026-08-15: `check_standards` now reads every
catalogue entry with `ast` and fails when its anchor is absent, after
seven entries were found anchored on text that no longer existed. It
is asked at push time rather than inside `mutation_check`, which is
where the original entry wanted it -- a sweep run by hand still gets
no preflight, and that is the part left standing.)
`check_standards` compares only the COUNTS in the derived
documents where the generators' own `--check` catches more. Three
`EQUIVALENT` entries exclude nothing. And `mutate_auto`'s watchdog
ignores a child's CPU, so it can score a live mutant as stalled --
the same shape as the two stalls that turned out to be hiding
survivors, which is why the campaign work list also asks that a stall
not count toward a printed rate until it has been re-judged alone.

**Two mutation measurements, neither of them defect-finding.** The
expensive stratum, which nothing has ever measured -- 1,172 of the
1,488 reachable mutants, and the cheap stratum's 59% says nothing
about them. And a certification batch, once the suite stops changing,
since improvement rounds cannot certify themselves.

## Waiting on the upstream project

Blocked on the weavingspace project rather than on this repository, so
no release waits for it.

**Element ids past 26.** Weaves are specified as strings with one
character per element (`abcdef-|ghijk-`), so doubled letters have
nowhere to go, and case-distinguished ids collide on every path that
folds case. That last part is now measured rather than argued: writing
`tiles_a` and then `tiles_A` into one GeoPackage leaves a SINGLE table
holding the second element's data, and both writes report success
(2026-08-14). Going further means changing the weave string format
upstream and in every stored design.

**Two conversations to have.** Whether the corrected large-plain-weave
note was sent (`docs/process/upstream-note-large-plain-weaves.md`
supersedes the first, which blamed a commit wrongly), and the
element-id ceiling above, which is upstream's decision rather than
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
nothing compared those views systematically.

PART OF THIS IS NOW BUILT, which narrows what is left rather than
closing it. `test_random_designs_keep_their_views_in_agreement` covers
three of the pairs below -- the ramp cell, the row's assignment, and
the preview -- across random designs. What it does NOT cross is a
BOUNDARY, and the boundary crossings are where this project's evidence
says the value is: the saved project, the GeoPackage, and the colour
editor's listing. Those are the three worth building next.
`tools/equivalence_scenarios.py` dumps most of what they need.

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
