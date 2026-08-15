# Hunt log: what the table and the swatch CLAIM vs what the map draws

Direction: two-stores, over the pinned/copied element's UI claims —
boxed pinned end, hatched unused classes, the ramp cell, the Classes
cell, and the pin glyph's down/up state in category_editor.py.
HEAD 2adb7dd. Started 2026-08-15 15:24 UTC.

## 15:24:15  iteration 0  [setup]
TRIED:  read CLAUDE.md, HUNT-RECORD.md, TEST-MAP.md pin/copy rows.
RESULT: covered already — pin reaches map, copy leaves one number in
        every control, pin shows which way it is set (visual), copy
        survives round trip, reduction counts the pool a pin leaves.
NEXT:   read category_editor.py's swatch/glyph painting and dialog.py's
        Classes/ramp cell writers, and ask which store each reads.

## 15:41:30  iteration 1  [logical]
TRIED:  which store answers "hatch this stripe"? dialog.py:3955
        `_unworn_stripes` reads the ELEMENT OUTPUT LAYER's live
        renderer + uniqueValues. dialog.py:4029-4038 caches the icon
        under a key made only of the ASSIGNMENT record (field, ramp,
        reverse, scheme, k, range, picks, pinned) plus the REGION
        layer's fingerprint. Two stores, one key.
RESULT: by reading only: the key cannot see the element layer at all.
        Worse, dialog.py:4917 `_apply_style_change` runs
        `_refresh_preview_colours` -> `_queue_live` ->
        `_update_dynamic_columns` -> `_sync_row` -> swatch BEFORE
        `_restyle_only()` at 4926 re-seeds the layers. So the swatch
        is computed from the PREVIOUS renderer and cached under the
        NEW key. `_restyle_only` (5313-5451) never pops the cache and
        never re-syncs; `_add_output_layers` (~6579) does not pop it
        either; `_on_layer_style_edited` is gated off by
        `_applying_style`.
NEXT:   worktree at scratchpad/hunt-swatch (HEAD 2adb7dd). Probe:
        copy a ladder that leaves unreachable classes, then read
        (a) bridge.unworn_classes on the LANDED renderer, (b) the
        icon pixels the table actually shows.

## 15:52:10  iteration 2  [perturbation]
TRIED:  swatch_probe1.py on the worktree. n=12 region, laves 3.3.4.3.4,
        element a on v3 (0-121), element b on v1 (0-11). Generate, then
        copy a's ladder onto b. _custom_swatch_icon spied.
RESULT: CONFIRMED. The one swatch built after the copy was drawn with
        hatched=[]. The landed element-b renderer holds 5 classes
        (0-4, 4-14.2, 14.2-30, 30-55, 55-55) over values 0..11, and
        bridge.unworn_classes on it says [2, 3, 4]. dlg._unworn_stripes
        asked afterwards also says [2, 3, 4]. Second route, pixels:
        the held icon has 5 distinct colours, a correctly built one 14.
NEXT:   how long does it last, and is the held icon literally the
        unhatched one?

## 15:58:40  iteration 3  [perturbation]
TRIED:  swatch_probe2.py, clean project (0 layers at start), byte
        comparison of the held pixmap against D._custom_swatch_icon
        built with hatched=[] and with hatched=[2,3,4].
RESULT: CONFIRMED and PERSISTENT. held==UNHATCHED True at: right after
        the copy, two seconds later, after a SECOND full Generate, and
        after nudging another element's opacity. It heals only when
        something in the TARGET ROW's own cache key moves -- ticking
        the target's Reverse gave held==HATCHED True.
NEXT:   rule in/out the other four claims in the area: the boxed pinned
        end, the ramp cell, the Classes cell, and the pin glyph.

## 16:10:05  iteration 4  [perturbation]
TRIED:  swatch_probe3.py — the other four claims, driven through the
        editor's own PinButton.click().
RESULT: RULED OUT, all four. Pin low=30 on element a: record
        {'low': 30.0}, swatch boxed=[0], ramp cell still reads "Reds"
        with pinned display on and Custom off — exactly the settled
        2026-08-14 decision. After the copy the Classes cell, user_k,
        _class_counts, assignment k and the map all read 5. The
        target's pin glyphs are both UP with a breaks-only record,
        which is the "a copy is not fully pinned" rule holding.
        BUT: with the editor still open after the pin, its rows still
        printed the PRE-pin ladder.
NEXT:   measure that.

## 16:18:40  iteration 5  [perturbation]
TRIED:  swatch_probe4.py — print the open editor's cells before and
        after a pin, then click the OTHER pin without typing.
