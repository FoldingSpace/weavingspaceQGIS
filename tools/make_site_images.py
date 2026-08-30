#!/usr/bin/env python3
"""Assemble the images used by README.md and the project page.

    QT_QPA_PLATFORM=offscreen ... <qgis python> tools/make_site_images.py

Two kinds of picture end up in docs/img/, and both are drawn here
rather than collected by hand. The maps come from the visual suite's
own case functions, called with a white canvas in place of the
magenta chroma key the suite measures against, so what a reader sees
is the output the tests actually check. The dialog is grabbed live
from a running instance, for the same reason.

Why a script at all: these images go stale the moment the plugin's
appearance changes, and a documented command is the difference
between refreshing them and hoping nobody notices. release.py runs it
on every release, and the content audit afterwards fails if the files
were not in fact rewritten.

Outputs:
  docs/img/*.png, overwritten in place.
"""
import argparse
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "docs", "img")

# The maps chosen for the page, as (gallery case function, filename).
# Between them they cover the range a reader needs to see: several
# variables at once, a weave, categorical data, a tiling whose parts
# are adjustable, glyphs, and the geometric modifiers.
#
# These are the SAME case functions the visual suite runs, called
# here with a white canvas instead of the suite's magenta chroma key.
# Publishing the tested maps rather than a second set drawn by a
# second code path is the point: a separate "pretty" renderer would
# be free to drift from the one under test, and the first anyone
# would know of it is a page showing maps the plugin no longer makes.
# Only what the published pages actually SHOW. Four more were rendered
# here until 2026-08-12 -- four-variables, hex-slice, icons and
# rotate-insets -- and were referenced by nothing: two had never been
# used, and two came loose when the pattern grid replaced the plates
# they sat in. Each cost a gallery render at every release to produce
# a file no reader ever met. If one is wanted again, add the case back
# here and reference it in the same commit, so a picture and its
# reader arrive together.
MAPS = [
  ("case_twill_gaps", "twill-weave.png"),
  ("case_categorized", "categorical.png"),
]

# White, not the suite's magenta and not transparency. Magenta is a
# measurement device, and a transparent PNG would leave pale ramp
# colours (a sequential ramp's light end) invisible against a dark
# page. Maps are read on white.
PAGE_BACKGROUND = "#ffffff"


def render_maps():
  """Draw the chosen gallery cases onto a white canvas.

  Returns:
    The number of maps written to docs/img/.

  Each case builds its own layers and renders them; the only thing
  changed here is the canvas colour, set through the constant the
  visual suite exposes for exactly this purpose. A case that fails is
  reported rather than skipped silently, since a page quietly missing
  half its images looks like a design choice instead of a fault.
  """
  sys.path.insert(0, os.path.join(ROOT, "tests"))
  import importlib.util
  spec = importlib.util.spec_from_file_location(
    "visual_tests", os.path.join(ROOT, "tests", "visual_tests.py"))
  visual = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(visual)
  visual.BACKGROUND = PAGE_BACKGROUND

  started = time.time()
  written = 0
  for case_name, target in MAPS:
    case = getattr(visual, case_name, None)
    if case is None:
      print(f"  the visual suite no longer has {case_name}")
      continue
    path = os.path.join(OUT, target)
    complaint = None
    try:
      case(path)
    except Exception as exc:                        # noqa: BLE001
      complaint = exc
    # Several cases assert on the fraction of CHROMA-KEY background
    # in what they drew ("gaps between the strands are visible"), and
    # on white there is no chroma key to count, so those assertions
    # fail here by construction. That measurement is the suite's job
    # and the suite still does it, in magenta, on every release. What
    # matters here is only whether a picture was actually produced,
    # so that is what gets checked: a fresh file of a plausible size.
    if os.path.exists(path) and os.path.getmtime(path) >= started \
            and os.path.getsize(path) > 5000:
      written += 1
    else:
      print(f"  {case_name} drew nothing usable: {complaint}")

  # the cases also write an "_unclassed" companion beside each map,
  # which the suite compares but no published page shows
  for stray in os.listdir(OUT):
    if stray.endswith("_unclassed.png"):
      os.remove(os.path.join(OUT, stray))
  return written


