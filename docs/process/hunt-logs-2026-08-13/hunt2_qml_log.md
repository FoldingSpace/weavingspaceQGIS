# hunt2 — the imported class source, end to end

Worktree: /private/tmp/claude-501/-Users-luke-claude-scratch/9a569ef7-3f5e-4a44-8ecf-716f080f3573/scratchpad/hunt2-qml

## 03:14:39  iteration 1  [logical]
TRIED: read the class-source path — dialog.py:2163 combo, :3763 _template_for,
  :4244 _restyle_only, :4290 template load, :4408 _signature, bridge.py:1051.
RESULT: two suspicions, neither confirmed yet. (a) _signature (dialog.py:4408)
  carries only the class_source TOKEN, so a QML rewritten on disk leaves every
  signature equal and _restyle_only:4308 `continue`s past the element — Generate
  would repaint nothing. (b) _adopt_row_symbology (:3073) restores ramp, count,
  opacity and hand-picks on reopen but nothing restores _class_choices.
NEXT: build a dialog-level reproduction of (a) — edit the QML, press Generate,
  read the colours off the layer's renderer — because the existing test
  test_a_class_source_file_that_changes_on_disk only exercises bridge.

## 03:16:58  iteration 2  [perturbation: edit the QML on disk between runs]
TRIED: scratchpad/repro_qml_stale.py — QML forest #112233, Generate, rewrite the
  same path as forest #aa0000, Generate again.
RESULT: CONFIRMED. forest still draws #112233 after the second Generate, and
  after a THIRD run at a changed spacing (a real re-tile). Second route agrees:
  rendered pixels contain #112233 and not #aa0000. Cause: _signature
  (dialog.py:4408) holds the token only, so _restyle_only:4308 and
  _add_output_layers:5222 both take the "unchanged" branch and reuse the old
  renderer. git log -S: present since the initial commit in this history.
NEXT: check whether the user has ANY route back (re-choosing the same file is
  documented as a no-op), then move to the reopen boundary — nothing restores
  _class_choices while ramp/count/opacity/picks are all adopted.

## 03:19:15  iteration 3  [logical: the reopen boundary]
TRIED: scratchpad/repro_qml_reopen.py — QML class source, gpkg output, real .qgz
  write/clear/read, fresh dialog, row pointed back at landcover, Generate.
