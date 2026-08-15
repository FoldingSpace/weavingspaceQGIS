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

**PINNED CLASS BOUNDS in the colour editor. Settled by `/grill-me` on
2026-08-14; every decision below is the maintainer's and should not be
quietly revisited.** A user may pin the first and/or last class and
type its inner bound by hand. Samples at or beyond a pinned bound
leave the pool, the scheme computes `k` minus the number of pins over
what remains, and unpinning recomputes that break as though it had
never been set. This is a familiar cartographic move -- everything
below X is one class, everything above Y is another, and the middle
is classed normally -- and it is what a reader needs when outliers
otherwise eat the ramp.

*How it is computed.* By extending the subset string
`make_graduated_renderer` already sets and restores for nulls and
non-finite values, so QGIS's own classifier goes on deciding every
break we do not pin. No reimplementation of quantiles, equal
intervals, Jenks or pretty breaks, for the reason recorded at that
function: owning four algorithms means four new ways to disagree with
the panel the user opens next.

*The ladder stays contiguous.* Pin the lower class at 10 where the
remaining samples start at 14 and the first computed class would
begin at 14, leaving 10 to 14 in no class at all -- so the outermost
computed edge SNAPS to the pin. Only that edge moves; the scheme's
internal breaks are untouched. It also settles Pretty breaks, whose
round numbers can sit outside the filtered range entirely. Without
the snap, a value arriving later in the gap paints as no data on a
map that looks perfectly fine.

*The shape of the record*, which the copy feature below shares and
extends: the boundary VALUES a person set, and a per-end PIN FLAG
saying which ends they pinned. For pins alone the two say the same
thing, and it is the copy that separates them -- so build the record
with both from the start rather than discovering it later.

*Ownership.* Keyed by tile id AND field, beside the hand-picked
colours, so switching a variable away and back restores the pins.
That makes a pin a per-element styling choice like the class count,
which is also per element -- so two elements showing one variable can
be pinned differently and will then class differently. That is
accepted deliberately: it is a choice the user made rather than
something the software did behind them, which is the distinction that
matters after the work of 2026-08-14.

*Lifetime.* Pins survive a change of scheme, class count, ramp or
reversal, since surviving a recalculation is the whole point. They
are STAMPED on the layer as a custom property, because nothing on a
renderer records that a break was chosen rather than computed;
without the stamp a reopened project would lose them and the next
Generate would overwrite the map, which is exactly how the opacity
and ramp defects of 2026-08-13 worked. A pin whose class is left
holding NO samples after the data moves is released, that break
recalculates normally, and the note line says which element and which
bound -- the rule shipped this version applied to pins, since a
legend must never show a class the map does not have, whoever put it
there.

*Guardrails.* REVERTED, with the cell restored and a word on the note
line: bounds that cross, a bound outside the data's range, a pin
leaving no samples for the middle. ACCEPTED and explained by the
existing notice: a pin leaving fewer distinct values than remaining
classes, which simply draws fewer classes through the reduction this
version already ships. One answer to "the data cannot support this
count", wherever the shortage comes from.

*Where it appears.* A pin column and editable bound cells on the
first and last rows of the editor's class table for the classed
styles, which widens that window; a clamp pair above the table for
Quant: Unclassed, beside the Ramp Display Range, because pinning row
0 of fifty faded slivers is a strange way to say "the ramp starts at
10". ONE stored record and ONE set of guardrails behind both
presentations, or this becomes a pair that drifts. Nothing whatever
in categorical dress, which has no bounds to pin.

*In the main table*, the element's ramp swatch draws a box around its
first and/or last stripe. The swatch already paints one stripe per
class, so this says "this end is yours" without the ramp cell having
to claim the ramp is no longer the ramp -- which it still is, since a
pin moves breaks and not colours. Two consequences: a pinned row's
swatch must come through the custom-swatch path so the stripe count
matches the class count, and the swatch cache key must carry the pins
or the box goes stale. On Unclassed, fifty classes are sampled down
to eight stripes, so the boxed stripe reads as "the low end" rather
than literally class 0.

*What must be true before it merges.* The bound rules and the snap
are tested in `bridge`, where they need no dialog. Above that: a pin
honoured end to end through a real run on each quant scheme and on
Unclassed; an unpin recomputing exactly the break it replaced; each
refusal proved to revert AND to report; a project round trip bringing
pins home, added to the differential that now covers everything else
a user chooses; and the categorical editor asserted to offer no pin
at all. Every new test gets a catalogue entry and must report
`caught`.

**COPY A CLASSIFICATION FROM ONE ELEMENT TO ANOTHER. Settled by
`/grill-me` on 2026-08-14, and it is built AFTER the pinned bounds
above, on the record that work creates.** A "Copy to..." dropdown at
the top of the colour editor, listing the other elements this one may
be copied to and reading "Copy to..." until it is used. Picking one
sends this element's class breaks, its colours, its pin status and its
class count to that element.

