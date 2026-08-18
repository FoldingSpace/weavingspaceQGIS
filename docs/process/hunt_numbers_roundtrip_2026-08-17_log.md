# Hunt: numbers the plugin prints and numbers it reads back

Frozen at e2976b0. Shape: two-stores. Copy:
/var/folders/93/3nql803d21v_t9n6f1n8w6000000gn/T/weavingspace-hunt/numbers-roundtrip/tree

Excluded by the brief (already fixed): `bridge.spacing_in_words`.

## 09:40:00  iteration 1
Q: under de_DE, does a number the plugin prints survive being typed
back into a spin box? Probe p1, keyboard via QTest.keyClicks.
RESULT: confirmed  Python-formatted text ("12.5", "-0.9276") parses as
125.0 and -9276.0; the German form works. spacing_in_words is fixed.

## 09:55:00  iteration 2
Q: does the pin/null subset string still filter under de_DE, and are
pinned/copied class labels written Python-style while computed ones
get the locale's? Probe p2.
RESULT: ruled out  subset strings with full-stop decimals are accepted
and filter correctly (QGIS expressions are C-locale). Labels on both
computed and pinned classes come back locale-correct.

## 10:20:00  iteration 3
Q: does the graduated colour editor print a bound in one notation and
parse it in another? Probe p3, real CategoryColourDialog.
RESULT: confirmed  cell prints '12.5', the box in the same row shows
'12,5'; typing the cell's text gives 125.0.

## 10:45:00  iteration 4
Q: end to end, does that reach the map? Probe p4 (low pin) / p5 (high
pin), full dialog, keyboard, ladder read off the ELEMENT LAYER.
RESULT: confirmed  low pin refused with an unrelated message; HIGH pin
accepted: typed '4.052' (the window's own middle-boundary cell), pin
took 4052.0, every break moved, last class (4052, 4052) empty, and
{"pinned": {"high": 4052.0}} stamped on the layer.

## 11:05:00  iteration 5
Q: is the mixed legend ('7,16 - 4.052') a second defect?
RESULT: ruled out  that is QGIS's own German grouping of 4052, not a
Python full stop. Nearly reported; would have evaporated.

## 11:30:00  iteration 6
Q: re-run end to end at current HEAD, and does the box give the user
any cue? Probe p5 at 0c13aa7.
RESULT: confirmed  box echoes '4052' after '4.052' was typed, ladder
moves, stamp written, only notice is the ordinary "1 of its 5 classes
empty". Typing the German '4,052' does the right thing.

## 11:45:00  iteration 7
Q: which other printed numbers disagree with the control beside them?
Probe p6.
RESULT: confirmed (siblings)  coverage_message / icon_coverage_message
print "At 1,234.5 m spacing" where the spacing box shows "1234,5";
pin_problem prints "cannot end at 3.5 ... next break at 2.5" beside a
comma-parsing box; dialog.py:2761 (CRS recalculation), 3108, 8253,
8261, 9051 and bridge 812/1229 all use Python's `:,` grouping.

## 11:50:00  provenance
_format_bound has printed with a full stop since 0ec8ecc (2026-08-10);
the editable pin box arrived beside it in 12f8c3d (2026-08-14), which
is where two notations began sharing one window. The consequence became
a silently redrawn map rather than a refusal on 2026-08-17, when the
outside-the-data refusal was lifted from pin_problem.
