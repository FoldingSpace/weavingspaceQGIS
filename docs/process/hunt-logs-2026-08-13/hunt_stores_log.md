## 02:09:00  iteration 0 (setup)
TRIED: read the brief and CLAUDE.md; worktree at scratchpad/hunt-stores from b148baa.
RESULT: setup done. Settled decisions noted: reopened dialog does NOT restore variable assignment; ramp choice destroys hand-picks; per-element dicts keyed by tile id survive rebuilds; picks must be in _signature AND re-read in _add_output_layers (both editors).
NEXT: read docs/TESTING.md then inventory every per-element dict's writer/reader/stamp/restore, because the shape is "one fact, two stores".

## 02:20:11  iteration 1 (LOGICAL)
TRIED: inventory each of the nine dicts' writer/reader/stamp/restore, reading dialog.py:2830-3120 (rebuild, _stamp_category_colours, _adopt_category_colours, _adopt_row_symbology) and 3950-4040/4170-4383 (_assignments, _signature, _run_signature).
RESULT: inconclusive but mapped. Restore-from-layer covers _opacity_choices (layer.opacity), _ramp_choices/_class_counts/_single_colours/_quant_colours (renderer), _category_colours/_quant_colours/_ramp_ranges (stamps). NOT restored: _reverse_choices (known/deliberate), _class_choices (class SOURCE), and _category_colours has no renderer fallback the graduated twin now has (dialog.py:3087 `if not hasattr(renderer,"ranges"): return` bails before any categorized colour recovery).
NEXT: read _sync_row/_make_ramp_combo (2320-2680) to see how "Custom" is derived, because _adopt_row_symbology fills _quant_colours but never writes "Custom" into _ramp_choices — if the combo falls back to a DEFAULT ramp name while the picks say Custom, the two stores disagree and the next Generate pushes the default onto the map.

## 02:27:40  iteration 2 (LOGICAL)
TRIED: class count is held in THREE places -- the spin's displayed value, the spin's `user_k` property (dialog.py:2854/2863, the authority `_assignments` reads at 3991) and `_class_counts` (2866). Hypothesis: a rebuild while a row is on "Quant: Unclassed" writes prev["k"]==50 into user_k (2851-2854), and `_sync_row` (2494) then only CLAMPS the display to 20 without writing back.
RESULT: CONFIRMED in the dialog. probe1.py: set 7 classes -> Unclassed -> rebuild -> back to Quant: Quantiles gives shown=20, _class_counts=7, assignment k=50, scheme=Quantiles.
NEXT: second independent route -- run it and read the class count off the LAYER's renderer (len(renderer.ranges())), which is what the user's map actually shows, and confirm it is 50 while the cell reads 20.

(NOTE: the two timestamps above were mistyped ahead of the clock; from here they are `date -u` output. Iteration 2 was LOGICAL, not a perturbation -- the alternation starts properly at 4.)

## 02:14:11  iteration 3 (LOGICAL -- second route)
TRIED: confirm the k=50 leak by a different mechanism -- drive only the controls' own signals and the dialog's own debounces (_settle), then read the class count off the OUTPUT LAYER's QgsGraduatedSymbolRenderer. scratchpad/stores_probe3.py, clean project.
RESULT: CONFIRMED. "Classes cell shows 20; assignment k=50 scheme=Quantiles; _class_counts=7" and "MAP: QgsGraduatedSymbolRenderer with 50 classes". git log -S: present since the initial commit 3bd5f52 (the old form set user_k from prev["k"] the same way).
NEXT: perturbation -- stop following functions and follow ONE VALUE (the reverse flag) end to end across all four carriers (_reverse_choices, _signature, the stamp, the renderer), since the brief says Reverse is deliberately not restored and I want to know whether that omission stays cosmetic.

## 02:16:48  iteration 4 (PERTURBATION: follow the VALUE, four carriers, across a save/reopen)
TRIED: stores_probe4.py dumps all nine dicts, the ramp cell + Custom state, the renderer, the stamps and _last_signatures for a graduated element with hand picks (a) beside a categorized element fed by an imported QML class source (b), before a run / after a run / after project reopen / after a second run.
RESULT: the four lists disagree for b. After reopen the dialog holds _class_choices['b']='' and _ramp_choices['b']='Blues'->'Set2', _category_colours={} -- while the LAYER still carries the QML's colours (forest #112233, urban #778899, water #445566). The graduated twin a is fully recovered (_quant_colours from the stamp, _class_counts=5 from the renderer, row reads Custom). b's row reads a ramp NAME with custom=False. Cost: ~20 min, and it earned it -- it also showed the second run did NOT repaint b, which I did not predict.
NEXT: read _add_output_layers (dialog.py:4991-5230) to find why the second run left b's QML colours standing, because either the harm is smaller than it looks or the layer is being left stale while the table describes something else.

## 02:18:11  iteration 5 (LOGICAL -- rule out my own fixture)
TRIED: instrument the second run (stores_probe5.py) -- layer ids, _task, _last_signatures, _preserved_this_run, BAR_MESSAGES -- to find why the reopened project's Generate left b's QML colours standing.
RESULT: MY FIXTURE. No second run happened: dlg2._task is None and the bar says "The region layer was removed from the project, so there is nothing to map." make_region_layer() is a MEMORY layer and does not come back usable from a .qgz. The ADOPTION half of the probe is still sound (output layers and renderers did come back): after reopen b's ramp cell reads a library ramp name with custom=False while the layer draws the imported QML colours (#112233/#445566/#778899/#aabbcc) and _ramp_name_matching returns None for its QgsPresetSchemeColorRamp.
NEXT: redo with a GeoPackage-backed region layer so the reopened project can actually Generate, and see whether that run repaints b with Set2 -- that is the difference between "a control lies" and "the user's imported scheme is destroyed".

