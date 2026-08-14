# Hunt 3 — backwards hunt, harm first

Written 03:42 UTC before reading any plugin source (structure listing only).

## The ranked harm list (anger x plausibility)

Rank | The user's words | Route I would look for
--- | --- | ---
H1 | "I printed it and the legend was a lie — the swatch says 20-40 and the map paints 20-40 a different colour." | renderer seeded from one set of breaks, legend labels formatted from another; or labels written before a reversal/ramp swap
H2 | "The classes were computed off the wrong column. The map looks plausible and is quantitatively wrong." | field name resolved by index or by label rather than by field; a renamed/duplicated field; element->field map keyed by row not tile id
H3 | "I sent the GeoPackage to a colleague and it drew something else." | style embedded at export differs from live renderer (opacity, reverse, hand-picked categorical colours, single colour)
H4 | "I spent an hour styling those layers by hand in QGIS and one Generate wiped it." | signature comparison in _add_output_layers too eager; a style-only change taking the full path
H5 | "Two elements carry the same variable and the same value has two different colours." | per-element breaks computed from per-element subsets rather than the region layer
H6 | "I reopened the project and the map is not the map I saved." | style-on-layer vs style-in-project divergence; custom properties lost
H7 | "The NULLs were drawn as if they were the lowest value." | NULL class-break workaround; unassigned/absent values falling into class 0
H8 | "I set opacity per element and the print/export ignored it." | layer opacity native vs alpha in ramp; export path re-seeds
H9 | "I changed the region layer and it kept tiling the old one." | _run_signature / _geometry_signature missing the region layer id, or a stale cached gdf
H10 | "Cancel didn't cancel — it wrote layers into my project anyway." | task cancellation not checked in `done`; _finish_run ordering
H11 | "The legend says 5 classes; I count 6 colours." | off-by-one between class count spin box and ramp sampling (int(x*N) clamp)
H12 | "My reversed ramp came out unreversed on the map (or only in the legend)." | Reverse applied at one of two seeding sites
H13 | "It overwrote the GeoPackage I already had, without asking." | export path opening with overwrite semantics
H14 | "The preview showed one thing and the map drew another." | preview colours from table dict, map from renderer seeding — two stores
H15 | "The tile-id labels name the wrong tiles." | label anchor/id join after a reindex
H16 | "Undo brought the deleted output group back / undo did nothing." | layer-tree edits outside an undo macro
H17 | "It ran ten minutes and quietly produced nothing." | worker exception swallowed, done callback with empty gdf
H18 | "Same settings, different map each run." | nondeterminism (dict ordering, random seed) in the unit build

Effort goes to H1, H2, H5, H11, H3 first: those are "a wrong map that looks right", which this project names as its characteristic failure.

## 03:42:32 iteration 0 [list written]
TRIED: wrote the ranked harm list above before reading plugin source.
RESULT: 18 harms, ranked. Worktree at scratchpad/hunt3-harm on 8aebd09.
NEXT: read docs/TESTING.md + TEST-MAP.md, then chase H1 (legend text vs painted breaks) in bridge.py.

## 03:44:20 iteration 1 [H13 overwrote my GeoPackage]
TRIED: read bridge.write_gpkg_layer + its only caller (dialog.py:5259).
RESULT: CANDIDATE. `first=first_gpkg_layer and created`, where `created` is
"the layer-tree GROUP was newly made this run". So the FIRST element written
on a run that creates a new group uses ActionOnExistingFile.CreateOrOverwriteFile
= the whole .gpkg is recreated, destroying any non-plugin tables the user kept
in that file. The only overwrite warning (dialog.py:4513) fires ONLY when
"Create as new group" is ticked AND the path equals `_last_path`. Mitigant to
check: QgsFileWidget save mode may prompt at pick time; and a returning session
with no group re-creates too.
NEXT: park as C1; chase H1/H8/H12/H14 via the asymmetry between the run-landing
seeding and `_restyle_only`.

