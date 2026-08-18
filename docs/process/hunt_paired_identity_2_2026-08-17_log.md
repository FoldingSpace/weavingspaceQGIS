# Hunt `paired-identity 2`: the No Data twin against today's changes

Direction: the paired No Data layer; shape: two-stores. Re-hunt of the
2026-08-16 area against code written 2026-08-17 (the row following a
QGIS-side renderer, the mid-run deferral refresh, the colour guard
embedding on its way out).

Frozen at e2976b0. Copy: `$TMPDIR/weavingspace-hunt/solo/tree`.

## 10:05:00  iteration 1  [logical]

TRIED:  Read the whole of the twin's life against today's diff, and
        grepped every reader of `weavingspace_tile_id`. Readers:
        `_adopt_existing_group` (dialog.py:8697/8716/8725, splits the
        twin off by `weavingspace_no_data`), `_newest_output_group`
        (8857, presence test only), and the writers at 7716 and 9720.
        Today's three new/edited sites all key on
        `_element_layer_ids` alone: `_row_follows_the_renderer`
        (5746-5954), the mid-run `_refresh_deferring_rows` gate
        (5512-5540), and the four stamp-and-embed exits (5689-5704,
        5725-5740, 5947-5949).

RESULT: inconclusive. No reader gains a second answer -- adoption was
        fixed on 2026-08-16 and the split is intact. What the follow
        DOES do is move the row's variable and then re-record
        `_last_signatures[tid]`, with nothing said to the twin, whose
        rows are the PREVIOUS variable's absences.

NEXT:   measure that. Does a followed field change leave the twin
        painting real values as "no data", and does anything heal it.
