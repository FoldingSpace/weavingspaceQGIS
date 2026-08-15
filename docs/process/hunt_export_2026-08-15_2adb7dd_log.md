# Hunt log — pinned bounds and copied ladders across non-project-save boundaries

HEAD 2adb7dd. Shape: one-boundary. Area: the GeoPackage output with
embedded styles, exportNamedStyle/QML out and back in, the "Create as
new group" path, and a style QGIS restores from a .qgs written by a
different plugin version.

Probes live in the session scratchpad and run under QGIS's own python
via `qpy.sh`. No repo source is edited by this hunt.

## 15:25:05  iteration 0  [logical]
TRIED:  Read the binding documents before forming any hypothesis —
        CLAUDE.md (pins/copies settled decisions at "CLASS BOUNDS A
        PERSON SET"), docs/process/HUNT-RECORD.md, and the code the
        area names: dialog._stamp_category_colours (3312),
        _adopt_category_colours (3369), _copy_classification (4629),
        _release_copied_breaks (4857), _add_output_layers (~6290),
        _restyle_only (5313), bridge.embed_style (2185),
        compat.save_style_to_database (222).
RESULT: baseline facts established, no claim yet.
        * pins ride ONE custom property, weavingspace_quant_style,
          holding {"field", "colours", "pinned": {low|high|breaks},
          "range"}.
        * both the run-landing path and the restyle path stamp, then
          embed_style, in that order (the 2026-08-13 fix).
        * "Create as new group" resets _element_layer_ids /
          _last_signatures inside _get_or_make_group BEFORE old_ids is
          read, so the previous group's layers are not removed. The
          obvious "new group destroys the old result" reading is WRONG
          and is ruled out here.
        * new group + the same .gpkg path is refused with a modal.
NEXT:   measure what actually crosses each boundary, rather than
        reading it. First question: does weavingspace_quant_style
        survive (a) saveNamedStyle/loadNamedStyle and (b) a cold
        reopen of the .gpkg through loadDefaultStyle? The existing
        test only asserts weavingspace_output over route (b).

## 15:29:50  iteration 1  [perturbation]
TRIED:  probe1.py — one pin (low=10.0) on element 'a' over v3, n=12,
        spacing 1200, then each of the three non-project-save
        crossings measured for BOTH the drawn ranges and the stamp.
RESULT: ruled out, on all three. Measured values:
        live ranges [(0,10),(10,22),(22,38),(38,62.25),(62.25,121)]
        stamp {"colours":{},"field":"v3","pinned":{"low":10.0},
               "range":[0,100]}
        (a) QML: saveNamedStyle wrote all three stamps into the file;
            loadNamedStyle onto a bare memory layer restored ranges
            IDENTICAL and the quant stamp verbatim. My prior that
            QgsVectorLayer::readSymbology filters custom properties to
            keys beginning "variable" is WRONG on QGIS 4.0.3.
        (b) .gpkg opened cold in a cleared project: ranges identical,
            quant stamp verbatim, weavingspace_output True. Note this
            also proves the SECOND embed reaches the file — the pin was
            set after the run, so only _restyle_only's embed_style
            could have put it there.
        (c) new group: group 2 ranges identical and stamped; group 1
            survives with its own layers and its own ranges; groups are
            ['WeavingSpace tiles 2', 'WeavingSpace tiles'].
NEXT:   the pin ITSELF crosses cleanly, so stop asking whether it
        crosses. Two things the probe showed in passing are worth
        chasing instead, both about the stamps travelling too far or
        being read by the wrong reader:
        (i) an exported QML carries weavingspace_output AND
            weavingspace_tile_id='a', so a style pasted from one
            element onto another makes TWO layers claim one element id;
        (ii) _adopt_existing_group looks up GROUP_BASE_NAME only, so
            after "Create as new group" a reopened dialog can only find
            "WeavingSpace tiles", never "WeavingSpace tiles 2".

## 15:31:10  iteration 2  [perturbation]
TRIED:  hypothesis (ii). dialog.py:5990 `root.findGroup(GROUP_BASE_NAME)`
        — after "Create as new group" the live result is in
        "WeavingSpace tiles 2", so a dialog closed and reopened (NO
        project save; the docstring says users do this constantly)
        adopts the KEPT-FOR-COMPARISON group instead. probe2.py:
        run 1 pinned low=10 -> new group -> unpin (run 2 recomputes) ->
        close -> reopen.
RESULT: CONFIRMED. Measured:
        run 2 after the unpin  (0,4)(4,14.2)(14.2,30)(30,55)(55,121),
                               stamp removed -> None
        run 1 (kept, untouched) (0,10)(10,22)(22,38)(38,62.25)(62.25,121),
                               stamp pinned low 10.0
        reopened dialog: _group_name 'WeavingSpace tiles', adopted layer
        IS run 1's, _pinned_bounds {'a': {'v3': {'low': 10.0}}} — a pin
        the user had removed, restored from the older group's stamp.
        A Generate from the reopened dialog then replaced run 1's layers
        and left run 2 untouched forever.
        Started at the first commit (3bd5f52): `git log -S
        "findGroup(GROUP_BASE_NAME)"` and `-S "opt_new_group"` both
        return only that commit, so the two features have never agreed.
NEXT:   second independent route, not the dialog's records and not
        renderer.ranges().

## 15:32:17  iteration 3  [perturbation]
TRIED:  probe3.py — same session, but the classes are read by starting
        a render context and asking symbolForFeature which symbol each
        tile actually gets, and the overwrite is read as FEATURE COUNTS
        after the reopened dialog changes the spacing to 2000.
RESULT: CONFIRMED by the second route.
        kept run 1 first class  #fff5f0 v3 0..10, n=44   (the pin)
        live run 2 first class  #fff5f0 v3 0..4,  n=33   (unpinned)
        after reopen + Generate at spacing 2000:
          group 'WeavingSpace tiles'   a..d at 45 features  <- REWRITTEN
          group 'WeavingSpace tiles 2' a..d at 113 features <- orphaned
          new map's first class #fff5f0 v3 0..10, n=18 — the deleted
          pin is in force again, measured without touching ranges().
        Ruled out my own fixture: probe3 starts from project.clear() in
        a fresh process and builds its own region layer; nothing else
        had run.
NEXT:   observation (i) — the stamps travel inside an exported QML.
        Measure what that costs when a style is pasted from one output
        layer onto another layer.
