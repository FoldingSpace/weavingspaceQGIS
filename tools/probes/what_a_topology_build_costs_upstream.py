"""What a Topology build costs in ONE upstream checkout, named exactly.

This project measures `hex-colouring 7` at about 21s and `chavey K` at
about 14.5s, while the library's author reports chavey K at about 10s
and hex-colouring 7 at about half that -- FASTER, and in the OTHER
ORDER. A slower machine scales both and keeps the order, so an
inverted ordering is not hardware, and docs/TOPOLOGY.md has carried
that as an open question with two things owed to him.

THERE ARE THREE CANDIDATE CAUSES AND THEY ARE SEPARABLE:

  the LIBRARY -- upstream's `experimental` branch carries a commit
  saying Topology construction is "now a bit quicker", and another
  that moves Tile, Vertex and Edge out of `topology.py` entirely;

  the DEPENDENCIES -- he is on shapely 2.0.6 and numpy 2.4.4 where
  QGIS 4.0.3 here bundles shapely 2.1.2 and numpy 1.26.4, and the
  build is dominated by an orbit search that is shapely predicates and
  numpy arithmetic;

  and WHAT HIS TIMING COVERS, since the constructor runs the dual
  eagerly and a cell timing only the constructor would not show it.

This probe measures ONE checkout under ONE set of dependencies and
prints all of it, so the caller can vary exactly one thing at a time.
It is deliberately not a comparison: a probe that holds both arms
would have to import two copies of one package into one process, and
whichever won the path is what both arms would have measured.

IT BUILDS THROUGH THE LIBRARY'S OWN DOOR, `TileUnit(**spec)`, rather
than through `catalog.make_unit`. That is the notebook's door and so
the author's, which is the point of comparison here -- and
docs/TOPOLOGY.md has already measured that the two doors give the same
times, so nothing is given up by taking his.

    "$QGIS_PY" what_a_topology_build_costs_upstream.py <checkout>

where <checkout> is the root of an upstream weavingspace tree (the
directory holding the `weavingspace` package).
"""
import importlib.abc
import importlib.machinery
import json
import os
import sys
import time
import types

DESIGNS = (
  ("hex-colouring 7", {"tiling_type": "hex-col", "n": 7}),
  ("chavey K", {"tiling_type": "chavey", "code": "K"}),
)