RESULT: CONFIRMED. After pinning low at 30 the map draws
        (0,30)(30,42)(42,55.5)(55.5,77)(77,121); the still-open window
        prints ('0',30)('4','14.2')('14.2','30')('30','55')(55,'121')
        — rows 1-4 are the pre-pin ladder, and row 0's upper (30) does
        not even meet row 1's lower (4). The HIGH spin box still shows
        55.0 while the map's last class starts at 77.0, so clicking
        that pin with nothing typed writes high=55 and moves three
        interior breaks (42 -> 37.333, 55.5 -> 44.667, 77 -> 55).
NEXT:   second independent route for both, and a different fixture.

## 16:31:20  iteration 6  [perturbation]
TRIED:  swatch_probe5.py — a DIFFERENT fixture (n=20 region,
        hex-dissection n=3, spacing 900), copy the OTHER way (b's v3
        onto a's v1), and second routes for both findings.
RESULT: BOTH REPRODUCE.
        Finding 1: map classes (0,14.8)(14.8,45)(45,90)(90,162)
        (162,162) over tile values 0..19; unworn_classes = [2,3,4];
        the swatch the CELL holds has 5 distinct colours over 5
        stripes, i.e. no hatching anywhere.
        Finding 2: pinned low at 45. Route A, _current_graduated_
        classes (its own renderer off the region's classification
        values), and route B, the output layer QGIS is drawing, BOTH
        give (0,45)(45,78)(78,121)(121,190)(190,361); the open window
        still prints (0,14.8)(14.8,45)(45,90)(90,162)(162,361).
NEXT:   provenance, then write up.

## 16:36:00  iteration 7  [logical]
TRIED:  when did each start? git log -S.
RESULT: Finding 1 arrived with the feature: `_unworn_stripes` and the
        cache key carrying `_layer_fingerprint()` both come from
        ee506ab, "Classes no tile wears are hatched rather than
        hidden", 2026-08-14. It has never worked from the copy that
        creates it. The suite tests `bridge.unworn_classes` directly
        (run_tests.py:7556) and nothing drives the dialog path — a
        pair with a motionless axis.
        Finding 2: the editor's `_bounds` snapshot predates pinning
        (0ec8ecc, 2026-08-10); pins were added to that window in
        12f8c3d, and nothing was added to refresh the rows. Note the
        asymmetry: `range_changed` DOES hand refreshed colours back to
        the window, `pin_changed` hands nothing back.

## 16:40:00  iteration 8  [close]
TRIED:  git status; worktree cleanup.
RESULT: plugin source untouched; only this log written. Worktree
        scratchpad/hunt-swatch removed. HEAD moved to 0305787 while I
        worked (tests + logs only, no plugin source), so both findings
        stand at 0305787 as measured at 2adb7dd.

## Reproductions

Both under QGIS's own python, from the repo root (or a worktree):

    bash <scratch>/qpy.sh <scratch>/swatch_probe2.py   # finding 1
    bash <scratch>/qpy.sh <scratch>/swatch_probe4.py   # finding 2

Finding 1, smallest form: region n=12, laves 3.3.4.3.4 n=4, spacing
1200, element a on v3 (0-121) and b on v1 (0-11); Generate; then
`dlg._copy_classification("a", "b")`. Compare the byte content of the
icon in `table.cellWidget(row_b, 4)._custom_icon` against
`dialog._custom_swatch_icon(shades, [], [])` and against the same
built with `bridge.unworn_classes(...)`. It equals the UNHATCHED one.

Finding 2, smallest form: same fixture, open a's graduated editor,
set the low spin box to 30 and click its pin; the window's rows and
the other pin's spin box are then the pre-pin ladder.

## Where it goes wrong

Finding 1: dialog.py:4062 asks `_unworn_stripes`, which reads the
ELEMENT OUTPUT LAYER (dialog.py:3982-3994); the icon is cached at
4064 under a key (4029-4038) that names only the assignment record
and the REGION layer's fingerprint. And `_apply_style_change`
(dialog.py:4925-4926) repaints the table BEFORE `_restyle_only`
re-seeds the layers. So the answer is taken from the previous
renderer and frozen under the new key. `_restyle_only` and
`_add_output_layers` neither pop the cache nor re-sync.

Finding 2: category_editor.py:293 `self._bounds = list(bounds)` is a
snapshot; `_pin_toggled` (580-604) and `_bound_edited` (606-631)
change the map and leave the table and the OTHER end's spin box on
the snapshot. `_pin_widgets["high"]`'s box (566) then offers a number
that is no longer a boundary of anything.
