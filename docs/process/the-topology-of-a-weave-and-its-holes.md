# The topology of a weave, and what its holes have to do with it

The Topology tab refuses every weave in the catalogue, which is more
than half of it. This note is the record of why, of the constructions
we tried, and of what we now think a weave's structure ought to be
computed from. It is written for whoever picks the question up next.
docs/TOPOLOGY.md points here rather than carrying the argument.

The short version has three parts. A thin weave can be given a
structure by treating the daylight between its strands as tiles, and
that works. The structure you get that way belongs to the weave and to
your cutting of the holes together, which we can demonstrate rather
than merely worry about. And the way out is to stop treating the holes
as one thing: cut them by what each piece is *for*, and then decide
what to do with each kind, at which point most of the difficulty
dissolves.

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

## Why the tab refuses one

`Topology` requires a gap-free tiling. Its constructor lays a patch of
repeats, matches the corners of one tile against its neighbours, and
derives the transitivity classes of edges and vertices that an edit is
later aimed at. A design that does not cover the plane has no such
structure to derive, and the constructor says so. A weave below aspect
1.0 therefore arrives already refused, and the refusal is correct.

## What we tried first

| Approach | Gap-free? | Same weave? | Notes |
|---|---|---|---|
| Build at aspect 1.0 | yes | no | the library fuses same-label pieces; a twill's sixteen tiles become two |
| Build at aspect 0.999 | no | nearly | a millionth of a cell of gap still refuses; the constructor is not asking about size |
| Inset a solid weave | yes, but wrong | no | an inset shortens where thinning lengthens, about 40% wrong on a plain weave |
| Treat the holes as tiles | yes | yes | the strands are untouched; the daylight becomes tiles beside them |

![A twill at aspect 0.75 beside the same twill at 1.0, where same-label pieces have fused into two tiles rather than sixteen.](images/holes-as-tiles/solid-is-a-different-design.png)

The first is the one to be clear about, because it looks like the
obvious answer. Going solid does produce a tiling, but not of the same
design: at an aspect of 1.0 the assembly dissolves adjacent pieces that
share a label, so the sixteen strand tiles of `twill weave a|b` become
two, and the structure derived from them is the structure of something
else. The over-and-under pattern that makes a weave a weave has gone.

## Holes as tiles

The route that works is to give the daylight to the design. We take the
uncovered ground of one fundamental cell, cut it into single-part
pieces, give each piece its own tile id, and hand the library a unit
whose tiles are the strands together with those pieces. The result
covers its cell exactly, `Topology` accepts it, an edit can be applied,
and dropping the filler afterwards leaves the original strand tiles
valid. It closes the round trip on sixty-five of the catalogue's
seventy-seven weaves.

![A twill at aspect 0.75: its sixteen strand tiles with the holes between them, the daylight alone as sixteen pieces, and the two together as a thirty-two tile design that covers the plane.](images/holes-as-tiles/holes-become-tiles.png)

Two details are load-bearing and neither is obvious. Every filler piece
needs its own id, because the library's regularising step dissolves
tiles by `tile_id`, and pieces sharing one merge into a multi-part tile
whose corners it then cannot take. And each piece is snapped to the
library's own precision before being handed over, since a piece that
pinches at that precision is split by `set_precision` inside the
library's own cleaner, and the multi-part result reaches a function
that asks it for its exterior ring.

## Whose structure is it?

If we invent the holes, the classes an edit is aimed at may be a fact
about our invention. The obvious test is invariance: holding a weave
fixed and varying its strand width changes every coordinate and none of
its combinatorics, so a structure that moves with the aspect belongs to
the filling.

On `plain weave a|b` it does not move. At every aspect from 0.9 down to
0.25 the filled design has four strand tiles and nine filler pieces,
covers its cell exactly, and carries ten edge classes and seven vertex
classes with a dual of twenty-five tiles.

![A twill filled and dualised at four aspects. It is invariant at 0.9, 0.75 and 0.5, and at 0.25 the daylight falls into twenty-five pieces rather than sixteen and the classes multiply.](images/holes-as-tiles/twill-across-aspects.png)