RESULT: CONFIRMED that _class_choices is not restored (cell reads "Automatic
  colours"; nothing stamps the token anywhere) while opacity/ramp/count/picks
  are. The reopened map still showed the QML colours; after Generate forest went
  #112233 -> #8da0cb (Set2). ODDITY to chase: _ramp_choices came back "Blues",
  which is DEFAULT_RAMPS[1], not a categorical ramp — so ramp adoption may not
  be reaching a CATEGORIZED renderer at all.
NEXT: diagnose the Blues reading before writing anything up — if adoption fails
  for categorized renderers that is a separate sibling gap; if it is just the
  row default overwriting, the class-source loss stands alone.

## 03:21:25  iteration 4  [logical: the Blues oddity, QML removed from the picture]
TRIED: scratchpad/diag_ramp_adopt.py — no QML at all; Set1 on a categorized row,
  Greens on a graduated one, .qgz round trip, then re-point both rows.
RESULT: CONFIRMED a second, separate loss. The renderer itself still names Set1
  after the reopen (_ramp_name_matching reads 'Set1' off the layer), but
  _ramp_choices comes back 'Blues' (DEFAULT_RAMPS[row]) and after re-pointing the
  row at landcover it settles on 'Set2', never Set1. The graduated twin keeps
  'Greens' throughout. So the 2026-08-13 ramp adoption holds for graduated and
  is undone for categorized — suspect dialog.py:2606-2615, the Graduated/cat-ramp
  swap firing while the reopened row still carries no variable.
NEXT: pin the mechanism (what mode the reopened row reports) so the report names
  a line, then go back to the QML boundary with the remaining perturbations.

## 03:23:35  iteration 5  [perturbation: cross the boundary with a run in flight]
TRIED: scratchpad/repro_qml_inflight.py — Generate, and while the task is running
  pick a QML in the class-source cell, exactly as
  test_a_ramp_chosen_during_a_run_reaches_the_map drives the ramp cell.
RESULT: CONFIRMED, and it is the twin of the ramp defect fixed on 2026-08-13.
  The landing run re-reads _ramp_choices/_reverse/_opacity/_single/_class_counts
  (dialog.py:5157-5168) but NOT _class_choices, and `templates` is loaded at
  :5098 from the launch snapshot anyway. After landing: cell says "scheme.qml",
  the assignment says file:..., the map draws #8da0cb (Set2) and none of the
  file's four colours appear in the rendered pixels. Any later restyle heals it.
NEXT: two elements on one source, and import-twice / ramp-then-import, to see
  whether the same omission bites the ordinary (not in-flight) path too.

## 03:25:49  iteration 6  [perturbation: four cheap crossings at once]
TRIED: scratchpad/probe_qml_perturbations.py — (A) two elements on one QML,
  (B) import then a ramp then the same import again, (C) a GRADUATED style file
  offered as a class source, (D) a QML saved off one element's own output layer
  and imported into a second element.
RESULT: all four RULED OUT. A and D transfer all four file colours exactly; B is
  the documented precedence (a ramp chosen over a class source changes nothing
  for values the file names, and the swatch agrees); C falls back to automatic
  colours and warns in the message bar naming the file. Only cosmetic snag: that
  warning shows the last 40 characters of the path, so it reads
  "0gn/T/qml_perturb_.../graduated.qml".
NEXT: the donor-LAYER form of a class source (token "layer:<id>"), because output
  layer identities change at every run by design — so a donor that is the
  plugin's own output is a token that dies at the next Generate.

## 03:27:01  iteration 7  [perturbation: the donor-layer form of the source]
TRIED: scratchpad/probe_donor_layer.py — element c takes its classes from element
  b's OUTPUT layer (the dropdown offers them), then a re-tile kills that layer id.
RESULT: INCONCLUSIVE about the donor case itself (the map keeps its colours,
  because the signature is unchanged and the renderer is carried over) but it
  exposed something to chase: after the re-tile the CELL silently reads
  "Automatic colours" while _class_choices still holds the dead token, and the
  next trivial change — opacity 100 -> 80 — repainted the element from
  #112233/#445566/... to Set1 automatic colours with NO message at all.
  _restyle_only:4292-4298 swallows the load failure (templates[token] = None),
  where _add_output_layers:5107 collects template_errors and warns.
NEXT: re-run that with a QML FILE deleted rather than a donor layer, since a moved
  or renamed file is the case a user actually meets and
  test_a_class_source_that_moves_after_the_map_is_drawn covers only the re-tile.

## 03:27:56  iteration 8  [logical: the same loss by the restyle path]
TRIED: scratchpad/repro_qml_gone_restyle.py — QML class source, Generate, the
  file renamed into a subfolder, then opacity 100 -> 80 (a style-only change, so
  _restyle_only answers it and nothing re-tiles).
RESULT: CONFIRMED. The element is repainted from the file's #112233/#445566/
  #778899/#aabbcc to Set2 automatic colours; the only notice is the ordinary
  success banner "restyled b (no re-tiling needed)"; the class-source cell still
  reads "landcover-scheme.qml". Rendered pixels agree — none of the four file
  colours remain. The re-tile path does the opposite (keeps the map, names the
  file that went, covered by test_a_class_source_that_moves_after_the_map_is_drawn):
  the asymmetry is _restyle_only:4292-4298 swallowing the exception where
  _add_output_layers:5107 collects it into template_errors.
NEXT: nothing further to open — four crossings measured, three confirmed losses
  plus one adjacent observation about categorized ramp adoption. Writing up.
