#!/usr/bin/env python3
"""What the coverage warning costs, measured rather than assumed.

The warning ("At 1,500 m spacing, 15 of 155 areas received no tiles
and appear nowhere on the map") is only worth having if it is close to
free, because it is computed on EVERY run, including the debounced
live ones. The budget the project set for it is 15% of the run's own
time. This harness is how that number was arrived at, and how to
re-check it after any change to the worker path or to the vendored
library.

WHAT IS BEING TIMED
-------------------
The worker's exact code path, on the packaged Auckland data
(tests/data/imd-auckland-sa2-2018.gpkg: 155 SA2 areas, EPSG:2193, the
same file tests/run_tests.py uses for its real-data test), across the
spacings a cartographer actually explores on it:

* WITHOUT: build the region frame, strip its CRS as the dialog does,
  then ``Tiling(unit, region).get_tiled_map(...)`` with the plugin's
  own arguments. This is what dialog._generate's ``work`` closure did
  before the warning existed.
* WITH: the same, plus ``bridge.add_unit_ids`` on the region before
  tiling and ``bridge.count_units_without_tiles`` on the result.
  That is the whole of the added work: one integer column that rides
  through the library's own attribute join, one hash over that column
  at the end, and the column dropped in place.

Everything timed here happens on the worker thread, which is the
conservative denominator: a run also does main-thread work afterwards
(a layer per element, renderer seeding, possibly a GeoPackage write)
that the warning does not touch, so the overhead as a fraction of what
the USER waits for is smaller than the figure printed here.

HOW THE NUMBER IS MADE HONEST
-----------------------------
Three things, each of which changed the answer when it was added:

* PAIRING AND ALTERNATION. The two arms run interleaved, and the order
  within each pair alternates, so a machine that slows down partway
  through (another process arriving, thermal throttling) penalises
  both arms rather than whichever ran second. The headline figure is
  the median of the PER-PAIR differences, which cancels drift that a
  difference of separate medians does not.
* AN A/A CONTROL. The same measurement is run with both arms doing the
  identical plain tiling. Whatever overhead it reports is noise, and
  it sets the resolution of the whole exercise: a with-versus-without
  figure near the A/A figure means "too small to measure here", not
  "measured and small". On the development machine A/A lands around
  1%, and single unpaired runs have been seen to differ by 30% or
  more, which is exactly why the first version of this script (median
  of one arm against median of the other, no control) reported 9% for
  a computation that a stopwatch inside the worker puts at 0.2 ms.
* THE ISOLATED COST. The count and the column-drop are timed on their
  own as well, so the report can separate what the plugin's own code
  does from what the extra column costs while passing through
  geopandas.

The first pair at each spacing is discarded as warm-up: geopandas,
shapely and the STRtree paths are cold on the first pass and it reads
tens of percent slow in both arms.

RUNNING IT

    QT_QPA_PLATFORM=offscreen \\
      PYTHONHOME=<qgis>/Contents/Frameworks \\
      PROJ_LIB=<qgis>/Contents/Resources/qgis/proj \\
      QGIS_PREFIX_PATH=<qgis>/Contents/MacOS \\
      <qgis>/Contents/MacOS/python3.12 tools/measure_coverage_warning.py

Options: ``--spacing 1500`` (map units, repeatable), ``--pairs 15``,
``--budget 15``. Exit status is 0 while every spacing stays inside the
budget, 1 when one does not, so this can be re-run as a check and not
only read as a report. Run it on an otherwise idle machine; the
project's own rule about never running two full suites at once applies
here with force, since this measures milliseconds.
"""

from __future__ import annotations

import argparse
import copy
import os
import statistics
import sys
from time import perf_counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "weavingspace_qgis", "vendor"))

DATA = os.path.join(ROOT, "tests", "data", "imd-auckland-sa2-2018.gpkg")
# the two variables the real-data test maps, so the region frame
# carries the same columns through the join as a real run's does
FIELDS = ["imd", "employment"]
# the design tests/run_tests.py uses for that test: a four-element
# Laves tiling, a middling element count and so a middling tile count
# for any given spacing
TILING_TYPE, CODE, CRS = "laves", "3.3.4.3.4", 2193


