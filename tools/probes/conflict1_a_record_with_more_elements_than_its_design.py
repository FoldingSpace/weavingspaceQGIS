"""Conflict 1, measured rather than coded: what does a record with more
elements than its design's n do when read back? A six-element design's
record is captured, its n lowered to four, and the record applied."""
import sys, probe_kit
sys.path.insert(0, probe_kit._repo_root()); probe = probe_kit.start(); suite = probe.suite
dlg, layer, tid = probe.dialog()
dlg.n_spin.setValue(6); suite._tick(600)
suite._choose_family(dlg, "hex-slice 6"); suite._tick(600)
print("design:", dlg._family_key(), "n", dlg._element_count(), "rows", dlg.table.rowCount())
for r in range(dlg.table.rowCount()):
  w = dlg.table.cellWidget(r, 1)
  if w is not None and w.count() > r % w.count(): w.setCurrentIndex((r + 1) % w.count())
suite._tick(300)
record = dlg._capture_working_state()
vars_at_6 = {e["id"]: e.get("var") for e in record["elements"]}
print("captured elements:", vars_at_6)
record["design"]["n"] = 4
dlg._apply_working_state(record)
suite._tick(800)
rows = {dlg.table.item(r, 0).text(): dlg.table.cellWidget(r, 1).currentText() for r in range(dlg.table.rowCount())}
print("after applying n=4 beside six elements: rows", rows)
print("first four match the record:", all(rows.get(k) == v for k, v in list(vars_at_6.items())[:4]))
print("surplus ids kept as memory (ramp/reverse records):", {k: (k in dlg._ramp_choices, k in dlg._reverse_choices) for k in list(vars_at_6)[4:]})
dlg.n_spin.setValue(6); suite._tick(800)
rows6 = {dlg.table.item(r, 0).text(): dlg.table.cellWidget(r, 1).currentText() for r in range(dlg.table.rowCount())}
print("raising n back to 6, the surplus rows read:", {k: rows6.get(k) for k in list(vars_at_6)[4:]}, "against the record's", {k: vars_at_6[k] for k in list(vars_at_6)[4:]})
print("PROBE ENDED")
