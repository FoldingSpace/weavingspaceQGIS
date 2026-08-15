# Hunt log: write-only state in the graduated colour editor's records

Direction: write-only state. Area: `_pinned_bounds`, `_quant_colours`,
`_class_counts`, `_ramp_choices`, the `weavingspace_quant_style` layer
custom property, and the pinned/copied fields inside `_signature` and
`_run_signature`. HEAD 3d13b87. Probes run against a clean `git archive
HEAD` copy in the session scratchpad; the repo tree is not edited.

## 14:50:12  iteration 0  [logical]
TRIED:  Read the brief, CLAUDE.md, the hunt record; mapped every write
        and read of the six records with grep.
RESULT: inconclusive (survey only). Writers/readers found:
        `_pinned_bounds` written at dialog.py:3449 (adopt), 4527 (pin),
        4615 (copy), 4684 (release); read at 3002, 4512, 4541, 4595,
        4610, 4899 (_signature via _assignments), 6190 (landing re-read).
        `_class_counts` written at 3232 (spinner), 3605 (adopt), 4620
        (copy); read at 3215 (rebuild restores the spinner) and 4597.
        `_ramp_choices` written at 2689, 2824, 2910, 3503, 4621 (copy);
        read at 2829, 2835, 3262, 4868, 4872.
NEXT:   The copy path (`_copy_classification`, dialog.py:4548-4629) is
        the one place that writes `_class_counts` and `_ramp_choices`
        WITHOUT touching the widgets those records shadow, and
        `_assignments` reads k and ramp from the WIDGETS (4863, 4871),
        falling back to the records only when the widget is absent. So
        a copied class count may be recorded and never used. Chase that.

## 14:55:04  iteration 1  [perturbation]
TRIED:  `_copy_classification` writes `_class_counts[target]`,
        `_ramp_choices[target]` and `_reverse_choices[target]`
        (dialog.py:4620-4622) but never touches the widgets those
        records shadow, and `_assignments` reads k/ramp/reverse from
        the WIDGETS. Probe: source on 7 classes, target on 5, copy,
        then read the spinner, the record, the assignment and the
        renderer. probe_copy_count.py in the scratchpad.
RESULT: confirmed, with values. After the copy: the target layer's
        renderer has 7 ranges (the MAP), the Classes spinner still
        reads 5 and user_k is 5 (the CONTROL), `_class_counts` holds 7
        (the RECORD), `_assignments()["k"]` is 5. Ramp likewise:
        `_ramp_choices[target]` = "Reds" while the combo still says
        "Blues". Moving the spacing forces a table rebuild and only
        THEN does the spinner catch up to 7. So the copy's count and
        ramp are write-only until an unrelated design change.
NEXT:   The dangerous version of the same write: an UNCLASSED source
        has 50 classes, so the copy writes `_class_counts[target] =
        50` -- into a record whose own comment (dialog.py:3210) says
        it "is only ever written by a user moving the spinner". The
        rebuild clamps to 20 (dialog.py:3218). Test whether an element
        that was on 5 classes silently becomes 20 after a copy from an
        Unclassed element, an excursion back to Quantiles and any
        design change. That is the three-numbers-for-one-setting fault
        test_an_unclassed_excursion_leaves_the_count_alone guards,
        reached by a path that test does not walk.

## 14:56:20  iteration 2  [perturbation]
TRIED:  The Unclassed version, with a NEGATIVE CONTROL (same session
        run twice, once with the copy and once without):
        probe_unclassed_copy2.py. User sets the target to FOUR classes
        by hand, copies onto it from an element drawn Quant:
        Unclassed, takes the target back to Quant: Quantiles, then
        moves the spacing.
RESULT: confirmed. Without the copy the element stays at 4 classes
        throughout (map=4, spinner=4, `_class_counts`=4). With it:
        after the copy `_class_counts`=50 (the copy overwrote the
        user's 4); back on Quantiles the spinner reads 4 while the
        record holds 50; after the spacing change the spinner reads
        20, `_assignments()["k"]` is 20 and the map draws 12 classes
        (20 asked for, reduced to the column's 12 distinct values).
        The user's four classes are gone and nothing said so.
NEXT:   Reach the class count by a route that is not
        `renderer.ranges()`.

## 14:57:34  iteration 3  [perturbation]
TRIED:  probe_second_route.py: the same sequence in a fresh process on
        a clean project, then read the count off the layer's
        SERIALIZED style (exportNamedStyle -> XML, count `<range`) and
        off what features actually get (startRender /
        symbolForFeature / stopRender).
RESULT: confirmed by both. Before: 4 `<range>` elements, 4 distinct
        fills. After: 12 `<range>` elements, 12 distinct fills,
        spinner 20, `_class_counts` 50. Two mechanisms neither of
        which is `ranges()`, and they agree.
        WHEN IT STARTED: `self._class_counts[target_id] =
        len(classes)` arrived with d342fd2 (2026-08-14, "Copy to...").
        The invariant it breaks -- fifty is Unclassed's number and
        must not stick to the user's row -- was established the day
        before, 28a061c (2026-08-13), and the comment stating it sits
        at dialog.py:3210.
NEXT:   Nothing further; writing up. Smaller observation kept for the
        report: the copy's `_ramp_choices` and `_reverse_choices`
        writes are stale in the same way, applied only at the next
        rebuild.
