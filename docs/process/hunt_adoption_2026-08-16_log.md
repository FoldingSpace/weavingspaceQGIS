# Hunt: adoption (2026-08-16)

## Summary

Two defects, both confirmed at `ed7231f` and both reproducible in
about four minutes with the probes named below. HEAD was re-read at
the end of the hunt and had NOT moved; the working tree carries
uncommitted edits to `dialog.py` from sibling hunts, which these
claims know nothing about.

1. **Adoption restores the group but not `_last_path`, so the next
   Generate abandons the group it just adopted.**
   `_forget_the_last_project` sets `_last_path = None`
   (dialog.py:4103); `_adopt_existing_group` (7487-7566) never sets it,
   though `_remember_our_table` parses the very path one line away.
   `_add_output_layers` then computes
   `force_new = self.opt_new_group.isChecked() or path != self._last_path`
   (dialog.py:7971), and the file widget still holds the path across
   File > Open. Measured: two groups, four of four adopted layers
   orphaned, both groups' layers reading the SAME GeoPackage tables,
   "Create as new group" UNTICKED, no notice. Controls: emptying the
   file box gives one group, and setting `_last_path` by hand gives
   one group. Scoped to GeoPackage output; memory output compares
   None with None and is unaffected.

2. **A project opened under the dialog leaves the region chooser on
   the plugin's own output layer, and Generate then fails with a
   pandas KeyError.** `_update_layer_exclusions` runs at construction
   (dialog.py:1232) and at the end of `_add_output_layers` (8484) and
   nowhere else, so a project read leaves the excepted list naming the
   destroyed project's layers. Measured: the chooser moves from
   `'region'` to `'a - v1'` (`weavingspace_tile_id='a'`), and Generate
   raises `KeyError: "['prototile_id'] not found in axis"` into a
   critical modal. Not INTRODUCED by the readProject wiring -- it
   would have happened before it too -- but it falsifies that wiring's
   own claim (dialog.py:1121-1126) that a dialog surviving File > Open
   "ends up in exactly the state a freshly opened one would be in",
   and adoption is now the one place that knows which layers are ours.

Third, observed and not chased to harm: `_last_run_sig` and
`_last_geometry_sig` survive `cleared` and adoption does not touch
them, so the two records that decide "nothing changed since the last
run" (2596) and "restyle instead of re-tiling" (6678, 6693) describe a
project that no longer exists, against `_element_layer_ids` that
adoption has just refilled.

Probes: `p1_lastpath.py`, `p2_enumerate.py`, `p3_control.py`,
`p4_chooser.py`, run through `tools/hunt_probe.py --run`.

Direction: what the new `readProject` -> `_adopt_existing_group` wiring
breaks, and what it LEAVES unfilled. Frozen at `ed7231f` via
`tools/hunt_probe.py --prepare --name adoption`; every probe runs in
that copy, never the working tree.

## 19:29:00  iteration 0  [reading]
TRIED:  read CLAUDE.md, docs/TESTING.md, docs/process/HUNT-RECORD.md,
        dev/state-of-play.md, and the wiring at dialog.py:1111-1129,
        1206, `_adopt_existing_group` 7487-7566, `_newest_output_group`
        7597-7647, `_get_or_make_group` 7649-7674,
        `_forget_the_last_project` 4044-4110.
RESULT: two shapes worth probing, both from "enumerate what adoption
        LEAVES".
        (a) adoption never sets `_last_path`, and `_add_output_layers`
            computes `force_new = opt_new_group.isChecked()
            or path != self._last_path` (dialog.py:7971). The output
            path is a WIDGET and survives File > Open; `cleared` sets
            `_last_path = None` (dialog.py:4103). So after a project is
            opened under an open dialog with a GeoPackage path in the
            box, `path != None` -> force_new True -> a SECOND group,
            which is the exact outcome adoption was added to prevent.
            The path is even parsed one line away, in
            `_remember_our_table`, and thrown away.
        (b) the same `_last_path` gates `bridge.embed_style` on both
            restyle sites (dialog.py:6412, 6794), so an adopted
            file-backed project's restyle would not reach the .gpkg.
NEXT:   probe (a) first: it is a wrong map rather than a stale file.

## 19:52:00  iteration 1  [perturbation]
TRIED:  probe p1_lastpath.py -- generate to a GeoPackage, save, then
        `project.clear()` + `project.read()` with the SAME dialog open,
        then Generate again and count groups.
