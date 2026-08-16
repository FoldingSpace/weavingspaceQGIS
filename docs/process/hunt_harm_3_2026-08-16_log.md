# harm-3: backwards from harm, 2026-08-16

Frozen tree: `ed7231f` (`hunt_probe.py --prepare --name harm-3`).
Direction: NOT code-reading. Start from a person who has spent an
afternoon on a map; ask what today's changes could take from them.

## The afternoon, written before any probe

She has a health layer, 144 areas, a rate column. Some areas were
never surveyed (NULL). One was a division by zero in the field
calculator (NaN). Two are rates over a zero population (+inf, -inf).
She picks a design, maps the rate to two elements and a categorical
to a third, sets 5 classes on Reds, pins the top class so this map
compares with last year's, hand-picks the three absence colours,
drops the opacity of one element, exports a GeoPackage, saves the
project, goes home, comes back and presses Generate again.

Ranked harms (what she would be furious to lose):

1. A colour meaning two things on the finished map: an absence
   colour that is also a class colour, or one absence kind wearing
   another's colour. She cannot see this; she sends the map.
2. An area drawn as NOTHING -- a paired-layer row whose kind no
   category covers. A hole that looks like the background.
3. Hand-picked absence colours destroyed by a reopen or a Generate,
   now that there are three of them and there used to be one.
4. A pin released when the data did NOT move under it (element
   values are a subset of the region's; the breaks are cut from the
   region).
5. Her hand renderer/filter on a paired layer surviving onto the
   WRONG element's paired layer.
6. The nudged bound putting a real value in the wrong class.
7. The kept comparison group ("create as new group") adopted and
   then replaced when a project is opened under the open dialog.

## Log

## 12:52:00  iteration 1  [logical]
TRIED:  harms 1 and 2 -- after one Generate over a column holding
        NULL, NaN, +inf and -inf, is any area drawn as NOTHING, do
        two absence kinds share a colour, or does an absence colour
        equal a class colour? Asked through started renderers
        (startRender / symbolForFeature / stopRender) on every element
        layer and every paired layer. Probe `probe_afternoon.py`.
RESULT: ruled out, at ed7231f. 64 areas, 4 elements, 220 tiles.
        ABSENCE_KINDS = no-value #dddddd, neg-infinity #8c9fc7,
        pos-infinity #c78c8c -- fixed per kind, so no positional
        re-sampling. Every paired feature got a symbol; every element
        feature got a symbol; no kind shared a colour; no absence
        colour appeared among the 5 class colours. The notice read
        "4 of 64 areas do not have finite numeric data", which is the
        right count.
NEXT:   harm 7, the kept comparison group. It is the one the brief
        names explicitly ("a kept comparison group") and the one
        today's ADOPTION change can reach.

## 13:40:00  iteration 2  [perturbation]
TRIED:  harm 7. Generate; tick "Create as new group" and Generate
        again so the FIRST group is the kept comparison; save; then
        open the project again with the dialog STILL SHOWING, and see
        which group is adopted and what the region chooser is pointed
        at. Probe `probe_kept_group.py`.
RESULT: at ed7231f, the adopted group was the right one (the newer),
        but the region chooser came back POINTED AT `a – no data`,
        one of the kept group's own paired layers -- the plugin
        offering its own output as a region, which the record names
        as how "the next map is tiled on top of the last".
NEXT:   confirm by a second route that does not save or reopen at
        all: ask the chooser's exception list directly.

