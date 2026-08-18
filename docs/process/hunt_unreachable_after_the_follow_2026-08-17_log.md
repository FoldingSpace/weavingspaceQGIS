# Hunt: what the follow's early success made unreachable

Direction: a step inserted before existing handlers; shape: unreachable.
Frozen copy: `$TMPDIR/weavingspace-hunt/unreachable2/tree`.
HEAD moved twice under this hunt (b4956cb, then e2976b0); every claim
below is measured at **e2976b0**, and neither of those commits touches
`_class_counts` or `_row_follows_the_renderer`'s class-count arm.

## 09:40:00  iteration 1

Read every exit downstream of `_on_layer_style_edited` and asked which
one the follow starves. Candidates: the categorized FOLLOW exit's
`combo.setCurrentText(name)` (the follow has already moved the combo,
so the ordinary ramp handler no longer fires); `_clear_quant_
customization` on a followed class count; `_release_copied_breaks`;
the no-data twin; opacity.

RESULT: inconclusive -- the categorized exit calls `_clear_category_
colours` and `_refresh_preview_colours` explicitly for exactly that
reason, so it was written for a combo that does not fire.

## 10:05:00  iteration 2

A row that moves with signals blocked must write the RECORD behind the
widget, or `_refresh_table` restores the record. The follow does this
for the style (`touched`, `last_style`) and for the ramp
(`_ramp_choices`), and NOT for the class count: it writes only
`counter.setProperty("user_k", count)` (dialog.py:5886-5890), while
`_refresh_table` reads `self._class_counts.get(tid)` FIRST
(dialog.py:4211-4216). The twin on the reopen path,
`_adopt_row_symbology`, writes `_class_counts` (dialog.py:4959) and
the copy-classification path writes it too.

Probe `p1_count.py`: assign v1/Quantiles, move the Classes spinner to
6, Generate, then install a 4-class renderer on the element layer and
emit `styleChanged` as QGIS's Symbology panel does.

    after the spinner: _class_counts = {'a': 6}
    seeded ranges: 6
    FOLLOWED: spinner = 4  assignment k = 4  _class_counts = {'a': 6}
    AFTER REBUILD: spinner = 6  assignment k = 6
    AFTER GENERATE: ranges the map draws = 6

RESULT: confirmed

## 10:30:00  iteration 3

Control and second route, `p2_control_and_file.py`.

    CONTROL (spinner never moved): seeded 5, followed 4,
      after rebuild 4, map draws 4
    GPKG RUN: seeded 6, followed 4, after rebuild 6, map draws 6
      sqlite: tiles_a styleQML declares 6 ranges

The control keeps the followed count, so this is `_class_counts` and
not rebuilds discarding everything. The GeoPackage was read with
sqlite rather than through QGIS: the file a colleague opens also
carries six ranges.

RESULT: confirmed

## 10:50:00  iteration 4

The brief's other two questions, `p3_twice.py`, one `styleChanged`
that moves the row AND diverges in colour, with a hand-picked class
colour in place:

    embed_style calls in ONE styleChanged: 3
    stamp calls in ONE styleChanged: 2 with k = [7, 7]
    pick after: {}
    said: ["... follows the styling you set in QGIS: classes to 7.",
           "Choosing a new colour ramp ... discarded 1 class
            colour(s) you had picked by hand.",
           "... now follows the 'Reds' ramp chosen in QGIS."]

So the follow does stamp twice and embed three times on that route,
and every write is of the same current style, so the last one wins and
nothing is lost. `_clear_quant_customization` is still reached, through
the ramp-follow branch, because the follow moves `k` and the trial
renderer then matches. `_last_path` cannot go stale in a way that
matters: `embed_style` writes into the LAYER'S OWN source and swallows
a failure, so a memory layer costs a no-op.

RESULT: ruled out (double stamp/embed, stale `_last_path`,
`_clear_quant_customization` unreachable)

## Not defects, noted in passing

The two notices in iteration 4 misdescribe what the user did -- they
changed the class count, and are told about "a new colour ramp" and
that the element "now follows the 'Reds' ramp", which is the ramp it
already had. Wording, not a wrong map.
