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
MAINTAINING.md under "Three queues".
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

**THE ROUND OF 2026-08-28 RAN A THIRD WAVE, and it is now much the
largest this project has run.** Fifty-five hunts in all. Twenty-three
further claims came out of the third wave; TEN were closed the same
evening (ledger rows 37 to 46), and FIFTEEN went onto a written owed
list in `docs/process/defects-2026-08-28.md`.

**AND THE OWED LIST WAS TAKEN TO THE END ON 2026-08-29**, on the
maintainer's instruction to keep the claims and fix them rather than
defer them. FOURTEEN of the sixteen are closed -- rows 47 to 60 --
each verified here by a route its hunt did not use, repaired, guarded
by a registered test and proved by a catalogue entry. Twenty commits.

WHAT THAT GIVES A USER, in the order somebody would care. A Save As
now tells the map where it went, so coming back to it does not revert
the box to the file you saved away from and overwrite the older
version. A colour picked in the editor reaches a map you OPENED, or
one the plugin adopted when you reopened it -- two of the commonest
journeys there are, where the whole restyle path was unreachable. A
shared map keeps "take my classes from that layer", which could not
survive a file at all. A blend mode set in QGIS survives a re-tile.
Opening a map whose region has a column called "no data" no longer
tells you half your map is missing. A Save says which elements it
left out, refuses when the group has been deleted rather than
emptying the file, and waits for a re-tile that is about to happen
instead of writing the map you have just changed away from. The Save
box comes home when the project reopens. A number you type into a
modifier survives a look at another family. A pinned ladder prints a
legend you can read on a column spanning magnitudes. Five kinds of
unopenable file say which way they failed instead of sharing one
sentence that is true of one of them. A column of names is counted
before the many-categories question rather than through a float. And
a limit typed while live update is on but no run can follow says so
rather than being taken in silence.

AND THE FIFTEENTH CLOSED ON 2026-08-29 (ledger row 61): **a follower's
inherited colours were adopted as its own when a self-contained map was
opened**, so it stopped following its donor and the two drew one column
in two sets of colours. A file saved with the source embedded carries a
copy of the region, the recipient's recovery lands on that copy, and
the comparison against the sender's own path answered False -- skipping
the record's value-laden half, which means neither applied nor cleared.
The claim named the Load door; the group chooser after a project reopen
was equally open, and a repair at one would have left the other.

WHAT IS STILL OWED FROM THAT LIST -- one claim, in the ledger with its
measurements:

- **Save and Load are quadratic in the element count and freeze the
  interface** -- 134s and 122s at the 256 ceiling, no progress bar,
  a 50 ms heartbeat recording zero beats. Every store was clean; the
  defect is in the act.
  MEASURED TO ITS EQUATION on 2026-08-29 and PARTLY REPAIRED, with the
  numbers in the ledger. Every call count is exactly linear: what
  grows is the cost of each call, because each opens the GeoPackage
  and opening one costs time proportional to the layers already in it.
  The one term that is ours -- removing superseded styles -- now opens
  the file once for the whole map instead of once per element, and its
  call count went from n to 1. The other three are QGIS's and OGR's
  own per-layer APIs and have no batch form, so closing the rest means
  making the save a single OGR session, which is a rewrite of the
  writer rather than a repair. THAT AND THE FREEZE ARE DECISIONS
  RATHER THAN WORK OWED: the loop pumps nothing, so a large save is an
  unresponsive window whatever it costs, and whether Save should report
  progress is a question about the interface.

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

**AND THE ROUND OF 2026-08-28, whose first two waves are below.** Twenty-three hunts kept at eight at a time and replenished as
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

NOTHING IS OWED FROM THE FIRST TWO WAVES ANY LONGER, and the last of
it came off on 2026-08-29 (the third wave's owed list is in the
ledger, named above). The design view painting an element in a colour
the map does not contain after a dock edit was REPAIRED at `148b154`
and UNGUARDED until the audit of that morning put the mutation on the
line its repair added and watched it survive; it is door three of
`test_every_restyle_door_repaints_the_preview` now. The catalogue
triage's two bad trades are both mended: the restyle leg that could
not fail has been restaged so that it can -- it used to run on an
element the arm above had already reclaimed, whose layer wore the
plugin's own renderer -- and the test its twin retirement left
carrying nothing now has an entry for each of the two paths a reclaim
can take.

ONE THING IS WATCHED RATHER THAN OWED, and is left open deliberately.
The landing's last preview repaint firing before the new layer exists
DID NOT REPRODUCE: every repaint through a whole landing saw all of
its layers. One clean journey is not a proof about all of them, so
the row stands as something to look at again rather than as work.

AND THE TWO FILE-SHARING ROWS CAME OFF IT ON 2026-08-29, both
audited first, both confirmed open, and both repaired with the harm
CORRECTED in the course of measuring it.

TWO SENDERS' MAPS (row 23) reproduced exactly: with two received
files open, returning to the first through the group chooser re-tiled
it from the SECOND sender's data, and the output path having come
home correctly is what made it worse, since the next Save would have
written that over the first sender's own file. The two halves of the
claim turned out to be one mechanism. A self-contained file records
the region its SENDER drew from, which on their machine is an
ordinary layer and on yours is a path that does not exist; the data
comes back from the copy inside the file, and the group was stamped
with the RECORD -- so nothing in the recipient's project ever
answered to it, and the chooser was silently left wherever it was.
The resume reports which of its three recoveries answered, and the
group is stamped with what it LANDED ON, falling back to the record
only where it landed on nothing -- which keeps the reason the code
was written that way, since a failed recovery must not file the
group under whatever dataset the chooser happens to hold.

A SHARED FILE SOMEBODY ELSE SAVED INTO (row 35) reproduced too, and
the harm is sharper than the claim rather than larger. Not a file
with no map in it, but an ELEMENT that vanishes: a colleague moving
one element to another column writes `tiles_b_v1` and drops
`tiles_b_landcover`, your layer goes on naming the dropped table, the
skip that treats "already reading from this table" as already saved
asks the SOURCE STRING and nothing else, and the stale-table drop
then removes what they HAD written. Both people lose that element,
under the word "Saved". It would empty the file outright only where a
colleague had changed every element.
NOTHING CAN BE WRITTEN IN ITS PLACE, which decided the repair's shape
rather than any preference: a layer whose table was dropped under it
answers `isValid` True and `featureCount` 40 and yields ZERO features,
so writing it would replace a real table with an empty one. The save
writes what it can, REMOVES NOTHING -- once a file has changed under
us, a table that looks like our own abandoned one is just as likely
to be their current one -- and says which element the file lost. That
sentence is IN THE TEXT-REVIEW QUEUE and is the maintainer's to
approve.
Measured with two QGIS processes and a rendezvous, because a running
QGIS serves its own cached pages and the drop is gated on the file
being the saver's own; the suite stages the same file state instead,
since what a colleague leaves behind is a state rather than a race.

