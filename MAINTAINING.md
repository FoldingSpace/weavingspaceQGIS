# Maintaining this plugin

A guide for whoever keeps this working, whether cartographer,
student, or AI assistant; it assumes no particular software
engineering background.

The full accounts of things this file states briefly are in
`MAINTAINING-archived.md`, by the ids it quotes (M-1). This file is
architecture, so most of it stays here; see docs/DOC-ARCHIVING.md.

## How to add to this file

This file explains MECHANISMS: what a thing is, the rule it keeps, the
comparison table where there is one, and why it is shaped that way. A
new mechanism gets a section stating those, in that order, at the
place in the file where its neighbours live -- not at the end. An
existing mechanism that changes is rewritten where it stands, and the
superseded account goes to MAINTAINING-archived.md under an id minted
with `python3 tools/doc_archive.py --mint M "title"`, quoted at the
sentence it supports. What does NOT belong here is the narrative of
finding out -- the day, the wrong first hypothesis, the measurement
with its numbers -- which is the account and lives in the archive; an
entry past 110 lines or a paragraph that opens with a date fails
`tools/check_standards.py` with the fix in the message.

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
of 2026-08-11, FOUR ways inside `release.py` since 2026-09-06 (three
before that, on the maintainer's instruction as the suite passed
eight hundred tests):

    WEAVINGSPACE_TEST_SHARD=i/n     every nth registered test

That is safe here for a specific reason -- every test runs with an
EMPTY project, which is the rule that makes a failure name the test
that is actually broken -- so a slice is a legitimate subset rather
than a different suite. It took the suite from 32 minutes to 11.

**A SHARD'S VERDICT IS ITS VERDICT LINE, NOT ITS LAST LINE, AND SHARDS
ARE READ SEPARATELY, NEVER ONLY THEIR SUM.** A shard that died and one
whose last line is noise look identical to a naive tail, and a shard
that dies at startup shows only as an asymmetry -- nineteen, thirty,
and nothing -- that the sum hides; `tools/merge_coverage_shards.py`
refuses a partial set, as a backstop rather than a detector. Each
shard prints how many tests it was OFFERED and the totals must agree,
since a probe registered from inside a test once consumed a slot
(`sharded=False` now); and every stall ceiling widens by two and a
half times under sharding, against a measured contention cost of
15-50%. (M-1, M-8.)

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
| `tools/coverage_report.py` | Which plugin lines the suite never reaches. Run it when you are deciding where to write tests; it is off the release path, having cost half an hour a candidate and gated nothing (M-9). |
| `tools/mutation_check.py` | Breaks each guarded behaviour and requires its test to fail. Run before substantial releases. |
| `tools/doc_archive.py`, `docs/DOC-ARCHIVING.md` | The binding documents are split into a live half that carries the rules and an `-archived.md` half that carries the account behind each one, under ids the live half quotes; the package's docstrings have the same split, into `docs/DOCSTRINGS-archived.md`. The tool checks that every pointer leads somewhere, that no account is stranded, that each live document is inside its line budget and keeps its SHAPE (a how-to-add section, fixed sections, a capped inbox, no date-led entries), and mints ids; `--suggest` says what the next pass would look at. |
| `tools/check_no_secrets.py` | Refuses to publish credentials, key material, private files or machine paths. Runs twice inside every release, and is worth running by hand before any commit. |
| `tools/macos_qgis_env.sh` | Finds a macOS QGIS bundle and prints the environment its Python needs, proving each candidate rather than trusting a path. Called by `tests/run_tests_macos.sh` and by the macOS CI job, which is what keeps the two in step. |
| `tools/sync_release_content.py` | Audits the claims the README and project page make (citation version, changelog, images, links, vendored version, URLs) and mends the mechanical ones. |
| `tools/make_site_images.py` | Retakes the published images: maps from the current release gallery, plus a fresh grab of the dialog. |
| `docs/MUTATION-LOOP.md`, `tools/loop/` | The runbook and scripts for re-running the whole mutation-score improvement campaign: cycle driver, health check, triage taxonomy, stopping rule. |
| `docs/PUBLISHING.md` | The release procedure end to end, and what still stands between here and the QGIS plugin repository. |
| `docs/PERFORMANCE.md` | Where a map's time actually goes, with the probe behind every figure; which speed-ups were taken, which were refused for changing the map, and what is still open. |
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
`tools/macos_qgis_env.sh`, which finds the app bundle, an interpreter
that will actually start, and `PYTHONHOME` and `QGIS_PREFIX_PATH` by
trying them against a throwaway profile; the macOS CI job calls the
same script, so the runner and this machine cannot drift apart about
how to start QGIS's Python. The hardcoded prefix that left QGIS with
no colour ramps on any unseeded machine: C-317, M-10.

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

**A CHANGE OF DATASET, AND THE OUTPUT GROUP THAT GOVERNS IT.** Settled
by a grilling on 2026-08-25 and built the same day, REPLACING the
contract of 2026-08-21 and 24 rather than patching it. What follows is
what GOVERNS; the earlier machinery survives underneath and is what you
will meet in the source -- `switched_from_work` in `_on_layer_changed`
still decides what counts as a switch, `_begin_new_dataset` still
clears the output path and asks the design-floor question, and
`_swap_dataset_memory` still keeps every field-keyed record in
PER-DATASET BANKS, so value-laden records never cross a shared column
name while the style keeps by name. None of it decides where a run
lands any more. (M-2.)

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
comes from which group is SELECTED now, a fact on screen rather than a
flag, and `_new_group_chosen` means one thing, set only when somebody
picks "create new". The report that prompted the replacement -- three
scopes answering one act three ways, none named on screen -- and the
first build's conflation: M-11. The rulings are in CLAUDE.md.

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

So adding a class in QGIS's panel is followed and recolouring one is
heard only through the repaint (ledger row 28); and since the plugin
calls `_on_layer_style_edited` DIRECTLY in places, a `HEARD` line in a
dump is not by itself evidence that QGIS said anything.

