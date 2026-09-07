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

Entries whose work is DONE keep their headline here and their account in
`ROADMAP-archived.md`, by the ids quoted (R-4). Nothing outstanding was
moved: what a version owes is still written here in full, because the
release gate reads this file and a debt nobody can see is a debt nobody
pays. See docs/DOC-ARCHIVING.md.

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

## How to add to this file

An entry is a bold-led paragraph under the version it belongs to,
saying what is owed and what must be true before it closes; while it
is OUTSTANDING it stays in full, however long, because the release
gate reads this file and a debt nobody can see is a debt nobody pays.
WHEN IT LANDS, delete it, or where its reasoning is worth keeping cut
it to its headline and quote an id minted with `python3
tools/doc_archive.py --mint R "title"`, the account going to
ROADMAP-archived.md. Do not write the account here: a DONE entry
longer than thirty lines, or one that opens with a date, fails
`tools/check_standards.py` with the fix in the message. Measurements,
refutations and the reasoning behind a ruling belong in the archive
from the day they are written, and the ruling itself in CLAUDE.md.

---

## Conflicts to settle by grilling

Collected 2026-08-31 at the maintainer's asking. Every entry here is
TWO SETTLED RULES GIVING ONE ACT TWO ANSWERS -- not a defect, not work
somebody forgot, and not a thing an assistant may decide by picking
the more convenient rule. This project's own answer to that shape is
`/grill-me`: one question at a time, the facts looked up first, a
recommendation offered, and nothing built until the maintainer
confirms.

THEY ARE NAMED HERE AND LEFT WHERE THEY LIVE. Each still sits in its
own version's section, because moving an entry between sections is
deferring it and that is the maintainer's act; this is an index, so
that the set can be seen at once rather than found by re-reading the
file. Delete a line here when its grilling settles it.

WHY THEY ACCUMULATE, which is worth saying once. When two rules
collide, the answer is usually BOTH -- with the thing that tells them
apart written down. That is how the kept-scheme ruling of 2026-08-26
was settled, and it is why none of these should be closed by choosing
a side quickly.

**NOTHING AWAITS GRILLING AS OF 2026-09-05.** All seven, and field
report 5 as an eighth, were put to the maintainer that day one at a
time with the facts measured first. FOUR WERE STRUCK because their
premise had dissolved: the mutation workflow (measured moot, R-31);
the element slider (settled 2026-09-01 and built, the flip speaks);
the colourspace limit (the comparison is handed the colours in force,
measures dE means of 0.3-0.4 here, and the three fresh-profile Linux
gallery jobs are green on the latest CI run); and the window ceiling
(1480 since 2026-08-29, so the 1334 measured under the real macOS font
fits). THREE BECAME RULINGS and are owed as work under 0.24.4 below:
the shelf key stays narrow and reports at replay (was 7), the record's
reader assigns the first n elements (was 1), and the comparison PDF
says it measures the vendor (was 5). FIELD REPORT 5 BECAME FIVE
RULINGS, in CLAUDE.md, with its work below. The eight as they stood,
verbatim: R-79.

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

(Released. What it gives you and what it puts right, in full, in
ROADMAP-archived.md R-1 -- kept out of the live ledger because a
shipped version owes nothing.)

## 0.24.4 — next

