# Maintaining this plugin

A guide for whoever keeps this working, whether cartographer,
student, or AI assistant; it assumes no particular software
engineering background.

## Long jobs are sharded by default

Anything that takes more than a few minutes and is made of
INDEPENDENT units is run four ways at once, not one:

    python3 tools/mutation_catalogue_sweep.py --shards 4      # catalogue
    WEAVINGSPACE_SWEEP_SHARD=0/4 ... tests/run_tests.py       # differential sweep
    (one process per shard, 0/4 through 3/4)

Independent means each unit's result does not depend on the others:
mutation judgements, differential-sweep cases, per-file audits. Those
shard cleanly and finish in about a quarter of the time.

The FUNCTIONAL SUITE and the per-test coverage record shard too, as
of 2026-08-11, three ways inside `release.py`:

    WEAVINGSPACE_TEST_SHARD=i/n     every nth registered test

That is safe here for a specific reason -- every test runs with an
EMPTY project, which is the rule that makes a failure name the test
that is actually broken -- so a slice is a legitimate subset rather
than a different suite. It took the suite from 32 minutes to 11.

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

What still does NOT shard is a MEASUREMENT beside another
measurement -- a census, the aggregate coverage report, anything
where contention changes the answer rather than only the duration.

The other half of the rule: arm a watcher in the same breath as you
launch, with a filter that matches failure as well as progress. Both
halves are in CLAUDE.md and in .claude/skills/long-job-supervision.

## The one-page mental model

```
you click Generate
      │
dialog.py      collects settings, builds the tile unit (catalog.py +
      │        vendored weavingspace), estimates tile count (refuses
      │        absurd ones), STRIPS CRS, then hands off to…
worker.py      a QGIS background task that runs the actual tiling
      │        (pure geometry, no pyproj! see Invariants)
dialog.py      takes the result on the main thread, reattaches CRS,
      │        splits it into one layer per element via…
bridge.py      GeoDataFrame ⇄ QGIS layer conversion, colour-ramp
      │        installation, renderer seeding, GeoPackage writing
QGIS           shows a layer group; the user restyles with normal tools
```

Files you will actually touch:

| File | What lives there |
|---|---|
| `weavingspace_qgis/compat.py` | **Every QGIS-version-dependent API call.** When a QGIS upgrade breaks the plugin, the fix is almost always one function here. |
| `weavingspace_qgis/dialog.py` | The dialog: controls, preview, live update, generate flow, layer-group management. |
| `weavingspace_qgis/bridge.py` | Data conversion and symbology. |
| `tests/data/` | Packaged fixtures: a real Auckland dataset, a generated categorical GeoPackage, and two importable QML colour mappings. Not shipped in the plugin zip. |
| `tools/make_test_fixtures.py` | Regenerates the categorical fixtures (tests assert on their exact colours; regenerate deliberately). |
| `tools/coverage_report.py` | Which plugin lines the suite never reaches. Run it when you are deciding where to write tests; it left the release path on 2026-08-12, having cost half an hour a candidate and gated nothing. It could not write a report at all until 2026-08-13: the suite ends in `os._exit`, so everything after the call was unreachable and the documented command produced nothing. |
| `tools/mutation_check.py` | Breaks each guarded behaviour and requires its test to fail. Run before substantial releases. |
| `tools/check_no_secrets.py` | Refuses to publish credentials, key material, private files or machine paths. Runs twice inside every release, and is worth running by hand before any commit. |
| `tools/macos_qgis_env.sh` | Finds a macOS QGIS bundle and prints the environment its Python needs, proving each candidate rather than trusting a path. Called by `tests/run_tests_macos.sh` and by the macOS CI job, which is what keeps the two in step. |
| `tools/sync_release_content.py` | Audits the claims the README and project page make (citation version, changelog, images, links, vendored version, URLs) and mends the mechanical ones. |
| `tools/make_site_images.py` | Retakes the published images: maps from the current release gallery, plus a fresh grab of the dialog. |
| `docs/MUTATION-LOOP.md`, `tools/loop/` | The runbook and scripts for re-running the whole mutation-score improvement campaign: cycle driver, health check, triage taxonomy, stopping rule. |
| `docs/PUBLISHING.md` | The release procedure end to end, and what still stands between here and the QGIS plugin repository. |
| `tools/mutate_auto.py` | Generates mutants from the syntax tree at random and measures how many the suite catches — the honest counterpart to the hand-picked catalogue above. Read `docs/MUTATION-TESTING.md` before quoting or chasing a score; the rules there are what keep it from becoming a vanity metric. |
| `weavingspace_qgis/catalog.py` | The tiling/weave menu: a verbatim copy of the web app's dictionary, plus two library extras (stripes, grid) appended by a loop after it. Sync the literal against the app; add further extras to the loop. |
| `weavingspace_qgis/deps.py` | Checks/downloads Python dependencies on QGIS builds that lack them. Version floors and pinned candidates at the top. |
| `weavingspace_qgis/help_content.py` | The Help tab text. Keep in step with `docs/USER-GUIDE.md`. |
| `weavingspace_qgis/said.py` | Everything the plugin has said, for the Messages tab. Its own module because `plugin.py` speaks before any dialog exists, and it imports nothing but `time` so that holding four strings does not drag the vendored library into QGIS start-up. |
| `weavingspace_qgis/topology_edits.py` | What a topology edit IS, with no Qt in it: the five manipulations upstream offers, whether a design can carry a topology at all, and how an edit is replayed onto a unit. Separate from the tab so the model can be tested without a window. |
| `weavingspace_qgis/topology_tab.py` | The experimental Topology tab: the drawing, the class picking, the drag, and the numeric boxes. Talks to the dialog through one signal. |
| `weavingspace_qgis/vendor/weavingspace/` | The upstream library, vendored and patched; see below before touching. |

## When a new QGIS version breaks things

This *will* happen (the 3→4 transition changed the Qt toolkit and
scoped the enums; a 4→5 transition will bring its own). The plugin
targets QGIS 4+ on the major platforms, so compat.py currently holds
plain QGIS 4 spellings, ready to grow fallback branches. The routine:

1. Run the test suite under the new QGIS (next section). The first
   failing test names the broken area.
2. The fix nearly always belongs in `compat.py`. Add a new branch to
   the relevant helper, keep the old branch so that older QGIS still
   works, and note the QGIS version in the docstring.
3. If something breaks outside compat.py, that is itself a rule
   violation; move the version-sensitive call into compat.py as part
   of the fix.
4. Re-run the tests, bump `version=` in `metadata.txt`, rebuild.
5. **The `qgisMaximumVersion` ceiling moves in the same commit as the
   first fallback branch, never before it.** `4.99` is what makes QGIS
   refuse to install this on a version nothing has run it on, and that
   refusal is the safety net rather than the problem: a user gets a
   clear no instead of a plugin that loads and throws at the first
   enum access. Raising it is a CLAIM that the plugin works there, so
   the honest moment is when `compat.py` has a branch for the new
   spellings and the suite is green under the new QGIS. Until then the
   published prose says "QGIS 4.x", which is what the metadata
   enforces. (Settled 2026-08-18, on being asked whether the ceiling
   could legitimately be lifted: it could be, and could not be
   justified. CI proves 4.0.0, 4.0.3 and stable; compat.py holds plain
   QGIS 4 spellings and no fallback at all.)

