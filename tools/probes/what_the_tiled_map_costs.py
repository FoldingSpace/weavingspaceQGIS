"""Where does drawing a map go, and is the overlay doing needless work?

TWO QUESTIONS, ONE RUN. The first is a profile: `get_tiled_map` already
carries its own per-step timings behind `debug=True`, so this drives the
real function and reads what it says rather than replacing anything --
this project's standing rule about instrumenting the code under test.

THE SECOND IS THE ONE THAT MIGHT PAY. In the `prioritise_tiles` path the
overlay's GEOMETRY IS DISCARDED: the fragments exist only to carry an
area, so that `idxmax` can say which zone each tile mostly lies in. A
tile lying wholly inside one zone has a foregone answer -- the fragment
is the tile, its area is the tile's area, and the argmax is that zone --
so every such clip computes something already known. If the interior
share is large, an interior/boundary split would reach the same lookup
by a cheaper route.

IT IS ANSWER-PRESERVING, AND THAT IS WHAT MAKES IT DIFFERENT from the
centroid approximation this project measured and refused on 2026-08-31:
that one changed which zone 4.4% of tiles take their data from, which is
a cartographic decision. A split computes the SAME argmax. So this probe
does not merely time the two, it compares their lookups TILE BY TILE and
reports any disagreement -- a differential, where a difference is a
defect by construction and no oracle is needed.

WHAT IT DOES NOT DO is implement the lattice arithmetic. Finding
straddlers by walking zone boundaries through the tiling's own lattice
-- integer division and modulus on the unit vectors -- is the cheaper
way to reach the same split, and it is worth building only if the
interior share measured here is large enough to pay for it. This probe
is the measurement that decides that, not the optimisation itself.

AND THE ATTRIBUTION HALF FOLLOWS AN ESTABLISHED SHAPE rather than
inventing one: `tools/probes/where_the_load_spends_its_time.py` profiles
at two sizes, ranks callees by CUMULATIVE time and prints each one's
growth, so a term that scales separates itself from a term that does
not. It dumps its own stats because these harnesses end in `os._exit`
and `python -m cProfile` writes nothing at shutdown, and it reads
cumulative rather than self time because the seconds are spent inside
somebody else's C++.

    unset PYTHONHOME PROJ_LIB QGIS_PREFIX_PATH
    set -a; eval "$(bash tools/macos_qgis_env.sh)"; set +a
    PYTHONUNBUFFERED=1 PYTHONPATH="$PWD:$PWD/weavingspace_qgis/vendor" \\
      "$QGIS_PY" -u tools/probes/what_the_tiled_map_costs.py
"""
import cProfile
import contextlib
import subprocess
import io as _io
import os
import pstats
import sys
from time import perf_counter

import geopandas as gpd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REGION = os.path.join(ROOT, "tests", "data", "imd-auckland-sa2-2018.gpkg")

# SPACINGS ARE CHOSEN TO CROSS AN ORDER OF MAGNITUDE IN TILE COUNT,
# because a cost that grows with the map is invisible at one size --
# this project's own rule that magnitude is a fixture dimension.
SPACINGS = (1200, 800, 500, 350)
DESIGN = "laves 3.3.4.3.4"


def a_unit(spacing, crs):
  """The tile unit, built through the door the dialog itself uses.

  Args:
    spacing: the tile spacing in map units.
    crs: the region's coordinate reference system.

  Returns:
    A Tileable. Built by `catalog.make_unit` rather than by calling the
    library directly, because the product is where the arguments are
    parsed and the defaults chosen, and those defaults are frequently
    the thing under test.
  """
  from weavingspace_qgis import catalog
  for n, designs in sorted(catalog.TILINGS_BY_N.items()):
    if DESIGN in designs:
      return catalog.make_unit(designs[DESIGN], spacing=spacing, crs=crs)
  raise AssertionError(f"PREMISE: {DESIGN} is not in the catalogue")


def heaviest(stats, limit: int = 16):
  """The heaviest callees by cumulative time, as (label, seconds).

  Args:
    stats: a `pstats.Stats` from one profiled call.
    limit: how many rows to keep.

  Returns:
    A list of pairs, cumulative time first. Cumulative rather than self
    time, because the question is which ACT costs the seconds and an
    overlay spends nearly all of its time inside GEOS.
  """
  rows = []
  for func, (_cc, _nc, _tt, ct, _callers) in stats.stats.items():
    filename, line, name = func
    rows.append((f"{os.path.basename(filename)}:{line} {name}", ct))
  rows.sort(key=lambda row: -row[1])
  return rows[:limit]


