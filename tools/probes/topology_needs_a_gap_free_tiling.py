"""What a Topology costs to build, and the designs it refuses.

WHY THIS IS COMMITTED. The maintainer asked on 2026-08-29 for a
topology tab, with a design note that the topology "should likely be
built when the tiling is built" and stored in the transportable
GeoPackage. Both halves turn on facts nobody here had measured, and
both answers are surprising enough that a later session would
otherwise re-derive them: building a topology costs SECONDS where
building the unit costs hundredths, and `Topology` refuses any tiling
with GAPS in it -- which is most of what this plugin draws.

WHAT IT ANSWERS, in one run:

  the COST, timed three times per design so a single sample on a busy
  machine cannot be mistaken for a measurement, against the two
  figures that bound it -- a unit builds in 0.01-0.05s and the live
  debounce is 900 ms;

  the GAP CONSTRAINT, by sweeping a weave's aspect and a tiling's
  inset, which are the two ordinary controls that open a design up.
  A weave at aspect 1.0 carries a topology and the plugin's own
  default of 0.75 does not; a tiling at inset 0 carries one and five
  map units of inset does not.

READ THE VERDICT AND NOT THE EXIT CODE. This is a measurement rather
than a gate: it prints what it found and exits 0 either way, and a
failure inside it is a finding rather than an error. What WOULD be a
defect in the probe is a design failing to BUILD, which is reported
separately and in those words, because a fixture that cannot be
constructed has measured nothing about the library -- an earlier
version of this probe reported two weave types as unsupported when it
had simply passed the catalogue's raw `n` string to `WeaveUnit`
instead of going through `catalog.make_unit`, which parses it.

Run it under QGIS's own Python, which is where geopandas lives. It
does not start a QgsApplication and needs no project:

    eval "$(bash tools/macos_qgis_env.sh | grep -E '^[A-Z_]+=' \\
            | sed 's/^/export /')"
    WS_REPO="$PWD" PYTHONUNBUFFERED=1 "$QGIS_PY" \\
      tools/probes/topology_needs_a_gap_free_tiling.py
"""

import os
import sys
import time

ROOT = os.environ.get("WS_REPO", os.getcwd())
# The vendored library is imported as `weavingspace`, exactly as the
# plugin imports it, so this measures the code that would ship rather
# than whatever copy happens to be on the path.
sys.path.insert(0, os.path.join(ROOT, "weavingspace_qgis", "vendor"))
sys.path.insert(0, ROOT)

from weavingspace import Topology, WeaveUnit  # noqa: E402

from weavingspace_qgis import catalog  # noqa: E402

REPEATS = 3
"""How many times each design is timed. Three is enough to show whether
a figure resolves; one sample on a machine that has been busy tells you
nothing in either direction."""

COST_CASES = [
  (2, "archimedean 4.8.8"),
  (5, "square-colouring 5"),
  (6, "hex-slice 6"),
  (12, "hex-slice 12"),
]
"""Catalogue designs to time, chosen to span the element counts rather
than the families: the question is what the element spinner costs.
They are named rather than discovered so the numbers in ROADMAP.md
can be compared with a later run of the same cases."""


def build(spec):
  """Make a Tileable the way the DIALOG makes one.

  Args:
    spec: one value from `catalog.TILINGS_BY_N`.

  Returns:
    The Tileable. It goes through `catalog.make_unit` rather than
    calling `TileUnit`/`WeaveUnit` directly, because the catalogue
    stores a weave's passing pattern as the string a user types and
    `make_unit` is what parses it -- and because `make_unit` supplies
    the aspect the plugin actually defaults to, which turns out to be
    the whole of the gap question below.
  """
  return catalog.make_unit(spec, spacing=500.0, crs=None)


def timed(make):
  """Build a Topology REPEATS times and report the seconds.

  Args:
    make: a zero-argument callable returning a FRESH Tileable. It is
      called inside the loop deliberately: reusing one unit would time
      a warmed object rather than the act being measured.

  Returns:
    A list of floats where every attempt succeeded, or the first
    exception raised. An exception here is a finding about the
    library, since the unit was built before the clock started.
  """
  times = []
  for _ in range(REPEATS):
    unit = make()
    start = time.monotonic()
    try:
      Topology(unit)
    except Exception as exc:                                  # noqa: BLE001
      return exc
    times.append(time.monotonic() - start)
  return times


