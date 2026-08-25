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

WHAT IS BUILT, so the entries below are read against it. The
dataset-switch machinery is complete: the seven rulings of
2026-08-21, the boundary the full suite drew (a change of dataset is
leaving a dataset this session has built from), and ruling 8 of
2026-08-24 -- per-dataset memory banks, value-laden records never
crossing a shared column name, the file boundary tested at the
GeoPackage's own bytes, and the "variables in common" carve built and
ended the same day by the maintainer's question about confidential
values. Every piece carries a test somebody watched fail and a judged
catalogue entry. rc17's number was spent by a superseded build, never
published; rc18 carried all of it.
EIGHT HUNTS AFTER rc18 PUBLISHED FOUND ELEVEN DEFECTS, every one in
the day's own code and nine of them inside its repairs; all eleven are
fixed here with tests and judged entries, so **rc18 is SUPERSEDED**
and the next candidate carries the cures. Two were privacy leaks of
the kind ruling 8 exists to prevent, reaching a saved project and a
GeoPackage by different routes. The record is
`docs/process/defects-2026-08-25.md`.

**AND THEN A COLLEAGUE DROVE THOSE RULES THROUGH A REAL DEMO AND THEY
DID NOT COHERE.** (dos, 2026-08-25, across several messages; every
claim re-measured here the same day by a probe rather than read out of
the source.) Each ruling is right on its own terms. What the demo
found is that they answer ONE ACT in three different ways and that
none of the three is named anywhere on screen: value-laden records are
remembered per dataset, the design is carried globally, and the output
group is remembered nowhere.
MEASURED ON THIS BRANCH, and these numbers are the ground the entries
below stand on. The design travels a switch intact -- element count,
family and "Use tileable as icon" all carried from A to B. A-B-A makes
THREE output groups, of which the first and third carry the SAME
dataset stamp, so one dataset already owns two maps with nothing to
tell them apart. Coming home, the design does NOT return: it arrives
as the DEFAULT family for the element count, which is neither the
dataset's own earlier design nor the one carried in. The floor
question's Yes takes that same default (a user's `grid 3` came home
`hex-slice 3`). The hand-picked colours and pinned bounds DO come home.
A hand-typed spacing does NOT, and says nothing about it (137.0 typed,
500.0 on return). No widget in the dialog names the output group at
all; the only channel is the transient note line, which on the
measured run was occupied by an unrelated notice.
THE COLLEAGUE'S OWN DIAGNOSIS, worth keeping in his words because it
is the argument the design has to answer: inferring all of this "is OK
as far as it goes, but it's too hard to be reliable and not produce
weird seeming behaviour relatively often". And his own caution against
his own proposal, which is the case for the smallest sufficient
change: "who is using this other than us?!"
THE MAINTAINER RULED, 2026-08-25, that EVERY item raised in that
conversation is settled in THIS version -- not 0.24.4, not 0.25.0 --
which is why the three entries below that used to sit under 0.24.4
now sit here.

**THE OUTPUT GROUP BECOMES THE UNIT OF WORK.** SETTLED BY A GRILLING
ON 2026-08-25; the rulings themselves are in CLAUDE.md where they
bind, and what follows is only what is left to BUILD. Six decisions:
a dropdown of output groups on the first tab beside the region
chooser, with a "create new" entry; dataset and group bound
symmetrically, each selecting the other; recency as the tie-break
where a dataset owns several groups, read off the project's layer
order rather than remembered; the WHOLE WORKING STATE belonging to
the group and restored by selecting it; the GeoPackage made
resumable, with the source recovered BY REFERENCE and embedding it an
explicit opt-in; and element tables trimmed to the symbolised
variable and named `tiles_<tid>_<variable>`.

THE WORK, in the order the dependencies force:

1. THE WORKING-STATE RECORD and its persistence in the group's custom
   properties. Everything else reads it. Its RESTORE WHITELIST is the
   record's real definition and is widened in the same commit as the
   record -- a key missing from it is dropped in silence on every
   reopen, which is how `_adopt_dock_bounds` was got wrong once.
2. THE DROPDOWN, the symmetric binding and the recency tie-break,
   retiring `_fresh_group_for_new_data` with them.
3. TRIMMING, TABLE NAMING, and adoption still reading the old
   `tiles_<tid>` so existing files and projects keep working. Names
   sanitised, and case-folding collisions handled: a GeoPackage folds
   `tiles_a` and `tiles_A` into one table with both writes reporting
   success (measured 2026-08-14).
