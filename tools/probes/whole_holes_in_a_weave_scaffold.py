"""Whether a weave's scaffold fills each hole with ONE tile, per weave.

The maintainer read the Topology tab's drawing of `plain weave a|b` at
strand width 0.75 (2026-09-13) and saw clusters of tiny cells where
the daylight should be single holes. The daylight is measured over one
fundamental cell, so a hole that straddles the cell's edge came back as
halves and quarters -- four filler tiles for one hole, with cut edges
and corners that belong to nothing in the cloth. This prints, for every
weave in the catalogue at one strand width, how many tiles the scaffold
holds by kind, whether a topology builds, its edge and vertex classes
under the counting reading, and the classes once the aspect holes are
glued, so the same run before and after a repair is the comparison.

Run it under QGIS's Python from the checkout, one shard per process:

    WEAVE_SHARD=0/4 python-qgis tools/probes/whole_holes_in_a_weave_scaffold.py
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


def main() -> int:
  """Print one line per weave, and a total line.

  Returns:
    0 always: this measures and reports, it does not judge.
  """
  from collections import Counter
  from weavingspace_qgis import catalog, topology_edits as te
  aspect = float(os.environ.get("WEAVE_ASPECT", "0.75"))
  shard, of = (int(x) for x in os.environ.get("WEAVE_SHARD", "0/1").split("/"))
  weaves = sorted((n, name) for n, table in catalog.TILINGS_BY_N.items()
                  for name, spec in table.items()
                  if spec.get("type") == "weave")
  mine = weaves[shard::of]
  print(f"shard {shard}/{of}: {len(mine)} of {len(weaves)} weaves at "
        f"aspect {aspect}", flush=True)
  built = 0
  for n, name in mine:
    spec = catalog.TILINGS_BY_N[n][name]
    started = time.monotonic()
    unit, kinds, note = te.scaffolded_weave(spec, 1000.0, aspect)
    if unit is None:
      print(f"{name:34} scaffold refused: {note[:70]}", flush=True)
      continue
    count = Counter(kinds.values())
    try:
      topology = te._topology_class()(unit, True)
    except Exception as exc:                          # noqa: BLE001
      print(f"{name:34} tiles {dict(count)} topology raised "
            f"{type(exc).__name__}", flush=True)
      continue
    built += 1
    edges = {e.label for e in topology.edges.values() if e.label}
    points = {v.label for v in topology.points.values() if v.label}
    glued = te.glue_the_aspect_holes(topology, kinds)
    print(f"{name:34} tiles {dict(count)} classes {len(edges)}e/"
          f"{len(points)}v glued {glued['after'][0]}e/{glued['after'][1]}v "
          f"holes glued {glued['glued']} {time.monotonic() - started:.1f}s",
          flush=True)
  print(f"shard {shard}/{of} done: {built} of {len(mine)} built", flush=True)
  return 0


if __name__ == "__main__":
  code = main()
  sys.stdout.flush()
  os._exit(code)
