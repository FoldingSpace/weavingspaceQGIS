# Hunt log — "Deferring to QGIS" across every boundary

HEAD e01896b. Shape: one-boundary. Date 2026-08-15.

AREA: deferral across a project save/reopen, a GeoPackage written and
read back, the plugin closed and reopened within one QGIS session, a
style QGIS restores from a .qgs, and a QML exported and re-imported.

THE CLAIM UNDER ATTACK (ROADMAP decision 4, hours old): deferral is
INFERRED from the renderer and NEVER stored; the maintainer's
condition is that a legacy `weavingspace_quant_style` stamp travelling
in a GeoPackage must NEVER decide the mode, and the stamp's colours
and pins are applied ONLY once the renderer has answered yes.

## Reading, before any code

* `bridge.expressible_style` (bridge.py:656) docstring: "it is asked
  from three directions that must agree: when the styling dock changes
  a layer, WHEN A PROJECT IS REOPENED, and when a layer comes back out
  of a GeoPackage."
* `_element_is_deferring` (dialog.py:5356) same claim, and names the
  GeoPackage case as the reason the stamp may never answer.
* `_refresh_deferring_rows` (dialog.py:5277) docstring: "Called
  wherever layers can have changed underneath the table — a run
  landing, A PROJECT ADOPTED, a style edited in QGIS's own panel."
* But `grep -n _refresh_deferring_rows dialog.py` gives exactly TWO
  call sites: line 4294 (`_on_layer_style_edited`, the dock edit) and
  line 6974 (end of `_add_output_layers`, a run landing). The
  "project adopted" caller does not exist. `_adopt_existing_group`
  (dialog.py:6270, called from `__init__` line 1025) does not call it.
* `_adopt_category_colours` (dialog.py:3399) applies the stamp's
  colours, its display range and its PINS with no consultation of
  `expressible_style` anywhere on the path.
* The three tests added by e01896b all live inside ONE session, after
  a Generate. None crosses a reopen. So the boundary is unguarded by
  construction, not by accident.

HYPOTHESES LOGGED (before running anything):

H1. A reopened dialog (plugin closed/reopened, or project reopened)
    shows a row that does NOT read "Deferring to QGIS" over a layer
    whose renderer no row can name, with the renderer-writing controls
    live. The row lies about the map.
H2. A legacy `weavingspace_quant_style` stamp beside a rule-based
    renderer is adopted anyway: `_quant_colours`, `_ramp_ranges` and
    `_pinned_bounds` come back, contrary to the maintainer's condition.
H3. Same across a real GeoPackage + `layer_styles` round trip in a
    fresh session.
H4. `_custom_swatch_for` asks the LAYER (`_element_is_deferring`)
    while the mode combo asks nothing, so swatch and mode can disagree
    after a reopen.

## Runs

(appended below as they happen)

### Run 1 — probe_defer_boundary.py (H1, H2, H3)

Region + output both on disk (GeoPackage), element `b` on `v3`,
Generate, then a legacy stamp planted and a rule-based renderer set in
the dock. Measured at three points:

| point | renderer | expressible | row combo | renderer cols enabled |
|---|---|---|---|---|
| same session, after dock edit | QgsRuleBasedRenderer | None | "Deferring to QGIS" | [] |
| plugin closed and reopened, same session | QgsRuleBasedRenderer | None | "Deferring to QGIS" | [] |
| project written to .qgz, cleared, read back | QgsRuleBasedRenderer | None | "Deferring to QGIS" | [] |

**H1 REFUTED.** The row reads "Deferring to QGIS" across both
reopens, the DEFERRING entry is enabled, and every renderer-writing
column is inert. The missing `_refresh_deferring_rows` call after
`_adopt_existing_group` does NOT show, because QGIS emits
`styleChanged` while restoring the layer and `_on_layer_style_edited`
reaches the refresh that way. Worth knowing: the docstring's "a
project adopted" caller is absent, but the behaviour is covered by
accident, so this is a documentation/robustness smell, not a defect.

**H2 CONFIRMED as a deviation, harm NOT driven home.** The stamp
`{"colours": {"1": "#ff0000", "2": "#00ff00"}, "field": "v3",
"pinned": {"low": 10.0}, "range": [20, 80]}` survives the .qgz and is
adopted WHOLE beside a rule-based renderer:
`_quant_colours={'v3': {'1': '#ff0000', '2': '#00ff00'}}`,
`_pinned_bounds={'v3': {'low': 10.0}}`, `_ramp_ranges=(20, 80)` —
against nothing in the same session (all three None before the
reopen). `_adopt_category_colours` (dialog.py:3399) consults
`expressible_style` nowhere, so the maintainer's condition "the
stamp's colours and pins are applied only once that has answered yes"
is unmet in the letter. It does NOT decide the MODE, which is the
part of the condition that holds. The restored state is inert while
the element defers and I did not find a route that turns it into a
wrong map, so I am NOT claiming it.

**H3.** `ogrinfo` on out.gpkg: layers `tiles_a..tiles_d, layer_styles`;
none of the four `layer_styles` QML rows carries the rule-based
renderer or the stamp, because the style is written at Generate time.

### Run 2 — probe_defer_textvar.py, and repro_defer_blank_map.py

