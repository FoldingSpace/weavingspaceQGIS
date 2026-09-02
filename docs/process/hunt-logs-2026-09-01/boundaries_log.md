# hunt: boundaries (round 6) -- commit b9551f5

## 07:52:00  iteration 0  [logical]
TRIED:  orientation only -- read BRIEF.txt, CLAUDE.md settled rulings, and the
        capture/restore tables in weavingspace_qgis/dialog.py:209-330,
        _capture_design at dialog.py:17977, _capture_working_state at
        dialog.py:18038, _apply_working_state at dialog.py:18402,
        _restore_recorded_topology_edits at dialog.py:6404.
RESULT: inconclusive, no hypothesis yet. Noted the crossings named in the
        direction: shelf key (family, element count), the group record's
        design["topology_edits"], the file's WEAVINGSPACE_STATE record via
        _file_safe_state, and topology_design beside the two tables.
NEXT:   read _write_or_drop_the_topology and the resume path, then enumerate
        every key written into the file's record against every key any
        restore reads.

## 08:21:00  iteration 1  [logical]
TRIED:  enumerate every key WRITTEN into the working-state record against every
        key any restore READS, per the direction's "captured with no matching
        restore". Read _capture_design (dialog.py:17977), _capture_working_state
        (18038), _apply_working_state (18423), _save_the_map's record assembly
        (19392-19470), _write_or_drop_the_topology (20538),
        _topology_description_key (22268), _topology_stamp (22232),
        _queue_topology (21740), _rebuild_unit (6343).
RESULT: inconclusive. Written keys: version, design(+topology_edits), elements,
        output_path, region, region_crs, region_embedded, topology_written,
        topology_design. Only `topology_written` has NO reader anywhere
        (grep over weavingspace_qgis/ finds only its write at 19465) -- but
        the drop asks bridge.gpkg_tables() instead, so nothing is lost by it.
        Also found `_topology_when_resumed` (dialog.py:3205, written at 20425)
        with no reader at all -- vestigial from the v2 drop rule. Neither is a
        harm a user could feel.
NEXT:   stop reading and drive it. The unexamined asymmetry is that
        `_capture_design` and `_topology_description_key` read the PANEL's
        edits while `_topology_edit_key` and `_queue_topology` read the SHELF,
        and only `_rebuild_unit` brings the panel up to the shelf -- and
        `_rebuild_unit` RETURNS EARLY (dialog.py:6355, 6359) before
        `_restore_topology_edits` when no unit can be built. Drive the
        boundaries with the harness and compare the two stores at each.

## 08:58:00  iteration 2  [perturbation]
TRIED:  drive the GROUP-SWITCH boundary end to end (probes/p1_group_switch.py):
        laves 3.3.4.3.4 n=4 with one rotate_edge edit -> Generate -> Save a.gpkg;
        "Create new" -> hex-slice 4 -> Generate -> Save b.gpkg; back to A through
        group_combo.activated; then Save again. Read the shelf, the panel, the
        drawn unit, the group's custom property and the file through stdlib
        sqlite + bridge.read_working_state.
RESULT: ruled out. Every store agrees at every step. A: unit (4, 354398.354,
        4634.938) before and after the round trip; a.gpkg keeps
        weavingspace_unit_no_crs + weavingspace_dual_no_crs and
        topology_design 'laves 3.3.4.3.4#4|2b91419b|b2f202c3' unchanged through
        the re-save; b.gpkg gets its own 'hex-slice 4#4|e55b0568|4f53cda1'.
        No leakage of A's edits into B (B's editkey () and file design None).
NEXT:   the box was TICKED throughout, which is not where a person stands after
        a reopen. Drive the REOPEN door -- a second dialog adopting the group
        with opt_experimental at its default -- and then a first Save into a
        file that has never held a motif, which is the one journey the
        2026-08-31 repair's synchronous rebuild cannot reach (it fires only
        when the file ALREADY holds weavingspace_unit_no_crs, dialog.py:20623).

