"""Whether patch 7 builds the same STRUCTURE, not merely the same class counts.

`does_patch_7_move_a_weave_that_built.py` compared edge and vertex class
COUNTS, and the census (`which_designs_the_centre_offset_misreads.py`)
then found four thin weaves whose copies the two offsets judge
differently while upstream's own loop still gets past the copy step:
`plain weave abcde|fghi`, `abcde-|fghi-`, `abcdef|ghijk-` and
`abcdef|ghijkl`, all at strand width 0.75. A count is conserved by a
relabelling and by a moved corner alike, so this asks the question the
claim "exact on what built without it" actually makes: build the whole
Topology under upstream's loop (compiled from the vendoring tool's own
patch 7 anchor, as the canary test does) and under the patched loop, and
compare every tile's corners, every edge's geometry and label, and every
vertex's point and label, rounded to a thousandth of a map unit.

Both scaffolds are asked -- holes cut by the measured cell, which is what
built before, and whole holes, which is what the plugin builds now. Two controls:
`laves 3.3.4.3.4` and `plain weave a|b` at strand width 1.0 must come back
IDENTICAL, and `plain weave a|b` at 0.75 with whole holes must NOT, since
upstream's loop raises there -- which is what says the comparison can tell
the two loops apart at all.

    python-qgis tools/probes/does_patch_7_build_the_same_structure.py [names...]
"""
import ast
import os
import sys
import textwrap

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
  os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
# THE VENDORED LIBRARY, which the plugin's own loader puts on the path
# and a bare script does not.
sys.path.insert(0, os.path.join(ROOT, "weavingspace_qgis", "vendor"))

DEFAULT = ["plain weave abcde|fghi", "plain weave abcde-|fghi-",
           "plain weave abcdef|ghijk-", "plain weave abcdef|ghijkl"]


def upstream_loop(vendored):
  """Compile upstream's copy-matching method from patch 7's anchor.

  Args:
    vendored: the vendored `topology` module the plugin loads (T-155).

  Returns:
    A function to install as `Topology._match_reference_tile_vertices`.
  """
  tool = open(os.path.join(ROOT, "tools", "vendor_weavingspace.py"),
              encoding="utf-8").read()
  for node in ast.walk(ast.parse(tool)):
    if (isinstance(node, ast.Call) and getattr(node.func, "id", "") == "targeted"
        and len(node.args) >= 4 and isinstance(node.args[1], ast.Constant)
        and str(node.args[1].value).startswith("7 ")):
      source = ("def upstream_match(self, tile1, tile2):\n"
                + textwrap.indent(textwrap.dedent(node.args[2].value), "  "))
      scope = {"tiling_utils": vendored.tiling_utils, "geom": vendored.geom}
      exec(compile(source, "upstream patch 7 anchor", "exec"), scope)
      return scope["upstream_match"]
  raise SystemExit("the vendoring tool carries no patch 7")


def digest(topology):
  """The structure a topology describes, as comparable sets.

  Args:
    topology: a built `Topology`.

  Returns:
    A dict of frozensets: tile corner rings, labelled edges, labelled
    vertices, each keyed by rounded coordinates rather than by the
    library's own ids, which a different insertion order renumbers.
  """
  def pt(p):
    return (round(p.x, 3), round(p.y, 3))
  tiles = frozenset(
    (t.base_ID, tuple(sorted(pt(c.point) for c in t.get_corners())))
    for t in topology.tiles)
  edges = frozenset(
    (e.label, tuple(sorted((pt(e.get_corners()[0].point),
                             pt(e.get_corners()[-1].point)))))
    for e in topology.edges.values())
  points = frozenset((v.label, pt(v.point)) for v in topology.points.values())
  return {"tiles": tiles, "edges": edges, "vertices": points}


