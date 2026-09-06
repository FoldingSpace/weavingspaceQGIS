# Archive: the accounts behind the package's docstrings

The docstrings in `weavingspace_qgis` keep what a maintainer needs -- what
a function does, its Args and Returns, and the reasoning behind any
non-obvious choice -- and quote an id here for the ACCOUNT: the day, the
first attempt, the measurement, the superseded form. Cut on 2026-09-05 at
the maintainer's asking; `tools/doc_archive.py` checks that every D-id a
docstring quotes is defined here and every account is still quoted.
Nothing is deleted and ids are never renumbered.

## Index

- **D-1** — bridge.py: split_out_the_no_data  <sub>docstring</sub>
- **D-2** — bridge.py: fitted_breaks  <sub>docstring</sub>
- **D-3** — bridge.py: unworn_classes  <sub>docstring</sub>
- **D-4** — bridge.py: empty_classes_message  <sub>docstring</sub>
- **D-5** — bridge.py: few_values_message  <sub>docstring</sub>
- **D-6** — bridge.py: pin_problem  <sub>docstring</sub>
- **D-7** — bridge.py: every_value_reads_as_a_number  <sub>docstring</sub>
- **D-8** — bridge.py: icon_misattribution_message  <sub>docstring</sub>
- **D-9** — bridge.py: estimate_tile_count_bounds  <sub>docstring</sub>
- **D-10** — bridge.py: estimate_icon_count  <sub>docstring</sub>
- **D-11** — bridge.py: ramp_swatch_colour  <sub>docstring</sub>
- **D-12** — bridge.py: get_ramp  <sub>docstring</sub>
- **D-13** — category_editor.py: _bound_box  <sub>docstring</sub>
- **D-14** — category_editor.py: NoPinHere  <sub>docstring</sub>
- **D-15** — category_editor.py: PinButton  <sub>docstring</sub>
- **D-16** — compat.py: layer_data_is_available  <sub>docstring</sub>
- **D-17** — dialog.py: _edited_unit_key  <sub>docstring</sub>
- **D-18** — dialog.py: _newest_output_group  <sub>docstring</sub>
- **D-19** — dialog.py: _tell_the_layers_which_region_we_landed_on  <sub>docstring</sub>
- **D-20** — dialog.py: _save_the_map  <sub>docstring</sub>
- **D-21** — dialog.py: _our_groups  <sub>docstring</sub>
- **D-22** — dialog.py: _needs_a_no_data_split  <sub>docstring</sub>
- **D-23** — dialog.py: _copy_onto_one  <sub>docstring</sub>
- **D-24** — dialog.py: _row_follows_the_renderer  <sub>docstring</sub>
- **D-25** — dialog.py: _legend_size_note  <sub>docstring</sub>
- **D-26** — dialog.py: _retire_an_undrawable_pin  <sub>docstring</sub>
- **D-27** — dialog.py: retire  <sub>docstring</sub>
- **D-28** — dialog.py: _layer_fingerprint  <sub>docstring</sub>
- **D-29** — dialog.py: changeEvent  <sub>docstring</sub>
- **D-30** — dialog.py: _within_the_screen  <sub>docstring</sub>
- **D-31** — dialog.py: _limit_the_figures_on_show  <sub>docstring</sub>
- **D-32** — dialog.py: SpacingSpinBox  <sub>docstring</sub>
- **D-33** — dialog.py: same_source  <sub>docstring</sub>
- **D-34** — topology_edits.py: _same_shape  <sub>docstring</sub>
- **D-35** — topology_edits.py: apply  <sub>docstring</sub>

### D-1 — bridge.py: split_out_the_no_data

<sub>Cut from `weavingspace_qgis/bridge.py`, the docstring of `split_out_the_no_data`, on 2026-09-05.</sub>

