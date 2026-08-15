# Hunt log: deferring to QGIS, races and odd data (HEAD e01896b)

Shape: two-stores. Area: deferral under races and odd data.
Probes in the session scratchpad, run under QGIS 4.0.3's own python
via `qpy.sh`. No repo source modified.

## 17:01:30  iteration 0  [logical]
TRIED:  Read e01896b, ROADMAP's "Deferring to QGIS" entry, CLAUDE.md
        settled decisions, the three new tests. Mapped every call site
        of `_refresh_deferring_rows` (dialog.py:4294 and dialog.py:6974
        only) against its own docstring, which claims it is "called
        wherever layers can have changed underneath the table -- a run
        landing, a project adopted, a style edited in QGIS's own panel".
RESULT: inconclusive-but-suspicious. `_on_layer_style_edited`
        (dialog.py:4293) calls it ONLY inside `if now_deferring:`. The
        symmetric case -- a dock edit that takes a layer BACK to a
        renderer a row can name -- falls straight through to the colour
        branches and never refreshes. So the row can keep reading
        "Deferring to QGIS" over a single-symbol/graduated/categorized
        layer. Two stores, and the row is the stale one.
NEXT:   Ask what mode that stale row feeds into a run.
        `_assignments` (dialog.py:5178-5185) passes `mode_raw` straight
        through when it is not in GRAD_SCHEMES, so mode becomes the
        literal string "Deferring to QGIS"; and the text-field
        correction at dialog.py:5194 is gated on `mode == "Graduated"`,
        so it does NOT fire. `bridge.seed_renderer`'s final `else`
        catches anything that is not Categorized/Single colour, i.e.
        a graduated renderer. Graduated over a TEXT column = no ranges
        = an element that paints nothing. Probe this.

## 17:14:05  iteration 1  [perturbation]
TRIED:  hd_probe1.py. (a) Does `getattr(QgsSymbolLayer,
        "PropertyFillColor")` resolve under this PyQt6 build?
        (b) Deferral begins in the dock (rule-based) and then ENDS in
        the dock (single symbol) -- does the row follow?
RESULT: (a) RULED OUT as a cause: it resolves to
        `<Property.FillColor: 3>`, StrokeColor to 4. The unscoped
        spelling still works here.
        (b) CONFIRMED as a disagreement. Row read 'Deferring to QGIS'
        while the layer held QgsSingleSymbolRenderer and
        `expressible_style` answered ('Single colour', None).
        `_assignments()` then reported mode='Deferring to QGIS'. After
        the next Generate the row read 'Categorized' over a flat blue
        single-symbol map -- the row lying in a second way. The map
        itself survived (the dock renderer was carried), so on THIS
        path the harm is cosmetic.
NEXT:   Force the re-seed. Decision 2's own path does it: change the
        element's variable. Make the new variable TEXT.

## 17:22:40  iteration 2  [perturbation]
TRIED:  hd_probe2.py. Element 'b' on v3, style hand-picked
        "Quant: Quantiles" (setCurrentIndex + activated, as a click
        does), Generate; rule-based renderer in the dock (row ->
        'Deferring to QGIS'); variable changed to 'landcover' (text);
        Generate.
RESULT: CONFIRMED, and it reaches the map.
        - row before the run: 'Deferring to QGIS';
          `_assignments` mode='Deferring to QGIS', var='landcover'.
        - notice fired as designed: "...so it is drawn by the plugin
          again."
        - it is drawn as NOTHING. renderer=QgsGraduatedSymbolRenderer,
          ranges=0, classAttribute='landcover', 112 features.
        - route 2, startRender + symbolForFeature: painted=0,
          unpainted=112.
        - route 3, QgsMapRendererParallelJob over the layer alone,
          200x200, white background: 0 non-background pixels of 10000
          sampled.
        - row AFTER the run: 'Categorized'. So the chooser says
          Categorized, the legend is empty and the element paints
          nothing.
        Mechanism: `_refresh_deferring_rows` runs at the END of
        `_add_output_layers` (dialog.py:6974), so the run reads the
        stale DEFERRING string as the element's MODE; the text-field
        correction at dialog.py:5194 is gated on mode == "Graduated"
        and never fires; `bridge.seed_renderer`'s final `else` builds
        a graduated renderer over words.