def one(name, spec, aspect, whole, te, vendored, upstream, patched):
  """Build one design both ways and print what differs.

  Args:
    name: the catalogue key, for the printed line.
    spec: its catalogue spec.
    aspect: strand width; None (a tiling) or 1.0 go through make_unit.
    whole: True for the plugin's whole holes, False for the cut ones.
    te: the topology_edits module.
    vendored: the vendored topology module.
    upstream: upstream's copy-matching method.
    patched: the vendored (patched) method.
  """
  from weavingspace_qgis import catalog
  saved = te._whole_holes
  if not whole:
    te._whole_holes = lambda pieces, unit, floor=1.0: pieces
  try:
    if aspect is None or aspect == 1.0:
      # A WEAVE'S SPEC CARRIES ITS DEFAULT STRAND WIDTH, so full width is
      # asked for by name: without it `make_unit` builds the thin weave,
      # which the first run of this probe did for its own control.
      unit = catalog.make_unit(spec, spacing=1000.0, crs=None,
                               **({"aspect": 1.0} if aspect else {}))
    else:
      unit, _kinds, note = te.scaffolded_weave(spec, 1000.0, aspect)
      if unit is None:
        print(f"{name:30} {aspect} {'whole' if whole else 'cut  '} "
              f"scaffold refused", flush=True)
        return
  finally:
    te._whole_holes = saved
  out = {}
  # A CONSTRUCTION THAT SPINS is recorded rather than holding the run:
  # upstream's loop repeats for ever on a pass that inserts nothing, which
  # is half of what patch 7 mends, and the first run of this probe sat
  # 38 minutes of cpu on one whole-holes weave.
  import signal

  def spun(_signum, _frame):
    raise TimeoutError("the construction did not end")

  signal.signal(signal.SIGALRM, spun)
  ceiling = int(os.environ.get("PROBE_CEILING", "600"))
  for arm, method in (("upstream", upstream), ("patch 7", patched)):
    vendored.Topology._match_reference_tile_vertices = method
    signal.alarm(ceiling)
    try:
      out[arm] = digest(vendored.Topology(unit, True))
    except TimeoutError:
      out[arm] = f"SPUN past {ceiling}s"
    except Exception as exc:                          # noqa: BLE001
      out[arm] = f"raised {type(exc).__name__}"
    finally:
      signal.alarm(0)
      vendored.Topology._match_reference_tile_vertices = patched
  a, b = out["upstream"], out["patch 7"]
  label = f"{name:30} {aspect} {'whole' if whole else 'cut  '}"
  if isinstance(a, str) or isinstance(b, str):
    print(f"{label} upstream {a if isinstance(a, str) else 'built'}; "
          f"patch 7 {b if isinstance(b, str) else 'built'}", flush=True)
    return
  moved = {k: (len(a[k] - b[k]), len(b[k] - a[k])) for k in a}
  same = all(x == (0, 0) for x in moved.values())
  counts = (f"{len({e[0] for e in a['edges']})}e/"
            f"{len({v[0] for v in a['vertices']})}v")
  print(f"{label} {'IDENTICAL' if same else 'DIFFERS'} {counts} "
        + " ".join(f"{k} -{m[0]} +{m[1]}" for k, m in moved.items()), flush=True)


def main() -> int:
  """Print one line per design, scaffold and control.

  Returns:
    0 always: this measures and reports, it does not judge.
  """
  from weavingspace_qgis import catalog, topology_edits as te
  vendored = sys.modules[te._topology_class().__module__]
  upstream = upstream_loop(vendored)
  patched = vendored.Topology._match_reference_tile_vertices
  by_name = {name: spec for table in catalog.TILINGS_BY_N.values()
             for name, spec in table.items()}
  one("laves 3.3.4.3.4", by_name["laves 3.3.4.3.4"], None, True, te,
      vendored, upstream, patched)
  one("plain weave a|b", by_name["plain weave a|b"], 1.0, True, te,
      vendored, upstream, patched)
  one("plain weave a|b", by_name["plain weave a|b"], 0.75, True, te,
      vendored, upstream, patched)
  for name in sys.argv[1:] or DEFAULT:
    for whole in (False, True):
      one(name, by_name[name], 0.75, whole, te, vendored, upstream, patched)
  return 0


if __name__ == "__main__":
  code = main()
  sys.stdout.flush()
  os._exit(code)
