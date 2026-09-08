# The topology of a weave, and what its holes have to do with it

The Topology tab refuses every weave in the catalogue, which is more
than half of it. This note is the record of why, of the constructions
we tried, and of where the answer turned out to lie. It is written for
whoever picks the question up next, and it is organised roughly as the
investigation went rather than as a tidy result, because the wrong
turnings are most of what it has to teach.

The short version is in four parts. A thin weave can be given a
structure by treating the daylight between its strands as tiles, and
that works, but the structure so obtained belongs to the weave and to
our cutting of the holes together, and no amount of care about the
cutting recovers the one thing a weave is about. The second part is
that this was the wrong place to look: the rendered design is a
projection, and the over-and-under is exactly what a projection
discards. The third is that the two halves can be joined after all,
which we had thought was the open problem and which turns out to be
measurable: every drawn piece can be attributed to the strand it
belongs to, and the classes the geometry then falls into are the same
partition the code gives, at every strand width tried. The fourth
takes the three ways a weave's ground can be empty, which are not the
same kind of thing as each other, and says what an edit on a weave
would have to preserve to be the analogue of an edit on a tiling.

Every figure and every number below names the probe that produced it,
and each was re-run against the code as it stands rather than quoted
from an earlier session.

## What a weave is made of, and why that matters here

A weave in this library is not a tiling that has been thinned. Its
strands are generated from a grid: the code `ab-|cd` says which
elements ride in which of two directions, a hyphen marking a strand
deliberately left out, and the `aspect` gives each strand's width as a
fraction of the spacing between them. At an aspect of 1.0 the strands
meet and the plane is covered. Below it they do not, and the design has
holes by construction rather than by accident.

That construction is why several obvious repairs fail. A strand piece
at a low aspect is not a solid one shrunk: it is narrower across its
axis and *longer* along it, which is what keeps a ribbon continuous
where it passes under another. Nothing that uniformly shrinks a solid
weave reproduces a thin one.

## What "the topology of a tiling" is here, stated carefully

The word does a good deal of work in this project and it is worth
saying plainly what the library computes, because the weave question
cannot be posed precisely until we have. It is not a topology in the
mathematical sense. It is three things together.

There is an *incidence structure*: which tiles meet along which edges,
and which edges meet at which vertices. There is a *group*, the
symmetries of the periodic design, acting on that structure. And there
are the *orbits* of edges and vertices under that action, which is what
the library calls classes and what an edit is aimed at.

The third is the one that matters for editing, and it is the reason a
tiling edit is safe. Moving a whole edge class at once moves both sides
of every edge in it, so the tiles still fit; and because the class is
an orbit, the result has the symmetry the class was derived from. The
operation is defined on the structure rather than on any particular
edge, and it preserves the property the structure was built on. So the
question to put to a weave is not "what is its topology" but "what
plays each of those three parts", and the three answers need not come
from the same place.

## Why the tab refuses one

`Topology` requires a gap-free tiling. Its constructor lays a patch of
repeats, matches the corners of one tile against its neighbours, and
derives the orbits an edit is later aimed at. A design that does not
cover the plane has no such structure to derive, and the constructor
says so. A weave below aspect 1.0 therefore arrives already refused,
and the refusal is correct.

# Part one: constructions on the rendered design

## What we tried first

| Approach | Gap-free? | Same weave? | Notes |
|---|---|---|---|
| Build at aspect 1.0 | yes | no | the library fuses same-label pieces, and a twill's sixteen tiles become two |
| Build at aspect 0.999 | no | nearly | a millionth of a cell of gap still refuses; the constructor is not asking about size |
| Inset a solid weave | yes, but wrong | no | an inset shortens where thinning lengthens, about 40% wrong on a plain weave |
| Treat the holes as tiles | yes | yes | the strands are untouched, and the daylight becomes tiles beside them |

![A twill at aspect 0.75 beside the same twill at 1.0, where same-label pieces have fused into two tiles rather than sixteen. From tools/probes/the_topology_of_a_thin_weave.py.](images/holes-as-tiles/solid-is-a-different-design.png)