def main() -> int:
  """Time both designs in the checkout named on the command line.

  Returns:
    0 where every design built, 1 where the checkout could not be put
    on the path at all. A design that RAISES is reported with its
    exception rather than skipped, because "this branch cannot build a
    topology for that tiling" is exactly the kind of answer this is
    looking for -- upstream's own experimental branch carries a revert
    saying a change there broke construction for some tilings.
  """
  if len(sys.argv) < 2:
    print("usage: <this> <upstream-checkout>")
    return 1
  root = os.path.abspath(sys.argv[1])
  # FIRST ON THE PATH, so this checkout wins over any vendored copy --
  # and the premise below says which file actually answered, because
  # two arms reading one library agree perfectly and mean nothing.
  sys.path.insert(0, root)

  # A CLEAN UPSTREAM CHECKOUT CANNOT IMPORT UNDER QGIS'S PYTHON, which
  # is the whole reason `tools/vendor_weavingspace.py` carries a patch
  # family making matplotlib optional: `tileable.py` imports pyplot at
  # module level and QGIS bundles no matplotlib. Our VENDOR imports
  # because it is patched; an unpatched tree dies at line 32 with
  # ModuleNotFoundError, on every arm at once, which is the uniform
  # verdict this project reads as its own instrument.
  # SO IT IS STUBBED, AND THE STUB REPORTS WHETHER IT WAS TOUCHED.
  # Plotting is not on the construction path -- upstream's own
  # experimental branch moves it out of `topology.py` altogether -- so
  # a stub should never be reached, and a reading where it WAS reached
  # is a reading about the stub rather than about the library.
  touched = []

  class _Watched(types.ModuleType):
    """A module that records any attribute anybody asks it for."""

    def __getattr__(self, name):
      """Record the ask and hand back another watched module.

      Args:
        name: the attribute being reached for.

      Returns:
        A further `_Watched`, so a chain of attribute access neither
        raises nor silently succeeds without being recorded.
      """
      touched.append(f"{self.__name__}.{name}")
      return _Watched(f"{self.__name__}.{name}")

  class _Fabricate(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    """Answer any `matplotlib...` import with a watched module.

    Naming four submodules by hand was not enough: `tile_map.py` does
    `import matplotlib.colors`, and a submodule import goes through
    the FINDER rather than through attribute access, so a stub that
    covers `pyplot` and three others still dies on the fifth. A finder
    cannot be caught out by the next module upstream reaches for.

    AND IT IS THE MODERN PROTOCOL. `find_module`/`load_module` were
    removed in Python 3.12, and a finder using them is simply never
    consulted -- which presents as the original ImportError, entirely
    unchanged, so it reads as the stub not being installed rather than
    as the stub being the wrong shape.
    """

    def find_spec(self, name, path=None, target=None):
      """Claim anything under matplotlib.

      Args:
        name: the module being imported.
        path: unused; present for the finder protocol.
        target: unused; present for the finder protocol.

      Returns:
        A spec naming this object as the loader, or None to decline.
      """
      if name.split(".")[0] != "matplotlib":
        return None
      return importlib.machinery.ModuleSpec(name, self, is_package=True)

    def create_module(self, spec):
      """Make the watched stand-in for this module.

      Args:
        spec: the spec `find_spec` returned.

      Returns:
        A `_Watched` recording every attribute anybody asks it for.
      """
      return _Watched(spec.name)

    def exec_module(self, module):
      """Nothing to execute; give it a package path and stop.

      Args:
        module: the module just created.

      Returns:
        None.
      """
      module.__path__ = []

  stubbed = False
  try:
    import matplotlib                                     # noqa: F401
  except ModuleNotFoundError:
    stubbed = True
    sys.meta_path.insert(0, _Fabricate())

  import weavingspace
  from weavingspace import TileUnit
  from weavingspace.topology import Topology
  import shapely
  import numpy

  report = {
    "checkout": root,
    "weavingspace_from": os.path.dirname(weavingspace.__file__),
    "topology_module": sys.modules["weavingspace.topology"].__file__,
    "shapely": shapely.__version__,
    "numpy": numpy.__version__,
    "python": sys.version.split()[0],
    # SAID OUT LOUD, because a stubbed matplotlib is a difference
    # between this arm and our vendored one, and a reader comparing
    # them has to know which arms carried it.
    "matplotlib_stubbed": stubbed,
    "designs": {},
  }
  # THE PREMISE: the library that answered is the one named on the
  # command line. A checkout that failed to win the path would
  # otherwise be timed as itself while being somebody else's.
  if not report["topology_module"].startswith(root):
    report["PREMISE FAILED"] = (
      "the topology module came from %s, not from the checkout"
      % report["topology_module"])
    print(json.dumps(report, indent=2))
    return 1

  # TOUCHES DURING THE IMPORTS ARE EXPECTED AND SAY NOTHING. Upstream
  # annotates with `pyplot.Axes` and asks for `__path__` on the way in,
  # so a count taken over the whole run flags every arm and means
  # nothing. What would matter is the stub being reached while a
  # topology is being BUILT, so the count is baselined here.
  at_import = len(touched)
  for name, spec in DESIGNS:
    entry = {"spec": spec}
    try:
      started = time.monotonic()
      unit = TileUnit(**spec)
      entry["unit_seconds"] = round(time.monotonic() - started, 3)
      entry["tiles"] = int(len(unit.tiles))
      runs = []
      for _ in range(3):
        started = time.monotonic()
        Topology(unit, True)
        runs.append(round(time.monotonic() - started, 3))
      entry["build_seconds"] = runs
      entry["best"] = min(runs)
    except Exception as exc:                              # noqa: BLE001
      entry["raised"] = f"{type(exc).__name__}: {exc}"
    report["designs"][name] = entry

  # ...AND THE STUB MUST NEVER HAVE BEEN REACHED. Where it was, the
  # timings are about a stand-in rather than about the library, and
  # saying so is worth more than a number nobody can trust.
  report["stub_touched_importing"] = touched[:at_import][:6]
  during = touched[at_import:]
  report["stub_touched_building"] = during[:6]
  if during:
    report["READ WITH CARE"] = (
      "the matplotlib stub was reached %d time(s) DURING a build, so "
      "plotting is on the construction path after all and these "
      "timings include a stand-in" % len(during))
  print(json.dumps(report, indent=2))
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