RESULT: inconclusive, and the probe's own fault. The region layer was
        a MEMORY layer, which does not survive a project save, so the
        second Generate was refused with "The selected layer has no
        (non-empty) polygon features" and no run happened at all. The
        measurement that DID stand: adoption restored
        `_group_name = "WeavingSpace tiles"` and 4 element ids, and
        left `_last_path = None` while the file widget still held
        `.../out.gpkg`. So the input to the force_new comparison is
        confirmed asymmetric; the consequence is not yet measured.
        Also learned: a probe importing tests/run_tests.py must call
        `T._no_modal_dialogs()`, or a refusal box hangs it offscreen
        forever (12 minutes wasted).
NEXT:   rerun with the region written to region.gpkg first, and assert
        the reopened region actually has features before believing
        anything the second Generate does.

## 20:06:00  iteration 2  [perturbation]
TRIED:  the same journey with the region on disk, so the reopened
        project can actually be tiled. commit ed7231f.
RESULT: **confirmed.**
          after readProject: group= WeavingSpace tiles  elements= 4
                             last_path= None
                             gpkg box= .../out.gpkg
          groups before Generate: ['WeavingSpace tiles']
          groups after  Generate: ['WeavingSpace tiles 2',
                                   'WeavingSpace tiles']
          adopted layers still in the project: 4 of 4
          MODALS: []
        The dialog adopted the opened project's group and then
        abandoned it on the next Generate, building a second group
        beside it and orphaning all four adopted layers -- with
        "Create as new group" UNTICKED and no notice of any kind. Both
        groups' layers read the same GeoPackage.
NEXT:   pin the cause with controls: empty the file box (force_new's
        other input) and, separately, set `_last_path` by hand.

## 20:19:00  iteration 3  [perturbation]
TRIED:  p3_control.py -- the same journey three times with an EMPTY
        project between cases. A: the box as the user left it.
        B: the box emptied after the reopen. C: `_last_path` set by
        hand to the box's path after the reopen.
RESULT: **cause pinned.** A=2 groups, 4 of 4 adopted layers orphaned.
        B=1 group, 0 orphans. C=1 group, 0 orphans, and the run still
        writes into the same GeoPackage.
        The detail that makes A a WRONG MAP rather than clutter: both
        groups' layers read the SAME tables --
        `out.gpkg|layername=tiles_a` appears once in the orphaned
        group and once in the new one -- so the abandoned group
        redraws the NEW data under the OLD symbology, on top of the
        live map. That is the "invisible double map" the wiring's own
        comment at dialog.py:1113-1120 says it cured.
NEXT:   enumerate what `cleared` leaves and what adoption fills, since
        `_last_path` is unlikely to be the only one.

## 20:34:00  iteration 4  [logical]
TRIED:  p2_enumerate.py -- 31 records snapshotted before the project is
        opened, after `cleared`, and after adoption.
RESULT: three groups, and the middle one is new ground.
        RESTORED by adoption: `_group_name`, `_element_layer_ids`,
        `_gpkg_tables_written`, `_pinned_bounds`, `_ramp_memory`.
        CLEARED AND NOT RESTORED: `_last_path` (finding 1),
        `_last_signatures` (deliberate, per the docstring),
        `_custom_swatch_cache` (a cache; harmless).
        **SURVIVED `cleared` ENTIRELY, and adoption does not touch
        them: `_last_run_sig` (tuple of 21) and `_last_geometry_sig`
        (tuple of 22).** Both describe the project that has gone.
        `_restyle_only` is gated on `_last_geometry_sig is not None`
        (dialog.py:6678) and on `_element_layer_ids` being non-empty
        (6695) -- which adoption has just refilled -- and live update
        skips a run outright when `_run_signature() ==
        _last_run_sig` (2596). So both are live inputs against a
        project they were never measured on.
        And a third thing the snapshot shows plainly: after the read,
        `_watched_layer_id` and `_auto_spacing_layer` both hold
        `a___v3_...`, and `_values_cache` is keyed on a layer whose
        fields are `weavingspace_fid, tile_id, prototile_id, v1, v2,
        v3`. That is one of the plugin's OWN OUTPUT layers, which
        means the region chooser selected it.
NEXT:   measure the chooser directly and press Generate with nothing
        set by hand, which is the user's own next action.

## 20:47:00  iteration 5  [perturbation]
TRIED:  p4_chooser.py -- read the region chooser before and after the
        project is opened under the dialog, setting nothing by hand.
