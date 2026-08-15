# Hunt log: pinning and copying INSIDE larger operations (two-stores)

HEAD 2adb7dd. Shape: two stores of one fact. Area: a pin or a copy made
while a run is in flight; live update queueing a rerun underneath one;
the restyle fast path against the run-landing path; the sequence
generate -> pin -> copy -> change spacing -> generate again.

Working copy for probes: scratchpad only. Repo source untouched.

## 15:24:50  iteration 0  [logical]
TRIED:  Orientation. Read the brief, HUNT-RECORD.md, CLAUDE.md's settled
        decisions, and the HEAD commit message so the seven fixes of
        tonight are not re-found.
RESULT: n/a. Established the shape of the landing re-read at
        dialog.py:6353-6388 -- category_colours, quant_colours, pinned
        (pins AND copied ladder), range_bounds -- and the writers behind
        the colour editor window at dialog.py:4565-4625 (picked,
        range_changed, pin_changed) and 4629-4779 (_copy_classification).
NEXT:   Ask the brief's question: what is the NEWEST thing written
        through that window, and does the landing read it?

## 15:28:40  iteration 1  [logical]
TRIED:  Hypothesis H1. The newest things written through the editor
        window are the ones a COPY writes beside the ladder:
        `_class_counts[target]`, `_ramp_choices[target]`,
        `_reverse_choices[target]` and the target row's OWN WIDGETS
        (dialog.py:4754-4771, `_sync_target_controls` at 4781, added at
        HEAD by tonight's fix "a copy wrote records without moving
        controls"). `_add_output_layers` re-reads none of them.
RESULT: inconclusive by reading. Reading says the ladder short-circuits
        the classifier (bridge.py:1690) and the copied positional
        colours cover every class, so a stale k/ramp/reverse in the
        snapshot may not change what is PAINTED. That is exactly the
        kind of reasoning this project's record says to distrust.
NEXT:   Stop reading and measure. Probe: perform the same copy twice --
        once with a run in flight, once quiescent -- and compare the
        target layer's drawn ranges, its symbol colours, its stamp, and
        the table's controls between the two.

## 15:32:39  iteration 2  [perturbation]
TRIED:  H1 measured. probe_copy_inflight.py: same copy (element a, v3,
        7 classes, Blues -> element b, v1, 3 classes, Reds) performed
        (i) quiescent and (ii) with a run in flight, then compared the
        TARGET LAYER's drawn ranges and symbol colours, its
        weavingspace_quant_style stamp, and the table's controls.
RESULT: RULED OUT. The two are byte-identical. Both draw 7 classes
        [(0,0) #f7fbff, (0,8) #d6e5f4, (8,16) #abd0e6, (16,27.71)
        #6daed6, (27.71,42.29) #3787c0, (42.29,65.14) #115ca5,
        (65.14,65.14) #08306b]; both stamp the same 7 colours and the
        same six copied breaks; both leave spinner 7 / ramp cell Blues
        / _class_counts 7. The stale k and ramp in the landing snapshot
        do not reach the map, because a copied ladder short-circuits
        the classifier (bridge.py:1690) and the copied positional
        colours cover every class.
NEXT:   The map is right; look at what DESCRIBES it. `_unworn_stripes`
        (dialog.py:3955) asks the ELEMENT LAYER which classes no tile
        wears, and `_custom_swatch_for` (3998) caches the resulting
        icon under a key holding the picks, ramp, scheme, k, window,
        pins and the REGION layer's fingerprint -- and nothing about
        the element layer or the run. H2: the hatching on the ramp
        cell is a second store of "which classes are empty", and the
        landing never invalidates it.

## 15:35:04  iteration 3  [perturbation]
TRIED:  H2 measured with probe_swatch.py: the hatching on a Custom ramp
        cell against `_unworn_stripes` recomputed from the landed layer,
        for a copy quiescent, a copy in flight, and after two further
        Generates at other spacings.
RESULT: The icon the cell holds is the UNHATCHED one in every case
        (truth [3,4,5,6], icon matches "none", identical hash
        b9a5f9ae5808 across all five measurements). But this is NOT
        mine to claim: `docs/process/hunt_swatch_2026-08-15_2adb7dd_
        log.md`, committed while I worked, already has it confirmed
        twice over on two fixtures, with provenance (ee506ab). Same
        defect, found first by another hunt. Recorded here as a
        DUPLICATE, not a finding.
        Also noted: HEAD moved under me to 4376ba1 (0305787 then
        4376ba1). The only plugin-source change since 2adb7dd is the
        deletion of `_numeric_value_count`, a helper nobody called, so
        everything measured here stands at both.
NEXT:   Drop the descriptive layer and go back to the map. H3: whatever
        the landing defers rather than applies, an explicit Generate
        afterwards must recover. Sweep the editor's actions -- pin,
        unpin, copy, class count, ramp, display window, class colour,
        variable, style -- performed (i) quiescent and (ii) with a run
        in flight, and compare the FINAL map after one more explicit
        Generate. Anything that fails to converge was destroyed rather
        than deferred.

## 15:41:53  iteration 4  [perturbation]
TRIED:  H3 measured. probe_converge.py, 18 actions x {quiescent, in
        flight} x {live update off, live update on}: pin low, pin high,
        copy, pin-then-copy, copy-then-unpin, class colour, display
        window, class count, ramp, opacity, copy from Unclassed, copy
        from Equal intervals, copy-then-count (releases the ladder),
        copy-then-style, copy-then-pin-on-top, copy both ways, variable
        change, style to Unclassed. Compared every element's drawn
        ranges, symbol colours, opacity, layer name and BOTH stamps,
        plus six dialog records.
RESULT: RULED OUT, all 36 pairs CONVERGE. With live update OFF the
        landing differs for exactly the four the settled rule defers
        (class count, ramp, opacity, style/variable) and the difference
        is gone after the next Generate; with live ON even the landing
        agrees, because the queued rerun restyles. Nothing pinned or
        copied was destroyed by a run landing on top of it.
NEXT:   That comparison is RELATIVE: if a loss happened on both paths it
        would read as convergence. H4, absolute: after an in-flight pin
        + copy, save the project, clear, reload into a fresh dialog, and
        ask whether the ladder and the pin come back -- and the same
        through a GeoPackage output, which is the artefact that leaves
        the machine.

## 15:44:30  iteration 5  [perturbation]
TRIED:  H4 measured. probe_roundtrip.py: pin (low 30 on element a, v3)
        + copy a->b, done quiescent and in flight, then (i) project
        saved, project CLEARED, reloaded into a fresh dialog, and (ii)
        the same with a GeoPackage output, the file then opened COLD as
        a brand new QgsVectorLayer with no dialog anywhere.
RESULT: RULED OUT. All four artefacts carry it. a draws
        (0,30)(30,42)(42,55.5)(55.5,77)(77,121) before and after the
        round trip; b draws the fitted ladder
        (0,30)(30,42)(42,55.5)(55.5,77)(77,77) in both. Stamps survive:
        a {"pinned":{"low":30.0}}, b {"pinned":{"breaks":[30,42,55.5,
        77]}} with five positional colours, and the fresh dialog adopts
        both. The cold .gpkg reads back identical (421888 / 413696
        bytes). Note b's low pin is correctly LEFT BEHIND -- v1 runs
        0..11 and pin_problem refuses 30 -- which is tonight's fix
        working through the in-flight path too.
NEXT:   H5: seeded random interleavings, in case a combination beats
        the hand-picked ones.

## 15:48:10  iteration 6  [perturbation]
TRIED:  H5. probe_sweep.py, seed 20260815, 22 sessions (10 + 12), live
        update chosen at random per session. Each: Generate; launch a
        second run; THREE random actions from {pin, unpin, copy, class
        count, ramp, style, class colour, display window} while it is in
        flight; land; Generate again; settle. Invariants: I1 the
        dialog's own class list (_current_graduated_classes,
        the helper the editor and the swatch both use) equals
        what each element layer draws; I2 the same steps replayed
        quiescently leave the same map.
        Then control_i1.py, the negative control the record insists on:
        re-seed one landed layer from a different ramp and a smaller k
        behind the dialog's back.
RESULT: 0 problem sessions of 22. Both invariants FIRE under the
        control -- I1 reported element a believing
        (0,4)(4,14.2)... while drawing (0,6)(6,21)..., and the
        divergence check reported ['a'] -- so the 22 clean sessions are
        evidence rather than decoration.
NOTHING CLAIMED. The map, the stamp, the project file and the
GeoPackage all survive a pin or a copy made underneath a run, on both
live settings. The one disagreement I found in the area (the hatching)
belongs to the swatch hunt, which got there first and reproduced it
twice.

## 15:48:39  iteration 7  [close]
TRIED:  git status; check nothing of mine is in the source tree.
RESULT: Nothing of mine outside this log. No repo source was edited by
        this hunt at any point; every probe lives in the scratchpad
        (probe_copy_inflight.py, probe_swatch.py, probe_converge.py,
        probe_roundtrip.py, probe_sweep.py, control_i1.py) and each is
        one command under qpy.sh. (`git status` is NOT clean at the
        moment I write this: category_editor.py and dialog.py carry
        somebody else's in-progress fix for the swatch hunt's second
        finding, arriving while I worked. Everything measured above
        was measured before it.)

## What I would look at next

The area's RECORDS are sound; what is not sound is what DESCRIBES
them, and that is where both disagreements found tonight in this
neighbourhood live -- the hatched swatch, and the open editor's stale
ladder, both in the swatch hunt's log. So the next direction here is
not "a pin inside a run" but "every widget that renders a pinned or
copied element, against the layer": the legend QGIS builds, the
Classes cell on an Unclassed row, the class preview under the editor,
and the message-bar notices, each asked twice -- once after a restyle
and once after a landing.

The other thing worth a night: the landing's re-read list is a
HAND-KEPT list of four keys against a record set that keeps growing.
It is correct today, measured six ways. It has been wrong three times,
each time within days of something new being written through that
window. A test that walks the editor's writers and requires each to be
re-read would cost less than a fourth occurrence.
