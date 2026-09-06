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
- **M-2** — The dataset-switch contract of 2026-08-21 and 24, as it stood before the group replac...  <sub>Architecture: superseded contracts</sub>
- **M-3** — The build QGIS never started: the 133-second measurement, the three deliberate choices ...  <sub>The light pass of 2026-09-05</sub>
- **M-4** — The topology drop's four faults, the key that replaced them, the guard that decides not...  <sub>The light pass of 2026-09-05</sub>
- **M-5** — The synchronous build inside a save, measured at 27.53 seconds, and the deferral that r...  <sub>The light pass of 2026-09-05</sub>
- **M-6** — The Design tab's layout: the style measurement, the four rows, the withdrawn show-time ...  <sub>The light pass of 2026-09-05</sub>
- **M-7** — The chained patches and the fixed-point self-check they broke, in full  <sub>The light pass of 2026-09-05</sub>
- **M-8** — Reading shards: the verdict line, the shard that died at startup, and the three things ...  <sub>The fourth pass of 2026-09-05</sub>
- **M-9** — The coverage report's history: off the release path, and the os._exit that kept it from...  <sub>The fourth pass of 2026-09-05</sub>
- **M-10** — The hardcoded macOS paths, and the wrong prefix that left QGIS with no ramps  <sub>The fourth pass of 2026-09-05</sub>
- **M-11** — The retirement of _fresh_group_for_new_data, the first build's conflation, and the repo...  <sub>The fourth pass of 2026-09-05</sub>
- **M-12** — Ledger row 28, and the empty dump of 2026-08-19 that settled a report six reproductions...  <sub>The fourth pass of 2026-09-05</sub>
- **M-13** — The two moments of the save's record, got wrong twice in one evening  <sub>The fourth pass of 2026-09-05</sub>
- **M-14** — The drop that put the un-edited design back: the measurements, the three exits, and the...  <sub>The fourth pass of 2026-09-05</sub>
- **M-15** — The held landing was found from a runner: one run in eight here, three legs failing on ...  <sub>The fourth pass of 2026-09-05</sub>
- **M-16** — The colleague's save that took an element out of a shared file, and the dropped table t...  <sub>The fourth pass of 2026-09-05</sub>
- **M-17** — Load live through every write until 2026-09-02: the paragraph that named a pair, and th...  <sub>The fourth pass of 2026-09-05</sub>
- **M-18** — The save's three doors after 2026-09-02: the nine repairs with their measurements, as t...  <sub>The fourth pass of 2026-09-05</sub>
- **M-19** — The resume that stamped the group and not the layers, reproduced at both doors  <sub>The fourth pass of 2026-09-05</sub>
- **M-20** — The cancel button briefly disabled during the write, and the maintainer's choice to shi...  <sub>The fourth pass of 2026-09-05</sub>
- **M-21** — The cancel that poisoned the next save: the measurement and the general form  <sub>The fourth pass of 2026-09-05</sub>
- **M-22** — Two senders' maps open at once: the chooser that found nothing and the Save that would ...  <sub>The fourth pass of 2026-09-05</sub>
- **M-23** — The one flag two kinds of request shared until 2026-08-28, and the press discarded in s...  <sub>The fourth pass of 2026-09-05</sub>
- **M-24** — The topology build's cost: the 0.75-4.4 figure this paragraph carried, and the synchron...  <sub>The fourth pass of 2026-09-05</sub>
- **M-25** — Greying the tab during a build, tried and withdrawn, and the third meaning written into...  <sub>The fourth pass of 2026-09-05</sub>
- **M-26** — The zigzag repair: the library author's words, the paired measurement, and the supersed...  <sub>The fourth pass of 2026-09-05</sub>
- **M-27** — The 2026-08-30 rebuild of the tab: select then act, the handles, the three highlight st...  <sub>The fourth pass of 2026-09-05</sub>
- **M-28** — The 2026-08-31 rebuild: the unit fit, the glyphs, the position-not-delta lever and the ...  <sub>The fourth pass of 2026-09-05</sub>
- **M-29** — Turn and zigzag 20.4px apart inside a 26px reach, and the other side of the edge tried ...  <sub>The fourth pass of 2026-09-05</sub>
- **M-30** — What a drag means: the four disagreements of 2026-09-01 with their measurements, in full  <sub>The fourth pass of 2026-09-05</sub>
- **M-31** — _same_shape's three wrong forms  <sub>The fourth pass of 2026-09-05</sub>
- **M-32** — The two doors to a new group, the readers that disagreed, and the checkbox's retirement  <sub>The fourth pass of 2026-09-05</sub>
- **M-33** — The vendoring record of 2026-08-31: twelve commits under one version string, and the tw...  <sub>The fourth pass of 2026-09-05</sub>
- **M-34** — The live path's refusal of a repaint, the ten named gates, and the two diagnoses silenc...  <sub>The fourth pass of 2026-09-05</sub>


## Long jobs: the accounts behind the rules

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

### M-8 — Reading shards: the verdict line, the shard that died at startup, and the three things that make a sharded suite trustworthy, in full

<sub>Cut from `MAINTAINING.md`, lines 49–75 of the 2026-09-05 revision.</sub>

