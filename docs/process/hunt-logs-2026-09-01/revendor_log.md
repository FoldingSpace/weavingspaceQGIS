# hunt: revendor  (round 6, commit b9551f5)

Direction: what the plugin reads from the vendored library BESIDE the ground
geometry, now that the vendor moved bf1bbbf -> 6190917. Shape hunted:
unreachable -- a branch whose precondition upstream no longer produces.

## 07:42:37  iteration 0  [logical]
TRIED:  orientation only -- read BRIEF.txt, CLAUDE.md settled decisions and the
        re-vendor lessons (CLAUDE.md:5664, :5747, :3837).
RESULT: inconclusive (no hypothesis yet). Confirmed the known ground: 588/590
        designs identical, square-colouring 6 and 8 shifted origin ~34 units;
        colourspace gate scores plugin against the SAME vendor so it is blind
        here.
NEXT:   enumerate every attribute the plugin reads off library objects
        (Topology, Tileable, TileUnit) and find which reads are guarded by a
        branch. That list is the search space.
## 07:44:42  iteration 1  [logical]
TRIED:  enumerate the whole seam -- every library attribute the plugin reads --
        and diff the vendor across the re-vendor commit d071467 (the old vendor
        is in this repo's own history, so both ends are here without upstream).
RESULT: inconclusive. The seam is narrow: topology.edges.values(),
        topology.points.values(), topology.tiles, topology.n_tiles,
        topology.dual_tiles.values(), get_dual_tiles(), transform_geometry,
        generate_dual, tiling_utils.get_clean_polygon, catalog.make_unit.
        The refactor is large: Tile.corners went list[Vertex] -> list[int],
        v.tiles -> list[int], e.left/right_tile -> int, tile.edges -> list[ID],
        Vertex/Edge/Tile gained a back-reference to the Topology,
        `unique_tile_shapes` deleted, `n_tiles: int = 0` class default DELETED,
        pickle -> copy.deepcopy in transform_geometry, and `for p in
        reversed(self.points.values())` -> forward order in
        _initialise_points_into_tiles. The plugin reads NONE of the renamed
        internals directly, so no AttributeError seam.
NEXT:   the unreachable candidates are now named: (a) topology_edits.py:383
        `if current is None`, (b) _make_drawable's whole repair now that
        upstream fixed zigzag vertex doubling at b3650e0, (c) _upstream_clean's
        `if clean is None` fallback. Read the rest of the diff, then measure (b)
        -- it is the one with a user-visible consequence if the repair now
        never runs OR still runs.
## 07:45:31  iteration 2  [logical]
TRIED:  read the whole topology.py diff (d071467^..d071467) and topology_edits.py
        top to bottom, looking for a plugin branch whose precondition upstream
        retired. Best unreachable candidates: topology_edits.py:383
        `if current is None` (current is never None once apply() is entered),
        and _make_drawable's repair (topology_edits.py:686) now that upstream
        b3650e0 fixed zigzag vertex doubling at source.
RESULT: inconclusive as DEFECTS -- neither completes "a user loses ___".
        But the diff named a much larger risk the differential cannot see:
        _initialise_points_into_tiles now scans `self.points.values()` FORWARD
        where it scanned `reversed(...)` before (topology.py:201 vs old :208),
        which changes WHICH existing vertex a corner snaps to and therefore the
        vertex ID order -- and transitivity-class labels are assigned by class
        INDEX (topology.py:688 `v.label = LABELS[v.transitivity_class]`,
        :738 `e.label = labels[e.transitivity_class]`).
        The plugin SHELVES edits by (family, element count) and replays them by
        class LABEL (topology_edits.py:1-30, ruling 4). Label stability was
        measured across rebuilds and across spacings -- NEVER across library
        versions, which is the one thing a re-vendor moves.
NEXT:   measure it. Two checkouts, every catalogue design that carries a
        topology: does it still BUILD, are the class strings the same, and does
        class 'a' still cover the same edges? A moved label silently replays a
        saved edit onto a different edge -- the flagship "wrong map that looks
        right". Read tools/hunt_probe.py first; the harness is mandatory.
## 07:49:06  iteration 3  [perturbation]
TRIED:  two checkouts (same plugin code b9551f5, vendor swapped to d071467^ in
        one arm), 28 catalogue designs through catalog.make_unit +
        topology_edits.build: does Topology still BUILD, are the class strings
        the same, and does each edge/vertex keep its label against its own
        ground? Probe:
        scratchpad/labels_across_the_revendor.py, run through the harness.
RESULT: ruled out -- labels did NOT move. All 28 designs build in BOTH arms
        (Topology refuses nothing new), every `classes()` string is identical,
        and of every edge/vertex whose ground is shared between the arms, ZERO
        are relabelled. So ruling 4's premise survives the re-vendor and a
        shelved edit list replays onto the same class.
        THREE DESIGNS' GROUND MOVED IN THE TOPOLOGY, which is more than the
        committed differential reports: square-colouring 6 (0 of 102 edges
        shared -- the known ~34-unit origin shift) but ALSO square-colouring 2
        (34 of 45 edges shared) and square-colouring 3 (52 of 54). The
        committed differential compares tile count, ids, area and bounds only,
        so a change that keeps all four is invisible to it.
NEXT:   two things. (1) normalise out the translation and re-ask the relabel
        question for square-colouring 2, 3 and 6, since with 0 shared keys that
        check was vacuous. (2) the harm that matters is not the label but the
        MAP: replay each of the five manipulations on both arms and compare the
        tileable that gets drawn. A saved edit list that draws a different map
        after an upgrade is the flagship failure here.
## 07:55:26  iteration 4  [perturbation]
TRIED:  replay all five manipulations through topology_edits.apply (the landing's
        own door) on 13 designs in both arms and compare the DRAWN tileable,
        the refusals, the marks, classes_after and the dual.
        Probe: scratchpad/edits_across_the_revendor.py.
RESULT: confirmed-as-equivalence for four of five. push_vertex, nudge_vertex,
        rotate_edge and scale_edge draw byte-identical tiles, identical
        refusals and identical marks on every design whose GROUND did not
        already move. zigzag_edge moves on 11 of 13 designs -- that is upstream
        b3650e0 (it no longer doubles the tiling vertices), and it is an
        IMPROVEMENT: the dual it produces grows from 2->4, 1->3, 3->6, 0->6
        tiles, i.e. the old dual was under-counted by the doubled vertices.
        No refusal text changed anywhere.
        The one thing that did NOT come out clean: square-colouring 2 and 3
        show topology ground moving between the arms (34/45 and 52/54 edges
        shared) even after normalising for translation, and the committed
        differential tools/probes/the_re_vendor_moved_no_map.py reports ONLY
        square-colouring 6 and 8 as moved.
NEXT:   settle that. Compare the TILES themselves as WKT (not count/ids/area/
        bounds, which is all the committed instrument compares) across the whole
        square-colouring family. If a design's tiles changed shape while
        keeping all four summary statistics, the instrument that was built to
        answer "did the re-vendor move a map" answered wrongly.
## 07:58:04  iteration 5  [perturbation]
TRIED:  re-run the re-vendor differential over ALL 1168 catalogue entries but
        fingerprint each design by its TILE GEOMETRY (each tile translated to
        the unit's own origin, shapely .normalize(), WKT) instead of by count/
        ids/area/bounds, which is all
        tools/probes/the_re_vendor_moved_no_map.py:78-88 compares.
        Probe: scratchpad/did_any_tile_change_shape.py.
RESULT: confirmed -- FIVE designs differ, not two. Beyond the known
        `square-colouring 6` and `8`, the designs `square-colouring 2`, `3` and
        `7` come back RESHAPED with 0 of 2, 0 of 3 and 0 of 7 tile shapes kept,
        while their tile count, their distinct ids, their total area AND their
        bounds are all identical to four decimals -- which is exactly the set of
        four statistics the committed instrument compares, so it reports them
        unchanged. 6 and 8 also change the SHAPE of their bounds
        (-306,-306,306,306 -> -272,-340,340,272), i.e. they are not a pure
        translation either, which the committed report describes as "shifted
        origin by about 34 map units ... same tiles, same ids, same area".
NEXT:   this could still be floating-point noise in the WKT rather than a real
        reshape. Quantify it the way the plugin itself does: symmetric
        difference over tile area, against topology_edits._NOTHING_MOVED (1e-7).
        If it is above that, three designs changed shape under every user and
        both the record and the instrument say they did not.
## 08:00:22  iteration 6  [perturbation]
TRIED:  quantify iteration 5's "RESHAPED" designs with the plugin's own
        instrument -- symmetric difference over tile area, tile-for-tile by
        tile_id, against topology_edits._NOTHING_MOVED = 1e-7.
        Probe: scratchpad/how_far_did_square_colourings_move.py.
RESULT: ruled out -- MY OWN FIXTURE. square-colouring 2, 3 and 7 differ by
        2.4e-16, 2.0e-16 and 9.0e-16 of a tile's area: WKT text inequality at
        the last bit, not a reshape. Only 6 (6.1e-1) and 8 (4.7e-1) really
        moved, which is exactly what the committed differential reports. 588 of
        590 stands and the instrument is sound; the fault was comparing WKT
        strings where the project's own rule is to compare shapes.
NEXT:   back to the unreachable shape, with a lead the last two iterations
        handed me. topology_edits._make_drawable (topology_edits.py:686) skips
        its repair when `_tiles_lay_out(unit)` is already True, and ONLY the
        repair path calls `_shallow_copy_with_tiles`, whose docstring
        (topology_edits.py:860) says it rebuilds the regularised prototile --
        "the step `transform_geometry` does not take and which upstream's own
        notebook takes by hand whenever it builds a unit from topology output".
        Upstream b3650e0 removed the doubled zigzag vertices, which were the
        reason zigzag output failed `_tiles_lay_out`. So the branch that
        rebuilds the prototile may now be unreachable for zigzag -- the
        precondition retired at source. Measure: (a) does `_tiles_lay_out`
        answer True for zigzag output in the new arm and False in the old, and
        (b) does the un-rebuilt regularised prototile differ from a rebuilt one,
        and does the TILING differ.
## 08:02:17  iteration 7  [perturbation]
TRIED:  is _make_drawable's repair branch (topology_edits.py:695-731) still
        reachable for zigzag after upstream b3650e0, and does the regularised
        prototile it alone rebuilds matter?
        Probe: scratchpad/is_the_prototile_rebuild_still_reachable.py.
RESULT: confirmed, HALF of it. The branch IS newly unreachable for zigzag: on
        archimedean 3.6.3.6, archimedean 4.8.8, hex-slice 4, hex-slice 6 and
        laves 3.3.4.3.4, `_tiles_lay_out` goes false -> TRUE and `repaired`
        goes true -> FALSE across the re-vendor, so the raw transform output is
        accepted and `_shallow_copy_with_tiles` -- the ONLY caller of
        `_setup_regularised_prototile(override=True)` anywhere in the plugin --
        never runs. The prototile the plugin now ships for a zigzagged unit
        differs from a rebuilt one by 0.08 to 0.18 of its area, where before
        the re-vendor it differed by 0.0.
        THE HARM IS NOT ESTABLISHED YET: `get_local_patch(r=1)` is IDENTICAL
        (symmetric difference 0.0, same tile count) between the shipped and the
        rebuilt unit in every case. AND THE STALENESS IS NOT NEW IN GENERAL --
        push_vertex and rotate_edge already ship a prototile 0.10 to 0.26 wrong
        in BOTH arms, because transform_geometry's own call at topology.py:1313
        omits `override` and tile_unit.py:187 makes it a no-op when the
        prototile is already set. So four manipulations were always stale; the
        re-vendor made the fifth join them.
NEXT:   the patch is not the map. `tile_map.py:498` feeds
        `tileable.regularised_prototile` into the tiled map, so measure the
        thing a user actually sees: tile a region with the shipped unit and
        with the rebuilt one and compare. If those differ, there is a live
        defect at the seam; if they do not, the prototile is inert here and
        the whole line is an equivalence to record.
## 08:03:43  iteration 8  [perturbation]
TRIED:  does the stale regularised prototile the plugin now ships for a
        zigzagged unit change the MAP? Tiled a 3000x3000 region through
        `Tiling.get_tiled_map` twice per case -- once with the unit
        topology_edits.apply hands back, once with the same unit after
        `_setup_regularised_prototile(override=True)` -- on three designs and
        three manipulations. Probe:
        scratchpad/does_the_stale_prototile_move_the_map.py.
RESULT: ruled out -- 9 of 9 SAME MAP. Identical tile counts (85/85, 180/180,
        194/194), identical total areas to four decimals, symmetric difference
        exactly 0.0. `tile_map.py:498` does read the regularised prototile, but
        for these units the stale one and the rebuilt one produce the same
        tiling, so the branch that stopped being reachable was not paying for
        anything. No harm; the unreachability is free.
NEXT:   settle unreachable vs merely RARE, which is the distinction the brief
        insists on. Sweep every manipulation over the EXTREMES of its control's
        domain (not just the defaults) across every design that carries a
        topology, and count how often `_tiles_lay_out` refuses the raw output.
        If it never refuses, then _make_drawable's repair, _upstream_clean,
        _without_repeats and _largest_part are all dead in the shipping plugin
        and that is the finding; if it refuses anywhere, the branch is rare and
        I have nothing.
## 08:15:05  iteration 9  [perturbation]
TRIED:  unreachable or merely rare? Swept every manipulation over the EXTREMES
        of its own spin boxes (low/default/high crossed, both a single class and
        the whole class string) against every catalogue design that carries a
        topology, counting how often `_tiles_lay_out` refuses the raw
        transform output -- the only door into _make_drawable's repair and
        therefore into _upstream_clean, _without_repeats and _largest_part.
        Probe: scratchpad/is_the_repair_dead_or_merely_rare.py.
RESULT: ruled out -- MERELY RARE, and the sweep found it inside ten minutes.
        `laves 3.3.3.4.4` scale_edge at sf=3.0 (the box's own maximum) and
        zigzag_edge at n=1, h=1.0, smoothness=0, and `square-colouring 5`
        zigzag at the same corner, all fail `_tiles_lay_out` and are then
        successfully mended (repaired=True). So the repair still earns its
        place; it is only the DEFAULT zigzag that stopped needing it. Nothing
        to retire, and no defect in the branch.
NEXT:   stop and report. HEAD re-checked with `hunt_probe.py --status`: still
        b9551f5, it did not move under me. No defect found at this seam; what I
        have is five measured equivalences and one measured improvement.
