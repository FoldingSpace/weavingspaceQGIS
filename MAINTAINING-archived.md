# Archive: MAINTAINING.md

The full accounts cut out of `MAINTAINING.md` by the archiving pass
(docs/DOC-ARCHIVING.md). Nothing here is a rule you must read
before working: `MAINTAINING.md` carries every rule and the headline
of every lesson. This file carries the episode each one came
out of -- what was measured, what was tried first, what the
superseded form of a rule was.

READ IT WHEN `MAINTAINING.md` points you here by id (M-1,
M-2, ...), when a rule surprises you and you want to
know what it cost, or when you are about to change a rule and
need to know what it was built to prevent. Ids are stable:
quote them, do not renumber them.

## Index

- **M-1** — Two shard faults: a verdict that was not the last line, and a shard that died at startup  <sub>Long jobs: the accounts behind the rules</sub>


## Long jobs: the accounts behind the rules
- **M-2** — The dataset-switch contract of 2026-08-21 and 24, as it stood before the group replac...  <sub>Architecture: superseded contracts</sub>
- **M-3** — The build QGIS never started: the 133-second measurement, the three deliberate choices ...  <sub>The light pass of 2026-09-05</sub>
- **M-4** — The topology drop's four faults, the key that replaced them, the guard that decides not...  <sub>The light pass of 2026-09-05</sub>
- **M-5** — The synchronous build inside a save, measured at 27.53 seconds, and the deferral that r...  <sub>The light pass of 2026-09-05</sub>
- **M-6** — The Design tab's layout: the style measurement, the four rows, the withdrawn show-time ...  <sub>The light pass of 2026-09-05</sub>
- **M-7** — The chained patches and the fixed-point self-check they broke, in full  <sub>The light pass of 2026-09-05</sub>


### M-1 — Two shard faults: a verdict that was not the last line, and a shard that died at startup

<sub>Cut from `MAINTAINING.md`, lines 30–54 of the
2026-09-05 revision.</sub>

**AND A SHARD'S VERDICT IS NOT ITS LAST LINE.** (2026-08-30.) A watcher
reporting `tail -1` showed a GDAL warning where a shard had in fact
finished — "231 passed, 0 failed" sits several lines above, because
OGR writes an auxiliary-file warning on the way out. Read for the
verdict LINE, not for the end of the file, and where there is no
verdict line say so in those words: a shard that died and a shard
whose last line is noise look identical to a naive tail, and only one
of them is a problem.

**AND A SHARD CAN DIE AT STARTUP, WHICH LOOKS LIKE NOTHING AT ALL.**
(2026-08-28.) Recording per-test coverage three ways, shard 0 was gone
before it ran a single test: `main()` cleared its scenario record with
`if os.path.exists(x): os.remove(x)`, all three recorders saw the
file, two removed it, and the third met FileNotFoundError. The other
two ran on perfectly, the progress total climbed, and the record would
have been missing a third of the suite -- which overstates survivors,
since a test absent from the record is never offered the chance to
notice a mutant. Both sites suppress the error now, and a family test
scans `tests/` and `tools/` for the shape.
SO READ SHARDS SEPARATELY, NEVER ONLY THEIR SUM. The fault was visible
as an asymmetry -- nineteen, thirty, and nothing -- and invisible in
the total. `tools/merge_coverage_shards.py` is the backstop rather
than the detector: it counts the files against the total each one
names and refuses a partial set, which is why this cost an hour of
machine time rather than a wrong measurement.

### M-2 — The dataset-switch contract of 2026-08-21 and 24, as it stood before the group replac...

<sub>Cut from `MAINTAINING.md`, lines 227–247 of the 2026-09-05 revision.</sub>

