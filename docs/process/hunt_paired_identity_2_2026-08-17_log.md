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

## 10:34:00  iteration 2  [perturbation]

TRIED:  p_twin_follow.py -- paste a graduated renderer on v2 onto an
        element whose twin was built for v1, and see what the twin
        then draws.

RESULT: confirmed but TRANSIENT, so not reportable on its own. The
        follow moves the row to v2 and the twin goes on drawing
        20 of 20 tiles as "no data" that all HAVE a v2 value;
        `_element_has_missing_values(a,'v2')` answers True and the
        editor offers a No data row for a column with none. A plain
        Generate heals all of it (twin gone, element on v2), because
        the follow moves the geometry signature. Nothing is lost past
        the next Generate.

NEXT:   the same question about the OTHER route by which a QGIS-side
        edit reaches the table -- deferral. `_assignments` resolves a
        deferring element's mode to "Deferring to QGIS", which is not
        "Graduated", so `_needs_a_no_data_split` and the landing's
        `field_here` both answer as though the column had no gaps.

## 10:58:00  iteration 3  [perturbation]

TRIED:  p_twin_defer2.py -- two arms, one fixture, cleared project
        each. Tile at 500, then at 700. Arm B pastes QGIS's own
        "convert to rule-based" onto the element in between, which is
        the refinement the plugin's own notice invites.

RESULT: confirmed, in pixels and in the records.
        CONTROL: twin survives, element 27 tiles, 0 unpainted pixels.
        DEFERRED: twin GONE after the second run, element 41 tiles of
        which 14 hold an unplaceable v1, renderer still the dock's,
        and 31,988 of 490,000 pixels (6.5%) unpainted. Note given to
        the user: none.
        Second route is genuinely separate: the records and layer
        attributes say the twin is gone and the 14 rows are back on
        the element layer; the magenta render says nothing paints
        there.

NEXT:   the minimal reproduction (is a spacing change needed at all?)
        and the ordinary route into deferral, which is not a rule-based
        paste but a classification method QGIS offers and the plugin
        does not. Then `git log -S` for when it started.