The first is worth being clear about, because it looks like the obvious
answer and because the reason it fails is deeper than the tile count.
Going solid does produce a tiling, but not of the same design: at an
aspect of 1.0 the assembly dissolves adjacent pieces that share a
label, so the sixteen strand tiles of `twill weave a|b` become two.
Worse, the tiles of a solid weave are the *visible portions* of
strands, and deciding which portion is visible is precisely what
consumes the over-and-under. A solid weave is a tiling of fragments
whose correspondence back to strands has been spent. It is not that
the design has changed a little; the object the structure should be
about is no longer in the picture.

The fourth is the one we followed. It leaves the strands untouched,
which is the property the others give up.

## Holes as tiles

The daylight is turned into polygons and handed to the constructor
beside the strands, so the design covers the plane and `Topology` will
take it. On `plain weave a|b` at any of four aspects the four strand
tiles plus nine filler tiles give a gap and an overlap of zero, ten
edge classes and seven vertex classes, and the edit round trip closes
(`tools/probes/the_topology_of_a_thin_weave.py`). This is what the
plugin does today and it works: it closes the round trip on
sixty-five weaves of seventy-seven.

![A twill at aspect 0.75: its strand tiles, the daylight alone, and the two together as a design that covers the plane. From tools/probes/the_topology_of_a_thin_weave.py.](images/holes-as-tiles/holes-become-tiles.png)

## Whose structure is it?

Here is the difficulty, and it is not a defect in the construction. The
classes that come back describe the weave *and our cutting of the
holes* together, and nothing in the result says which of the two a
given class is about.

The first sign of it is that they do not always hold still. The plain
weave's ten edge classes and seven vertex classes are the same at all
four aspects. The twill's are six and four at aspects 0.9, 0.75 and
0.5, and at 0.25 they are a hundred and twenty-two and eighty-one,
because its daylight falls into twenty-five pieces there rather than
sixteen (`tools/probes/the_topology_of_a_thin_weave.py`). Nothing about
the weave changed. The strand width changed, and with it the shape of
the ground left over, and the classes are partly about that ground.

![A twill filled and dualised across four aspects, from tools/probes/the_topology_of_a_thin_weave.py.](images/holes-as-tiles/twill-across-aspects.png)

## The control that settles it

The movement above is suggestive rather than conclusive: a sceptic
could say the design at aspect 0.25 is a different design. The way to
settle it is to hold the design still and change only the cutting, and
the ground here can be cut two ways without moving a single strand.

![The same twill at aspect 0.5, its daylight cut two ways. The ground is identical; the class structure is not. From tools/probes/the_topology_of_a_thin_weave.py.](images/holes-as-tiles/the-filling-decides.png)

Taking the pieces as the boolean difference happens to return them
gives sixteen filler tiles, six edge classes and four vertex classes.
Cutting each of those pieces in half gives twenty-two tiles, a hundred
and fourteen edge classes and seventy-six vertex classes. The strands
have not moved and the ground covered is identical
(`tools/probes/the_topology_of_a_thin_weave.py`). That settles it: the
filling decides the classes, so the classes are not the weave's, and no
amount of care about how the holes are cut changes what kind of thing
the answer is.

## Holes made of several kinds of tile

The obvious repair is to stop cutting arbitrarily. A hole in a thin
weave is not one thing: where a strand has been dropped, the band it
would have occupied and the ordinary aspect gaps flanking it are
different in kind and merely happen to touch. Two canonical cuts are
available, and neither has any freedom in it. The strands code names
the band a dropped strand left, so that cut comes from the
specification rather than from geometry. And the daylight a strand's
width opened divides by whose width opened it, which is a nearest-site
partition with every strand grown at the same rate
(`tools/probes/holes_made_of_typed_tiles.py`).