**A CHANGE OF DATASET HAS ITS OWN CONTRACT**, settled across
2026-08-21 and 24 and recorded as rulings in CLAUDE.md. In brief for
a maintainer: `switched_from_work` in `_on_layer_changed` decides
what counts as one (leaving a dataset this session has BUILT from --
a recovery, a combo auto-landing and a pre-generate fiddle are all
first choices); `_begin_new_dataset` clears the output path, arms a
fresh group and asks the design-floor question; and
`_swap_dataset_memory` keeps every field-keyed record -- hand-picked
colours, pinned bounds, the scheme shelf -- in PER-DATASET BANKS, so
nothing keyed by one dataset's column names is readable, steering, or
writable to file while another is chosen. Value-laden records never
cross a shared column name; the style (mode, ramp, Reverse, class
count) keeps by name as it always has.

**AND THAT CONTRACT WAS REPLACED RATHER THAN PATCHED, on 2026-08-25.**
Settled by a grilling after a colleague drove the old rules through a
real demo of several datasets in a row, and BUILT the same day, so the
paragraphs above describe machinery that still exists while this one
describes what now governs it.

### M-3 — The build QGIS never started: the 133-second measurement, the three deliberate choices and the undiagnosed cause, in full

<sub>Cut from `MAINTAINING.md`, lines 1396–1435 of the 2026-09-05 revision.</sub>

**AND A BUILD QGIS NEVER STARTS IS SAID TO BE ONE.** A task handed to
`QgsApplication.taskManager()` is ordinarily picked up at once -- 1.4s
answers on `crosses 4` all day -- and on 2026-09-04 one was measured
sitting `Queued` for 133 seconds with the global thread pool reading
`active=0 max=8`, while later dialogs' builds ran normally. Nothing was
running it and nothing was going to, and the tab went on saying
"Working out the design's structure…" at somebody whose question would
never be answered. That is the failure the topology matrix reported as
"the tab neither built a topology nor said why not".

`TOPOLOGY_START_CEILING_MS` arms a watch when the task is added, and
`_say_if_the_build_never_started` writes the reason into the panel's
NOTE -- which means "the answer, or why there is none", and a build
nobody has started is a reason there is none, so every waiter reading
that note gets a real answer instead of sitting out its ceiling on
silence.

THREE THINGS ABOUT IT ARE DELIBERATE. It asks about STARTING and never
about DURATION, so no slow design can reach it: a build under way is
`Running` however long it takes, and `hex-colouring 7` is nineteen
seconds of running. It SAYS rather than cancels, because a pool
genuinely busy with another plugin's work is a legitimate reason for a
queued task to wait -- the sentence is still true there, and the build
lands and clears it. And the watch is keyed to the TASK by identity, so
one armed for a build cannot speak about the build that replaced it.

THE CAUSE IS NOT DIAGNOSED AND THIS DOES NOT CLAIM TO FIX IT. Four
failures in eighty-six attempts here, clustered in one twenty-minute
window and absent from runs of 30 and 16 afterwards, so the condition
is not one this project can yet stage; the STATE it leaves is, and that
is what the guard and its test are aimed at.
`tools/probes/how_often_a_build_never_starts.py` carries the
discriminator that would settle the ownership -- at the stall it adds
a second task and reads whether the stuck one then starts -- and it is
committed because the stall has not yet been caught with it armed.
A PATH IS NEVER HARD-WRAPPED INSIDE ITS BACKTICKS: the gate that reads
these references matches a span on ONE LINE, so a break inside one
hides the path from it altogether -- and the tell is a quotation count
that does not move when you have plainly added a quotation.


### M-4 — The topology drop's four faults, the key that replaced them, the guard that decides nothing, and the stamp's missing modifiers, in full

<sub>Cut from `MAINTAINING.md`, lines 1729–1816 of the 2026-09-05 revision.</sub>

**THE DROP WAS WRONG FOUR TIMES AND WAS REDESIGNED ON 2026-08-31
RATHER THAN PATCHED A FIFTH TIME.** What follows is the four faults,
because they are the argument for the shape that replaced them, and
then the shape.