**AND A SHARD'S VERDICT IS NOT ITS LAST LINE.** (2026-08-30.) Read for
the verdict LINE, not for the end of the file, and where there is no
verdict line say so in those words: a shard that died and a shard whose
last line is noise look identical to a naive tail, and only one of them
is a problem.

**AND A SHARD CAN DIE AT STARTUP, WHICH LOOKS LIKE NOTHING AT ALL.**
(2026-08-28.) One of three coverage recorders met FileNotFoundError
before it ran a single test; the other two ran on and the progress total
climbed. SO READ SHARDS SEPARATELY, NEVER ONLY THEIR SUM -- the fault
was visible as an asymmetry (nineteen, thirty, and nothing) and
invisible in the sum. `tools/merge_coverage_shards.py` is the backstop
rather than the detector: it counts the files against the total each one
names and refuses a partial set. Both faults in full: M-1.

Three things make it trustworthy rather than merely fast. Each shard
prints how many tests it was OFFERED, and those totals must agree:
the first sharded run read 285, 285 and 286, which is not a
partition, and the cause was a test that registers a probe of its
own consuming a slot. A registration made from inside a test now
passes `sharded=False`. The merge of the coverage shards REFUSES a
partial or overlapping set, because an incomplete coverage record
never offers the missing tests the chance to notice a mutant and
overstates survivors silently. And every stall ceiling widens by two
and a half times whenever a shard is in force, against a measured
contention cost of 15-50%.


### M-9 — The coverage report's history: off the release path, and the os._exit that kept it from writing at all

<sub>Cut from `MAINTAINING.md`, lines 95–95 of the 2026-09-05 revision.</sub>

| `tools/coverage_report.py` | Which plugin lines the suite never reaches. Run it when you are deciding where to write tests; it left the release path on 2026-08-12, having cost half an hour a candidate and gated nothing. It could not write a report at all until 2026-08-13: the suite ends in `os._exit`, so everything after the call was unreachable and the documented command produced nothing. |


### M-10 — The hardcoded macOS paths, and the wrong prefix that left QGIS with no ramps

<sub>Cut from `MAINTAINING.md`, lines 160–169 of the 2026-09-05 revision.</sub>

That script does not know where anything is. It calls
`tools/macos_qgis_env.sh`, which finds the app bundle, finds an
interpreter that will actually start, and works out `PYTHONHOME` and
`QGIS_PREFIX_PATH` by trying them — the macOS CI job calls the same
script, so the runner and this machine cannot drift apart about how
to start QGIS's Python. Both paths were hardcoded here until
2026-08-15, and the prefix was wrong, which left QGIS with no colour
ramps at all on any machine whose profile had not already been seeded
by the plugin.


### M-11 — The retirement of _fresh_group_for_new_data, the first build's conflation, and the report that prompted the replacement

<sub>Cut from `MAINTAINING.md`, lines 310–322 of the 2026-09-05 revision.</sub>

`_fresh_group_for_new_data` retired with it: the protection it gave
comes from which group is SELECTED now, which is a fact on screen
rather than a flag. What replaced it is narrower and means one thing
-- `_new_group_chosen` is set only when somebody picks "create new" --
and the first build conflated the two, which put a file-overwrite
warning in front of an ordinary journey.

The reason the replacement was worth its cost is one sentence of the
report that prompted it: three scopes -- records kept per dataset, a
design carried globally, a group remembered nowhere -- answered a
single act in three different ways, and none of the three was named on
screen. The rulings are in CLAUDE.md, where they bind.


### M-12 — Ledger row 28, and the empty dump of 2026-08-19 that settled a report six reproductions could not

<sub>Cut from `MAINTAINING.md`, lines 421–431, lines 432–447 of the 2026-09-05 revision.</sub>

This is why a maintainer could add a class and watch the plugin follow
it, then recolour a class and watch nothing happen: the two actions
take different routes inside QGIS's own panel. Ledger row 28, which
had been read as a consequence of a failed Generate for a day, on
evidence that was true of one session and not of the next.

The consequence for anyone reading a dump: the plugin calls
`_on_layer_style_edited` DIRECTLY in a couple of places as well as
from the signal, so a `HEARD` line is not by itself evidence that
QGIS told us anything.

**So a session whose Generate has never succeeded hears nothing.** On
2026-08-19 a maintainer reported a class recoloured in QGIS reaching
the map and neither the plugin's swatch nor its colour editor. Six
reproductions on their own data all worked; what settled it was a dump
from their session, which was EMPTY -- their Generate had failed, no
run had landed, and no layer was watched. QGIS repainted the map
because QGIS owns the layer, and the plugin was simply never told.

Two things follow. When a dock edit appears not to reach the plugin,
ask FIRST whether a run has landed in that session, because the answer
is often that nothing is connected rather than that something is
broken downstream. And when adding a third route by which element
layers come into existence, connect the watch there too -- a layer the
plugin holds but does not hear is worse than one it does not know
about, since the table goes on describing a map that has moved.


### M-13 — The two moments of the save's record, got wrong twice in one evening

<sub>Cut from `MAINTAINING.md`, lines 489–496 of the 2026-09-05 revision.</sub>

