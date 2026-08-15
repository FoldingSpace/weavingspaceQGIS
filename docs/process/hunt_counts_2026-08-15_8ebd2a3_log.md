# Hunt: the counts the plugin reports about the user's own data

Direction: every COUNT the plugin reports to a user about their own
data — coverage_message, unmappable_areas_message /
count_areas_with_no_geometry, missing_values_message,
few_values_message / constant_field_message, and the "N tiles across M
element layers" note — each measured against what the map and the
region layer actually hold.

Shape: **two-stores**. Which frame is counted, the user's REGION layer
or the tiled output?

**Commit read: 8ebd2a3** (`8ebd2a3f37db23fcd7bf7d5a84f150484a3a9b99`,
"The hunt record and calibration catch up with the second round").
Everything below was measured against a `git archive HEAD` copy at
`$SCRATCH/repo`, never the live working tree — a sibling session is
editing it. Probe scripts live in the scratchpad
(`probe_lib.py`, `probe1_coverage.py` … `probe10_blank.py`), run under
QGIS 4.0.3's own python via `qpy_arch.sh` (a copy of `qpy.sh` that cds
into the archive copy). No repo source was modified.

---

## 12:0x  iteration 1  [logical]
TRIED:  Read the whole family at 8ebd2a3 and ask of each sentence
        which frame it counts. bridge.py:566 `count_areas_with_no_geometry`
        (LAYER), bridge.py:598 `unmappable_areas_message`,
        bridge.py:828 `coverage_message`, bridge.py:946
        `missing_values_message`, bridge.py:1182 `few_values_message`,
        bridge.py:1008ish `constant_field_message`; call sites
        dialog.py:6223–6320 and dialog.py:7150.
RESULT: The block at dialog.py:6255–6310 is mixed. `unit_count =
        len(region)` (dialog.py:6165) excludes blank-geometry rows;
        `missing_values_message` uses `layer.featureCount()`, which
        includes them; `_legend_size_note` (dialog.py:3509) reads the
        REGION LAYER via `_classification_values`; but
        `bridge.numeric_values_are_constant(gdf[field])`
        (dialog.py:6273) reads the TILED FRAME. That last one is the
        odd one out, and its own comment asserts "the renderer has
        already collapsed to a single class", which is a claim about a
        renderer seeded from the LAYER.
NEXT:   Measure. Start with the sentences that are easiest to check
        end to end (coverage, tile counts), then engineer a case where
        the tiled frame and the region layer disagree about how many
        distinct values a column holds.

## iteration 2  [perturbation] — probe1_coverage.py
TRIED:  Ten runs on synthetic uneven squares: tiled and as_icons, with
        and without blank-geometry rows, with a tile inset, at coarse
        and fine spacings. Second route: the distinct values of a
        unique per-area column read back off the OUTPUT element layers.
RESULT: Coverage and unmappable sentences agreed with the map in nine
        of ten. The tenth (icons + 4% tile inset, spacing 1500) lost
        one of four areas and said so correctly: "1 of 4 areas
        received no tiles". Noted in passing: with a blank-geometry
        row present the "'v' has 4 distinct values" notice DISAPPEARS,
        because the blank row's value is counted in the classification.
NEXT:   Chase the tile-count note, then the distinct-value family.

## iteration 3  [perturbation] — probe3_tilecount.py
TRIED:  "N tiles across M element layers" (dialog.py:7150, built from
        `len(gdf)`) against the sum of `featureCount()` over the
        element layers actually in the project — because
        `bridge.gdf_to_layer` silently skips rows whose geometry is
        empty or has no polygonal part after clipping.
RESULT: RULED OUT. Nine configurations (clip on/off, spacings 800 /
        1500 / 3000, icons, inset): claimed == held in every one.
        334/334, 112/112, 35/35, 12/12, 106/106.
NEXT:   Real, uneven data, where coverage loss is easy to provoke.

