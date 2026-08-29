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

**PROFESSIONALISED, USE-CASE DRIVEN USER TESTING.** (Colleague's own
words, 2026-08-25, closing a long report on the dataset-switch rules:
"this whole thing needs professionalised use-case driven
user-testing".) It is recorded here rather than acted on because it
is the one request in that conversation an assistant cannot fulfil:
every instrument this project has answers whether the plugin is
CORRECT, and none of them answers whether somebody can work out what
it is doing. The grilling of that day settled the rules on two
people's judgement, which is the best evidence available and is not
the same thing as watching somebody use it. Worth pairing with a real
demo of several datasets in a row, since that is the session that
produced every finding here.

**Two things to say out loud in that submission**, both already true
and both better disclosed than discovered: the vendored MIT-licensed
library under `weavingspace_qgis/vendor/`, and `deps.py` fetching
wheels from PyPI when QGIS lacks them. Plugins get rejected for
hiding the second, not for doing it. Full detail in
docs/PUBLISHING.md.

## 0.24.3 — released 2026-08-26

Published as `v0.24.3` from `main`, promoted from candidate rc21 with
its receipt rather than rebuilt. What follows is what the version
DELIVERS, kept because a reader arriving at this file wants to know
what the last release was for; everything it owed is done, and what it
never landed has moved to 0.24.4 below.

The record of how it was built is elsewhere and stays there: the
defect ledgers under `docs/process/`, sixty rows across 2026-08-17 to
26; the rulings in CLAUDE.md, where they bind; and the verification
lessons in docs/TESTING.md.

### What it gives you

**Areas with no value are drawn.** An area whose value is absent used
to come out as a hole. So did one holding an infinity, which a
classifier can no more place than a blank. Those areas are drawn now
and told apart — no data, infinity and negative infinity each get
their own colour, their own line in the legend, and their own entry in
that element's colour editor. QGIS gains a second layer beside the
element carrying them; the dialog still shows one element.

**You can set the class bounds yourself.** The box holding the first
or last class's inner bound is live whenever an element can carry a
pin. Move it off the computed value and the bound is yours, with the
classes between recomputed around it; move it back and it returns to
being worked out for you. Bounds may sit outside the data — that is
how one pair of limits can be given to several variables — and a
bound that cannot be DRAWN is refused with the reason said.

**A colour means the same thing everywhere.** An element is classed
from the whole map's values rather than from its own tiles alone, so
two elements set up alike can be read against each other. They could
not before.

**You can copy a classification** — classes, colours, pins and class
count — from one element to another in the same window. Where the two
carry different columns the ends are fitted to the receiving data, and
a class its values cannot reach is kept rather than dropped, so the
classification arrives whole.

### What it puts right

Forty-six defects, found and fixed over 2026-08-17 and 18, every one
with a regression test and a proved mutation-catalogue entry. Grouped
by what a user would have hit:

**Numbers you typed, quietly changed.** A class bound typed wider than
the data was truncated (1200 kept 120) and the map drawn from the
smaller number; a fine bound on a large column was rounded to a whole
one; Rotate, Skew and both angle boxes refused decimals, so 22.5°
became 22; a scale between −1 and 1 was mangled mid-keystroke, so
−0.5 silently un-mirrored a design. Under a comma-decimal locale three
separate sentences printed numbers their own boxes read differently.

**Work that disappeared.** A style pasted while a map was drawing was
destroyed as it landed; a copied classification was destroyed at the
instant of copying; pins set during a run were retired by a guard
reading the count the run STARTED with; and restyling an element in
QGIS erased its pinned bounds and hand-picked colours from the saved
project while the window still showed them.

**Edits made in QGIS that never arrived.** Change an element's breaks,
field, class count or ramp in the Symbology panel and the table went
on describing the old map — and the next Generate wiped the change.
A retyped break, a changed ramp, a stroke, a legend label and a
deleted category each reached the map and the project but never the
GeoPackage a colleague opens.

**A design view showing colours the map does not contain.** One
expression was wrong six ways: a deferring element's layer, the Ramp
Display Range, Reverse, hand-picked colours, a column with nothing to
classify, and a constant column. It reads what the map draws now.

**Things you should have been told.** A class with no areas in it went
unmentioned though four documents said otherwise; every Unclassed
element was warned a third of its fifty steps were empty; and where
two elements share a column, one element's notice silenced the other.

**A NO-DATA TWIN REPORTED ON COMPLETE DATA.** (Maintainer, rc16,
2026-08-24: the paired layer appears on the mosquito data though the
variable has no missing values.) MEASURED SO FAR: the source is clean
-- 3,011 features, no NULL, NaN or infinity in any column -- and the
creation gate (`if absent is not None and len(absent)`) held in two
read-only reproductions (4 and 23 elements, coarse spacing, default
options): zero twins. The split runs over the TILED frame, so a tile
the join hands no value is counted absent -- it would be a HOLE
otherwise, the very thing the twin abolishes -- which is the likeliest
route under the demo's own settings (icons mode or fine spacing).
THE HYPOTHESIS WAS MEASURED ON 2026-08-25 AND IS FALSE HERE. Fifteen
configurations on data proved clean: a dense grid at four spacings
from 2,000 down to 40 map units, icon mode coarse and fine, twelve
hundred areas at a fine spacing, and the three awkward shapes this
suite keeps for exactly this kind of question -- a donut, an L and a
sparse archipelago -- each at two spacings and in icon mode. NOT ONE
produced a twin. The route the entry guessed at is the one it can
rule out: the library CLIPS its tiles to the region, so a tile that
falls between areas is not a row with no value, it is not a row.

SO WHAT REMAINS IS THE MAINTAINER'S, and it is now a smaller
question than it was. Read the twin's FEATURE COUNT in QGIS on the
mosquito map: features present means real join-missed tiles that
nothing here can reproduce, and the question becomes whether the
LAYER'S NAME should say so ("no value at this spacing"); zero
features means a gate defect nobody has manufactured yet. Either way
the answer is one number, and this entry cannot close without it.
IT DOES NOT BLOCK A CANDIDATE: a paired layer that appears where
nothing is missing is a puzzle rather than a wrong map, and no
measurement available here reproduces it.

**CONFIRM THE GHOST NUMBERS ON A REAL SCREEN.** Deferred until after
the release by the maintainer, 2026-08-17, to be tested by the person
who reported it. The cause is removed — the Unclassed table is no
longer composited through a `QGraphicsOpacityEffect` and fades per
item through the palette's disabled colour — and guarded by
`test_the_unclassed_list_fades_without_a_graphics_effect` and the
catalogue entry `the-unclassed-list-is-not-composited`. What no test
here can say is whether the ghosts are GONE: they live in the window
system's backing store, where `grab()` repaints cleanly and a scrolled
render matched a force-repainted one across 32,900 sampled pixels. The
original report, kept so the check has something to check against: a
second, faint set of class bounds painted behind the live ones in the
Lower and Upper columns, offset by about a row, on scrolling.

## 0.24.4 — next

Worked on `pre-0.24.4rc1`. What follows is what the version owes.

**ONE LINE CARRIES 0.24.4**, since the two branches were merged on
2026-08-27: `for-0.24.4/copy-select-all`, which now holds the Save
work as well. `for-0.24.4/saving-is-an-act` is an ancestor of it and
is kept only so its history reads; nothing is owed on it.

WHAT THE VERSION HAS. The twenty-five defects of the hunt round, each
with a registered test and a proved catalogue entry; the Select all
button; the two element ceilings with `element_order` behind them;
and all five rulings of 2026-08-27 -- an output path never decides the
group, a ramp is remembered under the row's mode, donors are seeded
before their followers, saving is a positive act, and unticking
"Include the source data" takes it out of the file.

WHAT THE SAVE CONVERSION COST AND FOUND, because the ratio is the
argument for doing it that way again. Fifty-eight Save presses went
in by script where the old code's write used to happen; twenty-four
tests were converted BY HAND because what they assert changed rather
than moved; four tests were written that did not exist, one of them a
matrix of eleven routes to a press crossed with two shapes and three
aftermaths. Twenty catalogue entries are proved `caught`, two of them
guarding an ABSENCE by putting a deleted behaviour back, since there
is no line left to mutate.
IT FOUND FOUR REAL DEFECTS, three on ordinary journeys: a run
claiming a save it never made, a Save during the first run telling
somebody to press Generate, a region chooser excluding a newly loaded
layer for being allocated where a destroyed one had been, and -- the
worst -- a map opened with Load being DESTROYED by being saved.
Ledger rows 27 to 30.

WHAT IS OWED BEFORE A CANDIDATE: the full suite, which belongs to the
rc rather than to the working day (maintainer's instruction,
2026-08-27) and which shards three ways when it runs. The last whole
run was 636 passed and 7 failed at `844e6d4`; every one of those
seven is fixed, and the fixes are covered by targeted runs rather
than by a whole-tree measurement.

**THE DRIFTED CATALOGUE IS DONE**, decided entry by entry on
2026-08-28 and written up in `docs/process/catalogue-triage-2026-08-28.md`:
nine re-aimed or re-anchored and proved `caught`, twelve retired with
their measurement and the redundancy written at the test, four
accepted with the condition that would reopen each, and five tests
made materially stronger. The catalogue holds 548 entries where it
held 559. The finding worth carrying is that these were not weak
tests but facts that gained a SECOND WRITER as the fortnight's
rulings landed, which is how a catalogue loses a version's worth of
guards while its count goes on describing them.

**AND ONE DEFECT FOUND AFTER THE CATALOGUE ROUND**, fixed on
2026-08-28 and carried by `0.24.4rc3`. With live update off, a
Generate pressed while a run was in flight did nothing at all and said
nothing: the press was queued on the live-rerun flag and handed to the
live path, which declines whenever live update is off. The map kept
the elements of the run already going while the table described the
design just asked for, and layers were left tagged for elements that
design no longer had.
AND THE HARM IS THE SUITE'S RATHER THAN A USER'S, measured on the
evening of the same day: the Generate button is disabled for the whole
of a run, so no press can reach that state and only a direct call to
`_generate` does -- which is what the test that failed and
`test_race_double_generate` both do. The fix stands as defence in
depth, a press and a live tick being different facts; what was wrong
was the sentence around it. The changelog line this entry asked for is
therefore WITHDRAWN rather than owed, since a user did not meet this,
and the candidate's tester notes have to be rewritten before anything
goes out: they told testers to press a button the plugin greys out.
IT WAS FOUND BY THE SUITE RUN WHOLE, once, in a shard on a loaded
machine, and looked exactly like flakiness against fourteen clean
runs; what settled it was that the dialog had SETTLED before the
surplus layers were counted. Guarded by
`test_a_generate_pressed_during_a_run_is_not_swallowed` and the entry
`a-queued-press-is-a-press-not-a-live-tick`, both proved. The lesson
is in CLAUDE.md and docs/TESTING.md; the mechanism is in
MAINTAINING.md under "Two queues".
WHAT IT COST BESIDES: two existing tests read the moved record as
their premise and were repaired without changing their subjects, which
CI found and the targeted runs could not.

**A CHANGELOG LINE IS OWED BEFORE PROMOTION, AND IT IS THE
MAINTAINER'S** -- but not for the fix above, whose entry it was
originally written for and which a user never met. What 0.24.4's
`changelog=` entry should name is the round of 2026-08-28 recorded in
`docs/process/defects-2026-08-28.md`: a saved map recording the design
its own tiles were drawn at, a reopened project finding its own output
group however its folder is spelt, and whatever else that round
closes. Approving the wording is the user's act rather than an
assistant's. It does not block a candidate -- a candidate is for
feedback -- but it does block the build that gets promoted, since
`metadata.txt` ships and changing it retires a receipt.

**AND THE ROUND OF 2026-08-28, which is the largest this project has
run.** Twenty-three hunts kept at eight at a time and replenished as
each reported, with the consistency sweep rebuilt beside them as a
committed tool. Twenty-four confirmed defects, the ledger in
`docs/process/defects-2026-08-28.md`, the directions and what each
taught in `docs/process/HUNT-RECORD.md`.

WHAT IT GIVES A USER, in the order somebody would care. A saved map
now records the design and the variables its own tiles were drawn
with, so a colleague opening it is not shown a design nobody made and
does not lose the map to their first Generate. Opening somebody's
self-contained file and saving it keeps the copy of the data they
included. Opening a saved map with live update on -- the default --
no longer redraws it into memory and leaves the file's map empty next
time the project opens. Reducing a design and saving no longer leaves
the dropped elements' tables, columns and values in the file. A
project reopened under another spelling of its own folder finds the
output group its data made instead of piling a second one beside it.
A class bound survives a keystroke that types nothing. And a
256-element design draws in about two seconds where it froze QGIS for
thirty-eight.

WHAT IS STILL OWED FROM IT, and each is a defect confirmed by a hunt
and reproduced here rather than a guess: the design view's landing
repaint fires before the new layer exists; a floor or ceiling and the
colours after it are destroyed by a save-and-reopen before Generate,
because those stamps only happen as a side effect of a restyle that a
limit makes decline; pressing Load while your own polygon layer is
open replaces the sender's map with your data, across three coupled
sites; the duplicate-layer guard sits at the adoption door and not at
the landing door; deleting the output group and pressing Save empties
the file and reports success; two maps from two senders, where
returning to the first re-tiles it from the second's data; a shared
file somebody else has saved into while your map is open, where your
Save reports success and leaves the file with no map in it at all;
the group chooser describing a landing that will not happen whenever
"Create as new group" is ticked, because it knows one of the two
doors that arm it; and the catalogue triage of the same morning made
two trades whose compensating test legs cannot fail, one of which is
already mended.

**AND ONE QUESTION IS THE MAINTAINER'S RATHER THAN OUTSTANDING WORK.**
A quantitative style never stands on a text field, and the stated
reason is that a graduated renderer over text comes back with no
ranges. Measured on QGIS 4.0.3: true of WORDS, false of NUMERIC
STRINGS -- a String column running "10" to "120" classifies exactly as
its integer twin. So somebody whose numbers arrived through a CSV join
cannot draw a choropleth from them and is given one colour per value
instead. Whether a `str`-typed column should be classifiable is yours
to decide. What is not a decision is the second half: between a
graduated style built in QGIS's dock and the next Generate, the row
reads "Quant: Quantiles" while the assignment says Categorized, and
that Generate destroys the dock's work.

**WORK IS OUTSTANDING IN CODE, and it is the list two paragraphs
above.** This section said the opposite until the round of 2026-08-28,
and the phrase is withdrawn deliberately rather than left to be
satisfied by a heading: the release gate refuses a candidate while a
version's section lists work, and it is right to, because every item
on that list is a defect confirmed by a hunt and reproduced here. When
they land or are moved, the declaration comes back.

Everything the version carried BEFORE that round is done or
deliberately moved: the two that need a person rather than an
assistant are under "Needs the maintainer" above, the four
measurements and studies are under 0.24.5 below, and the changelog
line above is a sentence for the maintainer rather than work on the
software.
The branch that was superseded rather than owed, `for-0.24.4/save-load-tab`,
was deleted on the maintainer's decision the same day; its single
commit was `4a9cbfc`, the first Save & open tab, which ruling 1
overruled.

(The two rulings that stood here -- SAVING IS A POSITIVE ACT and
UNTICKING "INCLUDE THE SOURCE DATA" MEANS IT IS NOT IN THIS FILE --
are deleted because they LANDED, which is what this file asks of an
entry that is done. Their reasoning lives in CLAUDE.md, where it
binds, and what they cost and found is in the ledger for 2026-08-27,
rows 26 to 30.)

## 0.24.5 — deferred here from 0.24.4

Moved on the maintainer's decision of 2026-08-27, in the act of
cutting 0.24.4's candidate. None of it is abandoned and none of it
was blocking the version: three are measurements rather than
defect-finding, and the fourth is a study whose answer is written
at its own entry.

**FOR STUDY: warn when a test asserts a string that also appears in
shipped source.** Added 2026-08-16, deliberately as a question rather
than a rule. That is exactly what rotted that day: a test asserted
`"no value" in said`, the maintainer reworded the notice to "do not
have finite numeric data", and the test failed on every platform while
looking like a Windows fault -- a second copy of the wording with no
mechanism keeping the two in step. The repair was to compose the
expected text from the same function the product uses.

What is NOT known is whether a checker can tell that fragment from a
coincidence. Tests legitimately assert on words that appear in source
for unrelated reasons, so this would have to WARN rather than fail,
and a warning nobody can act on is one people learn to ignore -- which
this project has written down twice about other instruments. The study
is: run the comparison over the current suite, count how many hits are
real and how many are noise, and only then decide whether it earns a
place. If the noise is heavy the honest outcome is to drop it and keep
the practice in docs/TESTING.md, where it already is.

THE STUDY WAS RUN ON 2026-08-27, AND THE NUMBERS SAY DROP IT. Method:
every `assert` in the suite, every string literal inside its test
expression that is at least twelve characters and carries a space --
prose rather than an identifier -- checked against the shipped
package with `vendor/` excluded, that being upstream's wording rather
than ours. RESULT: of 104 such fragments, 56 also appear in shipped
source. More than half of the suite's prose comparisons would warn.
AND THE HITS DO NOT SEPARATE. The largest group is tests choosing a
CONTROL BY ITS VISIBLE TEXT -- `Quant: Equal intervals`, `Quant:
Quantiles` -- which is what a user does, and what this project's own
rule about driving a control through its own signal asks for. The
rest are message fragments, which is the shape worth warning about.
Nothing mechanical tells the two apart: both are strings in
`dialog.py`, both are user-facing, and the difference is whether the
wording is a LABEL somebody selects or a SENTENCE somebody reads.
SO THE RECOMMENDATION IS TO DELETE THIS ENTRY, keeping the practice
where it already is -- compose the expected text from the function
the product uses. Deleting an entry that never landed is a scope
decision rather than a tidy-up, so it stays here with its answer
attached until the maintainer strikes it.

**Give the stochastic hunt an exported-file invariant that RUNS.** Added
2026-08-16. A hunt over 105 checked steps reported its five axes:
holes 103, tile totals 103, opacity pairing 23, values-on-no-data 23,
and the GeoPackage comparison ZERO. That last axis never executed, so
a green run said nothing whatever about the exported file while
looking like full coverage. Counting what each invariant actually
compared is the practice worth keeping; an axis that never runs is
indistinguishable from one that always passes.

THE SAME GAP IS NOW CLOSED IN THE OTHER INSTRUMENT, which narrows
this entry rather than answering it. `test_random_designs_keep_their_
views_in_agreement` compared three same-session views and nothing
across a boundary; since 2026-08-27 it also SAVES each random design
and compares what the file HOLDS -- tile counts per element, and the
class colours the file's own embedded style paints -- against the map
on screen, asserting how many elements it actually compared, which is
the practice this entry is about. What is still owed is the same
invariant inside the STOCHASTIC hunt, which drives random action
sequences rather than random designs.

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
Three `EQUIVALENT` entries exclude nothing. And a stall must not
count toward a printed rate until it has been re-judged alone --
which is the half of this entry that still stands.
THE OTHER HALF WAS ALREADY DONE AND THE ENTRY DID NOT KNOW.
Re-reading `tools/watchdog.py` on 2026-08-27: it polls the child's
CPU and its output, and a stall is declared only when NEITHER has
moved for the whole window, which is precisely the "ignores a child's
CPU" fault this entry reported. The stall patience also widens with
CONCURRENCY, on a measurement of three mutants that "stalled" at
141-175s under three workers and ran to real verdicts in 1683-1855s
alone. What is left is the SCORING question -- a stall counts as
caught, so a false one flatters the rate -- and that is a campaign
commitment rather than a defect, so it belongs to a session that has
read docs/MUTATION-TESTING.md, which governs it.
(The third of them landed on 2026-08-27: `check_standards` compared
only the COUNTS in the derived documents, which is blind to a test
RENAMED, a purpose rewritten or an area re-assigned -- everything
that leaves the opening number alone while the document goes on
describing a suite that no longer exists. It renders both documents
through the generators' own `render()` now and compares the whole
text, naming the first line that differs so a failure is a work
list rather than a diff to go hunting through.)

**SHOULD A CATALOGUE ENTRY BE ABLE TO BREAK TWO SITES?** Raised
2026-08-28 while deciding the drifted entries, and recorded rather
than done because it is a change to campaign machinery in the middle
of a candidate. `tools/mutation_check.py` applies exactly ONE
replacement per entry, deliberately -- an entry names one site, and
mutating several would make its verdict mean nothing. But this
project's commonest defect shape is ONE FACT HELD IN SEVERAL STORES,
and three entries that round stood on one limb of a pair whose other
limb answers: a fallback chain, two readings a few lines apart, two
terms of one tuple. Where the sites are adjacent an anchor can cover
both. Where they are not -- the run signature's identity and
fingerprint terms are 47 lines apart -- no entry can, and the honest
outcome was a retirement.
An `also=[(old, new), ...]` field would let those be guarded, at the
cost of a verdict that no longer names one site. THE QUESTION TO
SETTLE FIRST is whether that is still a mutation test or has become a
feature test wearing one: breaking three sites at once and requiring a
failure proves the SET is live, which is exactly the weaker claim the
one-replacement rule exists to refuse. Worth an hour of thought and a
grilling before any code.

**Two mutation measurements, neither of them defect-finding.** The
expensive stratum, which nothing has ever measured -- 1,172 of the
1,488 reachable mutants, and the cheap stratum's 59% says nothing
about them. And a certification batch, once the suite stops changing,
since improvement rounds cannot certify themselves.

## Waiting on the upstream project

Blocked on the weavingspace project rather than on this repository, so
no release waits for it.

**Element ids past 26, FOR WEAVES ONLY.** The tiling half of this
entry LANDED on 2026-08-27 and what remains is the weave half, which is
genuinely upstream's. Three routes were set out here rather than one,
because compressing them is how the reasoning gets misremembered, and
they stop in three different places.

*Using the capitals as well* — a..z then A..Z, 52 ids — is blocked by
GEOPACKAGE CASE FOLDING, and that part is measured rather than argued:
writing `tiles_a` and then `tiles_A` into one file leaves a single
table holding the second element's data, with both writes reporting
success (2026-08-14). Any other case-insensitive path waits with the
same fold. This route is not difficult; it is closed.

*Doubling the letters* — a..z then aa, ab.. zz, 702 ids — is NOT
blocked by the GeoPackage: `tiles_aa` and `tiles_ab` stay distinct
however case is folded. It is blocked by the WEAVE STRING FORMAT, in
which one character means one element ("abcdef-|ghijk-"), typed by
users and stored verbatim in `catalog.py`. Upstream's code makes it
concrete: the strand count is `len(ID)` and the ids are `list(IDs[i])`,
so "ab" already means two strands, a then b.

WHAT UPSTREAM SETTLED, read on 2026-08-18 and MEASURED against the
vendor on 2026-08-25 once the jump was taken. weavingspace 0.0.7.89
supplies tile ids from `TILE_IDS = [a..z, aa..zz]`, used only in
`_tiling_geometries`; `weave_unit.py` never touches it. Measured
against the vendored copy: 702 ids, all lowercase, no capitals
anywhere, and a request for 710 elements comes back with 702
silently. So for TILINGS both blockers are off — upstream provides
the ids, and doubled lowercase survives the GeoPackage. For WEAVES
the format is still the obstacle, and changing it is upstream's
decision rather than ours, which is why this entry stays in this
section, narrowed to that half.

AND THE READING THAT SAID IDS HAD BECOME CASE-SENSITIVE WAS WRONG.
The 0.24.3 entry above carried it from a commit message, and it
pointed the opposite way — toward capitals colliding. Measuring the
vendor settled it. Kept here because this entry's own opening says
compressing the reasoning is how it gets misremembered.

IT BECAME OURS ON 2026-08-27, and this paragraph replaces the
prediction that stood here. The maintainer ruled the two ceilings
apart: weaves keep `a`..`z`, tilings run `a`..`z` then `aa`..`zz`
capped at sixteen by sixteen, so `catalog.py` now carries
`MAX_ELEMENTS_WEAVE`, `MAX_ELEMENTS_TILING` and an alias, where this
entry used to say one number served both. The reasoning is in
CLAUDE.md under "TWO ELEMENT CEILINGS, NOT ONE" and the code is on
`for-0.24.4/copy-select-all`.
THE PREDICTION WAS RIGHT ABOUT WHERE THE WORK WOULD BE. It said the
work is not the number but auditing everything that assumes an id is
one character, and that is exactly what it was: `"aa" < "z"` compares
character by character, so the twenty-seventh element sorted SECOND in
the assignment table, the layers panel, the design view's labels, the
legibility pairs, and again in a resumed panel where table names carry
the same fault. `bridge.element_order` owns that question now.
WHAT IT WAS WRONG ABOUT is the last line, which said nobody had asked
for a twenty-seventh element. Somebody did, and a roadmap entry
predicting the absence of a request is a sentence with a short life.

**Two conversations to have.** Whether the corrected large-plain-weave
note was sent (`docs/process/upstream-note-large-plain-weaves.md`
supersedes the first, which blamed a commit wrongly), and the WEAVE
half of the element-id ceiling above, which is upstream's decision
rather than ours now that the tiling half is built.

## Later, or never

**CANCEL A RUN THAT IS ABOUT TO BE SUPERSEDED.** The third of the
three debounce questions, and the only one the decision of 2026-08-26
left open. The other two are settled: the preview wait is a floor that
widens to whatever a rebuild costs, and the two debounces stay
separate.

WHY IT IS NOT DONE HERE. The live interval is 900 ms because it guards
something genuinely expensive -- 229 ms of CPU on a sixteen-polygon
fixture, seconds on three thousand areas -- and the honest way to
shorten it is to make a superseded run STOP rather than to start the
next one sooner and have two in flight. That is a change to the run
lifecycle rather than to a number: `QgsTask` cancellation, what a
cancelled run does to the group it was going to land in, and the
existing rule that a run is not over until its layers exist. It wants
its own round with its own races tested, and it would be the wrong
thing to fold into a candidate whose gates are about to measure
everything else.

WHAT WOULD MAKE IT WORTH DOING: a report that the map itself, rather
than the preview, still feels slow to iterate with. The preview is
what tells somebody their input registered, and that half is now as
fast as the machine allows.

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

**THE TEXT-REVIEW QUEUE SHOWS THE MAINTAINER THINGS THEY CANNOT
JUDGE.** (Maintainer's observation, 2026-08-26: an SQL statement --
`DELETE FROM layer_styles WHERE f_table_name = '%s'` -- reached the
queue, and "that string is irrelevant for me to approve".) Recorded
rather than acted on, because the fix is not obviously an
improvement: the filter is deliberately over-inclusive, and the day
it skipped strings opening with `{` it dropped three live
user-facing sentences unread. So the question is whether a rule
exists that admits SQL and internal identifiers while admitting
nothing a person meets -- "contains a space and no SQL keyword" is
the sort of guess that fails on the first sentence carrying a table
name. A study, in the shape this file already prescribes for the
assert-a-shipped-string idea: run the candidate rule over the whole
corpus of 312 approved pieces, count what it would have hidden, and
only then decide. What must NOT happen is the queue being narrowed
to make review pleasant, which is how a gate becomes decoration.

**Badges on the README**, and the "minimalist faux 3d" button styling
the user mentioned. Both cosmetic, neither designed.

**The custom ("this") weave type**, with its tie-up, treadling and
threading matrices. Deprioritised rather than rejected: it needs a
matrix-entry UI and its own documentation.