## 02:19:14  iteration 6 (LOGICAL -- with the fixture fixed)
TRIED: stores_probe6.py, region layer written to a GeoPackage first so the reopened project can really Generate. Sequence: categorized element b fed by an imported QML class source, run, save .qgz, clear, read, new dialog, put landcover back, Generate.
RESULT: CONFIRMED. First run and reopen both show b as [crops #aabbcc, forest #112233, urban #778899, water #445566]. The fresh dialog's row b reads ramp 'Blues' then 'Set2', custom=False, class_source=None. After Generate the layer is [crops #66c2a5, forest #8da0cb, urban #ffd92f, water #b3b3b3] -- Set2. The imported scheme is destroyed. The graduated twin a survives, because _adopt_row_symbology recovers unnamed graduated colours as positional picks (dialog.py:3106-3119) while the categorized branch returns at 3087 before reaching any colour recovery.
NEXT: perturbation -- go at it from the FILE inwards: read what the .qgz XML actually stores for element b, and render the layer to pixels before and after, so the second confirmation route is the map rather than the renderer object I have been reading all along.

## 02:20:14  iteration 7 (PERTURBATION: from the file on disk inwards)
TRIED: stores_probe7.py -- unzip the .qgz and read what it stores for element b, and RENDER the layer to pixels before and after the reopened project's Generate instead of reading renderer objects.
RESULT: mixed, and it cost about 15 min. The file half paid: the .qgz carries only weavingspace_output and weavingspace_tile_id, and no record whatever of the class-source QML path -- so nothing on disk could restore _class_choices even in principle. The pixel half was VACUOUS: "PIXELS reopened, before Generate: []" -- the memory-backed output layers come back from the .qgz with no features to draw, so the before/after pixel diff cannot see the loss.
NEXT: make the fixture realistic -- GeoPackage OUTPUT, so the reopened element layer actually holds features -- and redo the pixel before/after. That is the honest second route for "the map changed", and it also answers whether the harm needs GPKG output at all.

## 02:20:57  iteration 8 (LOGICAL -- the second route, on the map itself)
TRIED: stores_probe8.py, same sequence with GeoPackage OUTPUT so the reopened element layer holds features, then render layer b alone and count painted colours before and after the reopened project's Generate.
RESULT: CONFIRMED on the map. "reopened element b features: 78"; PIXELS before = [#112233 #445566 #778899 #aabbcc] (the imported QML scheme), PIXELS after Generate = [#66c2a5 #8da0cb #b3b3b3 #ffd92f] (Set2); "colours lost from the map: [#112233, #445566, #778899, #aabbcc]". Independent of the renderer objects I read in iterations 4-6.
NEXT: bound the claim -- check that a HAND-PICKED categorical scheme does survive (it is stamped) and that a plain named ramp survives, so the report names only the case that actually breaks; and check docs/TEST-MAP.md for existing coverage of reopen/adoption.

## 02:23:41  iteration 9 (LOGICAL -- bound the claim, three siblings side by side)
TRIED: stores_probe9/9b, three categorized elements over one save/reopen/Generate -- b on an imported class-source QML, c on a plain library ramp, d with a categorical-editor hand-pick.
RESULT: bounded exactly. c survives (ramp NAME recovered by _adopt_row_symbology), d survives and reads Custom (stamped weavingspace_category_colours), b is destroyed and never reads Custom. ALSO found, unpursued and NOT reported: retyping the same GeoPackage path on a reopened project makes force_new true (dialog.py:5050, _last_path is None on a fresh dialog) and leaves TWO groups with duplicate element layers -- outside this area, and I did not check whether it is deliberate.
NEXT: rerun the same probe without retyping the output path, which is what a user actually does, so the comparison is one layer replaced in place rather than two groups.

## 02:23:41  iteration 10 (LOGICAL -- the realistic sequence)
TRIED: stores_probe10.py, identical but the reopened dialog does NOT retype the GeoPackage path, so _add_output_layers replaces the group in place.
RESULT: CONFIRMED, single layer per element. b goes from [crops #aabbcc, forest #112233, urban #778899, water #445566] to Set2 [#66c2a5 #8da0cb #ffd92f #b3b3b3]; c and d are byte-identical before and after. Existing coverage checked: test_a_dock_recolour_outlives_a_retile_a_save_and_a_reopen covers the DOCK route (which lands in _category_colours and is stamped); nothing covers the class-source route.
NEXT: write the report. Two confirmed defects, each with a second route (renderer + rendered pixels for the class source; spin box + renderer ranges for the class count).

## 02:23:51  iteration 11 (report)
TRIED: writing up. Worktree scratchpad/hunt-stores at b148baa, unmodified; probes are scratchpad/stores_probe*.py (my earlier probe1/probe2 filenames were overwritten by another agent sharing this scratchpad -- everything reported here is in the stores_* files).
RESULT: two confirmed defects, each with a second independent route. Ruled out: _opacity_choices, _single_colours, _ramp_ranges and _quant_colours all round-trip correctly; _reverse_choices not restored is documented and I did not chase it.
NEXT: nothing; handing back.
