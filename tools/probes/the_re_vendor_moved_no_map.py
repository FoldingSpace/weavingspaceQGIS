"""Did upstream 6190917 change what any catalogue design DRAWS?

The re-vendor of 2026-08-31 carries twelve upstream commits, and four
of them rework `_setup_square_colouring`: n = 4, 9, 16 and 25 now
delegate to the grid constructor, n = 3 is translated "for backward
compatibility at present", and every remaining case is rebuilt from an
offset list rather than from hand-written translations. That is a
change to GEOMETRY, in a family the gallery draws.

WHY THE ORDINARY GATES CANNOT ANSWER IT. The colourspace comparison
scores the plugin's render against `TiledMap.render` from the SAME
vendored library, so a change upstream moves BOTH SIDES TOGETHER and
they go on agreeing -- this project's own "a differential cannot see a
fault its expected side shares". The functional suite asks whether the
plugin's own rules hold, not whether the library's output moved.

SO THIS COMPARES TWO CHECKOUTS, old against new, through the door the
dialog uses (`catalog.make_unit`, which supplies the plugin's own
aspect and parses a weave's passing pattern).

TWO CHECKOUTS RATHER THAN TWO sys.path ENTRIES. `deps.add_paths()`
PREPENDS the plugin's own vendor directory, and each checkout's copy
resolves that against its OWN tree -- so an arm that put an older
`weavingspace` on the path and then let the product's own loader run
would be loading whichever vendor the checkout owns, not the one the
arm meant. Giving each arm its own checkout removes the question
entirely, and the premise below asserts the two arms really did load
different library files, since two arms reading one library agree
perfectly and mean nothing.

(An earlier draft of this comment said `__init__.py` calls
`add_paths()` at import. It does not -- the call is inside
`classFactory`, QGIS's entry point. The design was right and the
reason was wrong, which is this project's own rule about a cause named
by reading, met while writing the instrument for another one.)

A DISAGREEMENT IS A FINDING RATHER THAN A FAILURE: upstream is entitled
to change its tilings, and what this gives is WHICH designs moved, so
the answer is a decision somebody makes rather than a surprise in a
rendered map.

    PYTHONUNBUFFERED=1 QT_QPA_PLATFORM=offscreen \\
      "$QGIS_PY" the_re_vendor_moved_no_map.py <old-checkout> <new-checkout>
"""

import json
import os
import subprocess
import sys

# The designs worth asking about. Square colourings are the family
# upstream reworked; the rest are the CONTROL -- if they move too, the
# instrument is wrong rather than the library.
WANTED = ("square-colouring", "grid", "laves", "archimedean",
          "hex-slice", "plain weave", "twill")

ARM = r'''
import json, sys
ROOT = sys.argv[1]
sys.path.insert(0, ROOT)
# THROUGH THE PRODUCT'S OWN DOOR. `weavingspace_qgis/__init__.py` calls
# `deps.add_paths()` inside `classFactory`, which is QGIS's entry point
# and not an import-time side effect -- so importing the package alone
# leaves `weavingspace` unimportable, exactly as it did here first try.
# The suite calls it explicitly for the same reason.
from weavingspace_qgis import deps
deps.add_paths()
from weavingspace_qgis import catalog

WANTED = tuple(json.loads(sys.argv[2]))
import weavingspace
where = getattr(weavingspace, "__file__", "?")
out = {}
for n, by_label in catalog.TILINGS_BY_N.items():
  for label, spec in by_label.items():
    if not any(w in label for w in WANTED):
      continue
    try:
      unit = catalog.make_unit(spec, spacing=500.0, crs=3857)
      tiles = unit.tiles
      out[f"{n:>3}|{label}"] = {
        "tiles": int(len(tiles)),
        "ids": sorted(map(str, tiles["tile_id"].unique())),
        "area": round(float(tiles.geometry.area.sum()), 4),
        "bounds": [round(float(b), 4) for b in tiles.total_bounds],
      }
    except Exception as exc:
      out[f"{n:>3}|{label}"] = {"error": f"{type(exc).__name__}: {exc}"}
print("LIBRARY " + where)
print("JSON_BEGIN")
print(json.dumps(out))
'''


def arm(root):
  """Fingerprint every wanted design in one checkout.

  Args:
    root: a checkout of the plugin -- its own `weavingspace_qgis`, its
      own vendored library. Imported in a SUBPROCESS, since two
      versions of one package cannot share an interpreter.

  Returns:
    (library path, {label: fingerprint}). A fingerprint is the tile
    count, the distinct ids, the total area and the unit's bounds:
    together they are what a person would see, since a translation
    moves the bounds and a rebuilt shape moves the area.
  """
  result = subprocess.run(
    [sys.executable, "-c", ARM, root, json.dumps(WANTED)],
    capture_output=True, text=True,
    env={**os.environ, "PYTHONPATH": root})
  if "JSON_BEGIN" not in result.stdout:
    sys.exit(f"the arm at {root} produced no reading:\n"
             f"{result.stdout[-3000:]}\n{result.stderr[-3000:]}")
  head, body = result.stdout.split("JSON_BEGIN", 1)
  library = [ln for ln in head.splitlines() if ln.startswith("LIBRARY")]
  return (library[0] if library else "LIBRARY ?"), json.loads(body.strip())


def main():
  """Compare the two checkouts and name every design that moved."""
  if len(sys.argv) != 3:
    sys.exit(__doc__)
  old_root, new_root = (os.path.abspath(p) for p in sys.argv[1:3])

  old_lib, old = arm(old_root)
  new_lib, new = arm(new_root)
  print(f"old {old_lib}\nnew {new_lib}")

  # PREMISE FIRST, and the second half is the one that matters: two
  # arms reading the SAME library agree perfectly and mean nothing,
  # which is exactly what a sys.path arrangement would have produced.
  assert old and new, "PREMISE: an arm built no designs at all"
  assert old_lib != new_lib, (
    "PREMISE: both arms loaded the same library file, so this "
    f"comparison cannot show anything: {old_lib}")
  print(f"old arm: {len(old)} designs   new arm: {len(new)} designs")

  gone = sorted(set(old) - set(new))
  fresh = sorted(set(new) - set(old))
  for label in gone:
    print(f"  ONLY IN OLD  {label}")
  for label in fresh:
    print(f"  ONLY IN NEW  {label}")

  moved, same, broke = [], 0, []
  for label in sorted(set(old) & set(new)):
    before, after = old[label], new[label]
    if "error" in after and "error" not in before:
      broke.append((label, after["error"]))
    elif before == after:
      same += 1
    else:
      moved.append((label, before, after))

  for label, error in broke:
    print(f"  NOW FAILS    {label}: {error}")
  for label, before, after in moved:
    print(f"  MOVED  {label}")
    for key in ("tiles", "ids", "area", "bounds", "error"):
      if before.get(key) != after.get(key):
        print(f"      {key}: {before.get(key)} -> {after.get(key)}")

  print(f"\n{same} unchanged, {len(moved)} moved, {len(broke)} now fail, "
        f"{len(gone)} gone, {len(fresh)} new")
  # Stated as its inverse: name anything that moved, rather than
  # announcing that all is well.
  if not (moved or broke or gone or fresh):
    print("NOTHING MOVED: every design draws the same ground as before.")


if __name__ == "__main__":
  main()