Reported from the field on 2026-08-16 with an area that is null in
every variable, so it read as a hole under two different tilings and
whichever column was mapped. The fix chosen by the maintainer keeps
every renderer standard: the missing rows become their own layer,
categorically rendered, grouped beside the graduated one, and the
plugin's own table goes on showing ONE element with No data as one
more class in its colour editor.

### D-2 — bridge.py: fitted_breaks

<sub>Cut from `weavingspace_qgis/bridge.py`, the docstring of `fitted_breaks`, on 2026-09-05.</sub>

A collapse moves the OUTER edge and never a copied boundary, and
the first draft did the opposite: pulling the top class's lower
bound down to a smaller column's max produced (30, 3) -- a class
running backwards -- whenever more than one copied break sat above
that max. Measured on breaks [4, 14.2, 30, 55] fitted to a column
running 0 to 3. The ladder must stay monotonic whatever it is
fitted to, so the collapse is expressed as an outer edge meeting
its neighbour rather than as a boundary being dragged.

### D-3 — bridge.py: unworn_classes

<sub>Cut from `weavingspace_qgis/bridge.py`, the docstring of `unworn_classes`, on 2026-09-05.</sub>

THAT LAST WORD WAS WRONG UNTIL 2026-08-16, and it was found when a
short-lived experiment moved a class bound (see docs/TESTING.md,
"Three ways to move a class boundary, and why none of them worked").
The experiment is gone; the correction it exposed is real and
stays. This used to exclude the
lower bound for every range but the first, which agrees with the
renderer while the ranges touch -- a value on a shared boundary is
caught by the range BELOW it, earlier in the loop, so first-match
hides the difference. A boundary value moved off that shared bound
-- by anything, including the experiment that briefly did so on
purpose -- falls to the degenerate range that means exactly it, and
the renderer accepts it there while the old rule refused it.

### D-4 — bridge.py: empty_classes_message

<sub>Cut from `weavingspace_qgis/bridge.py`, the docstring of `empty_classes_message`, on 2026-09-05.</sub>

So the two say different things and both are wanted. This one
reports THAT classes are empty, measured on the ladder the map
draws; ``few_values_message`` reports WHY when the reason is a
column with too few distinct values to fill the ladder. The caller
picks whichever fits and never says both, since two sentences about
one column is one too many.

### D-5 — bridge.py: few_values_message

<sub>Cut from `weavingspace_qgis/bridge.py`, the docstring of `few_values_message`, on 2026-09-05.</sub>

So the notice now reports EMPTINESS rather than shortening, and
since 2026-08-17 it is the ONLY thing that reports it. The swatch
used to hatch those classes as well; the maintainer ruled the mark
out as more confusing than helpful to somebody meeting it, which
puts the whole weight on this sentence. A user whose Classes
spinner reads five over a map drawing three deserves to be told
why, in words.

### D-6 — bridge.py: pin_problem

<sub>Cut from `weavingspace_qgis/bridge.py`, the docstring of `pin_problem`, on 2026-09-05.</sub>

NOR IS A BOUND OUTSIDE THE DATA, since 2026-08-17. It was refused
until then, and the maintainer's ruling on meeting the refusal is
that setting limits wider than one column is the point rather than a
mistake: one pair of limits across several variables is how a colour
comes to mean the same number on every map. The class beyond the
data simply goes unworn. The reasoning is
at the line where the check used to be.

### D-7 — bridge.py: every_value_reads_as_a_number

<sub>Cut from `weavingspace_qgis/bridge.py`, the docstring of `every_value_reads_as_a_number`, on 2026-09-05.</sub>

