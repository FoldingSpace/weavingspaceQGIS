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
