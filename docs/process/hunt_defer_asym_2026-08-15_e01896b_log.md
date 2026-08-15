# Hunt log — "Deferring to QGIS" read beside its twins

Direction: asymmetry. Area: `_refresh_deferring_rows` vs `_sync_row` /
`_adopt_row_symbology`; the deferring branch of `_on_layer_style_edited` vs the
two colour branches below it; `carried_while_deferring` vs `unchanged` in
`_add_output_layers`; `_custom_swatch_for`'s deferring arm vs its Custom arm.

HEAD: e01896b. Started 2026-08-15. Repo source not modified; probes live in the
session scratchpad.

## Reading notes (before any probe)

H1. `_assignments()` resolves `mode_raw == "Deferring to QGIS"` to
`mode == "Deferring to QGIS"` — it is not in `GRAD_SCHEMES`, so it falls through
the `else` to `mode = mode_raw`. Every consumer of `mode` therefore sees a
string none of them was written for.

H2. `bridge.seed_renderer` (bridge.py:2172) branches `not var` / `Categorized` /
`Single colour` / **else graduated**. A deferring assignment lands in the `else`
and gets a graduated renderer built from the row's ramp, scheme and k.

H3. `_add_output_layers` (dialog.py:~6841) grew `carried_while_deferring`, so the
RUN-LANDING path keeps the dock's renderer. `_restyle_only` (dialog.py:5589) has
no deferral test at all: it compares `_signature(a)` with `_last_signatures[tid]`
and re-seeds on a difference. This is the twin asymmetry.

H4. The signature MOVES the moment deferral begins, without the user touching
anything: `_refresh_deferring_rows` rewrites the row's style combo to
"Deferring to QGIS", `mode` changes, `_signature` changes, and
`_last_signatures[tid]` still holds the pre-deferral tuple. Nothing in the
deferring branch of `_on_layer_style_edited` re-records it — unlike the two
colour branches below it, which both do
(`self._last_signatures[tile_id] = self._signature(refreshed)`, dialog.py:4382,
4416, 4515, 4549). That is a second asymmetry, and it is what arms H3.

H5. Opacity is deliberately left live while deferring (RENDERER_COLUMNS omits
column 6). Opacity is applied to the layer only by `_restyle_only` or
`_add_output_layers`, so a user who fades a hand-styled element MUST press
Generate — straight into H3.

H6. `test_a_deferring_element_keeps_its_renderer_across_a_generate` always moves
`spacing_spin` before `_generate_and_wait`, so `_geometry_signature()` differs,
`_restyle_only` returns False and the full run path is taken. The fast path is
never driven while deferring.

## Probes

All probes ran under QGIS 4.0.3's own python via a scratchpad runner
(`defasym_run.sh <root> <probe>`), against PRISTINE `git archive` copies in the
scratchpad, never the shared tree. This mattered: partway through the hunt
`git status` in the shared tree went from clean to three modified files
(another agent added a `_refresh_deferring_rows()` call to `_refresh_table`),
so every number below was re-taken on `defasym_head` = a clean export of
e01896b, and on `defasym_parent` = a clean export of 4e8288e.

### FINDING — a Generate with the design unchanged destroys the dock's renderer

Sequence, all of it what a user does: Generate a map; restyle element `b` in
QGIS's Layer Styling panel to a rule-based renderer; press **Generate tiled
map** again without touching anything in the plugin.

Measured on `defasym_head` (e01896b), via the real `generate_btn.click()`:

| | renderer | row's style cell | interior pixels |
|---|---|---|---|
| after the dock edit | `QgsRuleBasedRenderer` | `Deferring to QGIS` | 640 of (0,170,68), 91 of (136,136,136) |
| after Generate | `QgsGraduatedSymbolRenderer` | `Deferring to QGIS` | 309 of (109,174,214), 204 of (33,113,180), 146 of (197,219,238) |

