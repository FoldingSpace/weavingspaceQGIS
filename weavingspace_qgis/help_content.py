"""In-dialog help: a condensed version of docs/USER-GUIDE.md.

Written in the plugin authors' voice; paraphrases (and cites) the
Cartographic Perspectives article rather than quoting it.
"""

HELP_HTML = """
<h2>What this plugin makes</h2>
<p>Mapping several attributes of the same areas at once is a
long-standing challenge of thematic cartography, and it has partial
answers already: multivariate choropleths (bivariate and trivariate
colour schemes) blend two or three attributes into a single
symbology, though their legends must be learned and their ceiling
arrives quickly. This plugin takes a different route. It lays a small
repeating pattern across your study area and colours each kind of
shape in it (each <i>element</i>, labelled a, b, c&hellip;) by its
own attribute, with its own ordinary symbology, so each variable
stays individually legible while sharing the one map. With two or
three variables the result can be read value by value, much as a
choropleth is; with more it reads as a texture in which agreement
forms smooth tone and exception announces itself. Nor are those the
only readings such maps repay (we take up others, and the design
choices that serve them, in a paper presently under review); it is
still worth deciding early which reading you are designing for.</p>

<h2>A way of working</h2>
<p>Begin with one polygon layer in the projected CRS you mean to
publish in, attributes as fields. Rough in a design with the spacing
kept coarse; iteration is fast, and live update follows your changes.
Assign variables and colours, refine rotation and insets, and tighten
the spacing last. The result is a group of ordinary QGIS layers, one
per element, so the finishing moves are ones you already know:
QGIS's built-in Layer Styling panel, GeoPackage export, a print
layout.</p>

<h2>Choosing a design</h2>
<p>Tilings and weaves carry the same information. Tilings give compact
side-by-side patches and suit the icon and glyph options; weaves let
the eye follow a strand between distant places. Two plainer families
round out the catalogue: stripes runs the elements as parallel bands,
and grid arrays them as squares, with rows and columns adjustable
(fewer elements than cells leaves regular openings in the pattern). A sensible final
spacing sits near the typical width of your polygons (divided, for a
weave, by the strands per direction); the smallest polygons will miss
some elements at any single spacing, the familiar compromise of
mixed-size choropleths. Rotation usually helps, with something between
fifteen and seventy-five degrees congenial for two-direction weaves,
while hexagon-based patterns change little at multiples of thirty. A
hyphen in a strands code leaves a deliberate gap so identical-looking
strands can be told apart, and the two insets open gaps that show which
shapes belong together.</p>

<h2>Colour</h2>
<p>Each element layer arrives with its initial symbology, a standard
QGIS renderer built from your Style choices, so nothing here is
final. The Style dropdown fixes each element's classification method
(Quant: Unclassed gives the look of a continuous
ramp, in fifty linear steps), and the Classes column beside it (present while
any element is graduated) its number of classes. Distinct ramps per element make
it easy to tell variables apart (the default). One shared ramp across
related variables turns the unit into an instrument for noticing
disagreement: agreement reads as smooth tone, and an element out of
step with its neighbours shows as speckle. Categorical fields (land
cover, period labels) receive a categorized renderer; each categorized
element's Categ colourmap src cell chooses where its class codes,
names, and colours come from: automatic assignment, another loaded
layer's categorized symbology, or a QML style file. A file chosen once
is offered to every categorized element, and the scheme travels
through regeneration and GeoPackage export alike.</p>

<p>An element left on <i>---</i> takes no variable and draws as plain
fill; that is a design choice like any other, and it stays put as you
change the pattern around it.</p>

<h2>The switches</h2>
<p><i>Join data using whole tileable</i> has every element in a unit
take data from the same area, so units read as coherent local
summaries; left off, each tile follows the area it overlaps most, which
is more faithful tile by tile but lets a unit near a boundary mix its
sources (for weaves we generally leave it off). <i>Clip by map
units</i> gives a tidy outline at the cost of fragmented edge tiles and
speed; the ragged default sits more comfortably with the pattern as a
design. <i>Use tileable as icon</i> places one unit per polygon, a
gentler multivariate symbol that pairs well with the outlines
layer.</p>

<h2>Regenerating and output</h2>
<p>A first map appears of its own accord once a layer and variables
are in place. Generate (and live update) then replace the previous
result in place, and styling you have refined by hand is kept unless
you change that element's assignment in the dialog. <i>Create as new group</i> keeps a previous attempt for
comparison. <i>Save to GeoPackage</i> writes all element layers, with
their symbology, into one shareable file. Layer identities change on
regeneration, so re-pick layers in print layouts afterwards.</p>

<h2>Further reading</h2>
<p>The thinking behind the technique, with worked examples:<br>
O'Sullivan, D., &amp; Bergmann, L. (2026). Using MapWeaver to make
tiled and woven maps of multivariate thematic data. <i>Cartographic
Perspectives, 108</i>, 41&ndash;52.
<a href="https://doi.org/10.14714/CP108.2109">doi:10.14714/CP108.2109</a><br>
O'Sullivan, D., &amp; Bergmann, L. Tilings and weaves for multivariate
mapping. Manuscript under review.</p>
<p>Library and examples:
<a href="https://github.com/DOSull/weavingspace">github.com/DOSull/weavingspace</a>.
If you would like to make maps like these outside QGIS, MapWeaver is a
browser-based tool built on the same library:
<a href="https://dosull.github.io/mapweaver/app/">dosull.github.io/mapweaver/app</a>.
We welcome your examples, questions, and reports of anything that
surprises you.</p>
"""
