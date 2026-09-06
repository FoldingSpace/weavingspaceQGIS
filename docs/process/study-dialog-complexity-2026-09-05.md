# Study: is dialog.py over-complex?

(The maintainer's question of 2026-09-05, recorded in ROADMAP.md: "in
ways a simpler approach would match exactly while being less
bug-prone". An audit naming candidates with a measurement each; no
code, and none in the same breath as a candidate.)

## The measurements

Taken on `dialog.py` at `c2f89b1`:

    lines                                       25,875
    methods on WeavingSpaceDialog                  275
    attributes assigned on self                    193
    methods over 150 lines                          20
      _add_output_layers 1,152   _save_the_map 962
      _build_ui 960              _generate 854
      __init__ 768               _resume_from_gpkg 657
      _on_layer_style_edited 484 _restyle_only 411
    QTimer.singleShot sites                         24
    remembered-intent flags (*_pending)              9
    blockSignals sites                             114
    diagnostic dump sites                          102
    docstring lines                              6,316
    defects in the 2026-08-28 ledger, of 58         54
    catalogue entries anchored here, of 764        527

Two comparisons say whether this is size or shape. `topology_edits.py`
is 1,636 lines with no Qt in it, tested without a window, and the tab
that drives it is 3,333 lines; the split was made on 2026-08-30 and the
tab was rebuilt twice afterwards without the model moving. And the
save's three doors (MAINTAINING.md) are already described as a state
machine in prose, which is the sign that the code could be one.

## Candidates, by defect density and clarity of boundary

**D1. THE SAVE AND LOAD AS A MODULE WITHOUT QT**, as `topology_edits`
is to `topology_tab`. `_save_the_map` 962, `_resume_from_gpkg` 657,
`_write_or_drop_the_topology` 343, `_embed_or_drop_the_source`,
`_drop_tables_this_map_no_longer_has`, `_this_map_owns_the_file` and
`_may_overwrite` are about 2,300 lines whose inputs are a path, a
record and a list of layers, and whose questions -- whose file is it,
what does it hold, which moment is each half of the record about --
are answered by reading the file and the record. Measurement: five of
the seven defects repaired on 2026-09-02 were in the save; the drop was
wrong four times before it was redesigned. What would match exactly:
the writer already takes `should_stop` as a callable, so the model's
only reach back into the dialog is a flag it can be handed.

**D3. ONE DEFERRED-INTENT QUEUE.** Nine `*_pending` flags and 24
single-shot timers each implement the project's own rule -- consume at
the point of use, by a consumer that cannot decline for an unrelated
reason -- separately. Measurement: four defects came from a flag whose
consumer could decline (the press handed to the live path, the save
honoured against the old map, the load consumed against the other
file, the cancel poisoning the next save), and `_honour_a_queued_save`
is connected at three sites because no one of them covers the ground.
A queue of (intent, condition, act) drained at every landing and every
decline would be one mechanism with one test family.

**D2. THE LANDING AS A PIPELINE.** `_add_output_layers` at 1,152 lines
is the method every design of a fast path has to enumerate the rulings
of: split, build, seed in donor order, stamp, bind the group, report.
Named stages taking and returning the tiled-map value of the companion
study would make that list explicit, and a stage is what a catalogue
entry can anchor on without being re-anchored by every edit above it.

**D4. THE DOCK-FOLLOW FAMILY AS A MODULE.** `_on_layer_style_edited`
484, `_graduated_layer_edited` 361, `_adopt_dock_bounds` 338,
`_adopt_row_symbology` 282 and `_row_follows_the_renderer` 260 are
about 1,725 lines whose state is the attribution records
`_painted_ladders` and `_painted_categories`. Measurement: the
categorical and graduated halves are near-twins written months apart,
and reading one beside the other found three defects with no machine
(docs/TESTING.md, T-126); a module with one implementation over a
mode parameter removes the twin.

**D5. A BOUND-PAIR HELPER** for the 114 `blockSignals` sites: dataset
and group, `live_check` and the tab's box, the class combo, the tick
list and the drawing. Each pair is written out by hand and the rule
that the two must not disagree is asserted per pair.

**D6. THE DUMP AS A STRUCTURED TRACE**, 102 sites, low priority: it has
answered two diagnoses in one run each and costs nothing while off.

## What is not recommended

Splitting the file by line count. The 275 methods are one object's
state machine, and moving a method across a file boundary without
moving the state it reads makes the boundary a lie. The candidates
above each move a STATE with its methods, which is what the topology
split did. And nothing here in the same breath as a candidate: the
label/key separation touched 121 suite sites for a change smaller than
any of these, and 527 catalogue entries are anchored on lines a move
would shift.

## Order

D1 first, for defect density and the clearest boundary; then D3, which
is small and closes a recurring shape; then D2 with the companion
study's C3, since the two are one design. D4 and D5 follow as the
suite allows.