The user's green is gone entirely — 640 pixels to 0 — replaced by a five-class
Blues quantile classification the plugin rebuilt from the row's remembered
ramp. The message bar says `restyled b (no re-tiling needed)`. No loss is
reported, and the row goes on reading "Deferring to QGIS" over a map the
plugin is once again drawing, so the control now contradicts the map in the
opposite direction to the one deferral was built to fix.

**Second, independent route.** Probe 1 read `type(layer.renderer()).__name__`
and `bridge.renderer_fill_colours` off the layer object. Probes 2–5 never ask
the renderer anything: they run `QgsMapRendererParallelJob` over the element
layer at 300×300 and tally interior pixels on a 3-pixel lattice. Both routes
agree, and the pixel route is the one that shows the harm.

**Mechanism.** `_assignments()` resolves `mode_raw == "Deferring to QGIS"` to
`mode == "Deferring to QGIS"` (it is not in `GRAD_SCHEMES`). `_signature`
carries `a["mode"]`, so the signature moves the moment
`_refresh_deferring_rows` rewrites the style cell — measured:
`_last_signatures[tid] != _signature(a)` is True with the user having touched
no plugin control. `_restyle_only` (dialog.py:5589) then finds a moved
signature and calls `bridge.seed_renderer`, whose branch chain
(bridge.py:2176-2193) has no deferring arm: `not var` / `Categorized` /
`Single colour` / **else graduated**. So the element is re-seeded as graduated.

**The asymmetry, twice over.** `_add_output_layers` grew
`carried_while_deferring` (dialog.py:~6852) and keeps the renderer;
`_restyle_only` beside it grew nothing and has no mention of deferral at all.
And in `_on_layer_style_edited`, both colour branches below re-record
`self._last_signatures[tile_id] = self._signature(refreshed)` (lines 4382,
4416, 4515, 4549); the new deferring branch above them `return`s without doing
so, which is what leaves the signature moved and arms the fast path.

**Why the new test does not see it.**
`test_a_deferring_element_keeps_its_renderer_across_a_generate` moves
`spacing_spin` before each `_generate_and_wait`, so `_geometry_signature()`
differs, `_restyle_only` returns False and the RUN-LANDING path is taken every
time. The fast path is never driven while deferring.

**Worse case, not yet measured:** a deferring element whose variable is TEXT.
The numeric correction in `_assignments` is guarded on `mode == "Graduated"`,
so it does not fire for a deferring row; `seed_renderer`'s `else` would build a
graduated renderer over a text column, which has no ranges and draws nothing.

**When it started.** e01896b, and nowhere earlier. Same probe on `defasym_parent`
(4e8288e): after the dock edit the row reads `Quant: Quantiles`, the signature
never moves, `_restyle_only` skips the element, and after Generate the renderer
is still `QgsRuleBasedRenderer` with 640 green pixels intact. The feature and
the defect arrived in the same commit.

### Observations that are NOT claimed as defects

* `_refresh_preview_colours` (dialog.py:~5548) colours a deferring element with
  `ramp_swatch_colour(a["ramp"])`, the stale ramp name, so the DESIGN PREVIEW
  shows a colour the map never paints. Lower harm than the above — the preview
  is for judging a design before committing — but it is the same family as
  `test_an_unassigned_element_previews_as_it_draws`.
* `_legibility_note`'s shared-ramp exemption keys on `a["ramp"]`, which a
  deferring row still carries. Two deferring elements remembering one ramp are
  exempted from a clash they may genuinely have. Speculative; not driven.
* The colour-editor buttons and the Classes/ramp/Reverse/class-source cells ARE
  correctly inert: `RENDERER_COLUMNS = (3, 4, 5, 7, 8)` omits only opacity
  (column 6), which is the settled decision. Nothing wrong found there.

Probes: `defasym_probe1.py` (renderer route), `defasym_probe2.py` (pixel
route), `defasym_probe3.py` (real button), `defasym_probe4.py` (pristine
`WS_ROOT`), `defasym_probe5.py` (parent-vs-head), all in the session
scratchpad. Every probe starts from `QgsProject.instance().clear()` and prints
the layer count first; every run reported `CLEAN PROJECT: layers = 0`.

