# The hunt record: which directions found defects, and which did not

Every bug hunt this project has run, what it was pointed at, and what
came of it. It exists because the yield of a hunt turns almost
entirely on the DIRECTION it is pointed in, and that is not obvious in
advance — the single worst defect ever found here came from the first
hunt that stopped reading code and started from the user's losses,
after eight hunts reading code had walked past it.

**Keep this current.** The instructions for doing so are at the
bottom, and `tools/bug_hunt_brief.py` tells every hunt to come back
here. A record nobody updates becomes a record nobody trusts, and this
one earns its keep only while the numbers in it are real.

Last updated 2026-09-01, after ROUND SIX -- ten hunts, eight defects
closed, and the first round in which two hunts converged on one defect
from opposite directions TWICE. See the section immediately below;
before that, 2026-08-31 (late), after ROUND FIVE and the day the
twenty-defect campaign closed. See the section immediately below;
before that, 2026-08-29 (late), after the verification session below
and the DECISION session that followed it -- six open questions put to
the maintainer one at a time, all six settled, and two of them turning
into work the version now owes.

WHAT A DECISION SESSION COSTS AND FINDS, since this record has never
carried it. Six questions, about two hours, and the two findings worth
keeping are both about the QUESTIONS rather than the answers:

- **ONE OF THE SIX WAS ALREADY DONE.** Whether `check_standards`
  should require a catalogue anchor to be unique as well as present
  was put as open, decided yes, and found already true since
  2026-08-28 -- with a test and a carve-out for computed placeholders.
  One ledger paragraph said it was recorded rather than done and
  another, forty lines below, said it had been done that night. A
  document that records a question as open after it has been answered
  invites somebody to answer it twice, and here somebody did.
- **AND ONE PREMISE WAS MINE AND WAS WRONG.** The window question was
  put as "narrow the columns; the Colour ramp cell is 172px for a 64px
  swatch and a name". Measured per column at a desktop font, the table
  needs 1096px against 947 -- a deficit of 149, not slack -- so the
  answer that was chosen could not be built. Re-measuring, saying so,
  and putting the question again with the real numbers cost one probe.
  A DECISION IS ONLY AS GOOD AS THE MEASUREMENT UNDER IT, and the
  measurement has to be taken before the question is asked, not after
  the answer arrives.

AND THE SESSION FOUND A CRASH BETWEEN TWO REPAIRS. Running twelve
tests in one process to check a repair's neighbours segfaulted,
reproducibly, at the same point twice: three callables outliving their
dialog reached it through bare lambdas, and an attribute read on a
deleted sip wrapper is a crash rather than an exception. NO SINGLE
TEST COULD HAVE FOUND IT -- each of the twelve passes alone -- which
is the whole-suite argument arriving in a neighbour run of a dozen.

Before that, after the VERIFICATION SESSION that followed
round ten's third wave -- the first time this project has taken an
owed list to the end rather than to the next round.

WHAT A VERIFICATION SESSION COSTS AND RETURNS, measured over sixteen
claims and twenty commits, because this record has never carried the
other half of the method's price:

- **FOURTEEN of sixteen owed claims closed**, each verified here by a
  route its hunt did not use, repaired, guarded by a registered test
  and proved by a catalogue entry. Two remain: one whose cause is now
  measured and written down, and the quadratic Save and Load.
- **THE HARM WAS CORRECTED ON THREE OF THE FOURTEEN, and the door on
  a fourth.** A claim's mechanism is nearly always right; what it
  says the mechanism COSTS is where it goes wrong. The class source
  really is dropped, and the follower keeps the colours it inherited,
  so nothing looks wrong until somebody moves the DONOR -- a slower
  and quieter harm than "the recipient's first Generate repaints it".
  The restyle claim named the Load door and bit hardest on the
  reopened-plugin door, which its hunt never tried.
- **TWO CLAIMS WERE CLOSED BY A FIX WRITTEN FOR ANOTHER**, and both
  were checked on the tree the hunt read rather than assumed: the
  Save box that came back empty after a reopen, and the follower's
  colours, which stopped being adopted once the donor token came
  home. A claim that has stopped reproducing still owes a guard at
  its own door.
- **SIX CATALOGUE ENTRIES WERE ORPHANED BY THESE REPAIRS** and one
  SURVIVED after re-anchoring, because it stood on one limb of an
  if/elif the repair had created. Expect to re-anchor whatever stands
  on a line you touch, in the same commit, and expect the standards
  gate to be the thing that tells you.
- **THE INSTRUMENT FAULTS WERE THE SAME FAMILY AS EVER**, five of
  them: one colour across three arms, so an arm compared a colour
  with itself; a control arm holding a value the fixture's own
  default cycle produced; a box set to the number it already held; a
  note line read once instead of sampled; and a dict watched by
  rebinding an attribute that is a VIEW into a per-dataset bank.
  Every one was caught by a control arm or a premise assertion, and
  none by reading.

AND THE SUITE FOUND WHAT THE ROUND'S OWN REPAIRS BROKE. Run whole at
the session's midpoint: 666 passed, one failed, and the failure was a
repair from earlier the same evening -- a preview refresh added to a
handler that undid the deferring row's own swatch. Bisected in four
runs. That is the fourth defect this round found inside the round's
own repairs, and the ratio this file has recorded since August did not
improve with practice.

Before that, 2026-08-28 (late), after ROUND TEN'S THIRD WAVE -- and the
wave that changed what this file says about COST rather than about
direction.

THIRD WAVE: FIFTEEN HUNTS, TWENTY-THREE CLAIMS, and the first round
whose effort was measured per hunt rather than per round. Every claim
was reproduced here by a route its hunt did not use before anything was
repaired; ten defects were closed with a registered test and a proved
catalogue entry, and fifteen claims remain in a written owed list.

WHAT THE NUMBERS SAY, and they are the answer to "are defects getting
harder to find":

- **Effort per hunt is FLAT across two and a half hours.** Three to
  fourteen hypotheses logged, no upward drift as the ground is picked
  over. What holds it flat is the AIMING: each wave was pointed at
  newer code, including the round's own repairs.
- **131k tokens per claim**, against the 573,967-for-one this file
  records for a round aimed at old ground in August. Per hunt, 205k
  and 32 to 129 tool calls.
- **The cheapest ground is the round's own repairs**: 78k per claim,
  against 144k for the fortnight's new machinery and 156k for old code.
- **Every zero-yield hunt launched in the first hundred minutes**, and
  three of the four were among the highest-effort of the night:
  `sweep`, `weaves`, `boundary`, `stochastic` -- the directions aimed
  at settled ground. Thirty-eight hypotheses between them, nothing
  confirmed.
- Hunts logging three to five hypotheses (`deps`, `pathspellings`,
  `chooserclaim`) found as much as those logging ten, at similar cost.
  The brief should say: on the first finding confirmed by a second
  route, write it up and stop.

AND THE HUNTS ARE NOT THE EXPENSIVE HALF. At 131k per claim they are
cheap against what a claim costs to VERIFY and REPAIR, which runs in
the maintainer's context and is where this round's bottleneck was
throughout. Running more hunts does not raise throughput; it lengthens
that queue, which this file has said since August and which was
demonstrated again by a night that ended with fifteen claims owed.

THE PROBE KIT CAME OUT OF THIS WAVE. `tools/probe_kit.py` is the forty
lines every probe was re-typing, and it exists because the wave
produced four instrument faults in one evening -- a modal shim never
installed, a message store read after the helper that blanks it, a
temporary directory collected out from under an open GeoPackage, and a
fixture that forced the defect into its own control arm. Every one was
already written down somewhere, and every one was made by somebody who
had read the entry describing it. Full reasoning in docs/TESTING.md.

| Direction | Confirmed | The lesson |
| --- | ---: | --- |
| the repairs, fourth and fifth passes | 4 | nine rounds for nine. The moved-data notice written that evening was wrong THREE ways, and the first repair for it was worse than the defect -- so a repair's own repair needs the same suspicion, and the guard has to assert both answers where a rule has two |
| dependencies and consent (1st) | 2 | when a dialogue ENUMERATES, diff the enumeration against a recording of what the code actually requests, driven through the shipped entry point. A whole family of downloads sat outside a hard rule that had a registered test, because the test asserted the box names what it was HANDED |
| the file underneath you (1st) | 1 | when a guard's docstring says "ours" and its code says `startswith`, the covering test is usually satisfied by a fixture name that never tested the claim; pick fixture names from the plugin's own namespace |
| the chooser as a claim (1st) | 1 | when a guard is added to one door, find the siblings by grepping the WALK rather than the method -- three copies of one four-line walk existed and the fix reached two; and a walk that skips "the layer already in force" makes an order-dependent fault deterministic |
| class sources across boundaries | 1 | when a token has two spellings (`file:` and `layer:`), drive BOTH through every crossing, and ask which crossing has no healer rather than which store is stale |
| the legend a reader sees (1st) | 1 | when a fix is inserted into a PIPELINE, enumerate what runs after it and whether any of it redoes the thing fixed; and read the RENDERED legend, which costs nothing extra and is the artefact the claim is about |
| the three absences | 2 | the paired-artefact rule has a second half: grep not only every reader keyed on the twin's identity but every WRITER that iterates the element record and therefore cannot see a twin at all |
| after the map is made (layouts, 1st) | 1 | when a landing CARRIES a value across, read the dependency's own panel and carry its neighbours -- opacity was fixed twice and blend mode sits three rows below it in the same box |
| many real areas (1st) | 1 | hold the WORK fixed and vary only the dimension you are hunting; and where a threshold is reachable only at scale, ask what the fixtures make unreachable |
| the project menu (1st) | 2 | a clear site's survivor keyed by a name every project reuses is STALE rather than empty, which is worse than missing, because "empty" is the branch every recovery path was written for |
| broken and hostile files (1st) | 2 | a hunt aimed at FILES found its defect in the DOOR: when a feature adds a second way to acquire a map, grep for every guard whose precondition only a RUN sets, because the new door sets none of them |
| the sentences about saving | 3 | the productive question was not "is this sentence true" but "what does the sentence's own COUNT ask, and does anything else in the same loop ask something different" -- a count taken from a NAME beside four decisions taken from a STAMP |
| undo and redo (1st) | 1 | a guard whose precondition is a LOSSY digest is only as good as what the digest omits, and a counterfactual pair that corrupts the data identically and differs by one keystroke makes the guard's own machinery supply the positive control |
| path spellings (cross-platform, 2nd) | 1 | the unswept pair was not a path against a path but a SIGNATURE TUPLE against a signature tuple with a raw path inside it, so grepping for path-shaped operands could not reach it |
| icon mode across the new surfaces (2nd) | 1 | when a check moves from COUNTING to GEOMETRY, the first thing to test is a region whose CRS the pipeline changes -- the guard shipped beside it used projected data and could not |
| the modifiers (1st) | 1 | the record path was clean end to end; the loss was in the one store with no record at all, a widget whose RANGE is owned by a sibling control. Grep `setRange` on anything a person types into |
| the live path re-asked | 1 | a notice suppressed on "the user has live update on" is suppressed on a PROXY rather than on the fact: the telling gate and the acting gate must ask the same question, and the acting gate had grown twelve exits since the telling gate was written |
| hand-picked colours through the new doors | 1 | when an act is granted an EXCEPTION to a carry rule, check it grants the exception to every store of that fact; and drive Save AS, because a save that writes the same path twice cannot show a two-store split |
| the ceilings through persistence (1st) | 1 | the stores were all clean at 256 and the defect was in the ACT: a performance round aimed at Generate leaves Save and Load unmeasured, and they are the two acts that reopen a file whose size their own loop is growing |

AND VERIFICATION WIDENED A DOOR RATHER THAN CLOSING ONE, which is the
outcome this record has not carried before. `brokenfiles` reported
that a colour picked on a map opened with LOAD never reaches it, and
the mechanism it named was exact. Driven here with a third arm the
hunt had no reason to try -- the plugin closed and opened again, which
adopts a group rather than landing one -- the same silence appeared on
a journey the claim never mentioned and the code's own docstring calls
something "users do constantly". A claim's door is worth one extra arm
for the same reason its direction is worth one extra probe: the
mechanism is usually right and its reach is usually reported from
wherever the hunt happened to be standing.

AND A CLAIM'S DIRECTION WAS WRONG AGAIN, which this file already warns
about and which cost nothing this time because it was checked. The
`absences` hunt reported a no-data twin being dropped while its element
survived; driving the same panel act gave the OPPOSITE -- the element's
table dropped and the twin left orphaned -- and the opposite is what
was fixed and recorded. Of one fact written twice, ask which of the two
writers had a reason; of one claim, ask which way round it runs.