**So a session whose Generate has never succeeded hears nothing**,
since no run has landed and no layer is watched: a dump from a
reporter's session was EMPTY where six reproductions had all worked
(M-12). When a dock edit appears not to reach the plugin, ask FIRST
whether a run has landed in that session; and when adding a third
route by which element layers come into existence, connect the watch
there too, since a layer the plugin holds but does not hear goes on
describing a map that has moved.

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
too little (M-13). Whenever you add a key to this record, ask which
of the two moments it is about.

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

**AND A PLAIN CLICK INSIDE THE SELECTION CHANGES NOTHING.**
(Maintainer's rule, 2026-09-07.) A plain click OUTSIDE the ticked set
replaces it, which is what a plain click has always done; where several
classes are ticked, clicking one of them used to collapse the selection
onto that one, so an edit aimed at two was narrowed by the act of
pointing at what was already selected. `_on_chose` returns early where
the clicked class is already in hand, refreshing the manipulations and
nothing else -- the view has already moved `_chosen_thing` to the
instance under the pointer by then, so the handles follow while the
class selection stands still.

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

### The dual is completed here, and a button makes it a map

`topology_edits.complete_dual` builds the dual's frame from the
topology's own `dual_tiles` -- one polygon per vertex of the unit --
with every copy's centre taken as its base tile's centre translated.
It exists because the library's `get_dual_tiles` labels the dual with
the SOURCE's tile ids sliced to the dual's count, so pandas keeps as
many rows as the source has tiles, and because the library's tile
centre is a numerical search run per copy, landing about a unit apart
on two copies of one tile. The default design's dual came back four
tiles of six covering 77% of the ground, and the library refused to
build a Topology of it while building the same tiling from its own
catalogue. Both go upstream in
docs/process/upstream-note-the-dual-is-truncated-and-drifts.md, and
`test_the_library_still_truncates_and_drifts_the_dual` asks the
library directly whether either is still there. Both the map and the
file's `weavingspace_dual_no_crs` table come from this frame.

**"GENERATE THE DUAL AND TILE IT" IS A BUTTON ON THE TOPOLOGY TAB**,
not a box (the five rulings of 2026-09-05, in CLAUDE.md). It lands
the dual in a new group named `<group> — dual` through the chooser's
own "Create new" door, so every guard on that door holds; the store of
"is this map tiled with the dual" is still the record's `map_dual`
term, a box that is kept but never shown because thirteen readers
speak its language, with a label beside the button that follows the
store -- told directly after a record restore, which writes the store
with its signal blocked. `topology_edits.dual_on_offer` is the one
owner of whether a dual is offered: no topology, a dual the library
cannot lay out, or one short of its cell, each with its sentence, and
the button is disabled with that sentence at every landing. Elements
are assigned fresh by the ordinary landing.

**AND DUALS CHAIN.** (Maintainer's ruling, 2026-09-06.) The box stays
the boolean those thirteen readers speak, and `_dual_depth` beside it
says how many times over, read from the record's `dual_chain` -- one
frozen edit list per dualisation, `dual_source_edits` still written
as its first level for an older reader. `shelf_key`, `_topology_stamp`
and both signatures carry the depth, `_build_unit` takes the dual
once per level, and `_generate_the_dual` queues the unit's rebuild
itself, since a second press does not toggle the box that used to.
The way back to an earlier geometry is its own group in the chooser.
Account and measurement: C-334.

**AND THE CORNERS ARE FOUND TO A RELATIVE TOLERANCE.** `_exact_centre`
is the library's own choice of centre -- the incentre, by polylabel --
at one part in a thousand million of the tile's own size rather than
at polylabel's default of one map unit, because at the default each
base tile carried its own noise and the dual's symmetry changed with
the spacing: three edge classes at 3000, ten at 2900 (the tab audit,
2026-09-05; docs/TOPOLOGY.md has the table). The dual of the default
design now has the snub square's two edge classes at every spacing,
and the dual differential asks two spacings to agree.

`covers_its_cell` is the coverage question -- the tiles' area against
the prototile's -- and it is deliberately not `gaps()`: that measures
holes in a patch's union, which is what an edit opens, and an inset's
channels reach the patch's edge and are not holes at all (measured
0.0 on an inset that leaves 35% of the cell bare).

### The drop keeps the picture it was showing

`_commit_the_drag` used to open with `show_preview(None)`, so the
edited geometry was cleared AT THE DROP and the un-edited design stood
until the asynchronous rebuild landed -- 1.7 seconds on `laves
3.3.4.3.4`, nineteen on `hex-colouring 7`, the field report against
0.24.4rc15 (M-14).

**THE PREVIEW IS KEPT WHERE AN EDIT WAS RECORDED, AND THE LANDING
CLEARS IT**: `show_topology` sets `_preview = None` as its own third
line and every route to an answer passes through it, so the preview
stands exactly as long as there is nothing better to draw.

**AND EVERY PATH THAT RECORDS NOTHING STILL CLEARS AT ONCE** -- a press
that never grabbed anything, a selection the tab cannot act on, a
gesture with no travel -- since each leaves a preview describing an
edit the record does not hold, with no landing coming to correct it.
The three exits are three journeys and the guard walks each; an entry
aimed at one of them SURVIVED until the test grew that arm. Left open
deliberately: a record with no rebuild behind it, where the preview
still agrees with the change list.

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

It was found from a runner -- about one run in eight here, three legs
failing on the drag guard's own premise -- and a stack printed from a
patched `show_topology` named the caller on the first failing attempt
(M-15).

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
saved already -- correctly, since the first press repoints every layer
at the file and this is therefore the SECOND press on any map. The
data needs no writing; what still happens is the style, the name
counted as current so the drop spares it, and the record.

**THE QUESTION IS PUT TO THE FILE, NOT TO THE SOURCE STRING**, because
nobody rewriting the file underneath us can change a string we are
holding: a colleague's save that dropped `tiles_b_landcover` left a
layer naming a table that was gone, the element was skipped as saved
AND counted as written, the drop removed what they HAD written, and
the plugin said "Saved" (M-16). A layer whose table was dropped
under it still answers `isValid` True and `featureCount()` 40 and
yields ZERO features, so writing it would replace a real table with an
empty one. So the save writes what it can, REMOVES NOTHING once a file
has changed under us -- a table that looks like our own abandoned one
is as likely to be their current one -- and says which element the
file lost; the reading of what the file holds is taken ONCE, before
the loop, since asking per element opens the GeoPackage per element.

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

**AND IT IS EVERY CONTROL THAT ACTS, WHICH IS A LIST RATHER THAN A
PAIR.** `CONTROLS_A_PUMP_TAKES_DOWN` is taken and restored by one owner
that both pumping acts call, so a fourth control joins a list rather
than being remembered at two sites; LOAD was live through every write
until 2026-09-02, and a Load delivered by the save's own pump
repointed every element layer mid-loop (M-17).

WHAT IS DELIBERATELY NOT IN IT: the two file CHOOSERS, since a chooser
records what you would save to or load from and does nothing on its
own. And what is NOT YET DECIDED is the rest of the acting controls --
the Topology tab's Apply, Undo and Clear, and Auto -- which are live
during a write and whose reach into the record captured after the loop
nobody has measured. That is an open question rather than an omission,
and it is on the owed list rather than repaired blind.

**The pump and the disabling are one decision.** Turning the event
loop is exactly what would otherwise let somebody press Save or
Generate into a half-written file, so both controls go down for the
duration and are restored to what they WERE rather than enabled: a
save can be pressed while Generate is already refusing for its own
reasons. The bar comes down in a `finally`, the write raising
included.

## The save's three doors, after 2026-09-02

Seven defects were repaired in one campaign day and five of them were
in the save; the accounts are M-18. What a maintainer needs to hold
in their head, because the pieces only make sense together:

**A CANCEL HAS THREE MOMENTS AND THEY ARE ANSWERED DIFFERENTLY.**
Before the write opens the file, dropping the intent IS the rollback;
between tables, `write_gpkg_layers` reads `_save_cancelled` and undoes
the transaction; after the last table, during the repointing and the
styling, nothing reads it at all, so what matters there is that the
flag does not survive -- it is cleared where the act ENDS, in the same
`finally` as `_saving_now`.

**AND THE HOLD DECLINES WHERE IT CANNOT BE SERVED.** A close or a quit
arriving during a write is delivered by THAT WRITE'S OWN PUMP, so a
hold there would wait, nested, for a flag only the suspended frame
beneath can clear. `_hold_until_the_save_lands` returns True at once
while `_saving_now` is set: nothing is lost, and the save lands the
moment the hold returns. A save merely PROMISED still opens the
window, and the mid-write cancel is reachable there.

**AND A REFUSED COMMIT IS NOT A SAVE.** OGR answers `CommitTransaction`
by RETURN VALUE, so with a shared read transaction open on the file
every table went in, the commit was refused, `written` still named
all of them and every element layer was repointed at a table never
created; the answer is read now and `written` is cleared. A WRITE
lock fails at the first feature and was always reported; only a
SHARED READ transaction reaches the commit.

**AND OWNERSHIP IS ABOUT WHAT A FILE HOLDS.** `existed` asked the
file's SIZE, and a data source OGR created and nothing wrote to is
65,536 bytes holding no layer, so a stub from a cancelled first save
read as somebody else's for the whole session and every remover
stayed off. It asks `bridge.gpkg_tables` now, and the guard asserts
BOTH directions, since a repair that made every file ours would
destroy somebody's work.

**AND A PRESS WAITS FOR A BUILD ALREADY COMING.** `_a_topology_is_owed`
asks THE FILE, which is right about whether to START a build and was
wrong about one already running -- a Save during a build in flight
wrote no motif. It answers True while a build is running or queued,
and still starts none.

**AND THE CLOSE'S QUESTION IS ANSWERED WITH THE RIGHT MECHANISM.**
`_a_save_is_outstanding` merges a promise with the keeping of it,
right for the hold and wrong for a QUESTION: the Close arm cleared a
flag that was already False and let the write finish over a file the
person had just declined. It sets `_save_cancelled` now, and the
SENTENCE is the writer's, since ours cannot be true past the last
table.

**AND THE HOLD ONLY REPORTS WHAT IT WATCHED**: it records whether a
write was under way AT THE PRESS and leaves the report to the writer,
because resuming it could not tell a write that had just finished
from a wait where nothing was ever opened.

**AND A FILTER NEVER REACHES THE FILE.** `write_gpkg_layers` iterates
`getFeatures()`, which honours a subset, so a Query Builder filter was
written as though it were the map: 41 rows to 3, and to ZERO across a
re-tile. A subset says which features to DRAW; it comes off for the
write and goes back in the save's own `finally`, and the already-saved
question is asked without it.

**AND THE LAYER IS THE AUTHORITY ON WHAT ITS TABLE IS CALLED.**
`_element_tables` is filled by a LANDING and cleared by nothing, so
the witness is asked for EVERY element rather than only those the
record has never heard of; a drawn map's layers answer from memory at
the first save and from those very names afterwards, and a Save As is
answered None by construction.

## What a resume writes on the layers, and why it must

`_recover_the_source` returns the source it LANDED ON, and the group's
record is stamped with that rather than the record's own region, since
a self-contained file names the SENDER'S path. `_our_groups` asks the
LAYERS, so stamping the group alone left the two disagreeing, the
binding let go of the map just opened, and the next Generate built a
rival group whose Save wrote into the opened map's own tables -- at
both doors, which is what said the defect was older than the flag
that revealed it (M-19). `_tell_the_layers_which_region_we_landed_on`
is called from both branches and stamps NOTHING where the recovery
landed on nothing.

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

**CLOSING THE PLUGIN WINDOW ASKS TWO DIFFERENT QUESTIONS**, and which
one it asks is the difference between dropping an intention and
destroying work. (Maintainer's ruling, 2026-09-02: "a panel's close
button shouldn't stop a save, it should prompt whether to interrupt
save".) A WRITE UNDER WAY is asked about in its own words --
"Interrupt the save when closing?" -- with No as the default, and only
Yes sets `_save_cancelled`. A PROMISE NOT YET KEPT keeps the older
question below, because nothing has been opened and there is nothing
on disk to lose.
WHAT No DOES is written at the code rather than implied: the write is
not interrupted and the window closes, the save finishing in the frame
beneath and reporting for itself. It cannot WAIT there -- the close
arrives on the write's own pump, so holding would suspend the only
frame that can clear the flag.
ONE QUESTION USED TO COVER BOTH, which is ledger row 5's lesson one
layer up: the predicate was mended for merging a promise with the
keeping of it, and the question built on it went on merging them.

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

The button was briefly DISABLED during the write instead, and the
maintainer chose to ship the callback (2026-09-01) rather than grey a
control at the moment somebody most wants it (M-20).

A CANCELLED FIRST SAVE LEAVES AN EMPTY FILE, because the writer
creates the data source before the transaction opens. That follows the
existing behaviour of a FAILED write rather than being a new decision,
and it is why the sentence says the MAP was not written rather than
that nothing was.

**AND THE FLAG DOES NOT OUTLIVE THE ACT IT WAS SET FOR.** On the
commonest journey -- a wait for a REDRAW or a topology build -- nothing
opens the file and nothing consumes `_save_cancelled`, so left
standing it stopped the person's NEXT save (M-21). It is cleared
where the intent is dropped, safe in both directions since a write
that DID read it has already returned. THE GENERAL FORM: when a repair
adds state read by ONE consumer, enumerate the journeys where that
consumer never runs, and say at the line what clears it there.
Guarded by `a-cancel-does-not-poison-the-next-save`.

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

The third route is why this matters: a self-contained file records the
region its SENDER drew from, a path that does not exist on the
recipient's machine, so stamping the group with the record leaves
`_point_the_chooser_at` finding nothing -- with two senders' maps
open, returning to the first gave it the SECOND sender's data, and the
next Save would have written it over the first sender's file (M-22).
The fallback to the record survives for the case where recovery lands
on NOTHING, since capturing the chooser then would file the resumed
group under a dataset it was not made from.

## The tiled frame is held between runs, and what the key is made of

A Generate is mostly the JOIN: the overlay computes an argmax on AREA
and keeps a tile id against a zone id, throwing the fragments away --
1.034s of a 1.36s run at spacing 250, about 2.1s of 3.8s at 150. That
answer does not depend on WHICH attribute is displayed, so changing an
element's variable was paying for a tiling it already had.

`_tiled_frame_for` and `_keep_the_tiled_frame` hold it, `_caching_is_on`
reads the switch on Map options, and `_forget_the_tiled_frames` drops
it. THE KEY IS `_geometry_signature(without_variables=True)` -- the
signature ITSELF with its two variable terms blanked, not a copy of it.
That matters more than it looks: "what changes the tiles" has been
widened three times here, for a topology edit, for the dual and for
the per-element split's own field, and every one of those fixes landed
in that one function. A second enumeration beside the cache would have
to be widened a fourth time by somebody who did not know it existed,
and a cache that has not heard about a new term hands back the tiles
of a different design.

IT IS A PLAIN PYTHON OBJECT ON THE DIALOG, never a layer and never a
layer field, and that is what holds ruling 6 BY CONSTRUCTION rather
than by every writer remembering to. `_save_the_map` builds its write
list by iterating ELEMENT IDS rather than the group's children, so it
cannot write what it does not know about; QGIS serialises layers into
a .qgz and not a dialog's attributes; and `_only_this_elements_data`
is an ALLOWLIST over the source's columns, so a column the cache joins
for its own reasons cannot ride onto a layer and from there into
somebody's file. That last was a blocklist until 2026-09-05 and the
two forms agree only while nothing joins a column nobody mapped --
which is precisely what this cache does.

WHAT IT DOES NOT SKIP is `gdf_to_layer`, 0.239s at spacing 250 and
1.728s at 150, because `split_out_the_no_data` puts the rows a
graduated renderer cannot draw onto a PAIRED layer and which rows
those are is the variable's business. A switch therefore changes layer
MEMBERSHIP and not merely values -- measured at 0.0% of tiles on the
packaged Auckland data, whose nulls sit in the same six areas for
every variable, and 20.2% at worst on a multi-source shape. The design
for closing that is in ROADMAP.md with its four hazards.

## Four queues, because a press, a tick, a save and a Load are not one fact

One run at a time is settled, so anything asking for a run while one
is in flight is REMEMBERED and honoured when that run lands. Until
2026-08-28 a press and a live tick shared one flag, and with live
update off a remembered press was discarded in silence at the live
path's second gate, leaving layers tagged for elements the design no
longer had (M-23).

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

**AND THE FOURTH ARRIVED THE DAY AFTER THAT**, out of the sentence
above: the chooser being re-read is what makes a promise obey somebody
who changes their mind, and a LOAD moves that chooser while meaning
something else entirely -- where the map being OPENED lives. So a Load
pressed inside a promise's window consumed the promise against the
other file and the person's own map was never written.

`_load_pending` is a Load deferred behind a promised save (maintainer's
ruling, 2026-09-02: the save happens first, then the load).
`_honour_a_queued_load` performs it when the promise ENDS -- kept or
dropped, since either answers what the deferral asked -- and it is
connected beside `_honour_a_queued_save` at all three of that one's
sites, so a promise ending by any route lets the Load through in the
order the person asked for.

ONLY THE PROMISE IS ASKED ABOUT, and that is what keeps this door away
from the nested wait that froze the window on the same day: Load is in
`CONTROLS_A_PUMP_TAKES_DOWN`, so it is disabled for the whole of a
write and no click can be delivered by the write's own pump.

AND THE ORDER IS TWO CLAIMS, each with its own catalogue entry: the
save must land on the person's OWN file, and the Load must then
happen. A repair that protected the first while swallowing the second
would satisfy any reading of the ruling and leave a button that does
nothing.

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
graph, 0.8 to 21 seconds across the catalogue with `hex-colouring 7`
at the slow end (the narrower figure this paragraph once carried
justified a synchronous build inside a save, M-24; docs/TOPOLOGY.md
has the spread and the decomposition). It is queued by whatever
rebuilds the UNIT and never by a colour or a ramp, the boundary
`_geometry_signature` already draws for re-tiling, and
`_topology_stamp` tells a landing whose topology it is holding, so a
build that finishes after the design has moved on is discarded rather
than drawn against a unit it does not describe.

**And the tab SAYS when it is working.** A build is queued by whatever
rebuilds the unit and lands seconds later, and in between the panel
still holds the PREVIOUS design's topology -- so an edge somebody
clicks there is not the edge that would move.
`TopologyPanel.say_a_build_is_coming` writes "Working out the design's
structure…" from the moment the work is QUEUED, and `set_unit` clears
it wherever a build lands, so no route has to remember to.

Greying the tab was tried first and taken out the same hour
(maintainer, 2026-09-01), since it takes the tab away mid-edit and
retires a contract two registered tests state. And the message is its
own label rather than `note`, which already means "the answer, or the
reason there is none" and which the suite's `_settle_topology` reads
as an answer having ARRIVED: one store, two meanings, met in a QLabel
(M-25).

**AND A BUILD QGIS NEVER STARTS IS SAID TO BE ONE.** A task was
measured sitting `Queued` for 133 seconds with the pool reading
`active=0 max=8`, so `TOPOLOGY_START_CEILING_MS` arms a watch when the
task is added and `_say_if_the_build_never_started` writes the reason
into the panel's NOTE, which every waiter reads. It asks about STARTING
and never about duration, so no slow design can reach it; it SAYS
rather than cancels, since a pool busy with another plugin's work is a
legitimate reason to wait; and it is keyed to the task by identity.
The cause is undiagnosed and this does not claim to fix it -- the
discriminator rides in `tools/probes/how_often_a_build_never_starts.py`
(ROADMAP.md, R-4). A path is never hard-wrapped inside its backticks,
since the gate that reads these references matches one line. (M-3.)

**Not every design has a topology.** `Topology` needs a GAP-FREE
tiling, so a design with insetting or a family that does not close up
refuses, and `can_build` says which it is in words rather than letting
the constructor raise. Zigzag additionally needs its unit REPAIRED
first: the manipulation emits repeated vertices — six coincident pairs
among thirty-seven points on the case measured — which is what makes
the result invalid, not floating point and not the amplitude.

**THE REPAIR IS UPSTREAM'S OWN**, `tiling_utils.get_clean_polygon`,
which removes corners that are merely VERY CLOSE and then the colinear
ones where this module's dedupe removed only exact repeats; with it
first, all four measured designs draw where ours alone refused two
(`tools/probes/zigzag_cleaners.py`, both arms in one run; M-26).
OURS IS KEPT AS THE FALLBACK because this is a VENDORED dependency and
a re-vendor that dropped the function would take the repair with it
in silence; `make_valid` runs on whatever survives both.

### How somebody takes hold of it: select, then act, then a handle

Settled 2026-08-30, after the maintainer asked whether the interaction
was intuitive first time, powerful, and whether anything better
existed. The honest audit said no, moderately, and yes, so the tab was
rebuilt around three rules.

**SELECT, THEN ACT.** A click lands on whatever is under the pointer:
`_refresh_classes` lists every class of BOTH kinds and
`_refresh_manipulations` narrows the VERB to what suits the selection,
the opposite of the mode-first arrangement it replaced, where the
drawing highlighted an edge the panel would not select.
`_rebuild_arguments` no longer refills the class list, or the two
would recurse without end.

**A HANDLE IS THE CHOICE OF MANIPULATION**: `view.grabbed` carries the
manipulation to the panel, which sets its own chooser from it, so the
handle and the chooser cannot disagree and the tab is usable without
touching the chooser at all. **THREE HIGHLIGHT STATES, BECAUSE AN EDIT
APPLIES TO A CLASS**: held, classmates tinted, and what is under the
pointer, where two states lit half the drawing. **AND THE HIT TEST
FOLLOWS THE EDGE**, `_distance_to_edge` measuring to the nearest point
ON the line rather than to a disc at its midpoint, with the vertex
reach down from 12px to 8 because 12px at each end claimed more than
half of a median 43px edge. (M-27.)

**AND IT WAS REBUILT AGAIN ON 2026-08-31**, on the maintainer's report
that the tab was unusable and their standard for what would fix it: it
"should be easy to use and easy to learn", it "has to be perceivable",
and "hover states aren't as good as shapes that make sense".

Four things changed, each argued in docs/TOPOLOGY.md (M-28). THE
VIEW FITS THE UNIT, NOT THE PATCH: `n_tiles` is the library's count of
the unit's own tiles, and the neighbouring copies draw as context
running off the edges, where fitting all 36 drew the thing being
edited at a third of the size. EACH HANDLE IS A PICTURE OF WHAT IT
DOES -- a double-headed arrow for stretch, a curved arrow for turn, a
wave for zigzag, a four-way cross for a free move, an arrow on a rail
for a push -- since a hover label must be discovered before it can
teach and a first-time reader never hovers. A HANDLE IS A POSITION,
NOT A DISTANCE TRAVELLED, the zigzag's amplitude included since
2026-09-05, so where the pointer has taken the end handle IS a polar
coordinate about the edge's middle -- and a click that slips under
half a seat of travel from the grab point records nothing, the
amplitude's threshold being sized from the glyph as the count's
deadband is, since the box's floor was under a pixel on the tab's own
edges (grilled 2026-09-05, C-319; the count is even from the same
grilling, `_even_count` settling a typed odd one up; and since
2026-09-06 the count's seat along the edge interpolates the even
counts between 0.25 and 0.60 of it, C-336, while the Amplitude box
shows the crest's distance and holds `h`, C-337); and A POINT WITH
NO LABEL IS NOT HIT-TESTED OR SEATED, since a zigzag adds two hundred
unlabelled corners. AND EVERY MANIPULATION IS REACHABLE ON THE DRAWING:
`push_vertex` has a rail along the one direction a push can take, and
no handle at all where that direction cancels.

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
reach in a fixed order: turn and zigzag stand at 30 and 60 along the
same normal now, having been 20.4px apart inside a 26px reach on two
designs of three; the other side of the edge was tried first and lands
on the vertices, which are tested after handles (M-29).

WHAT IS STILL NOT BUILT is the audit's other design, merging scale and
rotate into one end handle. It is refused rather than pending: one
handle would have to say two things, which is what the glyphs exist not
to do. The argument is in docs/TOPOLOGY.md.

### What a drag means, and in whose units

Four things had to agree before a drag meant what it looked like, and
on 2026-09-01 none of them did.

**FRACTIONS IN THE RECORD, MAP UNITS AT THE LIBRARY, AT BOTH PLACES.**
`dx`, `dy` and `push_d` are absolute displacements in the unit's own
coordinates and the controls offer fractions, so
`topology_edits.in_map_units` multiplies -- and it had exactly ONE
caller, the commit path, so a gesture's two halves disagreed by the
span of the unit: 70.71 committed against 0.10 previewed.

**AND THE TWO SPANS MUST BE THE SAME SPAN**: `TopologyView.unit_span`
answers the same question as `topology_edits.unit_span`, `max(width,
height)`, where the view once divided by the width alone -- 1.268x on
laves and exactly 1.000x on a square design, which is why every
example tried by hand hid it.

**THE FRAME IS HELD FOR THE LENGTH OF A GESTURE.** `_fit` returns early
while `_press` is set and resumes at the drop, since re-measuring the
drawn extent on every paint made the transform an output of the thing
the gesture was changing: a nudge held still climbed 0.104 to 0.356
over six repaints.

**AND A DRAGGED VALUE IS HELD INSIDE ITS OWN BOX** on both vertex
branches as on the three edge ones, because the record is what the
drop keeps.

**THE DUAL REPEATS ON WHATEVER LATTICE THE TILEABLE HAS**:
`_lattice_offsets` takes the two shortest non-parallel translations
out of the vectors' VALUES, key-shape agnostic, where a lookup by
`(1, 0)` and `(0, 1)` missed every hex-keyed family and drew one copy
in silence. (M-30.)

### Rotating and scaling an edge keep the tiling

The library's `rotate_edge` and `scale_edge` move an edge's endpoint
vertices about its own midpoint and write them back last-write-wins,
which tears the tiling: on every design tried the per-edge result builds
no topology. `apply` reroutes both `how == "rotate_edge"` and `how ==
"scale_edge"` to `_move_edges_vertex_consistent`, which takes one
displacement per lattice orbit (`base_ID`) from the unmoved positions,
averages it, and applies it to every copy, as `transform_geometry`
applies `push_vertex`. One vector per orbit is a lattice-periodic
displacement, so the edited unit still tiles with its own translates.
Where symmetry forces that displacement to zero the edit moves nothing
and the `_same_shape` branch names the symmetry, since the per-edge move
there is a torn non-tiling and no gap-free rotation of that class
exists.

The soundness mark and the drawn hatch read `plane_coverage`, not
`gaps()`. `gaps()` finds only holes enclosed within a patch, so a tear
where the units pull apart (a gap open onto the surrounding space) read
as sound; `plane_coverage` measures the coverage of one fundamental
cell and catches gaps and overlaps alike. Both reformulations live here
rather than in the vendored library, so it stays as upstream ships it
and the change is easy to withdraw. The account, the alternatives and
the images are in
`docs/process/rotating-and-scaling-an-edge-without-tearing-the-tiling.md`
(C-341); it ships experimentally as a candidate and may be reshaped.

### What a drag shows while it is happening

(Maintainer's principle, 2026-09-06, and four rulings of 2026-09-07 in
CLAUDE.md.) The preview must never let a person imagine a move will be
allowed when it will not, so a gesture carries one of three states and
the drawing says which.

**THE STATE IS THE VIEW'S, THE JUDGEMENT IS THE PANEL'S.**
`TopologyPanel._status_of_a_drag` answers `{clamped, failed, reason,
key}` and `TopologyView.set_drag_status` holds it; the tile outlines
take their pen from it -- ordinary, amber where a value is held at its
limit, red and dotted where the previewed design cannot be tiled.

**FAILED ASKS COVERAGE, NEVER `gaps()`.** The scaffolding for this
predated C-341 and judged validity with the check that finds only holes
ENCLOSED within a patch, so a move pulling the units apart would have
previewed as sound -- the blind spot arriving in the one drawing whose
whole job is honesty about validity. `plane_coverage` answers gaps and
overlaps alike and each has its own sentence.

**THE VALUE HOLDS AT THE LAST ONE THAT LAID OUT.** Where the next step
raises or cannot be laid out, `_drag_last_good` is put back and the
state is CLAMPED: the pointer keeps going and the number does not. No
ceiling is computed for this, because the drag has already evaluated
the predicate -- a frame's transform is 158 ms and a ceiling probe 161
ms, being the same call -- and a true ceiling costs 1.4 s, which is a
freeze at the moment somebody starts dragging. The commit-time clamp
in `topology_edits.apply` then applies the exact ceiling at the drop,
so the two compose and a fast drag that stops short is corrected on
release.

**AND THE CUE IS ANCHORED TO THE FRAME THE GESTURE BEGAN IN.**
`_draw_what_the_move_bears_on` draws the pivot a rotate turns about and
a scale holds fixed, the edge a zigzag rides on, and a dashed arc swept
from where the edge's end WAS to where the pointer has taken it --
all against `grabbed_edge()`, captured at the press. Never the
preview's own geometry: a pivot that moves with what the gesture is
changing stops being the point that stays still, and re-deriving a
paint-time anchor from a gesture's own preview is the loop `_fit`
already paid for.

**THE STATE COMES DOWN AT THE DROP, THROUGH A `finally`.** The preview
is deliberately KEPT where an edit was recorded, since clearing it
there put the un-edited design back for 1.7 seconds; the colour is not,
describing as it does a pointer that is no longer down. The `finally`
covers every exit including one added later -- and the exit that needs
it is the one that RECORDS, since a gesture recording nothing leaves
through `show_preview(None)`, which clears the status for its own
reasons and made the first catalogue entry survive.

**AND THE SENTENCES ARE KEYED BY MANIPULATION.** `_HELD_SENTENCE` has
one per move with a fallback, because a single sentence written while
zigzag was in hand told somebody dragging a ROTATE that "a deeper wave
than this runs beyond the edges next to it". Found by rendering the
gesture; the refusal beside it carried the same fault (T-147).

**AND THEY ARE PAINTED IN THE DRAWING**, across its foot, in the
colour the outlines take (maintainer's ruling, 2026-09-07; C-344).
They were written into `reason` and read by nothing for a day: the
paint took `failed` and `clamped` for a pen colour and stopped, so
rendering the widget with the reason replaced or emptied gave
byte-identical pixels. The drawing is where the eye already is during
a gesture, and a sentence there DIES WITH THE PICTURE, so no clearing
has to be remembered -- where `note` already means two things and the
suite's own settle helper reads text there as an answer having
arrived.

**AND THE DROP REFINES WHAT THE DRAG HELD**, three bounded probes
toward what the pointer asked, each halving the gap
(`_refined_towards_what_was_asked`, `_REFINING_STEPS`). Holding at the
last value that laid out leaves a shortfall bounded by a FRAME of
travel -- 0.42 of the amplitude at 250 px/s against a ceiling of 0.594
-- so what somebody ended up with depended on how fast they moved the
mouse. Nothing is computed at the press, where 1.4 s would be a
freeze; half a second at the end of a gesture is not. The discrete
arguments are not interpolated, a count between two even numbers being
a value no control can hold, and `_this_frame_laid_out` is the ONE
site that keeps `_drag_last_good` and forgets `_drag_reached`, since a
pair written in two places comes apart -- as it did, letting a gesture
that ended at 0.100 record 0.350.

**AND THE PUSH RAIL CARRIES NO GAIN.** `push_d` is a DISTANCE: the
drag divides travel by the vertex's own gain (`push_gain`,
`_push_for_travel`) so the ground follows the pointer, while the
record keeps the library's parameter, as the Amplitude box shows the
crest and holds `h`. THE GAIN IS FROZEN AT THE PRESS beside
`_press_edge` AND TAKEN OFF THE HELD DESIGN, and the vertex is looked
up in that same topology by its `ID`: `push_vertex` reads the vertex's
point from its ARGUMENT and its neighbours from the TOPOLOGY, so both
halves must come from one store. Each of those three is a separate
door and each was found, in turn, by a hunt aimed at the repair before
it (ledger rows 9, 10 and 12 of 2026-09-07).

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

`_same_shape` answers that last one by comparing the GROUND, symmetric
difference over the unit's own area, with the measurement at the
function -- after three wrong forms: an absolute tolerance, a
statistic, and `shapely.equals_exact`, which compares coordinate
sequences the library restarts on the way past (M-31).

**Edits are SHELVED by design**, under `topology_edits.shelf_key`,
which is the family, the element count and how many times over the
dual is taken, 0 for the design itself. Move the design away and the edits go quiet; bring it back
and they return. This is the same shape as the per-field scheme
memory: what stays ACTIVE changes, what is REMEMBERED does not.

**AND EVERY OTHER DESIGN TERM STAYS OUT OF THE KEY, WITH THE REPLAY
REPORTING INSTEAD** (maintainer's ruling on conflict 7, 2026-09-05).
A scale in one axis splits the default design's two edge classes into
four, so a replayed `a` names a different set of edges while the
change list reads the same. Widening the key would have an ordinary
modifier tweak put somebody's edits away; so each edit records the
alphabet it was aimed against at the panel's one recording door, and
`apply` compares that with the design it replays onto and says, in
`CLASSES_MOVED`, that the classes have moved -- still applying what
the labels name now. Guarded as a topology-matrix aftermath.

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

**THE DROP WAS WRONG FOUR TIMES AND WAS REDESIGNED RATHER THAN
PATCHED A FIFTH.** All four asked whether we MAY drop, and none
recorded WHAT THE TABLES ARE ABOUT -- which the file can answer for
itself. So the file carries a key, `topology_design`, beside the two
tables: the family, the element count, a digest of the unit's options
and a digest of the EDIT LIST, as a string because JSON has no tuple.
The rule is then a comparison and needs no build:

    wrote both frames                      the key is this design's
    tables present, key DIFFERS, file ours drop both
    tables present, key equal or ABSENT    leave alone, keep its key
    no tables                              nothing to do

A file with no key of ours is left alone, and the key is carried
forward unchanged when the tables are spared. The branch discarding a
topology of another design decides nothing any more since the build
moved off this thread, and its catalogue entry is retired with that
measurement; `_topology_stamp` carries the MODIFIERS, which it omitted
until the redesign found a landing about the wrong design being shown.
The four faults, kept because the shape recurs, are M-4: read them
before touching `_write_or_drop_the_topology`.

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

**THERE WERE TWO DOORS UNTIL THEN**, the second a standing "Create as
new group" checkbox on Map options whose readers disagreed with the
flag's -- five sites read only the box, one only the flag, one both --
and the maintainer retired the checkbox rather than teaching the two
to agree, since a boundary between "once" and "always" that will
never read clearly is one nobody should have to hold in their head
(M-32). The retirement was a DELETION at the landing, `force_new`
already reading the flag as one of its four terms.

## The Design tab's layout, and what decides it

**WHETHER A FORM'S FIELD COLUMN STRETCHES IS DECIDED BY THE STYLE**:
macOS's default `fieldGrowthPolicy` is `FieldsStayAtSizeHint`, Fusion's
is `AllNonFixedFieldsGrow`, and QGIS ships Fusion as a style people
select -- so this document asserted a cause without that qualifier
until it was measured on both. The policy is set explicitly on both
forms by `_settle_a_form`, and the widths come from the controls:
`_ask_for_a_name_s_width` gives the two choosers `NAME_CHARACTERS` of
room in characters, since a pixel width is a claim about one machine's
font; the seven modifier boxes take the widest of the seven, because a
spin box sizes to its MAXIMUM's text; a hidden family-option row uses
`setRowVisible`, since a form reserves height for a row whose field is
a layout; `Auto` is not the default button. **Four rows share one field
width** through `_field_block`, fixed to the region chooser's own
sizeHint, which is font metrics and honest before a layout pass.

**A SHOW-TIME PASS FOR THE LAST THREE PIXELS WAS TRIED AND WITHDRAWN**:
widening short labels in `showEvent` grows their form's shared column,
the furthest edge moves, and the next show does it again -- 1296 to
1618 px in one run, the third failed repair to this layout wearing new
clothes. **The guard sets the style** to Fusion, compares each
control's width with what it asked for, keeps the glyph checkbox as its
positive control (the region chooser had been, and was the defect
itself), and restores the style in a `finally`.

**THE WINDOW IS SIZED BY THE TAB IN FRONT, AND GROWS WITHOUT
SHRINKING** (maintainer's ask, 2026-08-30): `_size_to_the_current_tab`
makes the page in front `Preferred` and every other `Ignored`, so
Design opens at 825 px where it opened at 1296 and Data & colours grows
it to 1296. `COLUMN_SUM_BUDGET` is `MAX_WINDOW_WIDTH - 400`, the 400 a
measured allowance for everything that is not the table, so the two
are re-derived together or not at all. The measurements are M-6.

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

## The motif in the file: replaced when stale, built off-thread, keyed without the CRS

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

**AND IT RUNS OFF THE MAIN THREAD, WITH THE PRESS DEFERRED BEHIND
IT.** (Maintainer's decision, 2026-09-01.) It was synchronous until a
save on `hex-colouring 7` was measured at 27.53 s with the build 27.22
of it and no repaint for 27.29 -- the hang the ruling of 2026-08-29
exists to prevent, arriving through the door that ruling opened. So
`_save_the_map` asks `_a_topology_is_owed` before it writes, queues the
build with `even_if_unasked=True`, sets `_save_pending` and says the
map will be saved once the structure is worked out;
`_honour_a_queued_save` writes when the build lands. Deferred rather
than refused, since a save that quietly did not happen is somebody
closing QGIS believing their map is on disk. `_topology_built_for`
records which design a build was ATTEMPTED for, whatever came back, or
a design with no topology would defer for ever. (M-5.)

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
re-applies every plugin patch, reporting each one.

**FOUR FAMILIES ARE CARRIED, and three of them are PERFORMANCE patches
offered upstream**; know what is carried before you read a re-vendor
report. The commit rule paid for itself on 2026-08-31: bf1bbbf to
6190917 carried TWELVE commits with the version string `0.0.7.89` at
both ends, and two patches retired themselves in that round when
upstream dropped the scipy spline, the tool NAMING them rather than
writing a broken vendor (M-33).

| family | what it does | offered upstream |
|---|---|---|
| **1a-1e** | matplotlib and scipy imports made optional, since QGIS bundles neither | no -- it is ours, about our packaging |
| **3** | the join lookup's pandas idiom: `.agg("idxmax")` rather than the FUNCTION, which defeats the cython path | ROADMAP.md |
| **4a-4d** | the grid disc reaches only what the region occupies, keeping the any-rotation promise | `docs/process/upstream-note-the-grid-disc-is-larger-than-it-needs.md` |
| **5a-5d** | a caller may DECLARE which rotations it will ask for; default `None` is today's behaviour exactly | the same note |
| **6** | the overlay clips only the tiles that straddle a zone boundary | `docs/process/upstream-note-the-overlay-clips-what-it-already-knows.md` |

**AND TWO PAIRS OF THEM CHAIN**: patch 6 anchors on the block patch 3
produces, and 5b on the tail of the method 4b produces. Fine on a
re-vendor, and it broke the cheap self-check -- run the tool with our
OWN vendor as upstream and every patch should say "already present",
which is what catches a hand-edited vendored file
(`test_the_vendoring_tool_reproduces_the_current_vendor`). A
superseded patch cannot say that of its whole form, so `targeted` takes
`superseded_by` and `landed` together, a mark the patch itself writes
and the anchor does not already carry, and the tool asserts both.
(M-7.)

WHAT TO DO WHEN ONE OF THEM FAILS TO APPLY. The tool NAMES the patch
rather than writing a broken vendor, and for the performance family the
honest first question is whether upstream has taken it -- in which case
retire the patch as patch 2 was retired, rather than re-anchoring it.
Each carries its measurement and its probe in
`docs/PERFORMANCE.md`, so "is this still worth carrying" is a question
with an answer.

AND PATCHES 4, 5 AND 6 ARE EXACT RATHER THAN MERELY FAST, which is what
makes them safe to re-apply blind. Each has a committed probe that
compares the map tile by tile -- 64 comparisons across four rotations
for patch 4, 12 for patch 5 plus a negative control that must bite, and
37,511 tiles for patch 6 -- and each has registered tests and catalogue
entries. If a re-vendor makes one of them stop applying, run its probe
before deciding what to do: a patch that no longer changes the output
is one upstream has adopted. (A convex-hull performance fix used to live here too; on
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
inputs -- the VENDORED library at the commit `VENDOR-VERSION.txt`
records, which is the only thing the comparison measures and the only
claim it makes (maintainer's ruling, 2026-09-05; the web app pins an
older library and is no longer spoken for). It needs a Python with
geopandas *and* matplotlib —
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

**AND THE LIVE PATH REFUSES ONLY THE TILING.** `_maybe_live_generate`'s
sixth gate is this same availability question and a debounced tick
never reaches `_generate`, so a ramp picked after the file moved was
refused with a false sentence; the gate tries `_restyle_only()` before
refusing, attempted AT the gate because `_extent_in_working_units`
below it would read the dead extent. `_generate`'s restyle fast path
already sits ABOVE its own check, an asymmetry guarded by
`the-button-restyles-before-it-asks-about-the-source`. Each of the ten
gates names itself behind `WEAVINGSPACE_ADOPT_DUMP` -- `LIVE-GATE
source-gone`, `LIVE-GATE too-many-tiles` -- after live update stopping
in silence had cost two diagnoses (M-34).

The general form, which is the reason this paragraph exists at all:
when a guard starts answering differently, follow its return value
into every TUPLE it is a member of, not only into its callers. And
when you name the SITE of a defect, measure it: a location reasoned
out of the source reads exactly like a location that was proved.
