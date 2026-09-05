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