AND TWO CLAIMS DID NOT REPRODUCE HERE AT ALL, recorded because this
table is only worth reading if it can look bad. The `projectacts` claim
that opening another project and pressing Save renames that project's
tables after the one you left did not reproduce on either of two
routes, including one that kept a single dialog across the project
change; it stays in the owed list as unverified rather than as
confirmed. And the `bigsave` saving from dropping a discarded OGR open
-- 22.4s to 16.2s at 128 elements on the hunt's machine -- could not be
resolved here at all: 4.12s against 3.72s at 64, and at 128 the
supposedly faster arm came back SLOWER. The change was kept on the
ground that it does not build an object nobody keeps, and the source
says so rather than quoting a number nobody here established.

Before that, 2026-08-28 (evening), after ROUND TEN -- the largest
round this project has run, and the one that changes what this file
says about which directions pay.

ROUND TEN: TWENTY-THREE HUNTS AND A REBUILT SWEEP, KEPT AT EIGHT AT A
TIME AND REPLENISHED AS EACH REPORTED, on the maintainer's
instruction to run until twenty-four defects were in hand. Twenty-four
confirmed, sixteen repaired the same evening with a registered test
each and an entry proved caught wherever one could reach. The ledger
is `defects-2026-08-28.md`.

THREE THINGS THIS ROUND SETTLES, and the first is the sharpest.

**THE UNTRIED DIRECTIONS BOTH PAID ON THEIR FIRST OUTING.** Two of the
four on the "not yet tried" list below were run and both returned a
confirmed defect: CROSS-PLATFORM DIVERGENCE found the twelfth reader
of a region stamp still comparing with `==`, so a project reopened
under another spelling of its own folder orphaned its map -- and it
drove that on a Mac, because `/var` and `/private/var` are a real
second spelling and a Windows-shaped defect needs no Windows. THE
SPECIFICATION ITSELF -- the direction that asks whether a SETTLED
DECISION is wrong rather than whether the code fails one -- measured
that the rule "a quantitative style never stands on a text field"
rests on a claim that is false for numeric strings, so a person whose
numbers arrived through a CSV join is given one colour per value.
The portfolio rule already reserved a third of a round for directions
that cannot pattern-match; what this round adds is that the UNTRIED
ones are the best-value third, and that they stay untried because
they are uncomfortable rather than because they are unpromising.

**A ROUND AIMED AT THE ROUND'S OWN REPAIRS IS NOW EIGHT FOR EIGHT.**
The `repairs` hunt was pointed at a fix that had landed ninety minutes
earlier and found that it carried two keys of a record and left the
third live -- so a saved file named a table it did not hold. That fix
had a registered test and a proved entry when the hunt started.

**AND PERFORMANCE IS A DEFECT DIRECTION, MEASURED RATHER THAN FELT.**
The element ceiling rose to 256 on 2026-08-27, and `scale` found two
quadratics that had been harmless at 26 and were thirty-eight seconds
of FROZEN QGIS at 256. Its method is the transferable part: compare
call COUNTS at four element counts rather than seconds at two, so the
answer is an equation naming its own caller, and use a 50 ms heartbeat
as the second route, because that is the only instrument that tells
SLOW from FROZEN and freezing is the harm.

| Direction | Confirmed | The lesson |
| --- | ---: | --- |
| two-stores (save and load) | 1 | a write that MOVES to a new trigger leaves behind the carry it was doing at the old one, and the docstring travels with it |
| backwards from harm (5th) | (same) | converged independently on the two-stores finding, from the opposite end; counted once |
| cross-platform divergence (1st, was untried) | 1 | grep the READERS of one stamp and ask which of them folds; `/var` against `/private/var` stages a Windows defect on a Mac |
| the specification itself (1st, was untried) | 1 | a justification stated as a fact about a dependency is a probe you can run in ten lines -- and the fact is often true of the EXAMPLE that prompted the rule and false of its SCOPE |
| the instruments audit (2nd) | 3 | run the CONTROL first and make it a plant the checker must catch; when a checker reads a LIST out of another file, ask who maintains that list |
| performance and scale (1st deliberate) | 2 | the ratio is the finding, and the ratio needs four counts; a heartbeat is what distinguishes frozen from slow; and the first Generate is cheap, so a hunt that measures one press measures the wrong press |
| the first five minutes (2nd) | 1 (3 sites) | when a code comment names its own uncovered case AND cites a mitigation, drive the mitigation |
| preview against map (2nd) | 2 | the existing pair asked the COMPUTATION and not the PICTURE; spying on the repaint turned "nothing happened" into a count |
| unreachable branches | 1 | the literal half found only dead code; asking what ELSE makes a precondition true found a destroyed file |
| write-only state (3rd) | 1 | the counterfactual arm -- replay the journey with one suspect record forced to the other arm's value -- turns "these differ" into "this is the cause" in one run |
| the dock-edit family | 1 | when a fix gives a path a MEMORY, ask who refreshes it; the twin with the same memory refreshed at every exit and this one at none |
| the colour editor across boundaries | 1 | a write that never reaches a landing must still reach the durable stores, so every refusal on the fast path is a hole in persistence |
| magnitude as a fixture dimension | 1 | a display rule is only display-only if nothing re-reads the display -- and Qt re-reads it on Return |
| the file's own bytes | 1 | a byte oracle must ask what the dialog COULD have known; the control run with the project KEPT is what turns "the drop is broken" into "the drop depends on adoption" |
| races on the newest surfaces | 1 | the four windows were a red herring; the hiding place was a DEFAULT the suite never drives |
| QGIS-side acts on the panel | 1 | a nine-day-old fix is worth re-asking at every door, and drive a drag the way QGIS does |
| asymmetry (deferred-work flags) | 1 | grep the sites that clear the flag's SIBLINGS, not the flag; and where a cancel reports synchronously, clearing after it is too late |
| the previous round's repairs (8th) | 1 | when a repair carries some keys of a record and not others, re-drive the commit message's OWN examples |
| tests that cannot fail (4th) | 1 + 1 | when an entry is RETIRED because a test was made stronger, mutate the retired entry against the new leg before believing the trade |
| the prose (3rd) | 1 | a user-facing sentence can regress HOURS after the code's own docstring is corrected for saying the same thing |
| one boundary but not another (element ids) | 0 | clean, and it drove the new 256 ceiling end to end through every crossing, which nobody had |
| stochastic (4th) | 0 | 193 settled sessions, six breaks, three of them its own -- and it found that `_settle` never waited on the repaint debounce, so the whole follow family was judged 300 ms early |
| the consistency sweep (2nd) | 0 | rebuilt as a COMMITTED tool this time, 14 acts and 2,972 comparisons clean, with two negative controls proving it can go red |

AND A SECOND WAVE OF EIGHT, launched when the first reached
twenty-four, aimed at ground the first had not walked:

| Direction | Confirmed | The lesson |
| --- | ---: | --- |
| the repairs, third pass | 2 | a repair that keys a fact by subject must key its OVERRIDE by subject too -- the fix for "a per-file fact on a session-wide control" shipped with a session-wide control governing it; and a flag added to make a resume count as work must be checked against every clause that exists BECAUSE a resume is not work |
| the twelve retirements, re-judged | 1 + 2 corrections | a retirement is two claims -- "the mutation survives" and "something else answers" -- and only the second needs a control; where the promise is carried by a flag, check that the named test's journey ever ARMS it |
| two dialogs and retirement | 1 | this project fixes retirement one door at a time and writes each fix in the door it was found at; diff the two teardown twins line by line and probe every line only one of them has |
| coordinate systems | 1 + 1 sibling | the round trips are clean; what is not is every place that rebuilds a layer from its SOURCE STRING, because a CRS a person assigned is on the layer and not in the string -- grep for `QgsVectorLayer(x.source()`, not for CRS |
| icon mode across the new surfaces | 1 | the boundaries were clean and the ARITHMETIC was not; where a project has already fixed a count twice, check the third against the geometry rather than against the code that computes it, because the test guarding it was written from the same arithmetic |
| the third hop of a shared file | 1 | replacing a file with `shutil` under a live QGIS proves nothing -- the running process serves its own cached pages, so the second writer must be a second PROCESS |
| edit sessions on the region | 1 | when a write moves from a run's landing to a user's button, every argument the landing handed it becomes a live read, and the fix its twin already received does not travel with it: diff the CALLER, not the callee |
| the second five minutes | 1 | RETURN is worth sweeping in PAIRS OF DOORS rather than in acts -- forty-five act-and-inverse pairs came back clean, and the one failure was a control armed by two paths where only one tells the display |
| weaves and strands | 0 | walked and empty, which is worth as much: seventy-seven strands codes through Save, Load, a group switch and the .qgz, character for character. And the suite's own fingerprint is blind to strand width, so three of the hunt's own readings could not have failed until it switched to tile AREA and proved the measure moved first |

AND THE VERIFICATION QUEUE WAS THE COST, again and more so. Every
claim above was reproduced here by a route its hunt did not use before
its fix landed. Two of my own harness faults are tallied in the
ledger, and one of my repairs was aimed an exit too low and was caught
by the hunt's own reproduction rather than by my reading. One
correction belongs at the top of any read of this round: THE
QUEUED-PRESS DEFECT FIXED THAT MORNING WAS THE SUITE'S AND NOT A
USER'S -- the Generate button is disabled for the whole of a run, so
no press can reach that state -- and the harm had reached four binding
documents and a candidate's tester notes before anybody asked whether
a person could drive the journey. Ask that as separately as you ask
about the mechanism.

Before that, 2026-08-26 (late), after ROUND NINE -- the bulletproofing round, below -- and before it TWO MORE ROUNDS of eight hunts
each -- the fifth and sixth this project has run, and between them the
strongest evidence yet for the method and for its cost.

ROUND FIVE: EIGHT HUNTS, SEVEN WITH FINDINGS, FOUR DISTINCT DEFECTS,
aimed at seven fixes made the same morning. THREE hunts converged
independently on one defect and TWO on another, from directions chosen
before any of them had read the code. The one that found nothing was
worth its place twice over: it established that the adaptive preview
wait's widening is reachable from real state (871 ms at 26 elements
over a hundred columns, arming the timer at its ceiling), which was an
open question, and it caught a false claim in the project's own
binding prose -- a rebuild's cost tracks elements and FIELDS, not
features, measured at 30,529 primitive calls over sixteen areas and
30,529 over three thousand.

ROUND SIX, AN HOUR LATER, AIMED AT ROUND FIVE'S REPAIRS: EIGHT HUNTS,
FIVE DEFECTS, and FOUR OF THE EIGHT ON ONE LINE. That line was a call
added to a branch in round five's own repair and placed AFTER the
restore where its twin puts it BEFORE. Four hunts reached four
different consequences of it: every element's variable re-derived
against the wrong dataset, the pins and categorical colours skipped
outright, the group stamped with the loss, and -- the worst thing
found all day -- one map's hand-picked value strings written into
ANOTHER dataset's memory bank and its GeoPackage, which is ruling 8's
cross-dataset leak. PRESENCE IS NOT ORDER, and no reading of "is the
call there?" would have found it.

SO THE CLAIM THAT A ROUND AIMED AT THE LAST ROUND'S REPAIRS ALWAYS
FINDS SOMETHING NOW STANDS AT SIX FOR SIX, and round six is the
sharpest case: the repairs were an hour old and had been driven,
tested and given proved catalogue entries before it started.

AND THE COST IS STILL THE JUDGEMENT, not the machine. Sixteen hunts in
an evening produced roughly a dozen claims to reproduce, five of my
own harness faults while reproducing them, and three catalogue entries
that could not be made to catch on the first fixture. One of those
three was never made to catch at all: the ORDER above is guarded by
the hunts' own reproductions rather than by an entry, because adoption
covers a late recovery by accident through the layer stamps -- an
accidental cover, which this record already knows is a countdown
rather than a defence.

Before that, 2026-08-26 (day), when a FOURTH round's claims were
finally judged. NINE CLAIMS, SIX CONFIRMED, THREE REFUTED -- and the three
refutations are the entry worth reading, because this record's value
depends on it being possible to look bad in.

WHAT A REFUTATION COSTS AND BUYS. Each of the three named a REAL
asymmetry in the source: a guard genuinely missing from two of three
doors, an embedded region genuinely loading under a source string the
gate cannot match (measured), a chooser genuinely moved outside a
flag. None of them costs a user anything, because in every case a
second mechanism answers first. Judging them took about as long as
judging the six that were real, which is the queue this record
already names as the limit on the method.

AND TWO OF THE THREE PAID FOR THEMSELVES ANYWAY. The probe written to
refute the mid-run claim found the chooser MISLABELLING a group,
which led directly to the worst of the six -- a map destroyed. The
probe written to refute the embedding claim measured the gate
answering DIFFERENT on the one journey embedding exists for: true,
benign today, and precisely the shape this file records from the
other side, where a fix removed the accident hiding a defect three
hours later.

