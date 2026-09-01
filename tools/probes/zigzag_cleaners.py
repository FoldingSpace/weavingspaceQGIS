"""Does upstream's `get_clean_polygon` rescue what our dedupe cannot?

The library's author said, 2026-08-30: "I can recover valid polygons
from the ones it makes with tiling_utils.get_clean_polygon", and "there
is probably some doubling up of coordinates happening". The second half
matches what this project measured independently -- repeated vertices --
so the question is only whether their repair reaches further than ours.

Measured here as a PAIR, on each design: zigzag applied with our own
exact dedupe alone, and with upstream's cleaner in front of it. Both
arms in one run, because a single arm tells you nothing about the
other and this project has been caught believing one before.
"""
import os
import sys

# THE REPOSITORY THIS FILE LIVES IN, derived rather than written
# down, as every probe here derives it. This one arrived from the
# gitignored `dev/instruments/` with the author's own machine path
# hard-coded -- which is a leaked directory layout under this
# project's secrets rule, and a probe that answers about whichever
# tree that path happens to name rather than the one it is run from.
REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
sys.path.insert(0, REPO)
# ...AND THE VENDOR DIRECTORY, which the suite puts there too. The
# library imports itself as a top-level `weavingspace`, so without this
# every design comes back "raised ModuleNotFoundError" -- which reads
# like a finding about the designs and is a fault in the probe.
sys.path.insert(0, os.path.join(REPO, "weavingspace_qgis", "vendor"))

from qgis.core import QgsApplication                    # noqa: E402

QgsApplication.setPrefixPath(
  os.environ.get("QGIS_PREFIX_PATH", "/usr"), True)
_app = QgsApplication([], True)
_app.initQgis()

from weavingspace_qgis import catalog, topology_edits    # noqa: E402

# The designs the ruling of 2026-08-30 names: two that our repair
# rescued, two it still refused. Built through the PRODUCT's own door,
# because `make_unit` is where the arguments are parsed and the
# defaults chosen.
WANTED = ("laves 3.3.4.3.4", "hex-slice 4", "hex-slice 3", "chavey K")


def spec_for(name):
  """Find a catalogue entry by the name the chooser shows.

  Args:
    name: the family name.

  Returns:
    (spec, n) or (None, None). Looked up rather than typed, which is
    this project's own rule about fixture names.
  """
  for n, families in sorted(catalog.TILINGS_BY_N.items()):
    for family, spec in families.items():
      if family == name:
        return spec, n
  return None, None


def zigzag_result(spec, use_upstream):
  """Apply a zigzag and say whether the result draws.

  Args:
    spec: the catalogue entry.
    use_upstream: whether upstream's cleaner is allowed to run.

  Returns:
    A short verdict string.
  """
  saved = topology_edits._upstream_clean
  if not use_upstream:
    topology_edits._upstream_clean = lambda _polygon: None
  try:
    unit = catalog.make_unit(spec, 500.0, None)
    topology, why = topology_edits.build(unit)
    if topology is None:
      return f"no topology ({why[:40]})"
    classes = topology_edits.classes(topology).get("edge") or ""
    if not classes:
      return "no edge classes"
    edited, refusals, _ = topology_edits.apply(
      topology, [{"classes": "".join(classes), "how": "zigzag_edge",
                  "args": {"n": 2, "h": 0.25, "smoothness": 3}}])
    tiles = getattr(edited, "tiles", None)
    bad = 0 if tiles is None else int((~tiles.geometry.is_valid).sum())
    if refusals:
      return f"REFUSED ({refusals[0][:44]}...)"
    return f"drew, {0 if tiles is None else len(tiles)} tiles, {bad} invalid"
  except Exception as exc:                              # noqa: BLE001
    return f"raised {type(exc).__name__}: {str(exc)[:40]}"
  finally:
    topology_edits._upstream_clean = saved


print(f"{'design':<20} {'ours alone':<38} upstream first", flush=True)
for name in WANTED:
  spec, n = spec_for(name)
  if spec is None:
    print(f"{name:<20} not in the catalogue", flush=True)
    continue
  ours = zigzag_result(spec, use_upstream=False)
  both = zigzag_result(spec, use_upstream=True)
  print(f"{name:<20} {ours:<38} {both}", flush=True)