## 03:45:29 iteration 2 [H13, sharpening]
TRIED: read _get_or_make_group (dialog.py:4825) and the stale-table drop
(dialog.py:5369-5376).
RESULT: `created` is True on the first run of any fresh dialog, and whenever
force_new fires ("Create as new group", OR the output path CHANGED). So
choosing a .gpkg that already holds the user's data and pressing Generate
recreates the file. Internal contradiction supporting this being an oversight:
the stale-table drop is careful to remove only tables THIS dialog wrote,
"never a table the user's own file already contained" -- and then the first
write of the run destroys the whole file anyway.
NEXT: reproduce end-to-end with a probe modelled on
test_a_geopackage_loses_the_elements_a_design_dropped, in my worktree copy of
tests/run_tests.py; second route = read the file with ogr, not through QGIS.

## 03:46:14 iteration 3 [H13 CONFIRMED]
TRIED: probe_users_own_geopackage_survives in the worktree copy -- clean
project, user's own .gpkg holding field_notes + site_boundaries, one Generate.
RESULT: CONFIRMED. before=['field_notes','site_boundaries']
after=['layer_styles','tiles_a','tiles_b','tiles_c','tiles_d']. Both of the
user's tables gone. Read back with OGR directly, not through QGIS.
NEXT: pin the mechanism -- reseed the user tables after run 1 and generate
again (created=False), expect survival. Then git log -S for when it started.

## 03:46:53 iteration 4 [H13 mechanism pinned + provenance]
TRIED: probe_second_run_spares_the_users_tables (created=False) and the
force_new variant; `git log -S` on both lines.
RESULT: run 2 into the same file SPARES a user table added between runs, so
the destruction is exactly the `created`/first=True write. "Create as new
group" also wipes -- and dialog.py:4513 tells the user in that very case to
"Choose a different file for this run", which destroys the other file instead.
Present since the initial commit (3bd5f52, v0.23.0).
NEXT: H1/H11 -- legend text against painted breaks; then H5 (two elements,
same variable, different breaks).

## 03:48:18 iteration 5 [H13 worst case: the source file]
TRIED: probe_output_gpkg_is_the_source_gpkg -- region layer loaded FROM
my_data.gpkg|layername=regions, that same file chosen as the output.
RESULT: CONFIRMED and much worse. after=['layer_styles','tiles_a'..'tiles_d'];
the "regions" table is gone and a fresh QgsVectorLayer on it is INVALID. The
open layer still answers featureCount()=16 from its cache, so nothing on
screen says the data has been deleted -- the user finds out on reopen.
NEXT: H5 (two elements, same variable, different breaks) -- check whether the
per-element subset classification matches vendored upstream before claiming.

## 03:48:55 iteration 6 [H5 ruled out, H11 opened]
TRIED: read vendor/weavingspace/tile_map.py::_plot_subsetted_gdf; then
probe_more_classes_than_values (3 distinct values, k=5 and k=7, Quantiles).
RESULT: H5 RULED OUT -- upstream also classifies per tile_id subset, so
per-element breaks are the reference semantics, not a defect. But the same
function shows upstream reducing k when n_values < k
(`cspec["k"] = n_values`), which the plugin does NOT do: it only collapses the
CONSTANT case. Measured: 3 distinct values, k=5 gives 5 classes with
degenerate breaks 1-1, 1-5, 5-5, 5-9, 9-9. QGIS assigns a value to the FIRST
range that contains it, so '5 - 5' and '9 - 9' should never paint -- a legend
with two swatches that appear nowhere on the map.
NEXT: measure which symbol actually paints v=5 and v=9 rather than reasoning
about QGIS's range semantics.

## 03:50:11 iterations 7-8 [H11 second route + coverage check]
TRIED (7): probe_which_symbol_paints -- ask the renderer itself, via
originalSymbolForFeature, which symbol each feature gets, rather than
reasoning about QGIS range semantics.
RESULT: legend [1-1 #ffffff, 1-5 #d8d8d8, 5-5 #979797, 5-9 #505050,
9-9 #000000]; painted {1: #ffffff, 5: #d8d8d8, 9: #505050}. Two swatches
('5 - 5', '9 - 9') never appear on the map, and the HIGHEST value draws
mid-grey while the legend's black sits beside a range nothing occupies.
TRIED (8): grep the suite and TEST-MAP for coverage of n_values < k.
RESULT: the case is deliberately EXCLUDED. run_tests.py:26770-27020 asserts
`distinct >= k` before measuring, and :34785 switches to Equal intervals
because "nine quantile breaks over four values is a fixture that cannot
exhibit nine classes at all". So nobody has asked what this map looks like.
NEXT: report. C1 (GeoPackage destruction) is the headline; H11 second.