WHY IT EXISTS AT ALL. The settled rule that a quantitative style
never stands on a text field rests on a measured claim: a graduated
renderer over text comes back with no ranges, so every tile falls
outside every class and the layer paints nothing. Measured again on
QGIS 4.0.3 (2026-08-28, the `spec` hunt), that is true of WORDS and
false of NUMERIC STRINGS -- a String column running "10" to "120"
classifies exactly as its integer twin, five ranges, same bounds,
twelve of twelve features symbolised. So the rule was true of the
example that prompted it and wider than its own evidence, and
somebody whose numbers arrived through a CSV join or a GeoJSON
could not draw a choropleth from them at all: at three thousand
areas they were given three thousand and one categories.
(Maintainer's ruling, 2026-08-29.)

### D-8 — bridge.py: icon_misattribution_message

<sub>Cut from `weavingspace_qgis/bridge.py`, the docstring of `icon_misattribution_message`, on 2026-09-05.</sub>

THE JOIN ITSELF IS THE VENDORED LIBRARY'S, and the maintainer's
ruling is that the plugin answers it by telling the user rather than
by computing a placement of its own; nothing is sent upstream yet.

### D-9 — bridge.py: estimate_tile_count_bounds

<sub>Cut from `weavingspace_qgis/bridge.py`, the docstring of `estimate_tile_count_bounds`, on 2026-09-05.</sub>

Only the last is generous on both, and a guard that UNDER-counts
waves through a run that then takes the machine. Each polygon's own
perimeter double-counts every shared internal edge and refuses maps
outright; the bounding box knows nothing of cells strung across it
and was measured 2% under, by a guard written the same hour. A
perimeter summed per row is a property of how the data was cut into
rows rather than of the ground it covers; the dissolved one is the
ground's own edge.

### D-10 — bridge.py: estimate_icon_count

<sub>Cut from `weavingspace_qgis/bridge.py`, the docstring of `estimate_icon_count`, on 2026-09-05.</sub>

MEASURED 2026-08-19, which is why it exists: on twenty-five areas
with a four-element unit the tiling estimator answered 208,521
where icon mode drew 100. The hard gate refused the run outright and
advised a larger spacing, which in icon mode draws bigger icons
rather than fewer of them, and live update had already paused itself
for a map of a hundred tiles.

### D-11 — bridge.py: ramp_swatch_colour

<sub>Cut from `weavingspace_qgis/bridge.py`, the docstring of `ramp_swatch_colour`, on 2026-09-05.</sub>

BOTH EXTRA ARGUMENTS WERE ADDED 2026-08-17, and each was a defect
rather than a nicety. Ignoring `reverse` drew a reversed element in
the forward ramp's colour, which on a diverging ramp is the opposite
end. Ignoring the window drew a narrowed element in a colour the map
no longer contains: measured on Reds narrowed to 0-20%, the preview
painted 15,460 pixels of #e7342a while the map painted none of it
and 8,692 of #fff5f0. The design view exists so somebody can judge
whether the elements read as distinct, which is exactly the
judgement a wrong colour makes for them.

### D-12 — bridge.py: get_ramp

<sub>Cut from `weavingspace_qgis/bridge.py`, the docstring of `get_ramp`, on 2026-09-05.</sub>

There used to be a third branch here, sampling an unknown ramp at 32
even steps and rebuilding it as a gradient, for "a ramp type we have
not met". It was unreachable and is gone (2026-08-13). `invert` is
defined on QgsColorRamp ITSELF, not on the subclasses, so
`hasattr(ramp, "invert")` is true for every ramp QGIS defines and
for any subclass a third-party plugin might register -- measured on
all six built-in classes and on a bare subclass. The fallback could
not run, and it was also the worst of the three: rebuilding a
discrete scheme as a two-stop gradient would have thrown away every
colour between the ends.

### D-13 — category_editor.py: _bound_box

<sub>Cut from `weavingspace_qgis/category_editor.py`, the docstring of `_bound_box`, on 2026-09-05.</sub>

THE DECIMALS, measured 2026-08-15 with real widgets: they were a
flat six, which rounded a rate of 4e-07 to zero and 8.5e-07 to
1e-06. On twenty provinces at k=4, pinning the number the control
produced rather than the number typed moved ELEVEN of twenty areas
into a different class, and ``pin_problem`` accepts both, because
both are inside the data. So the box takes nine significant places
below the column's own span -- but never FEWER than
``_LEAST_DECIMALS``, which is the half that was missing: a column
of square metres has a span of 1e12, nine places below that is
less than none, and a box at zero decimals cannot hold a bound of
0.5. Under the wide-limits ruling that is an ordinary thing to
ask for, since the whole point is giving one pair of limits to
columns of different magnitudes.

THE RANGE was plus or minus 100 TIMES this element's own extremes
until 2026-08-17, and before that a flat 1e12 -- so a province
area of 1.875e12 square metres appeared in the box as 1e12 and
pinned there, and typing 3000000000000 left 300000000000, a factor
of ten, with nothing said. The 100x rule fixed that case and kept
the shape of the fault: on an element whose tiles reach 11, typing
1200 keeps 120, because the fourth keystroke is refused by the
validator. The map is then drawn from 120, ``_pinned_bounds``
records 120, the layer is stamped 120, and nothing is said --
``pin_problem`` is asked about the number the CONTROL produced,
and 120 is perfectly legal. Two elements given the same typed 1200
pin 120 and 1200: one act, two ladders, which is precisely what
wide limits exist to prevent.

The docstring above this used to say the range was "wide open",
which is what the code intended and not what it did.

### D-14 — category_editor.py: NoPinHere

<sub>Cut from `weavingspace_qgis/category_editor.py`, the docstring of `NoPinHere`, on 2026-09-05.</sub>

Blank was tried first and is not available here for the reason the
cell is misleading in the first place: the grid draws the box
whether or not anything sits in it, so "nothing" and "an empty
control" look the same. Hatching says NOT AVAILABLE in the one
vocabulary a table has.

THIS IS NOW THE ONLY PLACE THE PLUGIN HATCHES ANYTHING, and the
history is worth a paragraph because it looks like a reversal and
is not. The ramp swatch used the same mark for "no tile wears this
class", and on 2026-08-16 the maintainer was asked whether two
hatchings saying different KINDS of thing, met by a reader on one
row, could be told apart; they ruled that 45 degrees in both is
fine, since "nothing available here" covers both honestly and a
second texture would ask somebody to distinguish two patterns at
twelve pixels. On 2026-08-17 they ruled on a DIFFERENT question --
whether the mark reads at all to somebody meeting it -- and took it
off the swatch. The first ruling stands where it applies: do not
differentiate this hatching from anything by angle or density on
confusability grounds, because that was weighed.

### D-15 — category_editor.py: PinButton

<sub>Cut from `weavingspace_qgis/category_editor.py`, the docstring of `PinButton`, on 2026-09-05.</sub>

THE SILHOUETTE IS A TACK, and the first version was not. It drew a
round head on a straight shaft, which is a MAGNIFYING GLASS -- the
maintainer read it as one on sight, 2026-08-16, and once seen it
cannot be unseen. What separates the two shapes is the taper: a
lens has a handle of even width, a tack has a body that narrows to
a point. So the head is wide and flat like a tack's, and the body
is a triangle ending in a point rather than a line ending in
nothing. Drawing an icon whose meaning is its outline is worth a
minute with a pencil first; "it has the right parts" is not the
same as "it reads as the thing".

### D-16 — compat.py: layer_data_is_available

<sub>Cut from `weavingspace_qgis/compat.py`, the docstring of `layer_data_is_available`, on 2026-09-05.</sub>

...UNTIL SOMETHING RELOADS THE LAYER, WHICH NOBODY DOES. That
paragraph describes a layer AFTER `reload()`, and until 2026-08-20
those two checks were the whole of this function -- so the case it
names in its own Returns block, a file that has gone while the
layer still claims to be valid, was exactly the case it waved
through. Measured on QGIS 4.0.3, moving a GeoPackage out from under
an open layer:

### D-17 — dialog.py: _edited_unit_key

<sub>Cut from `weavingspace_qgis/dialog.py`, the docstring of `_edited_unit_key`, on 2026-09-05.</sub>

THIS PARAGRAPH USED TO SAY `_topology_stamp` IS DELIBERATELY BLIND
TO MODIFIERS, "which is right for judging a BUILD", and that was
wrong -- corrected 2026-08-31. Ruling 1 does say the topology is of
the un-modified unit, but `_queue_topology` builds from
`self._unit`, which is the unit AFTER the chain, and the suite's
own drop test turns on exactly that: set a tile inset and the
topology stops existing, because `Topology` needs a gap-free tiling
and an inset opens gaps. So the stamp carries the modifiers now,
and the tuple below is REDUNDANT rather than a second fact -- both
read the same widgets. It is kept because the guard written for the
2026-08-30 defect stands on it, and it can go the day somebody
re-aims that.
Keyed on the stamp alone, moving Rotate to 30 and pressing Generate
put the pre-rotation unit back and drew a map TILE FOR TILE
identical to rotate 0 -- and Generate is guaranteed to land inside
that window, because it flushes the rebuild itself. The design view
showed the same wrong design, healing only when the background
build landed seconds later.

### D-18 — dialog.py: _newest_output_group

<sub>Cut from `weavingspace_qgis/dialog.py`, the docstring of `_newest_output_group`, on 2026-09-05.</sub>

AND WHY NOT THE NAME AT ALL, which is what replaced it. The newest
used to be read off the SUFFIX -- the bare name counting as zero
and "WeavingSpace tiles N" as N -- and the loop SKIPPED any group
whose name did not match, on the reasoning that somebody had
renamed it and it was not ours to guess. Renaming a group in the
layers panel is an ordinary thing to do, and the consequence was
that adoption found nothing: the next run built a rival, leaving
the user's own layers in the renamed group, stale, with the
GeoPackage link silently dropped. Measured 2026-08-17: rename,
save, reopen, change the spacing, and the project holds
'Deprivation, woven' with four file-backed layers beneath a fresh
'WeavingSpace tiles' holding four memory layers of the same map.

### D-19 — dialog.py: _tell_the_layers_which_region_we_landed_on

<sub>Cut from `weavingspace_qgis/dialog.py`, the docstring of `_tell_the_layers_which_region_we_landed_on`, on 2026-09-05.</sub>

MEASURED AT BOTH DOORS, one process, each on its own file
(`tools/probes/what_a_resumed_map_stamps_on_its_layers.py`): the
layers saying `MultiPolygon?crs=EPSG:3857&uid={...}` against a
chooser holding `<file>|layername=weavingspace_region`, the
binding answering False, and TWO groups of four layers each after
one Generate. The fresh branch does it too, which is why this is a
stamp's defect rather than a flag's -- `_landed_this_session` only
decides whether the binding is reached at all.

### D-20 — dialog.py: _save_the_map

<sub>Cut from `weavingspace_qgis/dialog.py`, the docstring of `_save_the_map`, on 2026-09-05.</sub>

WHY IT IS A BUTTON. Until 2026-08-27 every Generate wrote the file
whenever an output path was set, so the map was saved as a side
effect of drawing it: a path chosen for later was written to at
once, live update had to be gated to stop it rewriting somebody's
file on every keystroke, and clearing the box forked a second
group. The maintainer ruled that saving is a positive act.

### D-21 — dialog.py: _our_groups

<sub>Cut from `weavingspace_qgis/dialog.py`, the docstring of `_our_groups`, on 2026-09-05.</sub>

MAINTAINER'S RULING, 2026-08-26: NON-RECURSIVE IS FINE, and it is
recorded here with what it costs rather than only what it buys,
because a hunt raised it that day and the next one should not have
to. Nesting an output group inside a folder takes it out of every
reader that walks `root.children()`: the chooser stops listing it,
the one-file-is-one-map check in `_resume_from_gpkg` cannot see
it, so resuming that file builds a SECOND copy of the map beside
it, and a later run on the new copy drops tables the nested one is
still drawing from -- measured that day, `tiles_a_v1` removed from
the file while the tidied group went on pointing at it. "Left
alone" therefore means unmanaged rather than protected, which is
the honest reading and the one the ruling accepts.

### D-22 — dialog.py: _needs_a_no_data_split

<sub>Cut from `weavingspace_qgis/dialog.py`, the docstring of `_needs_a_no_data_split`, on 2026-09-05.</sub>

MEASURED 2026-08-17, two arms of one fixture differing only by a
dock edit: with the element left alone, 58 tiles and ZERO of
490,000 pixels unpainted; after refining it in QGIS's Symbology
panel, the paired layer gone, the rows folded back onto an element
whose renderer has no class for them, and 28,828 PIXELS UNPAINTED
with nothing said. That is precisely the harm the No Data layer
was built to remove: honest "not known" became holes reading
"nothing is here".

### D-23 — dialog.py: _copy_onto_one

<sub>Cut from `weavingspace_qgis/dialog.py`, the docstring of `_copy_onto_one`, on 2026-09-05.</sub>

TWO THINGS DO NOT TRAVEL, both added 2026-08-15 after a hunt.
A pin flag is CHECKED against the receiving column first, because
a pin is a claim about this element's own data and this was the
one route by which an unchecked bound could arrive; a bound the
receiving column cannot reach is left behind and said, and the
ladder still travels whole. And an Unclassed source's class count
does not travel at all: its fifty is fixed by the style rather
than chosen by anybody, and `_class_counts` is the record that
means CHOSEN -- written there, it was clamped to twenty at the
next rebuild and replaced a count the user had picked.

### D-24 — dialog.py: _row_follows_the_renderer

<sub>Cut from `weavingspace_qgis/dialog.py`, the docstring of `_row_follows_the_renderer`, on 2026-09-05.</sub>

THE MAINTAINER'S RULING, 2026-08-17, choosing between three
options put to them: the row FOLLOWS the layer wherever the plugin
can name what the layer holds, and defers only where it cannot.
Pins were the alternative and cannot carry this -- the tester's
element disagreed on the class COUNT and the RAMP as well as the
breaks, and a pin names a bound. Deferring on any outside edit was
the other, and hands away an element the user may still want to
drive from the table.

It also settles the reported oddity that three rows read
CATEGORIZED over graduated layers. That was never a categorical
fault: the rows were simply stale, and the greyed 32, 33 and 32
were distinct-value counts belonging to whatever those rows last
believed. Following the renderer makes the question disappear
rather than answering it.

### D-25 — dialog.py: _legend_size_note

<sub>Cut from `weavingspace_qgis/dialog.py`, the docstring of `_legend_size_note`, on 2026-09-05.</sub>

TWO QUESTIONS, ONE SENTENCE, AND THE RENDERER WINS. The
distinct-value count says WHY a ladder cannot be filled;
`unworn_classes` says THAT it is not, measured on the classes the
map draws. They are not the same question and a hunt found them
disagreeing in four cases of six on 2026-08-17 -- a pin below the
data, a pin above it, a copied ladder, and a plain tied column.
So where the renderer can be asked, its answer decides whether
anything is said at all, and the distinct-value sentence is
preferred only when it is also true, because it carries the
reason. Where it cannot be asked -- before the first run, most
often -- the old count answers alone, since a notice that waits
for output would never fire on the path a user meets first.

### D-26 — dialog.py: _retire_an_undrawable_pin

<sub>Cut from `weavingspace_qgis/dialog.py`, the docstring of `_retire_an_undrawable_pin`, on 2026-09-05.</sub>

Measured 2026-08-16: pin `v1`'s low at 7.0 on a column running
0-35, then retype that column to 5000-40000 or swap in a layer at
that scale. The map's first class ends at 12000, and
`_pinned_bounds` still holds 7.0, the ramp cell still draws its
pinned box, the layer is still stamped with it, and nothing is
said. Save, reopen, and the 7.0 is read back off the layer, so
the row shows a pin over a map that ignores it -- while
`pin_problem` refuses that very number if it is typed.

### D-27 — dialog.py: retire

<sub>Cut from `weavingspace_qgis/dialog.py`, the docstring of `retire`, on 2026-09-05.</sub>

IT DOES NOT CLEAR THE RECORD OF WHO IS IN CHARGE, and that was
the first attempt. The gate reads "if there IS a live dialog and
it is not me, drop" -- None means "nobody has said", so clearing
the record makes EVERY dialog believe it is in charge rather than
none. Measured 2026-08-27: the message the disabled plugin had
just been fixed for came straight back. So retirement is a fact
about this dialog, read by `_dialog_is_gone`, which every
long-lived handler already asks first.

### D-28 — dialog.py: _layer_fingerprint

<sub>Cut from `weavingspace_qgis/dialog.py`, the docstring of `_layer_fingerprint`, on 2026-09-05.</sub>

That is a LIMIT rather than a bug, and it is deliberate as of the
same day (maintainer's decision): the alternatives are polling
somebody's data or fingerprinting the values themselves, which
costs a full scan on every check for a case the plugin cannot
reliably detect anyway. The rule this file used to state — that
"neither mechanism covers the other's blind spot" — was simply
untrue, and a false promise in a docstring is worse than a known
gap, because it stops anybody looking.

### D-29 — dialog.py: changeEvent

<sub>Cut from `weavingspace_qgis/dialog.py`, the docstring of `changeEvent`, on 2026-09-05.</sub>

MEASURED 2026-08-31, and with a control arm, which is what makes
it a defect rather than a worry. A dialog BUILT at each size is
healthy: the Pattern chooser goes 250px at 9pt, 341 at 13, 522 at
20, and every family name stays legible. The same dialog built at
9pt and MET at 20pt keeps its 250px, and two pairs of designs
become one string -- `twill weave ab|cd 1,2` and `twill weave
ab|cd 1,2,2,1` both read `twill weave ab|cd 1...`, as do the two
basket weaves. A chooser that cannot tell two designs apart is a
chooser you cannot choose with.

### D-30 — dialog.py: _within_the_screen

<sub>Cut from `weavingspace_qgis/dialog.py`, the docstring of `_within_the_screen`, on 2026-09-05.</sub>

NO GUARD HERE OR ON CI CAN SEE THE ASSEMBLED WINDOW -- offscreen
reports 1279px where cocoa gives 1334 -- so what this promises is
measured by `tools/platform_probe.py` on a real desktop, and the
unit test can only ask that a size larger than the screen comes
back smaller.

### D-31 — dialog.py: _limit_the_figures_on_show

<sub>Cut from `weavingspace_qgis/dialog.py`, the docstring of `_limit_the_figures_on_show`, on 2026-09-05.</sub>

Where the two genuinely disagree -- a step of 0.01 on a control
whose values run in the thousands, where three figures are used
up before the point -- the CAP wins and the arrows move a digit
that is not shown. That is the maintainer's rule applied
literally, and the honest repair is to widen the step, so one
number per control still governs both.

### D-32 — dialog.py: SpacingSpinBox

<sub>Cut from `weavingspace_qgis/dialog.py`, the docstring of `SpacingSpinBox`, on 2026-09-05.</sub>

THE FIRST FIX FOR THAT WAS WRONG AND IS WORTH RECORDING, because the
mistake is easy to repeat. It sized `decimals` from the spacing
auto-fitting had just computed -- 500 gives three significant
figures at zero decimals -- and a QDoubleSpinBox with zero decimals
cannot REPRESENT 500.5. So typing 500.5 gave 501, typing 215.509124
gave 216, and the map was tiled from the rounded number with nothing
said. `decimals` governs display AND input AND storage, so any rule
that lowers it to tidy the display destroys data.

THE TRIMMING ITSELF MOVED TO `widgets.TrimmedSpinBox` on 2026-08-17,
when the class-bound boxes were widened and needed exactly the same
thing. It lived here in full for a day, and a second copy was
written in `category_editor.py` before anybody noticed the two would
have to learn about locales separately. This class keeps only what
is about SPACING; the shared behaviour is documented where it lives.

AND IT ASKS FOR LESS ROOM THAN ITS RANGE, added 2026-08-30. A spin
box's size hint is computed from its MAXIMUM's text, and this one's
maximum is 1e12 at six decimals -- twenty characters, which is a
large part of why the maintainer met a Design tab whose every
control ran the width of the window. The range is right and must not
shrink: spanning twelve orders of magnitude is exactly what lets one
control serve a floor plan and a country. What is wrong is reserving
room to show a number nobody types.

### D-33 — dialog.py: same_source

<sub>Cut from `weavingspace_qgis/dialog.py`, the docstring of `same_source`, on 2026-09-05.</sub>

WHAT THAT COST, measured on a Windows runner six CI rounds running:
a reopened project's output group appeared to have been made from
ANOTHER dataset, so the guard that protects a kept result refused
the ordinary recovery run -- through a QMessageBox, which never
reaches the message bar, so the user meets a Generate that produces
nothing and says nothing. The same comparison decides which group a
dataset owns, whether the landing may write over a group, and
whether the resume finds a layer already open, so the fault reaches
every one of the group-unit rulings on the platform most of this
plugin's users are on.

### D-34 — topology_edits.py: _same_shape

<sub>Cut from `weavingspace_qgis/topology_edits.py`, the docstring of `_same_shape`, on 2026-09-05.</sub>

ROUNDING AREAS TO NINE DECIMAL PLACES is an ABSOLUTE tolerance, and a
unit at spacing 500 has tiles of area 62,500. Measured 2026-08-30:
asking for a manipulation on a class that does not exist still moves
every area by about 4e-5 -- the library rebuilding and re-gridding
the geometry, not an edit -- so the test called that a change and the
report never fired. That is this project's rule about magnitude being
a fixture dimension, met from the other side.

COMPARING AREAS AT ALL IS THE SECOND MISTAKE, and it survived the
first repair. `push_vertex` on this suite's own fixture moves
vertices while leaving every tile's area inside any sane tolerance --
the four tiles of laves 3.3.4.3.4 are 62,500 apiece before and after
-- so a summary statistic said "nothing happened" about an edit whose
WKT plainly differs. A statistic is not a shape: two different
polygons can share an area, and this fixture is full of tiles that
do.

AND `shapely.equals_exact` IS THE THIRD, which is the one that made
this report unreachable rather than merely noisy. It compares
COORDINATE SEQUENCES and not shapes: two rings covering identical
ground read as different the moment one of them begins at another
vertex. `transform_geometry` re-grids the unit it hands back and
restarts those rings, so on archimedean 4.8.8 -- the first design in
the catalogue that carries a topology, and therefore the one the
registered test lands on -- a manipulation aimed at a class that does
not exist moved a coordinate by FIVE HUNDRED map units while the
symmetric difference stayed at 2.4e-4. The comparison duly answered
"something changed", the report stayed silent, and the test written
to catch exactly that silence failed. (Measured 2026-08-31.)

### D-35 — topology_edits.py: apply

<sub>Cut from `weavingspace_qgis/topology_edits.py`, the docstring of `apply`, on 2026-09-05.</sub>

WHAT REBUILDING COST, measured on the two designs a topology can be
had for. It made an edit after a topology-BREAKING one impossible:
`rotate_edge` routinely leaves a design with gaps, `Topology` refuses
a design with gaps, so `build` returned None and every later edit was
refused for want of anything to aim at. Chained, the same pair
applies -- laves 3.3.4.3.4 goes to area 246,110 where rebuilding
could not go at all. And it moved the LABELS under the person: a
fresh build re-derives the classes, so "A" afterwards is not
necessarily the A they clicked, which is why the two arms disagree by
a rounding on hex-slice 3 and agree exactly on laves.