That split was got wrong twice in one evening, both times by carrying
too little: the design and region alone, so the record named a
variable its own tiles were not drawn with; and then those plus the
variable but not the element LIST, so lowering the element count left
a record claiming `n=4` beside two elements and a file holding four
tables. Whenever you add a key to this record, ask which of the two
moments it is about.


### M-14 — The drop that put the un-edited design back: the measurements, the three exits, and the survivor

<sub>Cut from `MAINTAINING.md`, lines 661–692 of the 2026-09-05 revision.</sub>

`_commit_the_drag` used to open with `show_preview(None)`, so the
edited geometry a person had been dragging was cleared AT THE DROP --
and the rebuild that answers an edit is asynchronous, so until it
landed `_drawn` fell back to `_topology`, which is the UN-EDITED
design. That is the field report against 0.24.4rc15: "it reverts for a
second and then a few seconds later updates correctly". Measured on
`laves 3.3.4.3.4`, the old design stood for 1.676 seconds and the
settled drawing was IDENTICAL to what the preview had been showing, so
the right picture was thrown away and recomputed; on `hex-colouring 7`,
whose build is nineteen seconds, it is nineteen seconds of the wrong
design under somebody's hand.

**THE PREVIEW IS KEPT WHERE AN EDIT WAS RECORDED**, and the landing is
what clears it -- `show_topology` sets `_preview = None` as its own
third line, and every route to an answer passes through it. So the
preview stands exactly as long as there is nothing better to draw.

**AND EVERY PATH THAT RECORDS NOTHING STILL CLEARS AT ONCE**, which is
why this is a decision per exit rather than one line moved. A press
that never grabbed anything, a selection the tab cannot act on and a
gesture with no travel each leave a preview describing an edit the
record does not hold, with no landing coming to correct it -- the fault
`show_preview` was split from `show_topology` to prevent. The three
exits are three journeys, and an entry aimed at one of them SURVIVED
until the test grew an arm that walked it: a click that merely selects
leaves at the first exit and never reaches the travel test at all.

WHAT IS LEFT OPEN DELIBERATELY is a record with no rebuild behind it.
The preview then goes on showing what the person asked for, which
agrees with the change list; reverting would show a design the list
denies.


### M-15 — The held landing was found from a runner: one run in eight here, three legs failing on the same premise

<sub>Cut from `MAINTAINING.md`, lines 709–714 of the 2026-09-05 revision.</sub>

**IT WAS FOUND FROM A RUNNER.** It shows here about one run in eight,
and macOS, Linux 4.0.3 and Linux 4.0.0 all failed the drag guard on
its own premise -- "the drag drew no preview at all", 730 passed and 1
failed, three times over. A stack printed from a patched
`show_topology` named the caller on the first failing attempt.


### M-16 — The colleague's save that took an element out of a shared file, and the dropped table that still answered featureCount 40

<sub>Cut from `MAINTAINING.md`, lines 747–780 of the 2026-09-05 revision.</sub>

A layer whose source already names a table in this file is treated as
saved already -- correctly, and not as an edge case: it is the SECOND
press on any map, because the first repoints every layer at the file.
The data needs no writing because it is already there; what still has
to happen is the style, the name counted as current so the drop spares
it, and the record.

Since 2026-08-29 that question is put to the FILE and not to the
source string alone, because nobody rewriting the file underneath us
can change a string we are holding. A colleague saving the shared
GeoPackage while your map is open -- moving one element to another
column, so their save writes `tiles_b_v1` and drops
`tiles_b_landcover` -- left your layer naming a table that was gone.
Every such element was skipped as already saved AND counted as
written, and the stale-table drop then removed what they HAD written,
because it belongs to an element this map has and was not among the
names just written. The element left the file altogether, both people
lost it, and the plugin said "Saved".

**Nothing can be written in its place, and that is measured rather
than assumed.** A layer whose table was dropped under it answers
`isValid` True, `dataProvider().isValid()` True and `featureCount()`
40 -- and yields ZERO features. Writing it would replace a real table
with an empty one.

So the save writes what it can, REMOVES NOTHING, and says which
element the file lost. Once a file has changed under us, our record of
what is stale is worth nothing: a table that looks like our own
abandoned one is just as likely to be their current one, and nothing
here is deleted on a guess. The reading of what the file holds is
taken ONCE, before the loop, because asking per element opens the
GeoPackage per element -- the quadratic the style pass was moved out
of that loop for.


### M-17 — Load live through every write until 2026-09-02: the paragraph that named a pair, and the measurement

<sub>Cut from `MAINTAINING.md`, lines 789–800 of the 2026-09-05 revision.</sub>

**AND IT IS EVERY CONTROL THAT ACTS, WHICH IS A LIST RATHER THAN A
PAIR.** The paragraph below named Save and Generate, correctly when it
was written and incompletely from 2026-08-27, when LOAD arrived on the
row beneath Save. It was live for the whole of every write and every
resume, at both acts that pump -- measured 2026-09-02 at each of a
write's twelve beats -- and a Load delivered by the save's own pump
repoints every element layer mid-loop, so the other map's tiles go
into this file's tables and its record names the other file as this
one's output path. `CONTROLS_A_PUMP_TAKES_DOWN` is the list now, taken
and restored by one owner both acts call, so a fourth control joins a
list rather than being remembered at two sites.


### M-18 — The save's three doors after 2026-09-02: the nine repairs with their measurements, as the section stood

