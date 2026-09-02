# hunt `harm` -- round 6 -- worktree <a local path> scratch/weavingspace-qgis-plugin/dev/hunts/round6/harm @ b9551f5

## 07:42:42  iteration 0  [logical]
TRIED:  Before opening ANY source file: rank twenty things a person would be
        furious to LOSE while using this plugin today, around the Topology
        tab's editing, Save, Load, the change list, a shared GeoPackage, a
        saved project, and a demo of several datasets in a row.

        THE RANKED LIST (1 = most furious):

         1. A tile unit I spent an hour hand-editing in the Topology tab is
            silently replaced by a different/default one -- my edits are gone
            and nothing said so.
         2. Save writes a file that Load cannot read back, or reads back as a
            DIFFERENT tiling -- so the saved design is dead on disk.
         3. Save/export into a SHARED GeoPackage destroys someone else's
            layer already in that .gpkg (overwrite of the whole container
            rather than one table).
         4. A saved QGIS project reopens with the woven/tiled layers pointing
            at nothing, or at the WRONG table in the .gpkg, so the map is
            gone or is quietly a different map.
         5. The map on screen is a DIFFERENT tiling from the one the controls
            show, after edits -- I demo a wrong map and don't know.
         6. Undo/the change list rolls back MORE than the one change I asked
            it to (or rolls back into a state that never existed).
         7. Second dataset in a demo inherits the first dataset's topology
            edits / element-to-variable mapping, so run #2 is silently a
            hybrid of two datasets.
         8. Save "succeeded" (no error, dialog closed) but nothing was
            written, or was written to a path I did not choose.
         9. Loading a saved unit leaves the change list describing edits that
            are not actually applied -- the list lies about the geometry.
        10. Colours/styling on the output layer are lost or re-randomised on
            reopen, so a figure I already put in a paper cannot be reproduced.
        11. Writing to a .gpkg that is currently OPEN in the same project
            locks or truncates it (GDAL lock, layer holding the handle).
        12. Editing a topology element renumbers the OTHER elements, so a
            change I made earlier now applies to a different tile face.
        13. An edit that puts the unit into an invalid state is accepted and
            then poisons every later save until I restart QGIS.
        14. Cancel on a dialog still applies the edits (or Apply/OK does not).
        15. Repeated Save to the same filename appends a duplicate table each
            time so the .gpkg grows and later loads pick the stale one.
        16. Non-ASCII / spaces in a layer or file name break the save path.
        17. A long run started from the Topology tab blocks the GUI so I lose
            unsaved QGIS work by force-quitting.
        18. Loading a unit saved by an older plugin version fails hard rather
            than degrading.
        19. The change list's entries survive Load but point at indices of the
            OLD unit, so applying them corrupts the NEW one.
        20. Nothing at all happens on a control and I waste the demo hunting
            for why.

RESULT: inconclusive -- list only, no source read yet. Note the instruction:
        take the LOW ranks as seriously as the high. #3 (shared GeoPackage
        destroyed), #11 (open .gpkg), #15 (duplicate/stale table) are all
        cheap to test on disk with GDAL alone and are the classic
        "work destroyed, nothing said so" family.
