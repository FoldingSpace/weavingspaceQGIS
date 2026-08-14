# hunt2 — what the dialog believes about the region layer vs what the layer is

Worktree: /private/tmp/claude-501/-Users-luke-claude-scratch/9a569ef7-3f5e-4a44-8ecf-716f080f3573/scratchpad/hunt2-layer

## 03:16:22  iteration 1  [logical]
TRIED: read the two stores — `_layer_fingerprint` (dialog.py:1476, count/extent-rounded/field-NAMES/crs authid) and the signal set `_WATCHED_SIGNALS` (dialog.py:1581) driving `_data_version`. Docstring at 1484-1491 claims "Neither mechanism covers the other's blind spot".
RESULT: inconclusive on machine, but by reading: a value rewritten STRAIGHT THROUGH the provider (`dataProvider().changeAttributeValues`) changes no term of the fingerprint (count, bbox, field names, CRS all identical) and the layer emits none of the watched signals. The docstring names provider edits as exactly what the fingerprint is for.
NEXT: build the case on the machine and diff the dialog's belief before/after — if `_geometry_signature()` is unchanged, Generate takes `_restyle_only` (dialog.py:4274) and repaints the OLD joined values while saying "no re-tiling needed".

## 03:19:01  iteration 2  [perturbation: one property at a time, belief diffed]
TRIED: probe2_battery.py -- seven single-property changes to the region layer, each on a clean project, diffing layer truth / `_layer_fingerprint()` / `_data_version` / `_geometry_signature()` / the map.
RESULT: CONFIRMED two blind spots. (a) `dataProvider().changeAttributeValues` -- v1 sum 120 -> 1720 on the layer, fingerprint identical, dv 0 -> 0, geometry sig unmoved, Generate a silent no-op, map still 2305. (b) `dataProvider().changeGeometryValues` inside the bbox -- area 14.56M -> 15.94M, dv 0 -> 0, same. Edit-buffer twin of (a) is caught (dv 0 -> 18, map 2305 -> 32805). Also noticed: CRS reassigned 3857 -> 4326 moves BOTH stores yet the map is bit-identical afterwards.
NEXT: (a)+(b) are one defect -- provider-level edits, which `_layer_fingerprint`'s docstring (dialog.py:1484-1491) claims are exactly what it is for. Second route needed. And chase the CRS case separately: fingerprint moved and the map did not, which is a different mechanism.

## 03:21:25  iteration 3  [logical: second independent route]
TRIED: repro_provider_edit.py -- same provider edit, but read the result three ways: joined attribute values on the output layers, the CATEGORIES off each output layer's renderer, and whether a tiling task started at all.
RESULT: confirmed by all three. Layer holds cat='burnt' everywhere and v1 1000..1015; after Generate the tiles still carry crops/forest/urban/water and v1 0..15, the renderer still paints four categories that no longer exist in the data, `_generate` started NO task, and nothing was said (BAR_MESSAGES [], MODALS [], note ''). `git log -S "straight through the data provider"` -> ab94d4d, 2026-08-09, the commit that introduced the fingerprint.
NEXT: this stands. Keep perturbing -- in-flight provider edit, two changes at once, change-and-change-back, an uncountable layer -- to see whether the same blind spot has a worse expression or whether a second, different disagreement exists.

## 03:24:41  iteration 4  [perturbation: falsify each promise; change it back]
TRIED: probe6_promises.py -- (a) a column added in QGIS offered straight away, (b) a field retyped with ONE updateFields so the NAMES never change, (c) a column deleted then re-created under the same name, watching the hand-picked colours.
RESULT: (a) holds -- items ['---','v1','cat'] -> [...,'v2'], dv 0->1. (b) holds -- updateFields emits updatedFields so dv bumps even though the fingerprint stores names and not types; modes flip Graduated->Categorized, map re-tiles. (c) CONFIRMED an asymmetry at dialog.py:1787: losing a field pops `_category_colours[tid][field]` and NOT `_quant_colours[tid][field]`. Observed: cat picks {} after the delete, quant picks still {'v1': {0: '#ff00ff'}}, and re-selecting a NEW v1 column brings #ff00ff back onto it.
NEXT: the same line destroys categorical picks SILENTLY where `_clear_category_colours` (dialog.py:3154) reports every other loss of hand-picked colour -- CLAUDE.md says the loss "is reported, never silent". Test the rename-and-back / retype route, which is the plausible way a user meets it.

## 03:26:09  iteration 5  [logical: the sibling read beside its twin]
TRIED: repro_colour_loss.py -- element a hand-picked forest=#00ff00 (categorical), element b hand-picked class 0 = #00ff00 (graduated); then BOTH columns renamed away and straight back through `provider.renameAttributes` + `updateFields`, as Layer Properties does.
RESULT: CONFIRMED and cross-checked on the renderer, not the dict: element a's 'forest' was painted #00ff00 before and #d62728 (tab10) after; `_category_colours[a]` is now {} while `_quant_colours[b]` still holds {'v1': {0: '#00ff00'}}. The three warnings the user got all name the FIELD move; not one says colours were discarded, though `_clear_category_colours` reports exactly that loss on every other route.
NEXT: two findings stand. Spend the remaining iterations on the harder perturbations -- the edit made while a run is IN FLIGHT, two changes at once, and a layer whose feature count is unknown -- then re-run both repros on a clean project to rule out the fixture.

## 03:28:17  iteration 6  [perturbation: mid-flight, two-at-once, uncountable]
TRIED: probe7_inflight.py -- a column renamed WHILE the tiling ran; a retype AND a half-deletion applied together; and a layer answering featureCount() = -1.
RESULT: all three ruled out as defects. Mid-flight rename: the table adapts to v1_renamed, the run lands as 'a - v1' (its snapshot), the dialog knows (geometry sig moved) and the next Generate corrects it. Two-at-once: fingerprint moved, mode flipped to Categorized, map re-tiled 305 -> 158 tiles. Uncountable: `_restyle_only` refuses on `_data_is_unobservable`, so even a provider edit is followed (map 2305 -> 152500) -- the unobservable path is SAFER than the ordinary one.
NEXT: prove finding 1 on a real provider rather than the memory one, since a memory provider could be the whole story.

## 03:28:26  iteration 7  [perturbation: a real provider, clean project, fresh process]
TRIED: probe8_ogr.py -- the region layer written to a GeoPackage on disk and loaded through OGR, then the same `dataProvider().changeAttributeValues`, on an empty project in its own process.
RESULT: identical. Provider 'ogr', file values now 1000..1015, fingerprint (16,(0,0,4000,4000),('fid','v1','cat'),'EPSG:3857') unmoved, dv 0, map still 2305, nothing said. So it is not an artefact of the memory provider or of my fixture.
NEXT: date the two findings with git log -S, then write up.

## 03:28:30  iteration 8  [logical: when each started]
TRIED: `git log -S` on the fingerprint's own words and on the pop at dialog.py:1787.
RESULT: the fingerprint and its "straight through the data provider" claim both arrived in ab94d4d (2026-08-09); before it the signature held only the layer id, so provider edits were never covered -- the docstring overstated what the new mechanism bought. The categorical pop is also ab94d4d (2026-08-09); `_quant_colours` arrived later, in 0ec8ecc (2026-08-10), and the deletion path was never extended to it -- so the twin gap dates from the day the quantitative editor was written.
NEXT: report. Two findings, both with standalone repros; mid-flight, two-at-once, uncountable, column-added and CRS-change perturbations all ruled out.
