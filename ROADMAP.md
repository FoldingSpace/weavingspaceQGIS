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

**WORK IS OUTSTANDING AGAIN, AND THE EARLIER DECLARATION IS RETIRED
RATHER THAN CONTRADICTED.** The maintainer declared this section clear
on 2026-09-01, and that was true of what was known then. Five field
reports against `0.24.4rc15` and one suite failure arrived on
2026-09-04, so the declaration is struck HERE rather than left standing
beside a list of owed work -- the release gate reads this section for
that phrase, and a section that both declares itself clear and lists
defects would clear a candidate while the defects were live. (R-2.)

### Owed: one suite failure of two, the other closed

**THE SUITE REPORTED TWO FAILURES, NOT ONE**, and reading the shards
separately is what said so: 260 passed, 259 passed, and 257 passed with
2 failed. The three totals agree at 778, so the slice was a partition.

**THE VENDORING TOOL FAILURE IS CLOSED**, and it was this session's work
rather than upstream's. `the vendoring tool reproduces the current
vendor` went red at 0.1s because two pairs of patches CHAIN -- patch 6
anchors on the block patch 3 produces and renames what it binds, and
patch 5b rewrites the tail of the method patch 4b produces -- so on the
tool's own fixed-point check, where every patch must report "already
present" against our own vendor, patches 3 and 4b reported ANCHOR NOT
FOUND and the tool exited 1. That is the sentence reserved for an anchor
UPSTREAM has moved, and it is the one message a re-vendorer has to be
able to trust. (R-3.)

**THE TOPOLOGY MATRIX FAILS ONE CELL OF THIRTY-ONE**, and this is what
is still open:

    crosses 4 n=4 / after re-Generate / rotate_edge:
    the tab neither built a topology nor said why not, so somebody is
    left in front of a panel that never answers

**THE MECHANISM IS MEASURED AND IT IS NOT WHAT IT LOOKED LIKE.** At the
moment of failure, driven alone on an idle machine at CONTENTION 1.0:
NEVER ANSWERED after 72.7s manager: count=1 active=1 'WeavingSpace
topology' Queued global thread pool: active=0 max=8 python threads:
['MainThread'] The build is QUEUED AND NEVER STARTED, WITH THE POOL
IDLE. So it is not a slow build, not a worker holding a thread and not
the plugin looping: QGIS's task manager never runs it, and the dialog
waits on a `_topology_task` nothing will ever clear while the tab says
"Working out the design's structure…" for ever. (R-4.)

**TWO CORRECTIONS, BOTH TO THIS PROJECT'S OWN FIRST REPORTS OF IT, and
both the same fault -- a rate quoted from too few draws.** It is
INTERMITTENT rather than deterministic: 3 failures in 34 attempts on a
quiet machine, then 0 in 16. AND A TWO-ARM SPLIT OF 2 OF 8 AT HEAD
AGAINST 0 OF 8 AT `a3efb48` IS NOT EVIDENCE about this session's tiling
patches, because HEAD then produced 0 of 16 on its own. (R-5.)

**THE DEFENCE IS BUILT, AND IT DOES NOT CLAIM TO BE THE DIAGNOSIS.** A
tab that never answers is the reported failure whatever QGIS is doing,
and `showEvent`'s zombie-task recovery could not reach it -- that covers
`_task`, has no twin for `_topology_task`, and counts Queued as ALIVE.
So `TOPOLOGY_START_CEILING_MS` arms a watch when the task is added and
`_say_if_the_build_never_started` puts the reason in the panel's note,
which means "the answer, or why there is none" and is what every waiter
reads. (R-6.)

**WHAT IS STILL OPEN IS THE CAUSE**, and it is recorded as open rather
than closed by the repair: why QGIS accepts a topology build, leaves it
Queued and never starts it, while later builds run normally. The
discriminator that would settle it rides in
`tools/probes/how_often_a_build_never_starts.py` -- at the stall it
adds a second task and reads whether the stuck one then starts -- and
the stall has not yet been caught with it armed.

**AND IT NOW HAS A ROUTE AND A VOICE, 2026-09-05.** THE ROUTE: running
the suite three-sharded on this Mac reproduces it. Three full runs gave
1, 0 and 2 failures -- `a QGIS symbology edit reaches the plugin on
every shape`, `the drop keeps the picture it was showing`, `a design
that cannot carry its edits still draws` -- every one of them a
topology test, and every one passing alone. That is a cheaper
reproduction than waiting for CI, and it is what the probe has been
missing.

THE VOICE: `_wait_for_the_topology` used to give up by returning False,
so twenty-one tests reported whatever bare sentence each carried --
several of them "PREMISE: no topology" -- and the two failures above
could not say whether the build never started, was still running, or
had REFUSED IN WORDS. That last is not a stall at all and would have
been read as one. The waiter explains itself now, at the waiter rather
than at the twenty-one callers, with `_why_the_topology_tab_is_busy`
naming which term is still outstanding. Guarded by `a topology wait
that gives up says why`, which is the positive control for a path that
otherwise runs only on a rare failure, and its entry is proved
`caught`.

SO THE NEXT OCCURRENCE DIAGNOSES ITSELF, which is what the cause needs:
the shape of the answer decides where to look, and until now every
occurrence has cost a reproduction to learn nothing.

**AND THE VERY NEXT RUN ANSWERED IT, AND IT IS NOT THE STALL.** The
armed failure printed: "The panel says ''; it holds a topology; the
change list holds 1 edit(s); A BUILD IS STILL IN FLIGHT". So the waiter
had returned while the rebuild was running, and the topology the caller
then measured was the PREVIOUS one -- neither a stall nor a refusal,
but a HARNESS RACE.

`_settle_topology` returned on a single tick with no `_topology_task`,
and that is true in the window between an edit being RECORDED and its
build being QUEUED, while the panel holds the old topology throughout.
It is the fault this suite's own `_wait_for_the_topology` was written
to fix, left standing in its sibling -- a fix applied to the instance
somebody found rather than made a rule -- and it accounts for all three
intermittents, since all three settle that way. Under three-shard
contention the window is wide enough to land in; alone it is not, which
is why every one of them passed in isolation.

QUIET MUST NOW PERSIST: three consecutive clear checks, 600ms, longer
than the queueing gap and far shorter than a build at 0.75s on the
cheapest design. All three tests pass, and a full three-shard run over
`03d6ba7` was GREEN at 264, 264 and 264 -- 792 of 792, each shard
naming the same total.

**AND IT FIRED ON WINDOWS CI TOO**, which is worth knowing because it
says the window is not a peculiarity of this Mac: `tests` went red on
`2dc4d0b` with `the drop keeps the picture it was showing` and the
same 0.0 map units. That commit predates the repair, so the Windows
arm is a confirmation waiting to happen rather than an open question;
the run on `fa3158d` is the one to read.

**AND THE STALL DID NOT REPRODUCE IN 317 ATTEMPTS**, hunted the same
day with the discriminator armed
(`tools/probes/how_often_a_build_never_starts.py`): 117 before a
session ended and 200 after, none of them stalling.

THE RECORDED 4-IN-86 IS REJECTED at about 3 in ten million, and so is
contention as the trigger -- the loaded arm caught nothing either. The
original four were a CLUSTER, and 86 attempts inside one twenty-minute
window is itself too few draws. 452 draws is the point at which trying
harder to provoke it stops being the cheapest move, so the effort moves
from REPRODUCING it to CATCHING it. (R-76.)
SO THE SUITE'S STALL MESSAGE NOW NAMES WHAT QGIS'S OWN MANAGER HOLDS
-- the count, the active count, and every task's description and
status. Until 2026-09-05 `_why_the_topology_tab_is_busy` reported four
DIALOG-SIDE terms alone, so it could say a build was in flight and not
whether it was RUNNING or sitting Queued with the pool idle, which is
the whole of the difference between a slow machine and this defect.
Guarded by `a topology wait that gives up says why`, whose first
version walked only the no-panel path -- the catalogue entry SURVIVED
and said so, which is what a catalogue is for.

NONE OF THIS IS EVIDENCE THE STALL HAS GONE. Nothing in this week's
work touches the task manager, the defence is unchanged, and a defect
that clusters is one a quiet afternoon says nothing about. THE PRODUCT STALL OF R-4 IS
UNTOUCHED AND STILL OPEN -- it was measured with the pool idle and the
task Queued, which is a different thing. What has changed is that the
suite no longer reports a race as though it were that stall.

### The sweep for the snap-back: done, one fault found

**A TRANSIENT PICTURE IS CLEARED BY THE THING THAT REPLACES IT, NOT BY
THE ACT THAT REQUESTED THE REPLACEMENT** -- C-244, paid for by field
report 1. ONE INSTANCE MENDED IS NOT A RULE ENFORCED (maintainer's
instruction, 2026-09-05), so every store in this interface whose
replacement arrives asynchronously was enumerated and asked the same
two questions: WHO empties it, and does that actor stand where the
replacement lands.

THE ONE FAULT IS FIXED AND WAS FOUND AT THE FIRST SITE. The Topology
tab's PARAMETER BOXES were torn down and rebuilt at their defaults by
every build that landed -- `set_unit` to `_refresh_classes` to
`_refresh_manipulations` to `_rebuild_arguments` -- so `n` typed as 6
and `h` as 0.6 came back 2 and 0.25 on an ordinary journey. That is
field report 2. Values are remembered per manipulation now, guarded,
and the catalogue entry is proved `caught`.

TEN OTHER STORES WERE ASKED AND ARE SOUND, each for a reason worth
keeping so the sweep is not run again from nothing: the preview, the
tab's note, its working sentence, the symmetry line, the zigzag
readout, the live note, the progress text, the two deferred notes, the
design preview, and the assignment table's cell widgets -- that last
one sound by an EXISTING rule rather than by this sweep, which is worth
the distinction. (R-73.)
WHAT THE SWEEP IS WORTH KEEPING FOR is the question rather than the
table, which will age: for anything the interface shows and later
replaces, name the actor that empties it and the actor that fills it,
and where those differ, ask what happens in between. The fault it
found was invisible to reading -- both halves are healthy code, and
only the INTERVAL between them is wrong -- and it was caught by a test
premise rather than by an eye.

### Owed: five field reports against 0.24.4rc15

Reported by the maintainer on 2026-09-04, driving the DEFAULT design
(`laves 3.3.4.3.4`, four elements) on the packaged Auckland data. The
installed build was checked before any code was read: both profiles
carry `0.24.4rc15` from commit `09b6ef2`, which CONTAINS all three of
the drag-and-landing fixes, so none of these is a stale build.

1. **A DROP PUTS THE UN-EDITED DESIGN BACK FOR A SECOND. FIXED
   2026-09-04.** The preview is KEPT on the path that records an edit
   and the landing clears it -- `show_topology` sets `_preview = None`
   as its own third line, and every route to an answer passes through
   it -- while every path that records NOTHING clears at once, because
   there no landing is coming and a preview would describe an edit the
   change list denies. Guarded by
   `test_the_drop_keeps_the_picture_it_was_showing`, which reads ONE
   PUMP after the release: the claim is about an INTERVAL, and settling
   first would read the answer that arrives afterwards and pass
   whatever happened in between. Two catalogue entries, one per answer,
   both proved `caught`.
   AND A SURVIVOR NAMED THE ARM THAT WAS MISSING: the test's discard
   arm was a CLICK, which leaves at the drop's FIRST exit and never
   reaches the travel test at all. Three exits are three journeys, not
   three lines.
   WHAT IS LEFT OPEN DELIBERATELY is the journey where no rebuild
   follows -- the preview then goes on showing what the person asked
   for, which agrees with the change list, where reverting would show a
   design the list denies. It wants a state rather than a timer. (R-72.)

2. **A ZIGZAG DOES NOT STICK. DRIVEN, FOUND AND FIXED 2026-09-05, and
   it was not the mechanism reading had suspected.** EVERY BUILD THAT
   LANDED RESET EVERY PARAMETER BOX TO ITS DEFAULT. The chain is
   `set_unit` to `_refresh_classes` to `_refresh_manipulations` to
   `_rebuild_arguments`, which tore the boxes down and made fresh ones;
   measured by driving a landing, `n` typed as 6 and `h` as 0.6 came
   back 2 and 0.25, silently, on an ordinary journey. So the numbers a
   person set were not the numbers their edit was made with. The values
   are remembered per manipulation now and restored on the rebuild,
   guarded by `a build landing does not eat the numbers you typed` with
   its positive control, and the catalogue entry
   `a-landing-keeps-the-numbers-somebody-typed` is proved `caught`.
   IT IS THE SNAP-BACK IN A DIFFERENT STORE -- C-244's rule that a
   transient thing is cleared by whatever REPLACES it, with a build
   landing as the passing actor and a spin box as the store -- which is
   why the sweep above matters and why it found this one first.
   THE MECHANISM READING HAD SUSPECTED IS STILL THERE AND IS NOT THIS,
   kept because it is a live question about the threshold: a drag
   previews continuously, and on release `_commit_the_drag` asks
   `_drag_moved`, which for `zigzag_edge` is `abs(h) > 0.01` -- one per
   cent of the edge's own length. Below that the preview is cleared and
   NOTHING IS RECORDED, so a shallow zigzag is drawn while the pointer
   is down and gone when it comes up, with no sentence anywhere. That
   is a click choosing a class, which is the intended behaviour; what
   is unproved is whether the threshold sits where a person's "I meant
   that" does, and amplitude is the one parameter whose useful values
   start small.
   ONE CANDIDATE IS ELIMINATED, recorded so nobody re-reads it: the
   drag does NOT drop the count. `args = dict(self._arguments())` seeds
   every parameter from the boxes and the drag overrides one key, so
   `n` travels with the edit.
   TO DRIVE IT: record the h a real gesture produces at the zoom the
   tab opens at, against 0.01. If a comfortable zigzag lands under the
   threshold the number is wrong; if it lands well over, the fault is
   elsewhere and the next suspects are the refusal path in `apply`
   (which returns sentences the tab may not be showing) and
   `_make_drawable`, since zigzag is the manipulation that emits
   coincident vertices.
3. **THE NUMBER OF ZIGZAGS CANNOT BE SET FROM THE DRAWING. BUILT AND
   GUARDED 2026-09-05**, to the rulings in CLAUDE.md: along-edge travel
   of the zigzag handle sets the count, past a deadband of a tenth of
   the edge sized from the glyph itself, and the count snaps because
   the stops are the counts. (R-74.)
4. **THE ZIGZAG HANDLE SITS TOO FAR FROM ITS EDGE. BUILT AND GUARDED
   2026-09-05**, and it was a DEFECT rather than a matter of spacing:
   the offset was a static 60 while the code claimed that distance WAS
   the amplitude. The zero sits on the edge now, the glyph rides the
   wave's first peak, and the wave is ghosted along the edge with four
   painted cues saying what the two axes do. (R-75.)
5. **"MAP THE DUAL" ERRORS WHILE THE TAB DRAWS A DUAL PERFECTLY WELL.
   DRIVEN AND RULED ON 2026-09-05, and the reading was wrong about the
   mechanism.** On the packaged Auckland data, default design, no
   modifiers, on HEAD and on rc15 alike: ticking the box asks the
   Topology tab for a topology OF the dual, which the library's edge
   merge raises on; `_why_not` turns every exception into the "gaps"
   sentence, which is false of this design; and the landing's next
   call, `report([])`, erases the reason `set_unit` had just written,
   so the tab goes blank. No modifier is needed, which retires the
   reading above. AND THE MAP ITSELF HAS HOLES: the library's
   `generate_dual` carries its own TODO that the dual does not exhaust
   the plane, and measured in unit space the default design's dual
   covers 77% of the ground (4 tiles of 6), archimedean 4.8.8 50% and
   hex-colouring 3 50%, while five other designs are complete.
   Choosing an interior vertex per base set completes all three, and
   the library builds the snub-square tiling from its own catalogue,
   so the remaining refusal of the default design's dual is in our
   promotion. Five rulings, in CLAUDE.md under "THE DUAL: FIVE RULINGS
   OF 2026-09-05"; the work is owed just below. The probes are under
   `dev/probes/fr5_*`, arms A to L. (R-79.)

### Owed: the dual button, and three settled conflicts (2026-09-05)

**rc16 WAITS FOR THESE**, on the maintainer's decision (ruling 3 of
the dual). Cheapest and most durable first.

- **THE DUAL BUTTON IS BUILT** (2026-09-05, later the same day).
  "Generate the dual and tile it" on the Topology tab lands the dual
  in a NEW group named `<group> — dual` through the chooser's own
  "Create new" door; the store stays the record's `map_dual` term, a
  box that is kept but never shown because thirteen readers speak its
  language, with a label beside the button that follows the store;
  elements are assigned fresh by the ordinary landing; the button is
  disabled with its reason where there is no topology, no dual the
  library can lay out, or a dual short of full cover. Driven on the
  synthetic fixture: six dual layers beside the source's four, the
  source untouched, and both groups restoring from their records with
  the label right. Two registered tests, three entries proved
  `caught`. 34 sentences now sit in the text-review queue.
- **THE DUAL IS COMPLETED HERE AND OFFERED UPSTREAM -- DONE** (same
  day): `complete_dual` builds one tile per source vertex with every
  copy's centre taken as its base tile's centre translated; coverage
  1.000000 on eight designs and the library builds a Topology of each,
  the default design's included. The differential and a two-arm
  canary are registered; the note is
  `docs/process/upstream-note-the-dual-is-truncated-and-drifts.md`.
- **THE TWO TAB DEFECTS ARE FIXED AND GUARDED** (2026-09-05, later the
  same day): `_why_not` measures whether the tiles cover their cell
  before it blames a gap, and a landing's `report([])` no longer erases
  the reason `set_unit` wrote. Two registered tests, three catalogue
  entries proved `caught`. AND THE TWO TOPOLOGY MODULES JOINED TEXT
  REVIEW AND THE HARD-RULE CHECK, having spoken to users since
  2026-08-30 with neither reading them: 27 sentences are in the queue,
  which is the maintainer's to read.
- **THE SHELF REPORTS AT REPLAY -- DONE** (was conflict 7; built
  2026-09-05, later): every edit records the class alphabet it was
  made against at the panel's one recording door, so a drag and the
  Apply button both carry it; `apply` compares it with the design it
  replays onto and, where they differ, applies what its labels name
  now and SAYS the classes moved, in one template whose mark a guard
  looks for. The key stays family, count, dual. Guarded as a matrix
  aftermath, "after a modifier splits the classes", on both kinds of
  route by name: the tab must speak exactly when the alphabet moved
  and stay quiet when it did not. Entry proved `caught` against the
  matrix.
- **THE READER ASSIGNS THE DESIGN'S OWN ELEMENTS -- MEASURED, AND
  ALREADY SO** (was conflict 1, 2026-09-05, later). Driven rather than
  coded, on the maintainer's note that a test per item is not the
  method: a six-element record with its `n` lowered to four was applied
  through `_apply_working_state`, and the table came back with four
  rows carrying the record's own first four variables, the surplus two
  ids keeping their ramp, reverse and opacity records as memory
  (`dev/probes/conflict1_a_record_with_more_elements_than_its_design.py`).
  The one caveat, said plainly: on widening back to six the surplus
  rows re-derive their VARIABLE by the cycling default rather than
  reading it off the record, which is the ordinary count-change
  behaviour and not this record's; if a person's variable is to be
  memory too, that is a widening of ruling 6 and a decision. No code
  changed and no test was added; the record is a faithful superset
  and the reader already reads it as the ruling says.
- **THE PDF MEASURES THE VENDOR -- DONE** (was conflict 5, 2026-09-05,
  later): the PDF's reference caption, the report tool's own docstring,
  MAINTAINING.md's release section and CLAUDE.md's suite section all
  name `TiledMap.render` from the vendored library at its recorded
  commit and say the web app is not spoken for; the old three-way
  paragraph is C-263. Nothing here is text a plugin user meets, so the
  review queue is untouched by it.
- **AND A GENERAL AUDIT OF THE TOPOLOGY TAB** (maintainer's ask,
  2026-09-05: "audit the topology tab more generally to make sure it
  functions as expected"), after the items above: every control and
  every handle driven on the packaged Auckland data as a person meets
  them, with live update at its default, and every store read at each
  step -- the shape field report 5 needed and reading did not supply.
- **THEN A RE-AUDIT OF THE BINDING DOCUMENTS** (maintainer's ask,
  2026-09-05): "make sure they say what they need (for LLMs) but no
  more", moving more into the `-archived.md` halves. The measure is
  the rule plus about one clause of evidence, applied a second time
  now that the first pass and its audit have settled what the shape
  is, and read entry by entry to the end rather than by length.
- **AND THE SAME EDIT TO THE DOCSTRINGS** (same ask): "they're not
  terribly useful for human maintainers right now, though of course
  we want them to be effective for LLMs as well". The documentation
  standard in CLAUDE.md still governs -- inputs, outputs, the
  QGIS-shaped reasoning at the line -- and what goes is the narrative
  that belongs in a commit or an archive: the day, the wrong first
  hypothesis, the measurement that decided it. Where a docstring's
  account is the only record of a measurement it moves to an archive
  rather than being deleted, which is the same rule the documents
  keep.
- **TWO STUDIES, ALSO THE MAINTAINER'S ASKS OF 2026-09-05**, recorded
  as questions with no code: IS THERE A BETTER WAY OF STRUCTURING THE
  TILING AND LAYER DATA BEHIND THE SCENES, for efficiency or for fewer
  defects -- the tiled frame, the per-element layers and their twins,
  the records keyed by tile id, the group's working state -- and IS
  dialog.py OVER-COMPLEX in ways a simpler approach would match
  exactly while being less bug-prone. Both want an audit that names
  candidates with a measurement each, and neither is to be done in the
  same breath as a candidate. The ledger of 2026-09-02 and the
  catalogue triage of 2026-08-28 are where the defect shapes to weigh
  them against are counted.

Worked on `pre-0.24.4rc1`. What follows is what the version delivers,
and what each piece of it cost to prove.

**AND THE CANDIDATE IS BUILT: `0.24.4rc10`, from `663f77d`.** Every gate
green -- the roadmap and branches, the standards check, the secrets
audit, the functional suite at 26 minutes, the visual gallery at 13 of
13 and the colourspace comparison at dE means of 0.30 to 0.42, the
published-content audit, the zip and its receipt. (R-7.)

**AND rc10 IS SPENT, WHICH IS THE DOCUMENTED TRADE RATHER THAN A
WASTE.** CI went red on its commit -- one test, on its own premise, "the
chosen vertex offers no handle to drag" -- so no later fix can publish
it. (R-8.)

**AND `0.24.4rc11` IS BUILT FROM `4b643c7`, WITH EVERY LOCAL GATE
GREEN**: the roadmap and branches, the standards check, the secrets
audit, the functional suite at 29 minutes, the visual gallery, the
colourspace comparison, the published-content audit, the zip and its
receipt. (R-9.)

**AND rc11 IS SPENT TOO, ON TWO SUITE FAULTS AND NO PRODUCT DEFECT.** CI
answered for `4b643c7` on 2026-09-02: `mutation` green, `windows` and
`macos` green, three installs and three galleries green, `suite
(stable)` green, and the two remaining Linux legs red on ONE TEST EACH
-- different tests, one per leg, which is the tell that both are about
timing rather than about the plugin. (R-10.)

**THE CAMPAIGN REACHED ITS TWENTY-FOUR, AND THE ROUND THAT DID IT ADDED
TWO RULINGS ON TOP.** Ledger rows 22 to 26 close round seven: the resume
stamping a stranger's coordinate system onto somebody's region and the
repair for it overriding the group's own record; the edit shelf unable
to tell a design from its dual; the close question that covered a
promise and a write with one sentence; and a Load that threw a promised
save away. (R-11.)

**AND `0.24.4rc14` IS SPENT, ON FOUR CEILINGS SIZED FOR THIS MAC.** Its
software is rc13's, measured member by member and identical bar
`metadata.txt`; `mutation` was green on its commit and `tests` was not.
The 4.0.3 leg failed `a drag is measured in the frame it began in` on
its PREMISE after ninety seconds -- 771 passed and 1 failed of one shard
of three -- while the next topology test on that same runner passed in
4.3 seconds, which is what says the tab was healthy and only the
allowance was local. (R-12.)

**AND A THIRD HYPOTHESIS ABOUT THE TEARDOWN ABORT IS REFUTED, 2026-09-05,
BEFORE ANYTHING WAS SHIPPED ON IT.** Recorded because a refuted
hypothesis is worth as much as a confirmed one here: two guesses at the
destruction ORDER have already been made and neither held, and this is
the third thing not to try.

THE HYPOTHESIS was that `dlg.deleteLater()` followed by `_tick(100)`
does not actually destroy anything, because Qt delivers a
DeferredDelete event at the loop level where `deleteLater` was called
and `_tick` runs a NESTED QEventLoop -- so the dialog would outlive the
block, and the provider would be destroyed later, against a file the
`finally` had already removed. It fits the abort's shape exactly:
`corrupted double-linked list`, one CI leg per round and a different
leg each time, which is what a race looks like when read as a version
difference.

IT IS SIMPLY FALSE ON THIS BUILD: asked of the C++ object with
`sip.isdeleted` rather than of Python's `__del__`, a nested `_tick(100)`
destroys it and `sendPostedEvents` adds nothing. The order was right and
so was the timing; the cause is still unknown. (R-77.)
**AND THE TEARDOWN ABORT IS NOT 4.0.0'S, WHICH IS A CORRECTION.** Exit
134, `corrupted double-linked list`, at `project.clear()`. It was
recorded as 4.0.0's alone; on the next round it fired on `stable`
instead, with 4.0.0 -- by then skipped -- green. (R-13.)

**AND `0.24.4rc13` IS SPENT TOO, ON A SUITE FAULT AND NO PRODUCT
DEFECT.** Every local gate passed on `6e40574` and CI's coverage leg did
not: `a build that lands mid drag does not wipe the gesture`, 256 passed
and 1 failed on one shard of three, each naming the same total of 772.
It failed on its MAIN assertion this time rather than on a premise, and
the product was innocent -- the test read its subject before the clicks
that find a handle, and a landing arriving in that window is adopted
correctly. (R-14.)

**AND `0.24.4rc12` WAS BUILT GREEN AND SPENT WITHIN THE HOUR**, which
is the documented trade rather than a waste: every stage passed, the
suite's three shards read 257 each against one total of 771, and the
tree it measured does not carry the Load ruling that followed. No
later commit can make an earlier candidate publishable, so `rc13` is
built from the merged tree instead.

**AND THE 24-BUG CAMPAIGN IS RUNNING, WITH THIRTEEN CLOSED ON ITS FIRST
DAY.** The seven below were the first round; six more came from a second
round of three hunts, replenished as bugs closed, and every one is again
reproduced here by a route its hunt did not use, repaired, guarded and
proved. (R-15.)

**THE FIRST ROUND'S SEVEN, kept because the reasoning is what a later
session will not have.** (Maintainer's instruction, 2026-09-01: keep
eight hunts going on temporary worktrees, replenishing after each bug is
fixed and committed, until twenty-four are repaired and tested.) The
plan is in `docs/process/HUNT-RECORD.md`, the watcher is
`tools/hunt_campaign_watch.sh`, and the ledger is
`docs/process/defects-2026-09-02.md`. (R-16.)

**ONE LINE CARRIES 0.24.4**, and it is `pre-0.24.4` -- renamed on
2026-09-05 from `pre-0.24.4rc7`, which named a candidate NINE behind the
tree and read to anybody glancing at it as a version. The work branches
merged into it long ago: `for-0.24.4/copy-select-all` carried the Save
work and `for-0.24.4/saving-is-an-act` is an ancestor of that; both are
kept only so their history reads, and nothing is owed on either. (R-17.)

**THE DRIFTED CATALOGUE IS DONE**, decided entry by entry on 2026-08-28
and written up in `docs/process/catalogue-triage-2026-08-28.md`: nine
re-aimed or re-anchored and proved `caught`, twelve retired with their
measurement and the redundancy written at the test, four accepted with
the condition that would reopen each, and five tests made materially
stronger. (R-18.)

**AND ONE DEFECT FOUND AFTER THE CATALOGUE ROUND**, fixed on 2026-08-28
and carried by `0.24.4rc3`. With live update off, a Generate pressed
while a run was in flight did nothing at all and said nothing: the press
was queued on the live-rerun flag and handed to the live path, which
declines whenever live update is off. (R-19.)

**THE CHANGELOG LINE IS WRITTEN AND APPROVED, 2026-09-01**, and what
follows is why it took a second pass rather than what it owes. It was
approved once on 2026-08-29 and went stale in the way this project's own
rule warns is most expensive: the version then took on the re-vendor,
the rebuilt Topology tab, nine defects and four features, all of which a
user meets. (R-20.)

**THE ROUND OF 2026-08-28 RAN A THIRD WAVE, and it is now much the
largest this project has run.** Fifty-five hunts in all. Twenty-three
further claims came out of the third wave; TEN were closed the same
evening (ledger rows 37 to 46), and FIFTEEN went onto a written owed
list in `docs/process/defects-2026-08-28.md`.

**AND THE OWED LIST WAS TAKEN TO THE END ON 2026-08-29**, on the
maintainer's instruction to keep the claims and fix them rather than
defer them. FOURTEEN of the sixteen are closed -- rows 47 to 60 -- each
verified here by a route its hunt did not use, repaired, guarded by a
registered test and proved by a catalogue entry. (R-21.)

**NOTHING ENDS WHILE A SAVE IS OUTSTANDING -- BUILT, AND ONE PIECE OF IT
IS OWED.** (Maintainer's ruling, 2026-09-01.) A waiting window holds a
quit or a window close while a save is promised or being written, says
what it is waiting for, and offers Cancel; the quit is DELAYED rather
than vetoed, so a wedged save can never trap somebody in QGIS. Closing
the plugin asks first, with Save as the default, and Save means WAIT FOR
THE REDRAW rather than write the map they had already changed away from.
(R-22.)

**AND A SIXTH RULING OF THE ROUND, THE MAINTAINER'S, ON 2026-08-29: A
SAVE PRESSED WHILE A RE-TILE IS COMING IS KEPT RATHER THAN REFUSED.**
Ledger row 54 had closed a real defect -- a press inside the live
debounce wrote the map the person had just changed away from -- by
refusing the press in words. The maintainer overruled that on a ground
no measurement here would have produced: most people will not read the
sentence, so a refusal that depends on being read is a save that
quietly did not happen. The press is kept, the notice says the map will
be saved after it is redrawn, and a third deferred kind honours it once
the new map has landed -- asked from three places, because a landing
alone cannot cover a run that declines.
IT ALSO REPAIRED TWO REGRESSIONS ROW 54 HAD SHIPPED (row 62), both
registered tests that press Save with live update at its default and
both measured red at `d809027` before any of the day's edits: the
targeted runs that verified row 54 never ran them. What a user gets is
in the changelog line owed below.

AND ONE MEASUREMENT IS THE MAINTAINER'S RATHER THAN OUTSTANDING WORK:
the assembled window is 1279px under the offscreen font every runner
uses and **1334px against its own 1280 ceiling under the real macOS
system font**. At that font the three settled layout priorities of
2026-08-09 cannot all hold. Which one gives is a decision.

WHAT THE THIRD WAVE GIVES A USER. A Save into a GeoPackage holding
somebody else's map no longer deletes their element tables and their
embedded copy of the data. Opening the map you have just saved no
longer loses it to a live re-tile that leaves the project empty on
reopen. Choosing your own map's group no longer empties the region
chooser and every element's variable, which it did whenever the
outlines layer was on. The dependency consent box names every
distribution it will fetch rather than six fewer, and a support package
lost to a dropped connection is no longer discarded in silence while
setup reports success. The notice that says the data has moved since a
map was drawn now speaks about the map being saved rather than about
whichever dataset the chooser holds, works for a map opened with Load,
and can see an ordinary value edit -- which is the case it was written
for and could not report. In icon mode a geographic layer is no longer
told that every element reaches none of its areas. And a saved file
never holds a no-data twin belonging to an element the map does not
have.

FOUR OF THOSE TEN WERE DEFECTS IN THE SAME EVENING'S OWN REPAIRS, which
is the rate this project's record predicts and does not improve with
practice.

AND `tools/probe_kit.py` CAME OUT OF IT: the forty lines every probe
was re-typing, written once, with the instrument faults that recur here
prevented at the line. The reasoning is in docs/TESTING.md.

**AND THE ROUND OF 2026-08-28, whose first two waves are below.**
Twenty-three hunts kept at eight at a time and replenished as each
reported, with the consistency sweep rebuilt beside them as a committed
tool. Twenty-four confirmed defects, the ledger in
`docs/process/defects-2026-08-28.md`, the directions and what each
taught in `docs/process/HUNT-RECORD.md`. (R-23.)

**THE SIX OPEN DECISIONS WERE PUT TO THE MAINTAINER ON 2026-08-29 AND
ALL SIX WERE SETTLED.** Recorded here because the reasoning is what a
later session will not have, and because two of them turn into work
this version now owes.

1. **Numbers stored as text are classifiable** -- BUILT, with a test
   and two proved entries. The rule is narrowed to its own evidence
   and `_field_is_numeric` is the one owner; strict, so a column with
   a word in it stays categorical. Reasoning in CLAUDE.md.
2. **The window ceiling gives at the columns**, not at the preview
   floor and not at 1280 -- BUILT. The columns grow to what their
   content needs and the ceiling is 1480, derived from the
   measurement rather than defended by a check, because setting a
   font is not switching a platform: the minimum size hint reads 1279
   at both 9pt and 13pt offscreen where cocoa gives 1334, so no guard
   here or on CI can see the window's own overshoot at all.
3. **Save becomes responsive now** -- BUILT. The write loop turns the
   event loop once per element behind a determinate progress bar, so
   the window says what it is doing instead of looking like a hang,
   and Save and Generate are disabled for the duration and restored
   to what they WERE: pumping is exactly what would otherwise let
   somebody press into a half-written file, so the two are one
   decision. The COST is untouched and deliberately so -- making the
   save a single OGR session is a rewrite of the writer and is under
   0.24.5 below.
4. **The guide's Save sentence is reworded** to say what Save actually
   asks -- it asks where the file holds a map made from OTHER DATA,
   which is what the ruling of 2026-08-27 settled. Done in the guide
   and the Help tab; the wording is in the review queue.
5. **`check_standards` requires a catalogue anchor to be unique as
   well as present** -- already true since 2026-08-28, and the ledger
   paragraph calling it undone has been corrected.
6. **`mutation_check` does NOT gain a list of replacements.** Anchor
   the whole decision instead, which cannot be split again by the next
   alternative somebody adds; where two sites are genuinely distant,
   retire with the measurement written at the test.

**AND ONE QUESTION WAS THE MAINTAINER'S RATHER THAN OUTSTANDING WORK,
AND IS NOW DECIDED** (item 1 above; what follows is how it stood). A
quantitative style never stands on a text field, and the stated reason
is that a graduated renderer over text comes back with no ranges.
(R-24.)

**THE DECLARATION STAYS WITHDRAWN, AND WHAT IT COVERS HAS CHANGED.** Six
things were owed after rc5 went out. FIVE ARE BUILT, on 2026-08-30, each
with a registered test and catalogue entries proved `caught`; the sixth
was the window ceiling, and it is built too -- see "AND THE SIXTH IS
BUILT TOO" below, which is the paragraph this sentence used to
contradict. (R-25.)

**AND THE SIXTH IS BUILT TOO, WHICH CLEARS THE SECTION.** 8. **THE
WINDOW IS BOUNDED BY THE SCREEN IT IS ON.** `_within_the_ screen` clamps
every path that resizes the dialog to `SCREEN_SHARE` of
`availableGeometry`, and all three resize sites go through it -- the
opening size, the fit to the Design tab, and the growth the assignment
table asks for. (R-26.)

**THE DECLARATION WAS WITHDRAWN ON 2026-08-30 (late) AND IS STILL
WITHDRAWN, with one thing left rather than three.** The maintainer
reported the Design tab's alignment, spacing and sizing as "just
nonsensical" against a screenshot; the work that followed is now
committed and guarded, and this is where it stands. - THE DESIGN TAB'S
THREE BARE ROWS, at `34ea0aa`, with fourteen layout guards passing. -
THE SECOND PASS, at `02dc3e6`: spacing on its own row, one field width
shared by four rows so they end at one edge, the Transformations label
column aligned with the rows above, `Auto` no longer painted as the
default button, and the window sized by the tab in front -- 825px on
Design where it opened at 1296, growing to 1296 for Data & colours.
(R-27.)

**AND THE DECLARATION IS WITHDRAWN AGAIN, LATE ON 2026-08-31.** It went
back earlier that day and the version has since taken on the RE-VENDOR
and the Topology tab's rebuild, on the maintainer's decision to merge
both into this version rather than hold them for 0.24.5 ("we want the
revendor now"). (R-28.)

**THE FOUR APPROVED FEATURES ARE IN 0.24.4, GRILLED AND THEN BUILT ON
2026-09-01.** All four are in, each with a registered test and catalogue
entries proved `caught`: the label/key separation and the twelve common
names, multi-class selection, the symmetries drawn and gating, and the
dual as a design. (R-29.)

**THE ELEMENT SLIDER KEEPS ITS RANGE AND THE FLIP SPEAKS.** (Same
grilling.) Weave families run n=2 to 12 and tilings to 256, so from 13
up only tilings exist and `test_design_cascade` requires the kind toggle
to flip -- silently, today. (R-30.)

**AND THE `publish_candidate` QUESTION IS MOOT, MEASURED RATHER THAN
DECIDED.** The worry recorded here was that a genuine sampling survivor
would one day block a candidate and start the `--despite-ci` habit. It
cannot: every measuring step in `mutation.yml` is `continue-on-error` --
the catalogue sweep, `mutate_auto` on changed lines, the census and the
gallery render -- so a survivor cannot redden that workflow at all.
(R-31.)

## 0.24.5 — three tabs asked for, and what was deferred here from 0.24.4

Moved on the maintainer's decision of 2026-08-27, in the act of
cutting 0.24.4's candidate. None of it is abandoned and none of it
was blocking the version: three are measurements rather than
defect-finding, and the fourth is a study whose answer is written
at its own entry.

**AND ALL THREE ARE EXPERIMENTAL UNTIL DESIGNATED OTHERWISE, BEHIND A
BOX THAT IS UNTICKED BY DEFAULT.** (Maintainer's ruling, 2026-08-30.)
The **Experimental features** checkbox goes under the THIRD tab, which
is *Map options*. (R-32.)

**THE LIVE-UPDATE SWITCH IS ON THE TOPOLOGY TAB AS WELL, AS A SECOND
VIEW OF ONE FACT. BUILT AND GUARDED 2026-09-05.** `live_check` remains
the single owner and the only thing any reader asks; the tab's box is
bound to it symmetrically with signals blocked, in the dialog rather
than the panel. It is NOT the two-controls-one-fact fault of C-43,
which was two controls with different SEMANTICS aimed at one outcome.
Guarded by `one live update switch seen from two tabs`, which holds
both halves -- each box moves the other, and nothing asks the view what
it holds. (R-78.)
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

**A TOPOLOGY TAB: visual and quantitative interaction with what the
library already computes, and then past it.** `topology.py` is the
richest thing in the vendored library that the plugin does not currently
expose at all. It carries `Topology`, `Tile`, `Vertex` and `Edge`; it
can enumerate potential symmetries, generate a tiling's DUAL and hand
back its tiles; and it offers real MANIPULATIONS rather than only
description -- `zigzag_edge`, `rotate_edge`, `scale_edge`,
`push_vertex`, `nudge_vertex`, `insert_vertex_at`,
`merge_edges_at_vertex`, `transform_geometry`. (R-35.)

**THE TOPOLOGY TAB WAS GRILLED ON 2026-08-30 AND FIVE THINGS ARE
SETTLED.** The maintainer asked for an interactive tab with numeric and
click-and-drag editing, round-tripping through the GeoPackage, built
when the map is generated and kept up to date, with the races checked.
(R-36.)

**WHAT OF THE FIVE IS BUILT, as of 2026-08-30.** Recorded against the
rulings rather than as a narrative, so the gap is readable at a glance.
WHICH VERSION IT SHIPS IN IS THE MAINTAINER'S DECISION and the entry
stays in this section until they make it; the code is on
`for-0.24.4/copy-select-all` behind the experimental box, which is what
makes that decision cheap either way. - Ruling 1, the un-modified unit:
BUILT. `topology_edits.build` takes the motif before aspect and insets,
and the tab says so on its face. - Ruling 2, built on Generate off the
main thread and never on colour: BUILT. `_queue_topology` hangs off
whatever rebuilds the unit, and `_topology_stamp` throws away a build
whose design has moved on. - Ruling 3, an edit list governs: BUILT, and
so is its second half. (R-37.)

**THE INTERACTION WAS AUDITED AND REBUILT ON 2026-08-30, and what it
still owes is here.** The maintainer asked whether it was intuitive
first time, powerful, and whether better alternatives existed; the
audit answered no, moderately, and yes, and the rebuild that followed
is described in MAINTAINING.md under "How somebody takes hold of it".
Select-then-act, handles that ARE the choice of manipulation, a hit
test that follows the edge, and three highlight states are built.

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

TWO DESIGNS CAME OUT OF THE AUDIT. THE FIRST IS BUILT AND THE SECOND
IS REFUSED, both on 2026-08-31.

1. **A HANDLE IS A POSITION, NOT A DELTA -- BUILT.** Turning travel
   into a parameter needs a LEVER, and a lever is a gain factor nobody
   can see: half the edge's length made a 34px drag invert the edge,
   and the full length still turned a 35px drag into a scale factor of
   0.28. The end handle starts half a length from the edge's middle,
   so where the pointer has taken it IS a polar coordinate about that
   middle -- the scale factor is how far out it sits, the rotation is
   the angle it makes, the diamond's perpendicular distance is the
   amplitude. Nothing to tune, and each handle is a READOUT as well as
   a control.
2. **ONE END HANDLE INSTEAD OF TWO -- REFUSED, not deferred.** Moving
   an endpoint is exactly (angle, length) in polar coordinates about
   the midpoint, so scale and rotate really are two halves of one
   gesture, and it would remove a handle and the crowding with it.
   WHAT DECIDED AGAINST IT is the maintainer's standard of the same
   day: the handles must be "shapes that make sense ... for what they
   do", and one handle would have to say TWO things, which is the one
   thing a glyph cannot do. It would also record two edits from one
   gesture, which is honest and makes the change list harder to read
   back and to roll back through -- and rolling back one or two edits
   is a requirement of its own.
   THE CROWDING WAS ANSWERED THE OTHER WAY: the view fits the UNIT
   rather than the 36-tile patch, the seats are 12px, and the three
   edge handles sit at 0 and 30px of perpendicular offset rather than
   0 and 16. If the merged handle is wanted later, that is the argument
   it has to beat.

**AND EVERY MANIPULATION IS NOW REACHABLE ON THE DRAWING**
(maintainer's instruction, 2026-08-31: "all interactions in that
topology image, not just one"). `push_vertex` was reachable only
through the chooser and the Apply button; it has a rail now, drawn
along the one direction a push can take, with no handle at all where
that direction cancels -- which on laves 3.3.4.3.4 and hex-slice 3 it
exactly does, the incident unit vectors summing to 1.5e-9.

**`push_vertex` IS SETTLED, AND IT WORKS: WHERE IT MOVES NOTHING THAT IS
A FACT ABOUT THE DESIGN.** (Measured 2026-08-31, closing a question this
section had left open since the grilling.) The suspicion was that
`transform_geometry` discarded the displacement vector upstream's
`push_vertex` returns rather than applying it (`topology.py:1482`).
(R-38.)

**THE REGRESSION FROM THE REBUILD IS CLOSED, AND IT WAS TWO FAULTS
RATHER THAN ONE.** (2026-08-31.)
`test_an_edit_for_a_class_that_has_gone_is_reported` was reported as
failing with its message unread. Read, it said the plugin had stayed
SILENT about an edit aimed at a class the design does not have -- and
the two reasons are worth keeping, because the second had been making
the same report unreachable on every design since it was written.
(R-39.)

**AND A TOPOLOGY MATRIX EXISTS**, five manipulations crossed with
designs found from the catalogue and three aftermaths, spine plus a
seeded sample. Its first honest run failed thirteen of thirty-one and
TEN were the harness's own -- a fingerprint reading only the unit's
envelope, which a vertex pushed inward does not move, and a settle
waiting on the ABSENCE of a build task, true before the build is queued
as well as after it lands. The survivor was real and is fixed: a
manipulation can be accepted, be drawable, and change nothing.

**THE DEFAULT STRAND WIDTH STAYS AT 0.75, having been changed to 1.0 and
changed back the same day** (maintainer, 2026-08-30). Recorded rather
than quietly reverted, because the reasoning that prompted it is sound
and somebody will propose it again. THE CASE FOR RAISING IT: aspect is a
family OPTION rather than one of the modifiers ruling 1 builds before,
so at 0.75 the Topology tab is unavailable for every weave by default.
(R-40.)

**ZIGZAG'S TROUBLE IS REPEATED VERTICES, AND IT IS PROPERLY
COMPENSABLE.** (Measured 2026-08-30 across two maintainer challenges,
each of which corrected a reading of mine: "zigzag should work where the
two ipynb shows it working right?" and then "are the zigzag problems
floating point errors? And if so can you compensate properly?") WHAT THE
NOTEBOOK ACTUALLY SHOWS. Driven exactly as `topology-working.ipynb`
drives it -- `TileUnit(tiling_type="chavey", code="K")`, every edge
class, `n=2, h=0.25, smoothness=3` -- TWELVE OF TWENTY tiles come back
invalid. (R-41.)

**AND THE AUTHOR ANSWERED IT ON 2026-08-30, WHICH SUPERSEDES THAT
SENTENCE.** Their words: "I can recover valid polygons from the ones it
makes with `tiling_utils.get_clean_polygon`", and "there's probably some
doubling up of coordinates happening". The second half is this project's
own measurement arriving from the side that wrote the manipulation,
which is agreement rather than correction; the first half is a function
ALREADY IN OUR VENDOR that does the job better than the repair written
here. THE HABIT WORTH CARRYING: before writing a repair for a
dependency's output, grep the dependency for one. (R-42.)

**AND CLICK-AND-DRAG IS AFFORDABLE, which the first reading of the cost
said it was not.** One edit costs 1.23s end to end on the fastest design
-- 0.15s for the transform and 1.08s to rebuild the Topology, which
upstream's own caution requires ("new Topology will probably not be
correctly labelled ... rebuild from the tileable"). (R-43.)

**WHAT THE NOTEBOOKS GAVE, on the maintainer's instruction to mine them
for the workflows their authors imagined.** `topology-working.ipynb`
plots with seven toggles -- original tiles, tile centres, vertex labels,
edge labels, edges, offset edges, dual tiles -- which is the view the
tab owes; it plots tiling symmetries (`plot_tiling_symmetries`); and it
promotes the dual to a TileUnit of its own, calling
`_setup_regularised_prototile(override=True)`, which is the step
`transform_geometry` does not do and which the tab will need. (R-44.)

**AND THE MAINTAINER'S DESIGN NOTE -- build the topology when the tiling
is built, and store it in the transportable GeoPackage -- MEETS TWO
MEASUREMENTS, taken 2026-08-29 before any of it is designed.** Recording
them here because they change what the note can mean, and because a
decision is only as good as the measurement under it. (R-45.)

**THE FILE ALREADY CARRIES JSON, AND THE MECHANISM IS THE ONE THE RECORD
USES.** `bridge.write_working_state` opens the GeoPackage with
`gdal.OpenEx(path, OF_UPDATE)` and calls `SetMetadataItem(
"WEAVINGSPACE_STATE", json.dumps(record))`, which lands in the format's
own `gpkg_metadata` table; `read_working_state` takes it back out with
`GetMetadataItem` and `json.loads`. (R-46.)

**AND NO, A GEOPACKAGE CANNOT STORE GEOSPATIAL TOPOLOGY, WHICH TURNS OUT
NOT TO MATTER -- THE TWO THINGS SHARE A WORD AND NOTHING ELSE.** (Asked
by the maintainer, 2026-08-29; checked against the OGC extension
registry and GDAL's own GPKG driver documentation rather than from
memory.) There is no topology extension to GeoPackage, adopted or
community: the registry lists WKT for CRS, Tiled Gridded Coverage and
Related Tables as the official three, and a dozen community ones for
vector tiles, styling, 3D tiles and the rest, with nothing for a
node/edge/face model. THE ONE THING TO CARRY FORWARD IS THE NAME: a tab
called "Topology" will be read by some GIS users as promising the
node/edge/face kind, and it does not, so wherever it is called that it
has to say early and plainly that it describes the repeating unit and
not the map. (R-47.)

**AND THE MAINTAINER'S OWN FRAMING SHARPENS ALL OF THAT: this project
has THREE kinds of layer -- the original data, the tiling over the whole
space, and the element layers which unioned together ARE that tiling --
so it is the TILING'S topology that is at stake.** That is right, and it
does not argue for a topology model over the output, because a tiling is
PERIODIC: the adjacency structure of the whole tiling is already
determined by the unit and its neighbouring copies, which is exactly
what `Topology` is built on. (R-48.)

**THE THIRD DESIGN DISAGREED, AND THE DISAGREEMENT IS THE USEFUL PART.**
On hex-slice 6 the unit reported NINE pairs and the geometry seven.
Classifying every contact by what it actually is: the seven share
288.675 map units of edge, and the two extra -- b-e and c-f -- have a
maximum shared length of 0.0 and intersect as a POINT. They touch at a
corner. (R-49.)

**SO: STORE THE UNIT AS A LAYER, AND THE DUAL BESIDE IT.** Both are tiny
-- n polygons and the dual's handful -- and it makes the file
self-describing: somebody opens the GeoPackage and sees the motif and
its dual without needing the plugin at all, which is the same argument
that put the element tables and their styles in there. (R-50.)

**AND FIND OR WRITE AN ALTERNATIVE TO PULLING IN THE WHOLE OF SCIPY.**
(Maintainer's instruction, 2026-08-29.) `zigzag_edge` is the one
manipulation that reaches outside numpy, and it does so at exactly ONE
line -- `topology.py:1418`, inside `zigzag_between_points`: spline =
interpolate.InterpolatedUnivariateSpline(x, y, k = 2) scipy is optional
in the vendored library and is NOT in `deps.py`, so that call raises a
clear ImportError today. (R-51.)

**FOR STUDY: warn when a test asserts a string that also appears in
shipped source.** Added 2026-08-16, deliberately as a question rather
than a rule. That is exactly what rotted that day: a test asserted `"no
value" in said`, the maintainer reworded the notice to "do not have
finite numeric data", and the test failed on every platform while
looking like a Windows fault -- a second copy of the wording with no
mechanism keeping the two in step. SO THE RECOMMENDATION IS TO DELETE
THIS ENTRY, keeping the practice where it already is -- compose the
expected text from the function the product uses. (R-52.)