def build_unit(spacing: float):
  """A CRS-less tile unit at this spacing, as the worker receives one.

  Args:
    spacing: the pattern's grain in map units (metres, for this data).

  Returns:
    A TileUnit with the CRS stripped from it and from each of its
    frames, exactly as dialog._generate does before handing it to the
    task: pyproj must not be touched off the main thread, and a unit
    still carrying a CRS would invite that. Built once per spacing and
    reused, as the dialog reuses the unit it built for the preview.
  """
  from weavingspace import TileUnit
  unit = copy.deepcopy(TileUnit(tiling_type=TILING_TYPE, code=CODE,
                                spacing=spacing, crs=CRS))
  unit.crs = None
  for attr in ("tiles", "prototile", "regularised_prototile"):
    part = getattr(unit, attr, None)
    if part is not None:
      part.crs = None
  return unit


def run_once(unit, region_source, with_coverage: bool) -> dict:
  """One tiling, timed, with or without the coverage computation.

  Args:
    unit: the tile unit from ``build_unit``.
    region_source: the region GeoDataFrame, CRS already stripped.
      Copied here, because Tiling mutates what it is given (it adds
      and removes its own DZID column) and the coverage column would
      otherwise accumulate across runs.
    with_coverage: time the new path rather than the old one.

  Returns:
    A dict with ``total`` (seconds for everything the worker does),
    ``coverage`` (seconds inside count_units_without_tiles, 0.0 for
    the plain arm), ``rows`` (tiles produced) and ``missing`` (areas
    left empty, None for the plain arm).
  """
  from weavingspace import Tiling
  from weavingspace_qgis import bridge
  region = region_source.copy()
  id_column = bridge.add_unit_ids(region) if with_coverage else None
  unit_count = len(region)
  start = perf_counter()
  tiled = Tiling(unit, region, as_icons=False).get_tiled_map(
    join_on_prototiles=False, retain_tileables=False,
    ragged_edges=True).map
  missing, coverage_seconds = None, 0.0
  if with_coverage:
    mark = perf_counter()
    missing = bridge.count_units_without_tiles(tiled, id_column, unit_count)
    coverage_seconds = perf_counter() - mark
  total = perf_counter() - start
  return {"total": total, "coverage": coverage_seconds,
          "rows": len(tiled), "missing": missing}


def paired_runs(unit, region_source, arm_a: bool, arm_b: bool,
                pairs: int) -> dict:
  """Run two arms interleaved and summarise the paired differences.

  Args:
    unit: the tile unit both arms tile with.
    region_source: the CRS-less region frame, copied per run.
    arm_a: whether arm A computes coverage (True) or not (False).
    arm_b: the same for arm B. Setting both False makes this the A/A
      control, whose result is the measurement's noise floor.
    pairs: how many pairs to keep; one extra runs first and is thrown
      away as warm-up.

  Returns:
    A dict of medians for both arms, the median per-pair difference in
    seconds and as a percentage of arm B, the range of those
    differences, and the last run's tile count, empty-area count and
    isolated coverage time.
  """
  a_times, b_times, last = [], [], None
  for i in range(pairs + 1):
    # alternate which arm goes first, so neither always inherits the
    # other's warmed caches and memory layout
    if i % 2:
      b = run_once(unit, region_source, arm_b)
      a = run_once(unit, region_source, arm_a)
    else:
      a = run_once(unit, region_source, arm_a)
      b = run_once(unit, region_source, arm_b)
    if i == 0:
      continue  # warm-up pair
    a_times.append(a["total"])
    b_times.append(b["total"])
    last = a if arm_a else b
  deltas = [x - y for x, y in zip(a_times, b_times)]
  median_b = statistics.median(b_times)
  return {
    "n": len(deltas),
    "median_a": statistics.median(a_times),
    "median_b": median_b,
    "mean_a": statistics.fmean(a_times),
    "mean_b": statistics.fmean(b_times),
    "range_a": (min(a_times), max(a_times)),
    "range_b": (min(b_times), max(b_times)),
    "delta_median": statistics.median(deltas),
    "delta_pct": 100 * statistics.median(deltas) / median_b,
    "delta_range": (min(deltas), max(deltas)),
    "rows": last["rows"],
    "missing": last["missing"],
    "coverage_seconds": last["coverage"],
  }


