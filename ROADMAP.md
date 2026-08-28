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

## 0.24.4 — next

Worked on `pre-0.24.4rc1`. What follows is what the version owes.

**WHAT IS ALREADY BUILT, AND ON WHICH BRANCH.** Two branches carry
0.24.4. A branch cannot tell you it is unfinished, which is why each
is named here with what must be true before it goes in.

`for-0.24.4/copy-select-all` -- everything finished so far, and the
branch to work in. It carries `hunt-fixes` merged whole (the
twenty-five defects of 2026-08-27, each with a registered test and a
proved catalogue entry), the Select all button, the two element
ceilings with `element_order` behind them, and three of the five
rulings of 2026-08-27: an output path never decides the group, a ramp
is remembered under the row's mode, and donors are seeded before
their followers.
A FULL SUITE HAS COMPLETED ON IT, which is what 0.24.4 owed most:
636 passed, 1 failed at `0e9056c`, and that failure -- the user guide
naming one element ceiling where the code has two -- is fixed with
the test re-decided rather than widened. THE SUITE HAS NOT BEEN RUN
AGAIN SINCE the three rulings landed on top of it, so what is proved
is the tree underneath them plus each ruling's own tests and entries.
BEFORE IT MERGES TO `main`: one more full suite over the whole of it.

`for-0.24.4/saving-is-an-act` -- rulings 1 and 2, the Save work, as
PRODUCT CODE ONLY. Read that branch's own ROADMAP entry before
touching it: it names what is built and what is owed, measured rather
than guessed. IT MUST NOT MERGE AS IT STANDS, and the reason is not
caution. Generate no longer writes the GeoPackage, so twenty-one
catalogue entries are orphaned and fifty-six registered tests expect
a file that a run no longer produces; merging it would take a tree
with one known failure to a tree with dozens. Nothing on it has been
run.

**SAVING IS A POSITIVE ACT.** (Maintainer's ruling, 2026-08-27,
settled by grilling. THE PRODUCT SIDE IS BUILT ON
`for-0.24.4/saving-is-an-act`; THE SUITE IS NOT CONVERTED, and the
branch must not merge until it is. What that means precisely, because
"partly done" is the state this file exists to make unambiguous:

BUILT. A Save & open tab carrying two file rows and a button each --
Save writes, Load reads, and neither chooser does anything on its own.
`_save_the_map` writes the element tables, the twins, the embedded
styles, the stale-table drop, the source copy or its removal, and the
resumable record, in one act; `compat.point_layer_at` repoints each
layer at the file in place, keeping the ids the rest of the dialog is
keyed on. `_may_overwrite` asks before writing over a file this map
did not write. Generate writes NOTHING: the landing's per-element
write, its style embedding, its index reload, its stale drop, its
`_last_path` move and its record write are all gone, along with the
eleven adoption and restyle exits that embedded a style and the two
that rewrote the file's record. `_rewrite_the_files_record` is
retired. Live update's output-path gate is deleted with the
measurement at the site, and so is the Generate-time modal that
refused a run whose path would overwrite a kept result -- a run
overwrites nothing now.

OWED, and measured rather than guessed. TWENTY-ONE catalogue entries
are orphaned by the move and must be re-aimed at Save or retired with
a reason at the entry; `python3 tools/check_standards.py` names every
one. FIFTY-SIX registered tests set an output path and then Generate,
expecting the file to be written; each needs the Save press a person
now makes, and the handful that are ABOUT the writing -- the dock
edit reaching the file, the file's record following a restyle, the
mid-write restyle race -- need re-deciding rather than mechanically
patching, because what they assert has changed rather than moved.
THREE TESTS ARE OWED THAT DO NOT EXIST: a Generate leaves the file
BYTE UNCHANGED, Save writes it, and the overwrite prompt fires on
somebody else's file and not on our own.
NOTHING HERE HAS BEEN RUN. The branch was written while the full
suite was measuring another tree, so every sentence above describes
code that compiles and has been read, not code that has been
exercised.) A path chooser records what
you WOULD save to or load from and does nothing on its own. A SAVE
button beside the output path writes the map as it stands; a LOAD
button beside the other path chooser reads one back. Generate DRAWS.
Auto-generate never writes.
WHAT SAVE WRITES, in one act: the element tables, the embedded styles,
the resumable record through `_file_safe_state`, the stale-table drop,
and the source copy when "Include the source data" is ticked.
IT ASKS BEFORE OVERWRITING a file the plugin did not write (the
maintainer's addition the same day). With Save a deliberate press,
asking every time is noise; a file somebody else's map is in is not.
WHERE THE WORK IS. Everything under `if path:` in
`dialog._add_output_layers`, and the file-record write the restyle
makes through `_rewrite_the_files_record`, becomes what Save does.
This is the largest piece of the five and the one to take slowly: the
resumable record and the stale-table drop both live there, and both
have their own ledger rows from 2026-08-26 and -27.
AND ONE GATE IS DELETED RATHER THAN EXPLAINED. Live update refuses
while an output path is set, silently, and the user guide promises a
note (ledger row 11 of 2026-08-27). Its reason was that a live run
must not rewrite somebody's file on every keystroke -- and under this
ruling no run writes at all, so the gate cannot fire. A guard that
cannot fire reads as protection; remove it with the measurement at the
site, as this project did on 2026-08-20.
IT ALSO OVERRULES WORK ALREADY WRITTEN. The Save & open tab on the
`../ws-save-load` worktree resumes the moment a file is chosen, which
is exactly what this forbids; its open row becomes a Load button.
BEFORE IT MERGES: a test that a Generate leaves the file BYTE
UNCHANGED and that Save writes it; a test that the overwrite prompt
fires on somebody else's file and not on our own; and the live-update
gate's removal proved by its own catalogue entry going with it.

**UNTICKING "INCLUDE THE SOURCE DATA" MEANS IT IS NOT IN THIS FILE.**
(Maintainer's ruling, 2026-08-27. NOT BUILT.) Ticking the box, then
unticking it and saving again, leaves the file holding a full private
copy of the region layer while the record beside it says
`region_embedded: False` -- so the privacy the box promised is gone
AND the resume the copy would have given is refused, since the record
is what a resume reads. Measured through OGR on the file's own bytes
by the save-gpkg hunt, 2026-08-27; ledger row 26.
THE FIX IS AT SAVE, not at Generate, which is where writing now
happens: `weavingspace_region` is dropped, and ONLY that table -- the
one the plugin wrote itself, never anything else a user keeps in the
file. `bridge.drop_gpkg_layer` is already to hand and already takes
the saved style with the table.
WHY: the ruling of 2026-08-26 that the file shows the limit of what it
contains. A private copy somebody has switched off is exactly what
they would be surprised to find in a file they send on.
BEFORE IT MERGES: a test that reads the file's BYTES after the untick
-- once the dataset is closed, since sqlite's freelist keeps a deleted
page while the file is open (measured 2026-08-27).

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

**Give the stochastic hunt an exported-file invariant that RUNS.** Added
2026-08-16. A hunt over 105 checked steps reported its five axes:
holes 103, tile totals 103, opacity pairing 23, values-on-no-data 23,
and the GeoPackage comparison ZERO. That last axis never executed, so
a green run said nothing whatever about the exported file while
looking like full coverage. Counting what each invariant actually
compared is the practice worth keeping; an axis that never runs is
indistinguishable from one that always passes.

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