On `twill weave a|b` it holds and then breaks. At 0.9, 0.75 and 0.5 the
design is sixteen strands and sixteen filler pieces with six edge
classes, four vertex classes and a sixty-four tile dual. At 0.25 the
same weave's daylight falls into twenty-five pieces instead of sixteen,
the six and four become a hundred and twenty-two and eighty-one, and
the dual grows to eighty-one tiles. The break is not slivers: at 0.5
the sixteen pieces are congruent, every one of area 250,000 square
units, while at 0.25 the twenty-five take seven distinct areas from
15,625 to 562,500.

## The control that settles it

Invariance over a range is suggestive rather than decisive, so we
tested it directly: fill the same holes, on the same weave at the same
aspect, two different ways. Cutting each filler piece in half across
its own middle is not a better filling and is not meant to be. It
covers exactly the same ground.

![The same twill at aspect 0.5, its daylight cut two ways. The ground is identical; the class structure is not.](images/holes-as-tiles/the-filling-decides.png)

Both leave a gap and an overlap of zero and both leave the strands
untouched. Taken as the difference gives them, the sixteen pieces yield
six edge classes and four vertex classes. Halved, the twenty-two pieces
yield 114 edge classes and 76 vertex classes.

So the classes are a property of the weave together with a
decomposition of its holes that we chose, and a different choice
covering the same ground gives a wholly different answer. What the
invariance of the previous section records is that the difference
operation happens to return congruent pieces over part of the range,
which is a fact about our construction rather than about weaving.

## Holes made of several kinds of tile

The way out is not a better arbitrary cut but a principled one, and it
comes from noticing that a hole need not be of one kind. In a weave
whose code drops a strand, a single connected hole is the missing
strand's own band together with the ordinary daylight flanking it.
Those are different things that happen to touch, and cutting them apart
is not a choice but a reading of what the design says.

`topology_edits.daylight_by_kind` already separates the two, by
building the same weave with each hyphen replaced by an unused letter
and taking the ground the ghost carries and the real design does not.
The aspect daylight then divides again, by which strand's width opened
it. Both cuts come from the weave's own construction rather than from
where a boolean operation chose to split.