<sub>Cut from `MAINTAINING.md`, lines 814–915 of the 2026-09-05 revision.</sub>

Seven defects were repaired in one campaign day and five of them were
in the save. What follows is what a maintainer needs to hold in their
head about it, because the pieces only make sense together.

**A CANCEL HAS THREE MOMENTS AND THEY ARE ANSWERED DIFFERENTLY.**
Before the write opens the file, dropping the intent IS the rollback.
Between tables, `write_gpkg_layers` reads `_save_cancelled` and undoes
the transaction. AFTER the last table -- during the repointing or the
styling, which is 13.0s of a 256-element save -- nothing reads it at
all, so what matters there is that the flag does not survive: it is
cleared where the act ENDS, in the same `finally` as `_saving_now`.

**AND THE HOLD DECLINES WHERE IT CANNOT BE SERVED.** The write turns
the event loop once per element, so a close or a quit arriving during
one is delivered by THAT WRITE'S OWN PUMP and the hold would run
nested inside it -- waiting for `_saving_now`, which only the
suspended frame beneath can clear. It returned at the ceiling rather
than at the save, with the bar frozen and the only button on the
window throwing the map away. `_hold_until_the_save_lands` returns
True at once where `_saving_now` is set: the save is running, nothing
is lost, and it lands the moment the hold returns.
WHAT THAT MOVES rather than removes is where a mid-write cancel is
reachable. A save that is merely PROMISED still opens the window, the
run lands inside that window's own pump, and the write happens there
-- so the button is live exactly where the writer can still read it.
The guard for the mid-write cancel is staged on that journey for the
same reason.

**AND A REFUSED COMMIT IS NOT A SAVE.** OGR answers by RETURN VALUE
rather than by raising, so the `except` around `CommitTransaction`
could not fire and its answer went unread. With a shared read
transaction open on the file, every table goes in, the commit is
refused, and `written` still named all of them -- so every element
layer was repointed at a table that had never been created, the map on
screen emptied, and the person was told "Saved". The answer is read
now and `written` is cleared, which is the same sentence the rollback
branch beside it has always carried.
THE TWO WAYS A LOCK BITES ARE NOT THE SAME, and it matters when you
reproduce this: a WRITE lock held by another process fails at the
first feature and is reported correctly; only a SHARED READ
transaction reaches the commit.

**AND OWNERSHIP IS ABOUT WHAT A FILE HOLDS.** `existed` asked the
file's SIZE, and a data source OGR created and nothing wrote to is
65,536 bytes holding no layer -- so a stub left by a cancelled or
failed first save read as somebody else's work, and the answer is
cached for the session. Every remover scoped to our own files stayed
off, and shrinking a design then left the dropped elements' tables,
columns and values in the file a colleague receives. It asks
`bridge.gpkg_tables` now, and the guard asserts BOTH directions,
because a repair that made every file ours would destroy somebody's
work.

**AND A PRESS WAITS FOR A BUILD ALREADY COMING.** `_a_topology_is_owed`
asks THE FILE, which is the cost ruling of 2026-08-30 and is right
about whether to START a build. It was the wrong question about one
already running: a Save pressed while a topology build was in flight
wrote no motif and recorded `topology_written: False`, where the same
press a second later wrote the unit and its dual. It now answers True
while a build is running or queued -- it still starts none, so nobody
who has not opened the tab pays anything.

**AND THE CLOSE'S QUESTION IS ANSWERED WITH THE RIGHT MECHANISM.**
`_a_save_is_outstanding` merges a promise made with the keeping of it,
which is right for the hold and wrong for a QUESTION: during a write
there is no promise to drop, so the Close arm cleared a flag that was
already False, said nothing had been written, and let the write finish
over the file the person had just declined -- repointing every element
layer at it. It sets `_save_cancelled` now, which is the same
mechanism the waiting window's Cancel uses, and the SENTENCE is the
writer's, because ours cannot be true past the last table.

**AND THE HOLD ONLY REPORTS WHAT IT WATCHED.** Past the last table
nothing reads the flag, so a Cancel landing during the styling or the
repointing cannot be served and the save completes. The hold used to
report it anyway: resuming, it read `_saving_now` as False and could
not tell a write that had just FINISHED from a wait where nothing was
ever opened. It records whether a write was under way AT THE PRESS --
the only moment that can be known -- and leaves the report to the
writer, which speaks in both cases.

**AND A FILTER NEVER REACHES THE FILE.** `write_gpkg_layers` iterates
`getFeatures()`, which honours a layer's subset, so a filter set in
QGIS's Query Builder was written as though it were the map: 41 rows to
3 between two saves, and to ZERO across a re-tile, where the plugin
carries the filter onto the new layer and it names ids the new tiling
never produced. A subset says which features to DRAW, which the line
that carries one across a re-tile says in as many words, so it comes
off for the write and goes back in the save's own `finally` -- the
cancel branch returns between the two, and an exception may leave by
neither door. The already-saved question is asked without the subset
too, so a filtered layer is recognised as reading from its own table.

