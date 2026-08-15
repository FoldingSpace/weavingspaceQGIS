# Hunt log — "Deferring to QGIS" over awkward data, asymmetry shape

Commit read: **e01896b** ("Deferring to QGIS": the row describes the map
even when the plugin stops). `git rev-parse HEAD` = e01896b at the time
of the run. The working tree was dirty (another session building on this
feature), so everything below was probed against a `git archive HEAD`
copy at
`/private/tmp/claude-501/-Users-luke-claude-scratch/9a569ef7-3f5e-4a44-8ecf-716f080f3573/scratchpad/head`,
never the live tree. Probe scripts live beside it in the scratchpad. No
repo source was modified; the only file this hunt writes is this log.

Specification read first: the commit message, and ROADMAP.md's
"Deferring to QGIS" entry (the eight decisions plus THE SWATCH and the
TESTING NOTE). Also CLAUDE.md's settled decisions, docs/TESTING.md,
docs/TEST-MAP.md, docs/process/HUNT-RECORD.md.

Races and two-stores were left to the neighbouring hunt.

---

## Hypotheses logged

1. `bridge.expressible_style` on a graduated renderer over a CONSTANT
   column: the plugin collapses such a column to one class, so the round
   trip may misname the scheme, or worse report an element the plugin
   itself styled as unnameable (= deferring).
2. The Unclassed recognition rule is "equal intervals AND exactly 50
   classes". A distinct-value reduction leaving fewer than 50, or a user
   building 50 equal intervals by hand, may cross that line.
3. `renderer_has_data_defined_fill` is supposed to make the swatch a
   NEUTRAL marker. Driven through the ICON'S PIXELS rather than the
   helper's return value.
4. A deferring element over a column with nulls, against the
   null-handling `make_graduated_renderer` does for its own renderers.
5. (Not on the brief; found while probing.) The RESTYLE route and the
   RUN-LANDING route are twins. `_finish_run` grew a
   `carried_while_deferring` guard in e01896b. Did `_restyle_only`?
6. (Same shape.) `_refresh_deferring_rows` paints the ramp cell's Custom
   display. `_sync_row` also owns that cell. Do they agree?

## What was measured

### H1, H2, H4 — the round trip over awkward columns: NOTHING FOUND

`scratchpad/p2.py`, QGIS 4.0.3. Eight columns (plain, constant, two
distinct, three distinct, nulls, all-null, nine orders of magnitude,
non-finite), each as double and as integer where meaningful, times five
schemes. `bridge.make_graduated_renderer(...)` then
`bridge.expressible_style(renderer)`:

* The four classification methods round-trip **symmetrically** through
  `compat.classification_method` / `compat.scheme_for_method` on every
  column: Quantile, EqualInterval, Jenks, PrettyBreaks all come back
  under their own class name. sip downcasts `classificationMethod()`
  correctly, so no plugin-styled element is ever reported unnameable.
  The dangerous direction — the plugin styles it, the row flips to
  "Deferring to QGIS" and every styling control greys out — **does not
  occur** on any of the columns tried.
* Integer columns behave identically to doubles throughout.
* Nulls, all-null and non-finite columns all stay expressible. The
  all-null column gives 0 ranges under Quantiles/Jenks/Pretty and 5
  under Equal intervals; `expressible_style` still names them, which is
  right.
* Unclassed is exempt from the distinct-value reduction, as intended:
  two distinct values still give **50** ranges, three still give 50. So
  the "<50 classes" case cannot arise from reduction.
* ONE mismatch, with no consumer today: **Unclassed over a CONSTANT
  column** collapses to `k=1` (the constant rule is deliberately placed
  after the Unclassed line and overrides it), so 1 equal-interval range
  comes back as `("Graduated", "Equal intervals")` rather than
  `("Graduated", "Unclassed")`. Both answers are non-None, so the
  deferring boundary is never crossed and no row moves. `expressible_style`'s
  *scheme* half is not read by any caller in e01896b — only the None /
  not-None distinction is. Recorded as a curiosity, not a defect; it
  becomes one the day a caller uses the scheme to set a row.
* A user hand-building 50 equal intervals reads Unclassed. The docstring
  says that is what they made. Settled, not a defect.

### H3 — the neutral swatch, through the icon's pixels: WORKS

`scratchpad/p3.py`, a real dialog, a real Generate, a rule-based
renderer whose rule symbol carries
`QgsSymbolLayer.PropertyFillColor` = `QgsProperty.fromExpression(...)`,
delivered by `styleChanged`. Read off `cell._custom_icon.pixmap(48,16)`:

* plain rule-based → `('888888','888888','888888','888888','00a944',
  '00aa44','00aa44','00aa44')` — the map's own colours.
