
## 02:09:03  iteration 0 (setup)
TRIED: got brief (--shape write-only), created worktree hunt-writeonly at b148baa, read CLAUDE.md in full.
RESULT: settled decisions noted; the 2026-08-13 quant-editor/`weavingspace_quant_style` fix is the excluded pattern (CLAUDE.md:990-1000).
NEXT: read docs/TESTING.md + TEST-MAP.md, then inventory every custom-property/stamp key writer.

## 02:11:26  iteration 1 (LOGICAL)
TRIED: grep every writer/reader of each layer custom property in plugin source (dialog.py:5187,5196,5233,5234,2935,2948 write; 1419,4732,4740,3007,3020 read).
RESULT: ruled out at key level -- all five keys (weavingspace_output/tile_id/outline/category_colours/quant_style) have a real reader, and every JSON sub-key (field/colours/range) is read back in _adopt_category_colours.
NEXT: move down a level -- the GeoPackage side of it. embed_style(dialog.py:5185) runs BEFORE the three setCustomProperty calls at 5187/5196, so the style stored in layer_styles cannot contain them; check whether QGIS style XML carries customproperties at all, and who reads the .gpkg back.

## 02:12:40  iteration 2 (PERTURBATION: open the FILE, inventory it, then ask who reads each part)
TRIED: tools/probe_gpkg.py -- drive dialog to a .gpkg, then read the file with sqlite3 (independent of GDAL/QGIS) and dump tables, layer_styles and columns.
RESULT: confirmed. 4 element tables, rtree indexes, layer_styles with 4 default styles (~24.5kB QML each). Each stored QML HAS a <customproperties> block but it is EMPTY of weavingspace keys -- because bridge.embed_style() is called at dialog.py:5185, BEFORE setCustomProperty at 5187/5196 and _stamp_category_colours at 5191. Column list also shows weavingspace_fid written into every table.
NEXT: find whether that costs anything. The sharp version is: does QGIS's own loadDefaultStyle (which the ogr layer constructor runs) then OVERWRITE a layer's live custom properties with the empty stored set -- on project reload, or on a second Generate into the same file? If it does, the stamps are erased by the plugin's own file.

## 02:16:01  iteration 3 (LOGICAL)
TRIED: follow the empty-customproperties finding to a harm, and separately audit every key _assignments() produces (17 keys) for a consumer.
RESULT: mixed. probe_roundtrip.py: a .qgz save+reload KEEPS weavingspace_output/tile_id (B), so the .qgz is the carrier and the empty stamp in layer_styles costs a colleague only the tags, not the map -- weak harm, parking it. All 17 assignment keys have a real reader (mode_raw, class_choice, style_touched each have exactly one, at dialog.py:2815/2911/2816).
NEXT: chase the style SIDE-TABLE instead of the stamps. bridge.embed_style is called again on every restyle (dialog.py:4286) with useAsDefault=True; if GDAL/QGIS appends rather than replaces, the .gpkg a user sends could still open on the FIRST style. Measure layer_styles rows before/after a restyle and reopen the file fresh.

## 02:16:53  iteration 4 (LOGICAL)
TRIED: tools/probe_restyle.py -- generate to .gpkg, move row 0 from Reds to Blues via ramp.activated (the user path), Generate (restyle fast path), then read layer_styles with sqlite3 and reopen the table in an empty project.
RESULT: ruled out. layer_styles stays 4 rows, ids 1-4, useAsDefault=1 throughout; the row is UPDATED in place. Map ['#f7fbff','#c5dbee','#6daed6','#2171b4'] and the reopened file agree exactly. The side-table has a reader and stays current.
NEXT: even iteration, so perturb the method -- inventory what the plugin writes into the OUTPUT ATTRIBUTE TABLE and its layer names (prototile_id, weavingspace_fid, tile_id) and ask who reads each; and probe the future-version stamp (extra/short keys).

## 02:18:55  iteration 5 (PERTURBATION: written but not written CONSISTENTLY -- one path stamps, its twin does not)
TRIED: compare the four exits of the styling-dock watcher. ADOPT branches call _stamp_category_colours(layer, refreshed) at dialog.py:3616 (categorized) and 3722 (graduated); FOLLOW branches (clean classify from a named ramp) at 3579-3600 and 3686-3703 clear the dialog's picks via _clear_category_colours/_clear_quant_customization and set _last_signatures, but NEVER re-stamp.
RESULT: confirmed by reading; _clear_category_colours (3121) and _clear_quant_customization (3207) touch only dialog dicts, not the layer property. And because the follow branch writes _last_signatures, _restyle_only skips that element forever, so the stale stamp is never healed.
NEXT: build the reproduction. Predicted harm: picks the plugin SAID it discarded come back on project reload via _adopt_category_colours and re-impose themselves over the ramp. Note this branch was UNREACHABLE until today's sourceColorRamp fix, which is why it has never been exercised.