Before that, 2026-08-25, after THREE rounds totalling eight hunts:
ELEVEN confirmed defects, nine of them inside the same day's repairs.
THE CURVE DID NOT FLATTEN -- four defects, then three, then four --
and every round aimed at the last round's fixes found something. That
is the argument for not building a candidate while hunts are still
running, which is now written into ROADMAP.md as well.

Before that, after TWO rounds totalling six hunts: SEVEN
confirmed defects, and the second round is the argument for the
second round. Four hunts found four; three hunts aimed at those four
REPAIRS found three more, one of which the first round had examined
and ruled BENIGN -- it went live because a fix removed the accident
hiding it. Six of the seven were inside repairs. The round is in
`defects-2026-08-25.md`; the second round's directions were the
dataset identity (two-stores), door three's in-place edits
(one-boundary), the reset flag (write-only) and the user's losses
(asymmetry), and the losses hunt found the one that cost a finished
map.

Before that, the same day's FIRST round of four hunts: FOUR confirmed
defects, four for four, every one in
code written within hours and THREE of the four inside repairs for
defects the same day had found. Two hunts converged INDEPENDENTLY on
one defect from different directions, which is the strongest
confirmation this method produces -- and the second hunt saw what the
first could not, that a LAYER COUNT decided which of two code paths
ran. The round is written up in `defects-2026-08-25.md`; the
directions were the banks (two-stores), the boundary (asymmetry), the
switch acts (one-boundary) and the shelf (write-only). The
distribution has now held across four separate rounds, which is the
argument for aiming at fresh work as a matter of course.

Before that, 2026-08-20, after a round of EIGHT hunts aimed at the
previous day's repairs. Five confirmed defects; FOUR were in code
written that day and THREE of those four were inside repairs for
defects the same day had found. The entry is under "2026-08-20"
below. The ratio has not improved with practice, which is the
argument for aiming a round at fresh work as a matter of course
rather than when somebody remembers.

Before that, 2026-08-19, when a MATRIX rather than a hunt found three
defects in a day -- two of them in ground the feature under
construction had nothing to do with. The entry is under "2026-08-19"
below; the short version is that adding an AXIS to an existing grid
outperformed adding a hunt, and cost about two minutes of machine time
because the grid samples.

Before that, 2026-08-17, when the stochastic hunt's seven-seed claim
was judged and did not reproduce; the lesson it left is under "What
the record says", above the entry it corrects.

Before that, 2026-08-16 (evening), after SIX rounds in one day: three against
the No Data feature as it was written, then four aimed at the same
day's fixes, then six more after those. Twenty-one hunts in all.

THE DISTRIBUTION IS THE FINDING, and it sharpened as the day went on.
Of the later rounds' fourteen confirmed defects, ELEVEN were in code
written within the previous few HOURS, and five were inside repairs
for defects the earlier rounds had found. Three separate attempts at
one fix were each withdrawn after a hunt measured what they broke.
A hunt aimed at fresh work is not a check on old code; it is the
last stage of writing the new code, and this project should treat it
as part of the change rather than as an audit afterwards.

The earlier note, kept because its numbers are still the ones quoted
below: eleven hunts were launched across the first three rounds; the table below carries rows for the directions whose
findings were confirmed and acted on. IT IS NOT A COMPLETE ROSTER OF
THE ELEVEN, and saying so is the point of a record that counts against
itself: several hunts wrote their logs into session scratch that has
since been cleared, so their hypotheses-logged counts cannot be quoted
honestly and are not. What IS quoted is what was reproduced
independently and fixed.

The round is worth one summary line, because the distribution is the
finding. Of roughly seventeen confirmed defects across the three
rounds, THIRTEEN WERE IN CODE WRITTEN THAT SAME DAY, and three were
inside earlier fixes for the same feature. Hunting is usually
described as looking for old bugs; here it was overwhelmingly a check
on new work, and the directions that paid were the ones aimed at
shapes (a paired identity, an order, a record that outlives its
subject) rather than at features

## ROUND SIX, 2026-09-01: ten hunts, eight defects, and a verification queue that was the whole cost

Eight hunts at once in worktrees under `dev/hunts/round6`, with the
consistency sweep run beside them per the standing rule, and TWO
REPLACEMENTS launched as repairs completed rather than as hunts
reported -- which is the maintainer's own instruction and matches what
round five found. The sweep came back clean: 14 acts, 2,972
comparisons, no disagreements and no harness faults of its own,
including the five boundary crossings that went red the first time it
ever ran.

| Direction | Confirmed | The lesson |
| --- | ---: | --- |
| the specification itself (2nd) | 1 (+1 in the same sentence) | when a ruling says a conversion happens "at the one place", COUNT the places -- `in_map_units` had one caller and the drag preview was not it, so a gesture's two halves disagreed by the whole span of the unit |
| backwards from harm (7th) | (same) + 1 | converged on the drag units from the opposite end, having ranked the losses before opening the source; its second finding was the vertex branch not clamping where the edge branch does |
| the round's own repairs (9th) | 1 | a repair that reads a dependency's dict BY KEY must be run against every key shape that dictionary uses -- one lookup pair covered 871 catalogue entries and quietly declined 297, and the commit's own message named one of the 297 as a case it had measured |
| stochastic settled sessions (6th) | 1 | an ownership answer that our own first act makes true is not an ownership answer: the second save into a colleague's file deleted their layer |
| topology edits across boundaries (2nd) | 1 | when a repair is guarded on "is there an X", enumerate what leaves a STALE X in hand; three of four cells were sound and the fourth differed only in that something non-None sat where the guard looked |
| two stores of one fact, on the tab (2nd) | 1 | a widget that re-derives its view transform from what it is DRAWING has made the transform an output of the gesture as well as its frame |
| tests that cannot fail (5th) | 2 axes | sixteen assertions mutated, fourteen killed cleanly; both dead axes were in tests written the day before |
| the re-vendor's blast radius (1st) | 0, six equivalences | a re-vendor differential must compare SHAPES, not WKT -- normalised WKT invented three reshaped designs at 1e-16 -- and sweep a control's domain before calling a branch unreachable |
| saving and what a colleague receives (1st) | 1 | when a repair closes a second-press ownership flip, sweep every remover taking the same argument in the same commit; three took it and one had been mended |
| today's own repairs (10th) | 0 | a repair that narrows a candidate set from "matched" to "composed" is worth PROVING is a subset first: ten minutes of reading turned six speculative harms into one question, which four probes then closed |

**WHAT THIS ROUND SETTLES.**

**TWO CONVERGENCES IN ONE ROUND, AGAIN, AND ONE OF THEM ACROSS
KINDS.** `spec` reached the drag-units defect by counting the places a
ruling's own sentence names; `harm` reached it having refused to read
the source until it had ranked twenty losses. That is a structural
direction and a consequence direction arriving at one line, which is
the strongest confirmation this method produces and is what made the
claim safe to act on inside the hour.

**THE DESIGN A CLAIM IS DRIVEN ON CAN REFUTE A REAL DEFECT.** Two of
this round's verifications came back clean on the first design tried
and reproduced on the second. A vertex drag past its control's range
records an out-of-range value on `archimedean 4.8.8` and cannot on
`laves 3.3.4.3.4`, where the library refuses the oversized nudge
first; a drag's frame drifts when a VERTEX is held and not when an
EDGE is scaled, because only the first grows the drawn extent the fit
re-measures. Both of my first probes were clean, and both would have
been recorded as refutations by anybody who stopped there. Vary the
design before believing a negative.

**AND THE QUEUE WAS THE WHOLE COST, for the third round running.**
Ten hunts produced twelve claims; verifying them here, by a route each
hunt did not use, is what set the pace, and four of my own repairs
failed their controls before they were right. Two spare slots were
held empty while the queue stood, which is this file's own rule
applied against an instruction to launch more, and it was right again.

## ROUND FIVE, 2026-08-31: eight hunts, and the day the campaign closed

Eight hunts at once, each in its own worktree under
`dev/hunts/round5`, with the consistency sweep run BESIDE them per the
standing rule. The ledger is `defects-2026-08-31.md`.

THE SWEEP CAME BACK CLEAN -- 14 acts, 2,972 comparisons, 0
disagreements and 0 harness faults of its own, including the five
boundary crossings that went red the first time it ever ran. That is
worth as much as a finding: it is ground the next round need not walk,
and it says the instrument can still answer, since its first outing
found three defects in exactly those acts.

| Direction | Confirmed | The lesson |
| --- | ---: | --- |
| the round's own repairs (9th) | 1 | when a repair frees ONE reader from a gate, grep the gate: the twin two hours older keeps it |
| topology across boundaries (1st) | 1 | when a repair makes one owner answer "what is the design", check the OTHER key for terms that were never design terms -- `crs` rode in through `_unit_kwargs` and is invisible to any comparison of design widgets |
| backwards from harm (6th) | (same) | reached the same defect from the opposite end, by two different acts; counted once. Its own ranked list put the finding at 3/13 and 13/13 and the ranking did not find it -- the PAIRING did |
| the deferred-work queues (1st) | 1 | when a project documents one reading as "a second reading of one question", diff the two term by term: the older had never learned the newer's first line |
| stochastic settled sessions (5th) | 1 | gate every act on what the interface actually ENABLES -- three of its six harness faults were states no person could drive, and the invariant reported all three as defects |
| the experimental tabs (via stochastic) | (same) | converged with the boundaries hunt on a gate that opens a tab and never fills it; counted once |
| the prose (4th) | 3 | when a prose gate is written for ONE document, grep the same fact in every other -- the weave ceiling was corrected in the guide that morning and left standing in the changelog, which more people read |
| audit the gates (3rd) | 3 | run the whole promise of a checker's docstring as a BATTERY: four controls and six misses came out of one script |
| matrix cells that cannot fail | 3 axes | two of the three dead axes were in tests written that same morning, which is this project's standing one-in-five holding on the freshest possible work |

**WHAT THIS ROUND SETTLES, and the first is new.**

**TWO DEFECTS WERE FOUND BY TWO HUNTS INDEPENDENTLY, in one round.**
That has happened before; twice in one round has not. Both times the
pair came from opposite kinds of direction -- one reading structure
(boundaries, the gates) and one reading consequence (harm, stochastic).
The portfolio rule already reserves a third of a round for directions
that cannot pattern-match; what this adds is that the CONVERGENCE is
what makes a claim safe to act on within the hour, and it only happens
if both kinds are in the round.

**READING THE DOCUMENTS IS STILL A DIRECTION, AND IT WENT FIRST.** The
maintainer asked for every procedural document to be re-read before any
work. That produced the day's first defect inside an hour -- a release
gate blind to everything quoted after a fenced block -- and it is the
third time this row has paid. It costs no machine time and it is the
only direction that finds a defect in the INSTRUMENTS by reading what
they claim.

**THE VERIFICATION QUEUE WAS THE WHOLE COST, AGAIN, AND IT WAS WORSE
THIS TIME BECAUSE THE MACHINE WAS FULL.** Eight hunts saturated this
Mac, and two of my own verification probes died on their own premise
under the contention -- which I reported as contention twice before
measuring it and finding the real cause was a shared `QgsProject`. The
standing advice is unchanged and now has a sharper edge: running eight
at once does not raise throughput, and it actively degrades the
JUDGING, which is the part that cannot be delegated.

**AND THE HOLDING OF EMPTY SLOTS WAS DELIBERATE.** The instruction was
to replenish as each hunt reported. After five had reported the queue
held three confirmed-but-unrepaired defects, three dead axes and three
gate findings, and the slots were left empty until it cleared. That is
this file's own rule about the queue, applied against an instruction to
launch more, and it was the right call: the remaining defects were all
closed from the existing claims without a new round.

## How to run one

Six steps. The whole thing costs an evening of machine time and a few
hours of yours, and the last step is the one that decides whether any
of it was worth doing.

**1. Choose a direction, not a place.** See below for what that
means, and read "The record" first: a direction already tried and
empty is worth knowing before you spend a night on it.

**2. Generate the brief.**

    python3 tools/bug_hunt_brief.py --shape asymmetry --area "worker.py and compat.py"

`--shape` is one of the structural questions the tool knows; `--area`
is what to point it at. Read the output before sending it. The brief
carries the confirmation protocol, the traps this project has already
paid for, and the calibration notes, and it tells the hunt to come
back and update this file.

**3. Give each hunt its own worktree.** Hunts edit product code to
prove a break, and they will collide with each other and with you:

    git worktree add /path/to/scratch/hunt-<name> HEAD

Editing a tree something else is reading spoiled two measurements in
one night here. This is not optional with more than one hunt running.

**4. Require a check-in log**, at a path you choose, appended to after
EVERY hypothesis and at least every fifteen minutes:

    ## HH:MM:SS  iteration N  [logical|perturbation]
    TRIED:  the hypothesis in one sentence, with file:line
    RESULT: confirmed / ruled out / inconclusive, with actual values
    NEXT:   what that makes you do, and why

