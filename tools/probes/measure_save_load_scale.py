"""What makes Save and Load quadratic in the element count?

The last owed claim of round ten: 134s and 122s at the 256 ceiling
with a frozen interface, every store measured clean, so the defect is
in the ACT rather than in what it writes.

THE METHOD IS THE ONE `scale` USED and this project wrote down: compare
call COUNTS at four element counts rather than seconds at two, so the
answer is an equation naming its own caller. A count that grows as n^2
is the finding; a count that grows as n and whose SECONDS grow as n^2
says the individual call is getting more expensive, which is a
different repair.

It reports both, per element count, for every function that touches
the file.
"""

import os
import sys
import time

sys.path.insert(0, os.environ.get("WS_REPO", os.getcwd()))

from tools.probe_kit import start                      # noqa: E402

TALLY = {}


def counted(module, name):
  """Wrap one function so every call is counted and timed.

  Args:
    module: the module holding it.
    name: the attribute to wrap.

  Returns:
    None. Wrapping the module attribute rather than standing IN for
    the function is deliberate: the real body still runs, so this
    measures the product rather than a spy's idea of it.
  """
  real = getattr(module, name, None)
  if real is None or not callable(real):
    print(f"  (no {module.__name__}.{name} to wrap)")
    return
  label = f"{module.__name__.split('.')[-1]}.{name}"

  def wrapper(*args, **kwargs):
    started = time.monotonic()
    try:
      return real(*args, **kwargs)
    finally:
      entry = TALLY.setdefault(label, [0, 0.0])
      entry[0] += 1
      entry[1] += time.monotonic() - started

  wrapper.__name__ = getattr(real, "__name__", name)
  wrapper.__doc__ = getattr(real, "__doc__", None)
  setattr(module, name, wrapper)


def install(bridge, compat, dialog_module):
  """Wrap everything that opens or writes the GeoPackage.

  Args:
    bridge: the plugin's `bridge` module, which holds the writing and
      style calls.
    compat: the `compat` module, whose layer repointing opens the file
      as well.
    dialog_module: the `dialog` module, wrapped because the act being
      measured is a Save as a PERSON causes it rather than a library
      call in isolation.

  Returns:
    None. Each named function is replaced by a wrapper that tallies
    its calls and passes through, so the measurement counts what the
    product actually did rather than what a reading of it suggests.
    Nothing is restored afterwards: this is a probe process that
    exits, and a wrapper left in a long-lived one would quietly
    measure the next thing too.
  """
  for name in ("write_gpkg_layer", "embed_style", "_drop_our_other_styles",
               "gpkg_tables", "gpkg_tables_we_would_replace",
               "drop_gpkg_layer", "write_working_state", "drop_our_other_styles",
               "read_working_state", "element_table_name"):
    counted(bridge, name)
  for name in ("save_style_to_database", "point_layer_at"):
    counted(compat, name)
  for name in ("same_destination", "same_source"):
    counted(dialog_module, name)


def counts_for(probe, elements, spacing):
  """Save and Load a map of `elements` elements, tallying every call.

  Args:
    probe: the running `Probe`.
    elements: how many elements the design should carry.
    spacing: map units between repeats -- coarse, because this is
      about the number of ELEMENTS and a fine spacing buys minutes of
      tiling that tell us nothing.

  Returns:
    A dict with the two wall times and the tally, or None where the
    element count is not on offer.
  """
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  suite = probe.suite
  probe.clear()
  dlg, _layer, _tid = probe.dialog()
  offered = [dlg.n_combo.itemText(i) for i in range(dlg.n_combo.count())]
  if str(elements) not in offered:
    dlg.close()
    return None
  dlg.n_combo.setCurrentText(str(elements))
  suite._tick(600)
  dlg.spacing_spin.setValue(spacing)
  suite._generate_and_wait(dlg)
  drew = len(dlg._element_layer_ids)
  assert drew == elements, (
    f"PREMISE: asked for {elements} elements and the map has {drew}, "
    f"so this reading is not about the count it claims")

  path = probe.path(f"scale_{elements}.gpkg")
  TALLY.clear()
  started = time.monotonic()
  assert probe.save(dlg, path), "PREMISE: the save failed"
  saved = time.monotonic() - started
  save_tally = {k: tuple(v) for k, v in TALLY.items()}
  dlg.close()
  probe.clear()

  opener = WeavingSpaceDialog(iface=suite._Iface())
  opener.live_check.setChecked(False)
  TALLY.clear()
  started = time.monotonic()
  opener.resume_widget.setFilePath(path)
  opener._load_pressed()
  suite._settle(opener, seconds=600)
  loaded = time.monotonic() - started
  load_tally = {k: tuple(v) for k, v in TALLY.items()}
  back = len(opener._element_layer_ids)
  opener.close()
  probe.clear()
  return {"elements": elements, "save": saved, "load": loaded,
          "back": back, "save_tally": save_tally,
          "load_tally": load_tally}


