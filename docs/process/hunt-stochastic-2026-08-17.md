# Stochastic hunt, 2026-08-17: what it saw before it was stopped

**JUDGED 2026-08-17 (later the same day): THE TOP SHAPE DID NOT
REPRODUCE.** See "The judgement" at the foot of this file. The record
below is left exactly as the hunt filed it, because a document that
edits away what was claimed cannot be checked against what was found.

Kept because the hunt record says a reproduction worth rerunning
belongs here rather than in a temporary directory. NONE OF THIS IS
CONFIRMED: no claim below has been reproduced by an independent
route, which is this project's bar for calling something a defect.
The ordering is the one the record prescribes -- by how many
INDEPENDENT SEEDS produced the same shape, which last time put both
real findings on top and every fixture fault below.

171 sessions across the batches, 30 steps each.

## Invariant fire counts, so no axis reads as decorative

- `PAINTED` checked 23,240 times
- `RENDERKIND` checked 10,990 times
- `RAMPMATCH` checked 9,038 times
- `HASLAYER` checked 5,153 times
- `NOEXC` checked 4,823 times
- `GROUPCOUNT` checked 3,745 times
- `RECORDS` checked 3,745 times

## Break shapes, most independent seeds first

- **7 seed(s)** — RENDERKIND/table says Graduated layer carries QgsCategorizedSymbolRenderer
  seeds: [102, 106, 109, 133, 135, 138, 142]
- **3 seed(s)** — DRIVER/famspin raised
  seeds: [1, 4, 5]
- **3 seed(s)** — HASLAYER/a table element has no layer
  seeds: [222, 235, 252]
- **2 seed(s)** — RENDERKIND/table says Graduated layer carries QgsSingleSymbolRenderer
  seeds: [100, 114]
- **2 seed(s)** — HASLAYER/an element of the design has no layer
  seeds: [153, 156]

## What to do with this

The top shape -- a row saying Graduated over a layer carrying a
categorized renderer -- is the table lying about the map, which is
this software's characteristic failure and the shape of the defect
found on 2026-08-13. Seven seeds is well above the noise floor the
record describes, so it is the one to reproduce first. The driver
faults (`DRIVER/...`) are the hunt's own and are listed only so
nobody re-finds them.

## The judgement, 2026-08-17

**NOT REPRODUCED.** Seven deliberate transitions were driven, each
settled before it was read, and the row's own text was compared with
the renderer its layer actually wears:

| route | what it stages | verdict |
| --- | --- | --- |
| A | categorized on a text column, then the variable moves to a numeric one | agree |
| B | a Quant style picked while the variable is text | agree |
| C | a hand-picked Graduated row, then the variable turns to text | agree |
| D | the variable changed WHILE a run is in flight, live update on | agree |
| E | a categorized renderer set by hand in the dock, then the row's style flipped | agree |
| F | every table row has a layer after a run | agree |
| G | ...and after a family change alters the element count | agree |

**TWO OF THOSE FIRST READ AS DEFECTS, AND BOTH WERE THE PROBE'S OWN
FAULT.** They are recorded because they are almost certainly what the
hunt was seeing.

D ran first with live update OFF. A row changed with live update off
is *supposed* to leave the map alone until somebody presses Generate,
so the disagreement was the dialog doing as it was told. With live
update on -- which is what a user has -- the queued rerun lands and
the two agree.

E first "changed" the row's style to the mode it was already showing.
The assignment never moved, so the signature never moved, so the hand
styling was preserved exactly as designed. That is the third of the
three shapes docs/TESTING.md lists under "a test can be WRITTEN AROUND
a defect", met from the other side: a probe written around correct
behaviour reports a defect that is not there.

**THE LIKELY EXPLANATION FOR SEVEN SEEDS.** A run carries the settings
it was LAUNCHED with, deliberately, so between a style change and the
queued rerun landing the table and the map genuinely disagree. An
invariant checked without waiting for the dialog to finish answering
fires on that, every time the random sequence happens to change a
style during a run -- which is common, not rare, and would fire on
many seeds without a defect anywhere. This is the "an invariant can
demand that the software get it wrong" shape.

**WHAT WOULD MAKE THIS DECIDABLE NEXT TIME**, and it is cheap: the
invariant must wait on the EVENT (the task clearing) rather than
checking immediately, exactly as `test_ui_affordances_are_deliberate`
was rewritten to do. An unsettled check cannot tell a defect from a
debounce.

**WHAT WAS KEPT.** `_views_disagree` -- the helper behind
`test_random_designs_keep_their_views_in_agreement` -- compared
`_assignments()` against the renderer, which is the CORRECTED view of
the row. It now also compares what the row SHOWS, which is the
stricter and more user-facing question and the one this claim was
about. So the axis the hunt pointed at is now swept over random
designs from inside the suite, whatever the verdict on these seeds.

The two HASLAYER shapes (3 seeds and 2 seeds) were judged only through
F and G above and did not reproduce there. They are weaker claims on
fewer seeds and the same timing explanation covers them; nobody should
treat them as settled on this evidence alone.