The entry goes in BEFORE the next hypothesis starts. The times are
not the point — forcing a hypothesis to be written down before it is
chased is the point, and a log reconstructed at the end has none of
that. Tell the hunt you will check the timestamps, and check them:
two hunts here estimated theirs and it showed.

**5. Watch them.** See the next section.

**6. Verify everything yourself, by a route the hunt did not use.**
This is the step that cannot be delegated and is the real cost of the
method. Of the claims judged here, most survived, one evaporated
entirely, one was a right observation with a wrong severity call, and
one led to a fix that contradicted a settled decision a test had
guarded for months. Running more hunts does not raise throughput; it
lengthens this queue.

## Watching a running hunt

A subagent cannot interrupt itself to report, so the log is the only
window. Poll it on a fixed cadence and print one line per hunt —
entries so far, confirmations claimed, and the newest RESULT:

    S=/path/to/scratch
    while true; do
      sleep 900
      echo "---- check-in $(date -u +%H:%M:%S) ----"
      for f in <names>; do
        L="$S/hunt_${f}_log.md"
        if [ -f "$L" ]; then
          n=$(grep -c "^## " "$L" 2>/dev/null || echo 0)
          conf=$(grep -ci "^RESULT: *confirmed" "$L" 2>/dev/null || echo 0)
          echo "$f: $n entries, $conf confirmed | $(grep '^RESULT:' "$L" | tail -1 | cut -c1-140)"
        else
          echo "$f: NO LOG YET"
        fi
      done
    done

Three things this deliberately does, each of which this project got
wrong somewhere else first:

- **It reports a summary on a cadence, not every line.** One event per
  hypothesis across four hunts is forty notifications nobody reads.
- **It says NO LOG YET rather than staying silent.** Silence from a
  watcher is not evidence that anything is running; an absent log is
  a finding about the hunt, and one of the first things worth knowing.
- **It reads the log rather than the agent.** The agent's own
  transcript is enormous and reading it will drown you.

What to watch FOR, rather than just watching: the ratio of ruled-out
to confirmed. A hunt logging nothing but confirmations is not being
sceptical enough, and the number that predicted a good report here was
how many of its own hypotheses a hunt killed.

Stop the watcher when the hunts finish. A poller left running is the
same waste as a heartbeat nobody stops.

## How hunting compares with the other instruments

None of these replaces another; they fail in different directions.

**The regression suite** answers "is what we fixed still fixed". It
cannot find anything nobody has thought of, and by this project's own
record roughly one test in five, when written, cannot fail at all.
Hunting the SUITE is therefore its own direction, and a productive one.

**Mutation testing** answers "would the suite have noticed?". That is
a question about the tests, not the software. It is worth running for
exactly that — a catalogue sweep returning 173 caught and 1 accepted
is real assurance — but across 128 survivors here it has produced no
product defects, and a campaign budgeted as defect-hunting will disappoint.
Full argument in docs/MUTATION-TESTING.md.

**Differential tests** (UI against library, colourspace against
upstream's own render, project round trips) are the strongest
standing instrument this project has, because a disagreement is a
defect by construction and needs no oracle. Their weakness is that
somebody has to build each pair, and a pair with a motionless axis
silently checks nothing.

**The randomised sweep** finds what nobody suspected, which is its
whole value, and it is the only instrument here that has done so by
accident. Its weakness is that a failure is expensive to read: one
red sweep cost an afternoon of bisecting to establish that the
plugin was right and the fixture was dirty.

**A second machine** (the Linux CI leg) finds what is invisible where
you develop. Its first run found a defect no Mac could show.

**Hunting** is the only one of these that goes looking with a
hypothesis and no oracle at all. It is cheap in machine time and
expensive in judgement — every claim must be reproduced before it is
believed — and its yield depends almost entirely on the direction
chosen, which is why this file exists.

## WHAT TO RUN INSTEAD OF A HUNT, AND WHEN

Added 2026-08-26 (night), and it belongs in this file rather than in
docs/TESTING.md because it is a question about WHERE A ROUND'S TOKENS
GO. Every rc process so far has answered "hunts", and hunts are not
always the best answer. **When a round of hunts is proposed, propose
the sweep beside it and say why one rather than the other.**

THE ARGUMENT, from this file's own numbers. A hunt costs about 200,000
tokens and SAMPLES the space by intuition, which is why four hunts of
eight landed on one line on 2026-08-26 -- convergence is this method's
strongest evidence and also its largest waste. The real cost is the
verification queue, which runs in the maintainer's context rather than
the hunt's. And the yield collapses on old ground: 573,967 tokens for
ONE confirmed defect on 2026-08-15.

Against that, the defects themselves are NOT evenly distributed over
shapes. Most of the ledger of 2026-08-26 is one shape -- ONE FACT HELD
IN SEVERAL STORES, MENDED IN ONE -- and CLAUDE.md now states it three
times about three different whitelists. A shape that recurs that
reliably can be ENUMERATED rather than hunted, and enumeration is
where the economics invert: one build, no judgement queue, a
reproduction attached to every failure, and it goes on catching the
next instance for nothing.

**THE CONSISTENCY SWEEP: ONE ORACLE, MANY ACTS.** A session is a
sequence of acts, and they fall into three kinds this project has
always tested separately -- dialog controls (a ramp, a class count, a
spacing), QGIS-side acts (a renderer edited in the dock, a group
renamed in the layers panel) and BOUNDARY CROSSINGS (closing the
plugin and opening it again, saving and reopening, choosing a group,
switching dataset). All three are judged by the same three invariants,
none of which needs an oracle:

  AGREEMENT   every store holding a fact agrees about it -- the row a
              person reads, the renderer the map draws, the group's
              own record, the record in the file a colleague opens;
  COLLATERAL  an act about element X leaves every OTHER element's row
              and ladder exactly as it was;
  RETURN      doing a thing and undoing it comes back to where it
              started, which is the commonest thing anybody does in a
              dialog and which this project's rules already promise.

ONE FLAG SEPARATES THE KINDS, and it is what lets one harness cover
all of them. A CONTROL act must change something -- an act that
changed nothing passes all three invariants while proving nothing,
which is this project's standing trap. A BOUNDARY CROSSING must change
NOTHING: closing a window and opening it again is not an edit, and
neither is saving a file.

WHAT IT COST AND WHAT IT FOUND, first outing. One evening to build,
about seven minutes to run, no verification queue at all. Seven
control acts passed all three invariants -- which is what makes its
red trustworthy, since the same run demonstrates the instrument can
answer either way -- and the boundary acts went red at once: closing
the plugin and opening it again lost every hand-chosen variable,
style, ramp and class count, while the map went on drawing the right
thing and the file went on holding the right design. Three defects in
all (rows 18 to 20 of `defects-2026-08-26.md`), in ground SIXTEEN
HUNTS had finished reading an hour earlier.

WHY IT REACHED WHAT THE HUNTS DID NOT, which is the whole argument for
keeping both. The hunts were aimed at the day's own code and every one
of them was aimed well -- rows 11 to 17 are all in it. The sweep's
three are older, and they are reached by the most ORDINARY act there
is rather than by an ingenious one. A hunt chooses where to look; a
sweep enumerates what a person does. Neither subsumes the other, and
the sweep is the cheaper of the two by a wide margin.

**AND ITS FOUR-CORNER FORM FOUND NOTHING, WHICH IS WORTH RECORDING.**
Asked at the maintainer's suggestion, the sweep was extended to the
classic question here: a class break, a colour, a ramp or a variable
changed at ONE corner, with four descriptions then required to agree
-- the user's intent, the plugin's row, QGIS's own renderer, and the
GEOPACKAGE read the way a colleague reads it, a fresh layer off the
file with `loadDefaultStyle`. Four doors were driven: a ramp picked in
the plugin, a class recoloured in the dock, a class bound retyped in
the dock, and the DATA edited underneath through the buffer QGIS's
attribute table uses. Every corner agreed at every door, immediately
and after the next Generate. That is the family CLAUDE.md records
failing at the fourth corner repeatedly -- "a retyped break, a changed
ramp, a stroke, a legend label and a deleted category each reached the
map and the project but never the GeoPackage" -- so a clean answer
there is evidence the 2026-08-17 repairs held, and it is ground the
next round need not walk.

AND IT AUTHORS ITS OWN FAILURES, which are counted for the same reason
a matrix's are: TEN of mine against three defects, listed in the
ledger. Eight of the ten were probe faults this project has already
written down -- a freed temporary answering `#000000`, a widget held
across a rebuild, an oracle reading from a stale snapshot, a fixture
that could not exhibit its case -- met again by somebody who had read
those very entries the same evening. The lesson is not that the list
should be longer. It is that ASSERTING THE PREMISE is the only thing
that catches them: the data-edit door reported the map ignoring a
change until the probe was made to check that the twelve values it
multiplied by ten were not all zero, which they were.

WHEN A HUNT IS STILL THE RIGHT ANSWER. When the ground is genuinely
new, so there is no settled invariant to enumerate; and for the
directions that cannot pattern-match at all -- backwards-from-harm and
stochastic -- which the portfolio rule already reserves a third of any
round for, and which found the worst defect in this project's history
after eight code-reading rounds walked past it. The sweep finds
DISAGREEMENTS between things that already exist. It cannot find a harm
nobody has described.

## ROUND NINE, 2026-08-26 (late): the bulletproofing round

Launched on the maintainer's charter -- everything of the last three
days bulletproof, in itself AND as the user experiences it -- with the
consistency sweep re-run BESIDE the hunts per the standing rule, and
the sweep run first because it is nearly free. Eight hunts: doors,
kept, switchdoor, livepreview, picksdict, seams, testbatch (the
per-assertion trigger, fired on the round-eight batch), and harm.
FIFTEEN confirmed product defects (ledger rows 39-53), four dead test
axes plus a shared-fixture fault, two ruling questions grilled and
settled the same night, and the sweep's four claims judged within the
hour -- two of them its own harness faults, one closed by row 42's
mechanism.

| Direction | Confirmed | The lesson |
| --- | ---: | --- |
| doors (asymmetry, keep_adopted) | 4 | a guard at two doors of three is a countdown at the third; a flag with one setter and one clearer leaks through every path that reaches neither |
| kept (write-only, the file limit) | 2 | the file has doors `_file_safe_state` cannot see -- a TABLE drop leaves QGIS's style row -- so a byte oracle must sweep the whole file, not the record |
| switchdoor (prose as claims) | 3 | a notice that flattens per-element pairs lies about the element that lost most; a recovery's setLayer is a switch to every unguarded listener |
| livepreview (timing) | 2 | a repaired pair travels to SOME doors by itself and to none of the rest -- enumerate the doors of a promise, not the fixes |
| picksdict (two-stores) | 1 | when a merge reads two dicts, ask WHOSE key each subscript uses; the twin three lines up had it right |
| seams (rows 29-33) | 3 | a fix one rung up leaves the same shape one rung down (the class source under the picks); retirement cannot cancel a run past its worker |
| testbatch (per-assertion) | 4 axes | the shim's exec intercept makes every visibility axis vacuous; a shared fixture's unasserted landing turns its dependants into tests of the draft |
| harm (backwards from losses) | 2 + sense-2 | ALL FIVE original complaints measured resolved end-to-end -- the round's charter answered -- and the two findings were experience gaps BESIDE fixed rows, which only a harm-first direction reports |

WHAT THE ROUND SAYS. The repairs-attract-defects claim now stands at
SEVEN ROUNDS FOR SEVEN, and the strongest single instance is the
verification queue's own: of the round's fifteen, THIRTEEN are in
code written inside the three-day window and five inside repairs of
the same window's repairs. The sweep-beside-hunts rule earned its
place from the other side this time: the sweep's reopen finding was
the doors hunt's row 42 wearing a session's clothes, and neither
instrument alone would have both FOUND it (the sweep) and NAMED its
mechanism (the hunt).

AND THE VERIFICATION QUEUE STAYED THE COST. Every claim reproduced
here by a route its hunt did not use before its fix landed; my own
harness faults this round -- a wrong-door copy probe, a grab of a
never-shown dialog, a memory fixture across a .qgz, a max-preserving
premise -- are tallied in the ledger beside the hunts' findings, per
the standing practice.

AND THE ENTRY PROOFS WERE A ROUND OF THEIR OWN, which is the part
this record has not carried before. Twenty-one entries: twenty prove
`caught`, one is RETIRED with its redundancy demonstrated by breaking
both routes together. Getting there cost four distinct kinds of
repair, and none of them was "strengthen the assertion":
- two anchors failed on a single backslash becoming a line
  continuation inside the entry's own string;
- two tests could not reach their case (a fixture with no output path
  for the clearing to speak about; one with no landed map for the
  rival to threaten);
- one fixture's `layer:` class-source token VANISHED with its layer,
  so the row forgot the choice and the arm never fired -- a `file:`
  token is the one that can move;
- and one entry was swallowed by a redundancy THIS ROUND created: the
  switch door now stamps the group on the way out of a dataset, so a
  fixture stripping the record before the switch had it re-written
  before the resume ran.
The last is the transferable one. When an entry stops catching, ask
what you added this round that now writes the same fact.

AND THE ROUND CORRECTED ONE OF ITS OWN READINGS IN PUBLIC. The
Windows probe's first output was read here as the recovery run being
refused, on the strength of "the region layer was removed" warnings.
They were the fixture's own teardown -- BAR_MESSAGES accumulates
across a test -- and the real finding was quieter and more useful:
the run leaves no file, no layers and NO MESSAGE, which is what
pointed at a modal refusal and at eight unnamed exits.


## ROUND SEVEN, 2026-08-26 (night): eight hunts at iterative exploration

Aimed at the CORE LOOP on the maintainer's word -- a person exploring
data iteratively -- in eight directions deliberately unlike the
consistency sweep's ground. FIVE CONFIRMED DEFECTS (ledger rows 21-25,
all fixed the same night with tests and proved entries), one marginal
claim, three directions empty WITH MEASUREMENTS. The round's rows:

