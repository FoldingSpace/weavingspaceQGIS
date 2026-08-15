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