NEXT:   Minimality: is the hand-picked style ("touched") needed?
        `_follow_variable` (dialog.py:5492) rewrites an UNtouched
        chooser to `_plausible_mode`, which would heal it. And the
        second claim: does a data-defined fill really give a neutral
        swatch, measured on the icon's pixels?

## 17:41:10  scope correction received
The odd-data half of the brief (constant columns, nulls, non-finite
values, data-defined fills) is HANDED OFF to a separate hunt. Iteration
1(a) above is the only work spent on it: the enum lookup in
`renderer_has_data_defined_fill` resolves fine on this build. Nothing
further pursued there. The direction from here is RACES AND TWO STORES
only. Iteration 2's finding stays: it is a two-stores finding (the row
chooser holding "Deferring to QGIS" while the run reads that string as
a MODE), and the text column is only the payload that makes the
disagreement visible.

## 17:44:30  iteration 3  [logical + perturbation]
TRIED:  `_restyle_only` (dialog.py:5599-5705) read for deferral
        awareness. It has none: it compares `_signature(a)` against
        `_last_signatures[tid]` and calls `bridge.seed_renderer` on any
        element that differs. A deferring row's signature carries mode
        "Deferring to QGIS" and can never match the stored one, so
        EVERY style-only change re-seeds a deferring element.
        `carried_while_deferring` lives only in `_add_output_layers`.
        hd_probe3.py drove three ways in: (A) press Generate with
        nothing changed; (B) nudge the OPACITY spin box, the one
        control decision 6 deliberately leaves enabled; (C) same as B
        with a TEXT variable.
RESULT: CONFIRMED in all three.
        A: rule-based -> QgsGraduatedSymbolRenderer, 5 ranges on 'v3',
           row still reading 'Deferring to QGIS'. No notice of the loss.
        B: opacity widget enabled=True; same destruction.
        C: -> graduated, ranges=0 on 'landcover', painted=0/112.
        Note this is exactly the Generate the new test does NOT drive:
        `test_a_deferring_element_keeps_its_renderer_across_a_generate`
        changes the SPACING, which is a geometry change and takes the
        `_add_output_layers` path where `carried_while_deferring`
        protects it. The plain Generate takes the fast path.
NEXT:   hd_probe4.py, to name the path from the message bar and to
        reach it with live update instead of a button.

## 17:52:00  iteration 4  [perturbation]
TRIED:  hd_probe4.py -- same sequence, but rendering the layer to
        pixels before the Generate, and reading the message bar.
RESULT: DISAGREES WITH ITERATION 3 and must be resolved before
        anything is reported. Message bar confirms the fast path ran
        ("restyled b (no re-tiling needed)") in both D and E, and live
        update reached it with no button press (opacity 0.70 applied),
        BUT the renderer stayed QgsRuleBasedRenderer and the rendered
        pixels were unchanged at 3504/10000 before and after.
        So probe 3 destroyed the renderer and probe 4 did not, on
        what I believed was the same sequence. One of the two is
        measuring something other than what I think.
NEXT:   Do not report either until this reproduces one way. hd_probe5:
        the identical sequence, instrumented with the stored signature
        and the live one, the renderer type either side of the run, and
        run TWICE in one process to see whether it is order-dependent.

## 18:05:00  iteration 5  [perturbation]
TRIED:  hd_probe5.py (the plain-Generate sequence four times in one
        process, instrumented) and then hd_probe3.py RE-RUN unchanged.
RESULT: The plain-Generate destruction of iteration 3 DOES NOT
        REPRODUCE, and the re-run of probe 3 disagreed with itself:
        A and B kept QgsRuleBasedRenderer this time, and C came back
        QgsCategorizedSymbolRenderer instead of a 0-range graduated
        one. Probe 5's four repetitions all kept the renderer, while
        the bar said "restyled b (no re-tiling needed)" every time and
        `stored sig == live sig` was False with stored mode='Graduated'
        and live mode='Deferring to QGIS'.
        TWO CORRECTIONS TO MY OWN MEASUREMENTS, both mine and both
        worth recording:
        - `symbolForFeature` is the WRONG question of a
          QgsRuleBasedRenderer: it answers None even when the renderer
          paints, so probe 3's "painted=0/112" lines for rule-based
          renderers mean nothing. Only the graduated readings in
          iteration 2 (0 ranges) were the right question, and those
          were corroborated by an actual map render.
        - the outcome varies run to run, which points at a DEBOUNCED
          TABLE REBUILD landing (or not) between the dock edit and the
          run. A rebuilt style chooser is restored from
          `prev["mode_raw"]` only when `style_touched`; otherwise it
          comes back as `_plausible_mode`, which silently heals the
          stale DEFERRING string. So whether the stale string reaches
          `_assignments` is a race.
