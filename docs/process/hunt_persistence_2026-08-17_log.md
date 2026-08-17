# Hunt: persistence — what survives a save, a reopen and a hand-off (2026-08-17)

Direction: PERSISTENCE of what rc7 creates. A project saved, closed
and reopened; and a GeoPackage written and opened elsewhere. Frozen
commit 1866338, probed in
/var/folders/.../weavingspace-hunt/persist/tree via tools/hunt_probe.py.

## 13:40:00  iteration 1  [logical]
TRIED:  Read the state map for the two crossings: _stamp_category_colours
        / _adopt_category_colours / _adopt_row_symbology (dialog.py
        4277-4952), _adopt_existing_group + _remember_our_table
        (8488-8620), _forget_the_last_project (4649-4752),
        _row_follows_the_renderer (5665-5839), _graduated_layer_edited
        (5841-5998), _restyle_only (7581-7770), _add_output_layers
        (9420-9660). Question: which record has two homes and only one
        of them travels.
RESULT: inconclusive, but two candidates. (a) `_row_follows_the_renderer`
        re-records `_last_signatures` and calls NEITHER
        `_stamp_category_colours` NOR `bridge.embed_style`, while its
        four sibling exits in the same handler call both. (b) The
        handler's own comparison is COLOURS ONLY --
        `expected = [colour for _lo, _hi, colour in
        self._current_graduated_classes(assignment)]` (5885) -- so an
        edit that moves BREAKS and not colours reads as "nothing
        changed" and returns at 5887 before any of those exits.
NEXT:   Measure (b) against the field report's own action: retype one
        break in the Symbology panel, then look at the .gpkg.

## 13:58:00  iteration 2  [perturbation]
TRIED:  scratchpad/p1.py -- paste a style built on a DIFFERENT field
        (v3, Blues, 4 classes) onto element a, as the field report
        describes; then Generate; then open the .gpkg cold.
RESULT: ruled out for this case. The row follows (v3 / 4 / Blues) and
        the file agrees with the project. The variable moved, so
        `_geometry_signature` moved, so Generate took the FULL re-tile
        path, where `kept_by_hand` preserves the renderer and the
        landing stamps and embeds. The follow's own missing embed is
        masked whenever the follow changes the variable.
NEXT:   Take the variable out of it: move BREAKS only.

## 14:12:00  iteration 3  [perturbation]
TRIED:  scratchpad/p2.py -- element a, Quant: Quantiles on v1, written
        to map.gpkg. Then the panel's own edit: `updateRangeUpperValue(0,
        0.5)` + `updateRangeLowerValue(1, 0.5)` on a clone, setRenderer,
        styleChanged. Then Generate, save the .qgz, clear, reopen, and
        read the file three ways.
RESULT: confirmed. Project and reopened .qgz both draw 0-0.5, 0.5-1.
        The .gpkg opened cold draws 0-0, 0-1 -- the ladder from before
        the edit. Read a third way, straight out of `layer_styles` with
        sqlite3, the stored QML holds lower/upper 0,0,1,2,3 / 0,1,2,3,3.
        Three routes, one answer.
NEXT:   Ask what heals it, and whether a recolour really does travel.

## 14:26:00  iteration 4  [perturbation]
TRIED:  scratchpad/p3.py A -- the same edit on a 6x6 region, then
        Generate, then a spacing change.
RESULT: confirmed. SEEDED 1,2,3,4,5 in both. After the retype the
        project reads 1.5,2,3,4,5 and the file 1,2,3,4,5. Generate
        changes neither (the row never moved, so `_restyle_only`
        `continue`s at 7647 and the embed at 7714 is never reached).
        Only a spacing change -- a full re-tile -- puts 1.5 in the file.
NEXT:   Is this specific to breaks, or does the rc7 embed fix cover
        less than it looks?

## 14:41:00  iteration 5  [perturbation]
TRIED:  scratchpad/p4.py -- three dock edits on identical fixtures,
        each followed by a Generate, project against file:
        R recolour class 1 to #abcdef; B retype one break;
        O set layer opacity to 0.25 in Layer Properties.
RESULT: confirmed, and it sorts cleanly.
        R  project and file AGREE (#abcdef in both) -- the four exits
           fixed on 2026-08-16 (e1ee511) do their job.
        B  project 1.5, file 1.0.
        O  project 0.25, file 1.0.
        So the rule "a dock edit reaches the file" holds for a COLOUR
        divergence and for nothing else; breaks and opacity are
        invisible to the only comparison the handler makes.
NEXT:   The other half of my brief: does the retyped break survive a
        save, a reopen and the next Generate?

## 15:02:00  iteration 6  [perturbation]
TRIED:  scratchpad/p5.py -- retype a break, save the .qgz, close the
        dialog, clear, reopen, build a fresh dialog, press Generate.
RESULT: (see below)
