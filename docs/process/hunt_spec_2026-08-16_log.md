# Hunt: THE SPECIFICATION ITSELF (settled decisions in CLAUDE.md)

Brief: `tools/bug_hunt_brief.py --shape one-boundary --area "the settled
decisions in CLAUDE.md"` -- `--shape specification` does not exist; the
five shapes offered are asymmetry, one-boundary, two-stores, unreachable,
write-only, and one-boundary is the closest to "do two rules contradict
each other at a boundary".

Direction: not whether the code fails the spec, but whether a settled
decision is itself wrong, or cannot be honoured alongside another.

Tree frozen at 3b34364 by `tools/hunt_probe.py --prepare`. (HEAD was
7bd34a6 when this hunt started and moved to 3b34364 within the first
minute, before any probe ran.)

## 18:07:24  iteration 0
TRIED:  orientation. Read the whole "Design decisions already settled"
        section (CLAUDE.md 1091-1568) and HUNT-RECORD's "Directions not
        yet tried". Listed candidate tensions rather than defects.
RESULT: inconclusive, by design. Candidates, in the order I will test:
        (a) "Quant: Unclassed" is EXEMPT from the reduction rule, and
            both the constant-column rule and the reduction rule exist
            to protect the LEGEND, not the map;
        (b) graduated KEEPS classes an element cannot reach (hatched)
            while categorized DROPS values an element does not hold --
            opposite answers to one question, each justified by a
            principle that refutes the other;
        (c) "hand styling survives unless that element's assignment
            changed" vs "breaks are cut once so every element agrees";
        (d) additive-only palettes: one project, two machines, two
            legends.
NEXT:   (a) first, because it is measurable in one probe.

## 18:10:54  iteration 1
TRIED:  "ONE COLOUR MEANS ONE THING ... class breaks are cut ONCE, from
        the region layer's values, and every element carrying that
        column wears them" (2026-08-14) against "CLASS BOUNDS A PERSON
        SET" (0.24.3, 2026-08-15), which keys pins by tile id AND
        field, i.e. per ELEMENT. Case: two elements on one column, one
        of them pinned.
RESULT: confirmed (as a spec contradiction; the code does exactly what
        both decisions say). Probe `pin_legend.py` on frozen 3b34364,
        one column of 14 values, Quantile k=5, ramp Reds, ONE shared
        `classify_from`:
          A (first class pinned at 10): (1,10) (10,23.25) (23.25,42)
                                        (42,77) (77,120)
          B (untouched, same column):   (1,3.6) (3.6,9.8) (9.8,23.6)
                                        (23.6,58.4) (58.4,120)
        All five ramp colours appear in BOTH legends. #fcbba2 means
        10-23.25 on A and 3.6-9.8 on B. That is the SAME fault the
        one-legend rule was written to kill (its own measured example
        was 3.4-14.0 vs 4.0-13.6 -- an order of magnitude smaller than
        this), reintroduced by a feature settled a day later. Nothing
        warns.
NEXT:   second route through the dialog, and check whether anything
        anywhere compares pins across elements sharing a column.

## 18:13:23  iteration 2
TRIED:  same finding, SECOND ROUTE. Not the ranges but the renderer's
        own dispatch: `symbolForFeature` through a QgsRenderContext,
        asking what colour each value is actually PAINTED on each
        element.
RESULT: confirmed. 8 of the 14 values paint a different colour on the
        pinned element than on the untouched one carrying the same
        column: 4, 6 and 9 are `#fff5f0` on A and `#fcbba2` on B; 13
        and 18 are `#fcbba2` on A and `#fa694c` on B; 25 and 34 shift
        a rung; 71 shifts a rung. So the fault reads both ways -- one
        colour, two numbers in the legend; one number, two colours on
        the map -- and the second reading comes from QGIS's renderer
        rather than from our introspection of ranges.
NEXT:   candidate (a): is "Quant: Unclassed is exempt from the
        reduction" honoured in both places that implement the
        reduction?

