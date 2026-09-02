"""What the save's success sentence counts, against what the file holds.

The claim: `kept` is `len(order) - len(left_out)` and `vanished` is
never subtracted, so where BOTH happen -- an element's layer deleted
from the layers panel, and another element's table dropped from under
the map by somebody else saving the shared file -- the sentence
overstates what the file holds by one element per vanished element.

TWO ARMS IN ONE RUN, each on its own file and its own project, because
the control is what says the instrument can answer either way:

  CONTROL   one layer deleted from the project, nobody else acting.
            The sentence's count and the file must agree.
  TREATED   one layer deleted AND a colleague's change removing a
            second element's table. The sentence's count is compared
            with what the file actually holds.

The file is read with stdlib sqlite3 through `probe.tables`, which is
a different library from the one the save writes with, and everything
has let go of it by then.

Run it as the other probes here are run, with BOTH the checkout and
this directory's parent on the path so `probe_kit` can find itself:

    eval "$(bash tools/macos_qgis_env.sh 2>/dev/null \\
      | grep -E '^[A-Z_]+=' | sed 's/^/export /')"
    export QT_QPA_PLATFORM=offscreen PYTHONUNBUFFERED=1
    PYTHONPATH="$PWD:$PWD/tools" "$QGIS_PY" -u \\
      tools/probes/what_the_success_sentence_counts.py
"""

import re
import sys

import probe_kit

sys.path.insert(0, probe_kit._repo_root())

from probe_kit import start  # noqa: E402


def our_element_tables(names):
  """The element tables belonging to THIS map, twins and theirs aside."""
  return sorted(n for n in names
                if n.startswith("tiles_")
                and not n.endswith("_no_data")
                and not n.endswith("_theirs"))


def counted(said):
  """The pair of numbers the success sentence quotes, or None."""
  found = re.search(r"holds (\d+) of (\d+) elements", said)
  return (int(found.group(1)), int(found.group(2))) if found else None


def arm(probe, name, colleague, also_drop_the_deleted=False):
  """Drive one arm and print what was said beside what the file holds.

  Args:
    probe: the `probe_kit` harness, whose project this clears first --
      two arms sharing one `QgsProject` is how a control gets
      contaminated, which cost this project two wrong readings.
    name: names both the arm and its own GeoPackage, so no arm can
      meet what another left behind.
    colleague: True to stage what somebody else's save leaves -- our
      element's table gone, theirs in its place, and the file's own
      record naming their variable.
    also_drop_the_deleted: True to have that same save take the
      DELETED element's table as well, which is what reducing a shared
      design does and is the only journey on which the count's two
      errors do not cancel.

  Returns:
    (the pair of numbers the sentence quoted or None, the number of
    this map's element tables the file really holds).
  """
  from weavingspace_qgis import bridge
  probe.clear()
  dlg, layer, _tid = probe.dialog()
  path = probe.path(f"{name}.gpkg")
  try:
    probe.generate(dlg, spacing=700.0)
    assert probe.save(dlg, path), "PREMISE: the first save failed"
    order = sorted(dlg._element_layer_ids, key=bridge.element_order)
    assert len(order) >= 3, \
      f"PREMISE: {len(order)} elements is too few to delete one and " \
      f"lose another"
    held = set(probe.tables(path))

    # ---- SOMEBODY DELETES ONE ELEMENT'S ROW IN THE LAYERS PANEL.
    deleted = order[0]
    probe.project.removeMapLayer(dlg._element_layer_ids[deleted])
    twin = dlg._no_data_layer_ids.get(deleted)
    if twin:
      probe.project.removeMapLayer(twin)
    probe.suite._tick(200)
    assert probe.project.mapLayer(dlg._element_layer_ids[deleted]) is None, \
      "PREMISE: the element's layer is still in the project"

    if also_drop_the_deleted:
      # ...AND THE SAME COLLEAGUE'S SAVE TOOK THE DELETED ELEMENT'S
      # TABLE TOO, which is what a person reducing a shared design
      # does. Its layer is already gone from my project, so the loop
      # counts it as left out and never asks the file about it.
      gone = dlg._element_layer_ids.get(deleted)
      del gone
      by_name = bridge.element_table_name(deleted, "v1")
      for candidate in probe.tables(path):
        if candidate.startswith(f"tiles_{deleted}_"):
          by_name = candidate
          break
      assert bridge.drop_gpkg_layer(path, by_name), \
        f"PREMISE: {by_name!r} could not be removed"

    lost = None
    if colleague:
      # ---- ...AND SOMEBODY ELSE SAVES THE SHARED FILE, moving a
      # SECOND element to another column: their table in place of
      # ours, and the file's own record naming their variable.
      lost = order[1]
      element = probe.project.mapLayer(dlg._element_layer_ids[lost])
      assert element is not None, "PREMISE: the second element has no layer"
      ours = element.source().split("layername=", 1)[-1].split("|")[0]
      assert ours in held, \
        f"PREMISE: element {lost} reads {ours!r}, which the file does " \
        f"not hold, so it cannot go missing from under us"
      theirs = bridge.element_table_name(lost, "theirs")
      bridge.write_gpkg_layer(layer, path, theirs, first=False,
                              open_after=False)
      assert bridge.drop_gpkg_layer(path, ours), \
        f"PREMISE: {ours!r} could not be removed"
      record = bridge.read_working_state(path)
      moved = False
      for entry in (record.get("elements") or []):
        if str(entry.get("id")) == lost:
          entry["var"] = "theirs"
          moved = True
      assert moved, f"PREMISE: the record names no element {lost!r}"
      assert bridge.write_gpkg_layer is not None
      assert bridge.write_working_state(path, record), \
        "PREMISE: the colleague's record could not be written back"
      staged = set(probe.tables(path))
      assert ours not in staged and theirs in staged, \
        f"PREMISE: the file was not left as a colleague leaves it: " \
        f"{sorted(staged)}"

    # ---- AND I PRESS SAVE, believing the map is still mine.
    probe.suite.BAR_MESSAGES.clear()
    assert probe.save(dlg, path), "the save was refused outright"
    said = probe.said(dlg)
    ended = our_element_tables(probe.tables(path))
    pair = counted(said)
    print(f"  {name}:")
    print(f"    deleted from the project : {deleted}")
    print(f"    lost from the file       : {lost}")
    print(f"    the sentence counts      : {pair}")
    print(f"    the file actually holds  : {len(ended)}  {ended}")
    print(f"    said                     : {said[:260]!r}")
    return pair, len(ended)
  finally:
    dlg.close()


def main():
  """Drive all three arms in one process and print the verdicts.

  Returns:
    None. It prints a sentinel when every arm has reported and the
    teardown is over, because an instrument that dies after reporting
    looks exactly like the thing it measures dying.
  """
  probe = start()
  print("WHAT THE SUCCESS SENTENCE COUNTS")
  control = arm(probe, "control", colleague=False)
  treated = arm(probe, "treated", colleague=True)
  sharper = arm(probe, "sharper", colleague=True,
                also_drop_the_deleted=True)
  print()
  for name, (pair, real) in (("control", control), ("treated", treated),
                             ("sharper", sharper)):
    if pair is None:
      print(f"  {name}: NO COUNT IN THE SENTENCE")
      continue
    verdict = "agrees" if pair[0] == real else "OVERSTATES"
    print(f"  {name}: sentence {pair[0]} of {pair[1]}, file {real} "
          f"-> {verdict}")
  print("BOTH ARMS REPORTED, teardown complete.")


main()