def main() -> int:
  """Measure, print the table and the raw numbers, and judge the budget.

  Returns:
    0 while every spacing measured stays inside the budget, 1 when any
    of them does not. The A/A control is printed alongside but never
    fails the run: it is context for reading the other figures, not a
    thing under test.
  """
  parser = argparse.ArgumentParser(
    description="Measure the cost of the no-tiles coverage warning.")
  parser.add_argument("--spacing", type=float, action="append",
                      help="map units; repeatable (default 2000, 1500, "
                           "1000, 600, 400)")
  parser.add_argument("--pairs", type=int, default=15,
                      help="timed pairs per spacing, after a discarded "
                           "warm-up pair")
  parser.add_argument("--budget", type=float, default=15.0,
                      help="percentage overhead allowed (default 15)")
  args = parser.parse_args()
  spacings = args.spacing or [2000.0, 1500.0, 1000.0, 600.0, 400.0]

  from qgis.core import QgsApplication, QgsVectorLayer
  QgsApplication.setPrefixPath(os.environ.get("QGIS_PREFIX_PATH", ""), True)
  app = QgsApplication([], False)
  app.initQgis()
  from weavingspace_qgis import bridge

  layer = QgsVectorLayer(DATA, "auckland", "ogr")
  if not layer.isValid():
    print(f"cannot open {DATA}")
    return 1
  unit_label = bridge.map_unit_label(layer)
  region_source = bridge.layer_to_gdf(layer, FIELDS)
  # the worker never sees a CRS (pyproj is main-thread-only), so the
  # thing being timed must not carry one either
  region_source.crs = None
  areas = len(region_source)
  print(f"{os.path.relpath(DATA, ROOT)}: {areas} areas, "
        f"{layer.crs().authid()}, spacing in {unit_label}")
  print(f"design {TILING_TYPE} {CODE}, fields {FIELDS}, "
        f"{args.pairs} pairs per spacing\n")

  header = (f"{'spacing':>8} {'tiles':>7} {'without':>9} {'with':>9} "
            f"{'delta':>9} {'overhead':>9} {'count only':>11} "
            f"{'missing':>8}")
  print(header)
  print("-" * len(header))
  worst, records = 0.0, []
  for spacing in spacings:
    unit = build_unit(spacing)
    ab = paired_runs(unit, region_source, True, False, args.pairs)
    aa = paired_runs(unit, region_source, False, False, args.pairs)
    records.append((spacing, ab, aa))
    worst = max(worst, ab["delta_pct"])
    print(f"{spacing:>8,.0f} {ab['rows']:>7,} "
          f"{ab['median_b'] * 1000:>8.1f}m {ab['median_a'] * 1000:>8.1f}m "
          f"{ab['delta_median'] * 1000:>+8.1f}m {ab['delta_pct']:>8.2f}% "
          f"{ab['coverage_seconds'] * 1000:>10.2f}m {ab['missing']:>8}")

  print("\nraw numbers, and the A/A control that says how much of the "
        "above is noise:")
  for spacing, ab, aa in records:
    print(f"  spacing {spacing:,.0f} {unit_label}, n={ab['n']} pairs")
    print(f"    without: median {ab['median_b'] * 1000:.1f} ms, mean "
          f"{ab['mean_b'] * 1000:.1f}, range "
          f"[{ab['range_b'][0] * 1000:.1f}, {ab['range_b'][1] * 1000:.1f}]")
    print(f"    with:    median {ab['median_a'] * 1000:.1f} ms, mean "
          f"{ab['mean_a'] * 1000:.1f}, range "
          f"[{ab['range_a'][0] * 1000:.1f}, {ab['range_a'][1] * 1000:.1f}]")
    print(f"    paired delta median {ab['delta_median'] * 1000:+.2f} ms "
          f"({ab['delta_pct']:+.2f}%), range "
          f"[{ab['delta_range'][0] * 1000:+.1f}, "
          f"{ab['delta_range'][1] * 1000:+.1f}] ms")
    print(f"    A/A control (plain vs plain): {aa['delta_pct']:+.2f}% "
          f"({aa['delta_median'] * 1000:+.2f} ms)")
    print(f"    message: {bridge.coverage_message(ab['missing'], areas, spacing, unit_label)}")

  print(f"\nworst measured overhead {worst:.2f}% against a budget of "
        f"{args.budget:.0f}%; anything at or below the A/A control "
        f"figures is below this method's resolution.")
  app.exitQgis()
  return 0 if worst <= args.budget else 1


if __name__ == "__main__":
  sys.exit(main())
