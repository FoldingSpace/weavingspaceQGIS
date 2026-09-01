"""What exactly does QGIS put in `layer_styles`, column by column?

Batching the style writes means writing those rows ourselves, and a
row that differs from QGIS's is a file a colleague opens differently.
So the format is read off a file QGIS itself wrote rather than
reproduced from the documentation.
"""

import os
import sys

sys.path.insert(0, os.environ.get("WS_REPO", os.getcwd()))

from tools.probe_kit import start                      # noqa: E402


def main():
  """Print the `layer_styles` schema and the rows QGIS wrote into it.

  Returns:
    None; it prints. Batching the style writes means writing those
    rows ourselves, and a row that differs from QGIS's is a file a
    colleague opens differently -- so the format is read off a file
    QGIS itself wrote rather than reproduced from documentation.
    The QML and SLD are abbreviated because they run to tens of
    thousands of characters and the question is the SHAPE.
  """
  probe = start()
  dlg, _layer, _tid = probe.dialog()
  dlg.n_spin.setValue(3)
  probe.suite._tick(400)
  probe.generate(dlg, spacing=900.0)
  path = probe.path("styles.gpkg")
  assert probe.save(dlg, path), "PREMISE: the save failed"
  dlg.close()
  probe.clear()

  from osgeo import ogr
  data = ogr.Open(path, 0)
  try:
    result = data.ExecuteSQL("PRAGMA table_info(layer_styles)")
    print("COLUMNS OF layer_styles:")
    for row in result:
      print(f"  {row.GetField('cid'):>2} {row.GetField('name'):<20} "
            f"{row.GetField('type'):<12} notnull={row.GetField('notnull')} "
            f"default={row.GetField('dflt_value')!r} pk={row.GetField('pk')}")
    data.ReleaseResultSet(result)

    result = data.ExecuteSQL("SELECT * FROM layer_styles ORDER BY id")
    print()
    print("ROWS (styleQML and styleSLD abbreviated):")
    definition = result.GetLayerDefn()
    names = [definition.GetFieldDefn(i).GetName()
             for i in range(definition.GetFieldCount())]
    for row in result:
      print("  ---")
      for name in names:
        value = row.GetField(name)
        if isinstance(value, str) and len(value) > 90:
          value = f"<{len(value)} chars> {value[:70]}..."
        print(f"    {name:<18} = {value!r}")
    data.ReleaseResultSet(result)
  finally:
    data = None


main()
