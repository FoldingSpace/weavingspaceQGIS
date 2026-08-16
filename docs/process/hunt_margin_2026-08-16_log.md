# Hunt `margin`, 2026-08-16 — what a relative margin breaks that an ulp did not

Frozen at `ed7231f` via `tools/hunt_probe.py --prepare --name margin`;
HEAD re-read at the end and had not moved. Target:
`bridge._nudge_off_shared_bounds` (v3, bridge.py:1630-1746), which
shrinks a class's upper bound by `(abs(hi) or 1.0) * 1e-9` where the
next range is degenerate and shares the bound.

Every measurement is of a STARTED renderer (`startRender` /
`symbolForFeature` / `stopRender`), with an empty `QgsProject` per
case and `ranges()` bound before subscripting.

## 21:05  iteration 1  [logical]
TRIED:  A RELATIVE margin is an ABSOLUTE gap (bridge.py:1735). At 1e12
        it opens a gap of 1,000 units below the shared bound; any real
        value inside that gap belongs to no range — the v1 harm (a
        value drawn as a hole) through a different door. Swept 9 value
        sets x 4 schemes x k=2..20 = 684 combinations.
RESULT: **confirmed.** 11 combinations orphaned a value the column
        holds. Sharpest: `[2e12]*6 + [2e12-100, 1e12, 5e11]`,
        Quantiles, k=2 — bounds `(5e11, 1999999998000.0),
        (2e12, 2e12)`, and `1999999999900.0` is in neither, so
        `symbolForFeature` returns None. Also Quantiles k=5 and Jenks
        k=4..8 on the same column, and `[1.0, 1.0, 1.0, 1-5e-10,
        1-2e-9, 0.5]` Quantiles k=3 orphaning `0.9999999995`.
NEXT:   establish causation and take it to pixels.

## 21:20  iteration 2  [perturbation]
TRIED:  Same case with `_nudge_off_shared_bounds` replaced by a no-op,
        then rendered onto a magenta chroma-key ground.
RESULT: **confirmed, at the pixels.** With the nudge, area 7 of 9
        comes back `#ff00ff` — the background. With the nudge stubbed,
        every area draws. Bounds `(5e11, 1999999998000.0)` against
        `(5e11, 2e12)`: the nudge and nothing else opens the gap.
NEXT:   the legend, which the docstring makes a claim about.

## 21:35  iteration 3  [differential]
TRIED:  The docstring (bridge.py:1729-1733) claims "QGIS's formatter
        rounds it away, so the label still reads '1 - 5'". Ran 836
        combinations twice — nudged and stubbed — and diffed the
        LEGEND TEXT.
RESULT: **confirmed false above ~1e5.** 64 of 836 combinations print a
        different legend line. Threshold measured exactly, one column
        shape at thirteen magnitudes: identical to 1e4, moved from 1e5
        up. At 1e12 QGIS's `100,000,000,000 - 1,000,000,000,000` is
        printed as `100,000,000,000 - 999,999,999,000`. Arithmetic
        agrees: the default label precision is 4 decimals, so the
        margin shows once `hi * 1e-9 >= 5e-5`, i.e. `hi >= 5e4`.
NEXT:   the journeys v2 died on, and the pins.

## 21:50  iteration 4  [perturbation]
TRIED:  H4 — the margin fails a GeoPackage write / embed_style /
        reopen, as the ulp did (2,413 of 48,948 pixels). 30 round
        trips over 5 columns x 2 schemes x k in (2, 5, 9).
RESULT: **ruled out.** Three round trips moved a bound in its last
        digit (QML writes `%.15g`: `1.4444444444444446` returns as
        `1.444444444444445`) and the drawn colour of every value was
        identical in all 30. The nudged bounds themselves —
        `4.999999995`, `8.999999991`, `-1e-09` — came back exactly.
        The margin is about 1e7 times the round-trip error, which is
        the property v2 lacked. v3 does cure what it was written for.
NEXT:   pins and copies.

## 22:00  iteration 5  [logical]
TRIED:  H5 — a pin placed ON a repeated value is moved by the nudge,
        so a bound a person set stops being the bound.
RESULT: **ruled out at ordinary magnitude.** `pinned={"low": 5.0}` on
        `{1,5,9}` and `{"low": 10.0}` on `[10]*8+[20,30]` keep the
        pinned bound exactly and label it `1 - 5` / `10 - 10`. At 1e12
        the pin is also kept exactly; the orphan of iteration 1
        survives beside it, but it is not caused by the pin. (A pin
        AT the column maximum was not honoured at all — but that is a
        bound `pin_problem` refuses and I did not call it, so the
        probe asked something invalid. Not claimed.)
NEXT:   the small end.

## 22:05  iteration 6  [logical]
TRIED:  H2 — `abs(hi) or 1.0` makes the step a WHOLE UNIT at a bound of
        exactly zero.
RESULT: **ruled out.** The `or 1.0` sits inside the parenthesis and is
        multiplied by 1e-9, so a zero bound steps to `-1e-09`, not to
        `-1.0`. Measured across three zero-crossing columns at k=2..20.
        Negative bounds and bounds spanning zero also step in the right
        direction, `abs()` seeing to the sign.
NEXT:   —

## 22:05  iteration 6b  [observation, NOT the nudge]
TRIED:  small magnitudes, `[1e-9, 1e-9, 1e-9, 5e-10, 2e-10, 1e-10]`.
RESULT: no orphan and no label move from the nudge — a relative margin
        is the right shape at this end. But under **Pretty breaks at
        k=6, 7 and 8 the renderer comes back with ZERO ranges**, so
        every value is orphaned and the element draws nothing at all.
        Nudge-independent by construction (no ranges to move) and so
        not this hunt's finding; recorded because a blank element is a
        wrong map and nothing in the suite covers it.
