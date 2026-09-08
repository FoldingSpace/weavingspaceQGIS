# How this plugin was actually tested

These are working records, kept because the reasoning in them is
worth more than the conclusions. They are not tidy, and several of
them are mostly accounts of being wrong.

**The three test campaigns** each set out to find defects in an area
nobody had tested, and each says what it looked for, what it found
and what it did not. The third is the most useful to read first: by
then the method had settled, and the ratio of tests written to
defects found is a fair picture of what this kind of work returns.

**The perceptual colour findings** measure how separable the default
element colours actually are, in a colourspace that models human
vision rather than in RGB. The uncomfortable result — most gallery
maps have element fills closer than a distance a reader can reliably
tell apart — is why the colour editor exists.

**Round six's briefs and logs** sit in `hunt-logs-2026-09-01/`, ten
hunts against the Topology tab's rebuild, the re-vendor and the save.
Read them beside the 2026-08-13 set for the same ratio, and for two
things that set does not show: what a BRIEF looks like when it names
what its siblings cover, and what a round looks like when four of its
ten hunts keep no running record at all.

**The hunt record** (HUNT-RECORD.md) is the newest of these and the
one to read if you are about to look for defects: which directions
have paid, which came back empty, how to run and watch a hunt, and
how the method compares with the suite, mutation testing and the
sweep. The raw check-in logs from the twelve hunts of 2026-08-13 sit
beside it in `hunt-logs-2026-08-13/`, kept for the ratio of ruled-out
to confirmed rather than for the prose, and including the two hunts
that recorded their own sloppiness about timestamps.

**The newest upstream note**,
`upstream-note-a-cleaned-polygon-may-be-multi-part.md`, reports two
lines of one method disagreeing about what a shape can be:
`get_clean_polygon` ends in `set_precision`, which may split a polygon
that pinches at the grid's scale, and `get_corners` asks the result for
`.exterior`. The measurement worth reading is the control rather than
the failure — the same tile cleans to a Polygon where it sits and to a
MultiPolygon in two of its seven translated copies, so what decides it
is the lattice offset rather than the tile.

**The note before it**,
`upstream-note-an-edge-is-deleted-while-a-tile-still-names-it.md`,
reports a `Topology` construction that deletes an edge from its own
dict while a tile goes on naming it, so `get_edges` raises `KeyError`.
It is worth reading beside the weave note above for what it took to
believe: two hypotheses of ours were refuted by their own controls
first, and the run that finally showed it observed the dict rather
than replacing any logic.

**The second upstream note**, `upstream-note-a-unit-from-supplied-
tiles.md`, asks the weavingspace project for a constructor that builds
a Tileable from tiles you already have. The plugin needs one to tile a
map with a design's DUAL, and works around its absence by replacing a
copied unit's tiles from outside the library -- which works (181 tiles
over a 3km region for laves 3.3.4.3.4, 84 for archimedean 4.8.8) and
leans on four private lines. A canary in the suite asserts the gap is
still there, so the day it closes we are told.

**Editing a weave's structure** (`weaving-and-topology.md`) asks
whether the Topology tab's refusal of every weave is a fact about
weaves or an artefact of how they are built. Four routes were tried
and three failed, each for a reason worth keeping; the fourth, the
maintainer's own, closes the round trip on one weave of three. It is
also the clearest example in these records of the difference between
what a library CAN be made to do and what would be in the spirit of
the thing it models, which is the question that reshaped the
investigation halfway through.

**Two studies of 2026-09-05**, `study-tiling-and-layer-data-2026-09-05.md`
and `study-dialog-complexity-2026-09-05.md`, answer the maintainer's
questions about whether the data behind a map and the dialog that
drives it could be structured with fewer defects. Each names candidates
with a measurement, says what is not recommended, and writes no code;
they are the argument a later refactor has to start from.

**The upstream note** reports a rendering difference to the
weavingspace project, and opens by retracting an earlier note that
blamed one of their commits. It is kept in full, retraction first,
because a project that publishes only its correct diagnoses is
publishing a fiction. The divergence was eventually found to be in
our own comparison harness, not in the library and not in the plugin.

What is deliberately NOT here: one-shot scripts, scratch files, and
the rolling session handover. Those are working files rather than
records, and publishing them would bury these.

The durable rules these campaigns produced live elsewhere and are
binding rather than historical: `docs/TESTING.md` for the test
shapes and the lessons each cost, `docs/MUTATION-TESTING.md` for what
the mutation score means and what is promised about it, and
`docs/MUTATION-LOOP.md` for running a campaign from scratch.
