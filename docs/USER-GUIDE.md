# WeavingSpace user guide

Mapping several attributes of the same areas at once is a long-standing
challenge of thematic cartography, and it has partial answers already:
multivariate choropleths (bivariate and trivariate colour schemes)
blend two or three attributes into a single symbology, though their
legends must be learned and their ceiling arrives quickly. This plugin
takes a different route. It lays a small repeating pattern of shapes
across your study area and colours each kind of shape by its own
attribute, with its own ordinary symbology, so that each variable stays
individually legible while sharing a single map.

The technique, and the vocabulary used here, come from the weavingspace
library, which can also be driven from a browser: MapWeaver
(https://dosull.github.io/mapweaver/app/) makes the same kinds of maps
outside QGIS, and is worth a look if you would rather not start here.
The thinking behind the technique, with worked examples, is set out in
two articles:

> O'Sullivan, D., & Bergmann, L. (2026). Using MapWeaver to make tiled
> and woven maps of multivariate thematic data. *Cartographic
> Perspectives*, 108, 41–52. https://doi.org/10.14714/CP108.2109
>
> O'Sullivan, D., & Bergmann, L. Tilings and weaves for multivariate
> mapping. Manuscript under review.

This guide restates the practical parts. The article is short and
illustrated, and we would sooner you read it than this.

## Words we use

The *tileable unit* is the small repeating group of shapes stamped
across the map. Everything on the Design tab configures this one
object; the map is simply many copies of it. Within the unit, each
distinct shape is an *element*, labelled a, b, c, and so on. An element
is a slot that one variable may occupy, so a unit with four elements
can carry four variables. The *prototile* is the plain rectangle or
hexagon recording how the unit repeats, and it is what the group inset
shrinks. In woven patterns the elements ride on *strands*, the ribbons
running across the map; a strands code such as `ab-|cd` names which
elements travel in each direction, and a hyphen leaves a deliberate
gap, often the only way to tell otherwise-identical strands apart in a
twill. *Spacing* is the grain of the pattern in map units: the size of
the repeating unit for tilings, the distance between neighbouring
strands for weaves. *Aspect* is how much of that spacing a strand
fills; at 1.0 the weave is solid, and smaller values open it up.

## A way of working

Begin with the data: one polygon layer, in the projected CRS you intend
to publish in, with your attributes as fields. (Geographic layers are
reprojected to Web Mercator so that you can explore, which is rarely
the projection you should finish in.) Then rough in a design. Choose
the number of elements, tiling or weave, and a family, and keep the
spacing coarse at first; large tiles compute quickly, the preview and
the live map follow your changes, and nothing about an early spacing
choice is binding. Assign variables and colours on the Data & colours
tab. Refine with rotation, insets, and the scale and skew controls, and
only then tighten the spacing. What the plugin adds to your project is
a group of ordinary layers. You can finish them in QGIS as you wish.

## Choosing a design

Tiled or woven? The two carry the same information, and we would not
argue you toward either in general. Tilings give compact side-by-side
patches; weaves let the eye follow a strand from one side of
the map to the other, which can make comparisons between distant places
easier to sustain. Try both; live update makes changing your mind
cheap.

How many variables to map is a design question more than a technical
one. Two to four supports genuine value-by-value reading. The catalogue
runs to twenty-six elements for a weave and to two hundred and
fifty-six for a tiling, and nothing stops you using them all, but at
some point the map stops being a table you look things up in and
becomes a texture you scan for pattern and exception. That may be
exactly what you want; it is better decided than discovered.

If the final spacing is near the typical width of your polygons, areas
much smaller than the repeating unit will not show every element at any
spacing; where polygon sizes vary widely this is unavoidable, and it is
the same compromise that any choropleth of mixed-size units strikes.
The Auto button proposes a coarse value from the layer extent, meant
for iteration more than publication.

Rotation usually helps. A square pattern aligned with the frame can
look mechanical; for two-direction weaves we find angles between about
fifteen and seventy-five degrees congenial, while hexagon-based
patterns repeat their own symmetry at multiples of thirty degrees and
change little there. The insets open gaps. Tiles inset opens a thin gap
around every tile (which also strengthens the woven look); group inset
opens one around each whole unit, so that a reader can see which
elements belong together. Group inset exists only for tilings, since
pulling a weave apart at unit boundaries would sever its strands; in
weaves, the hyphens of a strands code do the equivalent work.

An element you leave on `---` carries no variable and draws as plain
fill, which is a legitimate design: a woven map with two of its four
strands blank reads quite differently from one with all four working.
That choice stays put as you change the design around it.

## Colour

The Data & colours tab gives each element layer its initial
symbology, built as a standard QGIS renderer from the Style choices,
so nothing chosen here is final; the built-in Layer Styling panel can
revisit all of it. Each element's Style dropdown also fixes how numeric
values are classed (quantiles, equal intervals, natural breaks, or
pretty breaks), and a narrow Classes column appears beside it whenever
any element is classed, showing the count you asked for on a graduated
row and the number of categories found on a categorized one, so
different elements may be classed differently and into different
numbers of classes. Quant: Unclassed gives the look of a
continuous ramp, cut into fifty linear steps: indistinguishable from
an unclassed choropleth at map scale, while remaining an ordinary
graduated renderer in the styling panel. Two strategies are worth distinguishing. Giving each
element its own ramp (Reds beside Blues beside Greens) makes it easy to
tell which element carries which variable, and is the default. Giving
related variables one shared ramp turns the unit into an instrument for
noticing disagreement: where the variables move together, the pattern
reads as a single smooth tone, and an element out of step with its
neighbours shows up as speckle.

Categorical fields (land cover, dominant crop, period labels) are
initially symbolized with a categorized renderer, one colour per class.
Whenever an element is
categorized, a "Categ colourmap src" column appears in the table. There each element chooses
where its class codes, names, and colours come from: automatic
assignment, any loaded layer that already carries categorized
symbology, or a QGIS style file (a QML saved from any layer, holding
your usual scheme). A file chosen once is offered to every categorized
element, and values a scheme does not mention fall back to automatic
colours. The same QML can be loaded onto an element layer
through QGIS's own Load Style command; choosing it in the dialog
instead makes the scheme part of the design, so it is reapplied
whenever symbology is rebuilt and travels into the GeoPackage export. For numeric data, sequential ramps suit ordered
magnitudes, diverging ramps suit values with a meaningful midpoint, and
the qualitative sets (tab10 and its relatives) are for categories only.

### Setting a colour per value

No ramp knows that forest should be green. An "Edit colours" column
appears beside the ramp whenever any element is classed at all, whether
categorized or graduated; its "Customize"
button opens a small window listing every value that element's field
takes, with the colour each one currently draws in. Click a colour to
change it. The map repaints at once, without re-tiling, and the rest
of the dialog waits until you close the window.

Three things worth knowing:

- Values come from your region layer, so you can set colours before
  generating anything.
- The last row, "(no data)", is the colour for areas the field leaves
  blank.
- Choosing a different ramp, or importing a class source, starts that
  element's colours over and discards what you picked. The plugin says
  how many colours it dropped. Colours are remembered per variable, so
  switching an element to another field and back restores them, and
  they are saved with your project.

While hand-picked colours or an imported class file decide any part of
an element's appearance, its ramp cell reads Custom and shows a swatch
of the colours actually in use; the ramp you last chose still colours
whatever the picks and the file leave unmentioned, and choosing any
ramp puts it back in charge. Recolouring an element's layer in QGIS's
own styling panel works too. Colours set there are kept, exactly as if
you had picked them here, and a clean classify from one of the
standard categorical ramps simply moves the ramp cell to that ramp.

### Class colours and the display range

Quantitative elements open the same window. Each class is listed with
its lower and upper bounds and the colour it draws in. A class keeps
its colour even as its breaks are adjusted.

The first class and the last have boxes you can type into; the
classes between them have none, their breaks always being worked out
for you. On the first class you set where the ramp starts and where
that class ends, and on the last, where it begins and where the ramp
stops. Type a number into any of the four boxes and the relevant class
break(s) are adjusted; a heavy outline round the box says which
of the numbers in front of you were set by you rather than by the
plugin.
A cross inside the box returns the bound to plugin control, and typing
the automatically computed break value in again does the same. A bound
that cannot be drawn is refused and the reason said, rather than quietly
turned into a different number.

Where the ramp starts and stops are the two that reach outside the
data. Set either inside your own values and the areas beyond it stop
being classed: they are drawn in a colour you choose, with their own
line in the legend, rather than left as gaps in the pattern. Set them
outside the data and nothing is excluded, which is how two elements
carrying different attribute columns can be held to one scale and read against
each other. Leaving areas out changes which tiles the map holds rather
than only their colour, so the map catches up at the next Generate.

Changing the break method or the number of classes starts the colours
over, since the classes they were picked for no longer exist, and the
plugin says how many it dropped.

### Copying a classification to other elements

*Copy to* at the top of the window sends this element's classes,
colours, bounds and class count to other elements. Tick as many as you
want and press Copy. Where an element has a different attribute column
its ends are fitted to that attribute column's own data, and a class its
values cannot reach is kept rather than dropped, so the classification
remains relatively intact; a pinned bound the receiving attribute column
cannot reach is left behind and you are told. An element holding no
values at all inside the range you set is left out, and named, since the
copy would leave it with nothing to draw.

Above the list sits the Ramp Display Range: the ramp with two handles
and two percentage boxes beneath it, choosing where along the ramp the
first and last classes take their colours, with the classes between
spread evenly. The handles may meet but never cross. Narrowing the
range is how you keep a sequential ramp out of its near-white end, or
hold two elements to different stretches of the same ramp. For
'Quant: Unclassed' the class list is a preview, fifty faded steps
rather than classes you recolour one at a time, but its ends are still
yours to adjust: a strip above the list says where the ramp starts and
where it ends, which is the same pair of numbers the first and last rows
carry
in the classed styles. Reverse carries all of this along -- the
range mirrors and picked classes swap ends -- so flipping it twice
costs nothing. A bound you set is not Custom: its colours are still the
ramp's, so the cell goes on naming the ramp and boxes the bound.
The cell reads Custom while hand-picked colours or a narrowed range are
in force, and choosing a ramp starts the element over, range and class
colours alike.

## The map option switches

*Join data using whole tileable* asks every element in a unit to take
its data from the same underlying area, so that each unit reads as a
coherent local summary. Left off, each tile follows whichever area it
overlaps most, which is more faithful tile by tile but lets a unit
straddle a boundary and mix its sources; for weaves we generally leave
it off. *Retain complete tileables* keeps whole units that touch the
region, letting the pattern spill outward, and is mostly of interest
alongside the whole-tileable join. *Clip by map units* trims the
pattern to the region outline; it aids orientation, fragments the edge
tiles, and is the slowest step, so we suggest leaving it off until the
end. The unclipped, ragged edge sits more comfortably with the pattern
as a design, in our view. *Use tileable as icon* places one unit at the
centre of each polygon instead of tiling continuously, a gentler
multivariate symbol that pairs well with the outlines layer.

*Warn about lack of legibility in colour choices* checks, after each
map is drawn, whether any two elements use colours a reader may not be
able to tell apart — in ordinary vision and for the red-green colour
deficiencies — and says so. It is off by default. Turn it on when the
design is close to settled: while you are still trying ramps it has
little useful to say, and nothing about it changes the map.

A first map appears of its own accord once a layer and variables are
in place, and live update then regenerates it as you adjust settings,
replacing the previous result so long as the estimated tile count
stays modest. Past that it pauses with a note rather than attempt something
heroic, and the Generate button remains for deliberate large runs.

## Saving and sharing

Drawing a map and saving one are separate acts. Nothing is written until
you press *Save*, which puts every element layer into a single file
with its symbology embedded: one `.gpkg` that a colleague can drop
into QGIS and see your elements as you styled them. The region
outlines stay in the project, since they are drawn from your own
layer, and until you press Save the map lives only with the project.
Nothing is opened until you press *Load*, on the row beneath, which
brings a saved map back into the dialog so you can carry on with it.
Save prompts you to confirm if the file selected holds a
map made from unrelated data.

Regenerating replaces the previous group and keeps whatever styling
you have refined by hand; an element's symbology is rebuilt only when
you change its variable, style, ramp, or classification in the dialog.
*Create as new group* keeps a previous attempt alongside for
comparison, and a result you mean to keep on disk wants a file of its
own.

Each map the plugin draws lives in its own QGIS layer group, named for
the dataset it was made from, and the *QGIS Layer Group* chooser beside
the region layer says which one the next run will land in. Choosing a
dataset selects its group and choosing a group selects its dataset, so
the two cannot disagree; where one dataset owns several maps, the most
recent is chosen. Selecting a group brings back the design it was made
with, down to each element's variable, style, ramp, class colours and
pinned bounds, so a project holding several maps can be picked up
wherever you left it. Rename a group if you would rather call it
something else: the plugin finds its own output by what is inside the
group.

A map saved to a GeoPackage remembers how it was made. Open a saved
file and the plugin brings back its layers and its whole design without
the project you made it in, finding the data it was drawn from where
that data is still on your computer. Tick *Include the source data* if
the file is going to somebody who does not have it.

## Limits worth knowing

Tile counts grow with the square of the inverse spacing, so a small
spacing over a large region asks for an enormous number of polygons.
The plugin estimates the count first and asks before drawing a large
one, suggesting a workable spacing; past a certain size it says so in
stronger terms, since a map that large may use all the memory on your
computer and leave QGIS unresponsive while it is drawn. The decision is
yours either way. What it does refuse is a design that does not repeat
across the plane at all, and a layer whose extent it cannot measure,
neither of which any spacing would help. Layer identities
change when you regenerate (the styling carries over), so layers placed
in a print layout need re-picking afterwards. There is no tile-shaped
legend yet; the layer panel lists each element's classes, and a legend
composed from the element layers in a print layout does the job.

We welcome reports of anything else that surprises you.
