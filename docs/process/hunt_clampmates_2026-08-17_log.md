# Hunt: controls that clamp each other (one-boundary)

Frozen at 257b37d, re-frozen at 7482c9e and again at 0299c77 when HEAD
moved under the hunt twice. The finding reproduces unchanged at all
three; `_skip_zero_scale`, `mod_scale_x/y` and their keyboardTracking
are untouched by both intervening commits.
Harness: `tools/hunt_probe.py --name clampmates`. Probes in the
session scratchpad; the reproduction is kept beside this log as
`hunt_clampmates_2026-08-17_repro.py`.

Out of scope by instruction: the Ramp Display Range percent boxes,
already reported. (They were fixed in 7482c9e while this hunt ran.)

## 10:41:02  iteration 1
Inventoried every `QAbstractSpinBox` the dialog owns, with range,
decimals and step, and every site calling `setRange`/`setMinimum`/
`setMaximum` after construction: `_on_family_changed` (opt_offset,
opt_offset_angle), `_sync_row` (the class-count cells),
`category_editor._bound_box`, and the reported range widget.
RESULT: inconclusive -- an inventory, not a hypothesis.

## 10:58:30  iteration 2
Hypothesis: some control's range is narrower than the values it ought
to accept, so a validator eats a keystroke. Drove every named box and
the two table cells (class count, opacity) character by character
through `validate()`, inserting between prefix and suffix as QLineEdit
does. Fourteen controls, forty-odd in-range targets.
RESULT: ruled out -- no control refuses a value inside its own range.
The first run said opacity ate keys; that was my simulation appending
after the "%" suffix, not the widget. Fixture fault, recorded.

## 11:20:15  iteration 3
Hypothesis: the range is not the only thing that eats a keystroke. A
`valueChanged` handler that rewrites its own box will do it too, and
`_skip_zero_scale` is one -- `Scale EW`/`Scale NS` keep Qt's default
`keyboardTracking`, so the handler sees the LEADING ZERO of "0.5" as a
landing on zero. Typed with real key events (`QTest.keyClicks`).
`0.5` -> **-0.02**. `-0.5` -> **-0.502**.
RESULT: confirmed.

## 11:34:48  iteration 4
Swept the whole matrix: four starting values x fourteen targets. Every
one of the fourteen sub-unit values a user can type lands somewhere
else; only |v| >= 1 survives. Worst cases invert the SIGN: from a
mirrored design (-1), typing `-0.5` lands on `+0.502`.
RESULT: confirmed.

## 11:52:10  iteration 5
Second, independent route: read the answer off the tile unit's own
geometry (`_build_unit()` centroids) rather than off the spin box, on
a CLEAN project with no layer and nothing run before it. hex-slice
n=3, spacing 1000. Unscaled element 'a' at x=+304.7; after typing
`-1` at x=-304.7 (mirrored, correct); after typing `-0.5` at
**x=+153.0** -- un-mirrored, and 0.4% too wide.
RESULT: confirmed. The map is drawn from the wrong number.

## 12:01:33  iteration 6
When it started: `git log -S _skip_zero_scale` gives 20ae7fe,
2026-08-15, the commit that allowed negative scales and so put zero
inside the range for the first time. Its guard,
`test_a_scale_control_steps_over_zero`, drives with `setValue` and
`stepBy` -- the arrows, never the keyboard, which is why two days of
runs walked past it. The handler's own docstring says "a user dragging
or stepping across zero", so typing was never in view.
RESULT: confirmed.
