# Hunt: what the follow starves, second pass (the categorized twin)

Direction: a step inserted before existing handlers; shape: unreachable.
Frozen copy: `$TMPDIR/weavingspace-hunt/unreach3/tree` (this hunt's own).
HEAD moved three times under this hunt -- e2976b0, 413c186, 0c13aa7,
d5aa26b. Only the last touches `dialog.py`, and what it changes is the
sibling's `_class_counts` finding, not either site below. Both findings
were RE-MEASURED at **d5aa26b** and both still hold there; line numbers
below are d5aa26b's.

A sibling hunt logged the same direction earlier today
(`hunt_unreachable_after_the_follow_2026-08-17_log.md`); its
`_class_counts` finding is not re-claimed here.

## 11:20:00  iteration 1

Read every exit downstream of `_on_layer_style_edited` and asked which
ones the 2026-08-17 embed fix reached. It reached four adoption exits
and the GRADUATED colour guard (dialog.py:6059). The CATEGORIZED twin
of that guard, dialog.py:5626-5629, returns with no embed:

    if all(expected.get(key) == colour for key, colour in actual.items()):
      return  # our own seeding, or an edit that changed nothing

Everything a dock edit can change that leaves the FILL colours alone
therefore reaches the map, the project and the .qgz and never the
GeoPackage: layer opacity, outline colour and width, legend labels,
symbol size, blend mode.

RESULT: confirmed. `p1_cat_embed.py` -- one run, one graduated and one
categorized element, `setOpacity(0.25)` on each as Layer Properties
does. Project 0.25 on both; `layer_styles.styleQML` read with sqlite
says `<layerOpacity>0.25</layerOpacity>` for tiles_a and `1` for
tiles_b.

## 11:45:00  iteration 2

Second route and the healing question, `p2_cold_open.py`: open both
tables cold through QGIS with `loadDefaultStyle()`, which is what a
colleague's session does.

    COLD OPEN tiles_a: opacity=0.25  QgsGraduatedSymbolRenderer
    COLD OPEN tiles_b: opacity=1.0   QgsCategorizedSymbolRenderer

Pressing Generate first changes nothing: the project stays 0.25 on
both and the file stays 1 for tiles_b, because `_restyle_only`
continues past an element whose row never moved.

RESULT: confirmed

## 12:10:00  iteration 3

Widened it past opacity, `p3_stroke_and_reverse.py` part A: a red
1.2 mm outline and the label "Forest cover" set on one category in the
dock, fills untouched.

    A: fills unchanged? True
    A: PROJECT label0 = Forest cover  stroke = #ff0000
    A: FILE has 'Forest cover'? False   FILE has the red outline? False

and after a full Generate (`p4_file_route.py`) the file still has no
red outline while the project still has one. So this is a WRONG MAP in
the file, not only a wrong opacity.

RESULT: confirmed

## 12:35:00  iteration 4

A second defect met on the same walk, in the graduated FOLLOW branch
rather than the categorized one. `_graduated_layer_edited` builds its
trial renderer (dialog.py:6081-6085) without the row's `reverse`, though
`_current_graduated_classes` passes it (dialog.py:5253-5254). So a FORWARD
ramp installed in the dock matches a row set to REVERSE, and the
handler follows an agreement that does not exist. Part B:

    plugin drew (reversed Reds): 67000d cb1b1e fa694c fcbba2 fff5f0
    QGIS now holds             : fff5f0 fcbba2 fa694c cb1b1e 67000d
    the ROW still claims       : 67000d cb1b1e fa694c fcbba2 fff5f0
    ramp cell = Reds  Reverse switch = True  reverse = True
    said: "Element 'a' now follows the 'Reds' ramp chosen in QGIS."

Then one innocuous later edit -- asking for six classes -- redraws the
map reversed, destroying the direction set in QGIS. Read off the FILE,
cold, so no renderer object of the live session is involved:

    1. after the plugin drew it  : 67000d ... fff5f0   (reversed)
    2. after QGIS's forward Reds : fff5f0 ... 67000d   (forward)
    3. after asking for 6 classes: 67000d ... fff5f0   (reversed again)

RESULT: confirmed

## 12:50:00  iteration 5

The brief's third question: does the new `_refresh_deferring_rows()`
inside the in-flight gate fire too often during a run?
`p5_gate_frequency.py` wraps the method and counts.

    first Generate  : all 3, in flight 2
    second Generate : all 7, in flight 2   (4 elements)
    restyle-only    : all 2, in flight 0

Two per run, constant in the number of elements. The landing cannot
feed it either: `_watch_element_layer` is connected AFTER the renderer
is set, and `self._element_layer_ids` is not swapped for `new_ids`
until the loop is over (dialog.py:9848), so a mid-loop call reads the
PREVIOUS layers and returns the answer it had before the run.

RESULT: ruled out

## 13:05:00  iteration 6

Re-read HEAD before reporting. Finding A was repaired in the SHARED
WORKING TREE while this hunt ran -- uncommitted at d5aa26b, an
`embed_style` added to the categorized guard, with a comment recording
the same measurement independently. So A is confirmed twice and is
already in hand; the claim here is about committed HEAD. Finding B is
untouched in that working tree: the trial renderer still takes no
`reverse`.

RESULT: confirmed (A, independently, by somebody else's fix); B still
live.

## Ruled out, or not re-claimed

* double stamp/embed and a stale `_last_path`: the sibling hunt ruled
  both out and reading agrees -- `embed_style` writes into the LAYER'S
  own source, so the path only gates whether a file was ever written.
* `_clear_quant_customization` is still reached, through the ramp
  branch.
* `_class_counts` not written by the follow: the sibling's finding.