![A plain weave's daylight cut into typed tiles at four aspects: the strands in blue, the aspect tiles in grey. The class structure is identical at every width.](images/holes-as-tiles/typed-plain-weave-a_b.png)

Measured, the canonical cut behaves as one would hope. `plain weave
a|b` becomes four strands and sixteen aspect tiles, covering exactly,
with thirty edge classes and twenty vertex classes at every aspect from
0.9 to 0.25. `twill weave a|b` becomes sixteen strands and forty-nine
aspect tiles with 195 edge classes and 130 vertex classes, unmoved at
0.9, 0.75 and 0.5. The dependence that the arbitrary cut introduced is
gone.

What the typed cut does not do by itself is give a small answer.
Thirty edge classes for a weave of four strands is mostly an account of
the daylight, and it is the strands somebody wants to edit.

## What to do with the kinds, and the choice that matters

Once each hole tile carries what it is for, the constructions we had
been treating as rivals turn out to be settings of one machine: keep
every kind and you have the typed tiling, and treat the aspect kind as
not-really-there and you have something smaller. The interesting
question is what "not really there" should mean, and there are two
readings, which do not agree.

**Passing through.** Let a path run through aspect tiles, so two
strands separated only by daylight count as neighbours. This is
decomposition-free by construction, since it depends on the daylight as
a region rather than on any cutting of it, and it is invariant across
aspect: a twill reads sixteen strands and thirty-five adjacent pairs
with the same degree sequence at every width, including the 0.25 that
broke the filled construction.

![A plain weave at four aspects with its strands joined across the daylight, drawn as links between strand centres.](images/holes-as-tiles/plain-contracted.png)

Yet it is too generous, and the reason is worth stating because it is
not obvious from the pictures. The daylight of a weave is largely one
connected region, so a path may enter it beside one strand and leave it
beside any other. Counted properly, between strand orbits rather than
between copies in the patch, a plain weave's four strands come out with
all six possible pairs adjacent. A gap that everything touches makes
everything adjacent, and a complete graph is not a structure.

**Ownership.** Give each piece of aspect daylight to the strand whose
width opened it, and merge it in. Then the incidental gaps do not exist
to be traversed, each piece has exactly one owner and cannot act as a
hub, and what remains uncovered is only what a dropped strand left.

![A plain weave whose incidental daylight has been absorbed into the strands, at four aspects.](images/holes-as-tiles/absorbed-plain-weave-a_b.png)

This is the one that behaves. `plain weave a|b` absorbs exactly at
every aspect, gap and overlap both zero, and yields six edge classes
and four vertex classes, identical at 0.9, 0.75, 0.5 and 0.25. Six and
four is the size of answer a four-strand weave ought to have, and it
does not move.

Two things about the implementation are worth recording, since both
cost a run. A single buffer of half the nominal gap suits a design
whose daylight is all one width, and a twill's is not: it left six
pieces unclaimed on a weave with no hyphen in it. Growing every strand
at the same rate until the daylight is used up needs no distance chosen
in advance and closes both. And a Voronoi over points sampled along the
strand boundaries assigns the same ground with stepped edges where the
true partition is a straight midline, which the library's regularising
step then raised on at two aspects of four.

## Attributing the daylight to what it replaces

Ownership needs a rule for whose daylight a piece is, and proximity is
the wrong one. At a crossing the ground was opened by two strands
retreating from it, and it belongs to neither one more than the other;
worse, a nearest-strand rule divides a hole along its diagonals, so
each piece faces one strand and meets the others only at points, which
is not the division the design suggests.

The canonical rule asks what each piece REPLACES: which strand would
have covered that ground had the yarn been drawn at full width. It is
computed the way `daylight_by_kind` computes a conscious gap, by
building a second weave and comparing. The reference is the same weave
at an aspect just below 1.0, since at 1.0 the assembly fuses pieces
that share a label and there would be nothing left to attribute to.
Every piece of daylight then goes to the full-width piece covering most
of it, with no distance measured anywhere.

Measured on three weaves at four aspects, it attributes every piece of
daylight and the absorbed regions partition the ground exactly, at an
overlap of zero. Two questions this raised are settled by it.

A pair of strands running ALONGSIDE one another stays adjacent. At full
width they would abut along a line, so they are neighbours, and the
worry was that carving each crossing hole among perpendicular pairs
would leave them sharing nothing. It does not: `plain weave a|b` has
its two `a` strands adjacent at every aspect from 0.9 to 0.25, and the
twill has both its `a` pair and its `b` pair.

And the diagonal is refused, without a rule written to refuse it. Two
absorbed regions at opposite corners of a hole meet at a point, and
adjacency here requires a shared segment rather than a shared point, so
no such pair is ever joined. Where those two strands genuinely cross
somewhere else, that crossing is where the relation is recorded, with
whatever over-and-under sense it has. An adjacency asserted across the
diagonal would be the same relation restated in a place where nothing
happens, and restated without the over and under, which is the part of
a weave worth keeping.

What the attribution gives is therefore a small, stable answer: three
kinds of relation on a plain weave, one alongside and one crossing, at
every strand width, with nothing left over. Two caveats belong with it.
The relations are reported by element letter, so they say that some
pair of `a` strands is adjacent rather than how many are; and at aspect
0.25 one or two pieces of daylight go unattributed on the twills, which
is a small hole in the rule rather than in the idea.

## The dropped strand, which is the one real gap

The distinction the whole exercise turns on is between a gap that means
something and a gap that is an artefact of how wide we chose to draw
the yarn. `daylight_by_kind` computes it, and the constructions above
use it. What we could not do is make it earn its keep as a rule about
adjacency.

![A twill whose code drops a strand. The conscious gap is amber, the daylight strand width opens is grey.](images/holes-as-tiles/hyphen-twill-weave-a_b-.png)

Three formulations were tried against the passing-through structure,
and they bracket the answer rather than settling it. Declining to
bridge across conscious ground withholds nothing, on all three biaxial
weaves in the catalogue whose codes carry a hyphen: the strands either
side of a dropped strand are already neighbours by another route.
Refusing any daylight component that abuts conscious ground refuses 33
of 34 components on `plain weave ab-|cd-`, isolating twelve of its
sixteen strands, because the empty slot is a long band that most of the
daylight touches somewhere. And refusing pairs the slot lies between
finds none.

The honest reading is that a dropped strand does not *separate*
anything in these designs, since the fabric routes around it, and that
a rule strong enough to make it separate something severs a great deal
that has nothing to do with it. Under ownership the question does not
arise in this form: the dropped band is simply the ground nobody
absorbed, and it is a hole in the design rather than a prohibition on a
graph.

One measurement here was wrong before it was right, and the correction
is general. `daylight_by_kind` returns the width daylight as the whole
daylight less the conscious gap *buffered by a whisker*, so the two
regions are held about a millionth of a unit apart by construction and
their boundaries never meet. A veto written on boundary contact
therefore fired zero times on three weaves. A uniform verdict is almost
always the instrument.

## The dual inherits whatever the construction decided

A dual has one tile per vertex, so it can be no more canonical than the
vertices are. The filled plain weave duals to twenty-five tiles at
every aspect, the filled twill to sixty-four while its filling is
congruent and eighty-one once it is not. These are duals of the filled
design, and "the dual of a weave" becomes a definite phrase only once
somebody has said what the holes are. Where the construction is
settled, so is the dual, and it is a perfectly reasonable object to
map; what it is not is something one can quote without also quoting the
construction behind it.

## What this costs the tab

An edit on the Topology tab is aimed at a class, and on a weave the
classes do not line up with what somebody editing a weave would want to
take hold of. A strand's long side is not one edge but four or five,
cut by the filler abutting it at every crossing; the two long sides of
a strand share no class at all on a plain weave; and where they do
share one, whether the ribbon undulates at constant width or pinches
depends on whether that class's segments sit opposite each other. That
record is in `docs/process/weaving-and-topology.md`.

There is a smaller hazard worth flagging, since it is reachable at
ordinary settings. Past twenty-six classes the library issues
two-letter labels, `aa` after `z`, and our own helper returns the
labels joined into one string, which cannot be split back once any of
them is two characters. A thin twill at aspect 0.25 is already past it,
and so is the typed tiling of any twill. Anything built here has to
treat a class as a label rather than as a character.

## Where we have got to, and what is open

Filling the daylight is what the plugin uses today and there is no
argument for abandoning it: it is the only route that gives a thin
weave a structure at all while leaving the weave alone. What we would
not do is present its classes as the structure of the weave.

If the question is what a weave's structure *is*, the answer we would
now pursue is ownership over a typed cut: divide the daylight by what
each piece is for, absorb the part that only strand width opened into
the strand that opened it, and let a dropped strand be the one hole
that survives. On a plain weave that gives a small structure which does
not move with the aspect, which is what one wants from an invariant.

Three things are genuinely open. The attribution of aspect daylight is
currently by proximity, and it should probably be by the grid's own
cells, since what a piece of ground is for is decided by which strand
slot it lies in rather than by which strand it happens to be nearest;
that is likely also why a twill absorbs cleanly and then fails to
build, which we have not yet diagnosed. The structures we have compared
are coarse, being counts of classes and of adjacent pairs, and a real
comparison wants the incidence itself, with the cyclic order at a
vertex. And behind all of it sits the observation that a strand is more
naturally a path than a row of tiles: were the grid a weave rides on to
carry the undulation, the strand would keep its width, nothing would
need filling or absorbing at any aspect, and none of the choices above
would have to be made. That is upstream's territory as much as ours,
and the two are not rivals, since a structure of the kind sketched here
would say what a weave's combinatorics is whoever computes the
geometry.