4. THE FILE FORMAT: the record serialized into the GeoPackage with a
   version stamp, the reference-or-embed choice, and the resume path.
   TWO THINGS TO DECIDE AT THE CODE rather than in advance, both
   recommended and neither yet ruled: refuse a forward-incompatible
   file by version, and treat a recorded column the data no longer
   has exactly as a deleted column is treated today, which is
   machinery that already exists.
5. WHAT "THE WHOLE WORKING STATE" INCLUDES AT THE EDGES -- the output
   path, the live-update setting, the legibility warning. Write the
   list down explicitly wherever it lands.

AND THE MATRIX THAT PROVES IT (maintainer's instruction, same day):
edge cases across all four of the axes this work crosses -- the
QGIS-plugin boundary, the user-plugin boundary, styling, and the
choice of dataset. Not a case per ruling: a crossing, with the spine
run every time and the rest sampled under a printed seed, per the
default in docs/TESTING.md.

**THE SIZE GUARD WARNS RATHER THAN REFUSES.** (Maintainer's ruling,
2026-08-25: "Warning not absolute. Find a different approach to
sentinel if appropriate.") `MAX_TILES_HARD` refuses a run outright
above 200,000 estimated tiles, on a comment claiming the run would
exhaust memory and kill QGIS -- a figure NOTHING IN THIS REPOSITORY
MEASURES, and one the maintainer's own argument disposes of: different
machines have different maximums, and different designs have different
needs at the same tile count. The gate has already been wrong in the
expensive direction (ledger row 23, 2026-08-19: 585,765 estimated
against 70,659 drawn, refusing a map the library renders in five
seconds), and with the confirm gate raised to 100,000 the same day,
the band from there to 200,000 is "asked and allowed" while above it
is "refused however loudly you insist".
WANTED: one question whose wording escalates by band rather than two
gates, keeping what the refusal already gets right -- the workable
spacing it suggests, and icon mode's different sentence, since spacing
cannot help there -- and adding what a refusal never said: this may
exhaust memory, QGIS may stop responding, save your project first.
The safe button is the default, per the dependency-consent precedent.
WHAT MUST BE TRUE BEFORE IT CLOSES, and it is the reason the ruling
names the sentinel: `MAX_TILES_HARD + 1` is ALSO returned by
`estimate_tile_count_bounds` for two cases that are not about size at
all -- a unit whose vectors are degenerate, so the design does not
tile the plane, and an estimate that comes back non-finite, which is
how a layer with no CRS used to reach the user as an OverflowError.
Those must stay refusals. So the ceiling cannot soften until the
sentinel has its own mechanism, or a genuinely broken design becomes
something a user can click straight past.

**LANDED, so this entry records only what is left of it:** a spacing a
person TYPED now survives a change of dataset while one the plugin
DERIVED is still re-derived, and pressing Auto hands the choice back
(maintainer's ruling, 2026-08-25, on a probe's measurement rather than
a report -- 137 typed, 500 on return, with nothing said). Built,
guarded by `test_a_spacing_a_person_typed_outlives_a_change_of_dataset`
and two judged catalogue entries. NOTHING IS OUTSTANDING HERE; the
line is kept only until the changelog sentence has been through review,
and goes at that point.

**A SAVED RESULT CARRIES EVERY COLUMN OF THE SOURCE DATA.**
(Colleague's report, 2026-08-21, on the maintainer's own data: 23
element layers each holding all 26 source attributes took an 800 KB
dataset to a 19 MB GeoPackage. Moved here from 0.24.4 by the ruling
above.) Wanted: each element layer carries the variable it symbolizes
plus the identifiers (tile id, and probably the prototile id), with
the layer name saying which variable it displays. Decisions the
maintainer owns before anyone builds it: exactly which columns
survive; whether the layer NAME gains the variable (renaming is safe
-- adoption keys on custom properties, and a name is a label here,
never an identity); and whether the paired no-data layer needs
anything beyond the element's own column.
THE MAINTAINER MET THE NAME HALF ON rc16 (2026-08-24): in the project
the layers read "tileid - variablename", but the GeoPackage TABLE
names are `tiles_<tid>`, so loading the file directly shows
"filename - tiles_a" and the variable is nowhere. Renaming TABLES
reaches further than renaming layers: `_gpkg_tables_written`, the
stale-table cleanup's `tiles_{tid}` patterns, `drop_gpkg_layer` and
adoption-by-file would all need to follow, which is why it belongs to
this entry rather than to a quick fix. One
fact that lowers the cost: the set of mapped variables is already a
GEOMETRY change, so a variable switch re-tiles today regardless --
trimming the columns takes nothing from the restyle fast path.
TWO THINGS ARRIVED ON 2026-08-25 AND BOTH BELONG HERE, because they
pull in opposite directions and the decision needs them together. The
colleague argued FOR the current behaviour: a given tiling may be
missing data in some variables, so carrying the full set hedges
against what is otherwise a lossy encoding, and while you are still
working it makes switching variable cheap. Against it, a probe wrote a
four-column dataset out and read the file back with OGR: four tables
`tiles_a` to `tiles_d`, each carrying ALL FOUR source columns
including one deliberately named `secret_code` that was never
symbolized. So the file a user sends a colleague carries attributes
the map never displayed. That is not ruling 8's cross-dataset leak,
and it is the same family of concern.

**READ IN "ONE I MADE EARLIER".** (Same conversation; moved here from
0.24.4 by the ruling above.) Point the plugin at a saved output
GeoPackage -- without the project that made it -- and have it adopt
the group the way a reopened project is adopted, so a demo can open a
finished result instead of tiling one live. Depends on the entry
above: a trimmed output must still carry whatever adoption reads. The
adoption machinery exists; what is new is reaching it from a file
rather than from the project.
AND THE COLLEAGUE ASKED FOR MORE THAN ADOPTION: that such a file carry
the whole design as metadata, so reading it back RESUMES the work
rather than merely displaying it. Whether that is in scope is the
second half of the ownership decision above, and the two entries close
together or not at all.

### What this version has already closed

The thirteen guards owed for those fixes were written and proved on
2026-08-18 and the entry listing them is DELETED, which is what this
file asks. The ledger's OWES column is the record; check it rather
than believing this paragraph:

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
NEXT: reproduce with the maintainer's exact settings, or have them
read the twin's feature count in QGIS -- features present means real
join-missed tiles and the question becomes whether the LAYER'S NAME
should say so ("no value at this spacing"), zero features means a
gate defect nobody has manufactured yet.

**TAKE THE UPSTREAM LIBRARY FROM 0.0.7.61 TO 0.0.7.89.** Checked
2026-08-18 under the standing rule that upstream is compared before
the suite runs, and OFFERED rather than taken: the maintainer's
decision that day was to build rc8 on the current vendor and do this
as its own piece of work, because a twenty-eight-version jump cannot
be folded into a candidate whose gates are about to measure it.

We vendor 0.0.7.61 at commit c0f109c. Upstream's head is 0.0.7.89 at
ac69ca2, nine commits on, and it is BEHAVIOURAL rather than a licence
bump: compared as syntax trees with docstrings stripped, seven of the
ten library modules differ -- `_tiling_geometries.py`, `tile_map.py`,
`tileable.py`, `topology.py`, `weave_unit.py`, `tiling_utils.py` and
`symmetry.py`. Only `_loom.py`, `weave_matrices.py` and
`_weave_grid.py` are comments alone.

TWO OF THOSE COMMITS ARE ABOUT ELEMENT IDS, which is why this is not
just housekeeping. `6926d65` supplies tile ids from
`TILE_IDS = [a..z, aa, ab..zz]` and says WeaveUnits remain
single-character; `c26dc70` makes ids case-sensitive in both TileUnit
and WeaveUnit, so `a` and `A` are now different. Both bear on the
entry under "Waiting on the upstream project" below, which has been
blocked on exactly this — and the second one bears on the GeoPackage
collision measured there, in a direction that could go either way.
Read that entry beside this one before either is closed.

WHAT MUST BE TRUE BEFORE IT MERGES. The vendoring is a script rather
than a project (`tools/vendor_weavingspace.py`, which re-applies the
remaining patch family and refuses rather than writing a broken
vendor), but the MEASUREMENT is the work: `tile_map.py` and
`_tiling_geometries.py` have both moved, so the reference renderer
this project compares its maps against has moved too. The visual
gallery and the colourspace comparison must be read case by case
rather than glanced at, and any change in them attributed to upstream
deliberately rather than absorbed. The element-id ceiling of 26 in
`catalog.MAX_ELEMENTS` is ours and is now guarded by
`test_the_documents_numbers_match_the_code`; decide whether it moves,
rather than letting it move by itself.

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

WHAT UPSTREAM SETTLED, 2026-08-18. weavingspace 0.0.7.89 supplies tile
ids from `TILE_IDS = [a..z, aa..zz]`, used only in
`_tiling_geometries`; `weave_unit.py` never touches it. So for TILINGS
both blockers are off — upstream provides the ids, and doubled
lowercase survives the GeoPackage. For WEAVES the format is still the
obstacle, and changing it is upstream's decision rather than ours,
which is why this entry stays in this section.

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