New hypothesis, found while reading `_assignments` for run 1:

H5. The DEFERRING mode string is not "Graduated", so the text-field
    correction at dialog.py:5204 never fires for a deferring row, and
    `bridge.seed_renderer` falls into its graduated ELSE branch.

Differential, same script, same process, one step apart:

| Style ever picked by hand | row after var -> landcover | assignment mode | renderer after Generate | classes | tiles with NO symbol |
|---|---|---|---|---|---|
| no (`touched=False`) | "Categorized" | "Categorized" | QgsCategorizedSymbolRenderer | 5 | **0 of 84** |
| YES (`touched=True`) | "Deferring to QGIS" | **"Deferring to QGIS"** | QgsGraduatedSymbolRenderer | **0** | **84 of 84** |

`_follow_variable` (dialog.py:5507) is the reason: its correction is
`elif mode_combo.currentText() in self.GRAD_SCHEMES`, and DEFERRING is
not in GRAD_SCHEMES, so a touched row stays on DEFERRING while the
variable becomes text.

SECOND INDEPENDENT ROUTE: not the row, not `renderer_fill_colours` —
`renderer.originalSymbolForFeature(feature, ctx)` asked per feature.
84 of 84 return None. The map is blank.

The row afterwards reads **"Categorized"** (`_refresh_deferring_rows`
runs at the end of `_add_output_layers`, sees a graduated renderer,
and follows `_plausible_mode`), and the message bar says "...so it is
drawn by the plugin again" — a control and a notice both contradicted
by an empty map.

Clean-project check: `repro_defer_blank_map.py` asserts the project is
empty at start, runs in a fresh process with nothing before it, and
reproduces 84/84 identically.

WHEN IT STARTED: e01896b. `git log -S'DEFERRING = "Deferring to QGIS"'`
returns e01896b alone; the guard at 5204 dates from ab94d4d and was
never widened. Ran the same script against a clone at `e01896b^`
(4e8288e) in the scratchpad: QgsCategorizedSymbolRenderer, fills
`['#66c2a5', '#8da0cb', '#ffd92f', '#b3b3b3', '#dddddd']`, **0 of 84**
unpainted, and no "drawn by the plugin again" notice. Hours old.

Not covered by e01896b's three new tests: all three stay inside one
session, and the one that changes a deferring element's variable moves
`v3 -> v1`, both NUMERIC, so the graduated fall-through works and the
test passes.

### CORRECTION — run 1 was measured against a CONTAMINATED tree

The tree is shared. When I re-read `git status` after run 1 it showed
` M weavingspace_qgis/dialog.py` — another agent's UNCOMMITTED work,
adding `self._refresh_deferring_rows()` right after
`_update_dynamic_columns()` (dialog.py:3339). That is the exact fix
for H1, and my probe had imported it. My "H1 REFUTED" above was
measuring somebody else's in-flight change, not e01896b.

Re-ran the same probe against a CLEAN clone of e01896b in the
scratchpad (`scratchpad/head`, `git status` empty). **H1 CONFIRMED:**

| point (clean e01896b) | renderer | row combo | renderer cols ENABLED |
|---|---|---|---|
| same session, after dock edit | QgsRuleBasedRenderer | "Deferring to QGIS" | [] |
| plugin closed and reopened | QgsRuleBasedRenderer | **"Quant: Quantiles"** | **[3, 4, 5, 8]** |
| project .qgz written and read back | QgsRuleBasedRenderer | **"Quant: Quantiles"** | **[3, 4, 5, 8]** |

`_element_is_deferring` answers True at all three points; only the ROW
disagrees, because `_adopt_existing_group` never reaches
`_refresh_deferring_rows`. This is ROADMAP decision 8's named target
state — "a gap between the row saying Quantiles and the map still
showing dock work" — surviving one boundary. NOT CLAIMED AS MINE:
another agent has it and is fixing it in the working tree as I write.

H2 reproduces identically on the clean clone.

LESSON FOR THE NEXT HUNT, and it is the whole of what this run taught
about HOW to hunt: **in a shared tree, a probe that imports the repo
is measuring the working tree, not HEAD.** A sibling agent's
uncommitted fix turned a real finding into a confident "refuted" — a
false NEGATIVE, which no amount of second-route checking would have
caught, because both routes read the same contaminated import. Clone
HEAD into the scratchpad and point `sys.path` at the clone, from the
first probe onward. Cost here: one wrong conclusion, recovered only
because `git status` was read for an unrelated reason.

### The finding I am claiming — re-verified on the clean clone

`repro_defer_blank_map.py` with `HERE` pointed at `scratchpad/head`
(clean e01896b, empty `git status`):

    renderer   : QgsGraduatedSymbolRenderer
    classes    : 0
    fills      : []
    UNPAINTED  : 84 of 84 tiles get NO symbol
    row reads  : Categorized
    told       : "...so it is drawn by the plugin again."

Identical to the working-tree run, and untouched by the other agent's
diff (which changes neither `_assignments` nor `_follow_variable`).
Against `e01896b^` in a second clone: QgsCategorizedSymbolRenderer,
0 of 84 unpainted. The regression is e01896b's alone.