NEXT:   Stop trusting single runs. Repeat BOTH sequences five times
        each, arbitrate with rendered pixels rather than with
        symbolForFeature, and report a rate.

## 18:33:00  iteration 6  [the tree moved]
TRIED:  hd_probe8.py, wrapping `bridge.seed_renderer` to see whether
        the fast path really seeds a deferring element. It recorded ZERO
        calls while the bar still said "restyled b (no re-tiling
        needed)" -- an impossible pair against the code I had read.
RESULT: The SHARED TREE CHANGED UNDER ME. `git diff` now shows 105
        uncommitted insertions in dialog.py that were not there when I
        started, including a new `_restyle_only` arm whose comment
        reads: "Measured 2026-08-15 by a hunt: 640 interior pixels of
        the dock's green replaced by two shades of the plugin's Blues,
        the row still reading 'Deferring to QGIS', and the message bar
        saying only 'restyled b (no re-tiling needed)'." That is
        iteration 3's finding, fixed by somebody else while I was
        measuring. Iterations 3-5 are therefore NOT a race: probe 3 run
        1 measured the unpatched file and everything after it measured
        the patched one. All my remaining claims must be re-measured
        against the tree as it stands, and the report must say which
        tree that is.
NEXT:   Re-ask the one claim that survived on the CURRENT tree
        (iteration 6H, 3/3): deferral ENDS in the dock and the row does
        not follow. Does that reach the map now?

## 18:47:00  iteration 7  [perturbation]
TRIED:  hd_probe9.py against the working tree (e01896b + the
        maintainer's uncommitted dialog.py fixes). Deferral BEGINS in
        the styling panel (rule-based) and then ENDS there (plain single
        symbol, #3366cc); then one ordinary act -- press Generate, or
        nudge the opacity the design leaves enabled. Two variables, two
        triggers, three repeats each.
RESULT: CONFIRMED 12 of 12, deterministic.
        Row reads 'Deferring to QGIS' at both steps;
        `_assignments()` mode='Deferring to QGIS'; the new fast-path
        guard needs BOTH the row saying DEFERRING and the LAYER holding
        an inexpressible renderer, and the layer is expressible now, so
        `seed_renderer` is handed that string and falls through its
        final `else` to a GRADUATED renderer.
        - numeric v3: the user's single symbol (#3366cc, 1704 of 3504
          non-background pixels) is replaced by the plugin's Blues
          (#f7fbff 572, #6daed6 385, #08306b 355). Message bar says
          only "restyled b (no re-tiling needed)". No notice of the
          loss, though decision 8 requires one.
        - text landcover: QgsGraduatedSymbolRenderer with ranges=0 on
          'landcover'. Rendered non-background pixels 3504 -> 0 of
          10000. The element paints NOTHING, and the row then reads
          'Categorized'.
        Three independent routes agree: `_assignments()`'s mode string,
        the renderer's own class and range count, and a
        QgsMapRendererParallelJob pixel histogram.
        Root: `_on_layer_style_edited` calls `_refresh_deferring_rows()`
        only inside its `if now_deferring:` arm, so the row is never
        reconciled when the dock takes a layer BACK to a renderer a row
        can name. Probe 8H also measured the renderer columns (3, 4, 5,
        8) still disabled in that state, so the user cannot correct it
        from the plugin either.
        Not a settled decision: ROADMAP decision 1 says the row follows
        where it can express what the dock holds, and
        `_refresh_deferring_rows`'s own docstring says it is called
        "wherever layers can have changed underneath the table ... a
        style edited in QGIS's own panel".
NEXT:   Nothing further. Reporting.
