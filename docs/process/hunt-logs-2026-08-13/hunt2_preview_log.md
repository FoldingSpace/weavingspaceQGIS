# hunt2 — design preview vs generated map (asymmetry)

Worktree: /private/tmp/claude-501/-Users-luke-claude-scratch/9a569ef7-3f5e-4a44-8ecf-716f080f3573/scratchpad/hunt2-preview

## 03:14:56  iteration 1  [logical]
TRIED: read `_table_id_colours` (dialog.py:4191-4200) beside `seed_renderer` (bridge.py:1272-1286): preview tests `mode == "Single colour"` FIRST and ignores `var`; the map tests `if not var` FIRST and paints NO_DATA_FILL. An unassigned row defaults to mode "Single colour" (`_plausible_mode`, dialog.py:4076) and `_sync_row` (dialog.py:2544-2555) gives it a colour button pre-filled with the row's ramp swatch.
RESULT: inconclusive on paper — reads as a real divergence (preview = e.g. a mid-Reds, map = #dddddd) and the existing differential test skips exactly this case (`ramp is None: continue`, run_tests.py:29624).
NEXT: confirm by data — read `_table_id_colours()` for an unassigned element and the seeded renderer's fill off the output layer after a real run.

## 03:16:20  iteration 2  [perturbation: compare by DATA + pixels]
TRIED: repro_unassigned_colour.py — dialog on synthetic region, element "b" set to "---", generate, then read (a) `_table_id_colours()`, (b) the pixels `TilePreview` paints after show(), (c) `renderer_fill_colours` on the output layer.
RESULT: CONFIRMED. b: preview dict #ff3c8bc2, preview pixels #3c8bc2 (1317 sampled px, second commonest colour on the widget), map renderer single symbol (221,221,221)=#dddddd. Present since the initial commit (`git log -S` on both branches -> 3bd5f52).
NEXT: check the other direction of the same pair — does the preview also lie about a Single colour row that HAS a variable, and about ramp Reverse / display range? Then move to "which elements exist".

## 03:18:09  iteration 3  [perturbation: a design the region cannot carry]
TRIED: repro_missing_element.py — 2000x2000 region, "stripes 26", spacings 500/1500/3000, clip on and off; compare `_tile_ids()` (table + preview) against `_element_layer_ids` and against what the user was told.
RESULT: CONFIRMED at spacing 3000 (both clip settings): design/preview carry a..z, the map produces 18 layers, elements j..q have no layer at all. Only message: success "36 tiles across 18 element layers". Nothing names the eight elements that vanished; their table rows still show a variable each.
NEXT: verify the missing elements by a second route (the layer-tree group's own children, not `_element_layer_ids`), then check the family of preview-swatch lies (Reverse, Ramp Display Range, hand-picked colours).

## 03:20:57  iteration 4  [perturbation: compare SHAPE by data, not pixels]
TRIED: repro_shape_compare.py — modal map tile area per element against the area of the same element's tile in `preview._polys` (shells=0), ragged edges, for laves 3.3.4.3.4 (no inset / 20% tile inset / 20% prototile inset) and hex-slice 4 (10% tile inset). Also verified the layer-tree group agrees with `_element_layer_ids` on iteration 3's missing elements.
RESULT: ruled out for shape/insetting — ratio 1.0000 on every element in every case, including where the prototile inset makes a and c differ from b and d (43530.96 vs 37502.87, matched exactly on both sides). Iteration 3's second route agrees: the group holds the same 18 elements.
NEXT: drive ONE Data & colours control at a time (ramp, Reverse, opacity, single colour, Categorized + hand-picks, ramp display range) and read the preview colour beside the map's actual fills after each.

## 03:22:54  iteration 5  [perturbation: one control at a time, both views]
TRIED: repro_control_matrix.py — element a, each control driven through its own signal, preview colour vs `renderer_fill_colours` after each.
RESULT: ramp, opacity (0.3 layer + floored preview alpha) and Single colour agree. Three do not: Reverse leaves the preview identical (map colour SET unchanged, so arguably harmless); ramp display range 0-20% gives map fills #08306b..#1764ab while the preview still shows #3c8bc2; hand-picking all four categories to #111111-#444444 leaves the preview showing #e377c2, a colour the map now paints nowhere. The table's own ramp cell does show a Custom swatch in these states (`_custom_swatch_cache`), so the dialog knows the true colours and the preview does not use them.
NEXT: read the restyle route beside the run-landing route (the other twin pair that paints the map) and compare what each writes onto the layer.

## 03:24:28  iteration 6  [logical + data: what the preview cannot show]
TRIED: repro_icons_preview.py — "Draw as icons" changes what the map IS (one unit per region polygon), and `_build_unit` ignores the switch, so the preview cannot show it; measured both sides.
RESULT: ruled out as a shape defect. icons=False 312 tiles / icons=True 64 tiles, and per-element modal tile area is identical to the preview's in both (ratio 1.0000). Also read `_restyle_only` (dialog.py:4300-4335) beside `_add_output_layers`: restyle omits the >60-category cardinality warning and the legibility check, but the latter is a settled decision.
NEXT: repeat the shape differential on a WEAVE with aspect != 1, where `_build_unit` takes its own weave-only inset branch (dialog.py:2098-2102).

## 03:26:33  iteration 7  [perturbation: the other half of the catalogue]
TRIED: repro_weave_shape.py — same shape differential on weaves (plain a|b, twill a|b, plain ab|cd) with aspect 0.5-1.0 and the weave-only inset branch.
RESULT: first run showed ratio 0.5000 everywhere and I nearly believed it: MY FIXTURE. A weave unit carries several cells per strand and I was summing them against one map tile. Per-polygon, every case matches exactly, including twill's two distinct tile areas (21600.0 and 381600.0) and the aspect-scaled inset. Ruled out.
NEXT: run the suite's own two differential tests here, to be sure they pass over the three disagreements found (i.e. that these are uncovered, not something I have broken in this worktree).

## 03:27:20  iteration 8  [logical: is this ground already covered?]
TRIED: ran the suite's own differentials in this worktree — test_the_preview_agrees_with_the_map_it_predicts, test_the_row_agrees_with_the_map_about_what_it_shows, test_null_features_draw_as_no_data.
RESULT: all three PASS. The first skips single-symbol renderers (`ramp is None: continue`) and compares against the renderer's SOURCE ramp, so neither the unassigned element nor the display-range/hand-pick states can fail it. The disagreements found are uncovered, and nothing in this worktree is broken.
NEXT: how easily is an element lost? sweep spacing against a 4 km region for a tiling and a weave.

## 03:29:03  iteration 9  [perturbation: sweep one control, watch both views]
TRIED: repro_missing_sweep.py — 4 km region, hex-slice 12 / square-slice 9 / cube weave abc|def|ghi, spacing 500..4000.
RESULT: tilings keep every element at every spacing. cube weave abc|def|ghi loses b, e and h at spacing 3000 and 4000 (9 elements, 6 layers). There the user IS warned, but about AREAS ("8 of 16 areas received no tiles"), never about the three elements that vanished. In iteration 3's stripes-26 case no warning fired at all, because every area did get a tile.
NEXT: sharpen finding 1 — pick a Single colour by hand on an unassigned element (the deliberate act, not the default) and check the map again; note the layer name as a mitigating signal.

## 03:29:51  iteration 10  [logical: sharpen the harm, find the mitigation]
TRIED: repro_unassigned_colour.py extended — pick #00cc66 by hand on unassigned element b through the colour button's own colorChanged signal, then generate.
RESULT: CONFIRMED and sharper. Preview dict #ff00cc66, preview paints #00cc66 over 1320 sampled pixels, map renderer single symbol (221,221,221). Mitigation worth reporting: the output layer is NAMED "b (no data)", so the layer panel does say so even though the preview does not.
NEXT: report. Three observations (unassigned colour, elements absent from the map, preview swatch ignoring display range and hand-picks); ruled out: shape and insetting on tilings and weaves, icon mode, and one 0.5 ratio that was my own summing error.
