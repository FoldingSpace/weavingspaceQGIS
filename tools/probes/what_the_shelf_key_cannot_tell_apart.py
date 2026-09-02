"""Does the edit shelf know a design from its dual?

THREE hunts of round seven reached the same mechanism from three
directions on 2026-09-02 -- backwards from harm, the specification
itself, and the stochastic sessions -- which is the strongest
confirmation this method produces. `topology_edits.shelf_key` is
`f"{family}#{n}"`, and "Map the dual instead" changes neither term, so
a design and its dual share one shelf: an edit made on the dual is
replayed onto the design's own like-named edge when the box comes off
again, and the other way about.

THIS IS THE VERIFICATION, and it differs from all three on purpose.
Each of them took its verdict from GEOMETRY -- the unit's ground, or
the tiles read back out of a saved GeoPackage with OGR. This one asks
the RECORD: the shelf key itself, and what the shelf holds under it,
which is the store the mechanism is about and the one none of them
read. Geometry is kept only as corroboration at the end, and the
control is an ordinary design change, whose key DOES move.

Run it with QGIS's own interpreter, from the checkout::

    unset PYTHONHOME PROJ_LIB QGIS_PREFIX_PATH
    set -a; eval "$(bash tools/macos_qgis_env.sh)"; set +a
    QT_QPA_PLATFORM=offscreen PYTHONUNBUFFERED=1 \\
      PYTHONPATH="$PWD:$PWD/tools" "$QGIS_PY" -u \\
      tools/probes/what_the_shelf_key_cannot_tell_apart.py

It prints a completion sentinel, because a probe that dies at
interpreter teardown looks exactly like the product failing.
"""
import probe_kit

DESIGN = "hex-slice 4"   # a design with edge classes and a dual


def ground(unit):
  """A number that moves when the unit's shape does.

  Args:
    unit: the Tileable the dialog is holding.

  Returns:
    The total area of its tiles, rounded, or None where there is no
    unit to ask. Corroboration only: the verdict here is the record.
  """
  if unit is None:
    return None
  try:
    return round(float(sum(unit.tiles.geometry.area)), 3)
  except Exception:
    return None


def main():
  """Read the shelf key and the shelf across a dual toggle.

  Returns:
    None. Prints the key at each step, what the shelf holds, and a
    completion sentinel.
  """
  probe = probe_kit.start()
  suite = probe.suite
  from weavingspace_qgis import topology_edits

  dlg, _layer, _tid = probe.dialog()
  dlg.opt_experimental.setChecked(True)
  suite._choose_family(dlg, DESIGN)
  suite._tick(400)
  assert suite._wait_for_the_topology(dlg), \
    "PREMISE: the tab never answered about this design"
  panel = dlg.topology_panel
  assert panel._topology is not None, \
    f"PREMISE: {DESIGN} carries no topology, so there is nothing to edit"

  def key():
    """The key the PRODUCT would use, asked the way the product asks.

    Reading it any other way is how this probe first reported the
    repair as absent: a helper mirroring the OLD signature goes on
    printing the old answer however the product moves.
    """
    return topology_edits.shelf_key(dlg._family_key(), dlg.n_spin.value(),
                                    dlg._mapping_the_dual())

  def shelf():
    return [dict(edit) for edit in (dlg._topology_shelf.get(key()) or [])]

  def whole_shelf():
    return {name: len(edits)
            for name, edits in sorted(dlg._topology_shelf.items())}

  # ---- THE DESIGN'S OWN EDIT, which is the ordinary act.
  before = key()
  panel.apply_button.click()
  suite._tick(600)
  suite._wait_for_the_topology(dlg)
  on_the_design = shelf()
  print(f"design            key={before}  shelf={len(on_the_design)} "
        f"edit(s)  ground={ground(dlg._unit)}")
  assert on_the_design, \
    "PREMISE: pressing Apply recorded no edit, so nothing below means anything"

  # ---- THE CONTROL: an ordinary design change DOES move the key, so
  # the edits go quiet, which is what the shelf exists to do.
  # THE CONTROL IS A FAMILY CHANGE RATHER THAN AN ELEMENT COUNT, and
  # that is a correction to this probe rather than a preference:
  # moving `n_spin` REPOPULATES the family list and lands on whatever
  # that count offers, so the first draft went from `hex-slice 4#4` to
  # `square-colouring 5#5` and every later reading was about a design
  # nobody had chosen. This project's own rule about adding a step to
  # a sequence -- ask what it resets -- met inside the instrument.
  suite._choose_family(dlg, "laves 3.3.4.3.4")
  suite._tick(600)
  suite._wait_for_the_topology(dlg)
  print(f"another family    key={key()}  shelf={len(shelf())} edit(s)"
        f"  <- the control: a design change moves the key")
  suite._choose_family(dlg, DESIGN)
  suite._tick(600)
  suite._wait_for_the_topology(dlg)
  assert key() == before, (
    f"PREMISE: the chooser came home to {key()} rather than {before}, "
    f"so the treatment below is about another design")

  # ---- THE TREATMENT: the dual is a design in its own right, and the
  # key cannot see it.
  dlg.opt_map_dual.setChecked(True)
  suite._tick(800)
  suite._wait_for_the_topology(dlg)
  with_the_dual = key()
  print(f"dual ticked       key={with_the_dual}  shelf={len(shelf())} "
        f"edit(s)  ground={ground(dlg._unit)}")

  panel.apply_button.click()
  suite._tick(600)
  suite._wait_for_the_topology(dlg)
  on_the_dual = shelf()
  print(f"edited the dual   key={key()}  shelf={len(on_the_dual)} "
        f"edit(s)  ground={ground(dlg._unit)}")

  dlg.opt_map_dual.setChecked(False)
  suite._tick(800)
  suite._wait_for_the_topology(dlg)
  home = shelf()
  print(f"dual unticked     key={key()}  shelf={len(home)} "
        f"edit(s)  ground={ground(dlg._unit)}")

  print()
  print(f"the key is the same with the dual on and off: "
        f"{before == with_the_dual}")
  print(f"the design's own shelf grew by the dual's edit: "
        f"{len(home) > len(on_the_design)}")
  print(f"every shelf entry, by key: {whole_shelf()}")
  print("\nPROBE COMPLETE: control and treatment reported, teardown next.")
  dlg.close()


main()
