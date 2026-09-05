# The tile-to-zone overlay clips tiles whose answer is foregone

*A note offered to weavingspace, from the QGIS plugin that vendors it.
Measured 2026-09-04 against upstream 0.0.7.89 at commit 6190917.*

## What the code does now

In `get_tiled_map`'s `prioritise_tiles` path — the default — every tile
is clipped against every zone and the fragment with the largest area
wins:

    overlaps = self.region.overlay(join_layer, make_valid = False)
    overlaps[area_name] = overlaps.geometry.area
    lookup = overlaps.iloc[overlaps.groupby("joinUID")[area_name]
                           .agg("idxmax")][["joinUID", id_var]]

The fragments are never drawn. They exist only to carry an area, and
the `TODO` above that block already calls the section
performance-critical.

## The observation

**A tile lying wholly inside one zone has a foregone argmax.** The
fragment is the tile, its area is the tile's area, and the winner is
that zone. Clipping it computes something already known.

So the interior tiles can be assigned by a `within` join and only what
is left needs clipping.

## What it is worth

On the packaged Auckland data (155 zones, EPSG:2193):

    tiles that touch the region, spacing 250     10,526
      interior (no clip needed)                   6,324   60.1%
      straddling (a clip is really needed)        4,202

    `crosses 4` at spacing 250: 9,289 tiles clipped where 15,300 were

The share **rises with the map** — 48% at spacing 350, 74% at 150, 82%
at 100 — so it pays most exactly where the seconds are. We quote counts
rather than seconds here because the machine was under load when this
was written, and a comparison across two runs on a busy machine is not
a measurement.

## Exactness

**37,511 tiles compared across 6 designs and 2 spacings; not one
assigned to a different zone.** The oracle is written out separately
rather than calling the library's own lookup, so the two sides share no
code and a disagreement would be a defect by construction.

## The one guard it needs

If any tile lands inside two zones at once, the zones overlap,
"interior" does not mean what this assumes, and the split falls back to
clipping everything rather than guessing — the same shape as your
existing fall-through when something cannot be done the fast way.

Worth knowing if you test this: **that fallback makes a widened
predicate INERT.** We aimed a mutation at `within` → `intersects` and
it changed nothing, because the duplicate `joinUID`s trip the guard and
the split declines. It only bites when both are broken together.

## How we carry it

Patch 6 in `tools/vendor_weavingspace.py`, which re-applies at every
re-vendor and names itself if the anchor moves. Proved by
`tools/probes/the_overlay_split_assigns_the_same_zones.py`. We would
rather not carry it.
