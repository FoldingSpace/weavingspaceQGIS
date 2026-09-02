# Probes: reproductions worth re-running

These are not tests. They print, and a person reads what they print.
They live here because the hunt record asks that a reproduction worth
re-running be kept rather than left in a scratch directory that does
not survive the session — and each of these was written to settle a
question that is still open in ROADMAP.md.

Run them the way the suite runs, under QGIS's own Python:

    eval "$(bash tools/macos_qgis_env.sh 2>/dev/null | grep -E '^[A-Z_]+=' | sed 's/^/export /')"
    export QT_QPA_PLATFORM=offscreen
    export WEAVINGSPACE_REPO="$PWD"
    "$QGIS_PY" -u tools/probes/<one of them>

**`equal_intervals_under_pins.py`** shows the defect behind the
roadmap's equal-intervals entry: two columns of different range,
pinned identically, drawing different ladders, with class widths that
are not equal. Run it before touching `make_graduated_renderer` and
again afterwards; the fix is done when both columns print the same
ladder and the interior widths match.

**`one_interaction.py`** measures what ONE interaction costs -- a
spinner nudge, a weave-unit rebuild, a ramp pick, a table rebuild, and
a nudge with live update on -- in whichever tree `WEAVINGSPACE_REPO`
names, so two trees can be compared by running it twice. It prints its
own premise (how many layers reached the project, how many live ticks
actually ran a tiling) because both of the wrong answers it gave on
the way looked exactly like measurements. `PERF_EXTRA_LAYERS` fills
the project to test whether cost rises with project size;
`PERF_LIVE_TICKS` sets how many of the expensive tick to drive.

**`interaction_cost.py`** profiles runs and dumps the stats itself,
because the harnesses here end in `os._exit` and `cProfile -o` would
write nothing. `PERF_OUT` says where, `PERF_RUNS` how many.
**`compare_profiles.py`** diffs two of those by CALL COUNT, which is
the number that survives profiler overhead. Both were written for the
responsiveness question and both answer a narrower one than is being
asked — read that roadmap entry before believing a result.

**`number_boxes.py`** prints every number box in the dialog with its
value, step and decimals. Written for the three-significant-figures
rule; useful whenever a control's precision is in question, since
reading the list is faster than reasoning about five rules.

**`zigzag_cleaners.py`** is the measurement behind ruling 5's refusal
being rare rather than usual: each design is zigzagged twice in one
run, once with our own exact dedupe alone and once with upstream's
`get_clean_polygon` in front of it. Ours alone refuses laves 3.3.4.3.4
and hex-slice 4; upstream's cleaner first draws all four designs with
nothing invalid, because it removes corners that are merely very close
and then the colinear ones where ours removed only exact repeats. Both
arms run together deliberately -- one arm says nothing about the other,
and this project has been caught believing one before. Re-run it after
any change to the manipulation repair.

**`what_the_success_sentence_counts.py`** is the measurement behind
the save's "the file holds N of M elements" being asked of the FILE
rather than of one list. Three arms in one run, and the middle one is
the reason no arithmetic works: with an element's row deleted from
the layers panel and a colleague's save having taken a second
element's table, the count was wrong in both directions at once, and
the two errors cancel unless the colleague also took the deleted
element's own table. Re-run it after any change to what a save skips.

**`what_the_overwrite_question_asks.py`** is the measurement behind
"holds nothing" being a question about content rather than bytes. Four
arms, and the last two are the discrimination: a GeoPackage OGR
created and nothing wrote to must NOT be asked about, while somebody
else's map and a file that is not a GeoPackage at all must both still
be. It is also where the obvious composition was measured wrong --
GDAL returns None for a zero-layer GeoPackage exactly as it does for a
text file, so "it opens and holds no tables" cannot separate them.

**`which_crs_the_record_carries.py`** reads the GROUP'S OWN record at
each step of a journey rather than the file at the end of it, which is
where a region and its coordinate system first come to name two
different datasets. Two arms: draw and save, against draw, save,
glance at a second dataset in another system through the region
chooser, and come back through the GROUP chooser. Run it after any
change to what `_stamp_working_state` carries.

**`which_controls_are_live_while_writing.py`** asks two questions in
one run and keeps them apart: which controls a person could actually
press at each beat of a write, and what pressing one costs. The first
is worth asserting even if no press cost anything, which is why it is
sampled rather than deduced -- this project has already fixed a
mechanism whose journey turned out to be the suite's alone. Its seam
is the progress bar's own beat, immediately before the `processEvents`
that makes a click deliverable, and the press is staged there
synchronously rather than from a timer.

**`which_door_remembers_the_embedded_copy.py`** drives BOTH doors into
a saved map -- a Load, and the adoption a reopened plugin performs --
on one self-contained file in one run, and reads the DECISION's own
inputs at the moment of the press beside what the file ends up with.
Two doors on one file is what says whose defect it is rather than
which journey is unlucky. Re-run it after any change to what a door
records about a file.

**`what_a_new_project_leaves_on_the_shelf.py`** reads the SHELF and
the panel across a project clear, with `_scheme_memory` beside them as
the control -- a record that IS in the clear list, so a run where it
survives too is saying the clear never happened rather than that the
shelf is missing from it. It then walks the harm to its end by drawing
the same design in the emptied project against a dialog that never
edited anything. Its own premise is the thing to keep: the first index
of each chooser is a vertex class and `push_vertex`, whose
displacement is exactly zero on this design, so an edit aimed there
changes nothing and the journey afterwards shows nothing being
carried.

**`what_a_save_as_calls_the_tables.py`** asks whether a copy is named
for the map being copied or for the last one drawn, and its oracle is
the file contradicting itself: the copy's own record says which
variable each element was saved with, so a table named for another one
is a file that disagrees with its own description. The control draws
nothing first, since two maps on their defaults agree by accident.

**`where_the_handles_sit_after_a_list_choice.py`** clicks an edge, then
chooses a different class from the chooser, and reads the selection and
the three handle seats after each. The selection moving while the seats
do not is the whole finding: a drag's parameter is a polar coordinate
about the handle's own edge, so it would be measured on one edge and
recorded against another. It aims by asking the product which candidate
offers a handle rather than by computing a point.

**`what_an_apply_during_a_write_reaches.py`** answers what the acting
controls still live during a write can reach: the record is captured
AFTER the element loop, so the question is whether a press delivered by
the write's own pump lands in it. Three arms, and the answer is none of
them -- the record's design half is carried from the group's own
record, so a save standing at no landing cannot move it. Re-run it if
that carry ever changes.
