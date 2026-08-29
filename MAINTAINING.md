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
writer; it is under 0.24.5 in ROADMAP.md.

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
current vendor is upstream v0.0.7.89 at commit bf1bbbf — note that
upstream does not always bump the version string when code changes,
so record the commit as well when re-vendoring.

## Releases

```bash
python3 release.py   # tests + visual gallery + report + zip
```

This is the only sanctioned way to put out a version. Bump `version=`
in `weavingspace_qgis/metadata.txt` first; the script then runs the
functional suite and the visual gallery under QGIS's Python and writes
`reports/v<version>/index.html` (a self-contained page with the
functional results and the rendered gallery), and only if every step
passed builds `dist/weavingspace_qgis.zip`. A failing step aborts with
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