def profile_one(region, spacing):
  """Profile one whole `get_tiled_map`, with the tiling built outside it.

  Args:
    region: the zones GeoDataFrame.
    spacing: the tile spacing in map units.

  Returns:
    (stats, wall seconds, tile count). `Tiling()` is constructed OUTSIDE
    the profiler so the reading is about drawing the map rather than
    about making the tiles, which the stage table above already times.
  """
  from weavingspace import Tiling
  unit = a_unit(spacing, region.crs.to_epsg())
  tiling = Tiling(unit, region)
  profiler = cProfile.Profile()
  t0 = perf_counter()
  profiler.enable()
  tiling.get_tiled_map(join_on_prototiles=False, retain_tileables=False,
                       ragged_edges=True)
  profiler.disable()
  return pstats.Stats(profiler), perf_counter() - t0, len(tiling.tiles)


def stage_timings(region, spacing):
  """Time a whole tiled map at one spacing, reading the library's own steps.

  Args:
    region: the zones GeoDataFrame.
    spacing: the tile spacing in map units.

  Returns:
    A dict of timings, tile counts and the library's own STEP lines.
  """
  from weavingspace import Tiling

  epsg = region.crs.to_epsg()
  t0 = perf_counter()
  unit = a_unit(spacing, epsg)
  t1 = perf_counter()
  tiling = Tiling(unit, region)
  t2 = perf_counter()

  # THE LIBRARY PRINTS ITS OWN STEPS, so capture them rather than
  # timing from outside and guessing which part is which.
  said = _io.StringIO()
  with contextlib.redirect_stdout(said):
    tiled = tiling.get_tiled_map(
      join_on_prototiles=False, retain_tileables=False,
      ragged_edges=True, debug=True)
  t3 = perf_counter()

  steps = [line for line in said.getvalue().split("\n")
           if line.startswith("STEP")]
  return {"spacing": spacing,
          "make_unit": t1 - t0,
          "Tiling()": t2 - t1,
          "get_tiled_map": t3 - t2,
          "tiles": len(tiling.tiles),
          "drawn": len(tiled.map),
          "steps": steps,
          "tiling": tiling}


def split_and_compare(tiling):
  """How many tiles are interior, and do the two lookups agree?

  Args:
    tiling: a Tiling whose `get_tiled_map` has already run, so its
      region carries the id column that call adds.

  Returns:
    A dict with the counts, both timings and the number of tiles the
    two routes assign differently. Zero disagreements is the claim
    that matters: a split is only worth building if it is exact.
  """
  region = tiling.region
  # ASK THE LIBRARY FOR THE ID RATHER THAN LOOKING FOR ITS SIDE EFFECT.
  # `_setup_region_DZID` is what `get_tiled_map` itself calls, and it
  # ADDS the column and hands back its name; the first draft of this
  # probe searched the columns for it and failed its own premise on a
  # region that already carries an `id`.
  id_var = tiling._setup_region_DZID()
  assert id_var in region.columns, f"PREMISE: {id_var} was not added"

  tiles = tiling.tiles.copy()
  tiles["joinUID"] = list(range(tiles.shape[0]))
  area_name = "probe_area"

  # ---- THREE POPULATIONS, NOT TWO. A tile lying wholly OUTSIDE the
  # region is not a straddler: the overlay drops it and no argmax is
  # ever wanted for it. The first draft of this probe counted those as
  # straddlers and reported an interior share of 15% when the share of
  # the tiles that MATTER was three times that.
  touching = tiles.sjoin(region, predicate="intersects", how="inner")
  touching_ids = set(touching["joinUID"])
  outside = len(tiles) - len(touching_ids)

  # ---- AND THE INDEX IS PART OF THE COST, which the first draft hid.
  # `Tiling.__init__` touches `region.sindex`, and the first overlay
  # builds one over the TILES; a second overlay reuses both. Timing
  # route A on warm indexes and calling it the cost of the clip is the
  # measurement answering about the second run rather than the first.
  cold = tiles.copy()
  t_cold = perf_counter()
  _ = region.overlay(cold, make_valid=False)
  cold_overlay = perf_counter() - t_cold

  # ---- ROUTE A: what the library does today.
  t0 = perf_counter()
  overlaps = region.overlay(tiles, make_valid=False)
  overlaps[area_name] = overlaps.geometry.area
  current = overlaps.iloc[
    overlaps.groupby("joinUID")[area_name].agg("idxmax")][["joinUID", id_var]]
  t1 = perf_counter()

  # ---- ROUTE B: assign the tiles that lie wholly inside one zone
  # without any clipping, and clip only what is left.
  t2 = perf_counter()
  inside = tiles.sjoin(region, predicate="within", how="inner")[
    ["joinUID", id_var]]
  assert inside["joinUID"].is_unique, (
    "PREMISE: a tile is inside two zones at once, so the zones overlap "
    "and 'interior' does not mean what this split assumes")
  rest = tiles[~tiles["joinUID"].isin(inside["joinUID"])]
  if len(rest):
    edge = region.overlay(rest, make_valid=False)
    edge[area_name] = edge.geometry.area
    straddlers = edge.iloc[
      edge.groupby("joinUID")[area_name].agg("idxmax")][["joinUID", id_var]]
    proposed = gpd.pd.concat([inside, straddlers], ignore_index=True)
  else:
    proposed = inside
  t3 = perf_counter()

  # ---- THE DIFFERENTIAL. Compare the assignment tile by tile; a
  # difference is a defect by construction.
  a = current.set_index("joinUID")[id_var].sort_index()
  b = proposed.set_index("joinUID")[id_var].sort_index()
  shared = a.index.intersection(b.index)
  disagreements = int((a.loc[shared] != b.loc[shared]).sum())
  only_a = len(a.index.difference(b.index))
  only_b = len(b.index.difference(a.index))

  straddling = len(touching_ids) - len(inside)
  return {"tiles in the tiling": len(tiles),
          "  of which outside the region": outside,
          "  of which touch the region": len(touching_ids),
          "    interior (one zone, no clip needed)": len(inside),
          "    straddling (a clip is really needed)": straddling,
          "interior share OF TILES THAT TOUCH": len(inside) / max(len(touching_ids), 1),
          "overlay with COLD indexes": cold_overlay,
          "route A (overlay all)": t1 - t0,
          "route B (split)": t3 - t2,
          "assigned differently": disagreements,
          "only route A assigned": only_a,
          "only route B assigned": only_b}