NINE HAVE COME OFF THAT LIST, named here rather than quietly dropped,
since this list is what the release gate reads. Deleting the output
group and pressing Save is ledger row 19, closed with row 53. The
queued-work flags carried into the next project (row 8) landed in
`8db74ea`, and only the ledger's own OWES column was stale. And
pressing Load with your own polygon layer open (row 22) closed on
2026-08-29 with its harm corrected: the map is NOT replaced before you
touch anything -- driven with a control arm, it survives the Load
intact and a Save changes nothing. What the chooser holding your layer
really cost was the NEXT Generate, which took the restyle fast path
and recut every class from your data onto their tiles, then sent those
styles home in their file. The fast path asks whose region it is now,
and declines to a full run, which the landing's own refusal already
protects.
AND ROWS 18 AND 36 WERE REPAIRED THE SAME MORNING, both confirmed
open first and both guarded. The chooser asked one of the two doors
that arm a new group where the landing asks both, and the checkbox
arming the other was connected to nothing at all. The duplicate-layer
guard existed at adoption and not at the landing, where a run removes
the layers it knows about and a COPY is not among them -- so it
survived as last run's tiling over the new map, never updated again,
with nothing said. The question and the sentence have one owner
apiece now, so the two doors cannot come to disagree and the reviewed
wording is not composed twice.

AND FOUR MORE CAME OFF IT ON 2026-08-29, in an AUDIT RUN BEFORE
ANYTHING WAS BUILT -- the maintainer's instruction, after three of the
first nine turned out to be closed already with only their OWES column
stale. Row 6 was REPAIRED at `148b154` and UNGUARDED, which only the
catalogue could show: the mutation on the line its repair added
SURVIVED, and it is door three of `test_every_restyle_door_repaints_
the_preview` now. Row 7 did not reproduce -- every repaint through a
whole landing saw all of its layers -- and is left open rather than
deleted, since one clean journey is not a proof. Rows 9 and 10 are
closed, re-measured by planting the exact shapes they name and
watching the gate object, with the control silent. And row 36 is
FIXED: the chooser asked one of the two doors that arm a new group
where the landing asks both, and the checkbox that arms the other was
connected to nothing at all.

AND THE FOURTH IS ROW 20, closed the same night: a floor or ceiling,
and every colour picked after it, were destroyed by a save-and-reopen
before Generate, because every durable stamp an element carries was
written on the restyle's SUCCESS path and a limit is a geometry change
the restyle declines. The change is recorded on the decline now --
which is "preserve, do not repaint" read properly, since the map
waiting for the next Generate is settled and the change being LOST
never was. The decline has two meanings, so the stamping asks which
one it is: a second group and a colleague's map are not this map.

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
AND IS NOW DECIDED** (item 1 above; what follows is how it stood).
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

**THE DECLARATION STAYS WITHDRAWN, AND WHAT IT COVERS HAS CHANGED.**
Six things were owed after rc5 went out. FIVE ARE BUILT, on
2026-08-30, each with a registered test and catalogue entries proved
`caught`; the sixth is the window ceiling and is the one still owed.
Two further things the maintainer asked for the same day are built
beside them.

WHAT IS DONE, and what each cost:

1. **THE ELEMENT COUNT IS A SLIDER** with a spin box beside it, kept
   in step as one control, `_element_count()` the single owner of the
   question. THE TRACK SPANS THE WHOLE CATALOGUE, 2 to 256, rather
   than moving with the kind -- a departure from this entry's own
   design note, on a measurement. That note said 256 for tilings and
   26 for weaves; 26 is the ID ceiling for a weave's strand letters,
   and the CATALOGUE holds weave families only to n=12, so a
   weave-capped track would have offered thirteen counts with no
   weave family behind any of them and retired the contract
   `test_design_cascade` states outright. Flagged rather than settled
   silently: if the maintainer wants the track to stop where the
   weaves do, that is a ruling and it retires that contract.
2. **THE DESIGN TAB NO LONGER RUNS FULL WIDTH.** Kind, family,
   spacing and Auto share one line; every option row and modifier
   pair carries a stretch; the spacing box asks for room to show a
   realistic number rather than its 1e12 maximum. EW and NS are
   Left-Right and Up-Down.
   AND THE STATED CAUSE WAS A READING, corrected by measuring both
   trees in one run. Whether a form layout stretches its field column
   is decided by the STYLE: macOS defaults to `FieldsStayAtSizeHint`
   and Fusion to `AllNonFixedFieldsGrow`. Under the harness's macOS
   style every control ALREADY sat at its own hint before the repair,
   so the first guard written for this passed on the unrepaired code;
   under Fusion, which QGIS ships, the same tree drew a strand width
   between 0.083 and 1.0 at 1013px. The guard sets the style now.
3. **EVERY ARTEFACT CARRIES ITS VERSION, AND NO CHECK WRITES INTO
   `dist/`.** `build.py` names its output for the version and gains
   `--check`, which builds into a temporary directory; `release.py`,
   `ci.yml` and `install_and_load.py` ask `build.py` for the name
   rather than composing it.
   AND THE HAZARD HAD ALREADY BITTEN, measured 2026-08-30 before the
   evidence was overwritten: the build sitting in a QGIS profile was
   byte-identical to the unversioned zip across all 31 members, so an
   ungated artefact had been installed over a gated candidate. That
   is what the title bar had been faithfully reporting.
4. **THE GROUP CHOOSER IS THE ONLY DOOR TO A NEW GROUP.** The
   checkbox is retired, the standing "always new" behaviour with it.
   A deletion at the landing, since `force_new` already read the
   flag; the cost was the suite, as predicted -- twenty-four sites,
   eleven catalogue anchors of which two were RETIRED outright with
   their reason written where they stood, and two committed probes.
   The two-doors test became a one-door test, which is the stronger
   claim: it asserts no second control exists rather than that two
   agree.
5. **THE ZIGZAG NEEDS NO SCIPY**, and upstream answered it better
   than this entry imagined. Rather than writing a quadratic spline
   in numpy, upstream's commit 2dbea80 noticed the spline was
   interpolating samples of `sin` and evaluating it at a finer
   resolution -- so sampling `sin` at that resolution IS the function
   the spline approximated. Carried as patch 1f in
   `tools/vendor_weavingspace.py`, because that commit is on an
   experimental branch whose own first commit says the plugin can
   ignore it until merged; when it merges, the anchor stops matching
   and the tool names the patch. Verified exact at smoothness=0 and
   the true sine at every smoothness above it.

