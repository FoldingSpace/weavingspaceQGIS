# Hunt log: the ORDER a user works in

HEAD c7b787cd91920493ebc01aa532b45d15c3c64f17 ("The macOS job finds the
interpreter where QGIS actually puts it"). Shape: asymmetry. Area: the
SEQUENCE a user works in rather than the values they use — plugin
opened before data exists, design chosen before a variable, Generate
before configuration, family changed after assignments, colour editor
opened before a run, project opened while the dialog is showing.

Probed against a `git archive HEAD` copy at
`$SCRATCH/probe`, never the live tree (another session is editing it).
Probe scripts in the scratchpad; runner `$SCRATCH/qpy_seq.sh`.

The question carried through every probe: WHAT ORDER DOES THE SUITE
ALWAYS DO THIS IN, AND WHAT HAPPENS IN THE OTHER ORDER?

## 00:00:00  iteration 0  [logical]
TRIED:  Orientation. Read the brief, CLAUDE.md's settled decisions,
        HUNT-RECORD.md (no "sequence/order" direction listed yet;
        nearest are asymmetry/twins at 5 hunts, 9 confirmed, and the
        in-flight-race rows), TEST-MAP.md around the dialog rows, and
        dialog._on_layer_changed / _update_layer_exclusions.
RESULT: inconclusive — orientation only. Candidate asymmetries written
        down before any code runs:
        (a) the suite's fixtures add the region layer to QgsProject
            BEFORE constructing the dialog. Everything the dialog
            does at construction time from `currentLayer()` is
            therefore never exercised with a None layer that later
            becomes a real one.
        (b) `_update_layer_exclusions()` is a "keep our own output out
            of the region combo" guard. When is it called? If only at
            construction and after a run, a layer added later (or a
            project opened later) could slip past it.
        (c) the colour editors (category_editor.py) are documented as
            usable BEFORE a run, reading values from the REGION layer.
            The graduated half is the near-twin. What does the
            categorical half do before a run that the quant half does
            not, or vice versa?
NEXT:   read the construction path and every caller of the exclusion
        and rebuild routines, then drive the dialog in the user's
        order under QGIS's own python.

## 00:18:40  iteration 1  [perturbation]
TRIED:  seq_probe1.py — build WeavingSpaceDialog on an EMPTY project,
        then addMapLayer(make_region_layer()), pump 400ms; compare
        every dialog belief with the suite's order (layer first).
RESULT: CONFIRMED, and it is the reported shape, still live at HEAD.
        Order A (layer, then dialog): vars ['v1','v2','v3','v1'],
        modes all 'Graduated', spacing auto-derived to 500.0,
        _watched_layer set, _had_a_layer True, _auto_spacing_layer set.
        Order B (dialog, then layer): layer_combo.currentLayer() IS
        the region layer — the combo picked it up — but vars
        [None,None,None,None], modes all 'Single colour', spacing
        still the default 1000.0, _watched_layer None,
        _watched_fields (), _had_a_layer False, _auto_spacing_layer
        None. So the combo's selection and every belief the dialog
        holds about it disagree, and nothing ever reconciles them.
NEXT:   second route: read the variable QComboBox's own item list off
        the table widget, and press Generate, to see what the USER
        sees rather than what _assignments() reports. Then instrument
        layerChanged to find out whether it fires at all and what
        currentLayer() says at emission time.

## 00:31:05  iteration 2  [perturbation]
TRIED:  seq_probe2.py — second route. Instrument layerChanged, read
        the variable QComboBox's OWN item list, press Generate, read
        BAR_MESSAGES and the project's layers.
RESULT: confirmed by a second mechanism, and the mechanism is exactly
        the one reported. layerChanged fires ONCE, with arg None and
        currentLayer() also None at that instant; it never fires
        again. The variable combo DOES list ['---','v1','v2','v3',
        'landcover'] (the debounced _rebuild_unit repopulates it
        later) but every row sits on '---', and Generate produces no
        output layer at all. The exact line is dialog.py:3236-3242 in
        _refresh_table: `elif prev is not None and prev["var"] is
        None: pass  # deliberately unassigned`. The dialog cannot tell
        a user's deliberate '---' from the '---' its own construction
        wrote when there was no layer to assign from.
        This is the SEED bug and it is still live at HEAD c7b787c, so
        it is context rather than a new claim.
NEXT:   the seed is not the interesting part. Look DOWNSTREAM of it,
        where the same late-arming shows up in state that heals
        itself later and takes the user's work with it. First
        candidate: _auto_spacing_layer. dialog.py:1629-1634 guards
        auto-spacing so a combo re-emission "must not clobber a
        hand-set spacing" — but in order B that guard is never armed
        (_auto_spacing_layer stays None, measured in iteration 1), and
        the first generation's re-emission is the moment it fires.

## 00:44:20  iteration 3  [perturbation]
TRIED:  seq_probe3.py — in both orders, assign v1 by hand, turn live
        update OFF, type spacing 250, press Generate, wait for the
        task, then read spacing_spin back.
RESULT: CONFIRMED, and it is a new one. Order A: _auto_spacing_layer
        was armed at construction, spacing after the run 250.0, kept.
        Order B: _auto_spacing_layer is None right up to the run, and
        the spacing control reads 500.0 after it — the number the
        plugin derives from the extent, not the 250 the user typed.
        Four output layers in both cases, so the run itself succeeded;
        what changed is the control. Mechanism: dialog.py:1629-1634
        only skips _auto_spacing() when layer.id() == the remembered
        _auto_spacing_layer, and in order B that id was never
        recorded, because _on_layer_changed ran with layer None. The
        first generation adds four output layers, the combo re-emits
        layerChanged (now with the real layer), and the guard that
        exists precisely so a re-emission "must not clobber a
        hand-set spacing" fires the clobber instead.
NEXT:   read the MAP rather than the control — measure tile size off
        the output geometry — and repeat with live update at its
        DEFAULT (on), where the clobbered 500 should queue a second
        run and re-tile at a grain nobody asked for.

## 00:58:10  iteration 4  [perturbation]
TRIED:  seq_probe4.py — second, independent route: measure the tile
        size off the OUTPUT GEOMETRY (median feature area and feature
        count over the weavingspace_output layers) rather than off any
        dialog control, in both orders and with live update both off
        and at its shipped default. One configuration per process, so
        no fixture can carry over.
RESULT: CONFIRMED by the map itself, and the live-update default makes
        it worse rather than better.
          A live=False: control 250.0, map area 15625.0, 1104 tiles
          A live=True : control 250.0, map area 15625.0, 1104 tiles
          B live=False: control 500.0, map area 15625.0, 1104 tiles
          B live=True : control 500.0, map area 62500.0,  312 tiles
        So with live update off the CONTROL LIES about the map (box
        says 500, tiles are the 250 grain); with live update on — the
        shipped default — the clobbered 500 queues a live run and the
        MAP IS RE-TILED at a grain the user never asked for, four
        times coarser, 312 tiles where they asked for 1104. Nothing is
        reported either way.
        `git log -S"_auto_spacing_layer" -- weavingspace_qgis/dialog.py`
        returns 3bd5f52, the initial commit of 2026-08-07: the guard
        and the gap in its arming have both been there from the start.
NEXT:   one more order of the same family — a project OPENED while the
        dialog is showing, against _update_layer_exclusions, which is
        called at construction and after a run and nowhere else.

## 01:14:30  iteration 5  [perturbation]
TRIED:  seq_probe5.py / seq_probe6.py — File > Open with the dialog
        already showing. Order A: a tagged `weavingspace_output`
        layer and a region layer in the project, THEN the dialog.
        Order B: the dialog, then QgsProject.clear() (which is what
        QGIS fires immediately before File > Open), then the two
        layers. Read the exception list, the items the chooser
        offers, and which layer it selected.
RESULT: CONFIRMED, second finding.
          A: excepted ['weavingspace a']; chooser offers ['region'];
             selected 'region'.
          B: excepted []; chooser offers ['region','weavingspace a'];
             SELECTED 'weavingspace a' — the plugin's own output.
        _update_layer_exclusions() has exactly two call sites,
        dialog.py:1051 (construction) and dialog.py:7183 (after a
        run). `cleared` is connected — to _forget_the_last_project,
        dialog.py:991 — so the dialog is designed to survive a project
        change, and that handler empties eighteen per-element records
        and re-arms _auto_spacing_layer while leaving the exclusion
        list untouched. One store updated, its twin not.
        Second, independent route, off the MAP rather than the combo:
        put the old output at x=500000...504000 and the user's regions
        at x=0...4000, then Generate with live update off. The four
        new element layers come out at x=499589...504411. It tiled its
        own previous output, half a million map units from the user's
        data, and said nothing — the exact harm the docstring at
        dialog.py:1584 says the method exists to prevent. With live
        update at its default the first map is drawn from the old
        output too (98 tiles), and only the post-run exclusion refresh
        heals the chooser and re-tiles from the right layer.
        `git log -S"_update_layer_exclusions"` returns 3bd5f52, the
        initial commit; the `cleared` connection is 2adb7dd, this
        morning, which is when the dialog started outliving a project.
NEXT:   check the other hunt running in this direction
        (docs/process/hunt_fixture_order_2026-08-15_log.md) so the two
        claims are not the same claim twice.

## 01:22:00  iteration 6  [logical]
TRIED:  Read hunt_fixture_order_2026-08-15_log.md, another hunt in the
        same direction, to avoid claiming its finding again.
RESULT: no overlap. That hunt owns the SEED defect (empty dropdown,
        no defaults, Generate produces nothing) and its variants C, D,
        E. Neither of my two — the hand-set spacing clobbered by the
        late-armed auto-spacing guard, and the project-open exclusion
        gap that tiles the plugin's own output — appears in it.
        Hypotheses logged this run: 6. Findings claimed: 2, both
        reproduced by a route that reads the OUTPUT GEOMETRY rather
        than any dialog control. Ruled out / claimed-as-context: the
        seed bug (real, but already owned).