**NOTHING OUTSTANDING IN CODE, AS OF 2026-09-05 (LATE).** The
declaration of 2026-09-01 was struck when five field reports and a
suite failure arrived on 2026-09-04 (R-2); every one of those is now
closed below, and so is everything the maintainer asked for before the
next candidate -- the dual button and the completed dual, the two tab
defects, the three settled conflicts, the Topology tab audit, the
documents re-audit and the self-fixing documents, the docstrings pass
and the two studies. The three decisions that were the maintainer's
-- the zigzag threshold, odd zigzag counts, the count readout's clamp
-- were settled by grilling late on 2026-09-05 (CLAUDE.md, the zigzag
handle's rulings 6 and 7; the clamp stands), and the two that changed
code are built and guarded. The product stall of R-4 is parked under
"Later, or never" on the maintainer's decision, and the text-review
queue is empty, the three tooltip sentences those rulings wrote
having been approved before rc16 was built. AFTER rc16, ROUND EIGHT
CLOSED EIGHTEEN DEFECTS on 2026-09-06 (docs/process/defects-2026-09-06.md,
rows 1-18, most of them in the Topology tab's dual and zigzag work
of the days before), three rulings landed the same evening -- duals
chain, the count interpolates along the edge, the amplitude box
shows the crest (C-334, C-336, C-337) -- every sentence was approved,
and rc17 carries the lot; its first build found eight failures in
ground the targeted runs had passed (T-145, T-146, C-338).

### Closed: the two suite failures and the harness race

**THE VENDORING TOOL FAILURE IS CLOSED** (R-3) **AND THE HARNESS
RACE BEHIND THE INTERMITTENT TOPOLOGY FAILURES IS FIXED**: `_settle_topology`
returned in the window between an edit being recorded and its build
being queued, so quiet must now persist for three checks, and a full
three-shard run over `03d6ba7` was green at 264, 264 and 264. The
waiter explains itself, naming what QGIS's own task manager holds.

### The sweep for the snap-back: done, one fault found

Every store whose replacement arrives asynchronously was asked who
empties it and who fills it (C-244); the Topology tab's parameter
boxes were the one fault, torn down by every landing, and are fixed and
guarded; ten other stores are sound (R-73; the sweep R-81).

### The five field reports against 0.24.4rc15: all closed

Reported 2026-09-04 on the default design over the packaged Auckland
data, and each driven, fixed and guarded on 2026-09-05: the drop that
put the un-edited design back for a second (R-72); the zigzag that did
not stick, which was every landing resetting every parameter box
(R-73); the count set from the drawing (R-74); the handle too far from
its edge (R-75); and "map the dual" erroring while the tab drew one,
whose mechanism was not what reading suspected and whose five rulings
are in CLAUDE.md (R-79). The accounts, with the candidate eliminated
and the threshold question left open, are R-82.

THE QUESTION FROM REPORT 2 IS SETTLED: the click threshold was the
box's floor, under a pixel on the tab's own edges, and is now half a
handle seat of travel from where the handle was grabbed (ruling 6 of
the zigzag handle, CLAUDE.md; C-319).

### Done: the dual button, the three settled conflicts, and the maintainer's four asks (2026-09-05)

**THE NEXT CANDIDATE WAITED FOR THESE**, on the maintainer's decision
(ruling 3 of the dual), and all are done.

- **THE DUAL BUTTON IS BUILT**, landing the dual in `<group> — dual`
  through the chooser's own door; **THE DUAL IS COMPLETED HERE AND
  OFFERED UPSTREAM**, coverage 1.000000 on eight designs; **THE TWO
  TAB DEFECTS ARE FIXED**, and the two topology modules joined text
  review with 27 sentences for the maintainer; **THE SHELF REPORTS AT
  REPLAY** (was conflict 7); **THE READER ALREADY ASSIGNS THE DESIGN'S
  OWN ELEMENTS**, measured rather than coded (was conflict 1); **THE
  PDF MEASURES THE VENDOR** (was conflict 5); and **THE GENERAL AUDIT
  OF THE TOPOLOGY TAB IS DONE**, three defects found and fixed, with
  two decisions reported rather than changed -- an odd zigzag count
  opens a gap of 0.35-0.6% on class `b`, and the count readout's clamp
  bites at the window's own size (n=3 and 2 on the default design's
  edges at the size the tab opens). All on 2026-09-05; the accounts,
  measurements and probes are R-83 and docs/TOPOLOGY.md.
- **THEN A RE-AUDIT OF THE BINDING DOCUMENTS** (maintainer's ask,
  2026-09-05): "make sure they say what they need (for LLMs) but no
  more", and later the same day the measure in the reader's terms: "as
  context efficient as possible while being effective -- we want their
  lessons and logics and some reasons/evidence to be transmitted".
  DONE: CLAUDE.md 3,919 to 1,932, docs/TESTING.md 2,527 to 836, this
  file's DONE entries 1,540 to 524, and, after a second reading against
  the measure, docs/PUBLISHING.md 816 to 712 and MAINTAINING.md 2,302
  to 2,048 with every step and mechanism kept. AND THE MAINTAINER'S WRINKLE
  OF THE SAME DAY IS BUILT: the documents will be edited by a different
  model from now on, so each now opens with a how-to-add section, the
  themed ones have a capped inbox, and `tools/doc_archive.py` checks the
  SHAPE of growth -- fixed sections, an entry cap, no date-led entries
  -- failing the standards gate with the fix in the message, with
  `--mint` writing an archive stub under the next id. Two tests and
  six catalogue entries proved `caught`; the practice is in
  docs/DOC-ARCHIVING.md under "Writing for the next reader".
