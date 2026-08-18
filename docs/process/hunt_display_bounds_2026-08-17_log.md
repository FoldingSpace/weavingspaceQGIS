# Hunt: a display rule that quietly decides what can be stored

Shape: one-boundary. Frozen copy: `hunt_probe --name display-bounds`.
Started against e2976b0; HEAD moved twice under the hunt (413c186,
0c13aa7, d5aa26b) and the copy was re-frozen each time. Every result
below was last reproduced at **d5aa26b**.

Excluded by the brief and not re-reported: `_limit_the_figures_on_show`
lowering `decimals`, already fixed.

## 09:05:00  iteration 1

Enumerated every `QDoubleSpinBox`/`QSpinBox` the dialog owns and typed a
four-decimal value into each, inside its own range, rather than calling
`setValue` (probe `p1_boxes.py`). Question: does the new floor of three
decimals cost anything, and does any dialog box still eat what is typed?

Smallest `singleStep` in the dialog is 0.01 (`opt_offset`); nothing steps
by 0.0001. Every box holds three decimals; `spacing_spin` is exempt and
holds six. Typed three-decimal values survive everywhere. The only loss
is a fourth decimal on `opt_aspect` (0.3581 -> 0.358), which is the
three-figure cap doing what it was written to do.

RESULT: ruled out — the floor of 3 harms no control in the dialog.

## 09:40:00  iteration 2

Read the remaining bounding rules for whether each is a presentation
choice: `_WIDEST_BOUND`/`_LEAST_DECIMALS` in `_bound_box`, the 2..20
class ceiling in `_sync_row` and `_row_follows_the_renderer`,
`setSpecialValueText`, `_format_bound`'s read-only cells, the class
source combo's basename labels over full-path `itemData`, the
`weavingspace_quant_style` JSON stamp, `embed_style`'s thirty-character
style name.

Each is either guarded (`2 <= count <= 20` before the count is adopted;
`findData` not `findText`; full-precision JSON) or declared with its
reason at the site. The bound box's own range was widened to plus or
minus 1e15 hours earlier and is covered by a typing test.

RESULT: ruled out — no undeclared bound among them.

## 10:15:00  iteration 3

`category_editor._add_range_section`: the Ramp Display Range's two
percent boxes clamp each other (`lower_spin.setRange(0, hi)`,
`upper_spin.setRange(lo, 100)`, re-applied in `_slider_moved` and
`_spin_changed`). A `QSpinBox` validator refuses a keystroke that takes
the text past its maximum and KEEPS what it already accepted. Typed
"60" into the lower box with the upper at 40 (probe `p2_range.py`).

Box kept 6. The windows reported to the dialog were (0, 40), (6, 40),
(6, 100) — the user asked for (60, 100).

RESULT: confirmed

## 10:35:00  iteration 4

Second, independent route: drove the real dialog on a CLEAN project,
generated, opened the graduated editor, typed the same sequence, then
read the answer off the LAYER rather than off the widget
(probe `p3_map.py`).

`weavingspace_quant_style` stamped `[6, 100]`. The renderer's five class
colours are `#feebe2 #fcad90 #f85e43 #c6191d #67000d`, which equal
`bridge.quant_class_colours("Reds", False, 5, (6, 100))` and differ from
`(60, 100)` in four of five.

RESULT: confirmed — the swallowed digit reaches the map and the saved
project, not merely the control.

## 10:50:00  iteration 5

Scope (probe `p4_scope.py`). From (0, 100) typing 60 into the lower box
works; from (0, 40) it gives 6; from (0, 9) it gives 6. The mirror on the
upper box is a silent revert: from (60, 100), typing 9 leaves 100.
Dragging the slider from (0, 40) to 60-100 works, so the window IS
expressible — only typing it is not.

`git log -S`: the coupled ranges arrived with the Ramp Display Range
itself, 0ec8ecc, 2026-08-10.

RESULT: confirmed