Known risk points (where future breakage is most likely): enum access
patterns, `QgsField` construction, `QgsVectorFileWriter` options,
`saveStyleToDatabase`, the `QgsClassification*` class names, and
`qgis.PyQt` shims (e.g. `QAction`'s home moved in Qt6).

## Running the tests

The suite is self-contained (synthetic data) and must run under
**QGIS's own Python**, not the system one.

macOS:

```bash
bash tests/run_tests_macos.sh            # auto-finds /Applications/QGIS*.app
```

That script does not know where anything is. It calls
`tools/macos_qgis_env.sh`, which finds the app bundle, finds an
interpreter that will actually start, and works out `PYTHONHOME` and
`QGIS_PREFIX_PATH` by trying them — the macOS CI job calls the same
script, so the runner and this machine cannot drift apart about how
to start QGIS's Python. Both paths were hardcoded here until
2026-08-15, and the prefix was wrong, which left QGIS with no colour
ramps at all on any machine whose profile had not already been seeded
by the plugin.

Windows (OSGeo4W shell):

```bat
set QT_QPA_PLATFORM=offscreen
python-qgis tests\run_tests.py
```

Linux (system QGIS):

```bash
QT_QPA_PLATFORM=offscreen QGIS_PREFIX_PATH=/usr python3 tests/run_tests.py
```

All tests print PASS/FAIL and the process exits non-zero on failure.

## Keeping up with a layer that changes underneath you

QGIS is live and this dialog is not modal to it, so the region layer
can change while the plugin is pointed at it. Three mechanisms cover
it, and each exists because the other two have a blind spot.

**The fingerprint** (`_layer_fingerprint`) reads
the feature count, the extent rounded to the metre, the field names
and the CRS. It is cheap enough to ask on every debounce tick and it
catches edits made straight through the data provider, which is what
Processing and a good deal of plugin code do and which emits nothing
this dialog could hear. It goes into BOTH `_geometry_signature` and
`_run_signature`. Before it existed, those tuples held the layer's ID
and nothing about its contents, so deleting half the features left
every term identical: the run was classified as a style-only change
and answered by re-seeding renderers over tiles built from data that
no longer existed. Pressing Generate did not help, which is what made
it serious rather than merely untidy.

**The signals** (`_watch_layer`, `_WATCHED_SIGNALS`) catch what the
fingerprint cannot: a value retyped, a vertex moved inside the
bounding box. Simplification is the clean example — Douglas-Peucker
keeps the extreme vertices, so the count and the bounding box both
survive it while every polygon changes. Connections are made through
`getattr` and each is optional, because the list is QGIS's and a
future release may drop one; a missing signal should cost one blind
spot, not an exception on every layer change. The whole disconnect
loop is wrapped too: when a layer is removed from the project its C++
object goes with it, and then even asking the Python wrapper for an
attribute raises — which is precisely when this runs, since removing
the layer is what changed the combo. `repaintRequested` is
deliberately absent: it fires on style changes, and re-tiling on those
is the cost the restyle fast path exists to avoid.

**The honest gap** is a layer nothing local can observe. WFS, OGC API
- Features, an ArcGIS service and PostGIS all change server-side with
no event here, and may report `featureCount()` as -1 or an estimate.
An explicit Generate always re-tiles them; live update does not chase
them, because polling somebody's endpoint unattended is not a thing to
do behind their back. A layer with QGIS's own auto-refresh enabled is
followed, since switching that on is the user saying the data moves.

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

THE OUTPUT GROUP IS THE UNIT OF WORK. A chooser sits beside the region
chooser naming which map a run will land in, with a "create new"
entry; dataset and group are bound symmetrically, each selecting the
other, with recency deciding where a dataset owns several groups; and
the group carries the WHOLE WORKING STATE on its own custom property,
so selecting it restores that design and that symbology together
rather than the dialog inferring them. The GeoPackage carries the same
record as file metadata, which makes a saved map resumable without the
project that made it -- the source recovered by reference, embedding
it an explicit opt-in -- and element tables are trimmed to the
variable each element displays and named `tiles_<tid>_<variable>`.
SAVING IS A POSITIVE ACT, and since 2026-08-27 that is what the
plugin does rather than what it is going to do. A path chooser
records what you WOULD write to and does nothing on its own; the SAVE
button beside it writes the map as it stands -- element tables, their
no-data twins, each layer's style embedded beside it, the stale-table
drop, the source copy when the box is ticked and its REMOVAL when it
is not, and the resumable record, in one act. LOAD, on the row
beneath, reads a saved map back. Generate draws. Auto-generate never
writes at all.

`_save_the_map` IS THE ONLY WRITER, which is the part that matters to
whoever maintains this: every question about when the file learns
something has one answer instead of eleven. Three consequences are
worth knowing before touching it.

THE LAYERS ARE REPOINTED AT THE FILE by the press, in place, through
`compat.point_layer_at`, which keeps each layer's id, renderer, name
and custom properties -- the things the rest of the dialog is keyed
on. Without it a map drawn to memory and saved to a GeoPackage comes
back EMPTY when the project is reopened, since a memory layer
round-trips through a .qgz as a valid layer with no features.

AND A LAYER THAT ALREADY READS FROM THE DESTINATION IS SKIPPED rather
than written: asking OGR to write a layer into the table it is
reading from is asking it to overwrite a layer with itself, which it
refuses. That is not an edge case, it is the SECOND press on any map,
and before the skip existed every save after the first failed at the
first element and returned before the styles, the drop and the
record.

AND THE TABLE NAMES COME FROM THE LAYER where it already reads from
this file. A dialog that opened a map with Load never drew it, so it
holds no record of what the tables are called -- and where the region
data cannot be found the variables are not restored either, so
recomputing gave `tiles_a` for a table the file calls `tiles_a_v1`.
The save wrote new tables, the stale-table drop removed the real ones
as belonging to elements this map no longer had, and the file a
person had just opened was gone. Names are invented only where there
is no such layer, which is the adopted-group case.

TWO REFUSALS, both in words. A press while a run is IN FLIGHT is
refused, because what is on screen then is the previous map -- and
that guard sits ABOVE the no-map check, or a press during the first
run answers "there is no map to save yet" to somebody who has just
pressed Generate. And a press onto a file this map did not write asks
first; what counts as ours is the file's own record naming the
dataset in force, not this session's memory, so an ordinary re-save
after a restart is silent.

WHICH DATASET A MAP CAME FROM IS ASKED OF THE LAYER THAT WAS TILED.
Every output layer carries `weavingspace_region`, and three rules read
it: the chooser LABELS a group with it, the binding matches a
dataset's groups by it, and the landing refuses to write over a group
whose stamps name another dataset. The group's own working state
carries the same fact a second time. Both now come from the LAUNCH
moment -- the record from its snapshot, the stamp from `source_layer`,
the layer this run tiled. Until 2026-08-26 the stamp was read live
from the region chooser as the run landed, so switching the region
layer mid-run filed one dataset's tiles under another and a later run
on that other dataset destroyed them. When one fact is written twice,
both writers take it from the same moment or the two will disagree.

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

**AND THE SIZE GUARD ASKS RATHER THAN REFUSES.** (Same day.) Above
`MAX_TILES_CONFIRM` a run is confirmed; above `MAX_TILES_HARD` the
same question is put in stronger words -- this may use all the
computer's memory, QGIS may stop responding, save your project first
-- with the safe button as the default. Neither is a refusal any more.
What IS refused is what is not a size at all: `UNTILEABLE`, a design
whose vectors are degenerate, and `UNCOUNTABLE`, an extent that cannot
be measured. Those two used to share the ceiling's value, which is why
the ceiling could not soften until they were split off; they are
negative, so a gate comparing `est > ceiling` cannot wave one through.

**AND WHAT RE-DEFAULTS TAKES ITS STYLE WITH IT.** An element whose
column has gone re-points at a surviving field, and since 2026-08-20 it
also gives up the style somebody had chosen: a scheme cut for one
column says nothing about another, and a categorical one meeting a
numeric column draws a colour for every distinct value. The rule is
written at three places because three routes reach it -- the chooser
pointed at a new dataset, a column that keeps its name and changes its
kind, and `_adapt_to_the_layer` here, which re-points the row before
the table is rebuilt and is therefore invisible to the other two.

When adding a setting that depends on the layer's CONTENTS rather than
on the dialog's controls, it belongs in the fingerprint. When adding
one that depends on the controls, it belongs in the signature beside
the others — and think about which of the two signatures, because
that is the line between re-tiling and re-painting.

## Working around a QGIS bug, and knowing when to stop

There is one active workaround for a defect in QGIS itself, and the
pattern around it is meant to be reused rather than admired.

**The defect.** QGIS's classifier counts a NULL as zero when computing
class breaks. Its own `minimumValue()` excludes nulls, so QGIS
contradicts itself; nine values of 1..9 beside five nulls classify as
0-0, 0-2.5, 2.5-5.75, 5.75-9 instead of 1-3, 3-5, 5-7, 7-9. Verified
on the memory provider and on a GeoPackage through OGR under QGIS
4.0.3.

**The workaround.** `bridge.make_graduated_renderer` applies
`"field" IS NOT NULL` as a subset string, calls QGIS's own classifier,
and restores whatever subset was there before. It corrects the input
instead of computing breaks here, which would mean maintaining four
classification algorithms and diverging from the styling panel. It
filters the ELEMENT OUTPUT layer, which this plugin creates and owns.
A provider that refuses the subset falls through to the unfiltered
path, because wrong breaks beat no map.

**What it survives.** Project save and reload, a GeoPackage reopened
elsewhere with its embedded style, and the plugin's own restyle path.
It reverts only when the user presses Classify in QGIS's Graduated
panel. It cannot be hardened past that without leaving the filter on
permanently, which would hide the no-data features from the map — a
worse error, since a missing place reads as no place rather than as
missing data.

**How you will know it can go.**
`test_qgis_still_counts_nulls_as_zero` asserts the bug, with the
plugin out of the way. Its failure means QGIS fixed it; delete the
marked block and the canary, keep the notice.

**Reuse this shape.** Any future workaround for a dependency's bug
gets: the measurement recorded with a date and version, the fix at
the narrowest point, a comment at the fix saying when it can be
removed, and a canary test asserting the upstream bug so the suite
announces the day it is fixed.

## What the plugin hears from QGIS, and when it hears nothing

The dialog follows edits made in QGIS's own styling panel by
connecting to each element layer's `styleChanged`. That connection is
made in exactly TWO places: when a run lands its layers
(`_add_output_layers`) and when the plugin adopts a group from a
reopened project (`_adopt_existing_group`).

**AND THAT SIGNAL ONLY FIRES ON `setRenderer`, WHICH IS NOT EVERY
EDIT.** This section used to say `styleChanged` is emitted "both when
the styling dock installs a new renderer and when a symbol is edited
in place". The second half is FALSE, measured on QGIS 4.0.3,
2026-08-20, with the plugin out of the way:

    setRenderer(clone)                            rendererChanged, styleChanged
    addClass on the live renderer                 NOTHING
    updateRangeSymbol on the live renderer        NOTHING
    recolour a clone, then setRenderer            rendererChanged, styleChanged

(An earlier version of that table carried a `symbol().setColor()` row.
It was VACUOUS and is removed: `ranges()` hands back copies, so the
probe recoloured a temporary and the renderer never changed -- the
fixture-that-cannot-move trap, inside the measurement meant to settle
this. `updateRangeSymbol` is the honest in-place row, and its edit was
verified to reach the layer.)

`repaintRequested` was connected for that measurement too and fired on
none of the rows above by themselves. What DOES fire is the
`triggerRepaint()` the styling dock calls after an in-place edit -- it
is the only way the user's canvas learns, so it always follows -- and
that emits `repaintRequested`. The dialog therefore connects
`repaintRequested` on ELEMENT layers beside `styleChanged`, debounced,
gated against the plugin's own repaints and against the echo of a
heard `setRenderer` edit. The REGION layer's `repaintRequested` stays
deliberately unconnected: there a repaint must not cause a re-tile,
and that older rule is about that layer alone.

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

## Whose colour is this? Attribution, not delta

Both styling paths now answer that question from a RECORD of what the
plugin itself painted, rather than by comparing the layer against
what the plugin would seed today.

`_painted_ladders` has done it for graduated elements since
2026-08-20. `_painted_categories` is its categorical twin, added
2026-08-26: `{tile_id: {field: {value: colour}}}`, written wherever
the plugin paints (both `seed_renderer` sites and group adoption) and
NEVER from the follow, which runs before attribution and would record
the dock's own work as ours. An absent entry means "never seen" and
DECLINES, which is neither ours nor theirs.

Why the delta had to go: a landing that keeps a renderer over an
unreadable class source makes "what would we seed now" a lie -- it
answers automatic colours while the map honestly wears the template
-- so the template's colours were adopted as somebody's hand-picks
and outranked the template from then on. Three narrower guards each
closed one route into that and left another; the record closes the
question instead of the routes.

## Every exit from `_generate` says which one it was

Live update has named its ten gates behind `WEAVINGSPACE_ADOPT_DUMP`
since two diagnoses were lost to its silence. The button path has
eight exits and, until 2026-08-26, named none -- so a Generate that
produced no file, no layers and no message could not be diagnosed
from a log at all. Each exit now dumps `GEN-GATE <name>`, and the
keep-the-previous-result guard prints its whole decision: `keeping`,
`would_replace`, `same_destination`, and both paths.

THE ONE TO KNOW ABOUT is that guard, because it refuses through a
QMessageBox. In a headless run the suite's shim records it in MODALS
and the message bar stays empty, so the run looks like one that never
started. When a run appears to do nothing, read the modal store
before concluding silence.

## What a Save writes, and which moment each half of it is about

`_save_the_map` writes the file's working-state record last, and that
record is assembled from TWO moments. Three things describe the map
that was DRAWN and are carried off the group's own record, because
only a landing knows what was drawn: the design, the region, and the
elements -- their membership AND the variable each was drawn with,
since that variable names the table its tiles are in. Everything else
about an element is read live and must stay so, because the colour
editors remain usable after a landing and a colour or a pin chosen
then belongs in the file.

The one edge this act legitimately decides is `output_path`. A landing
does not choose where the file goes; a Save does, and a file whose own
record named another file would point a resume at a stranger's map.

That split was got wrong twice in one evening, both times by carrying
too little: the design and region alone, so the record named a
variable its own tiles were not drawn with; and then those plus the
variable but not the element LIST, so lowering the element count left
a record claiming `n=4` beside two elements and a file holding four
tables. Whenever you add a key to this record, ask which of the two
moments it is about.

**AND THE THREE STORES ARE NOT SYMMETRICAL, which decides what happens
when you add a key.** Writing is permissive and reading is strict:

    _capture_working_state   iterates WORKING_STATE_DESIGN and
                             WORKING_STATE_ELEMENT -- a key not named
                             there is never captured at all
    _file_safe_state         a BLACKLIST: it copies the record and
                             removes each element's `kept` map, so
                             anything captured travels to the file
    the restore              iterates those same whitelists -- a key
                             the file carries is dropped IN SILENCE

So a new key needs adding in two places, will reach the GeoPackage
whether or not anybody meant it to, and fails as a file that
faithfully holds something nothing can restore. This is the "widen the
whitelist in the same commit as the code that reads it" rule -- said
three times already, about `_adopt_dock_bounds`, the copy and `mode` --
with the wrinkle that the file needs no widening and will not warn you.

**The record is also the door for anything DERIVED from the design.**
It is JSON in the GeoPackage's own `gpkg_metadata` table, written by
`bridge.write_working_state` through GDAL's `SetMetadataItem` under
`WEAVINGSPACE_STATE`. Measured 2026-08-29 against a possible topology
tab: the structured half of a twelve-element design's topology is
2,424 bytes against about 1,151 for a representative record, and it
round-trips identically from a cold open. GEOMETRY DOES NOT BELONG
THERE -- a dual tiling is a GeoDataFrame and wants a layer, which a
colleague can open without the plugin at all. And anything travelling
as a tuple comes home as a list, JSON having no tuple, so every reader
has to put it back.

### A design is shown by one name and looked up by another

`family_combo` was built with `addItems(names)`, so a catalogue key --
`laves 3.3.4.3.4` -- was the label a person read, the string thirteen
sites looked the design up by, AND the `family` value written into
every saved GeoPackage and project. That is one string doing three
jobs, and it meant an entry could not gain a common name without
orphaning saved files.

**THE ITEM CARRIES THE KEY AND SHOWS A LABEL.** `catalog.label_for`
composes the label from `catalog.COMMON_NAMES`; `dialog._family_key`
is the one owner of "which design is this" and every one of those
thirteen sites asks it; the working state's `family` row is `"data"`,
so it stores the key -- which is the same string every file already
holds, so nothing saved moves. `_select_family` looks by data then by
text, which is what makes an older record and a caller holding a
label both land.

**THE SUITE HAD 121 SITES NAMING A FAMILY BY TEXT**, and they matter
because `setCurrentText` on a non-editable combo selects only an
exact match and otherwise does NOTHING, in silence. They go through
`_choose_family`.

### What an edit is aimed at, and by which control

`TopologyPanel._selection` is `(target, labels)` and is the one answer
to "what would an edit move". Three controls follow it, with their
signals blocked: the class combo, the tick list, and the drawing. A
modified click on the drawing adds or removes a class; ticking a row
does the same; picking a combo row replaces the lot. Apply, the drag
preview and the drop all ask the owner rather than the combo they used
to read.

**THE COMBO CANNOT LIE.** Where the selection is one class it names
it, where it is every class of a kind it names the group entry, and
where it is anything between it grows ONE temporary row -- "2 of 3
vertex classes" -- which is replaced rather than accumulated.

**AND THE HIGHLIGHT ASKS MEMBERSHIP, NOT EQUALITY**, which was a
defect of its own: "every edge" has always carried the whole group as
its datum, so an equality test lit nothing at all.

### The symmetries, and the one control they take away

`Topology` already holds `tile_matching_transforms`; the tab draws the
distinct ones -- highest order per centre, one line per mirror -- in
its own painter, because upstream's `plot_tiling_symmetries` goes
through matplotlib, which cannot run inside the signed QGIS process on
macOS.

**THE GATE IS A DIFFERENT QUESTION FROM THE READOUT, and they are kept
apart deliberately.** `topology_edits.tile_symmetry_codes` answers
about a TILE's own shape (`D4`, `C2`) and is a reading;
`directions_a_class_may_move` answers about a CLASS's stabiliser and
decides whether `push_vertex` is offered. Both get called symmetry.

**WHAT THE GATE MEASURES**: stack `L - I` for every transform that
holds a representative vertex modulo the lattice, and take 2 minus the
rank. Zero means no displacement survives the symmetry, which is why
`push_vertex` moved 0.0000 of the unit on `laves 3.3.4.3.4` class A
and on both classes of `hex-slice 3`, against 0.1027 on `archimedean
4.8.8`. It is asked ONLY of the push -- a nudge is an arbitrary
displacement and moves those same classes by 0.2 -- and only where
every selected class is held.

### The dual as a design, and the constructor that is missing

`topology_edits.dual_as_tileable` copies the source unit, replaces its
tiles with `Topology.get_dual_tiles()`, and rebuilds the prototile
from the vectors. That reaches into the library's own construction,
and it is written that way because `Tileable.__init__` dispatches on
`tiling_type` and has no path for supplied geometry: a `tiles=`
keyword is accepted, stored, and overwritten by the default unit.

**IT IS A WORKAROUND WITH THE PROCEDURE'S FURNITURE.** The measurement
and the removal criteria are at the site,
`test_the_library_still_cannot_build_a_unit_from_tiles` asserts the
gap, and `docs/process/upstream-note-a-unit-from-supplied-tiles.md`
asks for the constructor. When that test fails, delete the assembly
and use the library's.

**IT IS A GEOMETRY TERM**, so "Map the dual instead" is in
`_geometry_signature` and in the working state -- a colleague opening
the file gets the tiling that was sent -- and it falls through with a
sentence where there is no dual, since an inset opens gaps and a
gapped design has no topology.

### A gesture outranks a landing, for as long as it lasts

`TopologyView.show_topology` clears the drag preview and the chosen
thing. That is right for a rebuild -- both belong to the topology
being replaced -- and wrong under a pointer that is still down: a
build finishing mid-drag put the un-edited design back beneath
somebody's hand, dropped the highlight showing what they were aiming
at, and left the drop to commit an edit out of a record they could no
longer see.

**SO THE PANEL HOLDS A LANDING AND SETTLES IT AT THE DROP.**
`set_unit` stashes `(unit, topology, message, ghost)` in
`_landing_held` while `view.gesture_in_progress()` answers True, and
`_settle_a_landing_the_drag_held` applies it afterwards -- through a
`finally` rather than at each of the four exits, since an exit added
later would otherwise strand a build nobody applied. Where the gesture
committed an edit the held landing is DISCARDED, because that record
makes the dialog chain and land again within the tick and drawing the
older design first is a flicker; where it committed nothing, the held
one is what draws. A landing arriving with no gesture supersedes a
held one, which is what stops a press nobody released leaving a stale
design for ever.

**AND IT IS ONE QUESTION, NOT TWO.** `gesture_in_progress` is also
what makes `_fit` return early, so the frame a drag is measured in and
the topology it is aimed at are frozen by the same method for the same
span. Two predicates would come apart the day somebody changed one.

**IT WAS FOUND FROM A RUNNER.** It shows here about one run in eight,
and macOS, Linux 4.0.3 and Linux 4.0.0 all failed the drag guard on
its own premise -- "the drag drew no preview at all", 730 passed and 1
failed, three times over. A stack printed from a patched
`show_topology` named the caller on the first failing attempt.

### Whose file is it, and when was that decided

`_this_map_owns_the_file` answers True as soon as the file is in
`_gpkg_tables_written`, and OUR OWN FIRST PRESS puts it there. So the
answer flips under us: a colleague's GeoPackage is theirs on press one
and ours on press two. Three removers are gated on it -- the
stale-table drop, the source-copy drop and the topology drop -- and on
2026-09-01 the first was found deleting their `tiles_a_*` on a second
press and the second their `weavingspace_region`, which is the copy
that makes their file redrawable by anybody.

**SO THE ANSWER IS TAKEN ONCE, BEFORE ANY WRITE, AND REMEMBERED PER
FILE.** `_file_was_ours_when_met` holds it, and a file that did not
exist counts as ours by construction -- without that clause a file we
CREATE reads as somebody else's for ever, since nothing of ours is in
it to recognise on the first press, and the drop would then spare this
map's own orphans too. The OVERWRITE QUESTION keeps the live reading
deliberately: with Save a deliberate press, asking every time is
noise.

**AND THE DROP NAMES ITS CANDIDATES RATHER THAN MATCHING THEM.** It
swept every table whose name begins `tiles_<id>` for an id this map
has, and an element id is a letter every map in the world shares. A
table is ours if our own record accounts for it: this session's list
of what it wrote, or the file's record of the elements a previous save
put there, composed through `bridge.element_table_name`, which is the
function that named them. Read the field key out of
`WORKING_STATE_ELEMENT` when you touch this -- it is `var`, and a
first repair that asked for `variable` composed nothing at all and
spared everything.

### A save asks the FILE what is already there

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

### A save keeps the window painting, and takes its buttons down

Every call the write loop makes is one of QGIS's or OGR's own
per-layer APIs, and each opens the GeoPackage, so the seconds grow
with the layers already in the file: 134 of them at the 256-element
ceiling, with a 50 ms heartbeat recording zero beats. Making the save
a SINGLE OGR SESSION is the real repair and is a rewrite of the
writer; it moved into 0.24.4 on the maintainer's decision of
2026-09-01 and `bridge.write_gpkg_layers` is it. Two of the three
per-layer terms are closed -- the writing and the style embedding,
each now ONE call where it was n -- and the third, `point_layer_at`,
is measured rather than conceded: every layer genuinely needs its own
provider, a warm QGIS layer does not make it cheaper (0.85 to 1.02 of
the plain cost), and it is what remains of the quadratic.

What ships in 0.24.4 is the maintainer's decision of 2026-08-29: the
loop turns the event loop once per element behind a determinate
progress bar, so the window says what it is doing. The pump sits at
the TOP of the body, where none of that loop's four `continue`s can
skip it -- a bar that stops moving on the elements that are skipped
says the save has hung.

**The pump and the disabling are one decision.** Turning the event
loop is exactly what would otherwise let somebody press Save or
Generate into a half-written file, so both controls go down for the
duration and are restored to what they WERE rather than enabled: a
save can be pressed while Generate is already refusing for its own
reasons. The bar comes down in a `finally`, the write raising
included.

## The save's three doors, after 2026-09-02

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

## What a resume writes on the layers, and why it must

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

## Nothing ends while a save is outstanding

(Maintainer's ruling, 2026-09-01: when a save is outstanding and QGIS
or the user tries to quit, a window says what is being waited for,
offers Cancel, and nothing ends until the save finishes or the cancel
is pressed.)

`_a_save_is_outstanding` is the one question -- `_save_pending`, a
promise made and not yet kept, OR `_saving_now`, the keeping of it --
and two doors ask it.

**QGIS'S OWN QUIT** goes through an event filter on the main window.
It DELAYS rather than vetoes: `eventFilter` returns False, so the
close proceeds after the waiting window has held it. Refusing outright
would leave somebody unable to leave QGIS at all if a save ever
wedged, and their escape is the button rather than the code. The
filter is installed after `_retire_previous_instance` (which takes the
old dialog's off) and removed in the retirement path, or it is this
project's retired-dialog family wearing an event filter.

**CLOSING THE PLUGIN WINDOW** asks first, with Save as the default.
Before 2026-09-01 `closeEvent` cleared `_save_pending` with nothing
said, so shutting the panel threw away a promise the plugin had just
made -- the harm of the 2026-08-29 ruling, through a door nobody had
walked. SAVE MEANS WAIT FOR THE REDRAW, never "write what is on
screen": the press was deferred precisely because the map on screen is
the one they had changed away from.

**THE HOLD PUMPS RATHER THAN `exec()`ING**, and that is a
testability decision as much as a design one. The suite's shim patches
QMessageBox and nothing else, so a modal `exec()` on a custom dialog
waits offscreen for a click that can never come -- the thirty-one
minute hang this project has already paid for. `_waiting_window` is
held for the length of the wait so a test can arm a `singleShot` and
press Cancel where a person would click.

**CANCEL MEANS CANCEL AT EVERY MOMENT**, and the two moments are
answered by different mechanisms. Before the write, dropping the
intent IS the rollback -- nothing has been opened. During the write,
`_save_cancelled` is what `bridge.write_gpkg_layers` reads through its
`should_stop` argument: it asks BETWEEN tables, never mid-table, and
answers True with a `RollbackTransaction`. Every table went in inside
one transaction, so undoing them is one call rather than a repair.
`written` is cleared with it, and the save then RETURNS rather than
carrying on -- otherwise it would embed styles for tables that are not
there, drop "stale" tables on the strength of a map that was never
written, and repoint every layer at a table the rollback removed.

THE BUTTON WAS BRIEFLY DISABLED DURING THE WRITE INSTEAD, which was
honest about what it could do and worse than doing it. The maintainer
chose to ship the callback (2026-09-01) rather than defer it, on a
branch about to be a candidate, which is worth recording: the
alternative was a control that greys itself at the moment somebody
most wants it.

A CANCELLED FIRST SAVE LEAVES AN EMPTY FILE, because the writer
creates the data source before the transaction opens. That follows the
existing behaviour of a FAILED write rather than being a new decision,
and it is why the sentence says the MAP was not written rather than
that nothing was.

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

`SAVE_WAIT_CEILING` is a hang-catcher and not a budget, sized above a
topology build plus a re-tile.

## What a resume has to say for itself

Opening a saved map is not a passive act, and three records have to
learn about it or the next thing the user does destroys the file.

`_landed_this_session` -- a map opened is this session's work, exactly
as a map drawn is. Without it a change of dataset reads as a first
choice, the output path is not cleared and nothing is said, and the
next Generate writes the other dataset's tiles into the file that was
opened.

`_last_run_sig` -- nothing has changed since the map now on screen. A
resume moves the design controls, which arms both debounce timers, and
without this the live path's same-signature gate cannot fire: with
live update at its default the opened map is re-tiled into memory a
second later and the GeoPackage-backed layers are gone.

`_embedded_when_resumed[path]` -- whether THAT FILE carried a copy of
the region. It is deliberately not the checkbox: the box is a standing
preference and the fact belongs to a file, so a recipient who never
touched it does not strip the copy a sender included, and does not
have their own data copied into their own next file either.

And the GROUP is stamped with the region the recovery LANDED ON,
which is not the same fact as the region the record names.
`_recover_the_source` has three routes -- a layer already open, the
recorded source loaded from disk, and the copy inside the file -- and
it returns the source it used, or None where none of them worked.

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

## Three queues, because a press, a tick and a save are not one fact

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

So there are two flags now and they are honoured differently.
`_live_pending` is a deferred live tick and still restarts the live
timer. `_press_pending` is a deferred BUTTON press and is re-pressed by
`_finish_run`, through the same `singleShot(0)` the deferred adoptions
use, because `_task` is cleared inside the landing rather than after
it and `_generate` is entitled to a plugin at rest. A press supersedes
a queued tick; a closed window presses nothing.

The rule for anyone adding a third kind of deferred work: ask what
consumes the flag, and whether that consumer can DECLINE for a reason
that has nothing to do with the act being deferred. Every other
remembered-intent record here is consumed by taking and clearing it at
the point of use, which cannot lose anything; this one handed it to a
gated path.

**AND THE THIRD KIND ARRIVED THE NEXT DAY**, which is why that rule is
written where it is. `_save_pending` is a Save pressed while a re-tile
is COMING -- the live timer armed, no task yet -- and until 2026-08-29
such a press was refused in words. The maintainer overruled that: most
people will not read the sentence, so a refusal that depends on being
read is a save that quietly did not happen and somebody closes QGIS
believing their map is on disk. The press is kept, the notice says the
map will be saved after it is redrawn, and `_honour_a_queued_save`
writes the file.

IT IS CONSUMED AT THE POINT OF USE, taking and clearing the intent
before the write, and it is asked from THREE places because no one of
them covers the ground: `_finish_run`, for the ordinary case where the
queued run lands; the live timer's OWN second connection, for the tick
that declines at any of its ten gates, after which no landing is
coming at all; and a timer armed at the end of the landing, which runs
after the re-pressed Generate and so covers that method's eight
refusals too. A second `connect` rather than a line inside
`_maybe_live_generate`, because that method has ten exits and a tail
added to it would run on none of them -- and connected after the
handler already there, since an exception in a Qt slot is swallowed
and takes the rest of the slot with it.

WHAT IT HOLDS IS NOTHING. The chooser is read again at the moment of
the write, exactly as the button reads it, so every guard the press
would have met is met -- the overwrite question, the empty box, the
map that is no longer in the project. Remembering the path instead
would write to a file the person had since changed their mind about.

## Leaving a dataset stamps what you leave

The group record is ordinarily written at landings. A choice made and
switched away from INSIDE the live debounce has no landing yet, so
the return applied the record from before the choice and the choice
died -- while the switch notice had just announced it. `_on_layer_changed`
stamps the working group on the way out of a dataset it has built
from, taking the region from `_memory_layer_id` (the outgoing
dataset) rather than from the chooser, which already holds the new
one. A run in flight is left to its landing, whose launch snapshot
must win.

## Everything the plugin says, in one place

The plugin speaks into TWO stores that nothing brought together: QGIS's
message bar, and modal dialogues. Reading one and concluding silence is
a fault this suite has met so often it is numbered — harness fault
eleven — and it has cost real diagnoses, because a run refused through
a QMessageBox leaves the bar empty and is indistinguishable from a run
that was never launched. A user has no `MODALS` list to read.

Since 2026-08-30 there is one door and one record. `said.record` keeps
`{at, kind, text, answer}` in `said.SAID`, session-scoped and bounded
at `said.CEILING`; `_warn`, `_problem` and `_ask` on the dialog are
thin wrappers that record and then call QMessageBox exactly as the
call sites used to, so the suite's own modal shim intercepts them
unchanged and no harness had to learn anything. `_report_quietly` and
the four direct `messageBar()` pushes record too.

**THE RECORD IS A MODULE, NOT THE DIALOG'S OWN LIST, and that is the
part worth knowing.** `plugin.py` speaks BEFORE any dialog exists --
the dependency consent dialogue, the failure to provision, and the
failure to import the library -- and two of those mean the window
never opens at all. A record beginning at the dialog's construction
would be missing exactly the messages somebody most needs to look back
at. `said.py` therefore imports nothing but `time`, so holding four
strings does not drag the vendored library into QGIS start-up, and the
dialog's `_said` is a VIEW of the same list rather than a copy.

`said.clear()` empties the list IN PLACE for the same reason: the
dialog holds a reference, and rebinding would leave the tab reading a
list nothing writes to any more -- the watched-attribute-that-is-a-view
trap this project has already paid for once.

**AND THE COMPLETENESS IS GUARDED AS A SHAPE.** A list of the sites
that existed the day it was written would go stale the first time
somebody raised a new modal, which is the day the tab would start
lying. `test_everything_the_plugin_says_reaches_the_record` walks the
shipped package for QMessageBox and message-bar calls and requires the
function making one to record as well. It cannot see the consent
dialogue -- that is a QMessageBox INSTANCE the caller execs, not a
call to the class -- so the consent answer has its own behavioural
test driving both arms, which is how that gap was found: the
catalogue entry survived against the shape guard.

**THE ANSWER IS KEPT WITH THE QUESTION**, and that is half the point:
many of this plugin's modals decide something — whether a file was
overwritten, whether a design was recomposed to fewer elements,
whether a large run went ahead — so a log holding the question alone
describes a decision nobody can reconstruct.

The Messages tab shows it, newest first, with a Clear button. It is
EXPERIMENTAL and therefore greyed until the box below is ticked.

## Experimental features, and what "greyed" is made of

`opt_experimental` on Map options — the third tab, which is where the
maintainer's ruling of 2026-08-30 put it — is unticked by default and
gates the tabs listed in `_experimental_tabs`. `_gate_experimental_tabs`
calls `QTabWidget.setTabEnabled`, which greys a tab's title AND refuses
selection in one call, so the two halves of the ruling cannot come
apart later. When the box is unticked while an experimental tab is in
front, the dialog steps back to Design rather than leaving somebody
looking at a tab they can no longer use.

The tabs stay VISIBLE rather than being removed, deliberately: a person
should be able to see that there is more here and what ticking the box
would give them.

It is a standing preference about the PLUGIN, not a fact about a map,
so it does not belong in a group's working state — putting it there
would carry one person's appetite for experiments into another
person's project through a saved file. That is the two-relationships
framing in CLAUDE.md, applied to a control.

## The topology tab: where an edit lives between being made and being drawn

The Topology tab lets somebody move the EDGES and VERTICES of the tile
unit itself — zigzag an edge, rotate or scale it, push or nudge a
vertex — either by typing a number or by dragging on the drawing. It is
experimental and behind the box above.

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

**And the tab SAYS when it is working.** A build is queued by whatever
rebuilds the unit and lands seconds later, and in between the panel
still holds the PREVIOUS design's topology -- so an edge somebody
clicks there is not the edge that would move.
`TopologyPanel.say_a_build_is_coming` writes "Working out the design's
structure…" from the moment the work is QUEUED, and `set_unit` clears
it wherever a build lands, so no route has to remember to.

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

**Not every design has a topology.** `Topology` needs a GAP-FREE
tiling, so a design with insetting or a family that does not close up
refuses, and `can_build` says which it is in words rather than letting
the constructor raise. Zigzag additionally needs its unit REPAIRED
first: the manipulation emits repeated vertices — six coincident pairs
among thirty-seven points on the case measured — which is what makes
the result invalid, not floating point and not the amplitude.

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

### How somebody takes hold of it: select, then act, then a handle

Settled 2026-08-30, after the maintainer asked whether the interaction
was intuitive first time, powerful, and whether anything better
existed. The honest audit said no, moderately, and yes, so the tab was
rebuilt around three rules.

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

**AND IT WAS REBUILT AGAIN ON 2026-08-31**, on the maintainer's report
that the tab was unusable and their standard for what would fix it: it
"should be easy to use and easy to learn", it "has to be perceivable",
and "hover states aren't as good as shapes that make sense". Four
things changed, and the reasoning for each is in docs/TOPOLOGY.md.

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
lever that had been wrong twice. The end handle starts half a length
from the edge's middle, so where the pointer has taken it IS a polar
coordinate about that middle: the scale factor is how far out it now
sits, the rotation is the angle it now makes.

AND EVERY MANIPULATION IS REACHABLE ON THE DRAWING. `push_vertex` lived
behind the chooser alone; it has a rail now, drawn along the one
direction a push can take -- and no handle at all where that direction
cancels, which on laves 3.3.4.3.4 it exactly does.

AND THE TWO PANES HAVE FLOORS, WHICH IS WHAT MAKES ANY OF THE ABOVE
REACHABLE. (2026-09-01, on the last of the maintainer's editing asks:
"everything needs to be clickable at realistic sizes of course".) The
drawing's floor was 180px and the column of controls beside it claims
its own preferred width first, so that floor WAS the whole allowance --
180px of an 825px window for the thing the tab exists to edit. Raising
it alone moved the complaint rather than answering it, measured at 71px
of viewport for controls wanting 271; the horizontal scrollbar there is
deliberately off, so a column narrower than its content does not
scroll, it CLIPS. Both have floors now, 420 and 271, taken from the
content itself in `showEvent` once a layout pass has made the answer
meaningful. The window grows to 1025 when the tab is chosen and the
Design tab still opens at 825, the size policy of 2026-08-30 keeping
the stack off it.

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

WHAT IS STILL NOT BUILT is the audit's other design, merging scale and
rotate into one end handle. It is refused rather than pending: one
handle would have to say two things, which is what the glyphs exist not
to do. The argument is in docs/TOPOLOGY.md.

### What a drag means, and in whose units

Four things had to agree before a drag meant what it looked like, and
on 2026-09-01 none of them did.

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

### How an edit that cannot be drawn is told apart from one that did nothing

Three different things can go wrong with a replayed edit, they need
three different sentences, and until 2026-08-31 only one of them was
reliably said.

**A CLASS THE DESIGN DOES NOT HAVE is answered by name, exactly, before
any geometry.** This is the ordinary consequence of the shelf: edits
are replayed by class LABEL, and `a` names a different edge in laves
3.3.4.3.4 than in hex-slice 4. The library is entitled to take such a
selector -- `transform_geometry` walks its edges asking `label in
selector` and matches none, neither raising nor complaining -- so the
change list would grow while the map stood still. `apply` asks the
topology which labels it holds and refuses by name, and where SOME of
the named classes exist it applies to those and says which it could
not find.

**AN EDIT THAT CANNOT BE LAID OUT** is refused in the terms of the
control, which is `bridge.inset_collapse_message`'s shape rather than
the library's own count of invalid geometries.

**AND AN EDIT THAT WAS APPLIED AND MOVED NOTHING** is reported too,
which is a different sentence again and the one this project keeps
having to rebuild. It is not a hypothetical: `push_vertex` computes its
direction by summing the unit vectors from each neighbour to the
vertex, and at a symmetric vertex those cancel exactly, so on laves
3.3.4.3.4 and hex-slice 3 it moves the design not at all while on
archimedean 4.8.8 it moves it by 1.9e-4 of the unit's area. That is a
fact about the DESIGN rather than a defect, and the person still has to
be told, or they meet a control that takes a click and does nothing.

`_same_shape` is what answers that last one, and it has been wrong
three times: areas rounded to nine decimal places (an absolute
tolerance against tiles of area 62,500), then areas at all (a statistic
is not a shape), and then `shapely.equals_exact`, which compares
COORDINATE SEQUENCES rather than shapes -- and the library restarts
every ring on the way past, so identical ground read as changed and the
report could never fire on any design. It compares the GROUND now,
symmetric difference over the unit's own area, with the measurement at
the function.

**Edits are SHELVED by design**, under `topology_edits.shelf_key`,
which is the family and the element count. Move the design away and
the edits go quiet; bring it back and they return. This is the same
shape as the per-field scheme memory: what stays ACTIVE changes, what
is REMEMBERED does not.

**And the shelf rides the working state**, so a saved project brings
back what somebody did to the topology rather than only the design
they did it to. That needed BOTH halves of the record in one commit —
`_capture_working_state` writing `topology_edits`, and
`_restore_recorded_topology_edits` reading it — because writing here is
permissive and READING IS STRICT: a key captured with no matching
restore travels to the file faithfully and is dropped in silence on the
way back. This project has now written that rule down four times, for
`_adopt_dock_bounds`, for the copy, for `mode`, and here.

Two details of the restore that are easy to get wrong. **The key comes
from the RECORD, not from the controls** — the restore runs while the
controls are being written, so reading the family off the combo would
file the edits under whatever the dialog held at that instant. And
**the restore runs BEFORE `_apply_element_records`**, because
`_rebuild_unit` is what asks the shelf for them; a list put back
afterwards would describe a map already drawn without it.

`WORKING_STATE_VERSION` is deliberately NOT bumped for this. An added
key is invisible to an older reader, which iterates its own whitelist
and simply does not look; bumping the version would make every older
plugin refuse a file it could otherwise open perfectly well.

### The unit and the dual in the file, and why their names shout

A Save writes two more tables, `weavingspace_unit_no_crs` and
`weavingspace_dual_no_crs`, so the GeoPackage describes itself: a
colleague can open the motif and its dual without the plugin, which is
the argument that put the element tables and their styles in there.

**The edit list still governs.** These two are a DESCRIPTION and never
a source of truth, because their coordinates scale with the spacing —
stored geometry is wrong the moment somebody changes it, while a class
label was measured stable across rebuilds and across spacings 500 and
1300.

**The names carry the warning, and that is the ruling's own caveat
rather than a stylistic choice.** They live in unit space: a couple of
units across, no CRS, not in the map's coordinates and never will be.
Somebody who opens one expecting it to sit on the map has to be told
BEFORE they load it, because QGIS's answer to a layer with no CRS is
to ask them to pick one, and picking any at all puts a two-unit-wide
motif at that projection's origin. `topology_edits._in_unit_space` is
the one owner of the stripping, and it returns a COPY — the unit
carries the map's CRS deliberately, since `_adopt_edited_unit` puts it
back so the preview and the tiling agree, and stripping in place would
reach the object the dialog draws from.

Its guard asserts the EXTENT as well as the flag. A test reading only
`GetSpatialRef() is None` would pass on a frame that had been
reprojected and then stripped, which is the wrong map wearing the
right label.

**One method writes and drops, deliberately.** A design that stops
carrying a topology — a tile inset, a strand width off 1.0, the box
unticked — would otherwise leave the previous design's motif in the
file describing a map it is no longer made of. That is the ruling of
2026-08-26 that a file shows the limit of what it contains, and it is
the same shape as unticking the source copy. A wanted write that FAILS
also clears, because a stale motif is worse than none. And nothing is
removed from a file that was not this map's before the save began:
in a stranger's GeoPackage even our own table names were written for
THEM, which is the line the source copy and the stale-table drop both
hold.

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

**A CONNECTED SLOT THE DIALOG DOES NOT HOLD IS FREED, AND THE
MECHANISM IS NOT ESTABLISHED.** `_layer_slots` holds each layer's
`(style, repaint)` closure pairs so they outlive the connect call,
with `_already_watching` guarding the adoption site against a second
connection to one layer. THE FIX IS MEASURED -- two tests that aborted
the process at exit 134 pass with it and abort without it -- and the
mechanism is NOT: a hunt measured layer and QgsStyle connections
SURVIVING collection, an explicit gc pass and heap churn, so the
comfortable story about a wrapper being collected and freeing the
closure is not something this project has shown. The measurement lives
at the test rather than in a comment asserting a cause. Remember that
PyQt6 ABORTS the process when an exception escapes a slot, so the
symptom of anything wrong in this family is a shard that stops with no
verdict at all rather than a failure you can read.

**THE WAIT-FOR-THE-TOPOLOGY GATE SITS BELOW THE FLUSH, DELIBERATELY.**
`_generate` defers a run while an edit list exists and the edited unit
has not been restored, so the map is drawn from the edited unit rather
than the unedited one. That gate was first written ABOVE the flush,
which is wrong in a way that only shows on the second press: the
pending intent is what the flush exists to consume, so returning in
front of it left the press remembered AND unconsumed, and the run that
eventually landed drew a design two edits old. It reads
`_topology_edit_key()`, arms `_live_pending` or `_press_pending`
according to which path asked, and says in words that the map will be
redrawn when the changes are ready -- the shape the maintainer's
ruling of 2026-08-29 requires of a deferral, since a refusal nobody
reads is work lost. `_a_queued_run_would_redraw` answers True on
either pending flag before it looks at the timer, or a save queued
behind a deferred run would be honoured against the old map.

## The door that arms a new group

`force_new` decides whether a run builds its own group instead of
landing in the one on screen, and since 2026-08-30 exactly one control
arms it: the group chooser's "Create new" entry, which sets
`_new_group_chosen`. The flag is ONE-SHOT — the next run builds its own
group, the flag is spent the moment the landing reads it, and selecting
any real group clears it again.

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

## What an output group is called

`WeavingSpace tiles — <dataset>`, made in `_get_or_make_group` from
the layer the run tiled, with a counter appended only where that name
is already taken. The plugin's own name comes first so its groups sort
together in the panel.

The name is a LABEL. Every lookup asks the layers, so renaming a group
is the user's business and the plugin follows it rather than undoing
it; the counter exists for the case where one dataset owns two maps.
The group chooser shows the name as it stands and appends the dataset
only where the name does not already carry it, which is a renamed
group or output made before 2026-08-26.

## A group's record: which half comes from which moment

The design, the output path and the region describe THE MAP THAT WAS
DRAWN, so only a landing may move them: it passes the snapshot its run
was launched with. Every other writer -- the switch-out stamp above,
the queued restamp that follows an adopted dock edit -- carries those
three forward from the record already on the group and re-reads only
the ELEMENTS, which are live by design because the colour editors stay
usable during a run.

Until 2026-08-26 the three were re-derived from the live controls
whenever no snapshot was handed over, which cost three defects in one
day: a group claiming a design its own layers were never drawn at, a
map filed under a dataset it was not made from, and a blank table
written over a good record.

Two conditions belong to the switch-out stamp on top of that, and both
ask WHOSE state this is rather than when it was taken. A dataset that
has been removed leaves nothing to stamp, because the table is blank
only because its fields went with it. And the group has to be that
dataset's own map, asked of the layers' `weavingspace_region` stamps:
`_group_of_our_layers` answers where this dialog's layers are, which
is the group the last run LANDED in and not necessarily the group of
the dataset being left.

AND THE CONSEQUENCE NOBODY HAS DECIDED YET, recorded 2026-08-31 so it
is not rediscovered as a bug. Because the design half is carried and
the elements half is live, a Save can write `n=4` beside `elements
a..f` -- reachable in three presses with live update off. Trimming the
list would be wrong: the surplus entries are the per-element,
per-field memory ruling 6 of 2026-08-21 says must survive a switch and
come back. The likely answer is at the READER, a Load assigning only
the first `design.n` elements, but that is a decision about what the
record MEANS and it is the maintainer's. It sits in ROADMAP.md under
0.24.4.

## What a design IS, and why one function owns the answer

`_capture_design` returns every design term -- WORKING_STATE_DESIGN's
widgets plus this design's own topology edits -- and it is the ONLY
answer to that question. `_capture_working_state` puts its result
under "design"; the save's staleness guard compares it against the
record it is about to write.

IT WAS EXTRACTED ON 2026-08-31 BECAUSE A SECOND DEFINITION HAD DRIFTED.
The guard deciding whether the file's motif still describes the file's
tiles enumerated three terms -- family, element count, edit list --
while the key it writes beside the motif hashes `_topology_stamp()`,
the spacing and every modifier included. Any term outside those three
moved the key while the guard reported agreement. Measured: spacing
500 to 900 with no Generate then Save kept a unit of area 797,396
beside tiles drawn at 246,110, its record still saying 500; the same
journey moving the tile inset DELETED motif and dual from a file whose
tiles carry them. Two hunts found it independently.

So a guard that ENUMERATES the fields of a record is a copy of that
record's definition, and it goes stale the day somebody adds a
control. Ask whether the owner can be called instead.

## Colours kept for a file that has gone

An element whose class source cannot be read keeps what it draws, and
the record is how. `_own_the_colours_of_an_unreadable_source` writes
the kept renderer's colours into the element's hand-picked record and
notes them in `_kept_for_unreadable`, which shadows that record entry
for entry, banks with it per dataset, and travels in the layer's stamp
under `"kept"`. `_release_colours_kept_for_an_unreadable_source` gives
them back the moment the file answers again, before anything is seeded
-- a held colour outranks a template, so a late release would repaint
the map with the colours the file had before it went away.

Both are asked AFTER the renderer is settled rather than inside the
arm that keeps one, because two routes reach a kept renderer: that arm
and the older promise that an element whose assignment has not changed
keeps its styling. The first draft asked inside the arm and the
ordinary journey -- draw a map from a scheme file, move the file,
change the spacing -- takes the other route.

## The table's columns, the window's budget, and which wins

The assignment table's columns are sized from what they SHOW, not from
constants: the widths in the constructor are floors, and
`_fit_table_width` grows each visible column to the larger of its
content and its header. The constants alone were measured against the
9pt font `QT_QPA_PLATFORM=offscreen` supplies, and at a desktop 13pt
every cell but one elided -- including the chooser whose whole job is
saying which style a row wears.

**`COLUMN_SUM_BUDGET` is what the columns may occupy between them**,
and past it the widest give back what they can, never below
`COLUMN_FLOORS`. That is the layout rule's own priority order, settled
2026-08-09 and unchanged: the window stays within the narrowest screen
FIRST, and within that the table does not scroll. Where both cannot
hold, the window wins -- a scrollbar is a nuisance somebody can work
around, and a window wider than their display is not.

**So a column is as wide as its content WHERE THERE IS ROOM, which is
not the same as always.** On Windows 'Style' wants 295px where this
machine wants 184, and the nine columns want about 1200px inside a
1480px window that also holds the preview; there, cells elide and the
window fits. Asserting the stronger promise made it one the software
cannot keep on the platform most of its users are on.

The budget is bracketed by two measurements rather than chosen: at
least about 1030, which is what the columns need here before anything
elides, and at most about 1118, since with the columns wide the rest
of the layout wants 362px. The slack sits on the safe side because the
costs are asymmetric -- an elided label can be lived with and a window
off the side of a screen cannot.

**None of this can be measured from here alone.** In the suite's own
environment the window's minimum is SMALLER than the table's, so the
table does not drive the window and the ceiling has nothing to bind.
Forcing every column to 400px is what puts this machine in the state
wide fonts put another in, and it is how the guard reaches the case;
`tools/platform_probe.py` asks the real question on the real platform
in about fifteen minutes.

## Three mechanisms settled on 2026-08-31

**A FILE THAT ALREADY HOLDS A MOTIF GETS A FRESH ONE.** (Maintainer's
decision, after this method's fifth fault.) The two topology tables
describe a design and their coordinates scale with the spacing, so once
the design moves they are stale and dropping them is right -- what was
missing is putting a new one in their place. On the commonest journey
nothing has built a topology at all: the box is unticked on every new
dialog, so reopening a saved map, nudging the spacing, pressing
Generate and pressing Save moved the key while `topology` was None, and
the drop fired alone.

The build that answers it asks only where the file in front of it
already carries our unit table, so somebody who has never opened the
Topology tab pays none of it. And where the design genuinely has no
topology the build returns None with a reason and the drop is correct.

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

**THE DUAL IS BUILT AND STAMPED BESIDE THE UNIT, or the write declines
and the clear runs anyway.** This is the part that made two repairs
look like they did nothing. The write demands both frames and demands
that the pair be of ONE design, so a build that sets `topology` and
leaves `_topology_dual` empty produces a wanted write that FAILS -- and
a wanted write that fails still clears. The tables then go exactly as
they did before the repair, with a dump line the only evidence.

**AND THE FILE'S KEY DOES NOT HASH THE CRS.** `_topology_stamp()` is
built from `_unit_kwargs()`, which carries `crs` off the region layer,
and `crs` is the ONE stamp term `_capture_design()` cannot see -- so
the save's staleness guard reported the design unchanged while the key
had moved. `_topology_description_key()` strips it. The STAMP keeps its
crs, deliberately and narrowly: it also decides whether an off-thread
build that has just landed is still about the design on screen.
Measured: `make_unit` at EPSG:3857 and EPSG:27700 gives identical tile
WKT and identical topology classes, and the tables are written in unit
space with no CRS at all, so the CRS describes nothing about them.

**A SAVE WAITS ONLY FOR A RUN THAT IS COMING.** `_queue_live` arms the
live timer on every output-affecting change whatever the checkbox says,
and `_maybe_live_generate` then declines at its second gate -- so an
armed timer is not a run that will start.
`_a_queued_run_would_redraw` asks the checkbox on its timer limb now,
as its sibling `_a_live_run_will_follow` always did on its first line.
The FLAGS limb is untouched and the asymmetry is the point: a deferred
press or tick redraws whatever the box says, because something has
already undertaken to run. With the box off, saving what is on screen
is right rather than a lesser evil -- "preserve, do not repaint" means
the map deliberately does not follow the table until somebody presses
Generate, so the map on screen IS the map.

**TICKING THE EXPERIMENTAL BOX ASKS FOR THE TOPOLOGY.** The box's
`toggled` reached the gate and a touch counter, and the build runs from
`_rebuild_unit` -- so the gate opened the tab and nothing filled it.
`_ask_for_a_topology_when_the_experiments_open` queues one when the box
goes ON, and only then: unticking neither builds nor discards, since
putting an experiment away is not a request for work. The cost ruling
survives because the work hangs on the BOX rather than on the tab. The
stale half was worse than the empty one -- a design changed while the
box was off left the panel holding the previous design's unit, so the
tab offered classes of a design nobody was looking at.

## Invariants — do not break these

1. **The worker thread never touches pyproj/PROJ.** QGIS uses the same
   PROJ library on the main thread, and concurrent use segfaults the
   whole application (a real crash we chased, not a hypothetical). `dialog._generate`
   strips CRS from the unit and region before the background task and
   reattaches it afterwards. Any new geopandas code in the worker path
   must not set, compare, or convert CRS.
2. **All version-sensitive QGIS API calls go through `compat.py`.**
3. **Never provision numpy 2.x, never shadow a healthy QGIS package.**
   `deps.py` only extracts a wheel when the shipped package is missing
   or below the version floor, and only into the plugin's own `libs/`.
4. **Generation must stay size-guarded, the guard measures the GROUND
   rather than the extent, and since 2026-08-25 it ASKS rather than
   refuses — except for the two answers that are not sizes at all,
   which no question may soften.** Tile count grows with 1/spacing²,
   and `bridge.estimate_tile_count_bounds` runs before every
   generation, including live updates. What it divides by the
   prototile's area is the region's DISSOLVED area plus a strip one
   tile diagonal wide round its dissolved boundary — not a circle
   enclosing the bounding box, which is what it used to be and which
   refused maps the library draws: a region of two long islands
   filling 11.8% of that circle estimated 8.3 times what was tiled,
   and a user could not make their map at all (2026-08-19). The live
   gate still asks from a layer extent alone, where assuming the
   region fills its box is the most generous honest assumption; the
   hard gate has geometry and dissolves it, at about 0.05s for 3,011
   polygons. If you change one, change the other: a plugin that
   refuses at one figure and advises a spacing derived from another
   reads as contradicting itself.

## Updating the vendored weavingspace library

Dropping in a new upstream release is a script, not a project:

```bash
python3 tools/vendor_weavingspace.py /path/to/weavingspace/weavingspace
python3 release.py
```

The script copies the upstream package into `vendor/weavingspace/` and
re-applies every plugin patch, reporting each one. Only one family
remains: making matplotlib and scipy optional, since QGIS bundles
neither. (A convex-hull performance fix used to live here too; on
2026-08-07 upstream adopted the same optimisation, verified to tile
identically, so the patch was retired rather than carried alongside
an equivalent upstream one.) Upstream's modern
Python (match statements, dataclass slots) is vendored untouched,
since QGIS 4+ bundles Python 3.12 or newer.
Every targeted patch asserts on an exact anchor from upstream, so if a
new version changed that code the script names the patch that needs a
human decision instead of writing a silently broken vendor; the intent
of each patch is documented in the script where you would fix it. The
current vendor is upstream v0.0.7.89 at commit 6190917 — note that
upstream does not always bump the version string when code changes,
so record the commit as well when re-vendoring.

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

## Releases

```bash
python3 release.py   # tests + visual gallery + report + zip
```

This is the only sanctioned way to put out a version. Bump `version=`
in `weavingspace_qgis/metadata.txt` first; the script then runs the
functional suite and the visual gallery under QGIS's Python and writes
`reports/v<version>/index.html` (a self-contained page with the
functional results and the rendered gallery), and only if every step
passed builds the versioned zip in `dist/`, named
`weavingspace_qgis-<version>.zip` — every artefact carries its version,
and `build.py --check` is what a packaging CHECK runs, building into a
temporary directory so a gate never writes into `dist/` at all. A
failing step aborts with
no zip, so a bad release cannot be cut absent-mindedly. `build.py`
alone still exists for local experiments, not for releases.

For a side-by-side check of the gallery against the original
renderer, `tools/visual_reference_report.py` builds
`reports/v<version>/visual-comparison.pdf`: each case's QGIS render
next to weavingspace's own `TiledMap.render` output on identical
inputs, which is also exactly what the web app draws (it pins the same
library version). It needs a Python with geopandas *and* matplotlib —
not QGIS's own (macOS code-signing refuses PyPI C extensions in the
signed QGIS process); any virtualenv with those two packages works.

The zip must stay under 20 MB and contain no binaries if it is ever
submitted to the official QGIS plugin repository (this is why
dependencies are downloaded at runtime rather than bundled).

## Where the user documentation lives

- `docs/USER-GUIDE.md`: the full guide (glossary, workflow, design and
  colour guidance, switch semantics), grounded in O'Sullivan & Bergmann
  2026, *Cartographic Perspectives* 108, doi:10.14714/CP108.2109. It
  paraphrases rather than copies; keep it that way. It is also written
  in the authors' own prose style; match it when editing.
- `weavingspace_qgis/help_content.py`: the condensed in-dialog
  version. Edit both together.
- Control tooltips in `dialog.py` carry the same guidance in one-liners.

## Documentation standard (required for all new code)

Every new module, class, and non-trivial function gets a docstring, and
sections get comments, written for a reader who understands the core
weavingspace library but not QGIS: whenever a QGIS or Qt API is used,
say what it is and why in plain terms (what a renderer is, why signals
are blocked, what a memory layer is), not just what the call does. The
existing modules set the bar — match it. Line-by-line commentary is not
the goal; explaining the QGIS-shaped reasoning is.

## Asking a layer whether its data is still there

`compat.layer_data_is_available` is the one place that answers this,
and it must be asked BEFORE anything reads a layer's extent: on a
GeoPackage whose file has gone, `extent()` takes QGIS down with no
exception and nothing in the log.

**The cheap answers are cached, and a moved file does not disturb
them.** Measured on QGIS 4.0.3, moving a GeoPackage out from under an
open layer:

    before the move   isValid True   provider True    count 36   iterated 36
    file moved away   isValid True   provider True    count 36   iterated  0
    then reload()     isValid True   provider False   count -2   iterated  0

Nothing reloads a layer a user has not touched, so between the file
moving and somebody noticing, every cheap question answers as though
the data were there. The function therefore asks for ONE FEATURE, with
no attributes, wherever the layer claims to hold any: a positive count
and nothing coming back is data that has gone. Iterating a dead
provider is safe -- it yields nothing and raises nothing -- which is
what makes this affordable where reading the extent is fatal.

A layer that legitimately holds nothing is not unavailable, so the
question is only put where the layer claims otherwise. If you add a
caller, ask it here rather than reading `isValid()` yourself.

**AND ITS ANSWER MUST NOT TRAVEL INTO A SIGNATURE.** Corrected
2026-08-20, a regression from the fix above. `_layer_fingerprint`
answered `("unavailable",)` for a moved file, which is a DIFFERENT
value, so the geometry signature moved -- and a changed geometry
signature means "re-tile", which is the one thing that cannot be done
from data that has gone. The restyle path declined and the refusal was
discarded in silence.

"The source has gone" is not "the design you asked for is different".
The fingerprint therefore answers with the LAST READING TAKEN WHILE
THE DATA WAS THERE, kept per layer id in `_last_good_fingerprint`; it
cannot simply skip the question, because `extent()` on a dead source
segfaults QGIS, so standing still is the honest answer available. The
refusal belongs where a RUN is launched, which asks
`layer_data_is_available` for itself.

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

The general form, which is the reason this paragraph exists at all:
when a guard starts answering differently, follow its return value
into every TUPLE it is a member of, not only into its callers. And
when you name the SITE of a defect, measure it: a location reasoned
out of the source reads exactly like a location that was proved.
