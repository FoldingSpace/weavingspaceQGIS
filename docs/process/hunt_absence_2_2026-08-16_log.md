# Hunt log: absence-2, rendering and record of the three absence kinds

Frozen at `ed7231f` (`hunt_probe --prepare --name absence-2`). Every
probe runs against that copy, never the working tree.

## 09:05:00  iteration 1  [logical]
TRIED:  read absence.py, bridge.make_no_data_renderer, dialog's
        `_absence_kinds_for` / `_absence_colours_and_kinds` /
        `_add_no_data_layer` / `_repaint_no_data_layer`, the landing
        re-read at dialog.py:8010-8050, `_signature`, and
        category_editor's row build, asking which readers of "one
        no-data row" were widened to three when the kinds were.
RESULT: `_edit_quant_colours` (dialog.py:5269-5277) appends one row
        per kind present to `order` and NEVER extends `bounds`;
        category_editor.py:488-526 special-cases `NO_DATA_KEY` alone,
        so an infinity row falls into the CLASS branch and indexes
        `self._bounds[row]`. `_last_class_row` (category_editor.py:416)
        WAS widened to skip every trailing absence row, which is the
        tell: one reader of the pair was updated and its twin was not.
NEXT:   measure it rather than argue it -- build the window exactly as
        the dialog builds it.

## 09:18:00  iteration 2  [perturbation]
TRIED:  probe p1_editor_infinity_row.py -- construct
        CategoryColourDialog with two classes and four different
        absence row sets.
RESULT: CONFIRMED.
          no data only        OPENED rows=3 first-col=['0','5','no data']
          no data + infinity  RAISED IndexError: list index out of range
          both infinities     RAISED IndexError: list index out of range
          infinity alone      RAISED IndexError: list index out of range
NEXT:   a widget-level probe is not the product. Drive the dialog.

## 09:31:00  iteration 3  [perturbation]
TRIED:  probe p2_editor_via_dialog.py -- real dialog, region layer
        holding NULL/NaN/+inf/-inf (`_layer_with_infinities`), v1
        graduated, Generate, then `_edit_quant_colours` exactly as the
        "Edit colours" button calls it. Only `exec` replaced.
RESULT: CONFIRMED through the product path.
          kinds present: no-data, -inf, +inf
          paired layer holds ['neg-infinity','no-value','pos-infinity'],
            18 features -- so the SPLIT and the RENDERER are right
          pressing Edit colours: IndexError at
            category_editor.py:522, `self._bounds[row]`
        The map draws the three kinds correctly; the window that is
        supposed to colour them cannot open at all.