AND TWO MORE THINGS THE MAINTAINER ASKED FOR ON 2026-08-30, BUILT THE
SAME DAY:

6. **EXPERIMENTAL FEATURES, UNTICKED BY DEFAULT.** A box on Map
   options -- the third tab -- gates tabs that are experimental until
   designated otherwise. `setTabEnabled` greys the title and refuses
   selection in one call, so the two halves cannot come apart; the
   tabs stay visible, because somebody should be able to see what
   ticking the box would give them. It is a preference about the
   PLUGIN and deliberately not part of a group's working state.
7. **THE MESSAGES TAB, EXPERIMENTAL, SHIPPED IN THIS VERSION** rather
   than 0.24.5, on the maintainer's ask. Everything the plugin has
   said this session, newest first, with the ANSWER beside any
   question it asked. Every modal and every message-bar push now goes
   through one recording door, which is the "single door" this tab's
   own 0.24.5 entry asked to have decided; the wrappers are thin, so
   the suite's modal shim intercepts them unchanged.

**AND THE SIXTH IS BUILT TOO, WHICH CLEARS THE SECTION.**

8. **THE WINDOW IS BOUNDED BY THE SCREEN IT IS ON.** `_within_the_
   screen` clamps every path that resizes the dialog to
   `SCREEN_SHARE` of `availableGeometry`, and all three resize sites
   go through it -- the opening size, the fit to the Design tab, and
   the growth the assignment table asks for. On a roomy display it
   does nothing, which is what "no shorter than now" asks.
   WHAT IT REALLY FIXES IS WORSE THAN FILLING THE SCREEN: the height
   had NO upper bound at all, so a tall design on a small display
   could put the dialog's own buttons off the bottom edge. Width was
   bounded by `MAX_WINDOW_WIDTH`, a constant standing in for "the
   narrowest screen still in use"; nothing called `availableGeometry`.
   THE ONE NUMBER IS CHOSEN AND SAID SO. The maintainer declined to
   give a clearance figure and was right to -- the ask was a ceiling
   on growth, not a resize -- but "not the whole screen" needs some
   margin to mean anything, so 0.95 of the free area sits in one
   constant with the reasoning at the line, for whoever wants it
   different.
   AND THE GUARD SAYS WHICH HALF IT HOLDS. No runner here can measure
   the ASSEMBLED window -- offscreen reports 1279px where cocoa gives
   1334 -- so the unit test asserts the RULE (a size larger than the
   screen comes back smaller, a size that fits is untouched, and no
   `resize` call escapes the clamp), and the assembled window is
   measured by `tools/platform_probe.py`, which this joins.

nothing outstanding in code.

WHAT REMAINS IS THE MAINTAINER'S OWN, and neither is work on the
software: the CHANGELOG LINE for everything above, which is a sentence
a person writes and approves, and the FOURTEEN REVIEWED SENTENCES in
the text-review queue -- the slider's box, the two renamed transform
labels, the experimental box, the Messages tab and the prose about
them, and the three download sentences that now describe a versioned
artefact. CI will fail until those are approved, which is the gate
working: approving prose is nobody else's act.

AND ONE THING IS FLAGGED RATHER THAN DECIDED. The element slider's
track spans the whole catalogue, 2 to 256, where this section's own
design note asked for a ceiling that moves with the kind. The note's
number was wrong -- 26 is the ID ceiling for a weave's strand letters
and the catalogue holds weave families only to n=12 -- so a
weave-capped track would offer thirteen counts with no weave family
behind them AND retire the contract `test_design_cascade` states
outright, that a count offering only one kind flips the toggle
silently. If the track should stop where the weaves do, that is a
ruling and it retires that contract; it is one line either way.

IT IS WITHDRAWN RATHER THAN LEFT STANDING BECAUSE THE GATE READS THE
PHRASE. `check_roadmap` decides a section is clear by looking for
"nothing outstanding" with quoted spans stripped, so a section
carrying the declaration AND a list of work would clear a candidate
that owes both -- which is this file's own recorded fault about a
gate satisfied by a sentence, arriving from the other side.

ONE THING IS WATCHED RATHER THAN OWED AND IS NOT COVERED BY THIS. The
landing's last preview repaint firing before the new layer exists did
not reproduce -- every repaint through a whole landing saw all of its
layers -- and it is left open because one clean journey is not a proof
about all of them. It is not on the owed list because nothing here has
been able to make it happen, which is a different claim from its being
fixed.

AND THE CHANGELOG LINE IS WRITTEN AND APPROVED, on 2026-08-29, so the
paragraph above about it describes a thing now done: the maintainer
ruled on every sentence of the round's user-facing text one at a time
-- correcting two of them, and catching in the shared-file notice a
contradiction the software's own author had not seen, where "the data
is no longer there" sat beside "nothing was removed" without saying
that the two were about different people.

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

## 0.24.5 — three tabs asked for, and what was deferred here from 0.24.4

Moved on the maintainer's decision of 2026-08-27, in the act of
cutting 0.24.4's candidate. None of it is abandoned and none of it
was blocking the version: three are measurements rather than
defect-finding, and the fourth is a study whose answer is written
at its own entry.

**THREE TABS ASKED FOR ON 2026-08-29, and they are wants with no code
yet rather than work deferred from 0.24.4.** Each changes the shape of
the interface, so each gets `/grill-me` before anything is written --
this project's own rule, and the sessions that took it produced
designs that stuck.

