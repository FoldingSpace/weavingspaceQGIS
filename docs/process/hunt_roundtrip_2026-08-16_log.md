# Hunt: roundtrip — one boundary but not another (2026-08-16)

Direction: pins, copied ladders, no-data layers, hatching and opacity
across every boundary they cross. Frozen commit 1acaddc, probed in
/var/folders/.../weavingspace-hunt/roundtrip/tree via tools/hunt_probe.py.

## 15:01:42  iteration 1  [logical]
TRIED:  Read the whole state map first -- _stamp_category_colours /
        _adopt_category_colours / _adopt_row_symbology (dialog.py
        3747-4214), _add_no_data_layer + _restyle_no_data_layer
        (6255-6428), _add_output_layers (7700-8150), _restyle_only
        (6430-6600), _forget_the_last_project (3942-4005),
        _adopt_existing_group (7219-7300), _copy_classification
        (5266-5430), _signature / _run_signature / _geometry_signature.
        Question: which crossing is unlike its siblings.
RESULT: inconclusive -- but one ORDER stands out as the shape the
        brief names. _adopt_category_colours calls
        _adopt_row_symbology FIRST (3854); that method ASSIGNS
        self._quant_colours[tid][field] = recovered (4214) and
        self._category_colours[tid][field] = recovered (4143), both
        plain assignment. The stamped record is then merged with
        setdefault(field, ...) (3864, 3882), which is a no-op once
        the key exists. And `recovered` deliberately EXCLUDES the
        no-data entry: the categorized branch skips the blank
        catch-all (4136-4138) and the graduated branch enumerates
        renderer ranges only, where NO_DATA_KEY never appears (it
        lives on the paired layer).
NEXT:   Predict: a hand-picked NO DATA colour is LOST across a
        project save/reopen whenever any OTHER colour on that element
        was also hand-picked (or the ramp cannot be named). Measure it.

## 15:07:43  iteration 2  [perturbation]
TRIED:  scratchpad/p2.py -- element 'a' on v1 (one NULL), No data
        recoloured #abcdef AND class 0 recoloured #123456; save .qgz,
        clear, reopen, new dialog, then Generate.
RESULT: confirmed. BEFORE the map draws no-data #abcdef. After the
        reopen the dialog's record for (a, v1) is {'0': '#123456'} --
        the No data pick is GONE -- while the map still draws
        #abcdef, so the editor would offer #dddddd over a map showing
        #abcdef. The next Generate repaints the missing-value areas
        #dddddd while the hand-picked class colour survives at
        #123456. dialog.py:4214 (and its categorized twin 4143)
        assigns _quant_colours[tid][field] outright; the stamp is
        merged at 3882 with setdefault(field, ...) and cannot fill.
NEXT:   Rule out the fixture, isolate the precondition (is a second
        hand-pick required?), and reach the fact by a route that does
        not use the dialog's dicts at all -- read the stamped
        property out of the saved .qgz.

## 15:10:20  iteration 3  [perturbation]
TRIED:  p3.py -- isolate the precondition and reach the fact without
        the dialog: read weavingspace_quant_style straight out of the
        saved .qgz.
RESULT: confirmed, and sharply. The FILE is right -- its colours map
        holds both the no-data key and "0": "#123456" -- so the stamp
        writes both and the READ drops one. With ONLY the No data
        colour picked, everything comes home and Generate redraws
        #abcdef: the journey and the fixture are sound. With a class
        colour picked as well, the record comes back {'0': '#123456'}
        and Generate paints #dddddd.
        (Also caught myself in the named trap: reading
        categories()[0].symbol() off a temporary returned #000000 for
        both variants until the list was bound to a name.)
NEXT:   The categorized twin, and the cheapest door.

## 15:10:20  iteration 4  [perturbation]
TRIED:  p4.py -- same shape on _category_colours (landcover, one
        NULL, catch-all recoloured plus 'forest'), and with NO project
        file at all: just the plugin dialog closed and reopened over
        the existing group.
RESULT: confirmed on both. Graduated: {'0','NO_DATA'} -> {'0'}.
        Categorized: {'forest','NO_DATA'} -> {'forest'}. A plain
        plugin reopen is enough; no save, no restart, no export.
NEXT:   Check that the pins and the copied ladder in the SAME record
        do survive, so the report says what is and is not affected.

## 15:15:57  iteration 5  [logical]
TRIED:  p5.py -- the rest of the record across the same boundary, all
        in force at once: a pin on 'a', a copied ladder on 'b', a
        hand-picked class colour, a Ramp Display Range of (10, 90),
        an opacity of 40, k and reverse. Project round trip.
RESULT: ruled out for pins and copies. pins_a {'low': 4.0}, pins_b
        {'breaks': [4.0, 15.0, 30.0, 55.0], 'low': 4.0}, the drawn
        breaks, k and reverse all came home identical. The two claims
        in one record -- copied VALUES and per-end FLAGS -- both
        survive together.
        Two things did move and both were followed up: the recovered
        picks (iteration 6) and the opacity, which was my fixture.
NEXT:   Separate those two.

## 15:15:57  iteration 6  [perturbation]
TRIED:  p6.py / p7.py -- (a) is the picks result caused by the display
        window being restored AFTER _adopt_row_symbology asks what the
        ramp would draw; (b) why did the opacity spinner not reach the
        layer.
RESULT: (a) confirmed as an OBSERVATION. With no window, {'1':
        '#123456'} comes home unchanged. With a window of (10, 90),
        it comes home as four entries -- '0', '1', '3', '4' -- because
        dialog.py:4197 asks quant_class_colours with
        self._ramp_ranges, which _adopt_category_colours only fills at
        3884, thirty lines after it called _adopt_row_symbology at
        3854. Every class colour is then recorded as hand-picked,
        which the code's own comment at 4203-4206 says would be wrong.
        (b) RULED OUT, my fixture. The opacity spin's handler
        (dialog.py:3042-3047) records and calls
        _refresh_preview_colours; so does the ramp combo. With live
        update off nothing repaints until Generate, which is the
        settled behaviour, and _restyle_only() applied 0.4 the moment
        it was called. Nothing wrong here.
