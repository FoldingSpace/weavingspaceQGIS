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

## 0.24.3 — next

Worked straight on `pre-0.24.3rc1`. What follows is what the version
DELIVERS, organised as a user meets it; the complete defect record,
row by row with what each still owes, is
`docs/process/defects-2026-08-17.md`.

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

### Outstanding

**Nothing outstanding.** Everything this version owed in code is
built, tested and entry-proved, and the record of how lives where it
binds rather than here: `docs/process/defects-2026-08-26.md` for the
fifty-nine rows, CLAUDE.md for the five rulings of 2026-08-25 and
2026-08-26, docs/TESTING.md for what the round cost to verify.

THE LAST THINGS TO CLOSE, in the order they closed. The Windows red
of six CI rounds, diagnosed to its mechanism and fixed: a layer source
is a path plus a provider tail, a project save respells the path half,
and eight sites compared sources as raw strings. The four regressions
round nine shipped, found by the whole suite rather than by any
targeted run, three of them one mechanism -- a stamp taken away from a
landing may carry only what a landing decided -- and the fourth a
collision between two registered tests that the maintainer settled as
the day's third ruling. The debounces, decided by measurement: the
preview wait is a floor that widens to whatever a rebuild costs, and
the live interval is unchanged for reasons recorded under "Later, or
never". And the changelog, which gained three approved paragraphs for
behaviours this version acquired after the entry was first approved.

WHAT IS NOT IN CODE AND THEREFORE NOT HERE: the candidate's own gates,
which measure this tree, and CI, which `publish_candidate.py` refuses
to publish past. Neither is work owed; both are how the work is
checked.

### What this version has already closed

Entries are DELETED as they land, which is what keeps this file a
statement of what is owed rather than a diary. What follows is the
shortest record that leaves nothing unfindable: where the reasoning
lives, and the measurements that live nowhere else.

**THE DATASET-SWITCH CONTRACT.** The seven rulings of 2026-08-21, the
boundary the full suite drew (a change of dataset is leaving a
dataset this session has BUILT from), and ruling 8 of 2026-08-24 --
per-dataset memory banks, value-laden records never crossing a shared
column name, the file boundary tested at the GeoPackage's own bytes.
The "variables in common" carve was built and ended the same day by
the maintainer's own question about confidential values. rc17's
number was spent by a superseded build and never published; rc18
carried all of it. Eight hunts after rc18 found ELEVEN defects, every
one in the day's own code and nine inside its repairs, two of them
privacy leaks of exactly the kind ruling 8 exists to prevent -- so
**rc18 is SUPERSEDED** and the next candidate carries the cures.
Record: `docs/process/defects-2026-08-25.md`.

**THE OUTPUT GROUP AS THE UNIT OF WORK.** Settled by a grilling on
2026-08-25 after a colleague drove the rules above through a real
demo of several datasets in a row and found they answer ONE ACT in
three different ways, none of them named on screen. His diagnosis is
the sentence the design had to answer, and it is quoted in CLAUDE.md
where the six rulings bind: inferring all of this "is OK as far as it
goes, but it's too hard to be reliable and not produce weird seeming
behaviour relatively often". Built the same day in seven commits,
`18df97d` through `4527dec`: the working-state record on the group's
own custom property, the chooser and the symmetric binding with
`_fresh_group_for_new_data` retired, element tables trimmed and named
for their variable, the GeoPackage made resumable, the size guard
turned from a refusal into a banded question with its sentinels split
off, and the upstream library taken to 0.0.7.89. Guarded by five
tests, the four-axis matrix
`test_the_group_unit_rulings_hold_on_every_route`, and nineteen
catalogue entries proved to catch.

**AND ITS HUNT ROUND, JUDGED 2026-08-26.** Nine claims, six confirmed
and fixed with tests and proved entries, three refuted -- each by
driving the product rather than reading it, with the four probes
committed under `tools/probes/`. The worst of the six: the region
stamp was read off the CHOOSER as a run landed, so switching the
region layer mid-run filed one dataset's tiles under another and a
later run on that other dataset destroyed them.

