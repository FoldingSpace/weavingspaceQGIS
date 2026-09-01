"""Does a style read in one session come back the same as QGIS's own?

THE LOAD'S WORST TERM IS `loadDefaultStyle`, called once per table
inside the resume's loop: measured 2026-09-01 at 0.37s, 1.32s and
6.94s for 32, 64 and 128 elements, growing 5.3x per doubling, because
each call opens the GeoPackage and reads a `layer_styles` table whose
row count grows with the map. The cure is the same as the save's --
read every style ONCE and apply each from memory.

BUT A STYLE IS NOT A TABLE, and the risk is different in kind. What
comes back is the map a person sees: the renderer, the class breaks,
the hand-picked colours, the opacity and blend mode, and the CUSTOM
PROPERTIES this plugin's whole identity machinery is keyed on -- the
element id, the region stamp, the pinned bounds. The resume's own
comment says the stamps ride inside the embedded style, so a batched
read that dropped them would leave a map that draws correctly and is
no longer recognisably ours.

So this compares the two routes on EVERY layer of a saved map, by
exporting each layer's whole style back out and diffing the text, and
by comparing the custom properties key by key.
"""

import os
import sys

sys.path.insert(0, os.environ.get("WS_REPO", os.getcwd()))

from tools.probe_kit import start                      # noqa: E402

COUNTS = (4, 12)


def a_saved_map(probe, elements: int, spacing: float):
  """Draw and save a map, and return its path and its table names.

  Args:
    probe: the running `Probe`.
    elements: how many elements the design should carry.
    spacing: map units between repeats.

  Returns:
    A pair (path, tables), or (None, None) where the count is not
    offered. The premise that the map carries the elements it claims
    is asserted, since a comparison over a map that is not the one
    named says nothing.
  """
  probe.clear()
  dlg, _layer, _tid = probe.dialog()
  if not (dlg.n_spin.minimum() <= elements <= dlg.n_spin.maximum()):
    dlg.close()
    return None, None
  dlg.n_spin.setValue(elements)
  probe.suite._tick(600)
  dlg.spacing_spin.setValue(spacing)
  probe.suite._generate_and_wait(dlg)
  assert len(dlg._element_layer_ids) == elements, (
    f"PREMISE: asked for {elements} and drew "
    f"{len(dlg._element_layer_ids)}")
  path = probe.path(f"styles_{elements}.gpkg")
  assert probe.save(dlg, path), "PREMISE: the save failed"
  dlg.close()
  probe.clear()

  from weavingspace_qgis import bridge
  tables = sorted(name for name in bridge.gpkg_tables(path)
                  if name.startswith("tiles_"))
  assert tables, "PREMISE: the saved file holds no element tables"
  return path, tables


def style_of(layer) -> str:
  """A layer's whole style as text, for comparing two routes to it.

  Args:
    layer: the layer to describe.

  Returns:
    The QML QGIS itself would write for it. Exporting the style back
    OUT is the comparison rather than reading the renderer's fields
    one at a time: it covers the renderer, the labelling, the opacity,
    the blend mode and everything else in one, and it cannot go stale
    the day somebody adds a property to the record.
  """
  from qgis.PyQt.QtXml import QDomDocument
  doc = QDomDocument()
  layer.exportNamedStyle(doc)
  return doc.toString()


def properties_of(layer) -> dict:
  """Every custom property on a layer, as a plain dict.

  Args:
    layer: the layer to read.

  Returns:
    A dict of key to value. THE STAMPS ARE THE POINT: the element id,
    the no-data marker and the region a map was drawn from all live
    here, and the resume's comment says they ride inside the embedded
    style -- so a batched read that lost them would give back a map
    that draws right and is no longer recognisably this plugin's.
  """
  return {key: layer.customProperty(key)
          for key in (layer.customPropertyKeys() or [])}


def main():
  """Bring every layer of a saved map back both ways and compare.

  Returns:
    None; it prints. Every layer is reported rather than the first
    difference, because a named list is a work list and "they differ"
    is not.
  """
  probe = start()
  from qgis.core import QgsVectorLayer
  from qgis.PyQt.QtXml import QDomDocument
  from weavingspace_qgis import bridge

  clean = True
  for elements in COUNTS:
    print(f"---- {elements} elements", flush=True)
    path, tables = a_saved_map(probe, elements, 900.0)
    if path is None:
      print(f"     ({elements} is not on offer)")
      continue

    # ONE READ FOR THE WHOLE FILE, which is the thing under test.
    batched = bridge.read_embedded_styles(path)
    assert batched, (
      "PREMISE: the batched read found no styles at all, so the "
      "comparison below would pass by having nothing to compare")

    faults = []
    covered = 0
    for table in tables:
      theirs = QgsVectorLayer(f"{path}|layername={table}", table, "ogr")
      assert theirs.isValid(), f"PREMISE: {table} would not open"
      theirs.loadDefaultStyle()

      ours = QgsVectorLayer(f"{path}|layername={table}", table, "ogr")
      assert ours.isValid(), f"PREMISE: {table} would not open twice"
      qml = batched.get(table)
      if qml is None:
        faults.append(f"{table}: the batched read found no style for it")
        continue
      doc = QDomDocument()
      assert doc.setContent(qml), f"{table}: the stored QML would not parse"
      applied, why = ours.importNamedStyle(doc)
      if not applied:
        faults.append(f"{table}: the stored QML would not apply ({why})")
        continue

      covered += 1
      if style_of(theirs) != style_of(ours):
        faults.append(f"{table}: the two styles differ")
      if properties_of(theirs) != properties_of(ours):
        only_theirs = {k: v for k, v in properties_of(theirs).items()
                       if properties_of(ours).get(k) != v}
        faults.append(f"{table}: custom properties differ, "
                      f"e.g. {dict(list(only_theirs.items())[:3])}")

    assert covered, (
      "PREMISE: not one table was compared, so a clean result here "
      "would be the absence of a measurement rather than agreement")
    if faults:
      clean = False
      print(f"     {len(faults)} DIFFERENCE(S) over {covered} tables:")
      for line in faults:
        print(f"       - {line}")
    else:
      print(f"     {covered} tables came back identically by both "
            f"routes, styles and stamps alike", flush=True)
    probe.clear()

  print()
  print("=" * 78)
  print("THE TWO ROUTES AGREE" if clean else
        "THE TWO ROUTES DISAGREE -- the differences are listed above")
  print("=" * 78)


main()
