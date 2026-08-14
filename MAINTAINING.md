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
4. **Generation must stay size-guarded.** Tile count grows with
   1/spacing²; the estimate in `bridge.estimate_tile_count_bounds`
   runs before every generation, including live updates.

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
current vendor is upstream v0.0.7.61 at commit 80e1dab — note that
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