**MEASUREMENTS THAT LIVE NOWHERE ELSE.** The colleague's file: 23
element layers each carrying all 26 source attributes took an 800 KB
dataset to a 19 MB GeoPackage, which is what trimming answers. A probe
wrote a four-column dataset out and read it back with OGR: four
tables, each holding all four columns including one deliberately
named `secret_code` that no element ever displayed -- not ruling 8's
cross-dataset leak, and the same family of concern. And the maintainer
met the naming half on rc16: in the project the layers read
"tileid - variablename" while the TABLE names were `tiles_<tid>`, so
opening the file directly showed "filename - tiles_a" and the
variable was nowhere.

**A SPACING A PERSON TYPED** now survives a change of dataset while
one the plugin DERIVED is still re-derived, and pressing Auto hands
the choice back. Measured rather than reported: 137 typed, 500 on
return, with nothing said. Guarded by
`test_a_spacing_a_person_typed_outlives_a_change_of_dataset` and two
judged entries.

**THE THIRTEEN GUARDS** owed for the fixes of 2026-08-17 were written
and proved on the 18th. The ledger's OWES column is the record; check
it rather than believing this paragraph:

    python3 -c "
    import re,pathlib
    txt=pathlib.Path('docs/process/defects-2026-08-17.md').read_text()
    rows=[l for l in txt.split('## The ledger')[1].splitlines()
          if re.match(r'^\\|\\s*\\d+\\s*\\|',l) and len(l.split('|'))==7]
    print([(r.split('|')[1].strip(), r.split('|')[5].strip()) for r in rows
           if r.split('|')[5].strip() not in ('test + entry','prose')])"

The reasoning that outlives these fixes is in CLAUDE.md where it
binds, in docs/TESTING.md where it is about tests, and at the code.

### Process items, which do not block a candidate

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

### Everything that stood under 0.24.4, moved up on 2026-08-25

MAINTAINER'S RULING that day, in three words: **nothing is delayed.**
What follows was written as 0.24.4 work and is 0.24.3 work now. The
entries are unchanged apart from this line, so the reasoning each was
deferred WITH is still readable -- and in one case that reasoning is
an argument against doing it now, which is recorded rather than
quietly dropped: the twenty-eight-version upstream jump was held back
on 2026-08-18 precisely because it moves the reference renderer the
gallery and the colourspace comparison measure against, so its gates
have to be read case by case rather than glanced at.

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

**TAKE THE UPSTREAM LIBRARY FROM 0.0.7.61 TO 0.0.7.89.** Checked
2026-08-18 under the standing rule that upstream is compared before
the suite runs, and OFFERED rather than taken: the maintainer's
decision that day was to build rc8 on the current vendor and do this
as its own piece of work, because a twenty-eight-version jump cannot
be folded into a candidate whose gates are about to measure it.

**TAKEN ON 2026-08-25**, and what follows is the record rather than
the plan. The vendor is 0.0.7.89 at bf1bbbf -- past ac69ca2, which is
where upstream stood when this entry was written. All five remaining
patches (matplotlib and scipy made optional) re-applied on their
exact anchors, none needing a decision.

COMPARED STRUCTURALLY FIRST, as the standing rule asks. Six of the
twelve library modules differ behaviourally: `_tiling_geometries.py`,
`symmetry.py`, `tile_map.py`, `tileable.py`, `tiling_utils.py`,
`topology.py` and `weave_unit.py`. `_loom.py`, `_weave_grid.py` and
`weave_matrices.py` are comments alone; `__init__.py` and
`tile_unit.py` are identical. Nothing upstream that we do not carry.

AND ONE CLAIM IN THIS ENTRY WAS WRONG, which is worth keeping rather
than quietly correcting. It said `c26dc70` "makes ids case-sensitive
in both TileUnit and WeaveUnit, so `a` and `A` are now different" --
read out of a commit message rather than measured. Measured against
the vendor on 2026-08-25: `TILE_IDS` holds 702 ids, `a`..`z` then
`aa`..`zz`, ALL LOWERCASE, and asking for 710 elements comes back
with 702 silently. Capitals do not appear at all. This project's own
rule applies to its own roadmap: a fact read out of a message is a
hypothesis, and it reads exactly like one somebody proved.