**AND THE LAYER IS THE AUTHORITY ON WHAT ITS TABLE IS CALLED.**
`_element_tables` is filled by a LANDING and cleared by nothing, so a
session that has drawn any map carries that map's names -- and an
opened map's elements share their ids with it. The witness is asked
for EVERY element now rather than only for those the record has never
heard of, which costs a drawn map nothing: its layers read from memory
at the first save and from those very names afterwards, and a Save As
is answered None by construction.


### M-19 — The resume that stamped the group and not the layers, reproduced at both doors

<sub>Cut from `MAINTAINING.md`, lines 885–903 of the 2026-09-05 revision.</sub>

`_recover_the_source` returns the source it LANDED ON, and the group's
record is stamped with that rather than with the record's own region
-- a self-contained file names the SENDER'S path, and nothing on the
recipient's machine answers to it.

`_our_groups` asks the LAYERS. So stamping the group alone left the
two disagreeing about which dataset the map came from: `theirs` came
back empty, `_bind_group_to_dataset` let go of the map just opened,
and the next Generate built a rival group beside it whose Save wrote
into the opened map's own tables.
`_tell_the_layers_which_region_we_landed_on` is called from both
branches, and it stamps NOTHING where the recovery landed on nothing,
since writing the record's own region would put the sender's path onto
the recipient's layers.

IT REPRODUCED AT BOTH DOORS, which is what said the defect was older
than the flag that revealed it: `_landed_this_session` decides only
whether the binding is reached at all.


### M-20 — The cancel button briefly disabled during the write, and the maintainer's choice to ship the callback

<sub>Cut from `MAINTAINING.md`, lines 962–968 of the 2026-09-05 revision.</sub>

THE BUTTON WAS BRIEFLY DISABLED DURING THE WRITE INSTEAD, which was
honest about what it could do and worse than doing it. The maintainer
chose to ship the callback (2026-09-01) rather than defer it, on a
branch about to be a candidate, which is worth recording: the
alternative was a control that greys itself at the moment somebody
most wants it.


### M-21 — The cancel that poisoned the next save: the measurement and the general form

<sub>Cut from `MAINTAINING.md`, lines 972–989 of the 2026-09-05 revision.</sub>

**AND THE FLAG DOES NOT OUTLIVE THE ACT IT WAS SET FOR**, which is the
half that was missing until the guard for the button was written the
same day. `_save_cancelled` exists to be read BETWEEN TABLES by
`write_gpkg_layers`, and on the commonest journey of all -- a wait for
a REDRAW or a topology build -- nothing ever opens the file, so nothing
ever consumes it. Left standing it stopped the person's NEXT save:
measured 2026-09-01, cancel a deferred press, press Save again, and
the writer halts at its first table, rolls back, and reports "The save
was stopped, so the map was not written" to somebody who stopped
nothing. It is cleared where the intent is dropped, which is safe in
both directions: a write that DID read it has already returned by
then, since the pump that delivered the click sits inside that write
and `_save_the_map` resets the flag on its own way out.
THE GENERAL FORM, and it is this project's deferred-work rule wearing
a flag: when a repair adds state read by ONE consumer, enumerate the
journeys where that consumer never runs, and say at the line what
clears it there. Guarded by `a-cancel-does-not-poison-the-next-save`.


### M-22 — Two senders' maps open at once: the chooser that found nothing and the Save that would have followed

<sub>Cut from `MAINTAINING.md`, lines 1014–1029 of the 2026-09-05 revision.</sub>

The third route is why this matters. A self-contained file records the
region its SENDER drew from, which on their machine is an ordinary
layer and on the recipient's is a path that does not exist. Stamp the
group with the record and nothing in the recipient's project ever
answers to it: `_point_the_chooser_at` walks for a matching layer,
finds none, and leaves the chooser silently where it was. With two
senders' maps open, returning to the first through the group chooser
gave it the SECOND sender's data -- and the output path coming home
correctly is what made it worse, since the next Save would have
written that over the first sender's file.

The fallback to the record survives for the case it was written for:
where recovery lands on NOTHING the chooser still names another
dataset, and capturing that would file the resumed group under a
dataset it was not made from.


### M-23 — The one flag two kinds of request shared until 2026-08-28, and the press discarded in silence

<sub>Cut from `MAINTAINING.md`, lines 1067–1079 of the 2026-09-05 revision.</sub>

One run at a time is settled, so anything asking for a run while one is
in flight is REMEMBERED and honoured when that run lands. What was
wrong until 2026-08-28 is that both kinds of request shared one flag.

`_generate` queued a press on `_live_pending`; `_finish_run` honoured
that by starting the LIVE timer; and `_maybe_live_generate` returns at
its second gate whenever live update is switched off. So with the box
unticked a button press was remembered and then discarded in silence:
the map kept the elements of the run in flight while the table asked
for the design the person had just chosen, and layers stayed in the
panel tagged for elements that design no longer had -- which is what a
later dialog adopts a group by.


### M-24 — The topology build's cost: the 0.75-4.4 figure this paragraph carried, and the synchronous save it justified

<sub>Cut from `MAINTAINING.md`, lines 1236–1253 of the 2026-09-05 revision.</sub>

