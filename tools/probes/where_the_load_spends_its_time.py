"""Where does opening a saved map actually spend its seconds?

THE SAVE'S EQUATION IS KNOWN and the LOAD'S IS NOT. The committed
scale probe watches every function that touches the file, and on the
load side NOT ONE OF THEM GROWS: `gpkg_tables` is called once,
`read_working_state` once, `same_source` five times, at 8 elements and
at 64 alike -- while the wall runs 1.3, 1.7, 2.8, 5.6 seconds. So the
load's cost is somewhere that instrument does not look, and the 122s
recorded at the 256 ceiling has never been attributed to anything.

PROFILE THE THING A PERSON WAITS FOR, because the cost is often not
where the subject is. This runs the load under cProfile at two element
counts and prints the heaviest callees by cumulative time, plus the
per-count growth of each, so a term that is quadratic separates itself
from one that is merely large.

IT DUMPS ITS OWN STATS rather than using `python -m cProfile`, because
anything ending through `os._exit` writes nothing at interpreter
shutdown -- the trap that left this project's coverage report empty
for a fortnight.
"""

import cProfile
import io
import os
import pstats
import sys
import time

sys.path.insert(0, os.environ.get("WS_REPO", os.getcwd()))

from tools.probe_kit import start                      # noqa: E402

COUNTS = (32, 64, 128)


def a_saved_map(probe, elements: int, spacing: float):
  """Draw and save a map of `elements` elements, and return its path.

  Args:
    probe: the running `Probe`.
    elements: how many elements the design should carry.
    spacing: map units between repeats. Coarse deliberately -- the
      question is the number of ELEMENTS, and a fine spacing buys
      minutes of tiling that say nothing about it.

  Returns:
    The path written, or None where that element count is not offered.
    The premise that the map really has that many elements is asserted
    rather than assumed, since a reading about a count the design does
    not carry is a reading about something else.
  """
  probe.clear()
  dlg, _layer, _tid = probe.dialog()
  if not (dlg.n_spin.minimum() <= elements <= dlg.n_spin.maximum()):
    dlg.close()
    return None
  dlg.n_spin.setValue(elements)
  probe.suite._tick(600)
  dlg.spacing_spin.setValue(spacing)
  probe.suite._generate_and_wait(dlg)
  drew = len(dlg._element_layer_ids)
  assert drew == elements, (
    f"PREMISE: asked for {elements} elements and drew {drew}")
  path = probe.path(f"load_{elements}.gpkg")
  assert probe.save(dlg, path), "PREMISE: the save failed"
  dlg.close()
  probe.clear()
  return path


def profile_the_load(probe, path: str, elements: int):
  """Open a saved map under cProfile and return the stats and the wall.

  Args:
    probe: the running `Probe`.
    path: the GeoPackage to open.
    elements: how many elements it should bring back, asserted so a
      load that quietly returned less is not read as a fast one.

  Returns:
    A pair (pstats.Stats, wall seconds). The dialog is built OUTSIDE
    the profile and the settle is inside it, because what a person
    waits for is the whole act rather than the call that starts it.
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  suite = probe.suite
  opener = WeavingSpaceDialog(iface=suite._Iface())
  opener.live_check.setChecked(False)
  opener.resume_widget.setFilePath(path)

  profiler = cProfile.Profile()
  started = time.monotonic()
  profiler.enable()
  opener._load_pressed()
  suite._settle(opener, seconds=900)
  profiler.disable()
  wall = time.monotonic() - started

  back = len(opener._element_layer_ids)
  assert back == elements, (
    f"PREMISE: {elements} were saved and {back} came back, so this "
    f"reading is not about the load it claims")
  opener.close()
  probe.clear()
  return pstats.Stats(profiler), wall


def heaviest(stats, limit: int = 22):
  """The heaviest callees by cumulative time, as (label, seconds).

  Args:
    stats: a `pstats.Stats` from one profiled load.
    limit: how many rows to keep.

  Returns:
    A list of pairs. Read CUMULATIVE rather than self time: the answer
    wanted is which ACT costs the seconds, and a per-layer open spends
    almost all of its time inside somebody else's C++.
  """
  stream = io.StringIO()
  stats.stream = stream
  stats.sort_stats("cumulative")
  rows = []
  for func, (_cc, _nc, _tt, ct, _callers) in stats.stats.items():
    filename, line, name = func
    where = os.path.basename(filename)
    rows.append((f"{where}:{line} {name}", ct))
  rows.sort(key=lambda row: -row[1])
  return rows[:limit]


def main():
  """Profile the load at three element counts and print what grows.

  Returns:
    None; it prints. Three counts because the shape of the growth is
    the question -- a term that doubles with n is linear and one that
    quadruples is the quadratic being hunted, and neither shows in a
    single profile however detailed.
  """
  probe = start()
  seen = {}
  walls = {}
  counts = []
  for elements in COUNTS:
    print(f"---- {elements} elements", flush=True)
    path = a_saved_map(probe, elements, 900.0)
    if path is None:
      print(f"     ({elements} is not on offer)")
      continue
    stats, wall = profile_the_load(probe, path, elements)
    counts.append(elements)
    walls[elements] = wall
    for label, seconds in heaviest(stats, limit=40):
      seen.setdefault(label, {})[elements] = seconds
    print(f"     load {wall:.1f}s", flush=True)

  print()
  print("=" * 78)
  print("LOAD: cumulative seconds by callee, and how each grows")
  print("=" * 78)
  print(f"  {'elements':<44}" + "".join(f"{n:>10}" for n in counts))
  print(f"  {'WALL SECONDS':<44}"
        + "".join(f"{walls[n]:>10.1f}" for n in counts))
  print(f"  {'-' * 44}" + "-" * (10 * len(counts)))
  ranked = sorted(seen.items(),
                  key=lambda kv: -max(kv[1].values()))
  for label, byn in ranked[:26]:
    if max(byn.values()) < 0.15:
      continue
    print(f"  {label[:44]:<44}"
          + "".join(f"{byn.get(n, 0.0):>10.2f}" for n in counts))
  print()
  print("  RATIOS against the reading before. 2.0 is linear in the")
  print("  element count; 4.0 is the quadratic being hunted.")
  for label, byn in ranked[:26]:
    if max(byn.values()) < 0.15:
      continue
    ratios = []
    for i, n in enumerate(counts):
      before = byn.get(counts[i - 1], 0.0) if i else 0.0
      ratios.append("     -" if not i or before <= 0
                    else f"{byn.get(n, 0.0) / before:>6.1f}")
    print(f"  {label[:44]:<44}" + "".join(f"{r:>10}" for r in ratios))
  ratios = ["     -" if i == 0
            else f"{walls[counts[i]] / walls[counts[i - 1]]:>6.1f}"
            for i in range(len(counts))]
  print(f"  {'WALL SECONDS':<44}" + "".join(f"{r:>10}" for r in ratios))


main()