| Direction | Question | Logged | Confirmed | Note |
| --- | --- | ---: | ---: | --- |
| Backwards from harm (4th outing) | what would twenty minutes of exploring destroy? | 10 | 0 | destruction acts now uniformly noticed-and-recorded; next harm hunt should aim where notices cannot reach (mid-run, multi-dialog) |
| Oscillation convergence | does state after N round trips equal state after 1? | 12 | 0 | twelve pairs convergent across thirteen stores; return invariants look designed-in -- add a concurrency or persistence axis next time |
| The shelf's kept-silently records (write-only) | is any kept record never restored, restored wrongly, or kept only where nobody persists it? | 8 | 2 | both losses were in PERSISTENCE or a sibling's SCOPE, never the keep itself; the control leg (same journey minus the excursion) separates a stamp fault from an adoption fault in one run |
| Preview against map under churn | does either rest describing a design the other never received? | 4 | 1 | the suite's preview tests all call the refresher FRESH, so the widget's resting store was structurally untestable by them |
| Classification churn (unreachable) | does a revisited (scheme,k) redraw the ladder it drew? | 6 | 1 | churn determinism is genuinely solid; the yield was the label-sanity oracle carried along. MAGNITUDE MIX, not magnitude, is the fixture dimension the suite lacked |
| Colour editor mid-iteration (one-boundary) | does a settled map draw what the editor's records hold? | 6 | 1 (+2 medium) | when a dict gains a new KIND of key, grep every site that rebuilds or pops it -- the absence keys inherited the positional picks' lifecycle at three sites and nobody decided any of them |
| Monotonic growth | what grows without bound over fifty iterations? | 5 | 0 | nothing: file size plateaus, receivers stay at one, costs flat. A two-point profile diff LIES about growth; only the per-iteration trajectory separates drift from phase |
| Stochastic (3rd outing) | settled-only invariants over random acts | 8 | 1 marginal | 150 seeded sessions, 149 clean. Settling plus negative controls cut the last outing's 171-session noise to one shape -- which was the product writing back a byte-identical ramp twin's name |

WHAT THE ROUND SAYS. The exploration surface's ordinary acts are well
defended -- three empty directions measured it so. The five real
defects all lived at SEAMS the acts cross: the live path's missing
repair pair, a label formatter met only after classification, a
release scoped wider than its act, persistence writers reading a
mode-filtered view, and a mirror rebuilt without its newest kind of
key. And the verification queue held: every claim was reproduced here
by a route its hunt did not use before anything was fixed, with one
honest exception recorded in the ledger (the preview claim's
independent route could not stage the act, so its proof is the entry).

## ROUND EIGHT, 2026-08-26 (night): eight hunts at the seams

Aimed by the previous round's lessons at what its notices and clean
sweeps could not reach. SIX DEFECTS (ledger rows 29-34, all fixed the
same night), two clean directions with measurements, two ruling
requests raised to the maintainer. The rows, as the hunts filed them:

| Direction | Question | Logged | Confirmed | Lesson |
| --- | --- | ---: | ---: | --- |
| Mid-run acts (one-boundary) | which in-flight act has no guard and no test? | 4 | 1 | enumerate the guarded acts first -- the unguarded door was findable by grep before any probe ran |
| Two dialogs interleaved (two-stores) | what still acts for a retired dialog? | 5 | 1 | the reachable route into a retired dialog is not its widgets but its surviving child windows -- hunt the children |
| Oscillation × persistence (two-stores) | which returns stop finding the work when the trip crosses a save? | 5 | 1 (ruling raised) | a byte-grep of the saved file is the cheapest independent route to "no store holds it" |
| Notices as claims (prose, 2nd) | does every sentence survive being tested as a claim? | 6 | 2 (1 ruling raised) | drive the SAME loss through every door -- the door that speaks hides the doors that do not |
| Class-source family (asymmetry) | QML, templates and copies, iterated | 8 | 2 | when a keep-behaviour is an explicit arm on one path and "signature unchanged" on its twin, iterate a second control into the act -- the promise then rests on a debounce race |
| No-data twin (write-only) | what does a departing twin leave unread? | 11 | 0 | after any landing, tick the event loop before driving a control -- the deferred replay makes a starved probe read its own pick reverting as a defect |
| Data edited between acts (unreachable) | does the settled map follow every KIND of edit? | 7 | 1 | when a digest fixes "the data moved", ask which TYPES its terms can see -- the fix's guard drove the type the fix handled |
| Pixels vs records | does everything drawn match the record beneath? | 6 | 1 | diff a widget grab against the right baseline, or a stripe-count change swallows the stroke you seek |

AND THE VERIFICATION QUEUE EARNED ITS KEEP TWICE OVER: two of the
independent probes drove the WRONG DOOR (a graduated copy call for a
categorical claim; a direct internal call for a journey the fix
closes at the window) and were caught by re-driving through the right
ones; and one catalogue entry took FOUR fixtures to prove, each
failure a different mechanism quietly keeping the behaviour -- the
full ladder is in the ledger, and its moral is that nothing in a
hunt's reproduction is incidental until proven so.

THE ROUND'S TWO RULING REQUESTS WERE GRILLED AND SETTLED THE SAME
NIGHT (ledger rows 37-38, binding text in CLAUDE.md): the file shows
the limit of what it contains while the project carries the whole
working memory home, and the switch door speaks in its twin's
sentence family. A hunt that ends in a RULING rather than a fix is a
full-value outcome, and this round produced two -- both corroborated
across two hunts before they were put to the maintainer, which is
what made each a one-question decision.

## What a "direction" means

A direction is not a place in the code. It is the QUESTION a hunt
asks, and the shape of answer it will accept. "Look at bridge.py" is a
place; "find a path whose twin does the same job differently" is a
direction. Two hunts pointed at the same file with different questions
find different things, and two hunts asking the same question in
different files find the same KIND of thing.

The record below is organised by question, because that is the
variable that mattered.

## The record

Counts are of defects CONFIRMED by independent reproduction, not of
claims made. A claim that did not survive checking is worse than
nothing, so it is counted against the hunt, not for it.

| Direction | Question it asks | Hunts | Confirmed | Notes |
| --- | --- | ---: | ---: | --- |
| **Backwards from harm** | "What would a user be furious to lose, and how could the software do that to them?" | 1 | 2 | Found the worst defect in the project's history on its first run. Its second claim — more classes than the column has values, so swatches appear that no tile uses — was confirmed and fixed on 2026-08-13 (evening), two probes later: the first errored, the second lacked a render context |
| **Instruments audit** | "Does each tool actually enforce the rule it claims?" | 1 | 6+ | Found the catalogue certifying tests that never ran, and (2026-08-13, evening) a documented command — the coverage report — that could never write a report at all, because the suite exits through os._exit |
| **Asymmetry / twins** | "What does this path do that its sibling does not?" | 7 | 11 | The most reliable code-reading direction here |
| **Suite dead axes** | "Which tests cannot fail?" | 2 | 5 | Two dead tests plus an always-true assertion |
| **A value added today** | "Which values written this week are read where the same reasoning applies twice?" | 1 | 1 | New 2026-08-20. Found a guard computed as a DELTA, so armed for one invocation only: correct on the signal carrying the change and false on every signal after it |
| **A guard's return value downstream** | "This check now answers differently -- who else reads that answer?" | 1 | 1 | New 2026-08-20. The cheap questions the brief asked (cost, the empty layer) were both clean; the defect was two hops away, in what the new answer did as a member of a cache key and a signature tuple |
| **Two stores of one fact** | "Which of these two records wins when they disagree?" | 4 | 5 | Yielded well; several claims needed narrowing on verification |
| **Unreachable branches** | "Which guard's precondition nothing produces?" | 3 | 4 | Also caught a red suite nobody had noticed |
| **One boundary but not another** | "Which crossing was not fixed alongside the ones that were?" | 3 | 5 | Strong on export/reopen. Two QML findings confirmed later: a file edited on disk never reaches the map, and a moved file is repainted away on the restyle path |
| **Write-only state** | "What is written and read back by nobody?" | 2 | 2 | Also misjudged a real defect as harmless — see below |
| **Preview against map** | "Do two renderings of one design agree?" | 1 | 1 | An unassigned element previewed in colour and drawn grey, confirmed and fixed. Its other claim — elements silently absent on dense designs — did NOT reproduce over ten configurations on 2026-08-13, and is counted against this direction |
| **Dialog against live layer** | "Does the plugin's belief match the layer?" | 1 | 2 | A column rename destroying categorical picks (fixed), and a provider-level edit invisible to both stores — kept as a documented LIMIT, and the docstring that claimed otherwise corrected |
| **Stochastic sessions** | No question — random actions, invariants checked after each | 2 | 2 | ~100 sessions. Most "breaks" were its own fixture; found a defect present since the first commit, and a crash it hit on three separate seeds. SECOND OUTING (2026-08-17, 171 sessions) added **nothing**: its top shape fired on seven independent seeds and did not reproduce on any of seven deliberate routes when each was allowed to SETTLE first — see below, and `hunt-stochastic-2026-08-17.md` |
| **Reduction beside pinning** | "Does the newer path re-ask the older path's question?" | 1 | 1 | Run 2026-08-15 as an asymmetry hunt over two paths that both change how many classes a map draws. Found the reduction counting the whole column while a pin had already removed a class and its samples |
| **The first five minutes** | "What does a user meet before anything is configured?" | 1 | 1 | Removing the region layer from a project holding three or more polygon layers emits no layerChanged at all, so the dialog holds a destroyed layer and says nothing. Confirmed in substance, NOT in detail: the hunt reported a KeyError modal, and what a second route measured was silence -- a Generate that produced no map and no refusal. Which of the two a user meets depends on whether the surviving layer carries the same column names |
| **Order of operations** | "What order does the suite always do this in, and what happens in the other order?" | 1 | **0** | Two claims, neither reproduced. A hand-typed spacing destroyed by the first Generate: measured at HEAD, the typed 250 survives, because the hunt read a commit PREDATING the fix for the field defect. A project opened under a showing dialog offering the plugin's own output as a region: not reproduced with live update on or off |
| **Suite fixtures as blind spots** | "Which fixture order could no user follow, and what happens in the user's order?" | 1 | 0 | Reproduced the shipped field defect independently and found a second door into it (swapping the region layer), both already closed at HEAD. Three further shapes measured EQUIVALENT to the fixture order, which is worth as much: nobody need re-check them |
| **Paired identity** | "A new artefact carries the identity of the thing it is paired with. What does every reader of that identity do now that two layers answer to one id?" | 1 | 2 | New 2026-08-16, and the most productive single question of that day. Found "Create as new group" deleting the KEPT result's no-data layers, and a GeoPackage style embedded before the opacity it was meant to carry. Its lesson went further than its findings: the sibling faults live in the per-element DICTS, and the tell is a reset list that names some records and not others |
| **Order of operations** (2nd) | "Which setting is acted on at LANDING but recorded from LAUNCH?" | 1 | 1 | Found `opt_outlines`, the only geometry-signature input the landing reads live, so toggling it mid-run cancels its own signature difference and the box goes permanently inert. Present since 0.23.0. Three sibling cases (opacity, ramp, style mode) measured EQUIVALENT, which is worth as much as the finding |
| **Write-only state** (2nd) | "Does each new record survive the journeys it must, and do the clear sites clear the same set?" | 1 | 1 | A project opened under an OPEN dialog: three symptoms, one cause. The lesson is the transferable part — enumerate what a clear site LEAVES, not what it clears, and drive the reopened-project journey with the dialog still open, which no existing test did |
| **Tests that cannot fail** | "Which of the tests just written would pass with the behaviour broken?" | 1 | 3 | Aimed at fourteen tests written the same day, all mutated. Eleven killed everything; three had dead secondary axes, including a tautology that had already been "fixed" once and a literal `x == x`. About one in five, which is this project's historical rate. Turned on our own work rather than the product, and worth repeating whenever a batch of tests is written in haste |
| **Mutation sampling** | "Would the suite have noticed this change?" | many | **0** | 128 survivors, no product defects. It measures the SUITE |
| **The classification nudge** | "What does shrinking every finite upper bound break?" | 1 | 1 | New 2026-08-16, pointed at a change three hours old. Found the nudge DELETING THE COLUMN'S MAXIMUM: the loop moved every finite-width range's upper bound including the LAST, whose upper bound is the maximum, so the largest value belonged to no range, drew as nothing, and a lower value wore the darkest colour. Confirmed by rendering onto a coloured ground, where that tile came back as the background |
| **Backwards from harm** (3rd) | "What would a user be furious to lose, among today's changes?" | 1 | (same defect) | Reached the SAME finding as the nudge hunt, independently and by a different route — it was forbidden to read the source and started from "a value drawn as a gap". Counted once, in the row above, because two hunts finding one defect is one defect. Recorded here because the independence is the evidence: three outings, three first-probe hits |
| **The absence categories** | "Does every reader of *what the classifier cannot place* agree with the split?" | 1 | 1 (+1 minor) | New 2026-08-16. The missing-values notice still counted NULLs alone: two NULLs and four infinities among 144 areas were reported as "2 of 144" while the map drew nine no-data tiles across seven areas, and an infinities-only column produced NO SENTENCE AT ALL. `_element_has_missing_values` had the same one-line scan. Fifth and sixth readers of a predicate widened that morning; the question now has one owner |
| **Tests that cannot fail** (2nd) | "Which of today's tests would pass with the behaviour broken?" | 1 | 2 | Twelve of the day's tests mutated PER ASSERTION, 28 mutants, ten killed everything. Two in twelve, holding this project's one-in-five. Both dead axes sat in tests whose primary axis was live, and one was in a test rewritten THAT MORNING to repair a dead axis — the repair asserted only silence, so deleting the notice outright still passed |
| **The class-bound margin** | "What does moving a class bound break that the last attempt did not?" | 1 | 2 | Third round against the same code in one day, and it paid twice: a RELATIVE margin is an ABSOLUTE gap, so at 2e12 it was two thousand wide and a real value a hundred below the bound was orphaned and drawn as nothing; and above ~1e5 QGIS's own formatter PRINTS the margin, so a legend read "100,000,000,000 - 999,999,999,000". The experiment was withdrawn entirely. Lesson: MAGNITUDE IS A FIXTURE DIMENSION -- every fixture in this suite lived between 0 and 50 |
| **Adoption on projectRead** | "What does a signal that restores state fail to restore?" | 1 | 2 | Aimed at wiring one hour old. Adoption took the group and not `_last_path`, so the next Generate saw a changed destination and built a SECOND group beside the one it had just adopted, both reading the same tables -- the double map the adoption exists to prevent, arriving through the adoption. Also found the connection unguarded and the read path running one of the constructor's three calls, so its own comment claiming parity with a fresh dialog was false |
| **The absence categories** (2nd) | "Does the record survive every journey the rendering now has?" | 1 | 2 (+1 minor) | The colour editor raised IndexError on ANY column holding an infinity -- a row builder still testing one key while its twin had been widened that morning -- so no colour on that element was reachable. And the value digest was built from finite values only, so a NULL edited to an infinity moved nothing, the paired layer kept last run's categories, and those tiles drew as holes |
| **The prose** | "Do the sentences a user reads still describe what the software does?" | 1 | 5 | UNTRIED until 2026-08-16 and productive on its first outing. A tooltip corrupted since 766cada and shipping ever since ("the sloleft step") -- invisible to `test_every_control_explains_itself`, which asks for existence, length and non-repetition, none of which a typo violates. A user guide claiming class bounds are not yours, false since pinning shipped in the same release. A changelog describing a half-fix replaced two hours earlier. It also reached the editor crash independently. Reading prose as CLAIMS finds what no test asserts |
| **Tests that cannot fail** (3rd) | "Which of today's tests would pass with the behaviour broken?" | 1 | 2 | 11 tests, 77 assertions, 41 aimed mutations, 39 killed at the intended line. Both dead axes were substring or fixture faults: `str(4) in "144 areas"` passed with the notice counting NULLs alone, and a MEMORY region layer round-tripped through a .qgz comes back valid with ZERO features, so the second Generate was refused and the closing assertions counted restored layers rather than fresh ones. Third round, third time both sat in tests whose primary axis was live |