def start_qgis():
  """Start a headless QGIS, once, for everything this script draws.

  Returns:
    The QgsApplication, which the caller must shut down.
  """
  sys.path.insert(0, ROOT)
  from qgis.core import QgsApplication
  QgsApplication.setPrefixPath(
    os.environ.get("QGIS_PREFIX_PATH", "/usr"), True)
  app = QgsApplication([], True)
  app.initQgis()
  return app


def grab_dialog():
  """Render the plugin dialog offscreen and save it as an image.

  Returns:
    True when the grab was written.

  The dialog must be SHOWN before it is grabbed. Qt lays a widget out
  lazily, and grabbing one that has never been shown produces a
  picture with phantom sizes and unreliable visibility -- a lesson
  this project learned the hard way and wrote into CLAUDE.md.
  """
  from qgis.core import QgsProject
  from qgis.PyQt.QtCore import QEventLoop, QTimer

  sys.path.insert(0, os.path.join(ROOT, "tests"))
  import importlib.util
  spec = importlib.util.spec_from_file_location(
    "rt", os.path.join(ROOT, "tests", "run_tests.py"))
  rt = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(rt)
  rt._no_modal_dialogs()

  from weavingspace_qgis.dialog import WeavingSpaceDialog
  layer = rt.make_region_layer()
  QgsProject.instance().addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=rt._Iface())
  dlg.live_check.setChecked(False)
  # a design with several elements, so the table shows what the
  # plugin is actually for rather than a single empty row
  dlg.n_spin.setValue(4)
  dlg.kind_combo.setCurrentText("tiling")
  dlg.family_combo.setCurrentText("laves 3.3.4.3.4")
  dlg.show()
  loop = QEventLoop()
  QTimer.singleShot(1200, loop.quit)
  loop.exec()

  dlg.grab().save(os.path.join(OUT, "dialog.png"))
  dlg.close()
  return True


def main():
  """Draw every published image, then say whether all of them landed.

  Returns:
    0 when every map in MAPS was written, 1 otherwise -- release.py
    treats that as a failed step rather than publishing a page with
    holes in it. Leaves behind docs/img/*.png, overwritten in place
    (the maps named in MAPS, plus dialog.png), with the cases'
    "_unclassed"
    companions removed, and shuts the headless QGIS down again.

  One QGIS is started for the whole script because initialising it is
  the expensive part and the maps and the dialog grab both need it.
  --gallery is accepted and ignored: release.py still passes the
  report directory from when these maps were copied out of the
  gallery rather than rendered here, and quietly accepting it is
  cheaper than a flag day between the two scripts.
  """
  parser = argparse.ArgumentParser(description=__doc__)
  # accepted and ignored: release.py used to pass a gallery directory,
  # before the maps were rendered here rather than copied
  parser.add_argument("--gallery", default=None,
                      help=argparse.SUPPRESS)
  parser.parse_args()

  os.makedirs(OUT, exist_ok=True)
  app = start_qgis()
  written = render_maps()
  grab_dialog()
  app.exitQgis()

  # The pattern grid is NOT retaken here. It was, briefly, on the
  # reasoning that a published picture nobody regenerates goes stale.
  # That reasoning does not apply to this one: it shows the CATALOGUE
  # of families rather than the current renderer's output, so it
  # changes when somebody adds a family or rethinks the palette, and
  # not when the plugin does. Regenerating it every release would put
  # a rebuilt PNG in every release commit -- a diff nobody can review,
  # which is how people learn to wave diffs through -- and would make
  # each release depend on the reference environment being present.
  # Run tools/make_pattern_grid.py deliberately when the catalogue or
  # the design changes; sync_release_content.py knows not to expect it
  # fresh. (User instruction, 2026-08-12: the grid is done for now,
  # document it but do not regenerate each time.)

  print(f"wrote {written} map(s) and the dialog grab to docs/img/")
  return 0 if written == len(MAPS) else 1


if __name__ == "__main__":
  sys.exit(main())
