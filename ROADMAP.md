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

**1. THE RECORD CAN LIST MORE ELEMENTS THAN ITS OWN DESIGN HAS.**
(Under 0.24.4.) Only a landing may move the record's DESIGN half,
which is the ruling of 2026-08-26; everything the colour editor writes
must be re-read live at the landing, which this project learned three
times at the cost of somebody's pinned bounds. Both hold, and together
they let a Save write `n=4` beside `elements a..f` in three presses.
Trimming is ruled out: the surplus entries are the per-element,
per-field memory ruling 6 of 2026-08-21 requires to survive a switch.
The likely answer is at the READER, but that is a decision about what
the record MEANS.

**2. THE MUTATION WORKFLOW GATES A CANDIDATE, THOUGH IT IS DOCUMENTED
AS REPORTING.** (Under 0.24.4, added 2026-08-31.) The decision of
2026-08-11 took the mutation instruments out of the gating path
deliberately; `publish_candidate` refuses unless EVERY workflow on the
candidate's commit is green. It stopped rc7 rightly, because that
workflow's coverage leg runs the whole suite and had found a real test
fault -- so the question is whether the split belongs per JOB rather
than per workflow, the sampling jobs reporting and the whole-suite leg
gating.

**7. WHICH DESIGN TERMS PUT A TOPOLOGY EDIT AWAY.** (Under 0.24.4,
added 2026-09-02.) `topology_edits.shelf_key` now carries the family,
the element count and whether the DUAL is being mapped -- the last
added as ledger row 24, because a dual is a design in its own right
and an edit is replayed by label. Every OTHER design term is still
outside it, and the specification hunt measured what that costs: a
scale modifier turned two edge classes into four on `laves 3.3.4.3.4`,
so the class an edit names came to describe a disjoint set of edges
while the change list still read the same. Widening the key to the
whole design is the obvious repair and it is a RULING rather than a
fix: it would mean an ordinary spacing or modifier tweak putting
somebody's edits away and bringing them back, and where that line
falls is what a person feels. The alternative is to keep the key
narrow and REPORT at replay time where a named class no longer means
what it did.

**3. THE ELEMENT SLIDER'S TRACK AGAINST `test_design_cascade`.**
(Under 0.24.4, flagged rather than decided.) The track spans the whole
catalogue, 2 to 256, where a weave-capped track would offer thirteen
counts with no weave family behind them AND retire a contract that
test states outright -- that a count offering only one kind flips the
toggle silently. One line either way, and the line retires a contract.

**4. THE COLOURSPACE LIMIT WAS CALIBRATED ON A PROFILE NO USER HAS.**
(Under "Design decisions already settled", in CLAUDE.md.) A gate
certifying colour fidelity must not pass because of one machine's
seeded style library; and re-deriving a limit whose baseline was never
representative is close enough to loosening a threshold for a green
run that nobody should do it quietly. Reproduced in thirty seconds
under `QGIS_CUSTOM_CONFIG_PATH=$(mktemp -d)`.

**5. WHETHER THE REFERENCE COLUMN STILL SPEAKS FOR THE WEB APP.** The
comparison PDF's reference column was both the library and the app,
because the app pinned the same library version. The vendor is thirty
versions ahead of the app's pin, six of twelve modules changed
behaviourally, so the claim now rests on a gate that measures the
VENDOR. A live browser capture is the honest third column, and whether
to add one is a decision about what the PDF promises.

**6. THE WINDOW CEILING AGAINST THE THREE LAYOUT PRIORITIES.** At the
real macOS system font the assembled window measures 1334px against a
1280 ceiling, and the three priorities settled on 2026-08-09 cannot
all hold there. Which one gives is a decision, and no runner here can
measure the assembled window -- offscreen reports 1279 at both fonts.

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
   AND A SURVIVOR NAMED THE ARM THAT WAS MISSING. The entry on the
   no-travel exit survived at first, because the test's discard arm was
   a CLICK -- which leaves at the drop's FIRST exit and never reaches
   the travel test at all. An arm that grabs a handle and lets go
   without moving walks that route, and the entry catches. Three exits
   are three journeys, not three lines.
   WHAT IS LEFT OPEN DELIBERATELY is the journey where no rebuild
   follows: the preview then goes on showing what the person asked for,
   which agrees with the change list, where reverting would show a
   design the list denies. THE ORIGINAL REPORT AND ITS MEASUREMENTS
   FOLLOW, kept because they are what a later session will not have.

   **CONFIRMED AND MEASURED.** `_commit_the_drag` clears the preview at the
   drop while the rebuild is asynchronous, so the drawing falls back to
   the topology it still holds -- the one from before the edit -- until
   the build lands. Measured on the default design: the old design
   stays up for 1.676s, and the settled drawing is IDENTICAL to what
   the preview had been showing, so the correct picture was on screen
   and was thrown away and recomputed. On the catalogue's heaviest
   design a build is about twenty-one seconds.
   IT IS NOT WHAT THE THREE FIXES IN rc15 ADDRESS. Those cover a
   landing arriving DURING a gesture and the window between the click
   and the press; this is the window AFTER the drop, which none of them
   touches -- so "still there" was exactly right and it had never been
   fixed.
   THE REPAIR is to keep the preview standing on the path that RECORDS
   an edit and let the landing clear it, which it already does; the
   discard paths must still clear at once. What needs deciding is the
   journey where no rebuild follows, and it wants a state rather than a
   timer.
2. **A ZIGZAG DOES NOT STICK.** Not investigated.
3. **THE NUMBER OF ZIGZAGS CANNOT BE SET FROM THE DRAWING.** Not
   investigated. The drawing offers amplitude; whether the count is
   reachable only through the numeric boxes is the question, and if so
   whether that is a gap or a decision.
4. **THE ZIGZAG HANDLE SITS TOO FAR FROM ITS EDGE.** This is a real
   complaint against a fix for a different real problem: turn and
   zigzag are pushed along one normal from an edge's end and its
   middle, and at equal offsets their separation is half the edge's
   screen length, which cost twenty-three edges their zigzag handle
   until they were moved apart. The answer is a third arrangement
   rather than moving one back.
5. **"MAP THE DUAL" ERRORS WHILE THE TAB DRAWS A DUAL PERFECTLY WELL.**
   Not investigated, and the maintainer's "this doesn't make sense" is
   the right instinct: the tab's drawing and the checkbox reach the
   dual by different code, which is this project's commonest defect
   shape -- one fact, two stores, mended in one.

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

**THREE TABS ASKED FOR ON 2026-08-29, and they are wants with no code
yet rather than work deferred from 0.24.4.** Each changes the shape of
the interface, so each gets `/grill-me` before anything is written --
this project's own rule, and the sessions that took it produced
designs that stuck.

**AND ALL THREE ARE EXPERIMENTAL UNTIL DESIGNATED OTHERWISE, BEHIND A
BOX THAT IS UNTICKED BY DEFAULT.** (Maintainer's ruling, 2026-08-30.) An
**Experimental features** checkbox goes under the THIRD tab, which is
*Map options* -- the tab order is Design, Data & colours, Map options,
Save & open, Help. (R-32.)

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
