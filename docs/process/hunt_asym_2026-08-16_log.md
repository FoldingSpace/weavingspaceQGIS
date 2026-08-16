# Hunt: asymmetry and twins, pointed at the code written 2026-08-15

Frozen tree: 3b34364 (`tools/hunt_probe.py --prepare`).
Probes: scratchpad `probes/`, run only through the harness.

## 18:14:02  iteration 1
TRIED:  On a FRESH QGIS profile, every name the dialog can default to
        resolves to a ramp and the eight sets restored today carry
        their palettes.json colours -- bridge.py:107
        `ensure_ramps_installed`, bridge.py:66 `CATEGORICAL_RAMPS`,
        dialog.py:2447 `CAT_DEFAULT_RAMPS` against its quantitative
        twin `DEFAULT_RAMPS`.
RESULT: ruled out. Fresh profile holds 35 ramps before install and 66
        after (31 of the 36 palettes installed, 5 skipped as already
        present). All six CAT_DEFAULT_RAMPS, all twelve
        DEFAULT_RAMPS and all twelve CATEGORICAL_RAMPS resolve, are
        listed in the combo's source list, and every categorical name
        comes back as a QgsPresetSchemeColorRamp whose colours equal
        palettes.json exactly (Accent 8, Dark2 8, Paired 12, Pastel1
        9, Pastel2 8, Set1 9, Set2 8, Set3 12). Today's restore is
        sound on the profile it was written for.
NEXT:   Move to the other half of today's work, `_layers_removed`.
        The palette path is now measured on the machine state that
        hid the original defect, so the interesting asymmetry is the
        one the restore did not touch: what the region layer leaving
        does at project sizes above one.

## 18:31:10  iteration 2
TRIED:  Same hypothesis as iteration 3 below, but the fixture was
        wrong and I am recording that rather than hiding it: my probe
        built a dialog whose table had ZERO rows, so `_assignments()`
        was empty and no map was ever drawn.
RESULT: inconclusive. `_build_unit` (dialog.py:2379) raised
        ModuleNotFoundError: No module named 'weavingspace' and
        `_rebuild_unit` swallowed it into the preview's message
        panel, leaving a silent empty table. The vendored library at
        weavingspace_qgis/vendor was not on sys.path -- the plugin
        puts it there at load time and a bare probe does not.
NEXT:   Add the vendor directory to the probe prelude and re-run. The
        lesson is the brief's: suspect the driving first.

## 18:36:44  iteration 3
TRIED:  The two doors out of `_layers_removed` (dialog.py:1703 ->
        `_on_layer_changed`, dialog.py:1641) are not symmetrical
        about TELLING the user: at one layer the dialog reports the
        removal, at two or more `_on_layer_changed` finds a survivor,
        so `layer is None and self._had_a_layer` is False and nothing
        is said -- while `_adapt_to_the_layer` re-points the elements
        at the survivor's columns and `_queue_live()` redraws.
RESULT: confirmed, at project sizes 2, 3 and 4 on a fresh profile,
        commit 3b34364. Size 1 says "The region layer was removed
        from the project, so there is nothing to map. Choose another
        layer." Sizes 2/3/4 say nothing about the removal: the
        chooser silently moves from 'region 0' to 'region 1', the
        element variables move from ['v1','v2','v3','v1'] to
        ['income1','rain1','v3','income1'], and live update draws a
        fresh map -- bar reads "'WeavingSpace tiles': 312 tiles
        across 4 element layers" with no mention that the region the
        user chose has gone. Four output layers before, four after.
NEXT:   Second independent route. Messages are one witness; the map
        is another. Measure the OUTPUT layers' extents before and
        after the removal, since region 0 sits at x 0..4000 and
        region 1 at x 20000..24000 -- if the extent moves, the user's
        map has been replaced by a map of different ground with
        nothing said, which is the harm in its own terms.

## 18:52:20  iteration 4
TRIED:  Second, independent route to iteration 3 -- read the harm off
        the MAP rather than off the messages: output-layer extents
        and names before and after removing the chosen region layer,
        three layers in the project.