def measure_the_cost():
  """Time Topology construction across the catalogue and print it.

  Returns:
    None; prints one line per design plus the two figures that bound
    the answer, because seconds mean nothing without them.
  """
  print("WHAT IT COSTS  (three samples each, through catalog.make_unit)")
  for n, name in COST_CASES:
    spec = catalog.TILINGS_BY_N[n][name]
    got = timed(lambda s=spec: build(s))
    if isinstance(got, Exception):
      print(f"  n={n:<3} {name:<24} RAISED {type(got).__name__}: "
            f"{str(got)[:50]}")
      continue
    print(f"  n={n:<3} {name:<24} {min(got):.3f}-{max(got):.3f}s "
          f"(median {sorted(got)[len(got) // 2]:.3f})")
  print("  for comparison: a unit builds in 0.01-0.05s at every count "
        "up to 256,\n  and the live debounce interval is 900 ms.")


def measure_the_gaps():
  """Sweep the two controls that open a design up, and report.

  Returns:
    None; prints the aspect sweep and the inset sweep. The point of
    running both is that they are the SAME finding reached through
    unrelated controls -- one belongs to weaves and one to tilings --
    which is what makes "Topology needs a gap-free tiling" a statement
    about the library rather than about either control.
  """
  print("\nWHAT IT REFUSES  (a weave's aspect: 1.0 is solid, and the "
        "plugin defaults to 0.75)")
  for aspect in (1.0, 0.95, 0.9, 0.75, 0.5):
    try:
      # Built directly here rather than through make_unit, because
      # aspect is the variable under test and make_unit would supply
      # its own default and hide it.
      unit = WeaveUnit(weave_type="plain", strands="a|b", spacing=500.0,
                       crs=None, aspect=aspect)
    except Exception as exc:                                  # noqa: BLE001
      print(f"  aspect={aspect:<5} UNIT FAILED (the probe's fault): {exc}")
      continue
    try:
      topo = Topology(unit)
      print(f"  aspect={aspect:<5} carries a topology  "
            f"tiles={len(topo.tiles)} dual={len(topo.dual_tiles)}")
    except Exception as exc:                                  # noqa: BLE001
      print(f"  aspect={aspect:<5} {type(exc).__name__}: {str(exc)[:52]}")

  print("\nWHAT IT REFUSES  (a tiling's inset, in map units at spacing 500)")
  spec = catalog.TILINGS_BY_N[4]["laves 3.3.4.3.4"]
  for inset in (0, 5, 25, 50):
    try:
      unit = build(spec)
      if inset:
        # `inset_tiles` shrinks every tile by a fixed distance, which
        # is what the Design tab's Tiles inset spinner does.
        unit = unit.inset_tiles(inset)
    except Exception as exc:                                  # noqa: BLE001
      print(f"  inset={inset:<4} UNIT FAILED (the probe's fault): {exc}")
      continue
    try:
      topo = Topology(unit)
      print(f"  inset={inset:<4} carries a topology  "
            f"tiles={len(topo.tiles)} dual={len(topo.dual_tiles)}")
    except Exception as exc:                                  # noqa: BLE001
      print(f"  inset={inset:<4} {type(exc).__name__}: {str(exc)[:52]}")


def main():
  """Run both measurements and state what they mean together.

  Returns:
    None. It exits normally whatever it finds; see the module
    docstring on why this reports rather than gates.
  """
  measure_the_cost()
  measure_the_gaps()
  print("\nTAKEN TOGETHER: a topology belongs to the DESIGN and not to a "
        "run --\nseconds against a 900 ms debounce -- and it can only be "
        "asked of a unit\nwith no gaps in it, which the ordinary controls "
        "produce. Both are scope\ndecisions for the topology tab rather "
        "than defects. Recorded in ROADMAP.md\nunder 0.24.5.")


main()
