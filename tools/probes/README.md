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