**Two hunts, one defect, and it is counted once.** The nudge hunt and
the third backwards-from-harm outing found the same fault within the
hour, from opposite ends: one read the change and asked what it broke,
the other was forbidden the source and asked what a user would lose.
Recording both as findings would inflate the table; recording only one
would hide the more useful fact, which is that a code-reading
direction and a harm-first direction converged. The convergence is
also what made the claim safe to act on immediately.

Rows are updated as claims are judged, which is why several moved
after their hunt reported: a direction's number is what SURVIVED
verification, never what was claimed. One row moved DOWN that way —
backwards-from-harm was recorded at 2 on the strength of a claim
whose probe then errored before measuring anything, and a probe that
proves nothing must not be filed as a confirmation.

## What the record says, so far

**A CLAIM IS A HYPOTHESIS ABOUT A HARM, NOT ONLY ABOUT A LINE.**
Added 2026-08-26, and it is the sharpest thing the verification queue
has taught. This file already says that a hunt reports what it SAW
and the maintainer decides severity; what the fourth round adds is
that the two are separated by a whole journey. All three refuted
claims described the code correctly. Each stopped at the line, where
the harm is a deduction, and every one of those deductions was
answered further down by a mechanism the reader had not walked to. So
drive the journey to its END -- not to the guard that is missing, but
to the map that would be lost -- and where you cannot reach a loss,
say the mechanism is held redundantly rather than that the claim is
wrong.

**AND WHEN A CLAIM NAMES A DIRECTION, CHECK THE DIRECTION TOO.** The
one confirmed claim that mattered most was reported with its
direction REVERSED: a record and a layer stamp disagreed, and the
hunt named the record as the wrong half where the record was right.
Following the reading rather than the measurement would have moved
the field that was already correct and left the leak untouched. The
question that settled it -- of one fact written twice, which of the
two writers had a REASON -- is worth asking of any two-stores finding.

**Direction beats effort.** Eight hunts reading code forward found
fourteen defects and none of them was the GeoPackage data loss, in
which choosing an existing .gpkg as the output destroyed every other
table in it. One hunt starting from "what would a user be angry to
lose" found it in its first hour. Its own ranked list had put that
harm THIRTEENTH of eighteen, guessed safe on the assumption that a
save dialog would guard it. The guess was wrong and the item was the
worst thing on the list — which argues for hunting in directions you
cannot rank in advance, not against it.

**Ask for a structural property, never for "a bug".** The two
best-performing directions ask whether something either is or is not
the case: does this path differ from its twin; does this tool enforce
this rule. An agent asked for that can say "no" and still have done
its job. An agent asked to find a bug is being asked to come back with
something, and it will. The first hunt run here without this framing
returned one claim that reproduced under no configuration tried.

**The instruments are worth auditing, and almost nobody does it.** A
defect in the plugin produces a wrong map. A defect in the tools
produces a wrong NUMBER that everybody then believes, which is worse
because it is invisible and trusted. The first audit of them found the
mutation catalogue reporting CAUGHT for entries whose named test does
not exist, because the lookup raises and the non-zero exit reads as a
kill — while the standards checker's regex validated the name by
reading only its first string literal. Two counting rules, wrong
together.

**The suite is a hunting ground, not just a net.** By this project's
own record, tests that cannot fail appear at roughly one in five. They
are worse than no test: they occupy the ground so nobody writes the
real one, and they report success forever. One sweep found two, plus
an `assert x or True`.

**Observations are more reliable than severity judgements.** The
write-only hunt correctly observed that an exported GeoPackage's saved
style carried an empty custom-properties block, and parked it as
costing "a colleague the tags, not the map". Those tags are what keep
plugin output out of the region chooser; without them the plugin
offers its own output as a region layer and the next map is tiled on
top of the last. The observation was exactly right and the triage was
wrong. Hunts report what they SAW; the maintainer decides severity.

**Verification is the bottleneck, and it is not optional.** Every
confirmed defect above cost an independent reproduction here, by a
route the hunt had not used. That is what keeps the count honest: of
the claims judged so far, most survived, one evaporated entirely, and
one had to be narrowed — a hunt reported a table-versus-map
disagreement, the fix made the map repaint unasked, and it turned out
to contradict a settled decision that a test had guarded for months.
Running more hunts does not raise throughput; it lengthens the queue.

**AND REPETITION IS NOT ENOUGH ON ITS OWN, WHICH IS THE CORRECTION
THIS RECORD OWED ITSELF.** The rule below says to sort a stochastic
run by how many independent seeds produced a shape, on the evidence
that doing so once put both real findings on top. On 2026-08-17 the
top shape had SEVEN independent seeds -- more than either real finding
had ever had -- and it did not reproduce on any of seven deliberate
routes. The reason is that seed count measures how often the random
walk REACHES a state, not whether that state is wrong: an invariant
checked before the dialog has finished answering fires on every seed
whose sequence happens to change a style during a run, which is most
of them.

So seed count ranks what to LOOK AT FIRST and never what to believe.
Before reading a stochastic report at all, ask the question that
decides whether any of it means anything: **does each invariant wait
for the software to finish, or does it check immediately?** An
unsettled check cannot tell a defect from a debounce, and a whole
report built on one is unreadable rather than merely noisy. Two of the
seven routes above first read as defects in the JUDGING probe for
exactly this reason -- one had live update off, where a stale map is
correct, and one flipped a control to the value it already held.

**Repetition is the signal that separates a defect from a fixture
fault.** The randomised hunt's second real finding announced itself
by firing on three separate seeds in three separate batches -- an
emptied region layer making the dialog's fingerprint raise, from a
Qt slot, where nothing reports. Its fixture faults, by contrast, each
appeared once and then went away when the driver was corrected. So
when triaging a stochastic run, sort by how many independent seeds
produced the same shape before reading any of them; that ordering
would have put both real findings at the top and every false one
below.

**A queue of unjudged claims decays, and the decay is one-directional.**
The night of 2026-08-13 ended with seven reported findings nobody had
reproduced. Judging all seven the following evening took a few hours
and turned out this way: four confirmed and fixed, one confirmed and
kept as a stated limit, one deleted as unreachable code, and ONE that
did not reproduce at all. That last one had been recorded as "high
confidence" and, if true, as more serious than the item above it in
the list. Ten configurations later it is a claim that failed.
So the ratio to expect from an unjudged queue is roughly six in seven
real -- good enough that the queue is worth having, and far from good
enough to act on without checking. What makes the difference is that
the checking gets DONE: an unjudged claim keeps its stated confidence
forever, and confidence is the one thing reproduction can move.

**Two probes of mine proved nothing before the third one worked**, on
the same claim, and the reasons are worth naming because they are
generic. The first errored on a missing render context and was
recorded as untested. The second asked the renderer a question
without starting it, and got an answer that meant nothing. Only the
third -- startRender, ask which symbol each feature actually gets,
stopRender -- measured the thing. A probe that errors is not a
refutation, and a probe that returns without exercising the code is
worse, because it looks like one.

**Stochastic search works, and most of what it reports is its own
fault.** Eighty-five random sessions produced about a dozen invariant
breaks, of which one was a real defect — a ramp the dropdown offers
being refused while the user's hand-picked colours are destroyed for
it, present since the first commit and reachable in ordinary use. The
rest were the driver holding a reference to a layer it had deleted,
or intent it dropped itself. That ratio is the method's signature and
is not a criticism of it: no other direction here found something
that had survived every deliberate reading, and the price of that is
triage.

Three things made it work, and all three should be required of the
next one. **Seed everything and print the seed**, so a break is one
command to reproduce. **Shrink before reporting** — a forty-step
failure nobody can read is worth much less than a four-step one. And
**write negative controls**: sabotage the product deliberately, once
per invariant, and check each invariant actually fires. That last one
paid for itself here, because it exposed a hole in the hunt rather
than in the plugin — live update defaults to ON, and one invariant
was only checked when no run was possible, so four batches had barely
exercised it at all. An invariant that never fires is either sound or
broken, and only a control tells you which.

## 2026-08-15, third round: what a moving HEAD does to a hunt

Three hunts on the principle that a fixture must match the ORDER a
user works in. Between them, four claims and ONE defect.

**A hunt reads a commit; the tree does not stop for it.** Two of the
three read `c7b787c` and reported defects that `0f6f5c0` had already
fixed -- one of them the very field defect the fix was written for.
The existing rule (probe a `git archive HEAD` copy and stamp the
commit) was followed exactly, and it was not enough, because it makes
a hunt reproducible without making it CURRENT. The missing half: a
hunt re-reads HEAD before it reports, and says whether HEAD moved
under it. The one that did this caught its own two findings turning
into history and said so; the one that did not filed a fixed defect as
live, with high confidence, and cost an evening's verification.

