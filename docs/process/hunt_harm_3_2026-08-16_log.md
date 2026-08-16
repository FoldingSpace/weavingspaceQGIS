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