NEXT:   Read CLAUDE.md settled decisions + docs/TESTING.md + TEST-MAP.md +
        HUNT-RECORD.md (mandated, and needed to avoid re-finding covered
        ground), then go hunting for the mechanisms behind these losses,
        starting with the save/load-to-disk family (#2,#3,#8,#11,#15) because
        those end in destroyed files rather than in a wrong pixel.

## 07:44:24  iteration 1  [logical]
TRIED:  Orientation against the losses. Read the binding docs' settled
        decisions for topology/save (CLAUDE.md 5240-5300, 5370-5420,
        5480-5600), then the shelf machinery: topology_edits.shelf_key
        (topology_edits.py:195), dialog.py:6404 `_restore_recorded_topology_
        edits`, :6466 `_restore_topology_edits`, :17977 `_capture_design`,
        :22197 `_topology_edit_key`, :22233 `_topology_stamp`, :22262
        `_topology_description_key`, :22327 `_on_topology_edited`, and
        topology_tab.py:1307-1330 / 1759-1830 (edits/set_edits/_apply/
        _record/_undo/_clear/_refresh_list).
RESULT: ruled out (as findings) for now -- losses #1/#5/#7/#12 in my list all
        land on ground the ledger already names as repaired within the last
        48h: shelf keyed family#count, silence-clears on restore, the gate
        exemption, the stamp carrying modifiers, the FILE key dropping crs.
        One live observation kept: `_clear` shelves `[]` rather than popping,
        while `_restore_recorded_topology_edits` POPS on falsy -- two spellings
        of "no edits" in one store. Held redundantly today because every
        reader is `.get(key) or []`, so [] and absent are indistinguishable.
NEXT:   Go to where work is actually DESTROYED on disk rather than mis-keyed
        in memory: `_write_or_drop_the_topology` (dialog.py:20538) and the
        Save/Load pair (:18931 `_load_pressed`, :18955 `_save_pressed`,
        :18966 `_save_the_map`). Losses #2, #3, #8, #11, #15 -- the family
        that ends in a file a person cannot get their map back out of.

## 07:46:08  iteration 2  [logical]
TRIED:  Losses #2/#3/#8/#11/#15 on the write path -- read `_save_the_map`
        (dialog.py:18966-19260) and `_write_or_drop_the_topology`
        (dialog.py:20538-20800) hunting for a way a save destroys a file.
RESULT: ruled out as fresh findings. Every one of those five losses is
        already a repaired defect with its measurement written at the site:
        the save-after-load table-name recompute that emptied a loaded file
        (19113), the orphan no-data twin (19205), the colleague's
        concurrently-rewritten table (19240), the shared-file `ours` gate
        taken BEFORE the write (19092), `fresh` vs add-to (19140), and the
        six faults of the drop. This ground is saturated.
        ONE ASYMMETRY KEPT, not yet walked to a loss: the change list's
        MARKS. `TopologyPanel.set_marks` has exactly ONE caller
        (dialog.py:21959, a landed build), while `set_edits`
        (topology_tab.py:1315) replaces the whole list on every design
        switch and does NOT clear `_marks`. So `_refresh_list`
        (topology_tab.py:1816) indexes the PREVIOUS design's marks by
        position against the NEW design's rows -- the docstring at
        set_marks says a stale mark "describes another design" and that
        clearing is why the empty list clears, but the design-switch door
        never calls it.
NEXT:   Walk that to a loss or kill it: how long the window is, and whether
        a box-off/exempt-tab journey leaves it open indefinitely. Then get
        off reading and onto tools/hunt_probe.py, because the remaining
        losses in my list (#9, #10, #19) need a file on disk to answer.

## 07:49:45  iteration 3  [perturbation]
TRIED:  Loss #5/#20 ("the map is a different thing from what the control
        showed me"). HYPOTHESIS: the drag PREVIEW and the drop's COMMIT are
        near-twins that disagree. topology_tab.py:1662-1663 calls
        `self._topology.transform_geometry(True, True, data[1], key,
        **edits_module.whole_where_needed(args))` -- `whole_where_needed`
        ONLY -- while topology_edits.apply at topology_edits.py:432-435 calls
        `in_map_units(whole_where_needed(args), current.tileable)`.
        `_SPAN_RELATIVE = {"dx","dy","push_d"}` (topology_edits.py:125) says
        those three are recorded as FRACTIONS of the unit's span and handed to
        the library in MAP UNITS. `in_map_units` has exactly ONE caller
        (grep: topology_edits.py:162 defined, :433 called); the preview is not
        it.
RESULT: confirmed. Probe p1_preview_vs_commit.py, run through
        `python3 tools/hunt_probe.py --name harm --run <probe>` at b9551f5,
        measuring symmetric-difference ground over unit area:
          laves 3.3.4.3.4  nudge_vertex dx=dy=0.05  span 707.11
              preview 6.852e-04   commit 4.661e-01     x680
          archimedean 4.8.8 push_vertex push_d=0.1    span 646.45
              preview 1.941e-04   commit 1.370e-01     x706
          laves 3.3.4.3.4  rotate_edge angle=15       span 707.11
              preview 4.781e-02   commit 4.781e-02     EQUAL
        The rotate arm is the control: `angle` is dimensionless and not in
        _SPAN_RELATIVE, and there the twins agree exactly. The gap is the
        span, to three figures, on exactly the three span-relative arguments.
        The preview's 6.9e-04 of area on a ~400px drawing is invisible; the
        commit is nearly half the unit's ground.
NEXT:   Second, INDEPENDENT route -- pixels rather than shapely. Build the
        real TopologyPanel offscreen, drive `_on_dragging`/`_on_dropped`
        as the view's signals do, grab the drawing widget, and compare what
        the user SEES during the drag against what the recorded edit gives.
        Also check the vertex branch's missing `_within_the_box` clamp
        (topology_tab.py:1637 vs :1652).

## 07:56:52  iteration 4  [perturbation]
TRIED:  Second, INDEPENDENT route for iteration 3 -- not geometry at all.
        Wrapped `Topology.transform_geometry` and recorded the kwargs each
        twin hands the library, driving the REAL TopologyPanel offscreen and
        emitting the view's own `dragging`/`dropped` signals (a drag of 5%
        of the drawing's width on laves 3.3.4.3.4, nudge_vertex, vertex class
        A). Probe p5_kwargs.py.
RESULT: confirmed, and it agrees with route 1 to three figures.
          recorded edit : {'dx': 0.05, 'dy': 0.05}
          unit span     : 707.1067811865476
          PREVIEW handed the library: {'dx': 0.05,     'dy': 0.05}
          COMMIT  handed the library: {'dx': 35.35534, 'dy': 35.35534}
        35.35534 / 0.05 = 707.107 = the span exactly. One gesture, two
        numbers, 707x apart, and the picture gets the small one.
        Two earlier pixel routes (p2, p3, p6) are NOT quotable and I am
        saying so: `_fit` runs inside `paintEvent` on whatever `_drawn()`
        returns, so the view RESCALES to the preview -- and on laves the
        single vertex class means a nudge is a pure translation, which fits
        to the same picture. My own fixture, caught by a stability arm
        (two identical grabs differ by 0 px) and a control arm
        (show_preview(B) vs base = 10 px for a change of 47% of the unit's
        ground). The refit is a real second reason the drag shows nothing,
        but it is not the mechanism I am claiming.
NEXT:   Date it, and check whether the suite could have caught it.

## 07:56:52  iteration 5  [logical]
TRIED:  When did it start, and why has nothing caught it.
RESULT: confirmed. `git log -S`: the preview call went in at 02dc3e6
        (2026-08-30, "the Topology tab's interaction"); `_SPAN_RELATIVE`,
        `in_map_units` and the whole fractions-in-the-record convention
        went in at 7d5c589 (2026-08-31, "The topology tab draws what you
        just did to it") -- and that commit's diff of topology_tab.py does
        NOT touch the preview's transform_geometry call. So the repair for
        the maintainer's OWN report ("clicking and dragging nodes moved
        nothing at all") landed on `apply` and left its twin unvisited:
        a half-applied fix, which docs/TESTING.md names as reading like
        progress because the failure MOVES.
        AND THE GUARD CANNOT SEE IT.
        `test_every_way_of_editing_the_topology_moves_the_drawing`
        (tests/run_tests.py:5300) reads the preview store as
        `id(preview)` -- object identity -- so it asserts the preview
        CHANGED and never how much. That is this project's own "a map
        appeared" assertion, on the one store where the amount is the
        whole point.
        SECOND, SMALLER ASYMMETRY AT THE SAME SITE, same journey: the edge
        branch clamps a dragged value through `_within_the_box`
        (topology_tab.py:1652); the vertex branch (:1637) assigns dx/dy
        raw, and `self._drag_from = dict(args)` (:1660) is taken BEFORE
        `_show_arguments` (:1673) moves the boxes. Measured, drag 2.0:
        the number boxes read dx 1.0, dy 1.0 while the recorded edit holds
        dx 2.0, dy 2.0 -- the control reads half what the map is drawn
        from.
        HEAD re-read: b9551f5, unmoved.
NEXT:   Stop rule reached -- a finding confirmed by a second route. Write
        it up.
