"""Whether vendor patch 8's `_match_geoms_under_transform` builds the same Topology.

Profiled 2026-09-14 under QGIS 4.0.3, a whole-holes scaffold of `plain weave
abcd|efgh` spent 312 of its 333 seconds in the vendored
`Topology._match_geoms_under_transform`, which for every candidate re-applies
the same transform to the same source geometry, rebuilds each edge's LineString
to take its centroid (4.3 million times), and compares with one scalar shapely
call at a time. Whole holes (74e821b) make a scaffold more symmetric, more
transforms survive, and the edge search grows as transforms x edges x edges:
230.7 s against 28.6 s with the holes cut, and more than half an hour on
`plain weave abcde|fghi`.

Patch 8 does the same work once: the transform applied to the source once per
call, a candidate list's centroids and bounding boxes held, one array
`shapely.distance` (the same GEOS call a Point's `.distance` makes) with the
FIRST candidate in order that meets the tolerance returned, and a tile candidate
skipped only where its bounding box cannot meet the moved source's, where
`polygon_matches` is false for any tile of more than the tolerance's area. Both
methods are read out of tools/vendor_weavingspace.py -- upstream's from the
patch's anchor, the patch's from its replacement -- so this measures what the
tool applies. Design by design, it compares the whole structure (every tile,
edge and vertex label, the three lists of transitivity classes and the
transforms kept) and times both arms. With PROBE_SABOTAGE set the patched arm
matches nothing but itself, which must read DIFFERS.

    python-qgis tools/probes/does_a_faster_match_build_the_same_topology.py [designs]
"""
import ast
import os
import sys
import textwrap
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
  os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "weavingspace_qgis", "vendor"))

DEFAULT = ["laves 3.3.4.3.4", "archimedean 4.8.8", "hex-slice 6", "crosses 4",
           "chavey K", "hex-colouring 7",
           "plain weave a|b@cut", "plain weave a|b@whole",
           "twill weave a|b@whole", "basket weave ab|cd@whole",
           "plain weave abcd|efgh@whole"]


def patch_8_methods():
  """Upstream's method and patch 8's, as source read from the vendoring tool.

  Returns:
    (upstream_source, patched_source), each defining
    `_match_geoms_under_transform` at module level.
  """
  tool = open(os.path.join(ROOT, "tools", "vendor_weavingspace.py"),
              encoding="utf-8").read()
  node = next(n for n in ast.walk(ast.parse(tool))
              if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "targeted"
              and len(n.args) >= 4 and isinstance(n.args[1], ast.Constant)
              and str(n.args[1].value).startswith("8 "))
  head = "def _match_geoms_under_transform(self, geom1, geoms2, transform):\n"
  return tuple(head + textwrap.indent(textwrap.dedent(arg.value), "  ")
               for arg in node.args[2:4])


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
  """Build each design with upstream's method and with patch 8's, and compare.

  Returns:
    0 always: this measures and reports, it does not judge.
  """
  from weavingspace_qgis import catalog, topology_edits as te
  topology_class = te._topology_class()
  vendored = sys.modules[topology_class.__module__]
  upstream_source, patched_source = patch_8_methods()
  if os.environ.get("PROBE_SABOTAGE"):
    patched_source = patched_source.replace(
      "tolerance = 10 * tiling_utils.RESOLUTION", "tolerance = -1.0")
  methods = {}
  for arm, source in (("upstream", upstream_source), ("patch 8", patched_source)):
    scope = dict(vars(vendored))
    exec(compile(source, arm, "exec"), scope)
    methods[arm] = scope["_match_geoms_under_transform"]
  shipped = topology_class._match_geoms_under_transform
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
    for arm, method in methods.items():
      topology_class._match_geoms_under_transform = method
      started = time.process_time()
      try:
        out[arm] = (digest(topology_class(unit, True)),
                    time.process_time() - started)
      except Exception as exc:                        # noqa: BLE001
        out[arm] = (f"raised {type(exc).__name__}", time.process_time() - started)
      finally:
        topology_class._match_geoms_under_transform = shipped
    same = out["patch 8"][0] == out["upstream"][0]
    print(f"{entry:32} {'IDENTICAL' if same else 'DIFFERS'} "
          f"patch 8 {out['patch 8'][1]:.1f}s upstream {out['upstream'][1]:.1f}s",
          flush=True)
    if not same and not isinstance(out["patch 8"][0], str):
      for key in out["patch 8"][0]:
        if out["patch 8"][0][key] != out["upstream"][0][key]:
          print(f"    differs in {key}", flush=True)
  te._whole_holes = whole_holes
  return 0


if __name__ == "__main__":
  code = main()
  sys.stdout.flush()
  os._exit(code)