**A verification's own fixture can hide the harm it is verifying.**
The first reproduction of the surviving finding gave every layer the
same column names, so removing the region layer silently tiled a
different region and looked harmless. The same probe with DIFFERENT
columns showed a Generate that did nothing at all. The rule this
project already has for tests -- when a test mutates a fixture, check
the mutation changed something -- applies to the probes that judge
hunts, and they are written faster and with less scrutiny.

**Equivalence is a finding worth reporting.** One hunt measured three
shapes as equivalent to the fixture order and said so. That is not a
null result: it is ground nobody need walk again, and it is the only
kind of answer that shrinks the queue rather than lengthening it.

## What the mechanics cost, measured 2026-08-15

The audit that produced the harness and the portfolio rule. The
numbers are kept because the changes only make sense against them, and
because anybody proposing to undo one should have to argue with the
measurement rather than with the conclusion.

**Token cost.** Three hunts in one round: 165,391, 193,261 and 215,315
tokens, over 58, 96 and 57 tool calls. 573,967 in total, for four
claims of which ONE survived verification. The two rounds before it
returned 1.17 and 1.25 confirmed defects per hunt against this round's
0.33 -- and the difference was not effort or mechanics but DIRECTION:
both earlier rounds were pointed at code written the same day.

**Setup rebuilt every time.** 373 one-shot probe scripts in one
session's scratchpad, median 79 lines, of which roughly forty were the
same boilerplate re-typed -- standing up QGIS, a project and a dialog.
Names ran `hd_probe1` to `hd_probe9` and `stores_probe1` to `8`: a
fresh file per hypothesis rather than a case on a runner. Order of
18,000 lines written and read back, comparable to one whole hunt.

**And the setup was WRONG.** Eleven hand-written shell wrappers, every
one of them setting `QGIS_PREFIX_PATH` to the doubled path that leaves
QGIS unable to find its style database. Those hunts probed a QGIS with
NO STOCK COLOUR RAMPS and none of them knew. This is the finding that
turned an efficiency audit into a correctness one: a shared harness
would have been wrong once instead of eleven times, and would have
been fixed for every future hunt the day the prefix was understood.

**Stale trees.** Two hunts of the three read a commit that a fix landed
on top of while they ran -- about 350,000 tokens, 60% of the round,
spent confirming defects that no longer existed. One of them filed the
very defect the fix had been written for, with high confidence.

**Unreadable logs.** Two of the three logs drifted out of the
`RESULT: confirmed` shape the supervision loop greps, so watching them
meant reading them whole. A format that is advisory is a format that
costs more to check than to follow.

The scratchpad itself held 30,580 files and 1.8 GB by the end of the
session -- disk rather than tokens, and harmless, but a fair measure
of how much of hunting had become file management.

## The portfolio rule, and why yield is the wrong thing to maximise

Added 2026-08-15 after auditing what hunting costs. Three hunts that
night spent 573,000 tokens between them and produced ONE confirmed
defect, against 1.17 and 1.25 per hunt in the two rounds before. The
obvious conclusion -- point every hunt at whatever scores best -- is
wrong, and the record above is the evidence.

FIVE OF THE THIRTEEN DIRECTIONS ARE THE SAME MOVE: asymmetry and
twins, two stores of one fact, one boundary but not another,
unreachable branches, write-only state. Each reads two code paths and
asks how they differ. They are efficient precisely because they are
pattern matches, and a pattern match finds only what the pattern has
a shape for. The portfolio drifted that way with nobody deciding it.

What the record says about the exceptions is sharper than any yield
figure. The worst defect this project has had -- an existing
GeoPackage chosen as output losing every other table in it -- came
from backwards-from-harm, AFTER eight code-reading hunts had walked
past it, and that hunt's own ranked list had put the harm thirteenth
of eighteen. The stochastic direction, at two confirmations from
about a hundred sessions, found something present since the first
commit that no deliberate reading had found. A process tuned on yield
cuts both of those first.

SO: hold about A THIRD of any round on directions that cannot
pattern-match -- backwards-from-harm, stochastic, and whatever is next
off the untried list -- and judge those on whether they find KINDS
nothing else finds, never on count. Rotate one untried direction per
round. Cross-platform divergence proved itself by accident on
2026-08-15, when a second machine found three faults no hunt would
have; that is the argument for the four still untried.

The sample is too small to tune further, and saying so is part of the
rule: one to five hunts per direction and single-digit confirmations
cannot distinguish 1.8 from 1.3. Rank crudely, spend the judgement on
the direction, and do not mistake the table for a model.

## Two hunts that should be TRIGGERED rather than chosen

Settled 2026-08-16, after a round in which three of four defects were
in code written that day. The yield of a direction is confounded with
the age of what it was pointed at: what repeats is not a clever
question but a productive question meeting FRESH WORK. So two of them
stop being choices and become triggers, fired at the same moment as a
push, with nothing waiting on what they find.

**A batch of tests written in haste gets a tests-that-cannot-fail
hunt.** Run twice now, on fourteen tests and then on twelve: six dead
axes between them, right on this project's one-in-five. That is a
rate, not a hunch, and a rate is a trigger.

**A fix that ships with a single hand-made fixture gets a hunt.** Paid
for on the day it was written down: the class-bound nudge shipped
green against one fixture whose shape was the only one immune to its
defect, and was deleting the column's maximum from real maps.

WHAT IS AND IS NOT AUTOMATED. The mechanical half — would the suite
have noticed this change — is `mutation.yml`'s incremental instrument,
which mutates only the lines that changed. It runs in its own workflow
precisely so it can never colour a push's status. The judgement half
is not automatable and is not pretended to be: an agent reading the
day's diff and asking what a user would lose is a hunt, and it is
dispatched by hand at the same moment.

NOTHING DEPENDS ON WHAT THEY FIND. Their output is a work list for the
next candidate, never a gate on this one, for the same reason the
new-code mutation guard stopped gating: a red that means "write some
tests over the next few days" is not a gate, and treating it as one
teaches people to route around it.

The portfolio rule still governs what ELSE runs. Triggering the two
above does not fill the slate: a third of any round's directions must
still be unable to pattern-match against the code, or the hunts
converge on the failure modes we already know how to see.

## Reading the documents IS a direction, and it found two defects

2026-08-16, and it was not planned as a hunt at all. A session that
began by re-reading every procedural `.md` file turned up, within the
hour, a method DEFINED TWICE in one class -- the categorical colour
editor labelling every value "no data" -- and then, chasing why a
candidate was slow, an uncached swatch redrawn 306,558 times in one
test.

Neither came from a question about the code. The first came from
following a user-guide sentence to the window it described; the
second from asking why a stage was over its usual time instead of
waiting for it. That makes this a sibling of the prose direction, and
the same lesson applies more widely than either: THE DOCUMENTS AND
THE INSTRUMENTS ARE FULL OF CLAIMS, and a claim can be checked
without a hypothesis about where a bug is.

**Performance is now TRIED, and it paid.** It was on the untried list
above, described as "a design that takes ten minutes and produces
nothing is a harm, and nothing hunts for it". What actually happened
is that the harm arrived as a red CI suite, and the direction was
forced. The technique that worked: profile the SAME test at two
revisions and diff the CALL COUNTS, not the seconds. Counts are
immune to profiler overhead and to contention from anything else
running, which is what makes them usable on a busy machine -- the
self-time ratio understated a threefold difference as 1.2x while the
call counts carried it exactly.

**A stopped hunt is a legitimate outcome and belongs in the record.**
Four investigations were launched that afternoon and three were
stopped: two duplicates run on a second model for agreement, killed
when the token cost outweighed the value of a second opinion on work
that could be verified directly; and one real investigation killed
because it was running QGIS suites on the machine where the timing
measurement that decided the release had to be taken. That last is
the reusable point -- A HUNT THAT CONTENDS WITH A MEASUREMENT IS
COSTING MORE THAN IT KNOWS, and the rule against running two
measurements at once applies to agents as much as to processes. Its
question survives as a roadmap entry rather than as a loose end.

## 2026-08-17 evening and 2026-08-18: the portfolio rule, tested

Seven hunts in one round, partitioned by area AND shape, each told
what its siblings covered. Twelve confirmed findings. The round is
worth recording because it was the first chosen deliberately BY the
portfolio rule rather than by what looked productive, and the rule's
own prediction held.

TWO WERE TRIGGERED RATHER THAN CHOSEN, and both paid immediately. A
batch of tests written in haste found a DEAD AXIS in a guard committed
an hour earlier: the window arm narrowed the display range to (0, 20),
and with `lo` at zero the term it was meant to exercise is the
identity, so the preview could forget the low end of the window
entirely and every assertion passed. ZERO IS THE IDENTITY OF THE TERM
THE FIXTURE WAS MEANT TO EXERCISE -- a fixture pinned to the origin of
the quantity under test cannot show an error in it. The
single-fixture hunt found a REGRESSION made that same afternoon, in
the fix for the defect the previous round had reported.

TWO WERE DIRECTIONS THIS RECORD LISTED AS NEVER TRIED, and both paid.

**The specification itself** -- asking whether a settled decision is
WRONG rather than looking for code that disobeys one -- found two
rules giving opposite answers on one case: a constant column with
pins, where the copy door drew five classes and the pin door
collapsed to one, silently, with the stamp still claiming a pin. That
is a kind no code-reading direction can find, because both sites obey
their own rule perfectly. The maintainer ruled the same day.

**The prose** -- the user guide and help text tested AS CLAIMS -- found
three: a sentence describing a control the maintainer had moved the
day before, a ceiling wrong by six for a week, and a vendored commit
that a GATE had never once compared because it split the stamp on
whitespace. The last is the most interesting: hunting prose found a
defect in a CHECKER, which no amount of hunting code would have
surfaced, because the checker's own docstring was the claim being
tested.

WHAT THE ROUND SAYS ABOUT AIM. Four of the twelve were in code written
that same evening, including one regression of mine and one dead axis
in a guard I had committed an hour earlier. Knowing the rate did not
change the rate.

TWO DIRECTIONS REMAIN UNTRIED after this round: cross-platform
divergence, and performance-at-scale as a deliberate choice rather
than forced by a red CI. A hunt was briefed for the first and
cancelled before it reported.

A NOTE ON RUNNING THEM. Every hunt in this round found HEAD had moved
underneath it, some twice, and each said so in its report and
re-measured against the current tip. That is the behaviour to ask for
explicitly: tell a hunt to date every finding to a revision, because a
finding dated to a commit can be re-checked and one that is not has to
be re-derived from scratch. The same applies to documentation audits,
where it was got wrong in this session -- an audit was launched at one
commit and its document rewritten underneath it.

## Directions not yet tried

Written down so they are a decision rather than an oversight:

- ~~**Against an external oracle**~~ — TRIED 2026-08-16, twice, as the
  pixel-level hunts. Rendering the map and reading it, rather than
  asking the object graph, found the paired layer ignoring its
  element's opacity and then a hand-set opacity lost at every
  re-tile. Its technique is worth keeping: render the same scene on
  two backgrounds and opacity falls out per pixel without knowing any
  colour.
- **Cross-platform divergence** — the first Linux run found a defect
  invisible on any Mac. Nobody has hunted that seam deliberately. A
  hunt was briefed for it on 2026-08-18 and cancelled before it
  reported, so the direction is still untried; the brief is worth
  reusing, and its cheapest arm is to run with
  `QGIS_CUSTOM_CONFIG_PATH=$(mktemp -d)` and see what changes, since a
  seeded profile has already hidden three faults here.
- **The specification itself** — every hunt so far assumes the settled
  decisions are right and looks for code that fails them. None asks
  whether a settled decision is wrong.
- ~~**Performance and scale**~~ — TRIED 2026-08-16, not by choice:
  the harm arrived as four red CI suite legs, all stalled at one
  test. Found an uncached swatch redrawn 306,558 times in a single
  test. See "Reading the documents IS a direction" above for the
  technique, which is to diff call COUNTS between two revisions.
- ~~**The prose**~~ — TRIED 2026-08-18 and it paid, three findings
  including a defect in a CHECKER whose own docstring was the claim
  being tested. See the round above. Its lesson for next time, from
  the hunt's own report: read the PREVIOUS outing's committed log
  first, which had already ruled out two of its early candidates and
  had checked tooltips for LENGTH while never asking whether one was
  TRUE. That is where the ground still is.

## How to update this record

Do this at the END of every hunt, before the findings are forgotten
and while the log is still on disk. It takes two minutes.

1. **Add or update the direction's row.** If the direction is new, add
   a row with its question. If it already exists, increase the hunt
   count and add any newly CONFIRMED defects. Confirmed means
   reproduced independently of the hunt that reported it, by a
   different route.