## 18:13:23  iteration 3
TRIED:  "Quant: Unclassed (50 linear intervals) reproduces a
        CONTINUOUS RAMP rather than a class count anybody chose", and
        its exemption from "a column cannot be cut into more classes
        than it has distinct values". `make_graduated_renderer` has
        `elif not unclassed and 0 < distinct < int(k)`.
        `classes_the_map_will_draw` -- whose docstring says "This is
        the same arithmetic make_graduated_renderer performs, kept
        beside it so the two cannot drift" -- has never heard of the
        scheme, and `_legend_size_note` is not gated on it either:
        both call sites test `mode != "Graduated"`, and an Unclassed
        row IS mode "Graduated" with k forced to 50 (dialog
        `_assignments`, GRAD_SCHEMES).
RESULT: confirmed, with values. Column of 12 distinct values, scheme
        Unclassed:
          classes the MAP draws      : 50
          classes_the_map_will_draw(): 12
          sentence reported to user  : "'v' has 12 distinct values, so
                                       it draws as 12 classes, not 50."
        The map draws fifty; the message bar says twelve. That is the
        one thing this family of notices exists to prevent, in its own
        docstring's words -- "the sentence describes a legend the map
        does not have". It fires for any Unclassed row on a column
        with 2..49 distinct values, which is most small region layers.
        Also measured, for the spec argument rather than the defect:
        Unclassed over 3 distinct values gives 50 legend classes of
        which `bridge.unworn_classes` says 47 are worn by nothing,
        where "Equal intervals" with the same k=50 reduces to 3 and 0
        unworn. Same column, same k, opposite legends.
NEXT:   candidate (b), the categorized/graduated asymmetry about
        classes an element cannot reach; then re-read HEAD.

NOTE ON THE TIMES: iterations 1-3 were first written with
estimated timestamps and corrected in place to the clock
readings actually taken (18:10:54, 18:13:23, 18:13:23 -- 2 and
3 were logged in one pass after both probes had run). The
brief names estimated timestamps as a discipline failure and it
is; recording the slip rather than hiding it.

## 18:15:00  iteration 4
TRIED:  the plainest version of the same question, with NO pins: two
        elements on one column with different per-row Classes counts.
        Also read `test_one_variable_gets_one_legend_wherever_it_appears`
        to see what it actually fixes.
RESULT: confirmed as an argument, weaker than the pin case. k=5 and
        k=6 on the same column give
          k=5  (1,3.6) (3.6,9.8) (9.8,23.6) (23.6,58.4) (58.4,120)
          k=6  (1,3.17) (3.17,7) (7,15.5) (15.5,31) (31,67.5) (67.5,120)
        so "every element carrying that column wears them" is not true
        as written -- it is true of elements the user has left alone.
        The guard leaves every row's k at its default and sets no
        pins, and its own oracle is CLASS INDEX, not colour ("elements
        deliberately wear different ramps ... what must agree is the
        class"). Re-derived the pin finding against that oracle: value
        13 is class index 1 on the pinned element and 2 on the
        untouched one; 8 of 14 values land in a different class index.
        So the pin case fails the guard's own oracle, not merely a
        stricter one I invented. (Correcting my own arithmetic in
        iteration 2: 8 values, not 9.)
        Also noted, not chased: `_legend_size_note` dedupes its notice
        BY FIELD -- "several elements may carry the same column" --
        which itself assumes one class count per column, and reports
        whichever row it met first.
NEXT:   re-read HEAD and report. Candidate (b) (graduated KEEPS
        unreachable classes and hatches them, categorized DROPS values
        it does not hold) stays an argument: I did not find a case
        where it costs a user something I can measure, and the
        hatching is a dialog swatch, which the reader of the finished
        map never sees.

## 18:15:00  HEAD re-check before reporting
`tools/hunt_probe.py --status`: frozen 3b34364, HEAD 3b34364.
HEAD did NOT move while this hunt ran. It moved ONCE, from
7bd34a6 to 3b34364, in the first minute -- between reading
CLAUDE.md and running --prepare -- so every probe here tested
3b34364 and 3b34364 is current.
