
## 02:09:17  iteration 0 (setup)
TRIED: read brief + CLAUDE.md; worktree at scratchpad/hunt-boundary from b148baa.
RESULT: brief says hunt "one-boundary"; CLAUDE.md:990-1000 records the 2026-08-13 fix to _add_output_layers re-reading the GRADUATED hand-picks, and names a PAIR of consequences (in _signature, and re-read in _add_output_layers).
NEXT: read docs/TESTING.md + TEST-MAP.md, then check whether the OTHER consequence -- quant picks in _signature (restyle fast path) -- was fixed alongside. That is the named-pair trap.

## 02:16:40  iteration 1 (LOGICAL)
TRIED: walk hand-picked colour across each boundary in source: _signature (dialog.py:4373-4383), _run_signature (4335-4341), _add_output_layers re-read (5087-5109), stamp (2933-2954), adopt (3007-3038).
RESULT: ruled out -- all five carry BOTH category_colours and quant_colours+range_bounds. The 2026-08-13 fixes are complete for colour on those boundaries.
NEXT: switch the setting. class_source (the QML/donor template) is symbology by CLAUDE.md but is NOT re-read in _add_output_layers and is NOT stamped on the layer at all. Walk class_source across the same six boundaries.

## 02:21:05  iteration 2 (PERTURBATION: read a path beside its own sibling, ordering not content)
TRIED: compare the ORDER of operations in the two seeding paths -- _restyle_only (dialog.py:4285 stamp, then 4289 embed_style) vs _add_output_layers (5185 embed_style, THEN 5187/5192/5196 setCustomProperty + _stamp_category_colours).
RESULT: confirmed asymmetry in source. The full-run path embeds the GeoPackage style BEFORE any weavingspace_* custom property exists on the layer; the restyle path embeds after. If saveStyleToDatabase serialises <customproperties>, the exported GPKG style from a full run carries none of them, while a subsequent restyle repairs it.
NEXT: verify empirically under QGIS -- generate with a GPKG, read layer_styles.styleQML with sqlite3 directly (independent of QGIS), and look for weavingspace_category_colours / weavingspace_tile_id. Then restyle and read again.

## 02:28:30  iteration 3 (LOGICAL)
TRIED: probe1.py -- generate with GPKG output, then read layer_styles.styleQML with sqlite3 (no QGIS), for weavingspace_* custom properties.
RESULT: CONFIRMED the ordering gap. After a full run all four tables' embedded QML contain <customproperties> but NONE of weavingspace_output / _tile_id / _category_colours / _quant_style. After a restyle, tiles_a (the only re-seeded element) gains weavingspace_output and weavingspace_tile_id -- but still not the colour records, which I did not expect. Cold reopen through QGIS: layer a has output+tile_id, layer b has NOTHING.
NEXT: two threads. (1) work out why the restyle stamp did not reach the QML for the colour records -- may be my driving of the ramp, so re-probe with the assignment printed. (2) establish the HARM: does the missing weavingspace_output make the plugin offer a reopened .gpkg output as a region layer? Check _update_layer_exclusions.

## 02:35:10  iteration 4 (LOGICAL, continued)
TRIED: probe2.py -- reopen the exported .gpkg in a CLEAN project (QgsProject.clear()) and build a fresh dialog.
RESULT: CONFIRMED harm by a second route. Reopened tiles_a..d all report weavingspace_output = None; the region combo offers 'tiles_a','tiles_b','tiles_c','tiles_d' and AUTO-SELECTS tiles_a. dialog.py:1411 _update_layer_exclusions's own docstring says this must never happen. Also: probe2's restyle stamped nothing because I drove _opacity_choices directly and _assignments does not read it, so the signature never moved -- my fixture, not a defect; probe1's ramp-driven restyle is the valid evidence that custom properties DO serialise into styleQML.
NEXT: perturbation -- do the crossing TWICE (a second Generate to the same .gpkg) and see whether the second export repairs it or repeats it; and check git log -S for when embed_style moved ahead of the stamps.