**Give the stochastic hunt an exported-file invariant that RUNS.** Added
2026-08-16. A hunt over 105 checked steps reported its five axes: holes
103, tile totals 103, opacity pairing 23, values-on-no-data 23, and the
GeoPackage comparison ZERO. That last axis never executed, so a green
run said nothing whatever about the exported file while looking like
full coverage. (R-53.)

**CACHE THE TILE-TO-ZONE LOOKUP, SO CHANGING WHICH VARIABLE AN ELEMENT
SHOWS STOPS BEING A RE-TILE.** (Maintainer's question, 2026-09-05.)
Recorded rather than started, and the reading behind it is done.

WHY IT IS POSSIBLE AT ALL, which is the part worth having: the join is
NOT about the variable. `get_tiled_map`'s overlay computes an argmax on
AREA and keeps `["joinUID", id_var]` -- a tile id against a zone id --
throwing the fragments away. So the expensive half of a Generate is
purely geometric and gives the same answer whatever attribute is
displayed. `_geometry_signature` says the opposite in its own
docstring, "a new variable does need new geometry", and that is true of
the CODE as it stands rather than of the problem.

WHAT IT WOULD SAVE, measured 2026-09-03/04 rather than projected. At
spacing 250 with 10,502 drawn tiles a Generate spends 1.034s in the
worker -- `Tiling.__init__` 0.654s, overlay and join 0.378s -- against
0.322s in the landing. At spacing 150 it is about 2.1s of 3.8s. All of
the worker's share is what a cached lookup would let a variable switch
skip; what would remain is attaching the new values to the cached
lookup, and `gdf_to_layer` at 0.239s, which is 60 microseconds per
drawn feature and the largest single term once the tiling is gone.

AND THE SECOND HALF OF THE QUESTION IS THE INTERESTING ONE. If the
element layer CARRIED every candidate column rather than one, a switch
would not even rebuild the layer: it is a renderer change, `seed_
renderer` at 0.030s, which is the "light redraw" this project already
has for ramps and class counts arriving at variables too.

WHICH IS WHERE IT MEETS A SETTLED RULING AND MUST BE GRILLED. Ruling 6
of 2026-08-25 trims element tables to the symbolised variable, and
accepted "switching a variable RE-TILES from the source" as the price;
the colleague's argument for carrying every column was refused there.
THE TWO HALVES OF THIS ARE NOT THE SAME QUESTION, though, and the
ruling only answers one:
- IN MEMORY, for the session, touches no file and no ruling. Nothing
  is written, nothing can reach a colleague's copy, and the privacy
  argument that carries ruling 8 does not apply. This half is
  unblocked and is where most of the measured prize is.
- IN THE FILE, or on the layer QGIS holds, is ruling 6's ground and
  reopens it. The maintainer asks whether that wastes storage; the
  honest answer is that SIZE IS NOT WHAT THE RULING RESTS ON. Geometry
  dominates attributes in a GeoPackage, so k numeric columns against
  one is a modest addition -- measurable, and worth measuring before
  anybody argues from it. What ruling 6 rests on is PRIVACY: a file
  somebody sends on should not carry columns they never displayed,
  which is ruling 8's "value-laden records never cross" seen from the
  other side.

**AND THE PRIVACY RULING IS TO BE PRESERVED** (maintainer, 2026-09-05),
which decides the shape: the cache is a PLAIN PYTHON OBJECT ON THE
DIALOG -- never a layer, never a layer field -- so the ruling holds BY
CONSTRUCTION rather than by a guard somebody has to remember at every
writer, which is the failure mode this project keeps paying for.
THREE FACTS MAKE THAT AIRTIGHT, all of them already true.
`_save_the_map` builds its write list by iterating ELEMENT IDS (`for
step, tid in enumerate(order, 1)`) rather than the group's children, so
it cannot write something it does not know about. QGIS serialises
LAYERS into a `.qgz`, not a dialog's attributes. And the precedent is
exact: `_classification_values` and the dissolved-extent cache are
already fingerprint-keyed, memory-only and per-layer, with the
cache-of-one lesson recorded at them -- keep other layers' entries,
because replacing the whole dict on a miss gave a twenty-three element
design a hit rate of zero.

BOTH ALTERNATIVES FAIL, and the reasons differ. COLUMNS ON THE ELEMENT
LAYER leak and self-defeat: `write_gpkg_layers` reads each layer
through its own provider so every field reaches the file, and
`point_layer_at` repoints the layer at the GeoPackage afterwards, so
the extra columns vanish at the first Save -- the cache would die
silently exactly when somebody saves. A HIDDEN LAYER IN THE OUTPUT
GROUP is safer than it looks, since the save would not write it and a
memory layer round-trips through a `.qgz` with no features, both
measured here already; but it is still a QGIS object a person can see,
rename, reorder or delete, and a name a user can edit is not an
identity. A cache somebody can drag out of a group is a cache that
vanishes without saying so.

**AND CAN THE `gdf_to_layer` TIME BE SKIPPED TOO?** (Maintainer,
2026-09-05.) It is the biggest single term once the tiling is cached --
0.239s at spacing 250 and 1.728s at 150, a steady 60 microseconds per
DRAWN feature -- so it is the right thing to ask about next. There is a
route and there is a fact in the way, and the fact is worth knowing
before anybody designs around it.

WHAT IS IN THE WAY: `split_out_the_no_data` puts the rows a graduated
renderer cannot draw into a PAIRED layer, and which rows those are
depends on the field, its floor and its ceiling. So a variable switch
changes layer MEMBERSHIP and not merely values, which is why it cannot
be answered by rewriting attributes alone.

THE ROUTE, THEREFORE, IS TWO STEPS RATHER THAN ONE: rewrite the value
column IN PLACE through the provider -- which skips re-encoding every
geometry, and geometry is what the 60 microseconds is mostly made of --
and then move only the tiles that CROSS the no-data boundary between
the element layer and its twin.

**WHAT IT WOULD ACTUALLY TAKE, read out 2026-09-05 so the next session
does not have to.** Per element, on a cached switch: add the new
variable's field, `changeAttributeValues` over every feature, delete
the old field, move the crossers between the layer and its twin, and
re-seed the renderer. Steps one to three are provider operations that
touch attributes and never geometry, which is where the saving is.

AND FOUR THINGS MAKE IT MORE THAN THAT, each a place a WRONG MAP could
come from, which is this software's characteristic failure:
- THE TABLE NAME CARRIES THE VARIABLE. `element_table_name` composes
  `tiles_<tid>_<variable>`, so a switch renames the destination and the
  stale-table drop has to agree about which name is now stale.
- THE TWIN'S MEMBERSHIP IS THE VARIABLE'S BUSINESS. Measured, a
  multi-source dataset crosses 20.2% of tiles at worst, so "move only
  the crossers" is thousands of features, and a feature that lands in
  neither layer is a hole.
- THE LANDING CARRIES MOST OF THIS PROJECT'S RULINGS -- the stamps, the
  styles, the group binding, the exclusions, the pins re-read at the
  landing -- and every one of them assumes a layer that was just built.
- AND A HELD LAYER KEEPS ITS RENDERER, which is what the restyle path
  exists to exploit and what makes a stale one invisible here.

**GRILLED AND SETTLED 2026-09-05, three rulings, in CLAUDE.md.** A
switch that makes or unmakes a twin DECLINES and rebuilds, keeping the
prohibition `_restyle_only` has carried since the holes came back; so
it is an EXTENSION of the restyle path rather than a third one, with
the bare variable name leaving the geometry signature while
`_needs_a_no_data_split` stays in it -- which expresses the first
ruling in the signature that already exists; and it does not ship
without a differential over THAT path, on the awkward shapes.

WHAT IS OWED BEFORE ANY CODE: the differential. The one built today
exercises the FULL-RUN path and would go on passing while the fast
path drew something else, which is the exact shape of the three
previous signature narrowings -- each a wrong map that looked right.

THE OLDER NOTE, kept because it is the reasoning the rulings answer: `a cached switch draws what a
retile draws` compares the two paths feature by feature including the
field names, and it is what caught the last wrong map this ground
produced. The saving is worth having -- 1.728s at spacing 150 against
0.239s at 250 -- and it is not worth taking on the same day as the
cache it sits on.

AND THE NUMBER IS NOW MEASURED, 2026-09-05, by
`tools/probes/how_many_tiles_cross_on_a_variable_switch.py`, asked of
`bridge.split_out_the_no_data` itself rather than of a second copy of
its rule. IT TAKES TWO ARMS TO SAY ANYTHING, and the first alone would
have been a lie:

    packaged Auckland, spacing 250, 10,579 tiles     0.0% cross
    each variable null in a different tenth          20.2% cross (worst pair)

THE PACKAGED DATA CANNOT EXHIBIT THE CASE. Its nulls sit in the SAME
six areas for every variable -- the one reported from the field in
2026-08-16 that is null in everything -- so every pair crosses exactly
zero tiles, and a design tuned on that number would meet a multi-source
dataset and fall over. The synthetic arm is the honest shape for a
census table joined to a health table joined to a crime table, each
with its own suppressed cells.

SO THE DESIGN MUST BE CORRECT AT ANY RATE AND FAST AT THE COMMON ONE.
The crossing set is computable exactly and cheaply -- a set symmetric
difference over the joined frame, which the cache already holds -- so
the rule is: rewrite the column in place, move exactly the tiles that
cross, and fall back to a rebuild above a share to be measured once
both paths exist. Correctness never depends on the rate; only the
saving does.

**GROUNDWORK BUILT, 2026-09-05, in two pieces that stand on their own.**
THE KEY: `_geometry_signature(without_variables=True)` blanks the two
terms that say which variables are mapped and which element carries
which, and keeps everything else -- the grid, the unit, the modifiers,
the layer's fingerprint and data version. That is what a TILING depends
on and a variable switch does not. It is the signature ITSELF rather
than a copy, because "what changes the tiles" has been widened three
times and each fix landed in that one function; a second enumeration
would have to be widened a fourth time by somebody who did not know it
existed, which is how a cache starts answering with a map of something
else. Guarded by `the tiling key ignores variables and nothing else`,
which asserts BOTH halves -- a variable switch moves the signature and
not the key, anything else moves both -- with the second being the half
that would draw a wrong map. Entry proved `caught`.
THE TRIM: `_only_this_elements_data` is an allowlist over the source's
columns rather than a blocklist over the mapped ones, so a cache that
joins every candidate variable cannot leak one onto a layer and from
there into the file. That is ruling 6 held by construction rather than
by the cache remembering to.

**AND THE CACHE IS BUILT, 2026-09-05.** The frame is held per key on
the dialog, served inside the worker so every piece of the landing
machinery is untouched, and carried FULL WIDTH -- every column the
layer has -- because guessing which one somebody will reach for is the
one thing a cache like this cannot do (maintainer's ruling). The price
of full width is memory on a wide table at a fine spacing, and it is
answered by a switch on Map options, `Keep tiles between runs`,
defaulting ON: whoever cannot afford it turns it off and pays a
re-tile per switch, which is what they had before. A MISS IS ALWAYS
SAFE -- it costs a regenerate and nothing else -- so correctness never
depends on the width, the bound, or the switch.

THE DIFFERENTIAL IS THE ONLY TEST THAT MATTERS FOR IT, and it earned
its place immediately. `a cached switch draws what a retile draws`
drives the same variable switch twice, once served from the cache and
once with caching off, and compares the element layers feature by
feature INCLUDING THE FIELD NAMES. It caught a real defect before this
ever ran: the frame was held BY REFERENCE, and
`count_units_without_tiles` strips the tracing column off the frame it
is handed -- so the cache stored a frame missing a column, the run
served from it died before the landing, and the element layers went on
showing THE VARIABLE SOMEBODY HAD SWITCHED AWAY FROM. A wrong map that
looks entirely right, invisible to every other test in the suite. It
holds a copy taken before the count now, and the catalogue entry
`a-held-tiling-is-a-copy-not-the-frame-itself` breaks exactly that.

SO THE RECOMMENDATION IS TO SPLIT IT: build the in-memory cache as a
dialog-held object, which needs no ruling and takes the worker out of a
variable switch, and put the carry-every-column question to a grilling
on its own, with the file size measured first so the argument is about
privacy rather than about a number nobody has.

WHAT WOULD HAVE TO BE TRUE FOR THE CACHE TO BE SAFE, since a cache that
is wrong is worse than a slow map: it is keyed by everything
`_geometry_signature` already names EXCEPT the mapped variables, and
that key is the whole of its correctness. A topology edit, a modifier,
a spacing change, a new region layer or a re-tile of moved data must
all miss it -- and the fingerprint this project already computes for a
layer's contents is what would tell it that the data underneath moved.

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

**SAVE AS A SINGLE OGR SESSION WENT INTO 0.24.4 INSTEAD**, on
2026-09-01, on the maintainer's decision that quadratic time in saving
and loading is unacceptable to ship. It stood here from 2026-08-29, when
it was split off rather than folded into 0.24.4's candidate; the entry,
its equation and what the rewrite has to preserve are under 0.24.4,
where it now lands. (R-56.)

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

**THE RE-VENDOR'S OWN RECORD, kept here because the reasoning belongs
with the version that planned it.** `0.0.7.89 (bf1bbbf)` to
`0.0.7.89 (6190917)`, twelve upstream commits, with `topology.py` at
+179/-207 and `_tiling_geometries.py` at +44/-67; the third changed
file is a notebook that does not ship.

**THE VERSION STRING DID NOT MOVE**, which is the whole reason the stamp
records a commit. A version comparison alone reports us current, and
did. WHAT IT COST AND WHAT IT FOUND, kept because the shape recurs at
every re-vendor. (R-59.)

**AND A DIFFERENTIAL WAS BUILT FOR IT, because no gate here can answer
the question a re-vendor actually raises.** The colourspace comparison
scores the plugin against `TiledMap.render` from the SAME vendored
library, so a change upstream moves both sides together and they go on
agreeing; the suite asks whether the plugin's rules hold, not whether
the library's output moved. (R-60.)

**AND THE NEXT RE-VENDOR HAS A MEASURED PRICE ON IT, WHICH THIS ENTRY
DID NOT HAVE.** (2026-09-01.) Upstream's `experimental` branch carries
four commits on top of what we vendor, one of them saying Topology
construction is "now a bit quicker". (R-61.)

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

**AND EXPLOITING THE TILING'S OWN PERIODICITY, RAISED BY THE MAINTAINER
2026-09-03 AND MEASURED THE SAME DAY.** Two thirds of the tiles
generated at a realistic spacing lie wholly OUTSIDE the region -- 11,786
of 17,248 on the packaged Auckland data -- built, carried into the
overlay, clipped away and discarded. (R-63.)

**AND A THIRD, MEASURED 2026-08-31: THE JOIN LOOKUP IS A PYTHON LOOP.**
`tile_map.py` builds the tile-to-region lookup with
`.agg(pd.Series.idxmax)`, and passing the FUNCTION defeats pandas'
cython path -- it falls back to `_aggregate_series_pure_python` and
walks every group in Python. `.agg("idxmax")` is the same answer by the
fast path. spacing tiles groups callable method ratio 400 13,460 4,230
0.069s 0.002s 41x 250 32,436 10,526 0.173s 0.001s 141x 150 86,768 28,619
0.476s 0.003s 182x 100 191,184 63,684 1.076s 0.006s 191x END TO END
through the plugin's own path, old vendor against patched:
`get_tiled_map` goes from 2.68s to 0.94s at 86,768 tiles and from 3.21s
to 1.91s at 191,184. TIES BREAK IDENTICALLY, staged rather than hoped
for -- on a frame built with exact ties the callable, the method and the
string all return the first occurrence of the maximum. (R-64.)

**AND A THIRD, RAISED 2026-08-30: `zigzag_edge` EMITS REPEATED
VERTICES**, which shapely reports as self-intersections and which make
the result untileable. On `chavey` code K -- the design their own
`topology-working.ipynb` zigzags -- twelve of twenty tiles come back
invalid, and one of them carries six coincident point pairs among
thirty-seven points. (R-65.)

**AND UPSTREAM HAS NOW FIXED IT AT THE SOURCE, SO THIS CONVERSATION IS
CLOSED.** (Measured 2026-08-31 at the maintainer's asking.) Commit
`b3650e0`, *"fixed bug in zigzag edges code where it was doubling up
tiling vertices and creating invalid polygons"*, is two lines: the
endpoints were added once as `edge.vertices[0]`/`[-1]` and again from
`ls.coords`, which includes them. - new_corners = [... for xy in
ls.coords] - edge.corners = edge.vertices[:1] + new_corners +
edge.vertices[-1:] + new_corners = [... for xy in ls.coords[1:-1]] +
edge.corners = [edge.vertices[0], *new_corners, edge.vertices[-1]] That
is exactly what this project measured independently on 2026-08-30, and
it is the question this entry said was worth sending: whether
`zigzag_between_points` should stop emitting the coincident vertices
rather than every consumer cleaning up after it. (R-66.)

**THE EARLIER STATE OF THIS ENTRY, kept because the reasoning still
instructs.** They said "there's probably some doubling up of coordinates
happening" -- the same fault, reached independently from the two sides
-- and pointed at `tiling_utils.get_clean_polygon`, which recovers valid
polygons and which the plugin now uses as its first repair stage.
(R-67.)

## Later, or never

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