WHAT THAT SETTLES, and it is good news for the entry under "Waiting
on the upstream project" below. Doubled lowercase ids survive a
GeoPackage's case fold where capitals do not, so upstream has removed
the case blocker for TILINGS entirely. What it has not removed is the
WEAVE STRING FORMAT, where one character means one element and a
two-character id has nowhere to go -- so `catalog.MAX_ELEMENTS` stays
at 26, which is a DECISION and not a discovery: moving it means
auditing everything that assumes an id is one character and living
with a limit that differs by family, and nobody has asked for a
twenty-seventh element. Both canaries fired on the bump, which is
what canaries are for, and both were rewritten to what is true now
rather than relaxed.

THE MEASUREMENT IS THE CANDIDATE'S, and this entry said otherwise
until 2026-08-26. It read "recorded in the commit that carries them",
naming a commit that was never made: the bump commit said the
measurement would follow in its own, and nothing followed. The three
things owed -- the functional suite, the visual gallery read case by
case, and the colourspace comparison against the moved reference
renderer -- are precisely the gates `release.py --rc` runs, so the
candidate is where they happen rather than a commit somebody has to
remember. Read the gallery case by case when it does: the reference
renderer moved by twenty-eight versions, which is why this was held
back in the first place.

**WHAT SHOULD THE DEBOUNCES BE?** Measured 2026-08-17 and recorded
here because changing it would change the software, which is the line
between a process item and a real entry.

A user nudging a control with live update on waits about 1.7 SECONDS
before the map settles, of which roughly 225 ms is CPU and the rest is
the 350 ms preview debounce and the 900 ms live one. So about two
thirds of the wait is deliberate delay. That is not a regression --
the interactive loop is measurably FASTER than v0.24.0, the debounces
are identical in both, and 61 layers in the project change nothing --
but it is what "the snappy interactive feel has gone" is describing,
and nobody has ever chosen those numbers against a measurement.

Three questions, and they are design rather than defect: what should
the two intervals be; should the preview and the live run share one
debounce instead of firing at 350 and again at 900; and should a run
that is about to be superseded be CANCELLED sooner than it is.
`tools/probes/one_interaction.py` is the instrument, and it takes the
tree to measure as an argument so any two can be compared.


Deferred from 0.24.3 on 2026-08-15. All three are MEASUREMENT: they
say how good the suite is rather than whether the plugin is right,
so none of them blocks an artefact.

**ANSWERED and deleted from here on 2026-08-16.** The rebuild count
was retired dialogs: four routes into `_rebuild_unit` that a dialog
kept open after the user had finished with it, the last of them the
layer combo's own re-emission rather than a project signal. Fixed and
guarded; 1,282 rebuilds down to 173. Kept as one line only because
this entry said the question "changes no artefact", and it turned out
to be the direct cause of a red suite on three platforms -- deferring
it was the wrong call, made on a local measurement too cheap to show
the effect.

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

## 0.24.4 — after this one

**Nothing.** Everything that stood here moved into 0.24.3 on
2026-08-25 on the maintainer's ruling that nothing is delayed. The
section is kept rather than deleted because the release process
expects a version to have one, and because an empty section says
something a missing section does not: this was emptied deliberately,
not forgotten.

## Waiting on the upstream project

Blocked on the weavingspace project rather than on this repository, so
no release waits for it.

**Element ids past 26.** Two routes past the ceiling, blocked by two
different things. Setting both out because compressing them is how the
reasoning gets misremembered.

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
section.

AND THE READING THAT SAID IDS HAD BECOME CASE-SENSITIVE WAS WRONG.
The 0.24.3 entry above carried it from a commit message, and it
pointed the opposite way — toward capitals colliding. Measuring the
vendor settled it. Kept here because this entry's own opening says
compressing the reasoning is how it gets misremembered.

WHAT WOULD MAKE IT OURS. Moving the ceiling for tilings alone is a
decision, not a discovery, and the work is not the number: it is
auditing everything that assumes an id is one character, here and in
designs users have already saved, and then living with a limit that
differs by family. `MAX_ELEMENTS` is one number for both today.
Nobody has asked for a twenty-seventh element.

**Two conversations to have.** Whether the corrected large-plain-weave
note was sent (`docs/process/upstream-note-large-plain-weaves.md`
supersedes the first, which blamed a commit wrongly), and the
element-id ceiling above, which is upstream's decision rather than
ours.

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