## 02:43:55  iteration 5 (LOGICAL, decisive)
TRIED: probe3.py -- write one layer into two GeoPackages, setting weavingspace_output before vs after bridge.embed_style, read layer_styles.styleQML with sqlite3.
RESULT: CONFIRMED and decisive. set_then_embed -> property present in the stored QML; embed_then_set -> absent. So custom properties DO serialise, and dialog.py:5185 calling embed_style BEFORE 5187/5192/5196 is the cause. A SECOND full run does not repair it (run 2 still absent); only a restyle that actually re-seeds that element does (probe1, tiles_a). git log -S: single squashed commit, so "since the initial commit" is all the archaeology available.
NEXT: perturbation -- cross the QML-import boundary WHILE A RUN IS IN FLIGHT (choose a class source mid-tiling) and see what the landing keeps, since class_source is the one symbology item _add_output_layers does NOT re-read.

## 02:53:20  iteration 6 (PERTURBATION: cross the boundary while a run is in flight)
TRIED: probe4.py -- import a categorized QML as an element's class source DURING a tiling, through the combo's real browse/activated path (the idiom test_a_hostile_class_source_leaves_automatic_colours uses).
RESULT: CONFIRMED second defect. _class_choices and _assignments both say file:.../scheme.qml; the landed map still paints the automatic colours {crops #66c2a5, forest #8da0cb, urban #ffd92f, water #b3b3b3}, identical to the pre-run baseline. Calling _restyle_only() straight afterwards paints the file's colours {#ff0000,#00ff00,#0000ff,#ffff00}, which proves the template is readable and it is the LANDING that dropped it. dialog.py:5087-5109 re-reads category_colours and quant_colours only; class_source is not re-read.
NEXT: perturbation continues into a MATRIX -- is class_source special, or is every symbology setting changed mid-run swallowed the same way (ramp, class count, reverse, opacity)? The staggered-actions sweep's check_ramp (tests/run_tests.py:3940) only asserts output EXISTS, which is the "a map appeared" assertion the brief warns about.

## 03:03:40  iteration 7 (PERTURBATION continued: the MATRIX filled in)
TRIED: probe5.py -- ramp / class count / scheme / Reverse / opacity, each driven through its own control's own signal while a tiling is in flight, live update OFF.
RESULT: CONFIRMED, and wider than class_source. Ramp: landed reds (255,245,240)..(103,0,13), table says YlGnBu (255,255,217)..(8,29,88). Classes: landed 5 bands, table 3. Reverse: landed unreversed, table reversed. Opacity: layer 1.0, table 0.55. Only the scheme case matched (Quantiles/EqualInterval gave the same colours, so that cell is inconclusive rather than passing). So _add_output_layers re-reads the two colour records and nothing else, while the very argument written at dialog.py:5077-5086 -- the restyle path declines during a run -- applies to every one of these.
NEXT: pin the severity. live_check defaults ON, and CLAUDE.md gates live update off when a GeoPackage path is set, so re-run the ramp case (a) with live ON and no gpkg, (b) with live ON and a gpkg path, to find which users actually keep the wrong map.

## 03:12:05  iteration 8 (LOGICAL: pin the severity)
TRIED: probe6.py -- the same ramp-mid-run case three ways: live off; live on with memory output; live on with a GeoPackage path (which CLAUDE.md says gates live update off).
RESULT: CONFIRMED and sharpened. live ON + memory output -> the queued live rerun repaints and the map matches the table. live OFF -> map keeps the old ramp forever. live ON + GPKG path -> ALSO keeps the old ramp, because the gpkg gate removes the only thing that was rescuing it. live_check defaults to True, so the exposed users are exactly those writing a GeoPackage, i.e. the ones whose work goes to a file.
NEXT: last crossing -- read the exported .gpkg's embedded style with sqlite3 after a mid-run ramp change, to show the FILE carries the stale symbology too. That is a route through the artefact rather than through the project.

## 03:20:30  iteration 9 (LOGICAL: the artefact route)
TRIED: probe7.py -- ramp chosen mid-run with a GeoPackage output path; then read the file with sqlite3 and reopen tiles_a cold through OGR with loadDefaultStyle().
RESULT: CONFIRMED by a route that never touches the project. The table's ramp cell reads "YlGnBu"; the cold-reopened GeoPackage layer paints (255,245,240)...(103,0,13), the Reds the run was launched with. So the wrong symbology is not merely on screen, it is written into the artefact the user ships.
NEXT: nothing further to test. Two confirmed defects (mid-run symbology swallowed by the landing; embed_style ordering losing weavingspace_* custom properties from the exported .gpkg). Checked both against CLAUDE.md settled decisions: 805 and 989 assert the opposite of what happens, and 5077-5086's own reasoning covers the mid-run case. Writing the report.