![A plain weave's daylight cut into typed tiles at four aspects, from tools/probes/holes_made_of_typed_tiles.py.](images/holes-as-tiles/typed-plain-weave-a_b.png)

## What to do with the kinds

Once every hole tile carries its kind, an edge of the resulting
structure can be asked what it lies between: two strands, a strand and
its own daylight, or a strand and a dropped strand's band. Two uses
suggested themselves and both were built.

The first contracts across the incidental daylight and refuses to
contract across a hyphen, which is the maintainer's own framing of what
a weave's structure ought to ignore
(`tools/probes/a_weave_topology_that_ignores_its_gaps.py`).

![A plain weave at four aspects with its strands joined across the daylight, from tools/probes/a_weave_topology_that_ignores_its_gaps.py.](images/holes-as-tiles/plain-contracted.png)

The second absorbs the incidental daylight into the strand it replaces,
so the filler disappears rather than being contracted over
(`tools/probes/absorbing_the_incidental_gaps.py`).

![A plain weave whose incidental daylight has been absorbed into the strands, at four aspects. From tools/probes/absorbing_the_incidental_gaps.py.](images/holes-as-tiles/absorbed-plain-weave-a_b.png)

## Attributing the daylight to what it replaces

Ownership needs a rule for whose daylight a piece is, and proximity is
the wrong one. At a crossing the ground was opened by two strands
retreating from it and belongs to neither more than the other; worse, a
nearest-strand rule divides a hole along its diagonals, so each piece
faces one strand and meets the others only at points.

The canonical rule asks what each piece replaces: which strand would
have covered that ground had the yarn been drawn at full width. It is
computed the way `daylight_by_kind` computes a conscious gap, by
building a second weave and comparing, and the reference is the same
weave at an aspect just below 1.0, since at 1.0 the assembly fuses
pieces that share a label and there would be nothing left to attribute
to.

Measured on three weaves at four aspects
(`tools/probes/what_the_daylight_replaces.py`), it attributes every
piece at aspects 0.9, 0.75 and 0.5, leaves two pieces of a twill and
one of `twill weave a|b-` unattributed at 0.25, and the absorbed
regions partition the ground at an overlap of zero throughout. The
relation kinds it yields are the same at every aspect: `a` alongside
`a` and `b` alongside `b`, `a` crossing `b`. Two questions are settled
by it.

A pair of strands running alongside one another stays adjacent. At full
width they would abut along a line, so they are neighbours, and the
worry was that carving each crossing hole among perpendicular pairs
would leave them sharing nothing. It does not.

And the diagonal is refused, without a rule written to refuse it. Two
absorbed regions at opposite corners of a hole meet at a point, and
adjacency here requires a shared segment rather than a shared point, so
no such pair is ever joined. Where those two strands genuinely cross
somewhere else, that crossing is where the relation is recorded.

## Does any of it stay the size a tiling's structure is?

A tiling's structure is small. `laves 3.3.4.3.4` has four tiles with
two edge classes and two vertex classes, `archimedean 4.8.8` two tiles
with two and one, `hex-slice 3` three tiles with one and two
(`tools/probes/does_a_weave_topology_stay_small.py`). Any account of a
weave has to be comparable, or the labels are counting the method
rather than the design, and an edit aimed at one of a hundred classes
is not aimed at anything a person can hold in mind.

The column below is `plain weave a|b`, since it is the one weave every
construction here survives, and each row names the probe it came from.

| Construction | on a plain weave | across aspects |
|---|---|---|
| a tiling, for scale (`laves 3.3.4.3.4`) | 2 edge, 2 vertex | not applicable |
| holes kept as tiles, cut as the difference gives them | 10 edge, 7 vertex | invariant here, moves on a twill |
| holes kept as tiles, cut by kind | 30 edge, 20 vertex | invariant |
| daylight absorbed, then classes taken | 11 edge, 7 vertex | invariant, and three weaves of four refuse the step |
| relations between strands | 1 alongside, 1 crossing | invariant |
| strand classes from the interlacement | 1 class of 4 strands | the aspect is not an input |

Typing the cut buys the invariance and costs the size: thirty edge
classes where the arbitrary cut gave ten, because every hole tile
brings its own edges, and a hundred and ninety-five on `twill weave
a|b` at aspect 0.9 (`tools/probes/holes_made_of_typed_tiles.py`).
Absorbing goes the other way and helps with the size, eleven and seven,
stable at every aspect; but an absorbed strand is its own rectangle
together with the ground it claimed, so it has a complicated outline
and each extra corner is another class, and only the plain weave
survives the construction at all.

The last two rows are the ones that behave, and on reflection that is
the right comparison rather than a lucky one. A tiling's edge classes
are relations between tiles, so a weave's structure should be relations
between strands, and that stays small precisely because it does not
inherit the polygons' corners.

## The over and under will not come out of the geometry

A relation that says two strands meet, without saying which passes
over, has dropped the thing a weave is for. We tried to read that off
the shapes three ways, and none of them works.

The first asked for direct contact, on the reading that the under
strand is cut flush against the over strand's edge. It is not: a plain
weave has no contacts at all between its thin pieces, at any aspect,
the cut being set back across the daylight.

The second asked whose claimed ground reaches the other strand's own
edge, on the reading that the over strand covers the crossing at full
width and is handed that ground by the replacement attribution
(`tools/probes/over_and_under_in_the_strand_relations.py`). On a plain
weave it classifies nothing at all, leaving five relations of five
unclassified at every aspect. On a twill it classifies some and the
answer moves with the strand width: five crossings named at aspect 0.9,
twelve at 0.75, and none at either 0.5 or 0.25. A relation that appears
and disappears as a drawing parameter changes is not a relation of the
design.

The third asked whether a strand meets its neighbour end-on or side-on,
which does not require them to touch. Every relation lands in the
ambiguous band.

# Part two: the weave as an interlacement

## What the projection loses, and it loses two things

The three failures above have one cause, and stating it plainly
invalidates the whole of part one as a route to this particular
question. The rendered design is a *projection*, and it discards two
things rather than one.

It discards the third dimension, so which ribbon lies on which is gone.
And because a flat map cannot show one ribbon over another, it *cuts*
the ribbon passing beneath, so a strand is not a connected object in
the picture at all: what the drawing holds is pieces. The projection
therefore loses both the relation and the things the relation is
between, which is why no cutting of the holes recovers it. We were
measuring a shadow for a fact it does not carry, and doing so with the
objects already broken up.

![On the left, the weave as it is: continuous ribbons that cross, where the break in a ribbon means it passes beneath. On the right, the same thing as a flat map can hold it, where the break has become a cut edge of a polygon and no longer says why it is there. From tools/probes/the_weave_as_an_interlacement.py.](images/holes-as-tiles/what-the-projection-loses.png)

## The model, which is one layer below the geometry

In the conceptual model the strands are continuous and really do pass
over and under one another. That model survives in the library's
`Loom`, whose `indices` are the crossing sites and whose `orderings`
give the layer order at each, and none of it depends on the strand
width, the inset, or how a hole was cut, because no polygon has been
drawn yet.

What we build from it is a model rather than a reading of the library's
output. A strand is a whole ribbon, named by its letter and direction,
continuous even where the drawing cuts it. A crossing carries which
strand rides over. A float is a run of crossings a strand rides over
without dipping, which is what a weaver means by the structure of a
cloth. A dropped strand is absent from the model rather than being a
hole in it, since the code says it was never threaded.

![The interlacement of three families, read from the code: a filled cell is a crossing the warp rides over. From tools/probes/the_weave_as_an_interlacement.py.](images/holes-as-tiles/the-interlacement-of-three-families.png)

## What it gives

Measured by `tools/probes/the_weave_as_an_interlacement.py`, against
the tilings above for scale.

A code's two halves are its warp and its weft, and they are written
here as a pair because a pipe would end a table cell.

| Weave | loom | strands | classes | pattern | float | phase steps |
|---|---|---|---|---|---|---|
| plain weave, `a` and `b` | 2 by 2 | 4 | 1 | `UO` | 1 | (1) both ways |
| twill weave, `a` and `b` | 4 by 4 | 8 | 1 | `UUOO` | 2 | (3, 3, 3) both ways |
| twill weave, `ab` and `cd` | 4 by 4 | 8 | 1 | `UUOO` | 2 | (3, 3, 3) both ways |
| basket weave, `ab` and `cd` | 4 by 4 | 8 | 1 | `UUOO` | 2 | (0, 2, 0) both ways |
| twill weave, `a` and `b-` | 4 by 4 | 6 | 2 | `UO` and `UUOO` | 1 and 2 | (2) and (1, 0, 1) |
| plain weave, `ab-` and `cd-` | 6 by 6 | 8 | 1 | `UO` | 1 | (1, 0, 1, 0, 1) both ways |

One strand class for a plain weave and one for a twill, against two
edge classes for `laves 3.3.4.3.4`. The labels are fewer than a
tiling's, and they are the interlacement itself rather than an artefact
of measurement. Nothing here can move with the aspect, because the
aspect is not among the inputs.

The per-strand sequence alone is not enough, and the table says why. A
twill and a basket both ride over two and under two, so both read
`UUOO`, and anybody can tell them apart by eye. What separates them is
the phase between neighbouring strands: a twill steps by a constant
amount, which is what draws its diagonal, and a basket repeats in
blocks. With that second reading the three biaxial families are
distinct.

The dropped strand behaves as one would want without a rule written for
it. `twill weave a|b-` has six strands rather than eight, the missing
one absent rather than hollow, and its neighbours' floats lengthen,
which is what happens in cloth when a strand is left out. Note also
that its two directions differ, `(2)` one way against `(1, 0, 1)` the
other, which is right: dropping a strand from one direction is not
symmetric.

## What these invariants do and do not settle

Three limits, because the table above reads as more conclusive than it
is.

The float and the phase together separate the biaxial families we
measured. They are not shown to be *complete* invariants, and we have
no argument that two genuinely different weaves must differ in one of
them. Anything built on this should treat them as a discriminator that
has worked so far rather than as a normal form.

The phase is well defined only up to a strand's own period. Our reading
takes the first cyclic shift that carries one strand's sequence onto
its neighbour's, and where a sequence repeats within its own length
several shifts do, so the number reported is the smallest rather than
the only one. For `UUOO` in a four-cell repeat the shift is unique and
the readings above are safe; for a longer or more repetitive pattern
the convention would have to be stated.

And triaxial weaves are not measured here at all. Every family but
`cube` is biaxial, and a triaxial crossing involves three strands
rather than two, so "which one rides over" is an ordering rather than a
choice and the float-and-phase pair may simply be the wrong shape of
answer. The cube weaves also refuse the geometric construction of part
one for a separate and diagnosed reason
(`tools/probes/why_a_cube_weave_refuses_a_topology.py`).

# Part three: the join between the model and the drawing

The interlacement says what a weave is and carries no geometry. An edit
moves geometry. The obvious objection to the whole of part two is
therefore that it answers a different question from the one the
Topology tab asks, and the previous draft of this note conceded the
point and left the join as the open problem.

It is not open. The two sides can be matched, and the match is worth
making as a *differential*, which is the shape that has found most of
this project's real defects: two independent descriptions of one thing,
compared, so that a disagreement is a defect by construction rather
than a judgement. `tools/probes/the_join_between_a_weave_and_its_drawing.py` builds both sides and compares them. The loom side knows
nothing of the aspect; the geometry side knows nothing of over and
under.

## Every drawn piece is a float

The observation the join rests on is the one part two arrived at
sideways. A flat drawing cuts a strand wherever it passes beneath, so
what survives of a strand in the picture is exactly its *floats*, the
maximal runs of crossings it rides over. Piece and float are the same
thing seen from two sides.

That makes the attribution computable from the geometry alone, with no
appeal to the code. A drawn piece measures one strand width across and
something longer along, so the direction it runs in is the axis whose
extent equals `aspect * spacing`; the line its centre sits on says
which strand of that direction it belongs to; and its length along its
own axis is the float it draws. Nothing there is a heuristic, and the
one coincidence that could spoil it is declared rather than guessed
past: at an aspect of exactly 0.5 a float of one is as long as it is
wide, and eight of a twill's sixteen pieces measure a strand width both
ways. Those are settled by the strand lines the unambiguous pieces have
already drawn, which is information in hand rather than an assumption.

## What the differential says

Five weaves at four aspects, twenty rows, and every row agrees.

| Weave | tiles | strands drawn | strands threaded | floats | pieces per strand | classes from the code | classes from the drawing |
|---|---|---|---|---|---|---|---|
| plain weave, `a` and `b` | 4 | 4 | 4 | 4 | 1 | 1, sizes [4] | 1, sizes [4] |
| twill weave, `a` and `b` | 16 | 8 | 8 | 8 | 2 | 1, sizes [8] | 1, sizes [8] |
| basket weave, `ab` and `cd` | 16 | 8 | 8 | 8 | 2 | 1, sizes [8] | 1, sizes [8] |
| twill weave, `a` and `b-` | 8 | 6 | 6 | 6 | 1 and 2 | 2, sizes [4, 2] | 2, sizes [4, 2] |
| plain weave, `ab-` and `cd-` | 16 | 8 | 8 | 8 | 2 | 1, sizes [8] | 1, sizes [8] |

Every drawn piece is attributed to exactly one strand, at every aspect,
on every weave: no piece is left over and none is claimed twice. The
number of strands the drawing shows is the number the code threads,
which is the first thing that could have failed and did not. And the
partition of strands into classes has the same shape read either way.

![Twill weave a|b- read from both sides: the loom's crossings tinted by the class of the strand riding over each, beside the drawing at two strand widths with each piece tinted by the class of the strand it was attributed to. Each side is coloured by its own classes, since nothing here establishes that loom row zero is the leftmost line; what is measured is that the two partitions have the same shape. From tools/probes/the_join_between_a_weave_and_its_drawing.py.](images/holes-as-tiles/the-join-between-code-and-drawing.png)

Two cautions about what that table does and does not establish. The
comparison is of the partitions' *shapes*, the number of classes and
their sizes, rather than of their memberships: the two sides name their
strands differently, the loom by row and column and the geometry by
which line a piece sits on, and nothing here shows that loom row zero
is the leftmost line. A disagreement in shape would be a disagreement
whatever the naming, which is what makes the test worth running; an
agreement in shape is weaker than an agreement in membership, and
establishing the membership is the obvious next measurement. And five
weaves is five weaves. It is the biaxial families in the catalogue,
with and without a dropped strand, and it is not the whole catalogue.

## The classes do not move with the strand width

The drawing's own partition is invariant across the four aspects on
every weave tried. This is the property that all of part one lacked and
the reason the join matters: the classes read off the geometry now
behave like the classes read off the code, because they are the same
classes arrived at from the other end.

## The room a strand has, which is exactly the daylight

The same probe measures the clear air between neighbouring strands of
one direction, centre to centre less one strand width. It comes back as
0.100, 0.250, 0.500 and 0.750 of the spacing at aspects 0.9, 0.75, 0.5
and 0.25, on all five weaves: exactly one minus the aspect, which is
what it should be and is worth having measured rather than assumed.

That number is the ceiling on how far a strand may be moved across its
own direction before it meets its neighbour. It is a function of the
strand width and of nothing else, which has a consequence for how an
edit is recorded, taken up in part four.

# Part four: three absences, and what an operation must preserve

## Three absences that look alike

A thin weave's drawing is mostly empty ground, and nothing in the
picture says why any particular piece of it is empty. Three mechanisms
open it, and separating them settles most of what a weave's structure
ought to ignore.

![One plain weave carrying all three at once: the inset ring, the aspect daylight, and the bands two dropped strands left. From tools/probes/three_kinds_of_absence.py.](images/holes-as-tiles/three-kinds-of-absence.png)

On `plain weave ab-|cd-` at aspect 0.6 with a tile inset of a tenth of
the spacing, the inset ring is 0.22 of the ground the design would
occupy at full width, the aspect daylight 0.16 and the dropped strands'
bands 0.27 (`tools/probes/three_kinds_of_absence.py`). Three quantities
of the same order, three mechanisms of quite different standing, and
nothing in the drawing to tell them apart.

## Where each one enters, which is what decides its treatment

The useful question is not what each absence looks like but where in
the making of the design it enters, because the structure is a function
of what has happened by the time it is taken.

An **inset** is applied to the finished unit. It is the last step of
the chain that builds a design, every step before it preserves the
tiling, and the un-inset design is one call back. Nothing about an
inset is a fact about the weave, so the treatment it wants is not a
rule for reasoning about it but a decision not to apply it yet, which
is what the rulings for tilings already say. It is worth adding that a
weave takes an inset the same way a tiling does: the figure above is a
`WeaveUnit` with `inset_tiles` applied after the fact, so the boundary
that keeps weaves out of the inset work is about the *aspect* rather
than about insets as such.

An **aspect** looks as though it enters earlier, since it is an
argument to the same call that builds the unit. It is not. The loom is
computed from the strands code, the weave type and the over-and-under
alone; the aspect enters when polygons are drawn from it. So the strand
width is a parameter of the *drawing* rather than of the design, and
this is not an argument from the shape of the code but a measurement:
the classes read off the geometry are the same at every aspect tried
(part three), and the classes read off the loom cannot move with the
aspect because the aspect is not one of its inputs.

A **dropped strand** is a hyphen somebody typed. It changes the code,
so it changes the loom, so it changes the structure, and the change is
visible in the plainest way: `twill weave a|b` has one strand class and
`twill weave a|b-` has two. It is also not a hole at all. Nothing was
threaded there, and what shows in the cloth is that its neighbours
float further, which is what a weaver would say about it.

So the criterion falls out, and it is exactly the one the question was
put in terms of: **the only absence that appears in the structure is
the one that enters before the structure is taken.** No veto rule on an
adjacency graph is needed to get there, and none of the ones we wrote
worked. What settles it is choosing where to read the structure from.

## What each candidate structure does with them

Three notions have appeared in this note, and they are worth naming,
because "the topology of a weave" has been doing duty for all three.

The first is the **filled tiling's classes**: the daylight is made into
tiles, the library derives edge and vertex classes over the result, and
an edit is aimed at one of them. This is what the plugin does today.
The second is the **strand adjacency structure**: strands are the
things, the relations between them are alongside and crossing, and the
daylight is attributed to whichever strand it replaces. The third is
the **interlacement**: strands are continuous ribbons, a crossing
carries which of the two rides over, and no polygon has been drawn.

| | inset | aspect | dropped strand |
|---|---|---|---|
| Filled tiling's classes | invisible, where the structure is built before the inset | filled, and every filler tile brings its own edges | not filled, because the code says it was never threaded |
| Strand adjacency | invisible, same reason | absorbed into the strand it replaces | absent, and the neighbours are simply not adjacent |
| Interlacement | not an input | not an input | a strand that does not exist |

Reading down the columns is more instructive than reading across. Two
of the three absences are handled, in every treatment that works, by
knowing something the picture does not contain: where in the chain the
inset was applied, and what a hyphen in the code means. The one we
attacked geometrically is aspect, and it is the one that defeated every
geometric rule we wrote, until part two removed it from the question by
not measuring polygons at all.

## Operations, and why a weave's cannot be invariant in a tiling's sense

An operation on a tiling is aimed at an orbit of edges or vertices and
applied to every member at once, and two things make it safe: the
result is still a tiling, and the operation is defined on the structure
rather than on any individual edge, so it commutes with the symmetry
the classes came from. Coverage is what is preserved; the orbit is the
unit of aim.

Neither carries over. Coverage was never true of a weave below an
aspect of 1.0, so it cannot be what an edit preserves, and an edge
class of a filled tiling is not a stable name to aim at, since the same
weave at a different strand width returns a different number of them.
What a weave has in place of coverage is its interlacement, which gives
the condition directly: **an operation on a weave is admissible when
the interlacement is unchanged**, the same strands crossing the same
partners in the same order with the same floats.

![A schematic. Nudging a strand leaves every crossing the crossing it was, so the cloth is the same cloth drawn differently; carrying it past its neighbour takes its over-and-under with it, and what comes out is a different cloth rather than a moved one. From tools/probes/three_kinds_of_absence.py.](images/holes-as-tiles/what-an-edit-must-preserve.png)

That is a condition one can check, and it is the condition we had
already arrived at empirically without seeing it for what it was: an
edit survives provided a strand does not move across a crossing. The
geometry may be pushed about freely so long as no strand changes its
place in the order, because the over and under is settled when the
pieces are built and travels with them.

The unit of aim changes as well. An edit on a tiling is aimed at an
edge class; an edit on a weave is aimed at a strand, and moves that
strand's two long edges in phase, since a ribbon of constant width is
what reads as yarn. What it can be aimed at collectively is therefore a
*class of strands*, and part three is what makes that a usable
instruction rather than a wish: the classes are few, they can be read
off the drawing as well as off the code, and they do not move with the
strand width.

## Three consequences worth writing down

**The record names a strand, never an edge class.** An edit must not be
recorded against a label that moves with a drawing parameter, and the
filled tiling's labels do. A weave edit that is to survive a change of
strand width has to name a strand or a strand class.

**The clamp is a function of the aspect and the edit is not.** Part
three measures the room a strand has as exactly one minus the aspect,
so the same displacement is legal at 0.25 and refused at 0.9. This is
the shape of a rule this project already holds for the zigzag: hold
what was asked and clamp on the way to the screen, rather than writing
the clamp back into the record, where it would ratchet and never give
the value back when the design regained room.

**A hyphen is a change of design, not of appearance.** Dropping a
strand changes the set of strands and so changes the alphabet an edit
was aimed at, which is the case the existing rule about a shelf key
already covers: the replay applies what matches and reports which edits
now point at a changed design. Typing a hyphen ought to report as one.

## What is not an operation of this kind

It clarifies the boundary to say what falls outside it. Changing which
strand rides over, re-phasing one family against the other, and
dropping or adding a strand all change the interlacement, which is to
say they make a different cloth. They belong with the strands code and
the over-and-under box, where somebody is composing a design, rather
than with the handles on the Topology tab, where somebody is moving one
they have.

# Part five: where this leaves us

## Which structure, for which question

The question "what is the topology of a weave" has three answers here
and they are not competitors, because they answer different things.

For what a weave *is*, the interlacement. It is small, it comes from
the specification rather than from a measurement, and it holds the one
thing a weave is about. If somebody asks how many classes a weave has,
this is the number to give them.

For *where each strand lies*, the geometry, addressed through the join
of part three. This is what an edit needs, and it is now derivable
rather than merely wished for.

The filled tiling's classes are neither. They are an implementation
device that lets a library which insists on a gap-free tiling accept a
design that is not one, and they work as such: sixty-five weaves of
seventy-seven close the round trip. What they should not do is appear
in front of a user as the weave's own structure, because they are not.

## What is built, and what is only measured

Built and committed: the interlacement model, the typed cutting of the
daylight, the attribution of daylight to what it replaces, and the join
between the code and the drawing, each with its probe under
`tools/probes/`.

Measured but not built: everything in part four about operations. The
admissibility condition is stated and its ingredients exist, and
nothing yet enforces it. Making an edit aim at a strand class is a
change to the Topology tab and is the maintainer's to schedule.

Not measured at all: the membership half of the join, triaxial weaves,
and any weave outside the five in part three's table.

## Two smaller things that are unfinished

The absorbing construction of part one works on one weave of the four
tried. `plain weave a|b` comes down to eleven edge classes and seven
vertex classes, stable at every aspect; the twill, the basket and
`twill weave a|b-` all refuse inside the library's own bookkeeping at
every aspect, and the last of the three does not even tile exactly,
carrying an overlap of about 0.19 of a cell at aspect 0.9
(`tools/probes/does_a_weave_topology_stay_small.py`). We had recorded
this as one failure out of four and it is three, which is worth
correcting because the construction reads much better on one line of a
table than it deserves.

And past twenty-six classes the library issues two-letter labels, `aa`
after `z`, while our own helper returns the labels joined into one
string, which cannot be split back once any of them is two characters.
A thin twill at aspect 0.25 is already past that, so anything built on
the filled tiling has to treat a class as a label rather than as a
character.

## The thing that would make most of this unnecessary

Behind all of it sits the observation that a strand is more naturally a
path than a row of tiles. Were the grid a weave rides on to carry the
undulation, the strand would keep its width, nothing would need filling
or absorbing at any aspect, and most of the choices in this note would
not have to be made. The interlacement would then be the design rather
than a model recovered beside it, and the join of part three would be a
construction rather than a measurement. That is upstream's territory as
much as ours, and we would be glad to be shown that the question has a
tidier answer than the one we have reached.
