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
TRIED:  scratchpad/p5.py and p6.py -- retype a break, save the .qgz,
        clear, reopen, build a fresh dialog, press Generate.
RESULT: inconclusive, and it was MY FIXTURE. `make_region_layer` is a
        MEMORY layer, so the reopened project's region held no
        features and every Generate was declined -- p7.py caught the
        modal saying so ("The selected layer has no (non-empty)
        polygon features"). Worth recording: the reopened dialog looks
        perfectly healthy, the button is enabled, and
        `_generate_and_wait` returns at once because no task was
        launched, so a probe that only reads renderers sees "the work
        survived" where in fact nothing ran.
NEXT:   Write the region to disk first, as the suite's own project
        tests do, and repeat.

## 15:31:00  iteration 7  [perturbation]
TRIED:  scratchpad/p8.py -- region on disk. ONE dock edit moves a
        BREAK and a COLOUR together, so the two mechanisms are
        compared on the same element. Then a re-tile in the same
        session, then save / clear / reopen / fresh dialog / re-tile.
RESULT: ruled out as a defect, and it is the settled decision. Same
        session, breaks 1.5 and colour #abcdef both survive a full
        re-tile. After the reopen the map still holds both. The first
        Generate after the reopen keeps #abcdef -- `_adopt_row_symbology`
        recovered it -- and puts the break back to 1.0. That is
        `_adopt_existing_group`'s docstring in as many words:
        "`_last_signatures` is deliberately left empty... the next run
        re-seeds their symbology rather than preserving hand styling it
        cannot vouch for. Within a session, hand styling still survives
        as before." Reporting it would cost the maintainer the time to
        re-explain it.
NEXT:   Firm up iteration 5's file finding into a minimal reproduction.

## 15:48:00  iteration 8  [confirmation]
TRIED:  scratchpad/repro.py -- fifty lines: generate to a .gpkg, retype
        the first break through `updateRangeUpperValue`/`LowerValue`
        exactly as QgsGraduatedSymbolRendererWidget does, press
        Generate, then compare the project layer, the file opened cold
        through QGIS, and the `layer_styles` QML read with sqlite3.
RESULT: confirmed. Project [1.5, 2, 3, 4, 5]; file [1.0, 2, 3, 4, 5];
        stored QML upper= 1,2,3,4,5. Ran on a clean project in a fresh
        process with nothing else before it.
        Site: `_graduated_layer_edited` compares COLOURS only
        (dialog.py:5885) and returns at 5887, so the four
        `bridge.embed_style` calls added by e1ee511 are never reached;
        `_restyle_only` then `continue`s at 7647 because the row never
        moved, so its own embed at 7714 is never reached either. Only a
        change that forces a full re-tile puts the break in the file.
        The colour-only comparison dates from 0ec8ecc (2026-08-10); the
        rule that a dock edit must reach the file arrived at e1ee511
        (2026-08-16) and covered colour divergences alone.
        The roadmap names this exact comparison as one of the three
        boundary crossings not yet built (ROADMAP.md:361).

## 16:20:00  iteration 9  [confirmation]
TRIED:  HEAD had moved to b4956cb while this ran -- "Four defects the
        hunts found in one afternoon's own work", which ADDS a stamp
        and an embed to `_row_follows_the_renderer` for exactly this
        harm, with a comment naming sqlite reads of
        `layer_styles.styleQML`. Re-prepared and re-ran repro.py and
        p4.py against b4956cb.
RESULT: confirmed, still live. The new block sits AFTER
        `if not moved: return False`, so it runs only when the row
        actually moves. A retyped break moves nothing the row can name
        -- same field, same scheme, same count, same ramp -- so the
        follow returns before reaching it, and the colour-only guard
        in `_graduated_layer_edited` returns before the older four.
        p4 on b4956cb: R project and file agree; B project 1.5 / file
        1.0; O project 0.25 / file 1.0.

FINDING: a break retyped in QGIS's Symbology panel, and a layer
opacity set by hand in Layer Properties, are both in the project and
in the saved .qgz and neither reaches the exported GeoPackage. No
Generate heals it; only a re-tile does. HEAD was 1866338 at
--prepare, moved to b4956cb mid-hunt, and the claim above is about
b4956cb, re-measured.

## The row for HUNT-RECORD.md

| direction | question | hypotheses | findings | lesson |
|---|---|---|---|---|
| persistence: a save, a reopen, and a GeoPackage handed on | which of rc7's new state has two homes, and does the second one travel | 9 | 1 (one instance ruled settled, one fixture error found and named) | The four `embed_style` calls that make a dock edit reach the file all sit BEHIND a comparison of colours alone, so only a recolour travels. When a fix is placed at the exits of a handler, ask what the handler's OPENING guard lets past — the guard, not the exits, decides the scope. Also: a reopened dialog whose region layer is a memory layer declines every Generate while looking healthy, which reads to a probe as "the work survived". |
