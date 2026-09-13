"""Which weave topologies the vendored library builds under THIS QGIS.

Round ten's two-letter guard builds `basket weave ab|cd` at full strand
width, and the Windows runner's QGIS refused it ("the library could not
work out its structure") where this Mac builds it -- the C-356 shape, a
design one platform's shapely and GEOS reach and another's does not. This
prints, for a handful of weaves at two strand widths, whether a topology
came back, what kind, how many edge classes, and the reason where none
did, beside the shapely and GEOS versions that answered.

Run it under the platform's QGIS Python from the checkout:

    python-qgis tools/probes/which_weave_topologies_build_here.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
  os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
# THE VENDORED LIBRARY, which the plugin's own loader puts on the path
# and a bare script does not: without it every build reports an import.
sys.path.insert(0, os.path.join(ROOT, "weavingspace_qgis", "vendor"))


def main() -> int:
  """Print one line per weave and strand width, and the versions.

  Returns:
    0 always: this measures and reports, it does not judge.
  """
  import shapely
  from weavingspace_qgis import catalog, topology_edits as te
  print("shapely", shapely.__version__, "GEOS", shapely.geos_version_string)
  for name, count in (("plain weave a|b", 2), ("basket weave ab|cd", 4),
                      ("twill weave a|b", 2), ("plain weave ab|cd", 4)):
    spec = catalog.TILINGS_BY_N[count].get(name)
    if spec is None:
      print(f"{name:22} not in the catalogue at {count}")
      continue
    for aspect in (1.0, 0.75):
      try:
        topology, _unit, _kinds, _glue, note = te.weave_topology(
          spec, 1000.0, aspect, reading=te.ASPECT_LIKE_A_DROP,
          families=te.WARP_AND_WEFT_APART)
      except Exception as exc:                          # noqa: BLE001
        print(f"{name:22} {aspect}: raised {type(exc).__name__}: {exc}")
        continue
      if topology is None:
        print(f"{name:22} {aspect}: none -- {note}")
        continue
      labels = {e.label for e in topology.edges.values() if e.label}
      kind = "scaffold" if te.stands_on_scaffolding(topology) else "plain"
      print(f"{name:22} {aspect}: {kind}, {len(labels)} edge classes, "
            f"aa present: {'aa' in labels}")
  sys.stdout.flush()
  return 0


if __name__ == "__main__":
  sys.exit(main())
