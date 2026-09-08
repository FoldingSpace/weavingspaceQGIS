# An edge is deleted from `Topology.edges` while a tile still names it

A note for the weavingspace project, in the same spirit as the four
beside it: a small, reproducible inconsistency, with the measurement
that found it and no request attached beyond "is this what you
intend?".

## What happens

`Topology.__init__` raises `KeyError` from `Tile.get_edges`:

    File "weavingspace/topology.py", line 1606, in get_edges
      return [self.topology.edges[ij] for ij in self.edges]
    KeyError: (241, 238)

`get_edges` looks each of a tile's own edge ids up in the topology's
`edges` dict, and one of them is not there.

## What was measured, rather than read

The `edges` dict was replaced with a `dict` subclass that records its
deletions and changes nothing else, so the construction ran exactly as
it does normally. At the failure:

    missing edge key                     (241, 238)
    edges deleted during construction    21
    was the missing key deleted?         yes
    was its reverse deleted?             no
    is its reverse still present?        no
    tiles still naming the deleted edge  tile 92

So this is not a direction convention -- neither orientation of the
edge survives. The edge is deleted from the topology's dict, and a
tile that is not the one the deletion was performed on goes on
listing it.

## Where it appears to come from

`_match_reference_tile_corners` merges edges at a vertex and then
removes the old ones:

    old_edges, new_edge = self.tiles[v.tiles[0]].merge_edges_at_vertex(v.ID)
    for e in old_edges:
      del self.edges[e]
    self.edges[new_edge.ID] = new_edge

The merge is performed on `v.tiles[0]` alone, while the comment on the
line above notes that such a vertex "will have no more than 2
v.tiles". Where there are two, the second tile's own `edges` list is
never updated, so it keeps naming an edge the dict no longer holds.

`_match_reference_tile_vertices` has the same shape a few lines up,
deleting `old_edge` after `insert_vertex_at` on one tile.

THIS IS A READING OF THE SOURCE and is offered as such. What is
measured is the paragraph above it.

## A second failure lands in that same method, by another route

Added after the note was first written, because it bears on the
reading above rather than on the measurement. A DIFFERENT design --
a triaxial `cube weave abc|def|ghi`, scaffolded the same way, 114
tiles and a patch of 798, every shape single-part -- fails inside the
very method the paragraph above suspects:

    _copy_base_tiles_to_patch -> _match_reference_tile_vertices
      -> Tile.insert_vertex_at
           old_edge = self.get_edges()[i - 1]
    IndexError: list index out of range

`get_edges` is the same accessor that raises `KeyError` in the
measurement at the top of this note, and here it returns a list
shorter than the index asked of it. We have NOT established that the
two are one defect, and we are not claiming it; what we can say is
that a source reading which named `_match_reference_tile_vertices` on
suspicion was followed by an independent failure inside it.

The two designs differ in a way that may matter to you: gridifying the
filler changes nothing for the twills below, and for this cube weave
it is what gets the design as far as this failure at all.

## How to reproduce

The designs that show it here are weaves whose gaps have been filled
with extra tiles so that the unit is gap-free -- our own scaffolding,
described in `docs/process/weaving-and-topology.md` -- rather than
anything from the catalogue. The catalogue's own designs build
perfectly well, so this needs supplied geometry to reach.

    twill weave a|b- 1,2     9 strand tiles + 12 filler
    twill weave a|b- 3      18 + 24
    twill weave a|b 1,2,2,1 36 + 36
    twill weave a|b 4       64 + 64

Ten designs of seventy-seven fail this way; sixty-five build, edit and
round-trip cleanly. The probe is
`tools/probes/can_a_weave_carry_a_topology.py`.

## Why it may still be worth fixing

A `Topology` built from supplied geometry is exactly what a caller
does who wants to complete a design before analysing it, and it is how
this plugin reaches the dual as well (see
`upstream-note-a-unit-from-supplied-tiles.md`). A tile list and an
edge dict that disagree fail late, inside construction, with an error
that names neither the tile nor the design.

## What we are NOT claiming

That the geometry we hand in is above suspicion. Two hypotheses of
ours were refuted on the way -- T-junctions, which the designs that
BUILD have too (45 of them in one), and coordinate precision, where
gridifying the filler changed nothing and there are no near-duplicate
vertices at all. What the instrumented run shows is only what it
shows: an edge deleted, and a tile still naming it.