*What a copy IS, and why it is the same mechanism as a pin.* A full
set of copied breaks is every boundary pinned at once, so it is stored
in the SAME record the pins use, with pins as its two-ended case.
Copied breaks therefore survive every recalculation, stamp onto the
layer, and come home through a project round trip exactly as pins do.
One store, one set of guardrails, one thing to test; two stores of one
fact is the shape that produced three defects here on 2026-08-13.

*That record holds TWO things, and the difference is what makes the
copy behave.* The boundary VALUES a person set, and a per-end PIN FLAG
saying which ends they pinned deliberately. A copy carries both -- the
maintainer's instruction, 2026-08-14 -- and they are not the same
statement. Copying from an element with no pins leaves the target's
breaks hand-set and NEITHER end pinned, so its swatch draws no box and
its editor shows no pin: the target looks like what was copied, which
is the whole point. Collapsing the two would make every copy look
fully pinned and would leave "unpin" with nothing coherent to do.

*A copy degrades to its pins rather than to nothing.* Changing the
target's class count or scheme clears the copied VALUES with a notice,
since the copy was made for that count and those breaks -- but the pin
flags and the two bounds they name SURVIVE, and the scheme recomputes
the middle around them. A pin is a smaller and more durable statement
than a whole imported ladder, and this is the mechanism the pins
already provide doing exactly its job.

*The style travels with the breaks.* Copying from an Unclassed element
makes the target Unclassed, and copying from a five-class quantile
element makes the target classed at five. It is the only way "breaks
and number of classes" can be honoured in both directions: fifty
hand-set breaks on a row whose spinner caps at twenty is exactly the
three-numbers-for-one-setting fault
`test_an_unclassed_excursion_leaves_the_count_alone` already guards.

*The ends are fitted to the receiving data* (the maintainer's own
specification): the highest class's upper bound and the lowest class's
lower bound become the target column's max and min. Where the target's
max is BELOW the upper class's lower bound, the two are made equal, so
that class collapses; likewise where the target's min is above the
lower class's upper bound, the lower class's lower bound is set to its
upper. Since breaks are now cut from the region's values for a field,
two elements on the SAME variable share a data range and none of this
bites -- these rules exist for copying ACROSS variables, which is the
case the feature is really for.

*Interior breaks stranded outside the target's data are KEPT, and the
swatch says so with light diagonal hatching over the stripes no tile
can wear.* Copying v3's breaks onto an element carrying v1 leaves
several classes the data cannot reach; dropping them would be the
tidier answer and was rejected deliberately, because the copy is
supposed to reproduce a classification and a silently shortened one
does not. The hatch is what makes the emptiness visible rather than
silent, which was the only real objection to keeping them. It marks
ANY class no tile wears, so it covers the collapsed ends above as
well. Two limits to state plainly: it is a plugin-UI affordance, since
QGIS draws its own legend from the symbol and hatching that would
change the map rather than describe it; and it belongs in the editor's
class table as well as the main table's swatch, or the emptiness is
only visible from the window the user has just left.

*No collision with the class-count reduction.* Hand-set breaks bypass
the classifier entirely, so "a column cannot be cut into more classes
than it has distinct values" still governs every break the software
COMPUTES and never overrules one a user imported.

*Overwriting.* The copy lands at once and the map repaints while the
window is open; the note line names what was replaced ("element c's
four hand-picked colours and its low pin were replaced by a copy from
element a"). Reported, never silent, and never asked -- the habit
every other loss in this plugin follows.

*Two details settled without asking, recorded so they can be
overturned deliberately.* The dropdown returns to reading "Copy to..."
after each use, and copies to one element per pick rather than
offering a multi-select, because a destructive action reads better one
target at a time. And an element carrying no variable is not offered,
having no column to classify.

*What must be true before it merges.* The pinned-bounds work above
must be in, since this is stored in its record. Then: a copy proved
end to end across two elements carrying DIFFERENT variables, with the
end-fitting rules measured on both degenerate cases; a copy from an
Unclassed element proved to make its target Unclassed and back again;
the PIN FLAGS proved to arrive with the breaks, and proved ABSENT on
the target when the source carried none, since a test that only ever
copies from a pinned element cannot tell the flag from the values;
a count change on a copied target proved to keep the pins and drop
the rest;
the hatching asserted to appear exactly on classes no tile wears, and
to disappear when the data changes so that they do; the notice proved
to REACH a user through the message bar, not merely to exist, which is
the fault this session met twice; and the dropdown asserted to be
absent altogether in categorical dress. Every new test gets a
catalogue entry and must report `caught`.

**Sampling the six unsampled assignment-lookup copies.** Deferred here
from 0.24.2 deliberately: it is measurement rather than
defect-finding, and the night of 2026-08-13 put mutation sampling at
zero product defects across 128 survivors. `_assignment_for` now holds
the lookup, so a future mutant has one place to land.

**Four things the 2026-08-13 instruments audit left undone**, all of
them about tools that produce numbers people then believe. The
catalogue's entry validation is a script somebody ran once, and
belongs in the tool as a preflight that refuses to judge a broken
entry. `check_standards` compares only the COUNTS in the derived
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