**AND ALL THREE ARE EXPERIMENTAL UNTIL DESIGNATED OTHERWISE, BEHIND A
BOX THAT IS UNTICKED BY DEFAULT.** (Maintainer's ruling, 2026-08-30.)
An **Experimental features** checkbox goes under the THIRD tab, which
is *Map options* -- the tab order is Design, Data & colours, Map
options, Save & open, Help. Until it is ticked, none of the three tabs
above can be activated and each of their titles is greyed. Ticking it
is what makes them reachable.

THE MECHANISM IS QT'S OWN, which is worth writing down because it
matches the ask exactly rather than approximately:
`QTabWidget.setTabEnabled(index, False)` both greys a tab's title and
refuses selection, so "ungreyed" and "activatable" are one call and
cannot come apart. Nothing has to be hidden, which is the point --
somebody can SEE that there is more here and what it would cost them.

THREE THINGS THE DESIGN STILL OWES, none of them settled by the
ruling. WHERE THE ANSWER LIVES: this is a standing preference about
the plugin rather than a fact about a map, so it belongs in QSettings
beside the other preferences and NOT in the group's working state --
which is the two-relationships framing in CLAUDE.md, and getting it
wrong would carry one person's appetite for experiments into another
person's project. WHAT A TICKED BOX MEANS FOR A SAVED FILE: if an
experimental tab can put anything in the GeoPackage, a recipient
without the box ticked has to be able to open that file, so either
those tabs write nothing durable or the record has to survive being
unreadable. AND WHAT HAPPENS WHEN A TAB GRADUATES: the box stops
gating it, which is a one-line change and a sentence in the changelog,
so the cost of being wrong about any of this is low -- which is the
argument for the box rather than for holding the tabs back.

IT ALSO GIVES 0.24.5 A CHEAP FIRST STEP. The box and the greying can
be built and shipped BEFORE any of the three tabs exist, which is
worth doing: it is a small, self-contained piece of interface with its
own guard, and it means the first tab to arrive lands behind a gate
that is already tested rather than beside one written in the same
hurry.

**A MESSAGES TAB -- SHIPPED EXPERIMENTAL IN 0.24.4, and what is left
here is the part that did not ship.** The tab exists: everything the
plugin has said this session, newest first, with the answer beside any
question, behind the Experimental features box. Every modal and every
message-bar push goes through one recording door, which settles the
question this entry asked below; the record lives in `said.py` rather
than on the dialog, because `plugin.py` speaks -- including the
consent dialogue -- before any dialog exists, and two of the things it
says mean the window never opens.

WHAT IS STILL WANTED HERE: whether the log should survive the window
closing (it does not, by the maintainer's own ask, and that may be
worth revisiting once people have used it), and whether QGIS's own Log
Messages panel should be mirrored into it -- the plugin writes nothing
there today, measured 2026-08-30, so there is nothing to mirror until
it does.

The original ask, kept because the reasoning is what a later session
will not have: a reverse-chronological, timestamped, scrolling log of
what the plugin issues -- the message bar's notices, the text of every modal AND THE
ANSWER GIVEN TO IT, the QGIS warnings it raises. It need not survive
the session, and it carries a Clear button.

WHY IT IS MORE THAN A CONVENIENCE, and the argument is in this
project's own record. The plugin already speaks into TWO stores that
nothing brings together: the message bar, and modal dialogues. Reading
one and concluding silence is a fault the suite has met so often it is
numbered -- harness fault eleven -- and the same split has cost real
diagnoses, because a run refused through a QMessageBox leaves the bar
empty and is indistinguishable from a run that was never launched. A
user has no `MODALS` list to read. This tab is that union, offered to
the person rather than to the test harness.

RECORDING THE ANSWER MATTERS AS MUCH AS THE QUESTION. Half this
plugin's modals change what happens -- whether a file was overwritten,
whether a design was recomposed to fewer elements, whether a large run
was allowed to proceed -- so a log holding the question without the
answer describes a decision nobody can reconstruct.

WHAT NEEDS DECIDING: whether the plugin's own message-bar helper
becomes the single door everything passes through (it very nearly is
already), and what happens to a message issued while the tab does not
yet exist. Session-scoped storage is settled by the maintainer's ask.

**A LEGEND DESIGN TAB, and a two-way question at the end of it that
needs research before any of it is built.** A chooser of legend
styles, defaulting to NONE -- defer to QGIS, which is this project's
standing preference and the honest default for somebody who has not
asked for anything. Examples to draw on include the ones the
weavingspace library itself makes. A preview box shows the chosen
style, and the relevant controls adjust it.

THE EXPORT HALF IS THE STRAIGHTFORWARD HALF: a file selector and
buttons that write the legend to SVG, or to PDF WITH TRANSPARENCY,
either of which imports into a graphics package for the
post-processing that finishing a map for publication usually needs.

THE PART TO RESEARCH FIRST, because it decides whether the rest is
built at all: whether the legend can instead be written into a QGIS
PRINT LAYOUT the user picks from a dropdown -- and, harder, whether
tweaks made afterwards IN that layout can come back and update the
plugin's own configuration, wherever the two can both represent the
same thing. Nobody here knows yet how far QGIS's layout legend can be
driven that way.

AND THE SHAPE OF THAT QUESTION IS ONE THIS PROJECT KNOWS WELL. Two
stores holding one fact, mended in one, is the single commonest defect
in this repository's ledger. So the research has to answer not only
"can it be done" but "what happens to a tweak the plugin cannot
represent" -- and the answer must never be to lose it silently. A
legend the user has refined in a layout is their work, and the QGIS
boundary is where remembering is an obligation rather than a design
question.

**A TOPOLOGY TAB: visual and quantitative interaction with what the
library already computes, and then past it.** `topology.py` is the
richest thing in the vendored library that the plugin does not
currently expose at all. It carries `Topology`, `Tile`, `Vertex` and
`Edge`; it can enumerate potential symmetries, generate a tiling's
DUAL and hand back its tiles; and it offers real MANIPULATIONS rather
than only description -- `zigzag_edge`, `rotate_edge`, `scale_edge`,
`push_vertex`, `nudge_vertex`, `insert_vertex_at`,
`merge_edges_at_vertex`, `transform_geometry`.

Those manipulations are why this is a tab rather than a viewer: a
person could take hold of an edge or a vertex and watch the tiling
answer. Upstream's own plotting is the starting point and not the
destination; the maintainer's ask is explicitly to go BEYOND what
upstream offers, and creative interactive visualization is where that
starts rather than where it ends.

THE MATERIAL, given by the maintainer on 2026-08-29, is upstream's own
two working notebooks:
`examples/topology-working.ipynb` and `examples/symmetry-working.ipynb`
in `DOSull/weavingspace`. The first builds a unit
(`TileUnit(tiling_type="chavey", code="K")`), plots it, and hands it to
`Topology(tile, True)`; the second is the sharper of the two for our
purposes, since it drives `Symmetries(polygon)` over six deliberately
awkward shapes, reads `symmetry_group` and `symmetries` off each,
DRAWS every symmetry onto the shape with `Transform.draw(ax, radius=,
mirror_length=, w=)`, and then matches one polygon onto another with
`ShapeMatcher(p).get_polygon_matches(q)`. Its finding is worth carrying
into any interface we build: a reflection can only appear alongside a
rotation WITHIN a shape, while matching one shape to ANOTHER admits
reflections for shapes that have no internal symmetry at all. Those are
two different questions and a tab that shows both must say which it is
answering. Everything both notebooks use is already in our vendor at
0.0.7.89, so none of it waits on upstream.

**THE TOPOLOGY TAB WAS GRILLED ON 2026-08-30 AND FIVE THINGS ARE
SETTLED.** The maintainer asked for an interactive tab with numeric and
click-and-drag editing, round-tripping through the GeoPackage, built
when the map is generated and kept up to date, with the races checked.
Each decision below was put with the measurement under it, which
changed three of them.

1. **THE TOPOLOGY IS OF THE UN-MODIFIED UNIT**, built before aspect and
   insets are applied, and the tab says so. `Topology` needs a GAP-FREE
   tiling and the plugin's ordinary settings do not give it one -- the
   default weave aspect is 0.75 and ANY tile inset makes even laves
   3.3.4.3.4 raise -- so the alternative was a tab that is dark for
   most designs anybody actually makes. Edits land on the motif and the
   modifiers apply over the top, which is the order the pipeline
   already uses.
2. **IT IS BUILT ON EVERY GENERATE ONCE THE EXPERIMENTAL BOX IS
   TICKED**, off the main thread beside the tiling, and NEVER on a
   colour or ramp change (the maintainer's own correction). The hook is
   narrower than `_geometry_signature`, which also carries the region
   layer, the output path and the mapped variables: the topology
   depends on the UNIT alone, so it rebuilds with whatever rebuilds the
   preview -- family, kind, element count and the family's own options.
   MEASURED: a build costs 0.75s on laves 3.3.4.3.4 and 2.1-4.4s on
   hex-slice 6 and square-colouring 5, which is why it is not built for
   people who have not asked for it.
3. **AN EDIT LIST GOVERNS, AND THE UNIT AND DUAL ARE WRITTEN AS LAYERS
   BESIDE IT.** Two edits are 125 bytes against 546 for the edited
   geometry of four tiles -- but size is not the argument. The
   geometry's coordinates SCALE WITH SPACING, so stored geometry is
   wrong the moment somebody changes it, while a class label was
   measured stable across rebuilds AND across spacings 500 and 1300.
   The layers make the file self-describing, which is the argument that
   put the element tables and their styles in there.
   THE CAVEAT IS THE CRS: the unit lives in unit space, so those two
   layers carry NO CRS and say what they are in their names, or they
   land off the coast of Africa -- this project's own recorded hazard
   about a memory layer handed EPSG:4326, arriving through a new door.
4. **EDITS ARE SHELVED BY FAMILY AND ELEMENT COUNT**, going idle when
   the design moves away and returning if it comes back. Never replayed
   by label alone: laves 3.3.4.3.4 has edge classes `a,b` and
   hex-slice 4 has `a,b,c,d`, so `a` means a different edge in each and
   a blind replay would land somebody's edit on the wrong one. That is
   the shape already settled twice here -- the scheme shelf keyed by
   field, and `_re_range_remembering` holding a modifier number until a
   family can wear it.
5. **ALL FIVE MANIPULATIONS ARE OFFERED, AND ZIGZAG REFUSES IN WORDS
   WHEN IT CANNOT DRAW.** Measured on four designs: `push_vertex`,
   `nudge_vertex`, `scale_edge` and `rotate_edge` each produce a
   tiling that draws, at 0.04-0.05s. `zigzag_edge` produced none as
   first called -- and the correction is worth keeping, because it was
   nearly filed as a defect in the library: THE AUTHORS PASS A STRING
   OF MANY CLASS LABELS as the selector, not one, and add
   `smoothness=3`. Through their own call shape it still needs
   `shapely.make_valid` to draw at all, which rescues hex-slice 4 at
   382 tiles and makes laves 3.3.4.3.4 worse (159 invalid geometries
   becoming 343). So it attempts the repair and refuses in the terms of
   the control where it cannot, which is `inset_collapse_message`'s
   shape rather than the library's raw ValueError.

**WHAT OF THE FIVE IS BUILT, as of 2026-08-30.** Recorded against the
rulings rather than as a narrative, so the gap is readable at a glance.
WHICH VERSION IT SHIPS IN IS THE MAINTAINER'S DECISION and the entry
stays in this section until they make it; the code is on
`for-0.24.4/copy-select-all` behind the experimental box, which is what
makes that decision cheap either way.

- Ruling 1, the un-modified unit: BUILT. `topology_edits.build` takes
  the motif before aspect and insets, and the tab says so on its face.
- Ruling 2, built on Generate off the main thread and never on colour:
  BUILT. `_queue_topology` hangs off whatever rebuilds the unit, and
  `_topology_stamp` throws away a build whose design has moved on.
- Ruling 3, an edit list governs: BUILT. The edit list is the record,
  it is shelved, and since today it rides the working state so a saved
  project brings the edits home. THE UNIT AND DUAL AS CRS-LESS LAYERS
  AT SAVE ARE STILL OWED -- that is the half of ruling 3 that makes the
  file self-describing, and the CRS caveat above is the trap waiting
  in it.
- Ruling 4, shelved by family and element count: BUILT, keyed by
  `topology_edits.shelf_key`, idle when the design moves away and back
  when it returns.
- Ruling 5, all five manipulations with zigzag refusing in words:
  BUILT, and the zigzag half is better than the ruling promised --
  see the repeated-vertices finding below, which was measured after
  the ruling was written and replaces `make_valid` alone.

STILL OWED BESIDES THE LAYERS: the four race families named in the
grilling -- a stale topology landing, an edit aimed at a class that has
gone, an edit made during a run, and the restore dropping the record in
silence. THE LAST OF THOSE IS CLOSED, by
`test_topology_edits_survive_the_working_state` and two catalogue
entries standing on the write and the read separately, because writing
here is permissive and reading is strict and the pair is exactly what
this project has been caught by four times. The other three are
unmeasured, and unmeasured is not the same as absent.

**THE DEFAULT STRAND WIDTH STAYS AT 0.75, having been changed to 1.0
and changed back the same day** (maintainer, 2026-08-30). Recorded
rather than quietly reverted, because the reasoning that prompted it
is sound and somebody will propose it again.

THE CASE FOR RAISING IT: aspect is a family OPTION rather than one of
the modifiers ruling 1 builds before, so at 0.75 the Topology tab is
unavailable for every weave by default. Measured 2026-08-29, aspect
1.0 carries a topology and 0.95, 0.9 and 0.75 all raise.

THE CASE AGAINST, WHICH WON: at 1.0 the strands meet, so a plain weave
reads as a chequerboard rather than as strands with daylight between
them. That is the thing a weave is FOR, and the change would have
altered every weave map the plugin draws out of the box, the published
gallery images with them -- a large, visible cost paid by everybody to
unlock a tab most people will not open.

AND IT WOULD NOT HAVE BOUGHT WHAT IT LOOKED LIKE BUYING. Measured over
the first fourteen weave families at 1.0, EIGHT carry a topology and
SIX do not. NO CLEAN PREDICTOR WAS ESTABLISHED, and the attempt is kept
because it was wrong in an instructive way: "a strand code containing a
dash" held on eight cases chosen four-and-four, and that sample had
excluded two counter-examples already in hand -- `twill weave a|b 1,2`
and `a|b 1,2,2,1` carry no dash and still fail. At least two causes,
then, and a rule quoted from that sample would have been a uniform
verdict produced by the instrument rather than a fact about weaves.

WHAT ANSWERS IT INSTEAD IS THE REFUSAL. `topology_edits.can_build`
decides by TRYING to build a topology, never by inspecting the spec, so
it is right about every design whether or not anybody can say in
advance which those are -- and its sentence names the CONTROL: set the
strand width to 1.0, or the tile inset to 0. Somebody who wants a
topology for a weave is told what to move rather than left in front of
a dark tab.

**ZIGZAG'S TROUBLE IS REPEATED VERTICES, AND IT IS PROPERLY
COMPENSABLE.** (Measured 2026-08-30 across two maintainer challenges,
each of which corrected a reading of mine: "zigzag should work where
the two ipynb shows it working right?" and then "are the zigzag
problems floating point errors? And if so can you compensate
properly?")

WHAT THE NOTEBOOK ACTUALLY SHOWS. Driven exactly as
`topology-working.ipynb` drives it -- `TileUnit(tiling_type="chavey",
code="K")`, every edge class, `n=2, h=0.25, smoothness=3` -- TWELVE OF
TWENTY tiles come back invalid. The notebook PLOTS the result rather
than tiling it, and matplotlib draws a self-intersecting polygon
without complaint, so this was invisible from where the authors were
looking; their own markdown half-catches it, noting that outer tiles
"might not get 'deformed' correctly".

IT IS NEITHER AMPLITUDE NOR FLOATING POINT, and both were believed here
first. h from 0.25 down to 0.001 leaves 12-13 tiles invalid, so it is
not a matter of asking for too much. And the number in shapely's
message is WHERE a self-intersection is, not how large an error is: one
sat at 1e-14 from the origin and was read as a degenerate value, while
the rest sit at an ordinary 134 units out.

WHAT IT IS: REPEATED VERTICES. One invalid tile carried six coincident
point pairs among thirty-seven points. A repeated vertex is a
zero-length segment and shapely reports every one as a
self-intersection.

SO THE REPAIR IS IN TWO STAGES AND THE FIRST IS EXACT. Dropping
consecutive coincident vertices takes twelve invalid tiles to ONE with
every area unchanged to a part in 1e9 -- the boundary does not move,
because a null segment has no length. Mending the single genuine
residue takes it to none, and measured on that case moved no tile's
area either. Chavey K then tiles at 1802 tiles.

WHAT THAT BUYS, and it is not everything. With the repair, zigzag
applies on chavey K and hex-slice 3 and is still refused on laves
3.3.4.3.4 and hex-slice 4. So ruling 5 stands exactly as decided --
offer it, attempt the repair, refuse in words where it cannot -- and
what changed is that the refusal is now the minority case rather than
the only one.

AND IT IS STILL WORTH TELLING UPSTREAM, in "Two conversations to have"
below: a manipulation that emits coincident vertices is a defect
whatever the caller does about it, and the fix belongs in
`zigzag_between_points` rather than in every consumer's repair.

**AND CLICK-AND-DRAG IS AFFORDABLE, which the first reading of the cost
said it was not.** One edit costs 1.23s end to end on the fastest
design -- 0.15s for the transform and 1.08s to rebuild the Topology,
which upstream's own caution requires ("new Topology will probably not
be correctly labelled ... rebuild from the tileable"). But the rebuild
is only needed to go on EDITING. Applying a transform from the
pre-drag topology and redrawing the motif is 0.04-0.05s, so a drag runs
at roughly 20 frames a second and pays the rebuild once, on release.
The parameter is re-applied from the ORIGINAL topology each frame
rather than accumulated, or a drag would compose a hundred transforms.

**WHAT THE NOTEBOOKS GAVE, on the maintainer's instruction to mine them
for the workflows their authors imagined.** `topology-working.ipynb`
plots with seven toggles -- original tiles, tile centres, vertex
labels, edge labels, edges, offset edges, dual tiles -- which is the
view the tab owes; it plots tiling symmetries
(`plot_tiling_symmetries`); and it promotes the dual to a TileUnit of
its own, calling `_setup_regularised_prototile(override=True)`, which
is the step `transform_geometry` does not do and which the tab will
need. `symmetry-working.ipynb` reads `Symmetries(polygon)
.symmetry_group` over six deliberately awkward shapes -- C1, D1, C2,
D2, C4, D4 -- and matches one shape onto another with
`ShapeMatcher(p).get_polygon_matches(q)`. Its finding is the one to
carry into any interface: a reflection appears alongside a rotation
WITHIN a shape, while matching one shape to ANOTHER admits reflections
for shapes with no internal symmetry at all. Two different questions,
and a tab showing both must say which it is answering.

**AND THE MAINTAINER'S DESIGN NOTE -- build the topology when the
tiling is built, and store it in the transportable GeoPackage -- MEETS
TWO MEASUREMENTS, taken 2026-08-29 before any of it is designed.**
Recording them here because they change what the note can mean, and
because a decision is only as good as the measurement under it.

FIRST, IT IS NOT CHEAP. `Topology.__init__` does everything eagerly --
eight setup passes and `generate_dual()`, with no lazy half to
discount. Timed three times each on catalogue designs through the
plugin's own `make_unit`, over two runs on a machine of differing
business: archimedean 4.8.8 at 0.32-0.61s, hex-slice 12 at 1.90-3.05s,
hex-slice 6 at 2.08-4.38s, square-colouring 5 at 3.25-3.98s. THE
SPREAD IS THE MACHINE and the claim is about the ORDER rather than any
one figure -- seconds, reliably, on every design tried. The cost also
tracks the SHAPE rather than the element count, since n=5 is the
slowest of those and n=12 is not, so it cannot be bounded by the
element spinner. Against that, building the unit itself is 0.01-0.05s
at every count up to 256, and the live debounce is 900 ms.
Building a topology on every Generate would therefore be the dominant
cost of drawing a map, and building one on every live tick would make
the live path useless. What the note is really asking for is that the
topology belong to the DESIGN rather than to a button, which it can:
computed once per design change, off the main thread as the tiling
already is, and thrown away when the design moves.

SECOND, AND HARDER: `Topology` REQUIRES A GAP-FREE TILING, and most of
what this plugin draws has gaps. Measured on a plain weave at spacing
500: aspect 1.0 builds a topology, and 0.95, 0.9 and 0.75 all raise
`ValueError: Vertex ... Tiles: [] is not in list`, aspect 0.5 raising a
different unpacking error. The plugin's own default aspect is 0.75, and
opening the weave up is what aspect is FOR. The same fault reaches
tilings through the inset controls: laves 3.3.4.3.4 builds at inset 0
and raises at 5, 25 and 50 map units alike. So the tab is available for
an undecorated unit and unavailable for the ordinary settings a person
reaches for, which is a scope decision rather than a bug to fix here.
Three honest ways out, and choosing between them is the first design
question: compute the topology on the unit BEFORE modifiers and say so
on screen, since the topology of the shapes is arguably what somebody
wants anyway; disable the tab with a reason when the design has gaps;
or take it upstream, since a tiling with deliberate gaps is a
reasonable thing to ask a topology about and only upstream can widen
that. The third belongs in "Two conversations to have" below if it is
taken.

AND WHAT GOES IN THE FILE IS NOT THE OBJECT. `topology.py` imports
`pickle`, but only to deep-copy itself inside `transform_geometry`;
there is no save format, and a pickle would be the wrong one anyway --
version-fragile, and unpickling a file somebody sent you is precisely
the shape a plugin-repository reviewer looks hardest at, which this
project has a hard rule about.

**THE FILE ALREADY CARRIES JSON, AND THE MECHANISM IS THE ONE THE
RECORD USES.** `bridge.write_working_state` opens the GeoPackage with
`gdal.OpenEx(path, OF_UPDATE)` and calls `SetMetadataItem(
"WEAVINGSPACE_STATE", json.dumps(record))`, which lands in the
format's own `gpkg_metadata` table; `read_working_state` takes it back
out with `GetMetadataItem` and `json.loads`. That is how the whole
working state travels today, so topology facts need no new machinery
at all -- they are keys in a dict that is already written.

MEASURED 2026-08-29, on hex-slice 12 at spacing 500. The structured
half of a topology -- shape groups, the tile, vertex and edge
transitivity classes, and the counts -- serialises to **2,424 bytes**,
against about 1,151 for a representative record, so it roughly triples
what the file carries and the total is 3,589 bytes inside a 106 KB
GeoPackage. Written through the plugin's own two functions and read
back from a COLD open, the topology came back identical. The largest
term is the edge classes at 1,388 bytes, and that is the one that
scales, since it is per edge rather than per element.

THE DUAL IS THE EXCEPTION AND WANTS A TABLE. `get_dual_tiles()`
returns a GeoDataFrame, so it belongs in the file as a LAYER the way
element tables do -- a colleague can then open it without the plugin,
which a metadata string does not give them. Geometry in a JSON blob
would be the wrong shape twice over.

AND THE THREE STORES ARE NOT SYMMETRICAL, which is the trap to write
down before anybody builds this. `_capture_working_state` builds the
record by iterating `WORKING_STATE_DESIGN` and `WORKING_STATE_ELEMENT`,
so a topology key does not appear unless capture is taught it;
`_file_safe_state` is a BLACKLIST that strips only each element's
`kept` map, so once captured the key travels to the file for free; and
the restore iterates those same whitelists, so a key the file carries
is dropped in SILENCE on the way back in unless the whitelist knows it.
Writing is permissive and reading is strict. That is this project's
"widen the whitelist in the same commit as the code that reads it",
said three times already about `_adopt_dock_bounds`, the copy and the
mode, and it applies here with the extra wrinkle that the file will
happily hold something nothing can restore.

ONE SMALL THING THAT WILL BITE: edge ids are TUPLES and JSON has no
tuple, so they come home as lists and every reader has to `tuple()`
them. A silent type change across a boundary is the shape this
repository's ledger carries most often.

None of this troubles the ruling of 2026-08-26 that the file shows the
limit of what it contains: a topology is a fact about the DESIGN and
carries none of anybody's data.

**AND NO, A GEOPACKAGE CANNOT STORE GEOSPATIAL TOPOLOGY, WHICH TURNS
OUT NOT TO MATTER -- THE TWO THINGS SHARE A WORD AND NOTHING ELSE.**
(Asked by the maintainer, 2026-08-29; checked against the OGC
extension registry and GDAL's own GPKG driver documentation rather
than from memory.) There is no topology extension to GeoPackage,
adopted or community: the registry lists WKT for CRS, Tiled Gridded
Coverage and Related Tables as the official three, and a dozen
community ones for vector tiles, styling, 3D tiles and the rest, with
nothing for a node/edge/face model. GDAL implements no topology model
either. GeoPackage is a SIMPLE FEATURES format -- every geometry is an
independent blob, adjacency is not represented, and nothing enforces
planarity. PostGIS and SpatiaLite do carry ISO SQL/MM Topo-Geo models;
GeoPackage deliberately does not.

WHAT IT DOES HAVE, if anybody ever wants it: non-spatial ATTRIBUTE
tables since GeoPackage 1.2, and the Related Tables Extension (OGC
adopted, GDAL 3.6+) for many-to-many relationships. So incidence --
tile to edge, edge to vertex -- could be hand-rolled as ordinary
tables. Nothing stops it, and nothing reads it either: no consumer, no
enforcement, no QGIS interface.

WHY IT IS THE WRONG QUESTION HERE. Weavingspace's `Topology` is not
geospatial topology. It is the COMBINATORIAL AND SYMMETRY structure of
the repeating UNIT -- transitivity classes, shape groups, the dual --
and it lives in unit space with twelve tiles where the map on the
ground has seventy thousand. Geospatial topology would be a claim
about the OUTPUT: that the stamped polygons share edges exactly, with
no slivers and no gaps. That claim is one this plugin should not be
making. It never edits output geometry, so there is nothing to
enforce; the tiles come from exact construction in the library and are
then clipped; and with an inset or a weave aspect below 1.0 the map
DELIBERATELY has gaps, so a planar model would be actively wrong about
the commonest designs. It would also be enormous -- a structure over
seventy thousand tiles against 2.4 KB for the unit's.

THE ONE THING TO CARRY FORWARD IS THE NAME. A tab called "Topology"
will be read by some GIS users as promising the node/edge/face kind,
and it does not. Whatever it is called, the tab has to say early and
plainly that it describes the repeating unit and not the map.

**AND THE MAINTAINER'S OWN FRAMING SHARPENS ALL OF THAT: this project
has THREE kinds of layer -- the original data, the tiling over the
whole space, and the element layers which unioned together ARE that
tiling -- so it is the TILING'S topology that is at stake.** That is
right, and it does not argue for a topology model over the output,
because a tiling is PERIODIC: the adjacency structure of the whole
tiling is already determined by the unit and its neighbouring copies,
which is exactly what `Topology` is built on.

MEASURED 2026-08-29, as two independent descriptions of one fact. The
first takes every edge's `left_tile` and `right_tile` and reads their
`label`, giving the element pairs that share an edge according to the
UNIT. The second knows nothing about topology: it takes
`get_local_patch(r=3)` -- a real piece of the tiling, 111 to 222 tiles
-- and asks which polygons share a boundary of non-zero length. On
laves 3.3.4.3.4 the two agree exactly at six pairs, and on hex-slice 3
at three. So the unit does describe the tiling, and a structure over
seventy thousand output polygons would be an expensive restatement of
something 2.4 KB already says.

**THE THIRD DESIGN DISAGREED, AND THE DISAGREEMENT IS THE USEFUL
PART.** On hex-slice 6 the unit reported NINE pairs and the geometry
seven. Classifying every contact by what it actually is: the seven
share 288.675 map units of edge, and the two extra -- b-e and c-f --
have a maximum shared length of 0.0 and intersect as a POINT. They
touch at a corner. So "adjacent" in the topological sense includes
contacts a reader cannot see, and the two senses are not
interchangeable.

WHICH SENSE THE TAB MEANS IS THEREFORE A DECISION, and for the
cartographic question it is the geometric one. What somebody wants to
know is which elements they can compare across a shared border, and a
corner contact affords no comparison. The same distinction is worth
carrying to the LEGIBILITY CHECK, which today warns about pairs of
elements whose colours a reader may not separate without knowing which
pairs actually abut -- a pair that never shares an edge is a weaker
warning than one that does.

**SO: STORE THE UNIT AS A LAYER, AND THE DUAL BESIDE IT.** Both are
tiny -- n polygons and the dual's handful -- and it makes the file
self-describing: somebody opens the GeoPackage and sees the motif and
its dual without needing the plugin at all, which is the same argument
that put the element tables and their styles in there. The dual has to
be a layer in any case, being geometry.

ONE CAVEAT, AND IT IS A REAL ONE: THE UNIT LIVES IN UNIT SPACE. Its
coordinates are around the origin, not on the ground, so a layer
carrying the map's CRS would place the motif at that CRS's origin --
off the coast of Africa for a great many of them. That is this
project's own recorded hazard about a memory layer handed EPSG:4326 by
default, arriving through a new door. Either store these two with NO
CRS and say in the layer name what they are, or place them
deliberately; what must not happen is a layer that silently claims to
be somewhere.

WHAT COMES FIRST is still an inventory, and it is cheaper now that the
two constraints above are known: what each manipulation actually does
to a unit, which of them compose, and which produce a tiling the rest
of the plugin can still draw.

**AND FIND OR WRITE AN ALTERNATIVE TO PULLING IN THE WHOLE OF SCIPY.**
(Maintainer's instruction, 2026-08-29.) `zigzag_edge` is the one
manipulation that reaches outside numpy, and it does so at exactly ONE
line -- `topology.py:1418`, inside `zigzag_between_points`:

    spline = interpolate.InterpolatedUnivariateSpline(x, y, k = 2)

scipy is optional in the vendored library and is NOT in `deps.py`, so
that call raises a clear ImportError today. Adding scipy would be a
poor trade: it is a large download for one interpolating spline, and
it would have to be named in the dependency consent dialogue, whose
enumeration is a hard rule and was itself a defect this month when it
under-reported what was fetched.

WHAT MAKES AN ALTERNATIVE PLAUSIBLE is that the requirement is small
and exactly specified. `k=2` is a quadratic interpolating spline
through known points, numpy is ALREADY a dependency, and there is a
single caller. So the options are to write the quadratic spline in
numpy, or to reach for a simpler smooth interpolation that produces an
acceptable zigzag, or to ask upstream whether they would take such a
change.

AND IT HAS AN OBVIOUS HOME. `tools/vendor_weavingspace.py` already
carries a patch family whose whole purpose is "make matplotlib and
scipy optional", each patch asserting on an exact upstream anchor. A
numpy replacement for this one call is a NEW MEMBER OF THAT FAMILY
rather than a new mechanism, which also means it survives a re-vendor
by construction or names itself when upstream moves the line.

WHAT WOULD HAVE TO BE TRUE before taking it: the replacement draws a
zigzag a person cannot tell from the spline's, which is a VISUAL
question and therefore this project's own `visual_pair` shape --
render both and compare interior pixels -- rather than a numerical
tolerance argued in the abstract.

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

**SAVE AS A SINGLE OGR SESSION.** (Maintainer's decision, 2026-08-29,
splitting this off rather than folding it into 0.24.4's candidate.)
Save is super-linear in the element count and the reason is measured:
every call count is exactly LINEAR, and what grows is the cost of each
call, because each opens the GeoPackage and opening one costs time
proportional to the layers already in it. One of the four terms was
ours and is fixed -- removing superseded styles opens the file once
for the whole map now, its call count went from n to 1. The other
three are `write_gpkg_layer`, `save_style_to_database` and
`point_layer_at`: QGIS's and OGR's own per-layer APIs, with no batch
form, and 2.2s of the 2.6s wall at 64 elements.

Closing the rest means writing every layer in ONE OGR session rather
than one per layer. That is a rewrite of the writer, not a repair: it
changes what the file contains in ways the whole suite would have to
re-answer, and the risk lands on the one thing that must not break --
what a colleague receives. It wants its own round, its own hunts and
its own full suite, which is exactly why it is here rather than in the
version whose candidate is being cut.

WHAT IS ALREADY DONE FOR IT, so the round starts from a measurement
rather than a suspicion: the equation, the four terms, and the method
that produced them -- compare call COUNTS at four element counts
rather than seconds at two -- are in `docs/process/defects-2026-08-28.md`
under the quadratic, with the instrument in the session scratch.

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

**AND A THIRD, RAISED 2026-08-30: `zigzag_edge` EMITS REPEATED
VERTICES**, which shapely reports as self-intersections and which make
the result untileable. On `chavey` code K -- the design their own
`topology-working.ipynb` zigzags -- twelve of twenty tiles come back
invalid, and one of them carries six coincident point pairs among
thirty-seven points. Dropping the repeats is exact, leaves every area
unchanged to a part in 1e9, and takes twelve invalid tiles to one.
The notebook plots the result rather than tiling it, and matplotlib
draws an invalid polygon without complaint, which is why this is
invisible from where they were looking. Worth sending with the
measurement, the design and the two-line repair, since the fix belongs
in `zigzag_between_points` rather than in every consumer.

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