RESULT: **confirmed, and it is the plugin's own output.**
          BEFORE reopen, chooser: 'region' tile_id=None
                                  fields=['fid','v1','v2','v3','landcover']
          BEFORE reopen, excepted: ['a - v1','b - v2','c - v3','d - v1']
          AFTER  reopen, chooser: 'b - v2' tile_id='b'
                fields=['weavingspace_fid','tile_id','prototile_id',
                        'v1','v2','v3']
        `_update_layer_exclusions` is called from exactly two places,
        the constructor (dialog.py:1232) and the end of
        `_add_output_layers` (8484). Neither runs on a project read,
        so the excepted list still names the DESTROYED project's
        layers and the incoming project's outputs are offered and
        auto-selected.
        HONEST ATTRIBUTION: this is not caused by the readProject
        wiring -- it would happen at ed7231f^ too, since nothing
        refreshed exclusions on a project read then either. What the
        wiring changes is whose problem it is: `_adopt_existing_group`
        is now the one place that knows which layers in the incoming
        project are ours, and it does not tell the combo.
        This also reproduces the claim HUNT-RECORD's "Order of
        operations" row records as NOT reproduced ("a project opened
        under a showing dialog offering the plugin's own output as a
        region"). That row should be corrected.
        A probe fault worth recording: reading
        `layer_combo.exceptedLayerList()` after `clear()` + `read()`
        SEGFAULTS -- the list hands back wrappers around freed layers.
        The plugin only ever writes that list, so this is a trap for
        probes and tests, not a product defect.
NEXT:   press Generate with nothing set and see what gets tiled.

## 20:58:00  iteration 6  [perturbation]
TRIED:  the same probe, pressing Generate after the reopen with
        nothing set by hand.
RESULT: **confirmed.**
          AFTER reopen, chooser: 'a - v1' tile_id='a'
          CHOOSER IS POINTING AT OUR OWN OUTPUT: True
          modals: [('critical', 'WeavingSpace Tiling failed:\n\n
                    KeyError: "[\'prototile_id\'] not found in axis"')]
        A user who opens a project with the plugin window up and
        presses Generate meets a crash message naming a pandas axis.
        The sharpest way to state it: the wiring's own comment
        (dialog.py:1121-1126) claims "a dialog that survives a
        File > Open ends up in exactly the state a freshly opened one
        would be in". Measured, it does not. The constructor runs
        `_adopt_existing_group()` at 1206 and then `_build_ui()`,
        `_update_layer_exclusions()` at 1232 and `_on_layer_changed()`
        at 1237; the readProject path runs the FIRST of those and
        stops. A freshly opened dialog picks 'region'; the surviving
        one picks 'a - v1'.

## 21:02:00  iteration 7  [logical]  RULED OUT / NOT MEASURED
TRIED:  several of the directions given, settled by reading rather
        than probing, and recorded so nobody re-walks them.
RESULT: - NO output group in the incoming project: `_newest_output_group`
          returns None and `_adopt_existing_group` returns before
          touching anything (dialog.py:7509-7511). Nothing to report.
        - SEVERAL groups, one older: ranked by numeric suffix, and a
          group holding no output cannot win (7625-7647). Behaves.
          The residual case is a group whose LAYERS were deleted but
          which was KEPT: it fails `carries`, so adoption falls back
          to an OLDER group -- which may be the result the user chose
          to keep, and the next Generate replaces it. Not probed;
          logged as a suggestion rather than a claim.
        - `_last_path` and "Create as new group" DESTROYING a file:
          ruled out. `_generate` asks the FILE rather than the
          dialog's memory (`bridge.gpkg_tables_we_would_replace`,
          dialog.py:7106-7115), so the guard survives `_last_path`
          being None. The mismatch costs a second group, not data.
        - `_last_signatures` left empty: still right, and adoption
          does something better than trusting it -- `_adopt_row_symbology`
          reads the ramp, reverse flag, class count and colours back
          off the restored renderer (4109-4200), and `_adopt_row_pins`
          / `_adopt_category_colours` restore the stamped records, so
          hand styling arrives through the layer rather than through a
          signature the dialog cannot vouch for.
        - NOT MEASURED, and the reason it is worth someone's time:
          the connection at dialog.py:1128 is a LAMBDA. Its sibling
          `_on_layer_style_edited` carries two guards for exactly that
          -- `_dialog_is_gone(self)` at 4844 and the retired-instance
          gate at 4848-4853 -- and `_dialog_is_gone`'s own docstring
          (524-542) says a lambda is what Qt goes on calling after the
          dialog dies. `_adopt_existing_group` has neither guard, and
          nothing disconnects it, so every dialog ever built in a
          session adopts every project opened afterwards. I did not
          stage a destroyed dialog, so this is a reading, not a
          finding.