NEXT:   Can the mis-recovered picks produce a wrong map?

## 15:15:57  iteration 7  [perturbation]
TRIED:  p8.py -- set the window the way range_changed sets it, reopen,
        then ask for seven classes, against the same journey with no
        reopen.
RESULT: ruled out as a wrong map. Both draw the identical seven
        colours; the class-count handler retires the positional picks
        before they can be applied. What remains is a record claiming
        four hand-picks nobody made, which can only mis-report a loss
        in the next "a new colour ramp" notice. Reported as an
        observation, severity for the maintainer.

## 15:15:57  iteration 8  [logical]
TRIED:  Re-read HEAD before reporting.
RESULT: HEAD is 1acaddc, the commit frozen at --prepare. It did not
        move under this hunt. `git log -S` dates the collision: the
        categorized recovery branch is f1da490 (2026-08-13), the
        graduated one 98994c6 (2026-08-15), and the No data entry in
        those same dicts arrived with dd112bf (2026-08-15). The
        defect is at most a day old.

## The reproduction, kept because it is worth rerunning

Save as `p2.py` anywhere and run it with
`python3 tools/hunt_probe.py --run p2.py` (after `--prepare`).
It prints the colour the map draws, the record after a project
round trip, what the colour editor would then offer, and what the
next Generate paints.

    """A hand-picked No data colour across a project save/reopen, with a
    file-backed region layer so the reopened project is really usable."""
    import os, sys, tempfile, shutil
    sys.path.insert(0, os.path.join(os.getcwd(), "tests"))
    from qgis.core import (QgsApplication, QgsProject, QgsVectorLayer,
                           QgsVectorFileWriter)
    QgsApplication.setPrefixPath(os.environ.get("QGIS_PREFIX_PATH", "/usr"), True)
    _app = QgsApplication([], True); _app.initQgis()
    import run_tests as T
    T._quieten_the_offscreen_platform(); T._no_modal_dialogs()
    from weavingspace_qgis import bridge
    from weavingspace_qgis.dialog import WeavingSpaceDialog
    
    MINE = "#abcdef"
    folder = tempfile.mkdtemp(prefix="rt2_")
    
    def cat_colour(lyr):
      cats = lyr.renderer().categories()
      return cats[0].symbol().color().name()
    
    try:
      project = QgsProject.instance(); project.clear()
      mem = T._layer_with_a_gap(n=12)
      region_path = os.path.join(folder, "region.gpkg")
      opts = QgsVectorFileWriter.SaveVectorOptions(); opts.driverName = "GPKG"
      QgsVectorFileWriter.writeAsVectorFormatV3(
        mem, region_path, project.transformContext(), opts)
      region = QgsVectorLayer(region_path, "region", "ogr")
      assert region.isValid()
      project.addMapLayer(region)
    
      dlg = WeavingSpaceDialog(iface=T._Iface())
      dlg.live_check.setChecked(False)
      dlg.layer_combo.setLayer(region)
      T._tick(300)
      dlg.table.cellWidget(0, 1).setCurrentText("v1")
      T._tick(200)
      tid = dlg.table.item(0, 0).text()
      dlg.spacing_spin.setValue(400)
      T._generate_and_wait(dlg)
      assert dlg._no_data_layer_ids.get(tid), "no paired layer; probe means nothing"
      rec = dlg._quant_colours.setdefault(tid, {}).setdefault("v1", {})
      rec["0"] = "#123456"                       # one class recoloured by hand
      rec[bridge.NO_DATA_KEY] = MINE             # ...and the No data class
      dlg._apply_style_change()
      T._tick(500)
      paired = project.mapLayer(dlg._no_data_layer_ids[tid])
      print("BEFORE map draws no-data as:", cat_colour(paired))
      dlg.close()
    
      T._project_round_trip(folder)
      T._tick(400)
      revived = WeavingSpaceDialog(iface=T._Iface())
      revived.live_check.setChecked(False)
      T._tick(500)
      for row in range(revived.table.rowCount()):
        item = revived.table.item(row, 0)
        combo = revived.table.cellWidget(row, 1)
        if item is not None and combo is not None and item.text() == tid:
          combo.setCurrentText("v1")
      T._tick(400)
      after = dict(revived._quant_colours.get(tid, {}).get("v1") or {})
      print("AFTER  record keys:",
            [("NO_DATA" if k == bridge.NO_DATA_KEY else k) for k in after],
            "values:", list(after.values()))
      p2 = project.mapLayer(revived._no_data_layer_ids.get(tid) or "")
      print("AFTER  map still draws:", None if p2 is None else cat_colour(p2))
      print("AFTER  editor would offer:",
            after.get(bridge.NO_DATA_KEY) or bridge.NO_DATA_FILL)
    
      # ...and what the next Generate does with it
      revived.spacing_spin.setValue(420)
      T._tick(500)
      T._generate_and_wait(revived)
      T._tick(400)
      p3 = project.mapLayer(revived._no_data_layer_ids.get(tid) or "")
      el = project.mapLayer(revived._element_layer_ids.get(tid) or "")
      rr = el.renderer().ranges()
      print("AFTER GENERATE no-data colour:", None if p3 is None else cat_colour(p3))
      print("AFTER GENERATE class 0 colour:", rr[0].symbol().color().name())
      revived.close()
    finally:
      shutil.rmtree(folder, ignore_errors=True)