**The topology is built off the main thread**, in `_topology_task`,
because `Topology.__init__` is eager: eight setup passes and a dual
graph. THE FIGURE TO USE IS 0.8 TO 21 SECONDS, not the 0.75-4.4 this
paragraph carried until 2026-09-01: nobody had run the catalogue far
enough up to meet `hex-colouring 7`, which is seven tiles with
forty-two corners between them and takes about nineteen. The narrower
figure is what justified building inside a save, and that decision
cost twenty-seven seconds of frozen window before it was measured.
docs/TOPOLOGY.md carries the spread, the decomposition that exonerates
our wrapper, and the five arms that show the ordering itself belongs
to the LIBRARY rather than to this machine. It is queued by whatever rebuilds the UNIT and never by a
colour or a ramp, which is the same boundary `_geometry_signature`
already draws for re-tiling — a restyle changes no edge, so asking for
a topology on one would cost seconds for a picture that cannot have
moved. `_topology_stamp` is what tells a landing whose topology it is
holding, so a build that finishes after the design has moved on is
discarded rather than drawn against a unit it does not describe.


### M-25 — Greying the tab during a build, tried and withdrawn, and the third meaning written into the note

<sub>Cut from `MAINTAINING.md`, lines 1256–1268 of the 2026-09-05 revision.</sub>