## 09:26:00  iteration 3  [perturbation]
TRIED:  drive the REOPEN boundary with the experimental box at its DEFAULT
        (probes/p2_reopen.py): laves 3.3.4.3.4 n=4 + rotate_edge 15, Generate,
        NO save; close the dialog and build a second WeavingSpaceDialog over the
        same project (adoption); then a FIRST Save into a file that has never
        held weavingspace_unit_no_crs -- the one journey the 2026-08-31
        synchronous rebuild at dialog.py:20620 cannot reach, since it fires only
        when the file already holds that table.
RESULT: ruled out. The reopened dialog came back with the shelf, the panel and
        the unit all at (4, 354398.354, 4634.938) and the map unchanged
        (a..d 55 tiles, 4808106.0/4841791.0/4923757.7/4918254.7); the save with
        the box UNTICKED wrote both weavingspace_unit_no_crs and
        weavingspace_dual_no_crs, the edit list, and topology_design
        'laves 3.3.4.3.4#4|2b91419b|b2f202c3' -- byte-for-byte the same as the
        box-ticked control arm. `_queue_topology` runs on the edit key alone,
        so panel._topology and _topology_dual are both present.
NEXT:   the last named boundary I have not driven is a change of DATASET.
        Drive R1 -> R2 -> R1 with an edited design and read the shelf, the two
        files and the drawn map at each leg. Also worth one arm: _topology_stamp
        carries `crs` off the region layer while _capture_design and the file's
        key deliberately do not, so a second dataset in another CRS is where
        those two definitions of "the design" are furthest apart.

## 09:58:00  iteration 4  [perturbation]
TRIED:  drive a change of DATASET (probes/p3_dataset_switch.py) with a second
        region in EPSG:27700, since `_topology_stamp()` carries `crs` off the
        region layer while `_capture_design()` and `_topology_description_key()`
        deliberately do not (dialog.py:22290) -- R1 laves+rotate_edge, Generate,
        Save one.gpkg; switch to R2; Generate; Save two.gpkg; switch back to R1;
        Save again.
RESULT: ruled out. The output path cleared on the switch (ruling 1) and came
        back as one.gpkg on the return; the shelf, the panel, the edit key and
        the unit (4, 354398.354, 4634.938) held throughout; both files carry
        both no_crs tables and their own correct topology_design; the re-save of
        one.gpkg left it unchanged. Nothing of R2's reached one.gpkg.
        Also checked by reading: `_gate_experimental_tabs` IS re-asked from the
        family handler (dialog.py:4104) and the element-count handler (3978), so
        the stale-class-list door the comment at 22339 describes is shut, and
        both signatures carry `_topology_edit_key()` (14566, 15921).
NEXT:   the fourth named door, resume from a GeoPackage, with two arms nothing
        above has driven: a save back into the SAME file after a design change
        WITH a Generate (the "rewritten" outcome of topology_design), and the
        same after a modifier change, which moves _topology_stamp without moving
        the shelf key.

## 10:31:00  iteration 5  [perturbation]
TRIED:  resume from a GeoPackage and then save back into the SAME file after a
        design change (probes/p4_resume.py). Arm 1 moved a MODIFIER (rotate 30,
        which moves _topology_stamp but not the shelf key) with the edits still
        in force; arm 2 changed the FAMILY to hex-slice 4, which has no shelved
        edits. Both with a Generate before the Save, box at its default.