- **AND THE SAME EDIT TO THE DOCSTRINGS -- DONE** (same ask: "they're
  not terribly useful for human maintainers right now"). Every package
  docstring of thirty lines or more -- 116 of them, 4,587 lines -- was
  read paragraph by paragraph against the standard: what it does, Args
  and Returns, the reasoning at the line stay; the day, the first
  attempt and the measurement go. Thirty-five docstrings lost 372
  lines of account to `docs/DOCSTRINGS-archived.md` under D-1 to D-35,
  each quoting its id; the other 81 were reasoning end to end and
  stand. `tools/doc_archive.py` reads the package as the live half of
  that archive, so a D-id nothing quotes fails the standards gate. What
  it did NOT do is shorten reasoning, which is the half an LLM needs;
  a second pass could condense the all-caps paragraph style itself.
- **TWO STUDIES, THE MAINTAINER'S ASKS OF 2026-09-05 -- WRITTEN**, as
  audits naming candidates with a measurement each and no code:
  `docs/process/study-tiling-and-layer-data-2026-09-05.md` (four
  candidates; one field table for every signature first, then one
  element record, then a tiled-map value object) and
  `docs/process/study-dialog-complexity-2026-09-05.md` (six; the save
  and load as a module without Qt first, then one deferred-intent
  queue, then the landing as a pipeline). Both say what is NOT
  recommended and why, and neither is to be done in the same breath as
  a candidate: 527 of the catalogue's 764 entries are anchored on
  `dialog.py` lines. Whether and when to take any of them is the
  maintainer's decision.

Worked on `pre-0.24.4rc1`. What follows is what the version delivers,
and what each piece of it cost to prove.

**FIVE CANDIDATES WERE BUILT AND SPENT, rc10 TO rc14**, every one on a
suite fault or a ceiling and none on a product defect, which is the
documented trade (R-7, R-8, R-9, R-10, R-12, R-13, R-14; a third
hypothesis about the teardown abort refuted, R-77) -- and rc16's first
build went red the same way on 2026-09-06, on a test premise the
even-count ruling had made false (T-143), though no artefact bore the
number and the rebuild kept it, and rc16 itself was then red on every
runner for a documents gate that read this machine's disk (T-144),
published on the maintainer's one-off say-so past it as the
pre-release `v0.24.4rc16` of 2026-09-06, the fix's own CI run being
the verdict to read. **THE 24-BUG CAMPAIGN REACHED ITS TWENTY-FOUR**
(R-11, R-15, R-16). **ONE LINE CARRIES 0.24.4**, `pre-0.24.4` (R-17).
**THE DRIFTED CATALOGUE IS DONE** (R-18, R-19). **THE CHANGELOG LINE
IS APPROVED**, on its second pass (R-20). **THE ROUND OF 2026-08-28
RAN A THIRD WAVE AND ITS OWED LIST WAS TAKEN TO THE END** (R-21, R-23;
`tools/probe_kit.py` came out of it). **NOTHING ENDS WHILE A SAVE IS
OUTSTANDING IS BUILT** (R-22), and **A SAVE PRESSED WHILE A RE-TILE IS
COMING IS KEPT** -- the maintainer's overruling of a refusal, on the
ground that a refusal nobody reads is a save that quietly did not
happen. The accounts, and what the third wave gives a user, are R-84.

**THE SIX DECISIONS OF 2026-08-29 ARE ALL BUILT**: numbers stored as
text classify; the window ceiling gives at the columns, at 1480; the
save is responsive behind a determinate bar; the guide's Save sentence
is reworded; a catalogue anchor must be unique; and `mutation_check`
anchors the whole decision rather than gaining a list of replacements
(R-24, R-25, R-26, R-27). **THE FOUR APPROVED FEATURES ARE IN 0.24.4**
(R-29, R-30), the re-vendor and the Topology tab's rebuild with them (R-28),
and **THE `publish_candidate` QUESTION IS MOOT** (R-31). Accounts R-85.

## 0.24.5 — three tabs asked for, and what was deferred here from 0.24.4

**THE HONEST PREVIEW: A MANIPULATION SHOWS ONLY WHAT WILL COMMIT.**
(Maintainer's principle, 2026-09-06, after rc17's drag reports.) The
preview must never let a person imagine a move will be allowed when it
will not. Three states shown as the drag goes: VALID as now; CLAMPED,
the glyph stopping at the max so the rotation arc, the scale and
displacement arrows and the zigzag do not draw past their limits;
FAILED, red and dotted for a move that cannot be tiled, with the
reason. Each manipulation also shows a live sense of MAGNITUDE and a
subtle cue of the entity or symmetry it bears on (the pivot, the push
rail, the edge); a dashed rotation arc is part of it. The drop
already commits what a real drag draws (C-339); this is the drawing.
IN PROGRESS 2026-09-06: the state scaffolding is built and saved as
`dev/honest-preview-wip.patch` (reverted from the tree so nothing
half-built regresses). TWO THINGS FOR THE MAINTAINER, in the handover
in full: what FAILED means is not settled -- 'any gaps' conflicts
with ruling 5 (2026-08-31, validity SHOWN not enforced), since a
plain rotate leaves gaps and would paint every rotate red -- and it
needs a grilling; and the status must clear on the drop. It composes
with the palette below, so the two are done together.

**THE TOPOLOGY TAB'S PALETTE, TOWARD THE PAPER'S FIGURE 13.** (Maintainer's ask, 2026-09-06: learn the styling of `topology-styling-to-learn.png`, on the roadmap rather than now.) The figure draws a tiling as thin WHITE edges on a light grey ground, with ONE darker-grey region for the thing being worked on and DOTTED grey construction lines for the auxiliary geometry -- monochrome and restrained. The tab today is the opposite: black edges, orange for the selected class, a red selected edge, teal handles and ghost, red hatching for gaps, and a/b/A/B labels everywhere. The direction is to move to white-on-grey with one emphasis colour and dotted lines for the ghost, the rotation arc and the dual overlay, so the drawing reads as a diagram rather than a control panel. It is an aesthetic change and the maintainer's to tune, so it wants a before/after put to them rather than built blind; it also composes with the honest-preview work (a red dotted glyph for an impossible move needs the palette settled). The reference image is in `claude scratch/`.

Moved on the maintainer's decision of 2026-08-27, in the act of
cutting 0.24.4's candidate. None of it is abandoned and none of it
was blocking the version: three are measurements rather than
defect-finding, and the fourth is a study whose answer is written
at its own entry.

**ALL THREE ARE EXPERIMENTAL, BEHIND A BOX THAT STARTS UNTICKED**
(R-32), and **THE LIVE-UPDATE SWITCH IS ON THE TOPOLOGY TAB AS A
SECOND VIEW OF ONE FACT**, `live_check` the single owner (R-78; R-86).

**A MESSAGES TAB -- SHIPPED EXPERIMENTAL IN 0.24.4, and what is left
here is the part that did not ship.** The tab exists: everything the
plugin has said this session, newest first, with the answer beside any
question, behind the Experimental features box. WHAT NEEDS DECIDING is
whether the plugin's own message-bar helper becomes the single door
everything passes through -- it very nearly is already -- and what
happens to a message issued while the tab does not yet exist. (R-33.)

**A LEGEND DESIGN TAB, and a two-way question at the end of it that
needs research before any of it is built.** A chooser of legend styles,
defaulting to NONE -- defer to QGIS, which is this project's standing
preference and the honest default for somebody who has not asked for
anything. (R-34.)

**A TOPOLOGY TAB IS BUILT AND SHIPS EXPERIMENTAL IN 0.24.4**: the five
rulings of 2026-08-30 (R-36) are all built (R-37), the interaction was
audited and rebuilt on 2026-08-30 and again on 2026-08-31 -- select
then act, handles that are the choice of manipulation, a hit test that
follows the edge, glyphs that say what they do, a position rather than
a delta -- and MAINTAINING.md carries the mechanics (R-35; R-87).

**AND THE TAB DRAWS THE UN-EDITED MOTIF, which is a ruling rather than
a repair.** Read on 2026-08-31 and NOT yet driven, which is the
honest state of it: `set_unit` is handed `built["unit"]` and
`built["topology"]` -- the design BEFORE the edits were replayed --
while `_adopt_edited_unit` gives the dialog the edited one, so the
preview and the map move and the drawing somebody judges the edit by
does not. One fact, two stores, disagreeing on screen.

IT IS NOT A ONE-LINE FIX, and that is why it is here rather than done.
The view has a `show_preview` channel that already paints something
other than the held topology, so drawing the EDITED motif is easy. The
question is what the picture is then FOR: edits are replayed by class
LABEL against a topology built from the UN-EDITED unit, so the labels
a person aims with must keep coming from that one. Drawing the edited
geometry while hit-testing the un-edited topology puts the highlight
somewhere other than the ink; hit-testing the edited one records
labels that mean something else on replay. Neither is obviously right,
which makes it the maintainer's call and a candidate for a grilling.

**A HANDLE IS A POSITION, NOT A DELTA -- BUILT; ONE END HANDLE
INSTEAD OF TWO -- REFUSED**, because a glyph cannot say two things and
one gesture would record two edits. If the merged handle is wanted
later, that is the argument it has to beat. Every manipulation is
reachable on the drawing; `push_vertex` moving nothing at a symmetric
vertex is a fact about the design (R-38); the rebuild's regression was
two faults and is closed (R-39); a topology matrix exists.

**THE DEFAULT STRAND WIDTH STAYS AT 0.75** (maintainer, 2026-08-30,
changed to 1.0 and back the same day); the case for raising it is
sound and is R-40, so nobody proposes it again from nothing.

**ZIGZAG'S REPEATED VERTICES ARE REPAIRED WITH UPSTREAM'S OWN
CLEANER** -- before writing a repair for a dependency's output, grep
the dependency for one -- and click-and-drag is affordable at 1.23 s an
edit (R-41, R-42, R-43); the notebooks gave the seven-toggle view and the dual's
promotion (R-44); the design note's measurements settled that the
record holds JSON, that a GeoPackage has no topology extension and the
NAME needs saying early, that the tiling's topology is the unit's, and
that the unit and its dual are stored as LAYERS (R-45, R-46, R-47,
R-48, R-49, R-50). The
scipy question closed itself: upstream dropped the spline and the
vendored tree imports no scipy (R-51). The string-assertion study
recommended its own deletion, the practice living where it already is
(R-52). Accounts R-88.

**Give the stochastic hunt an exported-file invariant that RUNS.** Added
2026-08-16. A hunt over 105 checked steps reported its five axes: holes
103, tile totals 103, opacity pairing 23, values-on-no-data 23, and the
GeoPackage comparison ZERO. That last axis never executed, so a green
run said nothing whatever about the exported file while looking like
full coverage. (R-53.)

**THE TILED-FRAME CACHE IS BUILT** (maintainer's question, 2026-09-05,
answered the same day). The join is purely geometric -- an argmax on
area keeping a tile id against a zone id -- so a variable switch was
paying for a tiling it already had: 1.034 s of a 1.36 s run at spacing
250. The frame is held per key on the dialog, full width, served
inside the worker, switched by `Keep tiles between runs` on Map
options; the key is `_geometry_signature(without_variables=True)`, the
signature itself and not a copy, and `_only_this_elements_data` is an
allowlist so the privacy of ruling 6 holds BY CONSTRUCTION. The
differential `a cached switch draws what a retile draws` caught a
frame held by reference before the cache ever ran. Columns on the
layer and a hidden layer were both refused. Accounts R-89.

**OWED: THE VARIABLE SWITCH ON THE RESTYLE PATH**, to the three rulings
of 2026-09-05 in CLAUDE.md. `gdf_to_layer` is the largest term once the
tiling is cached -- 0.239 s at spacing 250, 1.728 s at 150, sixty
microseconds per drawn feature -- and `split_out_the_no_data` makes a
switch a change of layer MEMBERSHIP, so the route is to rewrite the
value column in place and move only the tiles that cross the no-data
boundary, declining and rebuilding where a switch makes or unmakes a
twin. Measured by `tools/probes/how_many_tiles_cross_on_a_variable_
switch.py`: the packaged Auckland data crosses 0.0% because its nulls
sit in the same six areas for every variable, and a synthetic
multi-source shape crosses 20.2% at worst, so the design must be
correct at any rate and fast at the common one. WHAT IS OWED BEFORE ANY
CODE is a differential over THAT path -- feature by feature, field
names included, on nulls in different places, a constant column, two
values against five classes and a permutation of two elements'
variables -- because the existing one exercises the full-run path and
would go on passing while the fast path drew something else, which is
the shape of the three previous signature narrowings. Four hazards: the
table name carries the variable; the twin's membership is the
variable's business; the landing carries most of this project's
rulings and assumes a layer just built; a held layer keeps its
renderer, which is what makes a stale one invisible.

**Sampling the six unsampled assignment-lookup copies.** Deferred here
from 0.24.2 deliberately: it is measurement rather than
defect-finding, and the night of 2026-08-13 put mutation sampling at
zero product defects across 128 survivors. `_assignment_for` now holds
the lookup, so a future mutant has one place to land.

**Three things the 2026-08-13 instruments audit left undone**, all of
them about tools that produce numbers people then believe. (The fourth
landed on 2026-08-15: `check_standards` now reads every catalogue entry
with `ast` and fails when its anchor is absent, after seven entries were
found anchored on text that no longer existed; a sweep run by hand
still gets no preflight, and that is the part of the fourth that
stands.) TWO OF THE THREE ARE STILL OWED, and naming them is the point
of the entry: three `EQUIVALENT` catalogue entries exclude nothing, and
a stall must not count toward a printed rate until it has been re-judged
alone -- a stall counts as caught, so a false one flatters the score.
(R-54.)

**SHOULD A CATALOGUE ENTRY BE ABLE TO BREAK TWO SITES?** Raised
2026-08-28 while deciding the drifted entries, and recorded rather than
done because it is a change to campaign machinery in the middle of a
candidate. `tools/mutation_check.py` applies exactly ONE replacement per
entry, deliberately -- an entry names one site, and mutating several
would make its verdict mean nothing. (R-55.)

**SAVE AS A SINGLE OGR SESSION WENT INTO 0.24.4 AND IS BUILT**
(`bridge.write_gpkg_layers`; R-56, R-90).

**Two mutation measurements, neither of them defect-finding.** The
expensive stratum, which nothing has ever measured -- 1,172 of the
1,488 reachable mutants, and the cheap stratum's 59% says nothing
about them. And a certification batch, once the suite stops changing,
since improvement rounds cannot certify themselves.

**PAIR INLINE SPANS WITHIN A PARAGRAPH, NOT ACROSS A WHOLE DOCUMENT.**
(Recorded 2026-08-31 rather than done, because it changes
`tests/run_tests.py` while a candidate's suite result is standing.)
`test_every_documented_command_still_exists` finds inline spans with a
pattern applied to the WHOLE document, deliberately, because a span may
wrap across a line and the gate has to join it. (R-57.)

## 0.24.5 — what is left once the re-vendor moved to 0.24.4

**THE RE-VENDOR WENT INTO 0.24.4 INSTEAD**, late on 2026-08-31, on the
maintainer's decision ("we want the revendor now") once the Topology
tab's rebuild turned out to sit on top of it. What it did is recorded
under 0.24.4, where it landed. The rest of this section stands.

**AND A QUESTION THE MERGE RAISED: SHOULD `for-**` BRANCHES GET CI?**
`ci.yml` triggers on `[main, "pre-**"]`, so work parked on a
`for-<version>/*` branch -- which is this project's OWN convention for
work meant for a later release -- is never seen by a second machine
until it is merged. (R-58.)

**THE RE-VENDOR'S RECORD**: `0.0.7.89 (bf1bbbf)` to `0.0.7.89
(6190917)`, twelve commits with the version string unmoved, which is
why the stamp records a commit; a differential was built for it since
no gate here asks whether the library's own output moved; and the next
re-vendor has a measured price on it (R-59, R-60, R-61; R-91).

## Waiting on the upstream project

Blocked on the weavingspace project rather than on this repository, so
no release waits for it.

**Element ids past 26, FOR WEAVES ONLY.** The tiling half of this entry
LANDED on 2026-08-27 and what remains is the weave half, which is
genuinely upstream's. Three routes were set out here rather than one,
because compressing them is how the reasoning gets misremembered, and
they stop in three different places. *Using the capitals as well* — a..z
then A..Z, 52 ids — is blocked by GEOPACKAGE CASE FOLDING, and that part
is measured rather than argued: writing `tiles_a` and then `tiles_A`
into one file leaves a single table holding the second element's data,
with both writes reporting success (2026-08-14). (R-62.)

**Two conversations to have.** Whether the corrected large-plain-weave
note was sent (`docs/process/upstream-note-large-plain-weaves.md`
supersedes the first, which blamed a commit wrongly), and the WEAVE
half of the element-id ceiling above, which is upstream's decision
rather than ours now that the tiling half is built.

**THREE PERFORMANCE FINDINGS ARE PATCHED AND OFFERED UPSTREAM**: the
grid disc reached two thirds of its tiles outside the region (R-63,
patch 4), and the join lookup was a Python loop that `.agg("idxmax")`
runs up to 191x faster with ties breaking identically (R-64, patch 3);
the table in MAINTAINING.md says where each was offered. **ZIGZAG'S
REPEATED VERTICES ARE FIXED UPSTREAM AT THE SOURCE**, in commit
`b3650e0`, exactly what this project had measured independently, so
that conversation is closed (R-65, R-66, R-67; R-92).

## Later, or never

**THE PRODUCT STALL OF R-4 IS IGNORED UNTIL IT RECURS.** (Maintainer's
decision, 2026-09-05.) QGIS accepted a topology build, left it Queued
with the pool idle and never started it: 4 in 86 attempts inside one
twenty-minute window, then none in 317 with the discriminator armed.
The DEFENCE stays built -- `TOPOLOGY_START_CEILING_MS` arms a watch and
`_say_if_the_build_never_started` writes the reason into the panel's
note (R-6) -- and the probe that would catch a recurrence is
`tools/probes/how_often_a_build_never_starts.py`, which adds a second
task at the stall and reads whether the stuck one then starts. Nothing
here is evidence it has gone; a recurrence reopens it (R-5, R-76; the
whole account R-80).

**CANCEL A RUN THAT IS ABOUT TO BE SUPERSEDED.** The third of the three
debounce questions, and the only one the decision of 2026-08-26 left
open. The other two are settled: the preview wait is a floor that widens
to whatever a rebuild costs, and the two debounces stay separate.
(R-68.)

**Deriving the aggregate coverage from the per-test record** (was
`for-0.24.1/coverage-dedupe`, commit 34dab50bd0cd, branch deleted
2026-08-12). It made `coverage_report --from-record` write the aggregate
from what the per-test recorder already collected, so the suite would
not run twice under monitoring. Dropped because its premise went away
the same week it would have landed: both coverage stages left the
release path, so nothing automatic measures twice any more. (R-69.)

**A "two views of one truth" differential campaign.** Recorded here
rather than started, because it is a session's work and the case for it
is an argument about where effort pays rather than a defect waiting to
be fixed. The plugin describes the same state in several places that
must agree -- the table, the design preview, the generated map, the
colour editor, and the saved project. PART OF THIS IS NOW BUILT, which
narrows what is left rather than closing it; what still needs deciding
is what a disagreement between two of those views would MEAN, which is
the part that is not coding. (R-70.)

**THE TEXT-REVIEW QUEUE SHOWS THE MAINTAINER THINGS THEY CANNOT JUDGE.**
(Maintainer's observation, 2026-08-26: an SQL statement -- `DELETE FROM
layer_styles WHERE f_table_name = '%s'` -- reached the queue, and "that
string is irrelevant for me to approve".) Recorded rather than acted on,
because the fix is not obviously an improvement: the filter is
deliberately over-inclusive, and the day it skipped strings opening with
`{` it dropped three live user-facing sentences unread. (R-71.)

**Badges on the README**, and the "minimalist faux 3d" button styling
the user mentioned. Both cosmetic, neither designed.

**The custom ("this") weave type**, with its tie-up, treadling and
threading matrices. Deprioritised rather than rejected: it needs a
matrix-entry UI and its own documentation.
