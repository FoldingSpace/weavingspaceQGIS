# Hunt log: the ORDER a user works in

HEAD c7b787cd91920493ebc01aa532b45d15c3c64f17 ("The macOS job finds the
interpreter where QGIS actually puts it"). Shape: asymmetry. Area: the
SEQUENCE a user works in rather than the values they use — plugin
opened before data exists, design chosen before a variable, Generate
before configuration, family changed after assignments, colour editor
opened before a run, project opened while the dialog is showing.

Probed against a `git archive HEAD` copy at
`$SCRATCH/probe`, never the live tree (another session is editing it).
Probe scripts in the scratchpad; runner `$SCRATCH/qpy_seq.sh`.

The question carried through every probe: WHAT ORDER DOES THE SUITE
ALWAYS DO THIS IN, AND WHAT HAPPENS IN THE OTHER ORDER?

## 00:00:00  iteration 0  [logical]
TRIED:  Orientation. Read the brief, CLAUDE.md's settled decisions,
        HUNT-RECORD.md (no "sequence/order" direction listed yet;
        nearest are asymmetry/twins at 5 hunts, 9 confirmed, and the
        in-flight-race rows), TEST-MAP.md around the dialog rows, and
        dialog._on_layer_changed / _update_layer_exclusions.
RESULT: inconclusive — orientation only. Candidate asymmetries written
        down before any code runs:
        (a) the suite's fixtures add the region layer to QgsProject
            BEFORE constructing the dialog. Everything the dialog
            does at construction time from `currentLayer()` is
            therefore never exercised with a None layer that later
            becomes a real one.
        (b) `_update_layer_exclusions()` is a "keep our own output out
            of the region combo" guard. When is it called? If only at
            construction and after a run, a layer added later (or a
            project opened later) could slip past it.
        (c) the colour editors (category_editor.py) are documented as
            usable BEFORE a run, reading values from the REGION layer.
            The graduated half is the near-twin. What does the
            categorical half do before a run that the quant half does
            not, or vice versa?
NEXT:   read the construction path and every caller of the exclusion
        and rebuild routines, then drive the dialog in the user's
        order under QGIS's own python.