def main():
  """Stage timings one size PER PROCESS, then profile and compare.

  ONE SIZE PER PROCESS IS NOT FUSSINESS. The first version of this probe
  drove every spacing in a single process and its figures inflated with
  position in the run -- 2.160s at spacing 350 where a fresh process
  reports 0.250, growing with each spacing measured before it. So the
  loop below RE-EXECUTES this file with one spacing as an argument
  rather than looping in place, which makes the correct measurement the
  one that costs nothing to remember.
  """
  assert os.path.exists(REGION), f"PREMISE: no region fixture at {REGION}"
  region = gpd.read_file(REGION)

  if len(sys.argv) > 1:
    # A CHILD MEASURING ONE SIZE: print one row and nothing else.
    row = stage_timings(region, float(sys.argv[1]))
    print(f"  {row['spacing']:>6}  {row['tiles']:>7} tiles  "
          f"Tiling() {row['Tiling()']:6.3f}s  "
          f"get_tiled_map {row['get_tiled_map']:6.3f}s   "
          + "; ".join(s for s in row["steps"] if "A2" in s))
    return

  print(f"region: {len(region)} zones, crs {region.crs.to_epsg()}")
  print("stage timings, ONE SPACING PER PROCESS:")
  for spacing in SPACINGS:
    finished = subprocess.run(
      [sys.executable, os.path.abspath(__file__), str(spacing)],
      capture_output=True, text=True, check=False)
    line = "".join(l for l in finished.stdout.split("\n") if "tiles" in l)
    print(line or f"  {spacing}: CHILD SAID NOTHING (exit {finished.returncode})")

  last = {"tiling": None}

  print("\n=== the overlay's own work, at the finest spacing")
  from weavingspace import Tiling
  finest = min(SPACINGS)
  tiling = Tiling(a_unit(finest, region.crs.to_epsg()), region)
  tiling.get_tiled_map(join_on_prototiles=False, retain_tileables=False,
                       ragged_edges=True)
  split = split_and_compare(tiling)
  for key, value in split.items():
    if isinstance(value, float):
      print(f"      {key}: {value:.3f}")
    else:
      print(f"      {key}: {value}")

  # ---- WHERE THE SECONDS ACTUALLY GO, at two sizes, so a term that
  # scales with the map separates itself from one that does not.
  print("\n=== what get_tiled_map spends its time IN, profiled")
  seen = {}
  for spacing in (500, 350):
    stats, wall, tiles = profile_one(region, spacing)
    print(f"--- spacing {spacing}: {tiles} tiles, {wall:.3f}s under the profiler")
    for label, seconds in heaviest(stats):
      before = seen.get(label)
      growth = f"  x{seconds / before:5.2f}" if before else ""
      if seconds > 0.005:
        print(f"      {seconds:7.3f}s  {label}{growth}")
      seen[label] = seconds

  print("\nA tile lying wholly inside one zone has a foregone argmax, so "
        "the share above is the share of clips that compute something "
        "already known. The split is worth building only if the two "
        "routes assign every tile identically.")
  print("\nPROBE COMPLETE: profile and differential reported, teardown next.")


main()