WHAT ALL FOUR SHARED: each asked whether we MAY drop, and none
recorded WHAT THE TABLES ARE ABOUT. The fact missing was never "does
this design have a topology", which needs a build nobody has run; it
was WHICH DESIGN THE TABLES IN THIS FILE DESCRIBE, which the file can
answer for itself.

SO THE FILE CARRIES A KEY. `topology_design` sits in the same record
the save already writes, beside the two tables, and names the design
they describe: the family, the element count, a digest of the unit's
own options and a digest of the EDIT LIST. A string, because JSON has
no tuple and `_topology_stamp()` is one -- stored directly it would
come home a list and never compare equal again. The edits are in it
because the tables describe the EDITED motif, and with the box off no
build runs while edits are still replayed onto the map, so a design
whose stamp has not moved can have tables describing a motif two edits
old.

THE RULE IS THEN A COMPARISON, and it needs no build:

    wrote both frames                      the key is this design's
    tables present, key DIFFERS, file ours drop both
    tables present, key equal or ABSENT    leave alone, keep its key
    no tables                              nothing to do

A file with no key of ours -- written before this, or a colleague's --
is left alone, which is the line the source copy and the stale-table
drop both hold. And the key is carried FORWARD unchanged when the
tables are spared, because the record has to stay true of the TABLES
rather than of the act that spared them.

**AND ONE GUARD IN THIS METHOD DECIDES NOTHING ANY MORE, WHICH IS
WORTH KNOWING BEFORE SOMEBODY LEANS ON IT.** The branch discarding a
topology of another design was load-bearing while the rebuild happened
HERE; since the build moved off this thread it is not. Measured
2026-09-01, when its catalogue entry survived and the discriminator
was run to the end: the deferral rebuilds wherever the file already
carries our unit table, so the only journey still reaching that line
is a save into a file that does not -- and there, with the branch
removed, the unit written is `self._unit`, the dual is refused for
being another design's, the both-or-neither test declines the write,
and the drop returns on the absent table. Identical file, identical
return, one dump line apart. The code stays because it states the
question where the question is asked and costs one comparison; its
entry is RETIRED with the measurement, since an entry that can only
ever be red is worth less than a retirement that says why. What would
make it load-bearing again is a write taking its unit from the panel's
topology rather than from `self._unit`, or a dual whose stamp stopped
being checked.

**AND THE REDESIGN FOUND A DEFECT UNDERNEATH IT.** `_topology_stamp`
omitted the MODIFIERS. `_queue_topology` builds from `self._unit`,
which is the unit after the modifier chain, and any tile inset opens
gaps that make `Topology` refuse -- so moving an inset left the stamp
identical, a build about the design before it compared equal to the
design after it, and a landing about the wrong design was shown rather
than discarded. The stamp carries them now. A docstring at
`_edited_unit_key` asserted that blindness was deliberate and correct
for judging a build; it was neither, and it is corrected there.

THE FOUR FAULTS, kept because the shape recurs: read this before
touching `_write_or_drop_the_topology`.

- v1 dropped whenever the experimental box was unticked. The box is
  unticked on EVERY new dialog, so opening a saved map and pressing
  Save DELETED its motif.
- v2 guarded with a per-file memory plus a count of box touches.
  Three faults: ticking the box to LOOK at the tab counted as speaking
  about the file; the memory was written only on the LOAD door, so
  adoption was unguarded; and it returned False beside tables it had
  spared.
- v3 -- what is in the tree -- drops only where a build has ASSESSED
  this design and found no topology. But with the box off no build
  runs, so IGNORANCE IS THE PERMANENT STATE of the common journey and
  v3 makes ignorance mean "spare". Measured: save laves, switch to
  hex-slice 4 (which has no topology at all), Save; the file keeps the
  laves motif and its record says `topology_written: True`.