NEXT:   the editor being unopenable makes "does an infinity pick reach
        the map / survive a landing / a save / a GeoPackage" untestable
        through the UI. Write the picks into the record directly (what
        the editor's `picked` callback does) and chase those four.

## 10:02:00  iteration 4  [perturbation]
TRIED:  probe p3_lifecycle.py -- write the three picks into
        `_quant_colours` exactly as the editor's `picked` callback
        does, then chase them: restyle path, a further Generate
        landing on top, project save + reload into a fresh dialog,
        and the GeoPackage table read back cold with its embedded
        style. Categories bound to a name before subscripting.
RESULT: RULED OUT, all four. #111111 / #22aa22 / #aa22aa arrived and
        stayed at every stage; `classAttribute` stayed 'ws_absence';
        labels stayed ['no data','negative infinity','infinity'] in
        ABSENCE_KINDS order throughout, so LEGEND ORDER IS STABLE too.
        The stamp/adopt path carries the two new keys without an edit
        because it JSON-dumps the whole picks dict.
NEXT:   the record and the persistence are sound. Ask the other
        question in the direction: what happens when the KINDS move.

## 10:24:00  iteration 5  [perturbation]
TRIED:  probe p4_kinds_change.py -- three acts on one session:
        generate with NULL/NaN/+inf/-inf; edit the +inf to 3.5 and
        regenerate; edit a NULL to +inf and regenerate. Compare the
        renderer's category list against the values the paired
        layer's tiles actually wear.
RESULT: CONFIRMED.
          act 0  legend == worn                      agree
          act 1  (+inf -> 3.5)  legend == worn       agree
          act 2  (NULL -> +inf) legend=['no-value','neg-infinity']
                 tiles wear     ['neg-infinity','no-value',
                                 'pos-infinity']     MISSING
NEXT:   act 1 rebuilt and act 2 did not, so the difference is the
        re-seed gate, not the renderer. Find which term of the
        signature moved in act 1 and not in act 2.

## 10:41:00  iteration 6  [logical + perturbation]
TRIED:  probe p5_digest.py -- print `_value_digest('v1')` and whether
        `_signature` still equals the stored one, either side of a
        NULL -> +inf edit and, as a control, either side of an
        ordinary finite edit.
RESULT: CONFIRMED, mechanism named.
          after the first run   digest=(144,140,0.0,11.0,-9102610715340115084)
                                signature unchanged: True
          NULL -> +inf          digest=(144,140,0.0,11.0,-9102610715340115084)
                                signature unchanged: True   <-- blind
          control finite edit   digest=(144,140,0.0,100.0,-1171698888464387657)
                                signature unchanged: False
        dialog.py:2838-2844 builds the digest's numbers from values
        that are `math.isfinite`, so every unplaceable value is
        excluded from all five terms. Swapping one KIND of absence for
        another moves nothing, `kept_by_hand` (dialog.py:8304) stays
        true, and `_add_no_data_layer` is handed
        `old_no_data_renderers[tid]` (dialog.py:8364) -- last run's
        categories over this run's tiles.
NEXT:   measure the harm through the renderer itself rather than
        inferring it from a category list.

## 11:03:00  iteration 7  [perturbation]
TRIED:  probe p6_holes.py -- startRender / symbolForFeature per
        feature / stopRender on the paired layer, on a fixture whose
        only unplaceable values start as NULLs and one -inf.
RESULT: CONFIRMED, both directions, in one session.
          first run                DRAWN {neg-infinity:4, no-value:9}
          NULL -> +inf, regenerate DRAWN {neg-infinity:4, no-value:5}
                                   DRAWN AS NOTHING {pos-infinity:4}
          -inf -> NULL, regenerate DRAWN {no-value:9}
                                   DRAWN AS NOTHING {pos-infinity:4}
                                   legend still lists negative infinity,
                                   which no tile now wears
        Four tiles are holes -- the exact failure the paired layer
        exists to remove -- and a swatch nobody can wear is in the
        legend, which is the defect this feature's own docstring says
        it fixes elsewhere. Both silent; the notice still reads "They
        draw as no data, outside the class breaks".
NEXT:   the two remaining items in the direction.

## 11:20:00  iteration 8  [perturbation]
TRIED:  probe p7_backward.py -- a paired layer with NO ws_absence
        column, rendered through make_no_data_renderer with kinds
        None, an empty set, and with a per-kind picks dict.
RESULT: RULED OUT for drawing: 5/5 features drawn in all three cases,
        attribute '', label 'no data'.
        ONE MINOR THING, worth a line rather than a fix on its own:
        in that fallback branch the colour is `plain or NO_DATA_FILL`,
        and `plain` is None whenever a DICT was passed -- so a hand
        picked No data colour is silently dropped and the layer paints
        #dddddd. `_absence_colours_and_kinds` returns exactly that
        shape (a dict, kinds None) for a layer with no column, so
        repainting an older paired layer ignores the user's pick.
NEXT:   report.

## 11:32:00  iteration 9  [summary]
RULED OUT this hunt: an infinity colour reaching the map; surviving a
run landing on top of it; surviving a project save and reload;
surviving a GeoPackage write and a cold reopen; legend order; the
backward-compatible single catch-all still drawing; the split and the
stored kinds themselves, which were right in every probe.
CONFIRMED: two, both above.