## 14:05:00  iteration 3  [logical]
TRIED:  the same claim at the tree as it now stands. HEAD had moved
        under me twice -- ed7231f -> 3b78241 ("Withdraw the class-bound
        experiment, and mend what the hunts found") -> b1e86d1 -- so I
        re-prepared and re-measured. Three probes: `probe_chooser.py`
        (one group, no reopen), `probe_reopen_chooser.py` (one group,
        reopen under the open dialog, settled 5.5s) and
        `probe_two_groups.py` (kept comparison group AND reopen).
RESULT: ruled out at b1e86d1. In all three the chooser excepts every
        layer carrying `weavingspace_output` -- 6 of 6, then 11 of 11
        including the kept comparison group's -- offers only `region`,
        and stays pointed at `region` after the reopen. The ed7231f
        reading was real but is history: 3b78241 mended it. NOTE the
        class-bound nudge is WITHDRAWN as of 3b78241, so the harm
        about a nudged bound putting a value in the wrong class no
        longer has a mechanism.
NEXT:   harm 5 -- hand styling on the paired layer. Today's change
        makes a renderer or filter set there survive a Generate; the
        question is whether it survives onto the RIGHT element.

## 15:10:00  iteration 4  [perturbation]
TRIED:  harm 5. Hand-style element a's paired layer (lime single
        symbol, plus a filter), then re-tile by changing the spacing,
        then swap two elements' variables. Does her work survive, and
        does it stay on HER element? Probe `probe_hand_styling.py`,
        measured at b1e86d1 through startRender/symbolForFeature.
RESULT: harm 5 itself ruled out -- the renderer and filter survived
        the re-tile on element a and appeared on no other element,
        and after the swap the renderer was correctly re-seeded
        (a's assignment changed, which is the settled rule). But the
        probe reported something I had not asked for: element c's
        paired layer, never touched by hand, drew 2 of its 5 features
        as NOTHING.
NEXT:   chase that. It is harm 2 on my list -- an area drawn as a
        hole -- arriving by a route I had not thought of.

## 15:40:00  iteration 5  [perturbation]
TRIED:  the hole, with NO hand styling anywhere and measured in
        PIXELS rather than by asking the object graph: two ordinary
        Generates at spacing 1500 then 1300, then for every paired
        layer compare the kinds its rows carry against the categories
        its renderer offers, and render the layer alone over a
        magenta ground and sample the pixel at each uncovered row's
        centroid. Probe `probe_holes.py`, at eaf7485.
RESULT: **CONFIRMED.** Element a gained a `pos-infinity` row and its
        renderer offers only `neg-infinity, no-value`; element c
        gained two `neg-infinity` rows against categories
        `no-value, pos-infinity`. All three tiles sample #ff00ff --
        the ground -- while the control, a covered row on the same
        layer in the same render, paints #8c9fc7 and #dddddd. The
        same carry gives the mirror harm on the other two elements:
        b and d keep categories for kinds their tiles no longer hold,
        so their legends name absences the map does not draw.
NEXT:   the mechanism, which I went to only now.

## 16:05:00  iteration 6  [logical]
TRIED:  reading dialog.py for the site.
RESULT: `dialog.py:8188` clones the paired layer's renderer before
        the run and `dialog.py:8439` hands it back when the ELEMENT's
        styling gate says the element was kept; `_add_no_data_layer`
        then applies it unconditionally at `dialog.py:6638-6639`, and
        the branch that would ask what kinds the NEW layer holds
        (`_absence_colours_and_kinds`) is the `else` at 6641-6642, so
        it never runs. `bridge.make_no_data_renderer` builds ONE
        CATEGORY PER KIND PRESENT and no catch-all
        (bridge.py:2793-2801), which is right when it is seeded and
        wrong when it is carried: the element's own graduated
        renderer stays valid across a re-tile because its breaks come
        from the whole region, while the twin's categories enumerate
        the values one tiling happened to produce. The element's gate
        is the wrong question for the twin.
NEXT:   report. Ruled out on the way: harms 1, 2 (by the first
        route), 5, 6 (no mechanism -- the nudge was withdrawn at
        3b78241) and 7.

## 16:20:00  iteration 7  [logical]
TRIED:  HEAD moved four times under this hunt (ed7231f, 3b78241,
        b1e86d1, eaf7485, 7908f9d). Re-prepared and re-ran
        `probe_holes.py` against 7908f9d before reporting.
RESULT: confirmed, identical figures. Nothing under
        `weavingspace_qgis/` changed between eaf7485 and 7908f9d.
NEXT:   nothing. Reported.

## What was NOT looked at

Harm 3 (hand-picked absence colours across a reopen, now that there
are three of them) and harm 4 (a pin released though the data did not
move) were on the list and were not reached. Neither is refuted.