- and the WRITE branch was separately wrong -- a current unit paired
  with a STALE dual -- repaired by stamping the dual and checking the
  stamp matches before writing it.

- and a FIFTH would have been the same shape again. What ended it was
  designing before coding, which none of the four had been.


### M-5 — The synchronous build inside a save, measured at 27.53 seconds, and the deferral that replaced it, in full

<sub>Cut from `MAINTAINING.md`, lines 2090–2123 of the 2026-09-05 revision.</sub>

**AND IT RUNS OFF THE MAIN THREAD, WITH THE PRESS DEFERRED BEHIND IT.**
(Maintainer's decision, 2026-09-01.) It was SYNCHRONOUS until then, on
the argument that the save already turns the event loop behind a
determinate bar with both buttons down, so there was a window to build
in and no press could land in it. The window was real; its SIZE was
taken from a figure of 0.75-4.4s that had already been superseded.
MEASURED, both arms in one run: on `hex-colouring 7` a save took
27.53s of which the build was 27.22, and a 50 ms heartbeat recorded
its longest gap at 27.29s -- twenty-seven seconds without a repaint,
against 1.05s on `laves 3.3.4.3.4` as a control. That is the hang
decision 3 of 2026-08-29 exists to prevent, arriving through the door
that decision opened.
(THE SIZE OF THAT FIGURE IS OPEN. The library's author measures
`chavey K` at about 10s and `hex-colouring 7` at about half that, in a
notebook on a MacBook Air, which is not a faster machine. Whether ours
is this machine's load, our own wrapper or QGIS's bundled shapely is
being measured; what does not turn on the answer is the SHAPE -- a
build of unbounded cost inside a write, on the thread that paints.)
So `_save_the_map` asks `_a_topology_is_owed` BEFORE it writes
anything, queues the build through `_queue_topology(even_if_unasked=
True)`, sets `_save_pending`, and says the map will be saved once the
structure is worked out. `_honour_a_queued_save` -- the third deferred
kind, which the landing already calls -- writes the file when the
build lands. The press is DEFERRED rather than refused for the reason
the maintainer gave on 2026-08-29: most people will not read a
refusal, and a save that quietly did not happen is somebody closing
QGIS believing their map is on disk.
`_topology_built_for` is what stops it deferring twice. It records
which design a build has been ATTEMPTED for, whatever came back, so a
design that has no topology at all -- an inset opens gaps, and
`Topology` needs a gap-free tiling -- defers once, comes back empty,
and is written without one. Asking whether a build SUCCEEDED would
have been a livelock.


### M-6 — The Design tab's layout: the style measurement, the four rows, the withdrawn show-time pass and the two guards, in full

<sub>Cut from `MAINTAINING.md`, lines 1807–1940 of the 2026-09-05 revision.</sub>

## Why the Design tab's controls ran full width, and what decided it

They are added with `QFormLayout.addRow`, and a form layout's field
column stretches to whatever width is going — **under some styles**.
That qualifier is the whole of it, and this document asserted the
sentence without it until 2026-08-30.

**WHETHER A FIELD COLUMN STRETCHES IS DECIDED BY THE STYLE.** The
macOS style's default `fieldGrowthPolicy` is `FieldsStayAtSizeHint`;
Fusion's is `AllNonFixedFieldsGrow`, and QGIS ships Fusion as a style
people select. Measured that day on HEAD and the repair in one run:
under the harness's macOS style every control on that tab ALREADY sat
at exactly its own hint, so nothing stretched and the first guard
written for this passed on the unrepaired code. Under Fusion the same
tree drew the strand-width box — a number between 0.083 and 1.0 — at
1013px against a hint of 63, and the region chooser at 1013 against
29. That is what the maintainer met.

So the cause was right and the sentence was not, which matters because
the sentence was a READING and read exactly like a measurement. It had
reached two binding documents before anything measured it.

**THE REPAIR IS PER ROW AND STYLE-INDEPENDENT**: each field is laid out
with a stretch after it, so the control sits at the width it asks for
whatever the style would have done. `_form_row` carries it for the six
family options, `pair` for the modifier pairs, and the kind, family,
spacing and Auto row shares one line with a stretch at the end. The
spacing box also asks for less: a spin box's hint comes from its
MAXIMUM's text, and 1e12 at six decimals is twenty characters.

**AND IT REACHED ONLY THREE ROWS OF FOUR, WHICH IS THE MAINTAINER'S
REPORT OF 2026-08-30** ("the alignment and spacing and sizing of these
UI elements is just nonsensical"). `Region layer`, `QGIS Layer Group`
and `Number of elements` were added with a bare `form.addRow`, so they
had NO WIDTH POLICY AT ALL and took whatever `fieldGrowthPolicy` the
style supplied. Measured on one tree, one run each:

    control            macOS (the report)   Fusion    own hint
    Region layer       33px stub            861px     33
    QGIS Layer Group   ~180px               861px     99
    element slider     84px stub            802px     84
    Pattern row        correct              correct   --

A stub too narrow to show a layer's name is the worse of the two wrong
answers, and it is the one the maintainer was looking at. So the
POLICY IS SET EXPLICITLY on both forms now, by `_settle_a_form`, and
the widths come from the controls: `_ask_for_a_name_s_width` gives the
two choosers `NAME_CHARACTERS` of room -- in characters, because a
pixel width is a claim about one machine's font -- and the slider asks
for the same, so the three top rows end at one edge.

FOUR MORE CAME WITH IT, all style-independent and all measured. The
seven modifier boxes were seven widths (59, 43, 43, 51, 51, 43, 37),
because a spin box sizes to its MAXIMUM's text and Rotate reaches
360.0 where the tile inset reaches 5.0; they take the widest of the
seven at run time, which also lands the second column at one x instead
of three. The two blocks had independent label columns, since they are
separate forms in a QVBoxLayout. A HIDDEN FAMILY-OPTION ROW KEPT ITS
HEIGHT, because a form reserves space for a row whose field is a
LAYOUT and `_form_row` wraps every option in one -- which is a block of
dead space above Transformations that CHANGES SIZE WITH THE FAMILY;
`_set_option_row_visible` uses `setRowVisible` and falls through to
hiding both widgets where that call is unavailable. And `Auto` was
Qt's default button, so macOS painted it in the accent colour, making
the loudest thing on the tab a convenience.

**A SHOW-TIME PASS FOR THE LAST THREE PIXELS WAS TRIED AND WITHDRAWN,
and the shape is the one this file already records.** Equal label
WIDTHS are not one column when the group box frames its own form, and
that offset is unknowable before a layout pass. Measuring the real
right edges in `showEvent` and widening the short labels is a FEEDBACK
LOOP: the widened labels grow their form's shared column, the furthest
edge moves with them, and the next show does it again -- 1296px to
1618px in one run. That is the third of the four failed repairs to
this same layout wearing new clothes, and the rule is the same: the
approach is wrong rather than the constant. The reasoning is kept at
the code so nobody writes it a second time.

**TWO GUARDS FAILED ON THE REPAIR AND BOTH WERE THE TESTS.**
`test_no_design_control_is_stretched_to_the_window` used the region
chooser as its POSITIVE CONTROL, on the reasoning that it "is meant to
take the width going" -- so its proof that the measurement works was
the defect itself, and it could no longer fail once the chooser asked
for a width. It stands on the glyph checkbox now, which spans its row
by construction. And `test_the_window_fits_its_design_tab_when_shown`
assumed the Design tab is the tallest page in the window; once it
stopped reserving the hidden rows' height another tab became taller,
and `resize` is refused below `minimumSizeHint`. It quotes that floor
from Qt rather than writing it down.

**AND THE GUARD SETS THE STYLE**, because it otherwise measures
nothing: `test_no_design_control_is_stretched_to_the_window` switches
to Fusion, compares each control's width with what it ASKED for
(the larger of its hint and its own minimum), asserts the region
chooser DOES take the width as a positive control, and restores the
style in a `finally`. Setting the style is the same move as setting a
font to reach a column measurement — ask what the other machine has,
and set that quantity directly.

**AND THE WINDOW IS SIZED BY THE TAB IN FRONT, not by the widest one.**
(Maintainer's ask, 2026-08-30: the first tab should open narrower, and
opening a wider tab should expand the window.) A QStackedWidget's
minimum is the LARGEST of its pages, so while the assignment table
exists on Data & colours the window could not be narrower than that
table whichever tab was showing -- and a 1180px floor inside
`_fit_to_design` made certain of it. `_size_to_the_current_tab` makes
the page in front `Preferred` and every other `Ignored`, so the stack
follows the current page; `_width_for_the_current_tab` adds what sits
BESIDE the tabs, measured from the window rather than written down.
Measured: Design asks 550px and opens the window at 825, where it used
to open at 1296; choosing Data & colours grows it to 1296.
IT GROWS AND DOES NOT SHRINK, deliberately -- a window that contracted
as well would resize under the pointer on every tab click, and the ask
was for a narrow start rather than a window that follows you about.

**AND FOUR ROWS SHARE ONE FIELD WIDTH.** `_field_block` puts a row's
controls in a holder fixed to `_field_width`, which the region chooser
sets from its own sizeHint -- a combo's hint is font metrics rather
than layout, so it is honest before a layout pass and can be settled
at construction. Region, group, elements and Pattern therefore end at
one edge. `FieldsStayAtSizeHint` alone gives each field its own hint,
which is what stops this tab running the width of the window and is
also why four rows built from different controls ended at four
different edges; `AllNonFixedFieldsGrow` lines them up by making every
one as wide as the window, which is the defect that started all this.
A block of a known width is the third answer.

**It is coupled to the assignment table's budget.**
`COLUMN_SUM_BUDGET` is `MAX_WINDOW_WIDTH - 400`, where the 400 is a
measured allowance for everything that is not the table, and the
budget is bracketed between about 1030 and 1118 on that basis. Narrow
the Design tab and that allowance changes, so the two are re-derived
together or not at all.


### M-7 — The chained patches and the fixed-point self-check they broke, in full

<sub>Cut from `MAINTAINING.md`, lines 2104–2130 of the 2026-09-05 revision.</sub>

**AND TWO PAIRS OF THEM CHAIN, which decides how the tool reads.**
Patch 6 anchors on the block patch 3 produces, and patch 5b on the
tail of the method patch 4b produces. That is fine on a re-vendor --
patches run in order and each later one anchors on its predecessor's
output -- and it broke the CHEAP SELF-CHECK, which is the thing worth
knowing here. Run the tool with our OWN vendor as its upstream and
every patch should report "already present"; that is what catches a
vendored file somebody has hand-edited, and
`test_the_vendoring_tool_reproduces_the_current_vendor` asserts it.
A superseded patch cannot say that about its whole patched form,
because a later patch has rewritten it, so patches 3 and 4b reported
"anchor not found" instead -- the sentence reserved for an anchor
UPSTREAM has moved, and the one message a re-vendorer has to be able
to trust. Measured 2026-09-04, on a vendor the tool had itself
produced.

So `targeted` takes `superseded_by` and `landed` TOGETHER: the label
of the later patch, and the smaller piece of its own work that the
later one leaves standing. The tool asserts that such a mark is text
the patch itself writes and is NOT text the anchor already carries --
without the second, a patch would read as already present against
pristine upstream and silently never apply -- so a badly chosen mark
fails on the first run rather than sitting there. The report says
which question it asked. A mark is a WEAKER test than the whole
patched form, and that price is stated at the function; it falls only
on the two patches that are chained.
