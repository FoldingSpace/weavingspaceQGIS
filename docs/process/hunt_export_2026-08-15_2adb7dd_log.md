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