RESULT: CONFIRMED on arm 2. Arm 1 rewrote the motif correctly (unit 354398.355,
        dual 274601.524, topology_design laves 3.3.4.3.4#4|1f24a75e|b2f202c3).
        Arm 2 DROPPED both tables: saved.gpkg went from
        weavingspace_unit_no_crs (4, 354398.354) + weavingspace_dual_no_crs
        (4, 274831.276) to NEITHER, with topology_design None, while the map it
        holds is a perfectly good hex-slice 4. Read two ways that agree: bare
        OGR geometry areas and stdlib sqlite3 table names, plus the plugin's own
        bridge.read_working_state.
        Reading the mechanism: `_write_or_drop_the_topology` takes
        `topology = panel._topology` (dialog.py:20589) and its synchronous
        rebuild is guarded by `topology is None` (20618). `_queue_topology`
        returns at its first gate when the box is off and the design in force
        has no shelved edits (21781), so the panel keeps the PREVIOUS design's
        topology -- non-None, so no rebuild, `wanted` True, while
        `_topology_dual` is still stamped for that previous design, so the
        both-or-neither test declines the write (20772) and the drop below it
        removes both tables because described != key.
NEXT:   confirm the mechanism by a second, independent route rather than by
        reading: print panel._topology and the dual's stamp at the moment of the
        save, and run the SAME journey with the box TICKED as a control -- if
        ticking it keeps the tables, the box is deciding what a file contains
        again, through a term the 2026-08-31 repair did not re-aim.

## 10:52:00  iteration 6  [perturbation]
TRIED:  the second route and the control (probes/p5_confirm.py, running): four
        cells crossing "the sender made a topology edit" x "the box is ticked at
        the recipient's second save", each one sender-saves laves 3.3.4.3.4 with
        a motif, then in a FRESH project a fresh dialog Loads it, changes the
        family to hex-slice 4, Generates and Saves back into the same file. It
        prints, at the moment of the press, whether `panel._topology` is None and
        whether `_topology_dual` is stamped for the design on screen -- the two
        terms the reading says decide it -- and reads the file with bare OGR
        geometry areas before and after.
RESULT: pending (the four cells take about twenty minutes).
NEXT:   `git log -S` already dates the guard: `if topology is None and path and
        ours` arrived at 1546077 (2026-08-31, "a motif that comes back") and
        `_write_or_drop_the_topology` itself at 4a3f5e0 (2026-08-30), so the
        drop-without-a-replacement is as old as the method and the repair aimed
        at it covers only the case where nothing holds a stale topology.

## 11:34:00  iteration 7  [perturbation]
TRIED:  the four-cell matrix finished (probes/p5_confirm.py), crossing "the
        sender made a topology edit" against "the experimental box is ticked at
        the recipient's second save". Each cell: sender saves laves 3.3.4.3.4
        with a motif; a fresh project and a fresh dialog Load it, change the
        family to hex-slice 4, Generate and Save back into the SAME file.
RESULT: confirmed, and exactly one cell of four is wrong.
          edit=True  box=False -> before unit (4, 354398.354) dual (4, 274831.276)
                                  AFTER  unit None, dual None, record None
          edit=True  box=True  -> AFTER  unit (4, 311769.145) dual (4, 311769.145),
                                  record hex-slice 4#4|e55b0568|4f53cda1
          edit=False box=False -> AFTER  rewritten, same key
          edit=False box=True  -> AFTER  rewritten, same key
        The printed internals name the mechanism at the press: in the broken
        cell `panel._topology is None -> False` and `dual is of this design ->
        False`; in the edit=False box=False cell `panel._topology is None ->
        True`, which is what lets the synchronous rebuild at dialog.py:20623
        fire and write a fresh motif.
        SO: the shelved edits for laves#4 keep `_queue_topology` building for
        laves; the moment the family moves to a design with no edits and the box
        is off, 21781 returns and the panel keeps LAVES' topology. Non-None, so
        the rebuild is skipped; `wanted` True, so the write is attempted;
        `_topology_dual` still stamped for laves, so 20772 declines; and the
        drop below removes both tables because described != key.
        Two independent readings agree on the outcome -- bare OGR geometry areas
        (p5's `motif`) and stdlib sqlite3 table names (p4) -- plus the plugin's
        own bridge.read_working_state saying topology_design None. Fixture ruled
        out: every cell clears QgsProject and builds a fresh dialog, and the
        three sound cells share that fixture.
NEXT:   stop rule reached -- first finding confirmed by a second route. Write it
        up against b9551f5 (HEAD re-read below).

## 11:40:00  iteration 8  [logical]
TRIED:  re-read HEAD before reporting, per the brief.
RESULT: confirmed -- HEAD is still b9551f5, the commit the frozen copy was made
        from, so nothing moved under this hunt. `git log -S` dates the site:
        `_write_or_drop_the_topology` arrived at 4a3f5e0 (2026-08-30) and the
        `if topology is None and path and ours` repair at 1546077 (2026-08-31).
NEXT:   report.