## 02:22:04  iteration 6 (LOGICAL: build the reproduction)
TRIED: tools/probe_stale_stamp.py -- adopt a dock recolour (stamps crops->#123456), then hand the dock the CLEAN Set2 renderer back (follow branch), save .qgz, reopen cold, new dialog, Generate.
RESULT: partly confirmed. Steps 1-5 all hold: dialog record empties to {}, ramp cell stops reading Custom, but the layer stamp STILL reads {"colours":{"crops":"#123456"},"field":"landcover"} and that text is in the saved .qgz (read out of the zip, an independent route). A fresh dialog adopts it: _category_colours == {'b':{'landcover':{'crops':'#123456'}}} and its ramp cell reads Set2 + Custom=True. Step 6 did NOT follow: after Generate the map paints crops #66c2a5 (plain Set2) although the assignment handed to the run carries category_colours={'crops':'#123456'} and _last_signatures is {}.
NEXT: step 6 is now its own question -- an override that _assignments() reports and the map does not wear. Instrument bridge.make_categorized_renderer to print the overrides it is actually given, because either the re-read in _add_output_layers drops them or something restyles after seeding.

## 02:24:16  iteration 7 (LOGICAL: kill the fixture doubt, then finish the repro)
TRIED: instrument bridge.seed_renderer/make_categorized_renderer; step 6's silence was MY FIXTURE -- rt.make_region_layer() is a memory layer, which keeps no features across a .qgz reload, so the second Generate was declined and proved nothing. Re-ran with the region written to its own .gpkg first.
RESULT: CONFIRMED end to end. seed_renderer b Categorized {'crops': '#123456'}; the regenerated map paints crops #123456 over Set2, and the new signature carries (('crops','#123456'),). Two independent routes: the value read out of the saved .qgz with a plain zip/XML read, and the colour read off the renderer rather than off the dialog.
NEXT: date it and check the twin -- the GRADUATED follow branch (dialog.py:3686-3703) has the identical hole, and unlike the categorized one it has been reachable all along, so the bug predates today's sourceColorRamp fix.

## 02:24:36  iteration 8 (LOGICAL: when did it start)
TRIED: git log -S on both follow branches and on the adopt branches' stamp call.
RESULT: both follow branches and both stamp calls arrived together in 0ec8ecc (2026-08-10) -- the stamp was added to the ADOPT exits only. So the graduated half has been live since 2026-08-10; the categorized half became reachable only today (c8c6c28, the sourceColorRamp fix), which is why it has never been seen.
NEXT: perturbation -- put the missing stamp call in MY copy and run the tests that cover these branches. If they pass unchanged, nothing in the suite notices either the bug or the fix, which is the other half of the finding.

## 02:25:38  iteration 9 (PERTURBATION: change the stamp in my copy and see whether anything notices)
TRIED: added the one missing line -- self._stamp_category_colours(layer, refreshed) -- to BOTH follow branches (dialog.py:3598 and 3703) and ran the eight tests that cover these paths.
RESULT: 8 passed, 0 failed, and the reproduction is cured (stamp None, fresh dialog adopts None, map stays #66c2a5). So nothing in the suite pins the buggy behaviour and nothing objects to the fix; the branch is covered for the dialog's DICT and the ramp cell, never for the layer stamp. dialog.py reverted to HEAD.
NEXT: confirm the graduated twin empirically rather than by reading, since that half has been live since 2026-08-10, then write the report.

## 02:26:34  iteration 10 (LOGICAL: the older twin, empirically)
TRIED: tools/probe_stale_quant.py -- the same sequence on a GRADUATED element (positional pick via updateRangeSymbol, then the clean Reds renderer handed back).
RESULT: confirmed, identically. weavingspace_quant_style stays {"colours":{"1":"#123456"},"field":...,"range":[0,100]} on the layer and in the .qgz; a fresh dialog adopts {'1': '#123456'}, its ramp cell reads Reds + Custom, and the regenerated map paints class 1 #123456 instead of Reds' #fcbba2. This half has been live since 2026-08-10.
NEXT: write the report. Two confirmed, one defect in two places; parked as not-a-defect: embed_style running before the stamps, which leaves the .gpkg's layer_styles customproperties empty (costs a colleague the tags, not the map).
