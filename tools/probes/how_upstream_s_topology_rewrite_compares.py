"""How a Topology build compares between two copies of the weavingspace library.

Upstream's `experimental` branch rewrote `topology.py` (17 commits after the
6190917 we vendor, to 329cd2f): symmetries found by snapping check points to the
lattice rather than by matching every tile under every transform, the radius-1
patch dropped after the vertices are found, and tile centres by centroid. This
measures ONE design in ONE library per process -- cpu seconds and the number of
edge and vertex classes -- so a caller can run each arm in a fresh interpreter,
which is the only honest way to time it (docs/PERFORMANCE.md: a series of sizes
inside one run is not a series of measurements).

The library is chosen by its package ROOT, the directory holding a
`weavingspace` package: this checkout's `weavingspace_qgis/vendor`, or the same
path inside a worktree re-vendored from the branch. Weaves are built through the
plugin's own scaffold (`topology_edits.scaffolded_weave`), so the root must be a
plugin checkout's vendor for the WEAVE mode; the TILING mode builds straight from
the catalogue spec with the library's own constructors.

    python-qgis tools/probes/how_upstream_s_topology_rewrite_compares.py tiling <root> "<design>"
    python-qgis tools/probes/how_upstream_s_topology_rewrite_compares.py weave <checkout> "<design>" cut|whole

Measured 2026-09-14 under QGIS 4.0.3 (Python 3.12.11, numpy 1.26.4). The branch
needs two changes before it imports there at all: its new `topology_plot.py`
imports matplotlib unguarded, and `topology.py` calls `np.atan2`, a NumPy 2 name
(`np.arctan2` is the same function under a name both accept).
"""
import ast
import json
import os
import signal
import sys
import time

CEILING = int(os.environ.get("PROBE_CEILING", "900"))


def spec_named(checkout, name):
  """Read one design's spec out of the catalogue literal without importing it.

  Args:
    checkout: the plugin checkout whose `weavingspace_qgis/catalog.py` to read.
    name: the catalogue key.

  Returns:
    The spec dict. Read by evaluating the `TILINGS_BY_N` assignment alone, so
    no copy of the library is imported by the catalogue before the arm chooses
    one.
  """
  path = os.path.join(checkout, "weavingspace_qgis", "catalog.py")
  tree = ast.parse(open(path, encoding="utf-8").read())
  scope = {}
  for node in tree.body:
    if isinstance(node, ast.Assign) and any(
        getattr(t, "id", "") == "TILINGS_BY_N" for t in node.targets):
      exec(compile(ast.Module([node], []), "catalog", "exec"),
           {"dict": dict}, scope)
  return next(t[name] for t in scope["TILINGS_BY_N"].values() if name in t)


def timed_build(topology_class, unit):
  """Build a Topology under a cpu-time ceiling and summarise it.

  Args:
    topology_class: the library's `Topology`.
    unit: the Tileable to build from.

  Returns:
    A dict: `ok`, `cpu` seconds, and where it built the number of distinct edge
    and vertex labels; where it did not, `why`.
  """
  def out(*_):
    raise TimeoutError

  signal.signal(signal.SIGPROF, out)
  signal.setitimer(signal.ITIMER_PROF, CEILING)
  started = time.process_time()
  try:
    topo = topology_class(unit, True)
    result = dict(
      ok=True,
      edges=len({e.label for e in topo.edges.values() if e.label}),
      vertices=len({v.label for v in topo.points.values() if v.label}))
  except TimeoutError:
    result = dict(ok=False, why=f"not done in {CEILING} cpu s")
  except Exception as exc:                            # noqa: BLE001
    result = dict(ok=False, why=f"{type(exc).__name__}: {str(exc)[:80]}")
  finally:
    signal.setitimer(signal.ITIMER_PROF, 0)
  result["cpu"] = round(time.process_time() - started, 2)
  return result


def main() -> int:
  """Print one RESULT line for the design and library named on the command line.

  Returns:
    0 always: this measures and reports, it does not judge.
  """
  mode, root, name = sys.argv[1], sys.argv[2], sys.argv[3]
  if mode == "tiling":
    sys.path.insert(0, root)
    from weavingspace import TileUnit
    from weavingspace.topology import Topology
    checkout = os.path.dirname(os.path.dirname(os.path.abspath(root)))
    spec = spec_named(checkout, name)
    unit = TileUnit(spacing=1000.0,
                    **{k: v for k, v in spec.items() if k != "type"})
    result = timed_build(Topology, unit)
  else:
    holes = sys.argv[4]
    sys.path.insert(0, root)
    sys.path.insert(0, os.path.join(root, "weavingspace_qgis", "vendor"))
    from weavingspace_qgis import catalog, topology_edits as te
    if holes == "cut":
      te._whole_holes = lambda pieces, unit, floor=1.0: pieces
    spec = next(t[name] for t in catalog.TILINGS_BY_N.values() if name in t)
    unit, _kinds, _note = te.scaffolded_weave(spec, 1000.0, 0.75)
    result = timed_build(te._topology_class(), unit)
    result["holes"] = holes
  print("RESULT", json.dumps(dict(root=root, design=name, **result)),
        flush=True)
  return 0


if __name__ == "__main__":
  code = main()
  sys.stdout.flush()
  os._exit(code)
