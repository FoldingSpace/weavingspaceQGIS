"""Whether a faster `_match_geoms_under_transform` builds the same Topology.

Profiled 2026-09-14 under QGIS 4.0.3, a whole-holes scaffold of `plain weave
abcd|efgh` spent 312 of its 333 seconds in the vendored
`Topology._match_geoms_under_transform`, which for every candidate re-applies
the same transform to the same source geometry, rebuilds each edge's LineString
to take its centroid (4.3 million times), and compares with one scalar shapely
call at a time. Whole holes (74e821b) make a scaffold more symmetric, more
transforms survive, and the edge search grows as transforms x edges x edges:
230.7 s against 28.6 s with the holes cut, and more than half an hour on
`plain weave abcde|fghi`.

`FAST_MATCH` below does the same work once: the transform applied to the source
once per call, an edge's centroid computed once per list of candidates, one
array `shapely.distance` (the same GEOS call a Point's `.distance` makes) with
the FIRST candidate in order that meets the tolerance returned, and a tile
candidate skipped only where its bounding box cannot meet the moved source's,
where `polygon_matches` is false for any tile of more than the tolerance's area.
So it answers identically by construction; this asks it to, design by design,
over the whole structure -- every tile, edge and vertex label, the three lists
of transitivity classes and the transforms kept -- and times both arms.

    python-qgis tools/probes/does_a_faster_match_build_the_same_topology.py [designs]
"""
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
  os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "weavingspace_qgis", "vendor"))

FAST_MATCH = '''
def _match_geoms_under_transform(self, geom1, geoms2, transform):
  import shapely
  if not geoms2:
    return -1
  tolerance = 10 * tiling_utils.RESOLUTION
  if isinstance(geom1, Tile):
    moved = affine.affine_transform(geom1.shape, transform)
    skip = moved.area > 1000 * tiling_utils.RESOLUTION
    x0, y0, x1, y1 = moved.bounds
    for geom2 in geoms2:
      if skip:
        bx0, by0, bx1, by1 = geom2.shape.bounds
        if bx0 > x1 or bx1 < x0 or by0 > y1 or by1 < y0:
          continue
      if self.polygon_matches(moved, geom2.shape):
        return geom2.base_ID
    return -1
  if isinstance(geom1, Vertex):
    moved = affine.affine_transform(geom1.point, transform)
    targets = [geom2.point for geom2 in geoms2]
  else:
    moved = affine.affine_transform(geom1.get_geometry().centroid, transform)
    held = getattr(self, "_plugin_edge_centroids", None)
    key = tuple(edge.ID for edge in geoms2)
    if held is None or held[0] is not geoms2 or held[1] != key:
      held = (geoms2, key, [edge.get_geometry().centroid for edge in geoms2])
      self._plugin_edge_centroids = held
    targets = held[2]
  hits = np.flatnonzero(shapely.distance(moved, targets) <= tolerance)
  return geoms2[hits[0]].base_ID if len(hits) else -1
'''

DEFAULT = ["laves 3.3.4.3.4", "archimedean 4.8.8", "hex-slice 6", "crosses 4",
           "chavey K", "hex-colouring 7",
           "plain weave a|b@cut", "plain weave a|b@whole",
           "twill weave a|b@whole", "basket weave ab|cd@whole",
           "plain weave abcd|efgh@whole"]


def digest(topo):
  """Everything a Topology's structure consists of, as comparable values.

  Args:
    topo: a built Topology.

  Returns:
    A dict of the tile, edge and vertex labels by ID, the three lists of
    transitivity classes, and the transforms kept with their 6-tuples rounded
    to a part in a thousand million.
  """
  return dict(
    tiles=[(t.ID, t.base_ID, getattr(t, "transitivity_class", None)) for t in topo.tiles],
    edges=sorted((k, e.label, e.base_ID) for k, e in topo.edges.items()),
    vertices=sorted((k, v.label, v.base_ID) for k, v in topo.points.items()),
    tile_classes=topo.tile_transitivity_classes,
    edge_classes=[sorted(c) for c in topo.edge_transitivity_classes],
    vertex_classes=[sorted(c) for c in topo.vertex_transitivity_classes],
    transforms=sorted((k, tuple(round(x, 9) for x in tr.transform))
                      for k, tr in topo.tile_matching_transforms.items()))


def main() -> int:
  """Build each design with the vendored method and with FAST_MATCH, and compare.

  Returns:
    0 always: this measures and reports, it does not judge.
  """
  from weavingspace_qgis import catalog, topology_edits as te
  topology_class = te._topology_class()
  vendored = sys.modules[topology_class.__module__]
  scope = dict(vars(vendored))
  source = FAST_MATCH
  # THE CONTROL: with PROBE_SABOTAGE set, the fast arm matches nothing but
  # itself, which must read DIFFERS -- or the digest cannot see a difference.
  if os.environ.get("PROBE_SABOTAGE"):
    source = source.replace("tolerance = 10 * tiling_utils.RESOLUTION",
                            "tolerance = -1.0")
  exec(compile(source, "FAST_MATCH", "exec"), scope)
  fast = scope["_match_geoms_under_transform"]
  slow = topology_class._match_geoms_under_transform
  whole_holes = te._whole_holes
  by_name = {name: spec for table in catalog.TILINGS_BY_N.values()
             for name, spec in table.items()}
  for entry in sys.argv[1:] or DEFAULT:
    name, _, holes = entry.partition("@")
    spec = by_name[name]
    te._whole_holes = whole_holes if holes != "cut" else (
      lambda pieces, unit, floor=1.0: pieces)
    if spec["type"] == "weave":
      unit, _kinds, _note = te.scaffolded_weave(spec, 1000.0, 0.75)
    else:
      unit = catalog.make_unit(spec, spacing=1000.0, crs=None)
    out = {}
    for arm, method in (("fast", fast), ("vendored", slow)):
      topology_class._match_geoms_under_transform = method
      started = time.process_time()
      try:
        out[arm] = (digest(topology_class(unit, True)),
                    time.process_time() - started)
      except Exception as exc:                        # noqa: BLE001
        out[arm] = (f"raised {type(exc).__name__}", time.process_time() - started)
      finally:
        topology_class._match_geoms_under_transform = slow
    same = out["fast"][0] == out["vendored"][0]
    print(f"{entry:32} {'IDENTICAL' if same else 'DIFFERS'} "
          f"fast {out['fast'][1]:.1f}s vendored {out['vendored'][1]:.1f}s",
          flush=True)
    if not same and not isinstance(out["fast"][0], str):
      for key in out["fast"][0]:
        if out["fast"][0][key] != out["vendored"][0][key]:
          print(f"    differs in {key}", flush=True)
  te._whole_holes = whole_holes
  return 0


if __name__ == "__main__":
  code = main()
  sys.stdout.flush()
  os._exit(code)