GREYING THE TAB WAS TRIED FIRST AND TAKEN OUT THE SAME HOUR
(maintainer, 2026-09-01: "it doesn't have to grey, that seems to make
trouble"). It takes the tab away from somebody mid-edit for as long as
a build lasts, and it retires a contract two registered tests state
outright -- ticking the box makes these tabs usable. Both went red.

AND IT IS ITS OWN LABEL RATHER THAN `note`, which is the part worth
remembering. `note` already means "the answer, or the reason there is
none", and the suite's `_settle_topology` treats a non-empty note as
an answer having ARRIVED. Writing a third meaning into it made that
waiter return before the build landed, and a test then read a class
list that did not exist yet. One store, two meanings, met in a QLabel.


### M-26 — The zigzag repair: the library author's words, the paired measurement, and the superseded sentence

<sub>Cut from `MAINTAINING.md`, lines 1285–1307 of the 2026-09-05 revision.</sub>

**THE REPAIR IS UPSTREAM'S OWN, and that is a correction of 2026-08-30
rather than the original design.** `tiling_utils.get_clean_polygon`
removes corners that are merely VERY CLOSE and then the COLINEAR ones;
this module's exact dedupe only ever removed exact repeats. The
library's author named it — "I can recover valid polygons from the ones
it makes with `tiling_utils.get_clean_polygon`", and "there's probably
some doubling up of coordinates happening", which is the same fault
this project had measured independently, confirmed from the side that
wrote the manipulation.

MEASURED AS A PAIR, both arms in one run
(`tools/probes/zigzag_cleaners.py`): with our dedupe alone,
`laves 3.3.4.3.4` and `hex-slice 4` REFUSE and `hex-slice 3` and
`chavey K` draw. With upstream's cleaner first, ALL FOUR draw with no
invalid geometry. So the sentence that used to stand here — that two of
the four still refuse — is superseded, and zigzag now applies wherever
it has been tried.

OURS IS KEPT AS THE FALLBACK rather than deleted, because this is a
VENDORED dependency: a re-vendor that dropped or renamed that function
would otherwise take the repair with it in silence. `make_valid` still
runs on whatever residue survives both.


### M-27 — The 2026-08-30 rebuild of the tab: select then act, the handles, the three highlight states and the hit test, in full

<sub>Cut from `MAINTAINING.md`, lines 1301–1338 of the 2026-09-05 revision.</sub>

**SELECT, THEN ACT.** A click lands on whatever is under the pointer,
whatever the controls happen to say. `_refresh_classes` lists every
class of BOTH kinds and `_refresh_manipulations` narrows the VERB to
what suits the selection -- the opposite of the arrangement it
replaced, which filtered the class list by the current manipulation
and so made the tab mode-first. With the default manipulation aimed at
vertices, clicking an edge moved nothing in the panel WHILE THE
DRAWING WENT ON HIGHLIGHTING IT: one fact, two stores, disagreeing on
screen, which is this project's commonest defect shape.
`_rebuild_arguments` no longer refills the class list -- that call
existed because the list depended on the verb, and now the two would
recurse without end.

**A HANDLE IS THE CHOICE OF MANIPULATION.** `_EDGE_HANDLES` puts a
square at the end that stretches, a circle offset from it that swings,
and a diamond offset from the middle that bows out; `view.grabbed`
carries the manipulation to the panel, which sets its own chooser from
it. So the handle and the chooser cannot disagree, and the tab is
usable without touching the chooser at all. The arrangement before
this had the drag mean whatever the chooser said -- a mapping that
exists only in the code, so nothing on screen said a drag would do
anything, or what.

**THREE HIGHLIGHT STATES, BECAUSE AN EDIT APPLIES TO A CLASS.** The
one being held is strong, its classmates are tinted, and what is under
the pointer is a third colour. Two states said only "these all change"
and lit about half the drawing, so a click never looked aimed at
anything.

**AND THE HIT TEST FOLLOWS THE EDGE.** `_distance_to_edge` measures to
the nearest point ON the line, walking every vertex of it, where it
used to measure to a disc at the midpoint -- so clicking squarely on
an edge anywhere but its centre selected nothing. THE VERTEX REACH
CAME DOWN WITH IT, 12px to 8: a vertex sits at the end of every edge
meeting it, and measured on laves 3.3.4.3.4 at a realistic size the
edges run 31 to 43px, so 12px at each end claimed 24 of a median 43 --
more than half of every edge was unclickable as an edge.


### M-28 — The 2026-08-31 rebuild: the unit fit, the glyphs, the position-not-delta lever and the push rail, in full

<sub>Cut from `MAINTAINING.md`, lines 1326–1358 of the 2026-09-05 revision.</sub>

THE VIEW FITS THE UNIT, NOT THE PATCH. `topology.tiles` is the unit and
its neighbouring copies -- 36 tiles for a four-tile design -- so the
thing being edited was drawn at a third of the size the panel could
give it, every class label overlapping its neighbour and the handles
arriving as a cluster of rings a few pixels across. `n_tiles` is the
library's own count of the unit's own tiles; the copies still draw, and
run off the edges as context.

EACH HANDLE IS A PICTURE OF WHAT IT DOES: a double-headed arrow along
the edge for stretch, a curved arrow for turn, a wave for zigzag, a
four-way cross for a free vertex move, and an arrow on a rail for a
push. They were a square, a circle and a diamond, whose meanings
existed only here. A hover label was the obvious repair and is the
wrong one -- a hover must be discovered before it can teach anything,
and a first-time reader never hovers.

A HANDLE IS A POSITION, NOT A DISTANCE TRAVELLED, which retires the
lever that had been wrong twice -- AND THAT INCLUDES THE ZIGZAG'S
AMPLITUDE since 2026-09-05, which had been the drag's travel while the
count beside it was a position; the tab audit measured a handle at
0.3 moved one pixel along the edge previewing 0.01. A POINT WITH NO
LABEL IS NOT HIT-TESTED OR SEATED either: a zigzag adds two hundred
corners to the default design, and until the same audit a click on
one selected a vertex of no class. The end handle starts half a length
from the edge's middle, so where the pointer has taken it IS a polar
coordinate about that middle: the scale factor is how far out it now
sits, the rotation is the angle it now makes.

AND EVERY MANIPULATION IS REACHABLE ON THE DRAWING. `push_vertex` lived
behind the chooser alone; it has a rail now, drawn along the one
direction a push can take -- and no handle at all where that direction
cancels, which on laves 3.3.4.3.4 it exactly does.


### M-29 — Turn and zigzag 20.4px apart inside a 26px reach, and the other side of the edge tried first

<sub>Cut from `MAINTAINING.md`, lines 1358–1368 of the 2026-09-05 revision.</sub>

AND TWO HANDLES CLOSER THAN TWICE THE HIT TEST'S REACH MAKE ONE OF THEM
UNREACHABLE EVERYWHERE, since `_handle_at` returns the first within
reach and the order is fixed. Turn and zigzag are pushed along the same
normal from an edge's end and its middle, so at equal offsets their
separation is HALF THE EDGE'S SCREEN LENGTH: 20.4px inside a 26px
reach on two designs of three, costing 23 edges apiece their zigzag
handle. They stand at 30 and 60 now. Putting the zigzag on the OTHER
side was tried first and is worse -- it lands where the vertices are,
and handles are tested before vertices, so the vertex beneath became
unclickable while the edge was held.


### M-30 — What a drag means: the four disagreements of 2026-09-01 with their measurements, in full

<sub>Cut from `MAINTAINING.md`, lines 1375–1420 of the 2026-09-05 revision.</sub>

**FRACTIONS IN THE RECORD, MAP UNITS AT THE LIBRARY, AT BOTH PLACES.**
`dx`, `dy` and `push_d` are absolute displacements in the unit's own
coordinates, and the controls offer them as fractions, so something
must multiply. `topology_edits.in_map_units` is that something and it
had exactly ONE caller, in `apply` -- the commit path. The drag
PREVIEW handed the library the raw fraction, so a gesture's two halves
disagreed by the whole span of the unit: 70.71 map units committed
against 0.10 previewed on laves 3.3.4.3.4 at a tenth of the unit.
Nothing appeared to happen while you dragged, and the design jumped
when you let go.

**AND THE TWO SPANS MUST BE THE SAME SPAN.** The view divided a drag
by the unit's WIDTH while the model multiplies it back out by
`max(width, height)`, which is 1.268x on that design (557.68 by
707.11) and exactly 1.000x on a square one, so every example anybody
tried by hand hid it. `TopologyView.unit_span` answers the same
question as `topology_edits.unit_span` now, and the press stores that
one expression rather than writing the arithmetic out a second time.

**THE FRAME IS HELD FOR THE LENGTH OF A GESTURE.** `_fit` re-measures
the drawn extent on every paint, and during a drag what is drawn is
the preview -- so the transform became an output of the thing the
gesture was changing. The loop is not subtle: the preview moves the
geometry, the fit re-measures a larger extent, the scale falls, and
the same screen point now means a larger displacement. Held still
through six repaints, a recorded nudge climbed 0.104 to 0.356 while
the scale fell 0.6138 to 0.5541. `_fit` returns early while `_press`
is set, keeping the frame the drag's own origin was taken in, and
resumes at the drop.

**AND A DRAGGED VALUE IS HELD INSIDE ITS OWN BOX.** The three edge
manipulations passed through `_within_the_box`; both vertex branches
did not, so a drag past the range recorded a number the control would
not show, and the record is what the drop keeps. Visible on
`archimedean 4.8.8` and not on laves, where the library refuses a
nudge that large before anything is recorded.

**THE DUAL REPEATS ON WHATEVER LATTICE THE TILEABLE HAS.**
`_lattice_offsets` read `vectors` by the keys `(1, 0)` and `(0, 1)`,
and a hex tileable keys that dictionary by three-element coordinates,
so both lookups missed and the fallback drew one copy in silence on
every hex-keyed family. It takes the two shortest non-parallel
translations out of the VALUES now, which is key-shape agnostic; hex-slice 6
went from one position to nine and the square-keyed families are
unmoved at nine.


### M-31 — _same_shape's three wrong forms

<sub>Cut from `MAINTAINING.md`, lines 1435–1444 of the 2026-09-05 revision.</sub>

`_same_shape` is what answers that last one, and it has been wrong
three times: areas rounded to nine decimal places (an absolute
tolerance against tiles of area 62,500), then areas at all (a statistic
is not a shape), and then `shapely.equals_exact`, which compares
COORDINATE SEQUENCES rather than shapes -- and the library restarts
every ring on the way past, so identical ground read as changed and the
report could never fire on any design. It compares the GROUND now,
symmetric difference over the unit's own area, with the measurement at
the function.


### M-32 — The two doors to a new group, the readers that disagreed, and the checkbox's retirement

<sub>Cut from `MAINTAINING.md`, lines 1585–1600 of the 2026-09-05 revision.</sub>

**THERE WERE TWO DOORS UNTIL THEN**, and the second was a standing
"Create as new group" checkbox on Map options. The readers disagreed
about which to ask — five sites read only the checkbox, one only the
flag, and exactly one read both, that one only since ledger row 36 of
2026-08-28, where the chooser went on describing a landing that would
not happen because it knew the flag and not the box. The maintainer
retired the checkbox rather than teaching the two to agree: a control
two panels from the chooser can never make the boundary between "once"
and "always" read clearly, and a boundary that will never be clear is
one nobody should have to hold in their head. The standing "always
new" behaviour went with it; asking for a second map is an act you
perform when you want one.

The retirement was a DELETION at the landing rather than a rewiring,
because `force_new` already read the flag as one of its four terms.


### M-33 — The vendoring record of 2026-08-31: twelve commits under one version string, and the two patches that retired themselves

<sub>Cut from `MAINTAINING.md`, lines 1877–1882, lines 1931–1943 of the 2026-09-05 revision.</sub>

**THERE ARE FOUR FAMILIES NOW, and three of them are PERFORMANCE
patches offered upstream.** That sentence used to say "only one family
remains", which was true until 2026-08-31 and false from the moment
`idxmax` landed; it is worth knowing what is carried before you read a
re-vendor report.

THAT RULE PAID FOR ITSELF ON 2026-08-31, which is why it is worth more
than a caution. The re-vendor from bf1bbbf to 6190917 carried TWELVE
commits, with `topology.py` at +179/-207 and `_tiling_geometries.py` at
+44/-67 — and the version string is `0.0.7.89` at both ends. A version
comparison alone reports us current; only the commit says otherwise.

AND TWO PATCHES RETIRED THEMSELVES IN THAT ROUND, which is the failure
mode working rather than a problem. Upstream merged the change patch 1f
carried, dropping the scipy spline, so both its anchor
and 1e's stopped matching, the tool NAMED them instead of writing a
broken vendor, and the vendored tree now imports no scipy anywhere.
Only the matplotlib family remains.


### M-34 — The live path's refusal of a repaint, the ten named gates, and the two diagnoses silence cost

<sub>Cut from `MAINTAINING.md`, lines 2032–2058 of the 2026-09-05 revision.</sub>

**AND THAT WAS HALF THE FIX.** Two places launch a run, and the
second one refuses a REPAINT as well. `_maybe_live_generate` holds ten
gates, of which the sixth is this same availability question, and a
debounced tick never reaches `_generate` at all -- so a ramp picked
after the file moved was still not drawn, and the user was told "That
layer's data is no longer available, so the map cannot be updated",
which is false: a restyle re-seeds renderers on tiles that already
exist and reads nothing from the region layer. That gate now tries
`_restyle_only()` before refusing, and refuses only the tiling.
Nothing may fall THROUGH it -- `_extent_in_working_units` is a few
lines below and would read the dead extent -- so the repaint is
attempted at the gate rather than after it.

`_generate`'s own check needed nothing: its restyle fast path already
sits ABOVE it, so a button press was never blocked. That asymmetry is
deliberate and is guarded, by
`the-button-restyles-before-it-asks-about-the-source`, which reverses
the order and requires a test to notice.

TEN GATES, AND EACH NOW NAMES ITSELF behind
`WEAVINGSPACE_ADOPT_DUMP`: `LIVE-GATE source-gone`, `LIVE-GATE
too-many-tiles`, and so on. Live update stopping without saying why
has cost this project two diagnoses -- the icon-mode estimate of
2026-08-19 and this one -- and the dump answered the second in one
run, after the site had been named wrongly by reading in four
documents at once.
