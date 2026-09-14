"""Whether matching a tile's copies by CENTROID changes any design that builds.

`Topology._match_reference_tile_vertices` decides whether a patch copy
lacks one of its base tile's corners by comparing corner offsets with
the offset between the two tiles' CENTRES, and a tile's centre is
`get_incentre`, a numerical search that wanders along a rectangle's
midline. On a weave scaffold whose holes are whole tiles the copies of
a strand then read as offset, a corner is judged missing at index 0,
and the insertion that follows corrupts the tile's edge list: the
KeyError of upstream-note-an-edge-is-deleted-while-a-tile-still-names-
it.md. The candidate repair takes the offset between the two tiles'
SHAPE centroids, which is exact for translates.

This asks, design by design over the whole catalogue, whether the two
offsets ever lead to a different decision, by running the construction
only as far as the copy step with the method instrumented and upstream's
own decision kept. A design where they never differ is built identically
by the repair. Tilings at their defaults; weaves at full width and, as
the plugin scaffolds them, at 0.75.

    CENSUS_SHARD=0/4 python-qgis tools/probes/which_designs_the_centre_offset_misreads.py
"""
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
  os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
# THE VENDORED LIBRARY, which the plugin's own loader puts on the path
# and a bare script does not.
sys.path.insert(0, os.path.join(ROOT, "weavingspace_qgis", "vendor"))


class StopAfterTheCopy(Exception):
  """Raised to end a construction once the step under study has run."""


def main() -> int:
  """Print one line per design and a total line.

  Returns:
    0 always: this measures and reports, it does not judge.
  """
  from weavingspace_qgis.vendor.weavingspace import topology as T
  from weavingspace_qgis.vendor.weavingspace import tiling_utils
  from weavingspace_qgis import catalog, topology_edits as te
  tolerance = 10 * tiling_utils.RESOLUTION
  seen = {}

  def decisions(tile1, tile2, dxy):
    """Which of tile1's corners tile2 would be judged to lack.

    Args:
      tile1: the base tile.
      tile2: its copy in the patch.
      dxy: the offset between them the judgement is made with.

    Returns:
      The indices upstream's loop would insert at, in order.
    """
    corners2 = tile2.get_corners()
    out = []
    for i, corner in enumerate(tile1.get_corners()):
      other = corners2[i % len(corners2)].point
      if abs((other.x - corner.point.x) - dxy[0]) > tolerance or \
         abs((other.y - corner.point.y) - dxy[1]) > tolerance:
        out.append(i)
    return out

  upstream = T.Topology._match_reference_tile_vertices

  def instrumented(self, tile1, tile2):
    if len(tile1.corners) > len(tile2.corners):
      seen["calls"] = seen.get("calls", 0) + 1
      by_centre = decisions(tile1, tile2, (tile2.centre.x - tile1.centre.x,
                                           tile2.centre.y - tile1.centre.y))
      a, b = tile1.shape.centroid, tile2.shape.centroid
      by_centroid = decisions(tile1, tile2, (b.x - a.x, b.y - a.y))
      if by_centre != by_centroid:
        seen["differ"] = seen.get("differ", 0) + 1
    return upstream(self, tile1, tile2)

  def stop(self):
    raise StopAfterTheCopy

  T.Topology._match_reference_tile_vertices = instrumented
  T.Topology._assign_vertex_and_edge_base_IDs = stop
  shard, of = (int(x) for x in os.environ.get("CENSUS_SHARD", "0/1").split("/"))
  cases = []
  for n, table in sorted(catalog.TILINGS_BY_N.items()):
    for name, spec in table.items():
      if spec.get("type") == "weave":
        cases.append((n, name, 1.0))
        cases.append((n, name, 0.75))
      else:
        cases.append((n, name, None))
  mine = cases[shard::of]
  print(f"shard {shard}/{of}: {len(mine)} of {len(cases)} cases", flush=True)
  totals = {"cases": 0, "reached": 0, "differ": 0, "crashed": 0}
  for n, name, aspect in mine:
    spec = catalog.TILINGS_BY_N[n][name]
    seen.clear()
    started = time.monotonic()
    try:
      if aspect == 0.75:
        unit, _kinds, note = te.scaffolded_weave(spec, 1000.0, aspect)
        if unit is None:
          print(f"{name:34} {aspect} scaffold refused", flush=True)
          continue
      else:
        unit = catalog.make_unit(spec, spacing=1000.0, crs=None,
                                 **({"aspect": aspect} if aspect else {}))
    except Exception as exc:                          # noqa: BLE001
      print(f"{name:34} {aspect} unit raised {type(exc).__name__}", flush=True)
      continue
    totals["cases"] += 1
    outcome = "raised before the copy ended"
    try:
      T.Topology(unit, True)
    except StopAfterTheCopy:
      outcome = "copied"
      totals["reached"] += 1
    except Exception as exc:                          # noqa: BLE001
      outcome = f"raised {type(exc).__name__}"
      totals["crashed"] += 1
    if seen.get("differ"):
      totals["differ"] += 1
    print(f"{name:34} {aspect} {outcome}: calls {seen.get('calls', 0)} "
          f"differ {seen.get('differ', 0)} {time.monotonic() - started:.1f}s",
          flush=True)
  print(f"shard {shard}/{of} done: {totals}", flush=True)
  return 0


if __name__ == "__main__":
  code = main()
  sys.stdout.flush()
  os._exit(code)
