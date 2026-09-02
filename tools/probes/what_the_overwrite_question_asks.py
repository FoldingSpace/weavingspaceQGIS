"""Does the overwrite question fire over a file that holds nothing?

`_may_overwrite`'s own Returns block promises that "a file that does
not exist, HOLDS NOTHING, or is one of ours is never asked about". Its
code asks `os.path.getsize(path) == 0`, and a GeoPackage OGR has
created and nothing has written to is 65,536 bytes of header holding
no layer -- non-empty by size, empty by content. That is the same
reading its sibling `_this_map_owns_the_file` was mended for this
morning, when a stub left by a cancelled first save made the file
nobody's for the rest of the session.

THE JOURNEY IS THE ORDINARY ONE. A first save is cancelled or fails
and leaves the stub; the plugin is reopened, so nothing remembers the
file; the person presses Save at the same path again. The question
raised there names "the tables this map needs" and "the rest of the
file", over a file with neither -- and its safe button is No, so a
stray Return declines a save the person asked for.

FOUR ARMS IN ONE RUN, and the last two are the whole discrimination:

  ABSENT   no file at all. The question must not be asked.
  STUB     a data source with no layers, as a stopped save leaves.
  REAL     somebody else's map, one table of their own. The question
           MUST be asked, or a repair that stopped asking altogether
           would pass the first two arms and destroy the ruling.
  FOREIGN  something that is not a GeoPackage at all. It must be asked
           about too: an empty answer from `gpkg_tables` also means
           "GDAL would not open this", so asking that alone would wave
           a save straight over somebody's file.

The stub is staged through OGR directly rather than by racing a
cancel, because what a stopped save leaves behind is a FILE STATE.

Run it with BOTH the checkout and this directory's parent on the path
so `probe_kit` can find itself:

    eval "$(bash tools/macos_qgis_env.sh 2>/dev/null \\
      | grep -E '^[A-Z_]+=' | sed 's/^/export /')"
    export QT_QPA_PLATFORM=offscreen PYTHONUNBUFFERED=1
    PYTHONPATH="$PWD:$PWD/tools" "$QGIS_PY" -u \\
      tools/probes/what_the_overwrite_question_asks.py
"""

import os
import sys

import probe_kit

sys.path.insert(0, probe_kit._repo_root())

from probe_kit import start  # noqa: E402


def leave_a_stub(path):
  """Create the data source a stopped save leaves and write nothing.

  Args:
    path: where the stub should be.

  Returns:
    Its size in bytes, so the arm can assert its own premise -- a stub
    that came out empty would make the case vanish.
  """
  from osgeo import ogr
  driver = ogr.GetDriverByName("GPKG")
  source = driver.CreateDataSource(path)
  assert source is not None, "PREMISE: OGR would not create the stub"
  source = None
  return os.path.getsize(path)


def leave_a_stranger_s_map(path, layer):
  """Write one table of somebody else's, so the file is plainly theirs.

  Args:
    path: where their file should be.
    layer: any vector layer to write, standing in for their work.

  Returns:
    None.
  """
  from weavingspace_qgis import bridge
  bridge.write_gpkg_layer(layer, path, "their_own_areas", first=True,
                          open_after=False)


def arm(probe, name, stage):
  """Drive one arm and report whether the overwrite question was raised.

  Args:
    probe: the `probe_kit` harness, whose project this clears first.
    name: names the arm and its own file, so no arm meets another's.
    stage: "absent", "stub", "real" or "foreign" -- what is at the
      path when the person presses Save.

  Returns:
    (whether the question was asked, what the file held beforehand,
    the plugin's own sentence).
  """
  probe.clear()
  dlg, layer, _tid = probe.dialog()
  path = probe.path(f"{name}.gpkg")
  try:
    probe.generate(dlg, spacing=700.0)
    size = 0
    if stage == "stub":
      size = leave_a_stub(path)
      assert size > 0, "PREMISE: the stub is genuinely zero bytes"
      assert not probe.tables(path), \
        f"PREMISE: the stub holds tables, so it is not a stub: " \
        f"{probe.tables(path)}"
    elif stage == "real":
      leave_a_stranger_s_map(path, layer)
      assert probe.tables(path), "PREMISE: their map wrote nothing"
      size = os.path.getsize(path)
    elif stage == "foreign":
      # SOMETHING THAT IS NOT A GEOPACKAGE AT ALL, which is the
      # control for the over-reach: `gpkg_tables` answers empty for a
      # file GDAL cannot open as well as for one holding nothing, so
      # asking it alone would wave a save straight over this.
      with open(path, "w", encoding="utf-8") as handle:
        handle.write("their notes, and not a GeoPackage\n")
      size = os.path.getsize(path)
      # ASKED THROUGH THE PLUGIN'S OWN READERS, because stdlib sqlite
      # RAISES on a file that is not a database and a probe whose
      # premise explodes reports on itself rather than on the product.
      from weavingspace_qgis import bridge
      assert bridge.why_a_file_will_not_open(path) == "unreadable", \
        "PREMISE: GDAL opens the foreign file, so it is not foreign"
      assert not bridge.gpkg_tables(path), \
        "PREMISE: the foreign file reads as a GeoPackage"
    # THE PLUGIN HAS NEVER MET THIS FILE, which is the fixture rather
    # than scenery: the ownership answer is remembered per file from
    # the moment it is first met, so a dialog that has already saved
    # here would answer "ours" and the question could not arise.
    assert path not in getattr(dlg, "_file_was_ours_when_met", {}), \
      "PREMISE: this dialog has already met the file"
    from weavingspace_qgis import bridge as _bridge
    before = sorted(_bridge.gpkg_tables(path))
    probe.suite.MODALS.clear()
    probe.suite.BAR_MESSAGES.clear()
    # THE WRITE IS ALLOWED TO FAIL AND THE QUESTION IS STILL THE
    # SUBJECT. A GeoPackage cannot be written over a text file, so the
    # foreign arm's save refuses -- correctly, and after the question
    # has been asked, which is the only thing this probe measures.
    try:
      wrote = probe.save(dlg, path, overwrite=False)
    except AssertionError as refused:
      wrote = f"refused: {str(refused)[:60]}"
    asked = [text for _kind, text in probe.suite.MODALS
             if "already exists" in str(text)]
    print(f"  {name} ({stage}):")
    print(f"    bytes on disk before : {size}")
    print(f"    tables before        : {before}")
    print(f"    the question asked   : {bool(asked)}")
    print(f"    the save wrote       : {wrote}")
    if asked:
      print(f"    it said              : {str(asked[0])[:170]!r}")
    return bool(asked), before, probe.said(dlg)
  finally:
    dlg.close()


def main():
  """Drive all four arms in one process and print the verdicts.

  Returns:
    None. It prints a sentinel once every arm has reported and the
    teardown is over, because an instrument that dies after reporting
    looks exactly like the thing it measures dying.
  """
  probe = start()
  print("WHAT THE OVERWRITE QUESTION ASKS")
  absent, _b1, _s1 = arm(probe, "absent", "absent")
  stub, _b2, _s2 = arm(probe, "stub", "stub")
  real, _b3, _s3 = arm(probe, "real", "real")
  foreign, _b4, _s4 = arm(probe, "foreign", "foreign")
  print()
  print(f"  absent  asked : {absent}   (must be False)")
  print(f"  stub    asked : {stub}   (the claim: must be False)")
  print(f"  real    asked : {real}   (must be True, or nothing is asked)")
  print(f"  foreign asked : {foreign}   (must be True: unreadable is "
        f"not empty)")
  print("ALL FOUR ARMS REPORTED, teardown complete.")


main()