## iteration 4  [perturbation] — probe4_auckland.py, probe6, probe7
TRIED:  The packaged Auckland IMD fixture (155 SA2s), spacings 4000
        and 8000, tiled and icons, with blank rows and with nulls.
        Second route: distinct ids on the output layers; third route:
        spatial intersection of every output tile with every area.
RESULT: The coverage arithmetic is exactly consistent with the joined
        data every time (155 − 52 = 103 missing at 4000 m tiled;
        155 − 18 = 137 at 8000 m; 155 − 99 = 56 at 4000 m icons;
        155 − 141 = 14 at 2000 m icons). BUT in ICON mode at 2000 m
        every element layer holds exactly 155 tiles — one tileable per
        area, all 155 areas wearing an icon — while the sentence says
        "14 of 155 areas received no tiles and appear nowhere on the
        map". So the count measures whose DATA reached the map, not
        who received tiles, and in icon mode those differ. This is the
        field report ("icon mode saying areas were not represented
        when they were") and it is still live at 8ebd2a3. Flagged as a
        secondary finding: my nearest-centroid matching (probe7) was
        too noisy in dense Auckland to pin which 14 icons carry a
        neighbour's values, so I am not claiming the wrong-attribution
        half.
NEXT:   The distinct-value family, which is where the two-stores split
        is unambiguous.

## iteration 5  [perturbation] — probe8_minimal.py
TRIED:  Smallest case where the tiled frame and the region layer
        disagree about distinct values: two areas, one 4000 m square
        with v = 10 and one 100 m square with v = 99, spacing 2000,
        TILED mode. The small area receives no tiles, so the tiled
        frame holds one value and the layer holds two.
RESULT: **CONFIRMED.** The message bar said:
          "At 2,000 m spacing, 1 of 2 areas received no tiles…"
          "Every area has the same value for 'v', so it draws as one
           class, not a range."
        The second sentence is false on both halves.
NEXT:   Confirm against the renderer, and against a clean project, and
        with a control where the column really is constant.

## iteration 6  [perturbation] — probe9_confirm.py
TRIED:  Same fixture, clean project each run, reading the GRADUATED
        RENDERER off each output layer (a different mechanism from the
        message bar and from the attribute values).
RESULT: **CONFIRMED, second route.**
          region layer holds v = [10.0, 99.0]
          tiled map holds    v = [10.0]
          legend on a,b,c,d  = [(10.0, 54.5), (54.5, 99.0)]  ← TWO classes
          said: "Every area has the same value for 'v', so it draws as
                 one class, not a range."
        Control, genuinely constant column (v = 10, 10): legend
        [(10.0, 10.0)] — one class — and the same sentence, correctly.
        So the fixture is not the cause; the difference is exactly the
        two-values case.
        Also: the constant branch calls `said_constant.add(field)`
        (dialog.py:6275), which SUPPRESSES the true sentence
        `_legend_size_note` would have produced — "'v' has 2 distinct
        values, so it draws as 2 classes, not 5" — which probe1 shows
        is what the plugin says when no area is dropped.
NEXT:   Find a case with no coverage notice beside it, so the user has
        no hint at all.

## iteration 7  [perturbation] — probe10_blank.py
TRIED:  Three areas with geometry all v = 10, plus one row with NO
        GEOMETRY carrying v = 99, spacing 500 (every drawable area
        drawn, so `coverage_message` is silent).
RESULT: **CONFIRMED, and worse.**
          region layer holds v = [10.0, 99.0]
          tiled map holds    v = [10.0]
          legend on 'a'      = [(10.0, 10.0), (10.0, 99.0)]  ← two classes
          said: "1 of 4 areas have no geometry…"
                "Every area has the same value for 'v', so it draws as
                 one class, not a range."
        No coverage notice at all. The user is told flatly that their
        column is constant while the legend beside it shows a range.
NEXT:   Provenance, then write up.

## iteration 8  [logical]
TRIED:  `git log -S 'numeric_values_are_constant(gdf' -- dialog.py`
        and `-S 'def constant_field_message' -- bridge.py` on the live
        repo (read-only).
RESULT: Both introduced in **ab94d4d, 2026-08-09, "Robustness round:
        nine defects, one of them a segfault"**. Present from the day
        the notice was written.
NEXT:   Check against CLAUDE.md's settled decisions.

## iteration 9  [logical]
TRIED:  CLAUDE.md and the brief's list of settled decisions.
RESULT: "a constant column collapses to one class deliberately" covers
        a column that really is constant — my control case, which
        behaves correctly. It does not cover a column the SPACING (or
        a geometry-less row) made constant on the tiles while the
        user's layer still holds a range. Every neighbouring sentence
        in the same block is explicitly documented as counting the
        REGION layer "because the sentence says 'areas' and must mean
        the user's areas: counting the tiled frame here once produced
        '31 of 96 areas' for a layer of twenty-four" (dialog.py:6290).
        This is that same mistake, one branch higher up.

---

## FINDING (claimed)

**Harm, one sentence:** a user is told that every one of their areas
holds the same value for a column that in fact holds a range, so they
go looking for the fault in their data or accept a flat-looking map,
while the legend on the map beside it shows two or more classes.

**Where:** `weavingspace_qgis/dialog.py:6273` at 8ebd2a3 —
`if bridge.numeric_values_are_constant(gdf[field])`. `gdf` is the
TILED frame. The renderer this sentence describes is seeded from
`_classification_values(field)` (dialog.py:2366), which reads the
REGION LAYER. When an area is dropped by the spacing, or carries no
geometry at all, the two disagree; the sentence follows the tiles and
the map follows the layer. `said_constant.add(field)` on the next line
then suppresses the true `few_values_message`.

**Reproduction:**
`bash $SCRATCH/qpy_arch.sh $SCRATCH/probe9_confirm.py`
(also `probe10_blank.py` for the no-coverage-notice variant).

**Second independent route:** the graduated renderer read straight off
each output layer — two class ranges (10.0–54.5, 54.5–99.0) against a
sentence saying "one class, not a range".

**When it started:** ab94d4d, 2026-08-09.

**Confidence:** high for the sentence being false and contradicted by
the map's own legend; measured on a clean project with a passing
control. What would change my mind: a settled decision I did not find
saying the constant notice is deliberately a statement about the TILES
rather than about the areas — but the sentence's own words ("Every
area") and every neighbouring sentence's documented rule say otherwise.

## SECONDARY (reported, not claimed)

In ICON mode the coverage sentence counts areas whose DATA reached the
map, not areas that received tiles. Measured at 8ebd2a3 on the
Auckland fixture, spacing 2000, as_icons: all four element layers hold
exactly 155 tiles for 155 areas — every area wears an icon — and the
bar says "14 of 155 areas received no tiles and appear nowhere on the
map". At 4000 m: 616 tiles (a=155, b=152, c=155, d=154) and "56 of
155". This is the same complaint the field report described. I could
not pin down, within budget, whether those icons carry a neighbouring
area's values (probe7's nearest-centroid matching is ambiguous where
SA2s are smaller than the icon offset), so I am reporting the
count-versus-map contradiction only.

## RULED OUT

- "N tiles across M element layers" (dialog.py:7150): agrees with the
  element layers in nine configurations including clipped runs.
- `coverage_message` arithmetic in TILED mode: agrees with the values
  actually on the output layers in every run measured, including
  103/155 and 137/155 on the Auckland fixture.
- `unmappable_areas_message`: `unit_count + blank_areas` really is the
  layer's full row count in every case tried (1 of 5, 2 of 6, 1 of
  156, 2 of 157).
- `missing_values_message`: counts and totals matched the layer
  (7 of 155, 7 of 157). Its denominator includes geometry-less rows
  while `coverage_message`'s excludes them, so one run can say "of
  155" and "of 157" — cosmetic, and arguably the deliberate split the
  code comments describe. Not claimed.