* data-defined fill → `('c0c0c0',) * 8` — the neutral marker.
* `QgsSymbolLayer.PropertyFillColor` and `PropertyStrokeColor` both
  exist on QGIS 4.0.3, and `isActive()` accepts them, so the helper's
  `except Exception: return False` is not swallowing anything here.
  Field-valued (`QgsProperty.fromField`) fills are caught too.
* A data-defined override set at the **symbol** level rather than the
  symbol-layer level is NOT caught, but QGIS's own styling panel writes
  symbol-layer properties, so this is theoretical.

The promise in the TESTING NOTE is kept for this axis.

### H5 — the restyle route has no deferral guard: **DEFECT**

`scratchpad/repro_defer_restyle.py` (and `p6.py` for the live-update
variant). Clean project (`QgsProject.instance().clear()`, 0 layers at
start), one region layer, element `b` on `v3`, one Generate, then a
rule-based renderer set in QGIS and `styleChanged` emitted. The row
correctly reads "Deferring to QGIS" and the notice fires.

Then **one more Generate, nothing geometric changed**:

```
took the restyle fast path: True
row STILL says: Deferring to QGIS
renderer      : QgsRuleBasedRenderer -> QgsGraduatedSymbolRenderer
map paints    : [00aa44 x120, 888888 x79]  ->  [f7fbff, 6daed6, 2171b4, 08306b]
said          : "restyled b (no re-tiling needed)"
```

Second, independent route: the colours above on the right are read from
a real `QgsMapRendererParallelJob` over the element layer, not from the
renderer object — the map itself is painted in Blues where it was
painted in the user's green and grey.

Mechanism. `_refresh_deferring_rows` (dialog.py ~5299) writes
"Deferring to QGIS" into the row's style combo. `_assignments()` reads
that combo, so `_signature()` moves:

```
recorded: ('v3', 'Graduated',           'Blues', 'Quantiles', 5, ...)
now:      ('v3', 'Deferring to QGIS',   'Blues', 'Quantiles', 5, ...)
```

`_restyle_only` (dialog.py ~5589) re-seeds every element whose signature
moved, and contains **no mention of deferral at all** — grep over its
body returns nothing. Its twin `_finish_run` (~6838) grew exactly that
guard in this commit (`carried_while_deferring`). One door was guarded
and the other was not.

`test_a_deferring_element_keeps_its_renderer_across_a_generate` passes
because it changes `spacing_spin` between the two Generates, which
forces the full run-landing route. The plain Generate — nothing changed
— takes the restyle route the test never visits.

Sharper still, with live update ON (`p6.py`): nudging the element's
**opacity**, the one control decision 6 deliberately keeps live because
it "cannot destroy dock work", is enough on its own. No button press:

```
USER ONLY NUDGES OPACITY
took the restyle fast path: True
renderer: QgsGraduatedSymbolRenderer
map paints: [fafdff, a8cfe7, 7baad2, 6c84a7]   (Blues at 60% opacity)
```

Afterwards the row still reads "Deferring to QGIS" and every styling
control on it is still greyed out with the tooltip "Styled in QGIS; set
it in the Layer Styling panel." — while the plugin has taken the element
back. The row now lies in the direction this feature was built to
remove, and the user cannot restyle the element from the dialog either.

When it started: e01896b. Nothing wrote "Deferring to QGIS" into the
mode combo before it, so nothing moved the signature this way.

### H6 — `_sync_row` wipes the deferring swatch: same shape, smaller

`scratchpad/p4.py`. After deferral the ramp cell correctly shows the
Custom display. `_queue_live` → `_update_dynamic_columns` → `_sync_row`
computes `show_custom` from `mode`, which for a deferring row is
"Deferring to QGIS" — neither "Categorized" nor "Graduated" — so it
falls to `set_custom_display(None)` and the cell goes back to naming
**"Blues"** over a rule-based map. Verified twice over: `showing_custom()`
False, and the widget's own painted pixels (`QWidget.grab()`) change
from the flat sampled swatch to the Blues gradient. Triggered by any
control that funnels through `_queue_live` — the shells spin was used,
the opacity spin does it too.

This is the same missing-guard family as H5 and, in practice, H5 fires
first and makes it moot: once the renderer is gone the cell is telling
the truth again. Reported as a secondary observation, not as a separate
claim.

## Ruled out / not chased

* Races and mid-flight ordering — the neighbouring hunt's ground.
* `renderer_fill_colours`' fall-through to `symbols()`: measured correct
  for rule-based renderers, in the renderer's own order.
* `_element_is_deferring` returning True for an element with no layer —
  guarded, returns False.
* The DEFERRING combo entry's enabled state on non-deferring rows —
  correct, already covered by the suite.

## Where I would look next

The mirror of H5 on the OTHER unguarded doors into a re-seed:
`_rebuild_unit` / the preview path, and the GeoPackage re-read. Each
asks "has the signature moved?" and none of them asks "is this element
deferring?".
