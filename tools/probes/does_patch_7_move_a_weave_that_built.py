"""Whether patch 7 changes the structure of a thin weave that built without it.

Patch 7 matches a tile to its patch copies by centroid rather than by
incentre. The catalogue census
(`which_designs_the_centre_offset_misreads.py`) answers for tilings and
full-width weaves; a thin weave reaches the constructor through the
plugin's scaffold, so this asks it on the scaffold the plugin built
before whole holes -- the cut one -- for every weave named in the file
given, printing each one's edge and vertex classes under the patched
loop, to be compared with the same design's line from before the patch.

    python-qgis tools/probes/does_patch_7_move_a_weave_that_built.py names.txt
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
  os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
# THE VENDORED LIBRARY, which the plugin's own loader puts on the path
# and a bare script does not.
sys.path.insert(0, os.path.join(ROOT, "weavingspace_qgis", "vendor"))


def main() -> int:
  """Print one line per weave named in the file.

  Returns:
    0 always: this measures and reports, it does not judge.
  """
  from weavingspace_qgis import catalog, topology_edits as te
  names = [line.strip() for line in open(sys.argv[1], encoding="utf-8")
           if line.strip()]
  by_name = {name: spec for table in catalog.TILINGS_BY_N.values()
             for name, spec in table.items()}
  # THE SCAFFOLD AS IT WAS BEFORE WHOLE HOLES, so only the loop differs.
  te._whole_holes = lambda pieces, unit, floor=1.0: pieces
  for name in names:
    spec = by_name.get(name)
    if spec is None:
      print(f"{name:34} not in the catalogue", flush=True)
      continue
    unit, kinds, note = te.scaffolded_weave(spec, 1000.0, 0.75)
    if unit is None:
      print(f"{name:34} scaffold refused: {note[:60]}", flush=True)
      continue
    try:
      topology = te._topology_class()(unit, True)
    except Exception as exc:                          # noqa: BLE001
      print(f"{name:34} raised {type(exc).__name__}", flush=True)
      continue
    edges = {e.label for e in topology.edges.values() if e.label}
    points = {v.label for v in topology.points.values() if v.label}
    print(f"{name:34} classes {len(edges)}e/{len(points)}v", flush=True)
  return 0


if __name__ == "__main__":
  code = main()
  sys.stdout.flush()
  os._exit(code)