RESULT: confirmed. Before: 'a - v1' xmin -47, 'b - v2' -298,
        'c - v3' -121, 'd - v1' -298 (region 0 spans x 0..4000).
        After: 'a - income1' 19953, 'b - rain1' 19702, 'c - pop1'
        19879, 'd - income1' 19702 (region 1 spans x 20000..24000).
        The four output layers were replaced in place, renamed to the
        other layer's columns, and the extent moved 20 km. Bar said
        only "'WeavingSpace tiles': 312 tiles across 4 element
        layers" plus two class-count notices; the note line was empty
        before and after; no message contains "removed", "no longer",
        "gone" or "region layer".
NEXT:   Date it. Take today's connection back out at runtime (no tree
        edited) and see whether the replacement still happens.

## 19:01:05  iteration 5
TRIED:  When did the silent replacement start? Ran the same probe at
        sizes 2 and 3 with `project.layersRemoved.disconnect(
        dlg._layers_removed)` after construction, which is the
        pre-c0b91e9 state without editing any tree.
RESULT: confirmed, and it dates cleanly. Size 2 behaves identically
        connected or not (xmin -47 -> 19953 either way): the combo
        already selected the survivor, so the silent replacement at
        two layers pre-dates today. Size 3 does NOT: with the
        connection removed the outputs stay at -47/-298/-121/-298,
        nothing is said, and `_watched_layer_id` still names the
        destroyed region_0 while the chooser reads 'region 1' --
        exactly the defect c0b91e9 was written to fix. So c0b91e9
        extends the silent, unannounced replacement of a finished map
        from two-layer projects to projects of ANY size.
NEXT:   The twin question one level up. `_on_layer_style_edited`
        (dialog.py:4382) opens with a `_live_dialog()` gate whose
        comment says a RETIRED instance's connections outlive its
        retirement and "the user would be told twice".
        `_layers_removed`, written today and connected in the same
        __init__, has no such gate, and `_retire_previous_instance`
        does not disconnect it. Measure whether a retired dialog
        still runs it.

## 19:18:40  iteration 6
TRIED:  `_layers_removed` (dialog.py:1703) lacks the `_live_dialog()`
        gate that opens its twin `_on_layer_style_edited`
        (dialog.py:4382 -- "a RETIRED instance's connections outlive
        its retirement ... the user would be told twice"), and
        `_retire_previous_instance` disconnects timers and the task
        but not `layersRemoved`. So a dialog the user closed and
        reopened should still react.
RESULT: confirmed as an asymmetry, unproved as a harm. Wrapping both
        instances' handlers and removing the region layer: the calls
        run interleaved, ['retired', 'live'] x 5 -- the retired
        instance's `_layers_removed` ran every time, and with it
        `_on_layer_changed`, `_adapt_to_the_layer` and `_rebuild_unit`
        on a hidden dialog. It did NOT produce a duplicate notice or a
        second tiling in this configuration: the bar carried one line
        and retirement had already unchecked live_check. So the gate
        is missing where its twin has one; the cost I could measure is
        wasted work and a retired instance mutating its own state.
NEXT:   The obvious worse case: a dialog CLOSED rather than replaced,
        whose live_check nobody unchecked. Test whether a closed
        plugin rewrites the map when a layer is removed.

## 19:24:05  iteration 7
TRIED:  With the dialog closed (not replaced) and `layersRemoved`
        still connected, removing the region layer should re-tile a
        survivor and rewrite the map -- a closed plugin changing the
        user's project.
RESULT: ruled out. After `dlg.close()` the dialog reports
        isVisible() False while live_check is still True, and
        removing the chosen region layer left the outputs exactly as
        they were: ['a - v1', 'b - v2', 'c - v3', 'd - v1'] before
        and after, bar said NOTHING. Something downstream of
        `_queue_live` declines to draw for a dialog that is not
        showing, so the closed case is safe.
NEXT:   Stop. Re-read HEAD and report iterations 3-5 as the finding,
        6 as an observation, 1 and 7 as ground ruled out.