2. **Count claims, not impressions, and count against as well as
   for.** A claim that did not reproduce is recorded — in the notes
   column, in words. The value of this table depends on it being
   possible to look bad in.
3. **Write the lesson, not the incident.** If the hunt taught
   something about how to hunt, add it to "What the record says" as a
   short paragraph with the concrete evidence attached. If it taught
   nothing new, add nothing; a document that grows on every run stops
   being read.
4. **Move anything from "not yet tried" that you tried**, even if it
   found nothing. A direction tried and empty is more useful to the
   next person than a direction untried.
5. **Update `tools/bug_hunt_brief.py`'s calibration section** in the
   same pass. It carries the running tally that hunts themselves are
   told about, and the two must not drift.
6. **Say when.** Change the "Last updated" date at the top. A stale
   date is the only warning a reader gets.

The hunt logs live in the session scratchpad and do not survive. If a
hunt produced something worth keeping — a ranked harm list, an
invariant set, a reproduction worth rerunning — copy it into
`docs/process/` rather than leaving it in a temporary directory.


## 2026-08-15: seven defects, and a instrument that had gone quiet

Six hunts over one evening, all pointed at the pinned-bounds and
copy-to features added in 0.24.3. Seven defects confirmed here after
independent reproduction, every one of them a WRONG MAP rather than a
crash, and every one fixed with a regression test and a catalogue
entry that was proved to catch it.

Three lessons the directions themselves taught, worth more than the
individual finds.

**When one record holds two claims, test them COEXISTING.** The pin
record holds copied boundary VALUES and per-end pin FLAGS. Each
worked perfectly alone, which is exactly why nothing noticed that
together the pin did nothing: the button stayed down, the number was
stamped into the project, and the map did not move. Two of the seven
were this shape.

**When one door into a state is guarded and another is not, check the
unguarded door against every downstream guard sized for the guarded
one.** `pin_problem` refused every pin on a constant column when this
was found, so no pin could put several classes on one value; a copy
could, and the colouring branch downstream had been written for the
guarded door. It left four of five classes on the placeholder grey
they are built with, and the element drew as no data.

BOTH DOORS ARE OPEN NOW, which is the better ending: the refusal was
lifted on 2026-08-17 and a pin was ruled to outrank the one-value
collapse on the 18th, so the asymmetry this entry is about no longer
exists. The lesson survives it -- when one door is guarded and another
is not, the downstream guard has been sized for one of them -- and it
is worth noting that the fix was to open the guarded door rather than
to guard the open one.

**A hunt's OBSERVATIONS outrun its SEVERITY JUDGEMENTS, and its
arithmetic is worth re-deriving.** Every claim reproduced here in
substance; two did not reproduce in detail (a pool reported as two
values was three, a count reported as fifty was twenty), and one
claim was a designed behaviour with a real defect sitting inside it —
copying a ladder onto a column that cannot reach it is the feature
working, while the pin riding along unvalidated is not. Reproduce
independently before believing, and separate the part that is a
defect from the part that is the design.

**The instrument that had gone quiet.** Auditing the catalogue while
adding to it found SEVEN of 243 entries anchored on text that no
longer existed in the file they named. Such an entry matches nothing,
mutates nothing, finds no survivor and exits clean — it reports
nothing, which is indistinguishable from reporting success. Five had
gone silent in a rework the day before and two under the same
evening's fixes. `tools/check_standards.py` now reads every entry
with `ast` and fails when its anchor is absent; it caught one of this
evening's own fixes moving a line another entry stood on, within the
hour. One re-anchored entry then SURVIVED, which was the second half
of the finding: since the constant-column rework either of two
branches delivers the same result on a classed style, so mutating one
alone changed nothing the test could see.


## 2026-08-15, second round: four hunts on a feature five hours old

"Deferring to QGIS" was designed by `/grill-me` and built the same
evening. Four hunts were pointed at it before it had a full day's age:
its twins, its boundaries, races and two-stores, and awkward data.
Between them they found FIVE defects, every one of which reached the
map, and all five were fixed the same night.

The finds, because the pattern in them matters more than the count.
The restyle fast path had no deferral arm while the run-landing path
did -- found by TWO hunts independently, which is some evidence they
are reading real fault lines rather than each inventing one. An
element could never be taken back, because picking the style it had
before deferral restored the old signature exactly and both paths
then read "unchanged". A deferring element moved onto a text column
drew nothing at all, because the new mode string was not "Graduated"
and the text-field guard had never heard of it. And the row never
came back out of deferring when somebody changed their mind in the
dock, because reconciliation ran in one direction only.

**A NEW FEATURE IS THE BEST HUNTING GROUND THERE IS, and hours old is
not too early.** Every one of these five was introduced that evening.
Hunting a feature the day it is written costs a fraction of hunting
it a year later, and the hunts arrive while the person who wrote it
still remembers why.

**The strongest single lesson: when a commit adds a guard, grep its
TWIN before testing anything else.** Two of the five were a guard
added to one path and not to the identical path beside it, and in
both cases the suite's own new test walked through the guarded door.
A test written alongside a fix tends to exercise the route the fix
was written for.

**And the shape of the near-miss is worth as much as the finds.** One
hunt spent three iterations chasing a defect that was being fixed
underneath it in the shared working tree, and another wrongly refuted
a real finding because its probe imported the live tree rather than
HEAD. Both recorded it. The rule that follows: a hunt probes a `git
archive HEAD` copy, never the working tree, and stamps the commit it
read in every claim -- otherwise a sibling's uncommitted fix reads
exactly like a race, and an unfixed defect reads exactly like a fixed
one.

## 2026-08-18 — a tester's report, and what hunting my own fix cost

Not a hunt round: one defect reported from outside, against rc8, with
two screenshots. Recorded here because the shape of the investigation
is worth more than the fix.

**THE REPORT WAS EXACT AND THE SCREENSHOT DID THE WORK.** "Regardless
of *how* I do it, changes to the Q symbology are not reflected in the
plugin", with QGIS holding 0-10, 10-20, 20-30, 30-50, 50-80 while the
plugin's editor showed 3.1-18.3, 18.3-33.5 and so on. THE COLOURS IN
BOTH PANELS MATCHED. That single detail ruled out the whole family of
"the plugin never heard the signal" explanations and pointed straight
at a path that carries colour and not numbers. A screenshot showing
what AGREES is as informative as one showing what differs.

**FOUR DIAGNOSES, THREE WRONG, AND THE MOST CONVINCING WAS THE WORST.**
The colour-comparison story was killed by my own control arm. The
wrong-column story was killed by the tester in one look. The pin story
accounted for EVERY measured number -- the exact top, the 6.6 at the
bottom, a step that was not the span over five -- and was still false,
because a premise was: 9.7 was the TILE layer's minimum and never the
column's. A HYPOTHESIS THAT EXPLAINS ALL THE NUMBERS IS NOT CONFIRMED
BY THAT WHEN ONE NUMBER IS A MISMEASUREMENT.

**A SECOND REPORTED DEFECT WAS NOT ONE.** The plugin classifies from
the SOURCE column while the tester was reading the TILE layer's
statistics, and at that spacing the tiles miss areas. Closed as a
design question -- source or tiles -- which is the maintainer's and is
open. Recorded rather than deleted, because a ledger keeping only the
surviving guess reads as though the answer was obvious.

**THE FIX THEN BROKE AN OLDER GUARD, and bisection found it where
reasoning could not.** An early `return` at successive points through
the new code, the first turning PASS into FAIL holding the culprit:
the STORE. Logging that one statement named what it wrote -- the
plugin's own ladder, recorded as though a person had typed it. Four
theories preceded this and each had been implemented.

**TWO INSTRUMENTS LIED, and cost more than the defect.** `print()`
inside a Qt signal handler goes nowhere under a capturing test, so an
empty dump read as proof the code never ran when it ran every time.
And a plain `python3` heredoc run AFTER sourcing the QGIS environment
dies at bootstrap and applies NO edit, so two "bisect results" were
the unmodified file. VERIFY THAT AN INSTRUMENT CAN REPORT AT ALL
before trusting its silence.

**THE COVERAGE SHARDS SEGFAULTED ONCE AND NOT ON RERUN.** Treated as
mine until proven otherwise, which was right; it proved to be
contention. The related inconsistency is real and unaddressed: the
shards run on the same slow runners as the suite but declare no
`WEAVINGSPACE_TEST_SLOWNESS`, so the job doing MORE work under tracing
gets the SMALLER allowance -- CONTENTION 2.5 against the suite's 3.

**WHAT REPLACED THE ONE-CASE GUARD.** A matrix: seven routes crossed
with nine synthetic shapes crossed with two aftermaths, spine plus
seeded rotation, 36 cells in 58 seconds, and 17 cells fail when the
fix is removed. The guard it replaced changed field, class count and
ramp TOGETHER and had passed for weeks. Written up in docs/TESTING.md
as the default shape for testing a promise.


## 2026-08-19 — a fourth axis found what no hunt was pointed at

Not a hunt round. The maintainer asked for the symbology matrix to
cover QGIS interaction high-dimensionally, on the grounds that class
boundaries and copy-paste of styles are where this plugin's defects
come from. Twelve routes, nine shapes, three aftermaths, three
schemes.

THREE DEFECTS, AND THE FEATURE BEING BUILT ACCOUNTED FOR NONE OF THEM.
A ladder retyped far from the data adopted a ceiling that excluded
every value and left the element with NO CLASSES where it had drawn
five -- reachable only through the new MAGNITUDE axis, since both
canonical shapes live between 0 and 80 where the same retype is
sensible. A dock edit made while a run was finishing was silently
thrown away, which is the rc9 fix rather than the new work, and is the
shape the maintainer had already ruled on for a pasted style. And the
guard for the tester's own report turned out to assert nothing about
the thing that had been reported, which only the mutation catalogue
could show.

WHAT THIS SAYS ABOUT WHERE EFFORT GOES, beside the directions in the
table above: an axis added to an existing grid is cheap in a way a
hunt is not. The grid already knew how to stage an edit and read the
result; the axis cost a parameter and about eighty seconds of runtime,
and it reached ground no direction in this record was pointed at.
Hunting still finds what nobody has thought of; a new axis finds what
somebody thought of once and then only ever tested at one magnitude,
one timing or one scheme.

AND THE GRID AUTHORED FOUR OF ITS OWN FAILURES, counted in the source
because a grid whose failures are mostly its own is one nobody acts
on. Each was an expectation blind to something the software does on
purpose -- Unclassed's exemption from the distinct-value reduction, a
mid-run paste being preserved rather than re-seeded, limits being
inclusive at their own value, and a floor contradicting the ladder
about to be typed over it.

## 2026-08-20: eight hunts at the previous day's repairs

Five confirmed defects. FOUR were in code written within the previous
day, and THREE of those four were inside REPAIRS for defects that day
had found. The full record, row by row with what each still owes, is
`docs/process/defects-2026-08-20.md`.

**THREE HUNTS CONVERGED ON ONE LINE**, from three different shapes:
asymmetry between two doors into a handler, the journey of a recolour
across boundaries, and two new stores of one fact. All three arrived
at a guard that read a MISSING record as a CHANGED one, which shut the
new repaint route in every reopened project. Convergence from
unrelated directions is worth more than any single confirmation: it
cannot be an artefact of one probe's fixture.

**THE STRONGEST SINGLE ROUND SO FAR, AND THE REASON IS THE AIM.**
Every direction here was pointed at code written in the previous
twenty-four hours. The same directions aimed at old ground have
returned little in this project's history — the table above records
that — and the hypothesis this round supports is that the yield
belongs to the AGE of the code rather than to the shape of the
question.

**A NEW DIRECTION THAT PAID, AND IT IS CHEAP TO REPEAT.** "This guard
now answers differently — who else reads that answer?" The cheap
questions its brief actually asked were both clean: the cost was flat,
and a merely empty layer changed no branch. The defect was two hops
downstream, where the new answer travelled as a member of a cache key
and a signature tuple, and killed the restyle path in silence. When a
guard's return value changes, follow it into every tuple it belongs
to, not only into its callers.

**AND ONE HUNT MEASURED ITS OWN NEGATIVE SPACE**, which is why the
ledger can list what was ruled out: an empty layer, a feature count of
-1, a subset string matching nothing, unfiltered cost at every size,
and eight of nine drop branches. Those cost real time and are worth
recording precisely so nobody spends it twice.

**WHAT THE ROUND COST ME RATHER THAN THE MACHINE.** Every claim was
reproduced by a route the hunt did not use before it was believed, and
that queue is what ended the round — not the hunts, which were still
running. Two of my own reproductions were wrong before they were
right: one fired inside a one-second window added the same day, so it
could not reach the case and reported good news; one blamed my own
fixture for a real block, which cost one command to disprove. The
verification queue is the limit on this method, exactly as the
paragraph above on stopping says, and running eight at once does not
raise throughput.