def show(rows, key, title):
  """Print one act's counts and seconds side by side across the counts.

  Args:
    rows: one dict per element count, as `measure` returns them --
      each carrying "elements", the wall seconds for each act, and a
      tally of how often each watched call was made.
    key: which tally to show, "save_tally" or "load_tally". The wall
      seconds shown beside it are chosen from the same word, so the
      two halves of the table cannot come to describe different acts.
    title: the heading to print above it.

  Returns:
    None; it prints. The table is the point: a call count that
    DOUBLES with the element count beside seconds that quadruple is
    what turns "saving is slow" into an equation, and neither column
    says it alone.
  """
  print()
  print("=" * 78)
  print(title)
  print("=" * 78)
  sizes = [r["elements"] for r in rows]
  print(f"  {'elements':<40}" + "".join(f"{n:>9}" for n in sizes))
  wall = "save" if key == "save_tally" else "load"
  print(f"  {'WALL SECONDS':<40}"
        + "".join(f"{r[wall]:>9.1f}" for r in rows))
  names = sorted({name for r in rows for name in r[key]})
  print(f"  {'-' * 40}" + "-" * (9 * len(sizes)))
  for name in names:
    counts = [r[key].get(name, (0, 0.0))[0] for r in rows]
    print(f"  {name + '  (calls)':<40}"
          + "".join(f"{c:>9}" for c in counts))
  print(f"  {'-' * 40}" + "-" * (9 * len(sizes)))
  for name in names:
    secs = [r[key].get(name, (0, 0.0))[1] for r in rows]
    if max(secs) < 0.05:
      continue
    print(f"  {name + '  (seconds)':<40}"
          + "".join(f"{s:>9.2f}" for s in secs))
  print()
  print("  RATIOS, each figure against the reading before it. A count")
  print("  doubling with n is linear; quadrupling is quadratic.")
  for name in names:
    counts = [r[key].get(name, (0, 0.0))[0] for r in rows]
    ratios = ["    -" if i == 0 or counts[i - 1] == 0
              else f"{counts[i] / counts[i - 1]:>5.1f}"
              for i in range(len(counts))]
    if max(counts) > 0:
      print(f"  {name:<40}" + "".join(f"{r:>9}" for r in ratios))
  walls = [r[wall] for r in rows]
  ratios = ["    -" if i == 0 else f"{walls[i] / walls[i - 1]:>5.1f}"
            for i in range(len(walls))]
  print(f"  {'WALL SECONDS':<40}" + "".join(f"{r:>9}" for r in ratios))


def main():
  """Measure save and load at four element counts and print the table.

  Returns:
    None; it prints. Four counts rather than two because the question
    is the SHAPE of the growth, and two points fit any line you like.
  """
  probe = start()
  from weavingspace_qgis import bridge, compat
  from weavingspace_qgis import dialog as dialog_module
  install(bridge, compat, dialog_module)

  rows = []
  for elements in (8, 16, 32, 64):
    print(f"---- {elements} elements", flush=True)
    row = counts_for(probe, elements, 900.0)
    if row is None:
      print(f"     ({elements} is not on offer for this family)")
      continue
    print(f"     save {row['save']:.1f}s  load {row['load']:.1f}s  "
          f"({row['back']} elements came back)", flush=True)
    rows.append(row)

  show(rows, "save_tally", "SAVE: what grows, and how fast")
  show(rows, "load_tally", "LOAD: what grows, and how fast")


main()
