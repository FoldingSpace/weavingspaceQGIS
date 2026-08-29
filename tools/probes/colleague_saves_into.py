"""A SECOND PROCESS that owns a shared GeoPackage and saves into it
TWICE, with the parent's Load in between.

Ledger row 35 is about what happens to your map when somebody else
saves the shared file while yours is open, and neither half of that
can be faked from one process. A running QGIS serves its own cached
pages, so a file rewritten inside the parent would go on reading as it
was; and the drop that removes tables is gated on the file being the
saver's own, which a fresh dialog meeting somebody else's file is
not. So the colleague here is a whole QGIS that CREATES the file and
then changes their design while the parent holds the map open --
which is the only arrangement in which their save removes tables the
parent's layers are still pointing at.

THE RENDEZVOUS IS TWO FILES AND NOTHING CLEVERER. This process writes
`ready-1` when its first save has landed and waits for `go-2`; the
parent loads the map in between and then touches `go-2`. A poll with
a ceiling rather than a wait on a pipe, because a colleague that
hangs must end the measurement rather than hanging the parent too --
and a probe that waits forever is indistinguishable from one that is
working.

THEIR SECOND SAVE MOVES ONE ELEMENT'S VARIABLE, which is an ordinary
thing to do and is what makes their old tables stale: table names
carry the displayed variable (ruling 6 of 2026-08-25), so the save
writes `tiles_b_v1` and drops `tiles_b_landcover` -- the table the
parent's own layer is still reading from.
"""

import os
import sys
import time

sys.path.insert(0, os.environ.get("WS_REPO", os.getcwd()))

from tools.probe_kit import start                      # noqa: E402

WAIT_SECONDS = 300      # generous: the parent's Load runs a whole resume


def wait_for(flag) -> bool:
  """Poll for the parent's signal.

  Args:
    flag: the path the parent touches.

  Returns:
    True where it appeared, False on the ceiling -- reported rather
    than raised, so the parent's log says the colleague gave up
    rather than showing an exception it has to interpret.
  """
  until = time.monotonic() + WAIT_SECONDS
  while time.monotonic() < until:
    if os.path.exists(flag):
      return True
    time.sleep(0.25)
  return False


def main():
  """Create the shared file, wait, then save a changed design into it.

  Returns:
    None. Prints one COLLEAGUE line per fact the parent needs, so a
    failure here is legible in the parent's own log.
  """
  path, ready, go = sys.argv[1], sys.argv[2], sys.argv[3]
  probe = start()
  dlg, _layer, _tid = probe.dialog()
  try:
    probe.generate(dlg, spacing=700.0)
    assert probe.save(dlg, path), "COLLEAGUE: the first save failed"
    print(f"COLLEAGUE: created {os.path.basename(path)} holding "
          f"{probe.tables(path)}")
    open(ready, "w").close()
    if not wait_for(go):
      print("COLLEAGUE: the parent never opened the map, so the "
            "second save would not be 'while it is open'")
      return

    # THE CHANGE: element b moves from the categorical column to a
    # numeric one, so its table is written under a new name and the
    # old one is stale -- to them. The parent's layer is still
    # reading from it.
    dlg.table.cellWidget(1, 1).setCurrentText("v1")
    dlg._update_dynamic_columns()
    probe.suite._tick(300)
    probe.generate(dlg, spacing=700.0)
    assert probe.save(dlg, path), "COLLEAGUE: the second save failed"
    print(f"COLLEAGUE: after changing a variable the file holds "
          f"{probe.tables(path)}")
    print(f"COLLEAGUE: said {probe.said(dlg)[-160:]!r}")
  finally:
    dlg.close()


main()
