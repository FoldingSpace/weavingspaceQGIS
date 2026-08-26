#!/usr/bin/env python3
"""Check that the tests would actually notice if the code broke.

Run under QGIS's own Python, from the repository root:

    QT_QPA_PLATFORM=offscreen ... <qgis python> tools/mutation_check.py
    ... tools/mutation_check.py --only chooser-race     # one mutation

A passing suite proves the code works today. It does not prove the
suite would object if someone broke the code tomorrow, and this
project has already shipped assertions that could not fail (a
one-element list "ranked", a gate test that passed equally well when
generation never ran at all). The remedy is direct: break a behaviour
on purpose, confirm the test that claims to cover it FAILS, put the
code back.

Each entry below names a real behaviour, an exact edit that defeats
it, and the test that must catch it. The catalogue is deliberately
small and hand-picked: these are the behaviours whose loss would be
expensive and quiet. Add an entry whenever a fix lands whose test you
are not certain has teeth.

Safety: the file is restored in a ``finally`` and its content is
verified byte-for-byte afterwards, so an interrupted run cannot leave
mutated source behind. Nothing is written outside the repository.
"""

import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
# where the mutating actually happens; filled in by main() with a
# throwaway copy so the project itself is never written to
BASE = [None]
DIALOG = "weavingspace_qgis/dialog.py"
BRIDGE = "weavingspace_qgis/bridge.py"
DEPS = os.path.join("weavingspace_qgis", "deps.py")
PLUGIN = "weavingspace_qgis/plugin.py"
CATALOG = "weavingspace_qgis/catalog.py"
COMPAT = "weavingspace_qgis/compat.py"
PERCEPTION = "weavingspace_qgis/perception.py"
EDITOR = "weavingspace_qgis/category_editor.py"
WORKER = "weavingspace_qgis/worker.py"
# The painted controls -- the marked bound box and its kin.
WIDGETS = "weavingspace_qgis/widgets.py"
# the release driver: not shipped, but it decides whether a candidate
# exists at all, so its guards earn the same proof as the plugin's
RELEASE = "release.py"
# the incremental mutation guard: it runs on somebody else's machine
# and reports rather than gates, so its ONE safeguard against
# answering a question it could not look at earns a proof too
MUTATE_AUTO = "tools/mutate_auto.py"
# the ONE part of the vendored library that is ours: the
# patch making matplotlib and scipy optional
VENDOR_TILEABLE = ("weavingspace_qgis/vendor/weavingspace/tileable.py")

# name, file, exact source to replace, replacement, test that must fail
MUTATIONS = [
  # Written after an automatic campaign found each gap. Every test
  # added to close a mutant belongs here, because a test verified only
  # to PASS proves nothing: six were written in one session, all
  # passing, and most then failed to kill the very mutants they were
  # written for. These entries are how that cannot happen quietly
  # again.
  # ---- this round's defects, each undone here so its test is proved
  dict(name="a-data-tab-change-never-rebuilds-the-table", file=DIALOG,
       # ANCHORED ON THE COMMENT, and it took two goes. The two lines
       # alone match TWO sites five lines apart -- `changed`, on
       # currentIndexChanged, and `picked`, on activated -- and the
       # tool rightly refused the ambiguous anchor. Narrowing it to
       # the SECOND site then SURVIVED, because setCurrentText emits
       # currentIndexChanged and never activated, so the test drives
       # the first. Which twin a test actually reaches is not a detail:
       # anchoring the wrong one certifies nothing while looking
       # exactly like a guard.
       old="""        # reselected anew", settled 2026-08-09)
        self._clear_category_colours(tid, "a new colour ramp")
        self._clear_quant_customization(tid, "a new colour ramp")
      self._refresh_preview_colours()""",
       new="""        # reselected anew", settled 2026-08-09)
        self._clear_category_colours(tid, "a new colour ramp")
        self._clear_quant_customization(tid, "a new colour ramp")
      self._rebuild_unit()""",
       test="test_palette_pick_survives_debounce",
       why="a rebuild replaces every cell widget in the table, so one "
           "debounced from a ramp pick lands mid-interaction with the "
           "next: open dropdowns die and a pick commits to a dead "
           "widget. Data-tab handlers repaint, they never rebuild -- "
           "and the test had no catalogue entry until 2026-08-15, so "
           "nothing had ever proved it could fail"),
  dict(name="a-ramp-reclick-never-rebuilds-the-table", file=DIALOG,
       # THE TWIN, anchored separately, which is the rule: a single
       # entry covering both handlers would report caught on the
       # strength of whichever one the test happens to drive. This one
       # SURVIVED when it was written on 2026-08-15, because the test
       # reached only the currentIndexChanged handler; it is here
       # because the test was then extended to send `activated`, which
       # is what a real click sends.
       old="""      if not c.showing_custom():
        return
      tid = c.property("tile_id")
      if tid:
        self._clear_category_colours(tid, "a new colour ramp")
        self._clear_quant_customization(tid, "a new colour ramp")
      self._refresh_preview_colours()""",
       new="""      if not c.showing_custom():
        return
      tid = c.property("tile_id")
      if tid:
        self._clear_category_colours(tid, "a new colour ramp")
        self._clear_quant_customization(tid, "a new colour ramp")
      self._rebuild_unit()""",
       test="test_palette_pick_survives_debounce",
       why="re-choosing the ramp already showing on a Custom row fires "
           "activated and NOT currentIndexChanged, so this handler is "
           "the only one that runs; a rebuild here replaces every cell "
           "widget while the user is still working the table"),
  dict(name="a-retyped-break-never-reaches-the-record", file=DIALOG,
       # ANCHORED ON THE CALL, not on the helper's body: what is at
       # stake is that the adoption RUNS at all, and it must run
       # before the colour comparison below, since an edit that moved
       # only the numbers changes no colour and reaches none of the
       # exits under it. Mutating inside the helper would prove some
       # detail of how a ladder is recorded while leaving the actual
       # defect -- nothing recorded, ever -- unguarded.
       old="""        self._adopt_dock_bounds(
          tile_id, assignment,
          [(r.lowerValue(), r.upperValue()) for r in live], actual)""",
       new="""        pass  # adoption removed""",
       test="test_a_break_retyped_in_qgis_reaches_the_plugin",
       why="this is rc8 exactly: every reader of a graduated element "
           "-- the table, the colour editor, the swatch -- goes "
           "through _current_graduated_classes, which REBUILDS a "
           "renderer from the dialog's record and never reads the "
           "layer's ranges. So a break retyped by hand in QGIS's "
           "Symbology panel exists only in that layer's renderer and "
           "is invisible everywhere, whatever QGIS is holding. The "
           "tester reported it as 'regardless of HOW I do it, changes "
           "to the Q symbology are not reflected in the plugin', "
           "which was exact: colour had an adoption path into the "
           "record and the bounds had none, so every route ended at "
           "the same missing one"),
  dict(name="a-coverage-spacing-never-follows-the-locale", file=BRIDGE,
       # ANCHORED ON THE CONVERSION, not on the rstrip beside it: the
       # trimming is the same in either version and a mutation of it
       # would prove the trimming, which is not what this guards. What
       # is at stake is WHOSE punctuation the number carries.
       old="""  text = locale.toString(float(value), 'f', 6)""",
       new="""  text = "{:,.6f}".format(float(value))""",
       test="test_a_coverage_notice_quotes_a_spacing_the_box_accepts",
       why="this is the hand-built formatting the fix replaced, and "
           "it is invisible in English: a full stop for the point and "
           "a comma for grouping is what a reader here expects, so "
           "every test that pins a spelling passes. On a "
           "comma-decimal QGIS the sentence then says 500.5 and the "
           "spacing box beside it reads 5005, so a user who types the "
           "number the plugin just showed gets a map ten times "
           "coarser. The same mutation reached the class bounds and "
           "the size-guard refusal and was repaired in both on "
           "2026-08-17; these two sentences were named as the "
           "remainder and missed"),
  dict(name="a-scale-of-zero-is-never-reachable", file=DIALOG,
       old="""    if value != 0:
      self._last_scale[box] = value
      return""",
       new="""    if True:
      self._last_scale[box] = value
      return""",
       test="test_a_scale_control_steps_over_zero",
       why="a scale of zero collapses the tile unit to no area, and "
           "the library does not refuse it -- it returns the "
           "degenerate unit and fails much later inside Tiling as a "
           "singular matrix, reaching the user as a raw traceback "
           "about a matrix they never asked about. Zero became "
           "reachable the day negative scales were allowed"),
  dict(name="a-blank-a-failure-imposed-is-not-a-choice", file=DIALOG,
       old="      elif prev is not None and prev[\"var\"] is None \\\n"
           "          and not self._fieldless_build:",
       new="      elif prev is not None and prev[\"var\"] is None:",
       test="test_a_project_whose_region_layer_has_moved",
       why="a table built with no fields on offer leaves every row "
           "blank, and honouring those blanks as deliberate is how a "
           "plugin opened before its data refuses to draw and blames "
           "the user; the same road reaches a region layer whose file "
           "has gone, where recovery must assign rather than stay "
           "blank (maintainer's decision, 2026-08-15)"),
  dict(name="a-named-ramp-does-not-prove-the-ramp-decides", file=DIALOG,
       old="""      expected = bridge.quant_class_colours(
        named, flipped, len(bands),
        tuple(self._ramp_ranges.get(tile_id, (0, 100))))""",
       new="""      expected = None""",
       test="test_a_graduated_dock_recolour_survives_the_plugin_being_shut",
       why="reading an adopted layer back has to ask whether the ramp "
           "EXPLAINS the colours drawn, not merely whether a ramp is "
           "named; QGIS keeps the source ramp on a renderer whose "
           "classes have been recoloured by hand, so without this the "
           "row believes the ramp is the whole story and the next "
           "Generate repaints over the user's choice"),
  dict(name="the-live-dialog-record-is-cleared-on-destruction",
       file=DIALOG,
       old="""    dialog.destroyed.connect(
      lambda *_ignored, t=token: _forget_live_dialog(t))""",
       new="""    pass""",
       test="test_a_destroyed_dialog_cannot_be_reached_by_a_layer_it_made",
       why="the record is parked on the QApplication so it survives a "
           "plugin reload, and nothing else clears it; left dangling, "
           "merely READING the property segfaults QGIS, so it has to "
           "be dropped while the dialog is still alive enough to say "
           "so"),
  dict(name="a-dead-dialog-answers-no-signal", file=DIALOG,
       old="""    if _dialog_is_gone(self):""",
       new="""    if False:""",
       test="test_a_destroyed_dialog_cannot_be_reached_by_a_layer_it_made",
       why="Qt disconnects a bound method when its receiver dies but "
           "keeps calling a LAMBDA, and an element layer outlives the "
           "dialog that made it; without this guard the styleChanged "
           "handler runs on a destroyed dialog, reaches a deleted "
           "QTableWidget and takes QGIS down with it"),
  dict(name="a-missing-value-is-drawn-not-left-as-a-hole", file=BRIDGE,
       # RE-ANCHORED 2026-08-16: the predicate widened from "missing"
       # to "the classifier cannot place this", so the isna() line
       # gained an infinity term beside it and this entry stood on
       # text that no longer existed. Anchored on the union now, which
       # is the line that actually decides what leaves the element.
       old="""  missing = missing | infinite""",
       new="""  missing = (missing | infinite) & False""",
       test="test_an_area_with_no_value_is_drawn_rather_than_left_as_a_hole",
       why="QgsGraduatedSymbolRenderer has no class for a NULL -- no "
           "default, no-data, else or fallback symbol in its whole "
           "public API -- so an unsplit frame leaves those tiles "
           "unpainted, and on a map made of areas a hole reads as "
           "'nothing is here' rather than 'this is not known'"),
  dict(name="the-no-data-row-is-not-the-last-class", file=EDITOR,
       # RE-ANCHORED 2026-08-16: the paired layer gained a row per
       # KIND of unplaceable value, so the trailing absence rows are
       # counted in a loop rather than tested one deep.
       old="""    self._last_class_row = len(order) - 1
    while self._last_class_row >= 0 \\
        and order[self._last_class_row] in absence_keys:
      self._last_class_row -= 1""",
       new="""    self._last_class_row = len(order) - 1""",
       test="test_a_class_that_cannot_be_pinned_says_so_in_its_cell",
       why="a no-data row sits below the classes, so reading 'last "
           "row' as 'last class' hands the high pin to a row that "
           "has no bound to pin and leaves the real last class "
           "unpinnable"),
  dict(name="the-removal-notice-does-not-depend-on-handler-order",
       file=DIALOG,
       old="""    lost = pending or self._watched_layer_id""",
       new="""    lost = self._watched_layer_id""",
       test="test_the_removal_notice_survives_the_chooser_moving_first",
       why="QgsMapLayerComboBox emits layerChanged when the project "
           "churns and with two polygon layers quietly selects the "
           "survivor; if that handler runs first the watched id has "
           "already moved, so without the id recorded before the "
           "removal the dialog says nothing -- which passed on the "
           "development Mac and failed on all three CI runners"),
  dict(name="a-negative-scale-mirrors-in-Y-too", file=DIALOG,
       old="""        self.mod_scale_x.value(), self.mod_scale_y.value(),""",
       new="""        self.mod_scale_x.value(), abs(self.mod_scale_y.value()),""",
       test="test_a_negative_scale_factor_mirrors_the_design",
       why="x and y are two controls reaching two arguments, and the "
           "entry beside this one mutates both at once, so it is "
           "caught by a test that drives x alone; this one mutates Y "
           "ONLY and therefore survives unless the other axis is "
           "genuinely exercised -- the twin problem this project has "
           "paid for on three other pairs"),
  dict(name="a-negative-scale-mirrors-rather-than-clamps", file=DIALOG,
       old="""      unit = unit.transform_scale(
        self.mod_scale_x.value(), self.mod_scale_y.value(),""",
       new="""      unit = unit.transform_scale(
        abs(self.mod_scale_x.value()), abs(self.mod_scale_y.value()),""",
       test="test_a_negative_scale_factor_mirrors_the_design",
       why="the sign is what mirrors the design about that axis and "
           "the magnitude is what scales it; taking the absolute "
           "value leaves a control that reaches negative numbers and "
           "a map that ignores them, which is worse than not "
           "offering them"),
  dict(name="both-halves-of-an-element-fade-together", file=DIALOG,
       old="""    layer.setOpacity(hand_opacity if hand_opacity is not None else
                     max(0, min(100, assignment.get("opacity", 100))) / 100.0)""",
       new="""    pass  # mutation: the paired half keeps full strength""",
       test="test_both_halves_of_an_element_fade_together",
       why="an element is one thing to a reader however many layers "
           "it is; without this the creating path leaves the "
           "missing-value areas opaque on an element faded to 40%, "
           "so they become the hardest shapes on the map and hide "
           "what lies beneath, until an unrelated restyle silently "
           "corrects it"),
  dict(name="the-no-data-split-is-geometry-not-style", file=DIALOG,
       # RE-ANCHORED 2026-08-19, when the term gained the limits as
       # VALUES, and again on 2026-08-25 when it gained the element's
       # own variable: every entry standing on this tuple moves with
       # it, which is what a shared anchor costs.
       old="""      tuple((a["id"], a.get("var"), self._needs_a_no_data_split(a),
             self._limits_key(a))
            for a in self._assignments()),""",
       new="""      (),""",
       test="test_changing_to_a_graduated_style_cuts_the_split_it_needs",
       why="only a full run can cut the split; the restyle path "
           "repaints a paired layer that exists and can neither make "
           "nor unmake one, so without this term a mode change or a "
           "variable swap is answered in place and the holes the "
           "feature exists to remove come back"),
  dict(name="a-paired-layer-is-not-its-element", file=DIALOG,
       old="""      if tid and layer.customProperty("weavingspace_no_data"):
        self._no_data_layer_ids[str(tid)] = layer.id()
      elif tid:""",
       new="""      if tid:""",
       test="test_a_reopened_plugin_does_not_mistake_a_no_data_layer_for_its_element",
       why="the paired layer carries its element's tile id, so "
           "adoption keyed on that id alone lets the twin overwrite "
           "the element; the next run then removes the twin and "
           "orphans the real layer, leaving yesterday's map on top "
           "of the new one for good"),
  dict(name="a-kept-result-keeps-both-its-halves", file=DIALOG,
       old="""    self._element_layer_ids = {}
    self._no_data_layer_ids = {}""",
       new="""    self._element_layer_ids = {}""",
       test="test_keeping_a_result_keeps_both_halves_of_every_element",
       why="three places clear per-element state and no two cleared "
           "the same set; without this the record goes on naming the "
           "KEPT group's no-data layers and the next run removes "
           "them, punching holes in the map the user asked to keep"),
  dict(name="the-file-gets-the-opacity-the-map-has", file=DIALOG,
       old="""    if path:
      bridge.embed_style(layer)
    project.addMapLayer(layer, False)""",
       new="""    if path:
      # mutation: what the FILE is told, before it is told it
      layer.setOpacity(1.0)
      bridge.embed_style(layer)
    project.addMapLayer(layer, False)""",
       test="test_a_geopackage_carries_the_no_data_opacity_it_was_given",
       why="embed_style writes what the layer wears at that moment, "
           "so an opacity set afterwards reaches the project and not "
           "the file, and the map a user sends on draws its "
           "missing-value areas opaque over a faded element"),
  # `the-split-term-carries-the-field` STOOD HERE AND WAS DELETED ON
  # 2026-08-25, WITH THE CODE IT GUARDED. It proved that the split
  # term carried the FIELD rather than a yes/no, because a boolean per
  # element is INVARIANT UNDER A PERMUTATION -- swap two elements'
  # variables and every boolean stays True. That was true until the
  # signature gained the element's own VARIABLE as a term of its own,
  # which it had to when ruling 6 trimmed each element table to the
  # column it displays. With the variable carried directly, a
  # permutation is visible whatever the split term says, so the entry
  # could only ever SURVIVE.
  #
  # The honest answer was to simplify rather than to defend: the term
  # is `_needs_a_no_data_split(a)` again, a plain boolean, and
  # `(id, var, bool, limits)` carries exactly what
  # `(id, var, field-or-None, limits)` did. Same shape as the
  # `_deriving_spacing` deletion earlier the same day -- when an entry
  # survives, ask whether the behaviour has two implementations before
  # asking whether the test is weak.
  dict(name="a-sign-guard-is-not-a-finiteness-guard", file=EDITOR,
       old="""    places = (9 - int(math.floor(math.log10(span)))
              if math.isfinite(span) and span > 0 else 6)""",
       new="""    places = 9 - int(math.floor(math.log10(span))) if span > 0 else 6""",
       test="test_the_colour_editor_opens_on_a_column_with_no_values",
       why="a column with no usable values gives Unclassed fifty "
           "classes spanning the whole float range, so the span is "
           "INFINITE and `span > 0` is true of it; log10 then "
           "overflows and the OverflowError escapes through a Qt "
           "slot, leaving Edit colours doing nothing and QGIS "
           "showing a Python error window"),
  dict(name="an-element-on-missing-values-is-still-split", file=BRIDGE,
       old="""  if bool(missing.all()) and not column_has_values:""",
       new="""  if bool(missing.all()):""",
       test="test_an_element_sitting_wholly_on_missing_values_still_draws",
       why="the split is decided per ELEMENT, so all-missing can be "
           "true of one element while the column has values "
           "elsewhere; without the column question that element "
           "keeps breaks cut from the whole map, matches none of "
           "them and is absent while its siblings draw"),
  dict(name="nothing-to-classify-draws-as-no-data", file=BRIDGE,
       old="""  elif not _anything_to_classify(layer, var):""",
       new="""  elif False:""",
       test="test_a_column_with_no_values_at_all_invents_no_class",
       why="a graduated renderer over a column with no usable values "
           "has zero ranges, so every tile gets no symbol and the "
           "element vanishes while the row shows a swatch and a "
           "class count and the bar says it draws as no data "
           "(maintainer's decision, 2026-08-16)"),
  dict(name="the-third-clear-site-clears-it-too", file=DIALOG,
       old="""    for record in (self._element_layer_ids, self._no_data_layer_ids,
                   self._last_signatures,""",
       new="""    for record in (self._element_layer_ids,
                   self._last_signatures,""",
       test="test_a_project_opened_under_an_open_dialog_keeps_its_no_data_layers",
       why="a project replaced under an open dialog leaves these ids "
           "behind, and a .qgz restores layers under the SAME ids, so "
           "the incoming project's no-data layers are deleted by the "
           "next Generate as though they were the last project's"),
  dict(name="a-replaced-project-is-not-drawn-over", file=DIALOG,
       # RE-ANCHORED 2026-08-16: the adopted-group record was added
       # between the second and third lines, so the old three-line
       # anchor matched nothing and this entry had gone silent --
       # which reads exactly like success. Anchored on the two lines
       # that carry the defect it names.
       old="""    self._group_name = None
    self._last_path = None""",
       new="""    pass""",
       test="test_a_project_opened_under_an_open_dialog_is_not_drawn_over",
       why="a project replaced under an OPEN dialog left the old "
           "group name and output path behind, so the dialog adopted "
           "a group in the incoming project without the ids that say "
           "what is in it and never rebuilt it either; the next "
           "Generate then drew alongside what was there and the map "
           "was two tilings at once, the stale one on top"),
  dict(name="unclassed-is-exempt-from-the-reduction", file=BRIDGE,
       old="""  if unclassed:
    return int(asked), False""",
       new="""  if False:
    return int(asked), False""",
       test="test_unclassed_never_announces_a_reduction",
       why="Unclassed reproduces a continuous ramp, so its fifty steps "
           "are the shape of the reproduction and make_graduated_"
           "renderer does not reduce them; without this guard the "
           "message bar announces a reduction the map never performs, "
           "which is the one thing these notices exist to prevent"),
  dict(name="the-file-not-the-memory-decides-an-overwrite", file=DIALOG,
       # RE-ANCHORED 2026-08-25: the names this run would write are
       # built by `element_table_name` now, because they carry the
       # displayed variable. The claim is unchanged -- the FILE
       # decides whether a run would overwrite, not this session's
       # memory -- and emptying the answer is still how it fails.
       old="""      would_replace = bridge.gpkg_tables_we_would_replace(path_now, planned)""",
       new="""      would_replace = []  # mutation: ask the file nothing""",
       # ONE LITERAL, however long: the standards check reads an
       # entry's test name from its FIRST string, so a name split
       # across two lines is read as a test that does not exist.
       test="test_a_reopened_project_cannot_overwrite_yesterdays_geopackage",
       why="the overwrite guard used to compare against _last_path, "
           "which records only what THIS dialog instance wrote, so a "
           "reopened project ticking 'create as new group' to KEEP "
           "yesterday's map destroyed it without a warning. A file "
           "outlives a session and session state cannot protect one"),
  dict(name="a-replaced-region-layer-is-announced", file=DIALOG,
       old="""    survivor = self.layer_combo.currentLayer()
    if survivor is not None:
      self._report_quietly(""",
       new="""    survivor = self.layer_combo.currentLayer()
    if False:
      self._report_quietly(""",
       test="test_removing_the_region_layer_is_noticed_in_a_real_project",
       why="with a survivor present the dialog FOLLOWS the removal, so "
           "the map moves to different ground with different variables "
           "and looks perfectly fine; the notice in _on_layer_changed "
           "fires only when the chooser is left holding nothing, which "
           "is the one-layer case. Silence here is a wrong map rather "
           "than a missing one"),
  dict(name="region-removal-heard-from-the-project", file=DIALOG,
       old="    QgsProject.instance().layersRemoved.connect(self._layers_removed)",
       new="    pass    # mutated: rely on the combo alone",
       test="test_removing_the_region_layer_is_noticed_in_a_real_project",
       why="QgsMapLayerComboBox does not emit layerChanged when the "
           "chosen layer is destroyed in a project holding three or "
           "more polygon layers, so without the project's own signal "
           "the dialog goes on believing in a layer QGIS has deleted, "
           "says nothing, and Generate produces no map and no refusal"),
  dict(name="consent-names-the-destination", file=PLUGIN,
       old='    f"      {deps.LIBS_DIR}\\n"',
       new='    "      a folder belonging to this plugin\\n"',
       test="test_the_dependency_consent_says_what_it_will_do",
       why="the consent dialogue must name the exact folder the "
           "downloaded packages land in, derived from where the "
           "plugin is installed; 'a folder belonging to this plugin' "
           "is a promise the reader cannot check"),
  dict(name="consent-safe-default", file=PLUGIN,
       old="  box.setDefaultButton(box.buttons()[-1])",
       new="  box.setDefaultButton(approve)",
       test="test_the_dependency_consent_says_what_it_will_do",
       why="the SAFE button is the default, so that Return on a "
           "dialogue nobody has read cannot start downloading and "
           "unpacking code"),
  dict(name="nulls-excluded-from-breaks", file=BRIDGE,
       old='    if source.setSubsetString(combined):\n      restore = previous',
       new='    if False:  # mutation: classify the nulls along with the data\n      restore = previous',
       test="test_class_breaks_ignore_nulls",
       why="QGIS counts a NULL as zero when it computes class breaks, "
           "so a column with gaps gets a spurious 0-0 class and every "
           "break shifted; the map is wrong everywhere and nothing on "
           "screen says so"),
  dict(name="output-crs-invented", file=BRIDGE,
       old="""  if gdf.crs is None:""",
       new="""  if False:  # mutation: let QGIS default the output to EPSG:4326""",
       test="test_hostile_numbers_are_handled_or_declined",
       why="a region layer with no CRS must not have one invented for "
           "its output; a memory layer whose URI names no CRS is given "
           "EPSG:4326 by QGIS, which ships coordinates in the "
           "thousands labelled as degrees"),
  dict(name="quant-style-on-text", file=DIALOG,
       old="""      if mode == "Graduated" and var and not self._field_is_numeric(var):""",
       new="""      if False:  # mutation: let a graduated style stand on text""",
       test="test_a_quantitative_style_never_stands_on_text",
       why="a graduated renderer over words has no ranges at all, so "
           "every tile falls outside every class and four full layers "
           "paint an empty map while the run reports success"),
  # Re-anchored 2026-08-10: the one pass over the column now answers
  # two questions at once, so the constancy test has moved up into a
  # `constant` local and this gate merely reads it. Mutating the GATE
  # rather than the local keeps this entry aimed at the class count
  # alone; the ramp-midpoint behaviour that shares the local has its
  # own entry (constant-class-takes-ramp-start).
  dict(name="constant-column-classes", file=BRIDGE,
       # RE-ANCHORED 2026-08-16: the general reduction was removed, so
       # the `elif` this stood on is gone and only the one-value
       # carve-out remains. It is load-bearing on its own again, which
       # is why one branch is now enough where two were needed.
       old='  if distinct == 1 and not pinned_here:',
              new='  if False:  # mutation: never collapse a constant column',
              test="test_a_constant_column_draws_one_class_and_says_so",
       why='a column that is 7 everywhere gets five classes all reading 7 - 7 in five colours, a legend showing variation the data does not have. From 2026-08-14 to 2026-08-16 a second branch reduced k generally and delivered the same k=1 by another route, so this entry had to mutate both and said so; that branch is gone and this one stands alone.'),
  # TWO entries, because there are two signatures and they gate
  # different paths: _geometry_signature decides whether pressing
  # Generate re-tiles or merely repaints, and _run_signature decides
  # whether a live update runs at all. One entry pointed at the wrong
  # one survived, which is the failure this file is for.
  dict(name="fingerprint-in-geometry-signature", file=DIALOG,
       # ANCHORED ON THE COMMENT ABOVE, not on the def below. Both
       # fingerprint entries used to disambiguate themselves by the
       # method that happened to follow, so adding a method anywhere
       # between the signature and `_restyle_only` silently orphaned
       # them; three arrived on 2026-08-16 and the standards check
       # caught it. Preceding context cannot be displaced by an
       # insertion in the same way.
       old="""      # demand and never marked as out of date.
      self._layer_fingerprint(), self._data_version,""",
       new="""      # demand and never marked as out of date.""",
       test="test_data_changed_in_qgis_while_the_plugin_is_open",
       why="without the layer's CONTENTS here, deleting half the "
           "features leaves every term identical, so pressing Generate "
           "is answered by repainting tiles built from data that no "
           "longer exists"),
  dict(name="fingerprint-in-run-signature", file=DIALOG,
       old="""      # not look like one.
      self._layer_fingerprint(), self._data_version,""",
       new="""      # not look like one.""",
       test="test_live_update_notices_the_data_changing",
       why="without it, live update compares two identical signatures "
           "after an edit and skips the run as a no-op, so a user "
           "watching the map sees it stop following their work"),
  dict(name="dead-layer-guard", file=DIALOG,
       old="""    if not compat.layer_data_is_available(layer):
      # The source is gone -- a deleted file, a dropped connection.""",
       new="""    if False:  # mutation: question a layer whose source has gone
      # The source is gone -- a deleted file, a dropped connection.""",
       test="test_qgis_changes_around_the_plugin",
       why="extent() on a layer whose file has been deleted segfaults "
           "QGIS outright: no exception, no traceback, nothing in the "
           "log. isValid() returns True and lies"),
  dict(name="an-in-place-edit-is-heard-through-its-repaint",
       file=DIALOG,
       old="""    layer.repaintRequested.connect(
      lambda *args, lid=layer.id(), tid=str(tile_id):
        self._queue_repaint_reconcile(lid, tid))""",
       new="""    pass  # mutation: only setRenderer edits are heard""",
       test="test_an_in_place_recolour_is_heard_through_its_repaint",
       why="recolouring a class IN PLACE emits no styleChanged and no "
           "rendererChanged (measured, QGIS 4.0.3); the repaint the "
           "dock asks for afterwards is the only audible trace. "
           "Without this connection the map follows the edit and the "
           "plugin never learns -- a maintainer met exactly that, "
           "three times over two days"),
  dict(name="a-heard-edits-echo-is-not-handled-twice", file=DIALOG,
       old="""    if time.monotonic() - self._style_signal_at.get(str(tile_id),
                                                    -1e9) < 1.0:""",
       new="""    if time.monotonic() - self._style_signal_at.get(str(tile_id),
                                                    -1e9) < 0.0:""",
       test="test_an_in_place_recolour_is_heard_through_its_repaint",
       why="a setRenderer edit emits styleChanged AND asks for a "
           "repaint. Handled once at the signal and again at the "
           "drain, the second pass runs after the row has followed "
           "the new class count, so anything that reasoned from the "
           "row rather than from what the plugin PAINTED read the "
           "second pass as a fresh edit and adopted the displaced "
           "ladder the first pass rightly declined"),
  dict(name="a-ladder-may-hold-two-classes-at-one-bound", file=DIALOG,
       old="""    if at_these_bounds:
      return here in at_these_bounds""",
       new="""    if at_these_bounds:
      return here == at_these_bounds[0]  # mutation: first match only""",
       test="test_a_second_reconciliation_adopts_no_colour_the_plugin_painted",
       why="a ladder may hold SEVERAL classes with identical bounds -- a "
           "constant column, a tied column, {1,5,9} at k=5 -- and QGIS's "
           "addClass inserts a degenerate (0.0, 0.0) class that collides "
           "with a first real class of the same bounds. Stopping at the "
           "first match compares the plugin's own colour against the "
           "placeholder grey sharing those bounds, calls it changed, and "
           "adopts it. Measured 2026-08-20 against this function's own "
           "first draft, which four passing tests did not see"),
  dict(name="an-unknown-ladder-is-not-an-unchanged-one", file=DIALOG,
       old="""    known = (self._painted_ladders.get(tile_id) or {}).get(field)
    if not known:
      return None""",
       new="""    known = (self._painted_ladders.get(tile_id) or {}).get(field)
    if not known:
      return False  # mutation: absent means theirs""",
       test="test_a_colour_on_a_ladder_we_never_saw_is_declined_and_named",
       why="an ABSENT record means the plugin has never seen this "
           "element's ladder, which is not the same as the ladder not "
           "having moved. Reading it as 'theirs' records the whole "
           "ladder as somebody's hand-picks; reading it as 'ours' "
           "throws away every real pick. The previous day's defect in "
           "this same family was a guard reading a deliberately-empty "
           "record as evidence of CHANGE, and this is that mistake "
           "mirrored"),
  dict(name="a-reclassification-adopts-no-colour", file=DIALOG,
       # RE-ANCHORED 2026-08-20, the second time in one day. The first
       # re-anchoring stood on `if not count_moved:`, a DELTA armed for
       # one invocation; that flag is gone and the question is now
       # asked of `_painted_ladders`, which can answer at any moment.
       # Mutating the "this colour is ours" arm makes every colour the
       # plugin itself painted read as somebody's hand-pick.
       old="""      if ours:
        continue
      if record.get(str(index)) != colour:""",
       new="""      if False:  # mutation: adopt the plugin's own colours
        continue
      if record.get(str(index)) != colour:""",
       test="test_a_class_added_in_qgis_is_not_a_colour_somebody_picked",
       why="QGIS inserts the added class and every OTHER class keeps "
           "the colour it had, at a new index -- so a positional walk "
           "sees the plugin's own earlier ramp sampling displaced by "
           "one and adopts the lot. Measured from a maintainer's dump: "
           "adding a class to a five-class Reds element adopted FOUR "
           "colours nobody chose, after which the ramp could never "
           "govern those classes again"),
  dict(name="a-cloned-template-is-not-a-hand-pick", file=DIALOG,
       # RE-ANCHORED TWICE ON 2026-08-20. First the walk moved a level
       # in under `if not count_moved:`; then that flag was deleted and
       # the walk was rewritten to iterate the renderer's own ranges,
       # so the indentation moved back out and `expected[index]` is no
       # longer read at all. Anchored now on the template check itself.
       old="""      if colour == template:
        continue
      ours = self._colour_is_ours(""",
       new="""      ours = self._colour_is_ours(""",
       test="test_a_class_added_in_qgis_is_not_a_colour_somebody_picked",
       why="QGIS clones the renderer's source symbol for a class the "
           "user ADDS in the Symbology panel, and this plugin sets "
           "that symbol to a placeholder grey -- measured on QGIS "
           "4.0.3, the new class lands at index 0 wearing #c0c0c0. "
           "Adopting it records the plugin's own placeholder as a "
           "colour somebody chose, and the element then defends that "
           "grey against its own ramp for good"),
  dict(name="a-moved-file-is-not-available-data", file=COMPAT,
       # RE-ANCHORED 2026-08-20: the request now declines the geometry
       # too, measured at 1.94 ms against 0.075 ms on a 200k-vertex
       # first feature.
       old="""    if layer.featureCount() > 0:
      request = QgsFeatureRequest()
      request.setLimit(1)
      request.setNoAttributes()
      request.setFlags(QgsFeatureRequest.Flag.NoGeometry)
      return next(layer.getFeatures(request), None) is not None
    return True""",
       new="""    return True  # mutation: believe the provider's stale yes""",
       test="test_a_layer_whose_file_moved_is_refused_before_it_is_read",
       why="a GeoPackage whose file moves under an open layer goes on "
           "reporting isValid True, a valid provider and its last good "
           "feature count, while getFeatures yields nothing. Believing "
           "those answers sends the run on to layer_to_gdf, which "
           "refuses in terms of the user's DATA when the fact is that "
           "their FILE has moved"),
  dict(name="an-absent-signature-is-not-a-moved-row", file=DIALOG,
       old="""        recorded = self._last_signatures.get(tile_id)
        if recorded is not None and self._signature(assignment) != recorded:""",
       new="""        if self._signature(assignment) != self._last_signatures.get(
            tile_id):  # mutation: absent reads as moved""",
       test="test_a_reopened_project_still_hears_a_recolour_made_in_qgis",
       why="`_adopt_existing_group` leaves `_last_signatures` EMPTY on "
           "purpose, because a dialog cannot know which assignments "
           "produced layers it has only just met. Asked with `.get()` "
           "alone, None never equals a real signature, so the repaint "
           "route -- the only way an in-place dock recolour reaches "
           "the plugin -- is shut in every REOPENED project, which is "
           "the commonest journey there is. Ledger row 1"),
  dict(name="the-copy-row-is-built-for-categorical-elements-too", file=EDITOR,
       old="""    if copy_targets and copy_to is not None:
      self._build_copy_row(layout, copy_targets, copy_to)""",
       new="""    if bounds is not None and copy_targets and copy_to is not None:
      self._build_copy_row(layout, copy_targets, copy_to)""",
       test="test_a_categorical_scheme_copies_onto_another_element",
       why="`bounds` are the GRADUATED class bounds, so gating the "
           "Copy row on them kept the control off the categorical half "
           "of the editor entirely -- which is how a tester came to "
           "report categorical copying as simply missing"),
  dict(name="a-copy-asks-before-a-colour-per-value", file=DIALOG,
       old="""      if count is not None and count > bridge.MANY_CATEGORIES \\
          and not self._many_categories_is_wanted(their_field, count):""",
       new="""      if False:  # mutation: draw a swatch per value, unasked""",
       test="test_a_copy_asks_before_drawing_a_colour_for_every_value",
       why="nothing caps the category count -- bridge takes "
           "`n = max(len(everywhere), 1)` -- so a categorical scheme "
           "copied onto a CONTINUOUS column is drawn with one class, "
           "one legend line and one swatch per value. On real data "
           "that is thousands, and the user finds out by watching QGIS "
           "do it. The maintainer ruled it a question rather than a "
           "refusal, on one threshold shared with the dataset switch"),
  dict(name="keep-by-name-is-what-a-switch-keeps", file=DIALOG,
       old="""      if prev and prev["var"] in fields:
        var_combo.setCurrentText(prev["var"])""",
       new="""      if False:  # mutation: keep nothing by name
        var_combo.setCurrentText(prev["var"])""",
       test="test_a_dataset_switch_keeps_its_promises_on_every_route",
       why="keep-by-name is the rule every other switch ruling is an "
           "exception TO, and it had no entry of its own: an element "
           "keeps its variable where the new data has a column of "
           "that name. The matrix's same-schema cells are the guard, "
           "which is fitting -- the matrix exists because journeys "
           "tested one axis each"),
  dict(name="orphan-records-belong-to-the-first-dataset-chosen",
       file=DIALOG,
       old="""      for name, store in outgoing.items():
        target = bank[name]
        for tid, fields in store.items():
          target.setdefault(tid, {}).update(fields)""",
       new="""      pass  # mutation: discard what adoption wrote before the swap""",
       test="test_a_saved_project_brings_back_its_colours",
       why="a reopened project's adoption reads the stamps into the "
           "views before the chooser settles; rebinding to a fresh "
           "bank without this merge silently discarded everything a "
           "saved project carried. Eleven round-trip tests went red on "
           "the banks' first full suite, every one with an empty "
           "record -- the gate doing what a targeted run cannot"),
  dict(name="value-laden-records-never-cross-a-shared-name", file=DIALOG,
       old="""    self._category_colours = bank["colours"]
    self._pinned_bounds = bank["pins"]""",
       new="""    bank["colours"].update(outgoing["colours"])
    self._category_colours = bank["colours"]  # mutation: reintroduce the carve, wholesale
    self._pinned_bounds = bank["pins"]""",
       test="test_value_laden_records_never_cross_a_shared_name",
       why="the wrong implementation somebody would plausibly write: "
           "carry the colours across the swap. Hand-picks are keyed by "
           "VALUE STRINGS and the landing stamp writes them into the "
           "new dataset's files, which is the confidential-values leak "
           "the maintainer named when they ended the carve"),
  dict(name="the-banks-swap-on-a-change-of-layer", file=DIALOG,
       old="""    new_id = layer.id()
    old_id = self._memory_layer_id
    if old_id == new_id:
      return""",
       new="""    new_id = layer.id()
    old_id = self._memory_layer_id
    if True:  # mutation: never swap
      return""",
       test="test_one_datasets_memory_never_steers_another",
       why="without the swap the field-keyed memory is one pool keyed "
           "by bare column names, so a scheme, its value strings and "
           "its pinned numbers made on one dataset reactivate on any "
           "later dataset sharing a name -- the leakage the "
           "maintainer's ruling of 2026-08-24 forbids"),
  dict(name="a-dropped-scheme-files-under-its-own-dataset", file=DIALOG,
       old="""    shelf = (self._pending_outgoing_shelf
             if self._pending_outgoing_shelf is not None
             else self._scheme_memory)""",
       new="""    shelf = self._scheme_memory  # mutation: file under the incoming""",
       test="test_a_dropped_column_takes_its_whole_scheme_and_the_shelf_returns_it",
       why="the rebuild runs AFTER the banks swapped, so without the "
           "pending pointer a dropped scheme -- column name and all -- "
           "is filed inside the INCOMING dataset's bank: A's names in "
           "B's memory, and the A-B-A journey comes home to an empty "
           "shelf"),
  dict(name="a-landing-never-writes-over-another-datasets-map",
       file=DIALOG,
       old="""      theirs = bool(stamps) and region_source not in stamps""",
       new="""      theirs = False  # mutation: write into whatever group is there""",
       test="test_a_landing_never_writes_over_another_datasets_map",
       why="ruling 2 makes a second output group the ordinary result "
           "of a demo, and adoption runs at CONSTRUCTION -- so a "
           "reopened project holding two datasets' maps adopted the "
           "newest and replaced it at the next Generate. A finished "
           "map deleted to make room for one the user already had"),
  dict(name="the-region-stamp-says-which-dataset-made-a-layer",
       file=DIALOG,
       old="""      if region_source:
        out.setCustomProperty("weavingspace_region", region_source)""",
       new="""      pass  # mutation: leave the layer silent about its dataset""",
       test="test_a_landing_never_writes_over_another_datasets_map",
       why="without the stamp nothing on a landed layer says which "
           "dataset made it, so the check above has nothing to read "
           "and the newest group is written into whatever it holds"),
  dict(name="a-dropped-columns-ramp-goes-whoever-chose-the-style",
       file=DIALOG,
       old="""      if mode_cell is not None and restored is None:
        # ...AND THE CONTROLS THEMSELVES, for EVERY row whose column""",
       new="""      if mode_cell is not None and restored is None \\
          and mode_cell.property("touched"):
        # ...AND THE CONTROLS THEMSELVES, for EVERY row whose column""",
       test="test_a_dropped_columns_ramp_goes_even_when_the_style_was_derived",
       why="the exact fault a hunt found an hour after this fix "
           "landed: the widget reset sat inside the touched-only "
           "branch while the records are popped for EVERY dropped "
           "row, so a chosen ramp on a derived style was lost twice"),
  dict(name="the-shelf-is-cleared-with-the-project", file=DIALOG,
       old="""                   self._scheme_memory,
                   self._custom_swatch_cache):""",
       new="""                   self._custom_swatch_cache):""",
       test="test_the_shelf_does_not_survive_the_project_that_made_it",
       why="the shelf was missing from this list and only emptied by "
           "the side effect of a swap-to-None; when that accident went "
           "away, a scheme shelved in the project you CLOSED merged "
           "into the next project's bank and redrew its column"),
  dict(name="the-settle-binds-the-dataset-in-force", file=DIALOG,
       old="""    self._swap_dataset_memory(layer)
    self._rebuild_unit()""",
       new="""    self._rebuild_unit()  # mutation: leave the identity unbound""",
       test="test_a_dataset_chosen_after_the_dialog_opened_owns_its_own_colours",
       why="a plugin opened BEFORE the data gets its first dataset "
           "through the settling combo; without the swap the identity "
           "stays unbound, and the next dataset takes the pre-identity "
           "merge and inherits the first one's hand-picked colours -- "
           "one dataset's value strings drawn on another's map and "
           "written into its project"),
  dict(name="door-three-moves-the-controls-not-just-the-records",
       file=DIALOG,
       old="""        fresh = self.DEFAULT_RAMPS[row % len(self.DEFAULT_RAMPS)]""",
       new="""        fresh = None  # mutation: leave the widgets showing the old scheme""",
       test="test_a_column_deleted_in_qgis_takes_its_ramp_and_count_too",
       why="door three edits the row IN PLACE and never rebuilds, so "
           "popping the records is not enough: `_assignments` reads "
           "the WIDGETS, and the ramp and class count went on being "
           "reported and drawn on the replacement column against "
           "ruling 3"),
  dict(name="a-removed-dataset-is-still-a-dataset-left", file=DIALOG,
       old="""    switched = (layer is not None and self._memory_layer_id is not None
                and layer.id() != self._memory_layer_id)""",
       new="""    switched = (layer is not None and self._watched_layer is not None
                and layer is not self._watched_layer)""",
       test="test_a_dataset_that_leaves_the_project_is_still_a_dataset_left",
       why="the exact code a hunt found broken on 2026-08-25: asked of "
           "the WATCHED LAYER OBJECT, a removal nulls it and the next "
           "dataset reads as a first choice, so Generate overwrites "
           "the previous dataset's GeoPackage unasked"),
  dict(name="our-own-output-never-binds-the-dataset-identity",
       file=DIALOG,
       old="""    if layer is not None and (
        layer.customProperty("weavingspace_output")
        or self._project_is_being_replaced):
      return""",
       new="""    if False:  # mutation: let an output layer be the dataset
      return""",
       test="test_a_reopened_project_reaches_its_own_colours_and_pins",
       why="on File > Open with the panel open the chooser binds to "
           "one of our own output layers for an instant before "
           "adoption runs; taking that as the dataset banked the "
           "project's hand-picks and pins where nothing could reach "
           "them, and the next Generate destroyed them in the .qgz "
           "and the GeoPackage"),
  dict(name="keeping-a-result-keeps-its-file", file=DIALOG,
       old="""    keeping = self.opt_new_group.isChecked() \\
        or self._new_group_chosen""",
       new="""    keeping = self.opt_new_group.isChecked()  # mutation: the box alone""",
       test="test_keeping_a_result_keeps_its_file_however_it_was_kept",
       why="four things now keep a previous result and this guard "
           "asked about one, so a change of dataset spared the GROUP "
           "and wrote over the FILE it draws from -- tables rewritten, "
           "others dropped, the panel looking right. The fourth is the "
           "chooser's 'create new', added 2026-08-25, and it is the "
           "only route where the group's own region stamps cannot "
           "answer: they name the current dataset, so the arming is "
           "all that stands between the run and the kept file. This "
           "entry SURVIVED the day the chooser landed, which is how "
           "that gap was found"),
  dict(name="the-roadmap-gate-cannot-be-satisfied-by-quoting-it",
       file="tools/check_roadmap.py",
       old="""  return CLEAR in QUOTED.sub(" ", section).lower()""",
       new="""  return CLEAR in section.lower()  # mutation: a mention will do""",
       test="test_the_roadmap_gate_reads_a_statement_not_a_mention",
       why="this gate is the FIRST stage of every release and refuses "
           "a candidate while the version's roadmap section still "
           "lists work. Searched as a bare substring, the phrase could "
           "be supplied by a sentence DENYING it -- which 0.24.3's own "
           "section carried, honestly, and the gate read the denial as "
           "the declaration and cleared a tree with a page of "
           "outstanding work under it"),
  dict(name="a-file-that-will-not-resume-says-so", file=DIALOG,
       old="""      if not bridge.write_working_state(path, resumable):""",
       new="""      bridge.write_working_state(path, resumable)
      if False:  # mutation: drop the answer on the floor""",
       test="test_a_saved_map_can_be_opened_and_carried_on",
       why="`write_working_state`'s own Returns block promises that a "
           "failure 'is reported rather than raised', and nothing read "
           "the bool it hands back -- a rule asserting its own "
           "enforcement, which this project has paid for before. The "
           "map, its styles and its tables reach the file either way; "
           "what is lost is the RESUME, and losing it in silence means "
           "the colleague who receives the file meets 'that GeoPackage "
           "does not carry a saved map' with nothing having been said "
           "to anybody at the time"),
  dict(name="the-preview-wait-follows-what-a-rebuild-costs",
       file=DIALOG,
       old="""    return int(max(PREVIEW_DEBOUNCE_MS,
                   min(PREVIEW_DEBOUNCE_CEILING_MS,
                       getattr(self, "_last_rebuild_ms", 0.0))))""",
       new="""    return PREVIEW_DEBOUNCE_MS  # mutation: the floor, whatever it costs""",
       test="test_the_preview_wait_widens_for_a_slow_rebuild",
       why="the preview debounce was shortened from a flat 350 to a "
           "FLOOR of 150, and what makes that safe on a machine nobody "
           "here has measured is that it is at least as long as the "
           "last rebuild took. A rebuild's cost scales with elements "
           "times features -- the ground the uncached-value defect of "
           "2026-08-19 lived on -- so on heavy data a fixed short wait "
           "would start work the user is about to interrupt, which is "
           "the complaint it was shortened to answer, made worse"),
  dict(name="the-preview-timer-is-armed-with-the-wait-it-computed",
       file=DIALOG,
       old="""    self._preview_timer.setInterval(self._preview_wait())
    self._preview_timer.start()""",
       new="""    self._preview_timer.start()  # mutation: keep whatever it had""",
       test="test_the_preview_wait_widens_for_a_slow_rebuild",
       why="a unit-tested mechanism with an undriven caller is a "
           "motionless axis, and this project has recorded that shape "
           "more than once. Computing the right wait and never arming "
           "the timer with it leaves every interval at whatever it was "
           "last set to, so the widening a slow machine depends on "
           "never happens"),
  dict(name="a-ramp-window-belongs-to-its-own-group", file=DIALOG,
       old="""      else:
        self._ramp_ranges.pop(tid, None)""",
       new="""      # mutation: leave the last group's window in place""",
       test="test_the_output_group_chooser_binds_to_the_dataset",
       why="`_ramp_ranges` means SOMEBODY NARROWED THE RAMP, and it "
           "was written only when the incoming record held a narrowed "
           "window where the two siblings on the neighbouring lines "
           "are assigned either way. Nothing else clears it, so a "
           "window narrowed on one group rode onto a group whose own "
           "record says the ramp runs end to end, and that group's "
           "classes took their colours from a stretch of ramp nobody "
           "chose for them"),
  dict(name="a-silent-record-clears-what-the-last-group-chose",
       file=DIALOG,
       # AIMED AT THE SINGLE COLOUR RATHER THAN THE RAMP, and the
       # reason is worth the line. A quantitative element's record
       # always carries a ramp, an opacity and a class count -- the
       # capture records what the element DRAWS, not only what
       # somebody chose -- so on that fixture the ramp branch writes
       # the group's own answer over the intruder and the pop is never
       # what answers. Mutating it therefore proves nothing about the
       # rule. The single colour is genuinely ABSENT from a
       # quantitative element's record, so its pop is the one line the
       # test can actually reach.
       old="""      if element.get("single_colour"):
        self._single_colours[tid] = element["single_colour"]
      else:
        self._single_colours.pop(tid, None)""",
       new="""      if element.get("single_colour"):
        self._single_colours[tid] = element["single_colour"]
      # mutation: leave the last group's single colour standing""",
       test="test_a_group_restores_its_own_state_and_no_one_elses",
       why="the ramp window was made assigned-always on 2026-08-26 "
           "and its six neighbours in the same loop were left "
           "set-only, so a group whose own record is silent inherited "
           "whatever the last one held. Ruling 4 is that selecting a "
           "group restores the whole working state 'so nothing is "
           "inferred', and three hunts that could not see each other "
           "reported this from three directions in one evening"),
  dict(name="a-pick-does-not-follow-you-to-another-group",
       file=DIALOG,
       old="""        else:
          self._quant_colours.get(tid, {}).pop(var, None)""",
       new="""        # mutation: keep the other group's hand-picked colours""",
       test="test_a_group_restores_its_own_state_and_no_one_elses",
       why="a class colour hand-picked on one output group came out "
           "DRAWN on another whose own record holds none, and stamped "
           "onto that map's layers -- so it reached the saved project "
           "and the GeoPackage a colleague opens. Driven 2026-08-26: "
           "#ff00ff where the control read the ramp's own #fff5f0. "
           "This is the value-laden half, cleared per element AND "
           "field so that switching a variable away and back still "
           "gives a person their work back"),
  dict(name="a-resumed-group-carries-the-design-it-resumed",
       file=DIALOG,
       old="""      self._stamp_working_state(already)""",
       new="""      pass  # mutation: leave the group without its record""",
       test="test_a_file_already_open_resumes_completely",
       why="the take-over branch was written from the twin that loads "
           "the file and dropped what came after it. The twin ends "
           "with this call and says at that line why: the file "
           "carries the record and the group did not, so saving the "
           "project, reopening it and choosing that group gave back "
           "its layers and none of its design. Measured: the twin "
           "leaves 1,959 characters on the group and this branch "
           "left none"),
  dict(name="a-resume-never-offers-its-own-tiles-as-a-region",
       file=DIALOG,
       # ANCHORED ON THE COMMENT ABOVE THE CALL, because both branches
       # now make this call and an anchor matching twice applies
       # nothing while the run still reports a result.
       old="""    # draws a map from the plugin's output.
    self._update_layer_exclusions()""",
       new="""    # draws a map from the plugin's output.
    pass  # mutation: skip the exclusion on the loading branch""",
       test="test_a_resume_keeps_its_output_off_the_region_list",
       why="construction, project-read and the run landing all keep "
           "the plugin's own output out of the region chooser, and "
           "the resume path registered element layers without doing "
           "so -- so a resumed map's own tile layers were offered as "
           "region data, one could be auto-selected, and the next "
           "Generate tiled the plugin's output into a new file and "
           "reported it as a success. Read back through GDAL"),
  dict(name="an-explicit-group-choice-outlives-ordinary-churn",
       file=DIALOG,
       old="""    on_it = {child.layer().id()
             for entry in theirs
             for child in entry[0].children()
             if getattr(child, "layer", lambda: None)() is not None}""",
       new="""    on_it = {child.layer().id() for child in group.children()
             if getattr(child, "layer", lambda: None)() is not None}""",
       test="test_the_output_group_chooser_binds_to_the_dataset",
       why="recency is a tie-break for choosing where nothing is "
           "chosen, not a rule that takes a chosen group away again. "
           "Asked of the NEWEST group alone, the already-working-on-it "
           "clause protected that group and no other, so deliberately "
           "picking an older one lasted until the next churn of "
           "project layers -- which a run causes twice, so it would "
           "rarely last at all. Ruling 1's whole gain is that the rule "
           "is on screen and CAN be overruled"),
  dict(name="one-file-is-one-map", file=DIALOG,
       old="""    if already is not None:
      # THE RECORD IS STILL APPLIED.""",
       new="""    if False:  # mutation: open the same file again anyway
      # THE RECORD IS STILL APPLIED.""",
       test="test_a_saved_map_can_be_opened_and_carried_on",
       why="nothing asked whether the file being resumed was already "
           "open, so resuming it twice built a SECOND group over the "
           "same tables -- two entries in the chooser that are the "
           "same map with nothing to tell them apart, and the next "
           "Generate writing into the file both of them draw from. "
           "The double map adoption exists to prevent, arriving "
           "through a door adoption never sees"),
  dict(name="a-paired-layer-is-not-an-element", file=DIALOG,
       old="""      if not table.endswith("_no_data"):
        loaded += 1""",
       new="""      loaded += 1  # mutation: count the twins as elements too""",
       test="test_a_saved_map_can_be_opened_and_carried_on",
       why="a paired no-data layer's table is `<table>_no_data`, which "
           "starts with `tiles_` like every other, so a four-element "
           "design told the user six element layers had come back. "
           "The twins are loaded and adopted correctly -- they are "
           "half of how absence is drawn -- and they are not elements"),
  dict(name="the-region-stamp-names-the-layer-that-was-tiled",
       file=DIALOG,
       old="""    region_now = (source_layer
                  if self._source_layer_alive(source_layer) else None)""",
       new="""    region_now = self.layer_combo.currentLayer()  # mutation: read live""",
       test="test_a_map_is_filed_under_the_dataset_it_was_drawn_from",
       why="which dataset a map came from is a fact about the TILES, "
           "and reading it off the chooser as the run lands makes the "
           "answer depend on where the user was looking when the "
           "tiling finished. Switch the region layer mid-run and A's "
           "tiles came out stamped as B's, so the chooser labelled "
           "A's map with B's name, the binding handed that group to "
           "B, and the landing's own refusal to write over another "
           "dataset's map read the same wrong stamp and let a B run "
           "replace it -- four of four layers destroyed, measured "
           "2026-08-26. The record had it right all along, taking "
           "`region` from the launch snapshot: one act was writing "
           "one fact twice, from two moments"),
  dict(name="an-empty-chooser-does-not-forget-the-dataset", file=DIALOG,
       old="""    if layer is None:
      # AN EMPTY CHOOSER IS NOT A DATASET""",
       new="""    if False:  # mutation: bank and forget on an empty chooser
      # AN EMPTY CHOOSER IS NOT A DATASET""",
       test="test_a_dataset_that_leaves_the_project_is_still_a_dataset_left",
       why="removing the layer empties the combo, so the handler runs "
           "once with NO layer; banking there and nulling the identity "
           "defeats the boundary before the next dataset arrives. This "
           "is the second fault of that route, and it HID the first"),
  dict(name="a-first-real-choice-is-not-a-change-of-dataset", file=DIALOG,
       old="""    switched_from_work = switched and self._landed_this_session""",
       new="""    switched_from_work = switched""",
       test="test_a_project_that_already_has_forty_layers",
       why="a dialog opened in a busy project lands on whatever layer "
           "the chooser offers first, and without the landed clause the "
           "user's first real pick read as a switch away from data they "
           "never chose: the fresh-group flag built a rival beside the "
           "adopted group. Found by the full suite on the rulings' "
           "first whole run"),
  dict(name="a-landing-is-what-makes-a-dataset-this-sessions-work",
       file=DIALOG,
       old="""    self._landed_this_session = True""",
       new="""    pass  # mutation: no landing ever counts""",
       test="test_a_change_of_dataset_starts_a_new_file_and_a_new_group",
       why="with the set-site gone every switch is a first choice "
           "forever: the path never clears and B's landing replaces "
           "A's result -- the two harms the rulings started from"),
  dict(name="a-short-dataset-gets-a-question-not-a-shared-column",
       file=DIALOG,
       old="""    if 2 <= len(usable) < elements:""",
       new="""    if False:  # mutation: never ask about a short dataset""",
       test="test_a_dataset_that_cannot_fill_the_design_asks_first",
       why="fewer seemingly-usable columns than elements used to mean "
           "two elements silently sharing one column; ruling 5 of "
           "2026-08-21 makes it a question naming both numbers. The "
           "hedge 'seemingly' is the maintainer's own wording, because "
           "the usable-column count is a heuristic"),
  dict(name="a-yes-to-the-design-floor-recomposes", file=DIALOG,
       old="""      if answer == QMessageBox.StandardButton.Yes:
        # Signals LIVE deliberately: the n chooser's own cascade is
        # what repopulates the family list for the new count and picks
        # its default, and driving that any other way would be a
        # second implementation of the rule.
        self.n_combo.setCurrentText(str(count))""",
       new="""      if answer == QMessageBox.StandardButton.Yes:
        pass  # mutation: agree, then do nothing""",
       test="test_a_dataset_that_cannot_fill_the_design_asks_first",
       why="a question whose Yes changes nothing taught the user that "
           "the dialog's questions are decoration; the recompose goes "
           "through the n chooser's own cascade so the family default "
           "is the same rule the chooser applies"),
  dict(name="a-no-to-the-design-floor-keeps-the-design", file=DIALOG,
       old="""      answer = QMessageBox.question(
        self, "WeavingSpace",
        f"This layer seemingly has {count} usable columns, and the "
        f"design has {elements} elements. Change to a design with "
        f"{count} elements?")
      if answer == QMessageBox.StandardButton.Yes:""",
       new="""      answer = QMessageBox.question(
        self, "WeavingSpace",
        f"This layer seemingly has {count} usable columns, and the "
        f"design has {elements} elements. Change to a design with "
        f"{count} elements?")
      if True:  # mutation: recompose whatever they answered""",
       test="test_a_dataset_that_cannot_fill_the_design_asks_first",
       why="declining must keep the design with columns shared, as "
           "always -- recomposing on a No is consent theatre, and the "
           "design is the one thing nothing could re-derive"),
  dict(name="a-switch-clears-the-output-path", file=DIALOG,
       old="""    widget = getattr(self, "gpkg_widget", None)
    if widget is not None and widget.filePath():
      widget.blockSignals(True)
      widget.setFilePath("")""",
       new="""    widget = getattr(self, "gpkg_widget", None)
    if False:  # mutation: keep the path across the switch
      widget.blockSignals(True)
      widget.setFilePath("")""",
       test="test_a_change_of_dataset_starts_a_new_file_and_a_new_group",
       why="a colleague met B's map silently overwriting the GeoPackage "
           "built from A -- a result on DISK, destroyed unasked. The "
           "path now clears on any change of region layer, same-schema "
           "included, and the clearing is announced (ruling 1 of "
           "2026-08-21)"),
  # `a-switch-detaches-the-group` STOOD HERE AND WAS DELETED ON
  # 2026-08-25, when ruling 1 retired the flag it mutated. It was
  # re-aimed first, at the binding's own answer for a dataset with no
  # group -- and it SURVIVED, so the redundancy question was put the
  # way this project's rules ask: break every route AT ONCE and see
  # whether the test can still pass. It could. THREE mechanisms now
  # keep a change of dataset out of the previous dataset's group, and
  # they are not duplicates of each other -- they answer different
  # questions and each is right on its own terms:
  #
  #   the CHOOSER falls back to "create new"   (a-dataset-with-no-group-claims-none)
  #   the DIALOG detaches from the old group   (same entry, same line)
  #   the LANDING refuses a group stamped for another dataset
  #                                            (`theirs`, its own entry above)
  #
  # Each of those is separately guarded and separately caught. What
  # cannot be guarded is the RULE they jointly implement, because no
  # single line owns it -- which is precisely the shape this project
  # already met with `_deriving_spacing`, and the honest record is a
  # note rather than an entry that can only ever be red.
  dict(name="the-fresh-group-flag-is-spent-by-its-landing", file=DIALOG,
       old="""    self._adopted_group_unwritten = False
    self._new_group_chosen = False""",
       new="""    self._adopted_group_unwritten = False
    pass  # mutation: the flag survives its landing""",
       test="test_a_change_of_dataset_starts_a_new_file_and_a_new_group",
       why="left armed, EVERY later run builds another group: the demo "
           "that switches once and then adjusts spacing five times "
           "would leave six copies of the map. Spent the moment it is "
           "read, like the adopted-group flag beside it"),
  dict(name="a-dropped-scheme-is-not-refilled-from-the-old-table",
       file=DIALOG,
       old="""      scheme_reset = restored is None and (
        column_gone or tid in self._scheme_just_reset)""",
       new="""      scheme_reset = False  # mutation: let prev refill the scheme""",
       test="test_a_dropped_column_takes_its_whole_scheme_and_the_shelf_returns_it",
       why="the shelve POPS the records, and three restores in the "
           "rebuild fall back to the previous assignment exactly when "
           "the record is empty -- the state the pop just created -- "
           "so the ramp, the tick and the count all came straight "
           "back. Measured on the fix's own first build, 2026-08-21"),
  dict(name="the-shelf-captures-the-mode-the-widget-holds", file=DIALOG,
       old="""      if column_gone:
        self._shelve_scheme(tid, dict(prev, mode_raw=raw_modes.get(
          tid, prev.get("mode_raw"))))""",
       new="""      if column_gone:
        self._shelve_scheme(tid, prev)  # mutation: trust _assignments""",
       test="test_a_dropped_column_takes_its_whole_scheme_and_the_shelf_returns_it",
       why="_assignments corrects a quantitative style on a non-numeric "
           "column to Categorized, and a column the NEW layer merely "
           "LACKS answers _field_is_numeric False exactly as text does "
           "-- so every dropped quant scheme was filed as Categorized, "
           "and the wrong mode greyed Reverse on the way back. Found by "
           "three dump lines after reading named the wrong suspect"),
  dict(name="an-element-returns-to-a-field-it-has-shown-before",
       file=DIALOG,
       old="""      elif remembered is not None:
        var_combo.setCurrentText(remembered)""",
       new="""      elif False:  # mutation: ignore the shelf when re-defaulting
        var_combo.setCurrentText(remembered)""",
       test="test_a_dropped_column_takes_its_whole_scheme_and_the_shelf_returns_it",
       why="ruling 6 is that switching back RESTORES: the element "
           "prefers a field it has shown before over the cycled "
           "default, and that preference is what makes the A-B-A "
           "demo return to its own work rather than to a plausible "
           "stranger"),
  dict(name="a-lost-column-still-costs-its-element-a-variable", file=DIALOG,
       old="""      elif preferred:
        var_combo.setCurrentText(preferred[row % len(preferred)])""",
       new="""      elif False:  # mutation: a lost column leaves the row blank
        var_combo.setCurrentText(preferred[row % len(preferred)])""",
       test="test_a_new_region_drops_a_setup_whose_column_has_gone",
       why="losing a column costs an element its VARIABLE and not its "
           "place on the map: left blank it draws as flat fill, so "
           "changing dataset would quietly cost the map two of its "
           "four variables. The recovery rule of 2026-08-15 says it "
           "auto-assigns to a column the new layer HAS"),
  dict(name="a-scheme-does-not-outlive-the-column-it-was-cut-for",
       file=DIALOG,
       # AIMED AT THE THIRD DOOR, deliberately. The same rule is
       # written at three places -- two in `_refresh_table` and this
       # one -- and the two there are each SUFFICIENT, because a change
       # of region dataset rebuilds the table twice and the second pass
       # reads what the first left. Mutating either of those survives
       # with every observable correct, which is a fact about the fix
       # rather than about the guard. This door has one implementation
       # and one line, so it is the one an entry can hold.
       old="""      elif mode_cell is not None and mode_cell.findText(instead) >= 0:""",
       new="""      elif False:  # mutation: the style outlives its column""",
       test="test_a_column_deleted_in_qgis_takes_its_scheme_with_it",
       why="the maintainer's ruling of 2026-08-20 is that a setup is "
           "KEPT where the data still has a column of that name and "
           "DROPPED where it does not. The variable re-defaulted from "
           "the first day and the STYLE rode along, so a categorical "
           "scheme cut for four land-cover words came to rest on a "
           "numeric column and drew a colour for each -- the "
           "colleague's report. Here the user is even TOLD their "
           "elements moved to another column, so the scheme riding "
           "along is what that account leaves out"),
  dict(name="a-dropped-scheme-is-no-longer-somebodys-pick", file=DIALOG,
       old="""        mode_combo.setProperty(
          "touched", bool(prev and prev.get("style_touched")
                          and not column_gone))""",
       new="""        mode_combo.setProperty(
          "touched", bool(prev and prev.get("style_touched")))""",
       test="test_a_new_region_drops_a_setup_whose_column_has_gone",
       why="the flag means somebody chose this style rather than the "
           "plugin deriving it, and what they chose it for has gone. "
           "Left set, the next rebuild restores a scheme nobody has "
           "chosen for the column now in force -- the same defect "
           "arriving one rebuild later"),
  dict(name="a-change-of-dataset-asks-about-what-it-keeps", file=DIALOG,
       old="""    if switched:
      self._settle_retained_schemes()""",
       new="""    if False:  # mutation: a change of dataset asks nothing
      self._settle_retained_schemes()""",
       test="test_a_column_that_keeps_its_name_and_changes_its_kind",
       why="the second door into 'too many categories', and it shares "
           "its number with the copy on the maintainer's ruling. A "
           "column keeping its NAME keeps its element's setup, and "
           "nothing about a name says the values are the same kind of "
           "thing: four words become thirty-six floats and the map is "
           "drawn with a swatch for each, unasked"),
  dict(name="the-answer-to-that-question-is-read", file=DIALOG,
       old="""      if self._many_categories_is_wanted(field, count):
        continue""",
       new="""      if True:  # mutation: ask, then ignore the answer
        continue""",
       test="test_a_column_that_keeps_its_name_and_changes_its_kind",
       why="a question that does the same thing whatever you answer is "
           "worse than no question, because it reads as consent. The "
           "refusal arm here had never once executed before "
           "2026-08-20: the suite answered every box Yes"),
  dict(name="a-refused-copy-is-a-copy-that-did-not-happen", file=DIALOG,
       old="""        refused.append((target_id, ("was left alone", "were left alone")))
        continue""",
       new="""        refused.append((target_id, ("was left alone", "were left alone")))
        pass  # mutation: report the refusal and copy anyway""",
       test="test_a_copy_asks_before_drawing_a_colour_for_every_value",
       why="the report saying an element was left alone while the copy "
           "went onto it is the worst of both: the user is told their "
           "refusal was honoured and the map is drawn with a colour "
           "for every value regardless"),
  dict(name="a-copy-lands-on-a-row-that-can-hold-it", file=DIALOG,
       old="""      self._sync_row(row)
    ramp_cell = self.table.cellWidget(row, 4)""",
       new="""      pass  # mutation: leave the receiving row as it was
    ramp_cell = self.table.cellWidget(row, 4)""",
       test="test_a_copy_carries_a_class_source_the_target_has_not_met",
       why="the class-source cell exists ONLY on a categorized row, so "
           "a target that was quantitative a moment ago has no widget "
           "in column 7 and the token was written into nothing. The "
           "colours arrive, the reference does not, and the window "
           "shows two elements agreeing while their colours come from "
           "different places"),
  dict(name="a-copy-never-carries-the-variable", file=DIALOG,
       old="""    their_field = target["var"]
    if picks:""",
       new="""    their_field = source["var"]  # mutation: carry the variable
    if picks:""",
       test="test_a_categorical_scheme_copies_onto_another_element",
       why="carrying the source's column would make the target a "
           "DUPLICATE of the source, so a map whose whole purpose is "
           "reading several variables against each other would quietly "
           "lose one. The maintainer named this as the record that "
           "must never travel, ahead of opacity"),
  dict(name="a-partial-recolour-is-not-a-classify", file=DIALOG,
       old="""    if ours != theirs and all(a != b for a, b in zip(ours, theirs)):""",
       new="""    if ours != theirs:  # mutation: any moved colour blocks the bounds""",
       test="test_a_boundary_retyped_beside_a_recolour_is_still_recorded",
       why="a Classify picks a ramp and rewrites EVERY class, so "
           "demanding that no colour moved is right about it and wrong "
           "about the visit where somebody retypes a boundary and "
           "recolours a class. That satisfies neither branch and the "
           "boundary is never recorded by the visit that typed it "
           "(ledger row 6)"),
  dict(name="custom-is-a-display-and-never-an-item", file=DIALOG,
       # BOTH THIS AND ITS SIBLING BELOW ANCHOR ON THE SAME TWO LINES,
       # which is fine because a mutation is applied one at a time --
       # and necessary, because the two assertions they prove name
       # different halves of one design decision.
       old="""    self._custom = bool(on)
    self.update()""",
       new="""    self._custom = bool(on)
    if on and self.findText("Custom") < 0:
      self.addItem("Custom")  # mutation: make it a real item
    self.update()""",
       test="test_a_ladder_somebody_else_cut_makes_the_scheme_cell_read_custom",
       why="an item a user could choose would need a meaning of its "
           "own, and adding one is the obvious implementation somebody "
           "reaches for. The list is how every scheme stays selectable "
           "at all times, which is an explicit user requirement"),
  dict(name="the-scheme-cell-keeps-its-index-under-custom", file=DIALOG,
       old="""    self._custom = bool(on)
    self.update()""",
       new="""    self._custom = bool(on)
    if on:
      self.setCurrentIndex(-1)  # mutation: leave the scheme behind
    self.update()""",
       test="test_a_ladder_somebody_else_cut_makes_the_scheme_cell_read_custom",
       why="the index stays on the last-picked scheme so that choosing "
           "one RECLASSIFIES and retires the stored ladder through the "
           "degrade-to-pins rule. Left on nothing, the row cannot be "
           "given back to a scheme at all"),
  dict(name="the-custom-scheme-display-reaches-the-screen", file=DIALOG,
       # THE PIXEL AXIS, entered separately because `showing_custom()`
       # and "the cell paints differently" are two claims, and the
       # first is proved by another entry. This project has shipped a
       # mark drawn into pixels its own widget covered, so a flag that
       # never becomes ink deserves a mutation of its own.
       #
       # THE ANCHOR DELIBERATELY DOES NOT END ON A QUOTE. The first
       # draft ended `option.currentText = "Custom"` inside a triple-
       # quoted string, so the four quotes ran together and the
       # catalogue would not parse -- caught by running it, 2026-08-20.
       old="""    option.currentText = "Custom"
    painter.drawComplexControl(QStyle.ComplexControl.CC_ComboBox, option)""",
       new="""    painter.drawComplexControl(QStyle.ComplexControl.CC_ComboBox, option)""",
       test="test_a_ladder_somebody_else_cut_makes_the_scheme_cell_read_custom",
       why="the cell can hold the Custom state and go on PAINTING the "
           "scheme name, which is the whole of what a user sees. The "
           "row then reads as cut by quantiles while the map is cut by "
           "numbers somebody typed, and nothing on screen says so"),
  dict(name="the-catch-all-is-adopted-like-any-other-class", file=DIALOG,
       # THE SECOND AXIS of the same test, and it needs its own entry:
       # the entry below breaks the FOLLOW branch, whose harm is the
       # sentence, and the sentence assertion fires FIRST -- so the
       # record assertion is masked and would be proved by nothing.
       # Per-assertion, 2026-08-20.
       old="""    for key, colour in actual.items():
      if expected.get(key) != colour and record.get(key) != colour:""",
       new="""    for key, colour in actual.items():
      if key == bridge.NO_DATA_KEY:
        continue  # mutation: adopt every class but the catch-all
      if expected.get(key) != colour and record.get(key) != colour:""",
       test="test_recolouring_the_catch_all_alone_is_not_a_new_ramp",
       why="the catch-all is a class like any other once the handler "
           "has decided this was not a Classify: skipping it in the "
           "adopt walk loses the one colour the user actually changed, "
           "silently, while every sentence and every other class stays "
           "correct"),
  dict(name="a-catch-all-recolour-is-not-a-classify", file=DIALOG,
       old="""      catch_all_moved = (here is not None and ours is not None
                         and here.lower() != ours.lower())""",
       new="""      catch_all_moved = False  # mutation: drop the catch-all again""",
       test="test_recolouring_the_catch_all_alone_is_not_a_new_ramp",
       why="the catch-all is a colour a reader sees, often over the "
           "gaps a join left, and the editor offers it deliberately. "
           "Dropped from the comparison, an edit touching only that "
           "class compares EQUAL to a clean Classify from a ramp: the "
           "handler tells the user the element now follows a ramp "
           "nobody chose, clears their picks, and repaints those "
           "areas the default grey at the next Generate. Ledger row 5, "
           "shipping since 2026-08-10"),
  dict(name="an-adopted-ladder-tells-the-row-it-is-custom", file=DIALOG,
       old="""    try:
      row = self._row_for_element(tile_id)
      if row is not None and row >= 0:
        self._sync_row(row)
    except Exception:
      pass

  def _replay_deferred_adoptions(self):""",
       new="""    pass  # mutation: leave the row describing the old scheme

  def _replay_deferred_adoptions(self):""",
       test="test_a_ladder_somebody_else_cut_makes_the_scheme_cell_read_custom",
       why="the Style cell reads Custom while a stored ladder is in "
           "force, and it is decided in `_sync_row`, whose only "
           "callers are the dynamic-column pass and the deferral "
           "refresh. A ladder retyped in QGIS reaches neither, so the "
           "record held somebody else's boundaries while the cell went "
           "on naming the scheme the map was no longer cut by"),
  dict(name="a-retired-ladder-gives-the-scheme-cell-back", file=DIALOG,
       old="""      try:
        row = self._row_for_element(tile_id)
        if row is not None and row >= 0:
          self._sync_row(row)
      except Exception:
        pass""",
       new="""      pass  # mutation: leave the cell reading Custom""",
       test="test_a_ladder_somebody_else_cut_makes_the_scheme_cell_read_custom",
       why="the TWIN of the entry above, at the other end of the same "
           "record. Choosing a scheme retires the stored ladder, and "
           "without this the cell goes on reading Custom -- a state "
           "with no control left to leave it by, since the scheme the "
           "user would press is the one they just pressed. It cannot "
           "live in the caller: `_on_mode_chosen` and `_queue_live` "
           "share one signal, so the sync can run BEFORE the "
           "retirement it is about to describe"),
  dict(name="a-vanished-source-still-repaints-on-the-live-path", file=DIALOG,
       old="""      if self._restyle_only():
        _dump("LIVE-GATE", "restyled-without-the-source")
        return""",
       # THE ORDER OF THE OPERANDS IS THE WHOLE MUTATION. Written
       # `self._restyle_only() and False` this SURVIVED: Python
       # evaluates left to right, so the restyle still ran and still
       # repainted, and only the `return` was skipped. A mutation
       # whose side effect survives it breaks nothing the test can
       # see. Short-circuit ahead of the call.
       new="""      if False and self._restyle_only():  # mutation: refuse it too
        _dump("LIVE-GATE", "restyled-without-the-source")
        return""",
       test="test_a_colour_picked_after_the_file_moved_still_reaches_the_map",
       why="the availability gate is about TILING, and a restyle "
           "re-seeds renderers on tiles that already exist. Left as a "
           "bare refusal it stands in front of the repaint exit, so a "
           "colour picked after the region layer's file moved is "
           "recorded, never drawn, and explained by a sentence about "
           "the user's DATA when the fact is about their FILE"),
  dict(name="the-button-restyles-before-it-asks-about-the-source", file=DIALOG,
       old="""    if not live and self._restyle_only():
      return  # the button pressed after a style change: instant""",
       new="""    if not live and False and self._restyle_only():
      return  # mutation: ask about the source first""",
       test="test_a_colour_picked_after_the_file_moved_still_reaches_the_map",
       why="the TWIN of the entry above, and the reason it needed no "
           "repair: `_generate` puts its restyle fast path ABOVE its "
           "own availability check, so a button press after a moved "
           "file repaints where a live tick did not. Reversing that "
           "order gives the button the defect the live gate had, and "
           "the second act of that test is what notices"),
  dict(name="unobservable-layer-retiles", file=DIALOG,
       old="""    if self._data_is_unobservable():
      # A layer that will not say how many features it has may have""",
       new="""    if False:  # mutation: repaint a source we cannot inspect
      # A layer that will not say how many features it has may have""",
       test="test_a_layer_that_will_not_say_how_big_it_is",
       why="a WFS or database layer can be rewritten on a server with "
           "nothing locally to show for it, so the fast path would "
           "repaint tiles built from data that is gone"),
  dict(name="lost-column-redefaults", file=DIALOG,
       old="""      moved.append((was, now))""",
       new="""      moved.append((was, now))
      combo.setCurrentText("---")  # mutation: unassign instead""",
       test="test_the_user_changes_the_data_underneath",
       why="losing a column must cost an element its variable, not its "
           "place on the map: unassigned draws as flat fill, so a "
           "deletion in QGIS would quietly cost the map two of its "
           "four variables"),
  dict(name="added-column-offered", file=DIALOG,
       old="""      combo.clear()
      combo.addItems(wanted)""",
       new="""      pass  # mutation: leave the chooser's list as it was""",
       test="test_a_sequence_of_edits_under_the_plugin",
       why="a column added in QGIS with the Field Calculator stays "
           "invisible until the user switches layers and back, with "
           "nothing on screen to suggest that is the remedy"),
  dict(name="region-chooser-exclusions", file=DIALOG,
       # RE-ANCHORED 2026-08-17: `_show_the_adopted_path()` went in
       # between these two lines, so the two-line anchor matched
       # nothing and the entry had gone silent -- which reads exactly
       # like success. Anchored on the call it is actually about.
       old="""    self._update_layer_exclusions()
    # order matters: families must be populated (_on_n_changed) before""",
       new="""    # order matters: families must be populated (_on_n_changed) before""",
       test="test_plugin_never_offers_its_own_output_as_a_region",
       why="a dialog opened on a project that already holds a tiled "
           "map must not offer that map as a region layer"),
  dict(name="spacing-default", file=DIALOG,
       old="self.spacing_spin.setValue(1000)",
       new="pass  # mutation: no declared default spacing",
       test="test_design_controls_are_usable_as_designed",
       why="the spacing a first-time user is given, before any layer "
           "can auto-size it"),
  dict(name="auto-spacing-button", file=DIALOG,
       old="spacing_row.addWidget(auto)",
       new="pass  # mutation: the button is never added to a layout",
       test="test_design_controls_are_usable_as_designed",
       why="a control constructed but never added is a feature no "
           "user can reach"),
  dict(name="modifier-step-size", file=DIALOG,
       old="box.setSingleStep(step)",
       new="pass  # mutation: whole-unit steps",
       test="test_design_controls_are_usable_as_designed",
       why="nudging a rotation or an inset, rather than lurching"),
  dict(name="point-angle-connection", file=DIALOG,
       old="self.opt_point_angle.valueChanged.connect(self._queue_preview)",
       new="pass  # mutation: the control reaches nothing",
       test="test_controls_respond_without_being_prompted",
       why="a star's point angle acting through its own signal"),
  dict(name="group-on-top", file=DIALOG,
       old="return root.insertGroup(0, name), True",
       new="return root.insertGroup(1, name), True",
       test="test_group_sits_on_top_of_the_layers_panel",
       why="a freshly generated map landing where it can be seen"),
  dict(name="catalogue-offset", file=CATALOG,
       old='"hex-slice 7": dict(type="tiling", tiling_type="hex-slice", n=7, offset=0)',
       new='"hex-slice 7": dict(type="tiling", tiling_type="hex-slice", n=7, offset=1)',
       test="test_catalogue_values_are_what_they_claim",
       why="where a hex-slice's cuts start; the element count is "
           "identical either way, so counting cannot catch it"),
  dict(name="region-chooser-filter", file=DIALOG,
       old="self.layer_combo.setFilters(_polygon_filter())",
       new="pass  # mutation: every layer offered, tileable or not",
       test="test_the_dialogs_chrome_does_its_job",
       why="the region chooser offering only layers that can be tiled"),
  dict(name="idle-progress-bar", file=DIALOG,
       # Narrowed 2026-08-12 (three sites: construction, the
       # alive-check and _finish_run). The named test inspects a
       # freshly built dialog's chrome, so it is construction that
       # this entry is about; hiding it after a run is a different
       # promise with its own tests.
       old="""    self.progress = QProgressBar()
    self.progress.setVisible(False)""",
       new="""    self.progress = QProgressBar()
    self.progress.setVisible(True)""",
       test="test_the_dialogs_chrome_does_its_job",
       why="the progress bar staying out of the way when nothing runs"),
  dict(name="close-button", file=DIALOG,
       old="close_btn.clicked.connect(self.close)",
       new="pass  # mutation: Close does nothing at all",
       test="test_the_dialogs_chrome_does_its_job",
       why="the Close button closing the window"),
  dict(name="palette-install-skip", file=BRIDGE,
       old="      if name.lower() in existing:",
       new="      if name.lower() not in existing:",
       test="test_ramp_swatches_and_palette_installation",
       why="the plugin's palettes reaching the QGIS style at all"),
  dict(name="family-angle-range", file=DIALOG,
       old="self.opt_offset_angle.setRange(lo, hi)",
       new="pass  # mutation: whatever range was last in force",
       test="test_family_option_ranges_track_the_family",
       why="a family's inner angle bounded by what that family accepts"),
  dict(name="single-category-guard", file=BRIDGE,
       old="          if n > 1 else 0",
       new="          if n >= 1 else 0",
       test="test_a_single_category_still_gets_a_colour",
       why="a field whose values are all the same still rendering"),
  dict(name="classes-placeholder", file=DIALOG,
       old="""      k_spin.setSpecialValueText("\u2013")
      k_spin.setValue(0)""",
       new="""      k_spin.setSpecialValueText("\u2013")
      k_spin.setValue(1)""",
       test="test_a_row_without_classes_says_so",
       why="a categorical row's Classes cell showing a dash rather "
           "than claiming one class"),
  dict(name="live-pending-initial", file=DIALOG,
       # Narrowed 2026-08-12 (three sites: the constructor, closeEvent
       # and _finish_run). The constructor is the one the name and the
       # why mean: initialised full, _finish_run then starts the live
       # timer after an ordinary Generate. docs/MUTATION-TESTING.md
       # records this exact mutant as causing an extra tiling run
       # after every Generate, which is how it is known not to be
       # equivalent.
       old="""    self._live_timer.timeout.connect(self._maybe_live_generate)
    self._live_pending = False""",
       new="""    self._live_timer.timeout.connect(self._maybe_live_generate)
    self._live_pending = True""",
       test="test_a_finished_run_leaves_nothing_armed",
       why="an ordinary Generate not arming a live rebuild nobody "
           "asked for"),
  dict(name="cvd-simulation", file=PERCEPTION,
       old="""  if vision == "normal":
    return tuple(float(v) for v in rgb)""",
       new="""  if True:
    return tuple(float(v) for v in rgb)""",
       test="test_colours_a_reader_cannot_separate_are_reported",
       why="colour-vision deficiency actually being simulated; without "
           "it every pair looks as separable as it does to a reader "
           "with normal vision, which is the whole point"),
  # The narrowing back to the ONE colour it used to be. Anchored on
  # the comparison rather than on ABSENCE_FILLS itself, because the
  # set is derived from bridge's kinds and a mutation of the derivation
  # would be a mutation of the data model rather than of this check.
  dict(name="every-placeholder-fill-is-excluded", file=PERCEPTION,
       old="    kept = [c for c in colours if _hex_of(c) not in ABSENCE_FILLS]",
       new="    kept = [c for c in colours "
           "if _hex_of(c) != NO_DATA_FILL.lower()]",
       test="test_no_placeholder_fill_is_ever_a_clash",
       why="the two infinity placeholders being left out of the "
           "comparison as the no-data grey is: every element that has "
           "an infinity paints the same colour, so comparing it with "
           "itself reports a clash between any two such elements and "
           "the warning stops meaning anything for those designs"),
  dict(name="shared-ramp-exemption", file=PERCEPTION,
       old="      if first in shared and shared[first] == shared.get(second):",
       new="      if False:",
       test="test_colours_a_reader_cannot_separate_are_reported",
       why="a shared-ramp design, which distinguishes elements by "
           "shape, not being warned about as though it were a fault"),
  dict(name="categorical-shift-notice", file=DIALOG,
       old="          shift = bridge.categorical_shift_message(",
       new="          shift = None or bridge.no_such_message(",
       test="test_a_changed_category_count_warns_that_colours_moved",
       why="telling the user that a changed class count has moved the "
           "colours of the classes that were already there"),
  # Diagnosed 2026-08-10: the named test tiled an EPSG:3857 layer, so
  # the geographic branch never ran and the mutation could not show.
  # The test now repeats its coverage case on the same fixture in
  # degrees and reads the sentence the message bar gets.
  dict(name="coverage-unit-label", file=COMPAT,
       old='  if layer.crs().isGeographic():\n    return "m"',
       new='  if False:\n    return "m"',
       test="test_the_map_says_which_areas_it_left_out",
       why="the coverage notice giving the units the plugin actually "
           "tiles in; a geographic layer is reprojected, so its "
           "spacing is metres and saying 'deg' contradicts the number"),
  dict(name="coverage-warning-spacing", file=BRIDGE,
       old="def coverage_message(missing: int, unit_count: int, spacing: float,",
       new="def coverage_message(missing: int, unit_count: int, spacing: float=0,",
       test="test_the_map_says_which_areas_it_left_out",
       why="the coverage notice naming the SPACING that produced the "
           "drops, without which a stack of them is unreadable"),
  # Re-pointed 2026-08-10 after this survived a sweep. The entry named
  # the deleted-column test, and a column deleted from the CURRENT
  # layer is answered elsewhere: the updatedFields handler re-defaults
  # the elements and says so, before the table is ever rebuilt.
  # Measured both ways, that scenario comes out identical with the
  # guard and without it. What the guard alone answers is the region
  # layer being SWITCHED to one whose columns are named differently;
  # mutated, every element there lands on "---" and the map goes to
  # flat fill.
  dict(name="stale-field-assignment", file=DIALOG,
       old='      if prev and prev["var"] in fields:',
       new='      if prev and prev["var"] is not None:',
       test="test_switching_region_layer_counts_as_a_change",
       why="an element re-pointing at a column the layer now chosen "
           "actually has; carrying the old layer's column name means "
           "setCurrentText finds nothing, the element goes unassigned, "
           "and a map of four attributes becomes a map of none"),
  dict(name="single-category-first-colour", file=BRIDGE,
       old="          if n > 1 else 0",
       new="          if n > 1 else 1",
       test="test_a_single_category_still_gets_a_colour",
       why="a lone category taking the palette's FIRST colour, so two "
           "maps of the same data agree and a second category does "
           "not steal the first one's colour"),
  dict(name="output-form-layout", file=DIALOG,
       old="    olayout.addLayout(out_form)",
       new="    pass  # mutation: the whole output form is never added",
       test="test_the_dialogs_chrome_does_its_job",
       why="the GeoPackage and grouping controls existing in the "
           "window rather than only in the source"),
  dict(name="progress-hidden-after-run", file=DIALOG,
       old="""        self.generate_btn.setEnabled(True)
        self.progress.setVisible(False)""",
       new="""        self.generate_btn.setEnabled(True)
        pass  # mutation: the bar stays on screen after the run""",
       test="test_choice_persistence_and_recovery",
       why="a dialog REOPENED after its run died without reporting "
           "must not still show a progress bar frozen at that run's "
           "percentage, which reads as 'still working'. This line is "
           "in showEvent's zombie recovery, not in the "
           "layer-disappeared path an earlier version of this entry "
           "named; ordinary completion is hidden by _finish_run and "
           "is defended elsewhere"),
  dict(name="square-slice-offset", file=CATALOG,
       old='"square-slice 2": dict(type="tiling", tiling_type="square-slice", n=2, offset=0)',
       new='"square-slice 2": dict(type="tiling", tiling_type="square-slice", n=2, offset=1)',
       test="test_catalogue_values_are_what_they_claim",
       why="where a square slice's cuts begin; the element count is "
           "the same either way, so counting cannot catch it"),
  dict(name="identifier-default", file=DIALOG,
       old="preferred = [f for f in numeric if f.lower() not in id_like] or numeric",
       new="preferred = [f for f in numeric if f.lower() in id_like] or numeric",
       test="test_defaults_avoid_identifier_columns",
       why="the default variable being a measurement rather than a "
           "row id, which maps storage order and looks like data"),
  dict(name="chooser-clear", file=DIALOG,
       # Narrowed 2026-08-10. Three combos call clear(), so the bare
       # anchor mutated whichever came first -- and the first attempt
       # at narrowing aimed at the VARIABLE chooser, which the named
       # test never drives. This is the CLASS-SOURCE combo, column 7,
       # which is the one that test repopulates: read what a test
       # executes before anchoring to it.
       old="""      combo.blockSignals(True)
      combo.clear()
      for text, data in wanted:""",
       new="""      combo.blockSignals(True)
      pass  # mutation: entries appended, never replaced
      for text, data in wanted:""",
       test="test_repopulating_a_chooser_does_not_duplicate_it",
       why="a dropdown rebuilt without duplicating everything in it"),
  dict(name="size-guard-degenerate", file=BRIDGE,
       old="  if det <= 0:",
       new="  if det <= 1:",
       test="test_the_size_guard_does_not_refuse_fine_patterns",
       why="fine patterns being drawn rather than declared impossible"),
  dict(name="categorical-palette-install", file=BRIDGE,
       old="""    if name.lower() in existing:
      continue
    save(name, QgsPresetSchemeColorRamp""",
       new="""    if name.lower() not in existing:
      continue
    save(name, QgsPresetSchemeColorRamp""",
       test="test_ramp_swatches_and_palette_installation",
       why="the categorical palettes, installed by their own loop, "
           "reaching a fresh QGIS profile"),
  # Diagnosed 2026-08-10, with gradient-stop-positions below: the
  # style library lives in the user's QGIS profile, so on any machine
  # that has run the plugin before, ensure_ramps_installed() skips
  # every name and the test read ramps an earlier session had built
  # correctly. The test now removes the plugin's own tagged ramps and
  # has THIS code install them again before looking.
  dict(name="palette-end-colour", file=BRIDGE,
       old="        QColor(stops[0]), QColor(stops[-1]), False, gradient_stops)",
       new="        QColor(stops[0]), QColor(stops[-2]), False, gradient_stops)",
       test="test_installed_palettes_span_their_declared_colours",
       why="every installed sequential and diverging ramp reaching "
           "the colour it declares at its dark end, which is the end "
           "carrying the highest values on the map"),
  dict(name="conditional-column-hidden-index", file=DIALOG,
       # Re-diagnosed 2026-08-10 after this survived a sweep: the
       # construction-time hide is REDUNDANT for any dialog that
       # reaches a layer, because _update_dynamic_columns decides the
       # same columns moments later. Mutating the construction line
       # therefore tests nothing a user could see. What IS testable,
       # and what the why below names, is the decision itself, so the
       # entry now mutates that.
       old="    self.table.setColumnHidden(COL_EDIT_COLOURS, "
           "not has_editable)",
       new="    self.table.setColumnHidden(7, not has_editable)"
           "  # mutation: hides the wrong column"
           "  # mutation: hides the wrong column",
       # The entry named test_dialog_structure, which asserts the
       # table's SHAPE (nine columns, their headers) and never drives
       # the conditional hiding; the decision itself is exercised by
       # the column test below, which is where the strengthened
       # assertions went. Re-pointed 2026-08-10 after this survived a
       # sweep: an entry naming a test that cannot reach it is a
       # guard in name only.
       test="test_the_edit_colours_column_appears_with_categories",
       why="the conditional columns starting hidden, and hiding the "
           "ones they name: an off-by-one here leaves a dead column "
           "in front of a first-time user"),
  dict(name="outline-layer-not-marked-output", file=DIALOG,
       old='      outline_layer.setCustomProperty("weavingspace_output", True)',
       new='      outline_layer.setCustomProperty("weavingspace_output", False)',
       test="test_plugin_never_offers_its_own_output_as_a_region",
       why="the outlines layer being excluded from the region chooser "
           "like every other output. It is polygons of exactly the "
           "region, so it is the one most likely to be picked back up "
           "by mistake"),
  dict(name="swatch-direction-default", file=DIALOG,
       old="def _ramp_icon(name: str, reverse: bool = False):",
       new="def _ramp_icon(name: str, reverse: bool = True):",
       test="test_ramp_swatches_run_the_right_way_round",
       why="the swatch in the dropdown showing the ramp the way the "
           "map will draw it; reversed, the whole list disagrees with "
           "every map made from it"),
  # Diagnosed 2026-08-10: the named test read the bar AFTER the run,
  # by which time _finish_run has restored the determinate range
  # whatever happened during the tiling. It now reads it while the
  # task is in flight, which is the only moment the bar is what the
  # user is watching.
  dict(name="progress-range-per-run", file=DIALOG,
       old="""    self.generate_btn.setEnabled(False)
    self.progress.setVisible(True)
    self.progress.setRange(0, 100)""",
       new="""    self.generate_btn.setEnabled(False)
    self.progress.setVisible(True)""",
       test="test_a_new_run_always_shows_real_progress",
       why="a run reporting a percentage even after one that ended "
           "through the zombie recovery, which does not restore the "
           "determinate range the way _finish_run does"),
  dict(name="cancel-reports-immediately", file=WORKER,
       old="""    super().cancel()
    self._report(None, None)""",
       new="""    super().cancel()""",
       test="test_cancelling_frees_the_dialog_at_once",
       why="a cancelled run handing the dialog back at once, rather "
           "than when the abandoned work happens to finish"),
  dict(name="scale-controls-in-a-layout", file=DIALOG,
       old='    pair("Scale EW / NS", self.mod_scale_x, self.mod_scale_y)',
       new="    pass  # mutation: the Scale controls reach no layout",
       test="test_every_design_control_is_reachable",
       why="controls being reachable by a user and not only by a test "
           "that assigns to them directly"),
  # ACCEPTED PERMANENTLY, by the user's decision (2026-08-10): the
  # show-time fit STAYS, untested, because a defence against the
  # window opening too small is worth keeping even where no test can
  # reach it. Do not re-triage this as an open survivor, and do not
  # delete the third call site on the grounds that nothing catches
  # its removal. What follows is the evidence behind that decision.
  #
  # Two attempts to give this an
  # occasion of its own both failed on CLEAN code -- the window will
  # not grow past what the design needs (no element count makes the
  # Design tab taller) and will not shrink below it (layout minimums
  # hold it), so no state a test can produce distinguishes a dialog
  # that fits on show from one that does not. The construction fit
  # covers every path the suite can reach; the show-time fit is a
  # third call site whose occasion, if it has one, lives in real QGIS
  # (a re-show after a screen or DPI change). Kept rather than
  # deleted because deleting a defence nobody can test is how the
  # window opened too small in the first place -- but the honest next
  # step is a human decision about whether it earns its place, NOT a
  # test contorted into passing. One attempt briefly reported
  # "caught" because the test failed on clean code as well: a test
  # that always fails kills every mutant and proves nothing.
  dict(name="fit-to-design-on-show", file=DIALOG,
       # Narrowed 2026-08-10 (three call sites): anchored inside
       # showEvent, the deferred fit the named test drives; the others
       # fire on construction and on a family change.
       accepted=True,      # see the decision recorded above
       old="""    super().showEvent(event)
    QTimer.singleShot(0, self._fit_to_design)""",
       new="""    super().showEvent(event)
    pass  # mutation: the window keeps its built size""",
       test="test_the_window_fits_its_design_tab_when_shown",
       why="the window opening tall enough to show the Design tab it "
           "contains, and no taller. ACCEPTED, not a gap: measured "
           "again 2026-08-13, Qt clamps the window to its own "
           "minimumSizeHint on show (634px) whatever the constructor "
           "left it at (560px), and the tick brings it to 453px with "
           "or without this call site, because construction and family "
           "changes fit it too. A third attempt at a discriminating "
           "assertion failed like the two before it. Being caught here "
           "would be news"),
  dict(name="inset-percentage-divisor", file=DIALOG,
       old="        unit = unit.inset_tiles(self.mod_t_inset.value() * spacing / 100)",
       new="        unit = unit.inset_tiles(self.mod_t_inset.value() * spacing / 101)",
       test="test_an_inset_percentage_is_a_percentage_of_the_spacing",
       why="an inset percentage meaning that percentage of the "
           "spacing; a one percent error passes every comparison in "
           "the suite, whose tolerance is wider than the mistake"),
  dict(name="element-count-keys", file=CATALOG,
       old="  5: {",
       new="  6: {",
       test="test_every_element_count_still_has_its_designs",
       why="every element count the chooser offers actually having "
           "designs. A duplicated key does not misfile them, it "
           "DELETES them, and the other catalogue tests iterate "
           "whatever keys exist"),
  dict(name="square-slice-8-offset", file=CATALOG,
       old='"square-slice 8": dict(type="tiling", tiling_type="square-slice", n=8, offset=0)',
       new='"square-slice 8": dict(type="tiling", tiling_type="square-slice", n=8, offset=1)',
       test="test_every_declared_offset_is_pinned",
       why="every declared offset being pinned, not only the handful "
           "somebody thought to list; the element count is identical "
           "either way and the design is not"),
  dict(name="gradient-stop-positions", file=BRIDGE,
       old="        QgsGradientStop(i / (len(stops) - 1), QColor(c))",
       new="        QgsGradientStop(i / (len(stops) - 2), QColor(c))",
       test="test_installed_palettes_span_their_declared_colours",
       why="the interior colours of every installed ramp sitting "
           "where the palette declares. Both ends stay right, so a "
           "legend looks correct while the classes between are wrong"),
  dict(name="shells-default-value", file=DIALOG,
       old="    self.shells_spin.setValue(1)",
       new="    self.shells_spin.setValue(0)",
       test="test_every_control_starts_where_it_should",
       why="the preview opening with a ring of neighbours, where "
           "insetting and the joins between tiles can be seen"),
  dict(name="tile-inset-ceiling", file=DIALOG,
       old="    self.mod_t_inset = spin(0, 5, 0, 0.1)",
       new="    self.mod_t_inset = spin(0, 6, 0, 0.1)",
       test="test_every_control_accepts_the_range_it_should",
       why="the tile inset stopping at 5%, beyond which a weave's "
           "thin strands are swallowed"),
  dict(name="colour-warning-default-off", file=DIALOG,
       old='    self.opt_colour_warnings = QCheckBox(\n      "Warn about lack of legibility in colour choices")',
       new='    self.opt_colour_warnings = QCheckBox(\n      "Warn about lack of legibility in colour choices")\n    self.opt_colour_warnings.setChecked(True)',
       test="test_every_control_starts_where_it_should",
       why="the legibility opinion being asked for rather than "
           "offered unbidden on every map"),
  dict(name="preview-brush", file=DIALOG,
       old="      painter.setBrush(QBrush(QColor(colour)))",
       new="      pass  # mutation: no fill is ever set",
       test="test_the_preview_actually_draws_what_it_is_given",
       why="the preview filling its tiles at all; without a brush the design view is an empty box"),
  dict(name="preview-antialiasing", file=DIALOG,
       # Narrowed 2026-08-10 (the toggle switch paints too): anchored
       # to the PREVIEW's painter by the fill that follows it, which
       # is the surface the named test inspects.
       old="""    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.fillRect(self.rect(), QColor("#fafafa"))""",
       new="""    pass  # mutation: hard edges
    painter.fillRect(self.rect(), QColor("#fafafa"))""",
       # Still survived once the anchor was unique: the test's
       # smoothing check compared painted pixels against _id_colours,
       # which carry alpha and so match nothing that reaches the
       # picture, making "a colour between the fills" true of the
       # whole drawing. It now compares against the fills as painted
       # and requires a real share of the picture to sit between them
       # (measured 2.8% smoothed against 0.14% jagged).
       test="test_the_preview_actually_draws_what_it_is_given",
       why="edges being smoothed, which is most of why the preview reads as shapes rather than as stairs"),
  dict(name="preview-margin", file=DIALOG,
       old="    margin = 8",
       new="    margin = -60  # mutation: overflow the widget",
       test="test_the_preview_actually_draws_what_it_is_given",
       why="the drawing staying inside the widget it is drawn in"),
  dict(name="preview-centring", file=DIALOG,
       old="    ox = (self.width() - scale * w) / 2",
       new="    ox = 0  # mutation: hard against the left edge",
       test="test_the_preview_actually_draws_what_it_is_given",
       why="the unit sitting in the middle of the design view rather than jammed against one side"),
  dict(name="preview-scale", file=DIALOG,
       old="""    scale = min((self.width() - 2 * margin) / w,
                (self.height() - 2 * margin) / h)""",
       new="""    scale = max((self.width() - 2 * margin) / w,
                (self.height() - 2 * margin) / h)""",
       test="test_the_preview_actually_draws_what_it_is_given",
       why="fitting the unit to the SMALLER dimension, so it fits in both; the larger overflows the other axis"),
  dict(name="outline-casing", file=BRIDGE,
       old="  sym.appendSymbolLayer(narrow.symbolLayer(0).clone())",
       new="  pass  # mutation: the dark line over the casing is lost",
       test="test_region_outlines_are_cased",
       why="region boundaries staying legible over both pale and dark "
           "parts of the pattern, which one line alone cannot do"),
  dict(name="live-update-default", file=DIALOG,
       old="    self.live_check.setChecked(True)",
       new="    pass  # mutation: live update starts off",
       test="test_live_update_is_on_by_default",
       why="a first map appearing without the user having to find the "
           "Generate button"),
  # family-list-signals-blocked was removed 2026-08-12: DEMONSTRATED
  # EQUIVALENT, and the demonstration disproved this entry's own
  # reason. Unblocking the family list makes _on_family_changed run
  # three times instead of once, and the handler is idempotent -- the
  # unit is rebuilt exactly as often, because the extra calls fall
  # inside the same debounce. A catalogue entry is a claim that
  # breaking something makes a named test fail; no test can fail on a
  # mutation with no observable difference, so the claim was false
  # and the entry was reporting a gap that did not exist. The
  # evidence is in EQUIVALENT in tools/mutate_auto.py.
  dict(name="editor-value-column-width", file=EDITOR,
       old="VALUE_WIDTH = 125",
       new="VALUE_WIDTH = 200",
       test="test_the_editor_is_laid_out_as_specified",
       why="the settled width of the value column, which the window "
           "is then sized to"),
  dict(name="editor-visible-rows", file=EDITOR,
       old="VISIBLE_ROWS = 15",
       new="VISIBLE_ROWS = 40",
       test="test_the_editor_scrolls_only_past_fifteen_values",
       why="the table scrolling rather than growing past fifteen "
           "values, so a field with forty categories cannot open a "
           "window taller than the screen"),
  dict(name="editor-scrollbar-room", file=EDITOR,
       old="""    if rows > VISIBLE_ROWS:
      width += self.table.verticalScrollBar().sizeHint().width()""",
       new="""    pass  # mutation: no room made for the scroll bar""",
       test="test_the_editor_scrolls_only_past_fifteen_values",
       why="the colour column surviving the arrival of a scroll bar, "
           "which takes its width from the viewport rather than "
           "adding to it"),
  # Re-anchored 2026-08-10: the editor now serves graduated elements
  # too, so the table is built in two branches and BOTH right-align.
  # The trailing NO_DATA_KEY line pins this at the categorical branch,
  # which is the one the test builds (it passes no bounds).
  dict(name="editor-value-alignment", file=EDITOR,
       old="""        cell.setTextAlignment(Qt.AlignmentFlag.AlignRight
                              | Qt.AlignmentFlag.AlignVCenter)
        if _is_absence(value):""",
       new="""        pass  # mutation: values fall back to left-aligned
        if _is_absence(value):""",
       test="test_the_editor_is_laid_out_as_specified",
       why="values set right against colours set left, so the eye "
           "runs down one gap rather than across a ragged one"),
  dict(name="category-colour-override", file=BRIDGE,
       old="""    if str(v) in overrides:""",
       new="""    if False:  # mutation: hand-picked colours ignored""",
       test="test_editing_a_category_colour_reaches_the_map",
       why="a colour chosen in the Categorical colour editor being "
           "the colour the map actually draws"),
  # Re-anchored 2026-08-10: the signature tuple has grown the
  # graduated customization terms, so the picks are no longer its last
  # element. Deleting the line still removes them from the tuple.
  dict(name="category-colours-in-signature", file=DIALOG,
       old="""            a.get("reverse", False), a.get("opacity", 100),
            tuple(sorted(picked.items())),""",
       new="""            a.get("reverse", False), a.get("opacity", 100),
            # mutation: picks invisible to the restyle path""",
       test="test_editing_a_category_colour_reaches_the_map",
       why="the fast path noticing a hand-picked colour at all; "
           "without it the element is skipped as unchanged"),
  # Narrowed 2026-08-13. This entry used to replace the whole
  # re-read LOOP with `pass`, which was harmless while the loop had
  # one branch and became a trap the moment it gained the graduated
  # one below: the mutation would have left a dangling `elif` and
  # killed the test with a SyntaxError, which is a pass for the
  # wrong reason and exactly the kind of false positive this
  # catalogue exists to avoid. Both entries now cut only their own
  # assignment, so each proves its own half of the fix.
  dict(name="category-colours-reread-after-run", file=DIALOG,
       old="""        a["category_colours"] = self._category_colours.get(
          a["id"], {}).get(a["var"])""",
       new="""        pass  # mutation: the run's stale snapshot wins""",
       test="test_a_colour_picked_during_a_run_is_not_lost",
       why="a colour picked while a tiling was finishing surviving "
           "that tiling, rather than being overwritten by the "
           "settings the run started with"),
  # The row's symbology across a reopen (maintainer's decision,
  # 2026-08-13: preserve where we can, else reload the classes,
  # count them, and call it Custom). Three entries because three
  # separate things have to hold, and one anchor covering them all
  # would report SURVIVED whenever any one of them still worked.
  # SPLIT IN TWO on 2026-08-13, because one anchor matched BOTH
  # follow branches. The catalogue's own rule: mutating one twin
  # while the other goes on doing the work reports SURVIVED whatever
  # the tests do -- and here it was worse, since an anchor matching
  # twice makes the tool exit rather than judge, and nothing noticed
  # because nothing runs the catalogue.
  dict(name="follow-branch-clears-the-stamp-categorized", file=DIALOG,
       old="""          # the CATEGORIZED half of this branch
          self._stamp_category_colours(layer, refreshed)""",
       new="""          pass  # mutation: the discarded pick stays stamped""",
       test="test_a_discarded_pick_does_not_come_back",
       why="a colour the plugin ANNOUNCED as discarded actually "
           "being gone. The dicts are cleared and the user is told "
           "the ramp governs; leave the stamp behind and the pick "
           "returns on reopen, painted over the ramp they chose, "
           "with the signature stamped so no restyle heals it"),
  dict(name="follow-branch-clears-the-stamp-graduated", file=DIALOG,
       old="""          # the GRADUATED half of this branch
          self._stamp_category_colours(layer, refreshed)""",
       new="""          pass  # mutation: the discarded pick stays stamped""",
       test="test_a_discarded_pick_does_not_come_back",
       why="a colour the plugin ANNOUNCED as discarded actually "
           "being gone. The dicts are cleared and the user is told "
           "the ramp governs; leave the stamp behind and the pick "
           "returns on reopen, painted over the ramp they chose, "
           "with the signature stamped so no restyle heals it"),
  dict(name="run-signature-carries-the-picks", file=DIALOG,
       old="""             tuple(sorted((a.get("category_colours") or {}).items())),""",
       new="""             # mutation: the live guard cannot see a pick""",
       test="test_a_pick_is_not_swallowed_by_the_live_path",
       why="the live tick RETURNS on an unchanged run signature "
           "before it reaches the restyle path, so a hand-picked "
           "colour missing from this tuple can never be applied "
           "under live update at all -- the editor and the table "
           "both showing it while the map goes on without it"),
  dict(name="existing-geopackage-is-never-recreated", file=DIALOG,
       old="""                                      first=(first_gpkg_layer
                                             and not os.path.exists(path)))""",
       new="""                                      first=first_gpkg_layer)""",
       test="test_a_generate_spares_the_rest_of_the_users_geopackage",
       why="the plugin never destroying data it did not create. "
           "Recreating an existing GeoPackage wipes every other "
           "table in it -- the user's own layers, and the region "
           "layer itself where it lives there, in which case the "
           "map is drawn from data the same run deleted, silently, "
           "because an open layer answers featureCount from cache"),
  dict(name="shrunk-design-tidies-its-geopackage", file=DIALOG,
       old="""      for stale in sorted(written):
        name = stale if stale.startswith("tiles_") else f"tiles_{stale}"
        if name not in current:
          bridge.drop_gpkg_layer(path, name)""",
       new="""      pass  # mutation: dropped elements stay in the file""",
       test="test_a_geopackage_loses_the_elements_a_design_dropped",
       why="the exported file describing the design that exists. A "
           "GeoPackage is replaced table by table, so a session that "
           "shrinks leaves its old elements behind -- and that file "
           "is the artefact that LEAVES, so the person who made it "
           "never sees the fault their colleague opens"),
  dict(name="ramps-installed-before-adoption", file=DIALOG,
       # the ordering bug as it actually happened: adoption ran two
       # lines before the ramp list existed, so every lookup threw
       # and every adopted element fell through to Custom
       old="""    bridge.ensure_ramps_installed()
    self._ramp_names = bridge.ramp_names()
    self._adopt_existing_group()""",
       new="""    self._adopt_existing_group()
    bridge.ensure_ramps_installed()
    self._ramp_names = bridge.ramp_names()""",
       test="test_a_project_round_trip_changes_nothing_a_user_chose",
       why="adoption asking which library ramp draws a reopened "
           "layer, at a moment when the library has been read. Run "
           "it first and no ramp can ever be named, so every "
           "reopened element reads Custom -- the map survives, but "
           "every ramp name a user chose is gone"),
  dict(name="reopened-ramp-read-off-the-layer", file=DIALOG,
       old="""    if named and tile_id not in self._ramp_choices:
      self._ramp_choices[tile_id] = named""",
       new="""    pass  # mutation: the ramp is not read back""",
       test="test_a_project_round_trip_changes_nothing_a_user_chose",
       why="the ramp a user chose surviving a save and reopen. "
           "Without it the table shows a default ramp beside a layer "
           "drawing another, and the next Generate pushes the "
           "table's belief onto the map"),
  dict(name="reopened-classes-recovered-as-custom", file=DIALOG,
       old="""    if recovered and (expected is not None or not named):
      self._quant_colours.setdefault(tile_id, {})[field] = recovered""",
       new="""    pass  # mutation: unnameable colours are not recovered""",
       test="test_a_graduated_dock_recolour_survives_the_plugin_being_shut",
       why="an element whose drawn colours the ramp does not explain "
           "comes back carrying those exact colours; without it the "
           "row claims a ramp that is not what is drawn, and the next "
           "Generate makes the map agree with the claim. RE-POINTED "
           "2026-08-16: this entry named the reversed ramp as its "
           "everyday case and pointed at a round-trip test, and both "
           "halves had gone stale -- since reversed ramps came back "
           "NAMED with a flip flag, that test stopped driving this "
           "line, and the entry SURVIVED the moment it was "
           "re-anchored. The behaviour is unchanged and still worth "
           "guarding; what changed is which journey reaches it"),
  dict(name="greyed-reverse-keeps-its-record", file=DIALOG,
       # The mutation is the code as it stood before 2026-08-13:
       # restore the switch's report verbatim, and a rebuild while
       # Reverse was greyed writes its False over the user's tick.
       old="""        self._reverse_choices[tid] = bool(prev["reverse"]) \\
            or self._reverse_choices.get(tid, False)""",
       new="""        self._reverse_choices[tid] = prev["reverse"]""",
       test="test_a_reverse_tick_survives_a_rebuild_while_it_is_greyed",
       why="a Reverse tick surviving a table rebuild that happens "
           "while the switch is greyed, rather than the disabled "
           "switch's report being allowed to speak for what the "
           "user chose"),
  dict(name="dock-classes-matched-by-length", file=DIALOG,
       # Anchored on the CONDITION rather than the whole guard: the
       # comment below it explains the constant-column collapse and
       # is worth keeping in front of whoever reads a failure here.
       old="""    if len(expected) != len(actual):""",
       new="""    if False:  # mutation: walk two lists of different lengths""",
       test="test_a_dock_classify_on_a_constant_column_does_not_crash",
       why="the positional walk over dock classes staying inside "
           "both lists; without it a Classify over a collapsed "
           "constant column raises IndexError inside a renderer "
           "signal handler, where the user sees nothing at all"),
  dict(name="quant-colours-reread-after-run", file=DIALOG,
       old="""          a["quant_colours"] = self._quant_colours.get(
            a["id"], {}).get(a["var"])""",
       new="""          pass  # mutation: the run's stale snapshot wins""",
       test="test_a_class_colour_picked_during_a_run_is_not_lost",
       why="the graduated half of the same race: a class colour "
           "picked while a tiling was finishing surviving it, "
           "rather than being destroyed by the run it was made "
           "during and stamped absent onto the layer as well"),
  dict(name="category-colours-cleared-by-ramp", file=DIALOG,
       # Narrowed 2026-08-12 (two sites). This is the primary path,
       # where choosing a ramp replaces the element's source of
       # truth; the other sits behind a showing_custom() guard.
       old="""        # reselected anew", settled 2026-08-09)
        self._clear_category_colours(tid, "a new colour ramp")""",
       new="""        # reselected anew", settled 2026-08-09)
        pass  # mutation: hand-picks outlive the ramp change""",
       test="test_a_new_ramp_discards_hand_picks_and_says_so",
       why="choosing a ramp meaning what it says, and the user being "
           "told which hand-picked colours it cost them"),
  dict(name="category-colours-stamped-on-layer", file=DIALOG,
       old="""      layer.setCustomProperty(
        "weavingspace_category_colours",
        json.dumps({"field": assignment["var"], "colours": picked},
                   sort_keys=True))""",
       new="""      pass  # mutation: nothing recorded for the project file""",
       test="test_hand_picked_colours_are_written_into_the_project",
       why="hand-picked colours outliving the session, so reopening a "
           "saved project and pressing Generate does not silently "
           "revert them"),
  # Re-anchored 2026-08-10, and the WHY with it: since the quant round
  # the editor serves graduated elements too, so the column's
  # condition widened from "any categorical element" to "any element
  # drawn in classes". The behaviour guarded is unchanged -- a column
  # that withdraws when nothing in the map has classes to edit.
  dict(name="edit-colours-column-visibility", file=DIALOG,
       old="""    self.table.setColumnHidden(COL_EDIT_COLOURS, not has_editable)""",
       new="""    self.table.setColumnHidden(COL_EDIT_COLOURS, False)"""
           """  # mutation: always on""",
       test="test_the_edit_colours_column_appears_with_categories",
       why="the column appearing only where some element draws in "
           "classes -- categorized or graduated -- rather than as a "
           "dead control on a map of flat fills"),
  dict(name="notices-share-one-line", file=DIALOG,
       old="""    self.live_note.setText(
      f"{existing}{NOTE_SEPARATOR}{message}" if existing else message)""",
       new="""    self.live_note.setText(message)"""
           """  # mutation: last notice wins""",
       test="test_two_notices_from_one_run_both_survive",
       why="a run with several things wrong reporting all of them, "
           "rather than only whichever was computed last"),
  dict(name="shells-spinner-layout", file=DIALOG,
       old="shells_row.addWidget(self.shells_spin)",
       new="pass  # mutation: the spinner is never added to a layout",
       test="test_the_dialogs_chrome_does_its_job",
       why="the context-shells control being reachable at all"),
  dict(name="optional-matplotlib-patch", file=VENDOR_TILEABLE,
       old="""except ImportError:
  from weavingspace._optional import MissingModule
  plt = MissingModule("matplotlib.pyplot")""",
       new="""except ImportError:
  raise  # mutation: the plugin's patch reverted to upstream""",
       test="test_the_library_works_without_matplotlib_or_scipy",
       why="the vendored library importing at all where matplotlib is "
           "absent, which is most Linux QGIS installations"),
  dict(name="over-under-connect", file=DIALOG,
       old="self.opt_over_under.textChanged.connect(self._queue_preview)",
       new="pass  # mutation: typing a pattern reaches nothing",
       test="test_no_control_is_dead",
       why="the over-under pattern field acting through its own "
           "signal; the walk claims to cover every control, and this "
           "is the check on that claim"),
  dict(name="dead-control-walk", file=DIALOG,
       old="self.spacing_spin.valueChanged.connect(self._queue_preview)",
       new="pass  # mutation: the spacing control reaches nothing",
       test="test_no_control_is_dead",
       why="the systematic walk itself: if deleting a connection does "
           "not fail it, the walk is decoration. Spacing is the "
           "control chosen here because its effect is unmistakable"),
  dict(name="nice-number-base", file=DIALOG,
       old="mant = x / 10 ** exp",
       new="mant = x / 11 ** exp",
       test="test_auto_spacing_offers_a_round_number",
       why="the Auto button proposing 2500 rather than 2371.8438"),
  dict(name="preview-patch-centre", file=DIALOG,
       old="patch = unit.get_local_patch(r=shells, include_0=True)",
       new="patch = unit.get_local_patch(r=shells, include_0=False)",
       test="test_preview_draws_the_middle_of_the_patch",
       why="the centre of the pattern being drawn at all, with "
           "context shells on"),
  dict(name="signature-layer-identity", file=DIALOG,
       # Narrowed 2026-08-10: the geometry signature and the run
       # signature open with the same line, so the bare anchor
       # mutated whichever came first while the other went on
       # noticing the change. Anchored to _run_signature by its
       # docstring, which is the one the named test drives.
       old="""    (reopening the dialog, for instance, changes nothing)."\"\"
    layer = self.layer_combo.currentLayer()
    kwargs = self._unit_kwargs()
    kwargs.pop("spec", None)
    return (
      layer.id() if layer is not None else None,""",
       new="""    (reopening the dialog, for instance, changes nothing)."\"\"
    layer = self.layer_combo.currentLayer()
    kwargs = self._unit_kwargs()
    kwargs.pop("spec", None)
    return (
      layer.id() if layer is None else None,""",
       # And it went on surviving with the anchor narrowed, because
       # the two layers the test switched between differ in extent:
       # the layer FINGERPRINT, which is in the same tuple, noticed
       # the change and the identity term was never needed. The test
       # now also switches to a layer the fingerprint cannot tell
       # apart -- same areas, same columns, same CRS, different
       # numbers -- and requires live update to redraw.
       test="test_switching_region_layer_counts_as_a_change",
       why="a different region layer counting as a change, rather "
           "than leaving the previous layer's map on screen"),
  # Re-anchored 2026-08-10: the mark used to be set by a lambda on the
  # combo's ``activated`` signal. That lambda now calls
  # _on_mode_chosen, which sets the mark on its first line, so the
  # behaviour lives one call deeper and the anchor follows it there.
  dict(name="chooser-race", file=DIALOG,
       old='    mode_combo.setProperty("touched", True)',
       new="    pass  # mutation: a hand-picked style is never remembered",
       test="test_style_follow_and_memory",
       why="the hook that remembers a hand-picked style (now the first "
           "line of _on_mode_chosen); without it every style goes on "
           "following the field's type and the user's own pick is "
           "overwritten the next time the variable changes"),
  dict(name="class-source-memory", file=DIALOG,
       old='default = self._class_choices.get(tid, "")',
       new='default = ""',
       test="test_choice_persistence_and_recovery",
       why="per-element colourmap source surviving a rebuild"),
  dict(name="selective-reseed", file=DIALOG,
       old="        out.setRenderer(old_renderers[tid])",
       new="        pass  # mutation: always re-seed, discarding hand work",
       test="test_output_management",
       why="hand styling kept when an element's assignment is unchanged"),
  dict(name="live-gpkg-gate", file=DIALOG,
       old="if self.gpkg_widget.filePath().strip() or \\",
       new="if False or \\",
       test="test_live_update_gates",
       why="live update declining to rewrite a GeoPackage on every tweak"),
  dict(name="group-adoption", file=DIALOG,
       old="    self._adopt_existing_group()",
       new="    pass  # mutation: adoption disabled",
       test="test_integration_second_dialog_session",
       why="a reopened dialog adopting the existing output group"),
  dict(name="output-tagging", file=DIALOG,
       old='      out.setCustomProperty("weavingspace_output", True)',
       new="      pass  # mutation: output not tagged",
       test="test_integration_region_layer_switch",
       why="outputs excluded from the region chooser"),
  dict(name="unclassed-intervals", file=BRIDGE,
       old='scheme, k = "Equal intervals", 50',
       new='scheme, k = "Equal intervals", 10',
       test="test_renderer_seeding",
       why="Quant: Unclassed cutting exactly 50 linear intervals"),
  dict(name="categorical-sampling", file=BRIDGE,
       old="idx = min(int(i * len(preset) / (n - 1)), len(preset) - 1) \\",
       new="idx = min(round(i * (len(preset) - 1) / (n - 1)), "
           "len(preset) - 1) \\",
       test="test_renderer_seeding",
       why="ListedColormap sampling of preset schemes (the tab10 bug)"),
  # --- the 2026-08-07 depth audit: one entry per behaviour whose
  # loss would be quiet and expensive. A mutation that SURVIVES
  # names a perfunctory test, and the fix is a sharper assertion
  # in that test, never a smaller catalogue here.
  dict(name='opacity-applied', file=DIALOG,
       old='        out.setOpacity(max(0, min(100, a.get("opacity", 100))) / 100.0)',
       new='        pass  # mutation: opacity never reaches the layer',
       test='test_element_opacity',
       why='the Opacity cell actually reaching the map'),
  dict(name='opacity-authority', file=DIALOG,
       old='          out.setOpacity(old_layer_opacity[tid])',
       new='          pass  # mutation: hand-set opacity discarded',
       test='test_element_opacity',
       why='an opacity set by hand in QGIS surviving regeneration'),
  dict(name='restyle-fast-path', file=DIALOG,
       old='    if self.opt_new_group.isChecked():',
       new='    if True:  # mutation: never restyle, always re-tile',
       test='test_restyle_without_retiling',
       why='style changes repainting instead of re-tiling'),
  dict(name='reverse-ramp', file=BRIDGE,
       old='  if not reverse:\n    return ramp',
       new='  if True:  # mutation: reversal ignored\n    return ramp',
       test='test_reverse_ramp_column',
       why='the Reverse box turning the ramp around'),
  dict(name='preview-opacity-floor', file=DIALOG,
       old='  PREVIEW_MIN_OPACITY = 40',
       new='  PREVIEW_MIN_OPACITY = 0  # mutation: no floor',
       test='test_opacity_in_preview',
       why='the preview staying readable at low opacity'),
  dict(name='run-lifecycle-order', file=DIALOG,
       old='    self.progress.setRange(0, 0)',
       new='    self._finish_run()  # mutation: clear the task too early',
       test='test_run_lifecycle_no_overlap',
       why='one run at a time, across the output-building phase'),
  dict(name='stale-unit-flush', file=DIALOG,
       old='      self._preview_timer.stop()\n      self._rebuild_unit()',
       new='      pass  # mutation: generate with the stale unit',
       test='test_generate_uses_the_design_on_screen',
       why='Generate using the design on screen, not the previous one'),
  dict(name='identity-transform-skip', file=DIALOG,
       old='    if self.mod_rotate.value():\n      unit = unit.transform_rotate(self.mod_rotate.value())',
       new='    unit = unit.transform_rotate(self.mod_rotate.value())',
       test='test_ui_library_weave_parameters',
       why='identity modifiers not perturbing tie-prone joins'),
  dict(name='unassigned-sticks', file=DIALOG,
       old='      elif prev is not None and prev["var"] is None \\\n          and not self._fieldless_build:',
       new='      elif False:',
       test='test_ui_library_categorical_template',
       why='an element left on --- staying unassigned'),
  dict(name='geometry-repair', file=BRIDGE,
       old='    gdf.loc[bad, "geometry"] = gdf.loc[bad, "geometry"].make_valid()',
       new='    pass  # mutation: invalid geometry passed through',
       test='test_awkward_geometry',
       why='invalid input geometry being repaired before tiling'),
  dict(name='null-normalisation', file=BRIDGE,
       old='      data[f].append(None if v == NULL or v is None else v)',
       new='      data[f].append(v)  # mutation: QGIS NULL passed through',
       test='test_awkward_geometry',
       equivalent=True,
       why='QGIS NULLs becoming real nulls in the frame -- EQUIVALENT '
           'on QGIS 4: an attribute set to NULL reads back as Python '
           'None (verified for numeric and string fields, memory and '
           'GeoPackage providers), so normalising it is a no-op and '
           'no test can tell the two apart'),
  # Re-anchored 2026-08-10: the catch-all's fill is now taken from the
  # editor's overrides (under NO_DATA_KEY) before falling back to
  # NO_DATA_FILL, so the call spans three lines. Same class, same loss
  # if it goes.
  dict(name='no-data-class', file=BRIDGE,
       old='  categories.append(QgsRendererCategory(\n'
           '    None, _fill_symbol(overrides.get(NO_DATA_KEY, NO_DATA_FILL), outline),\n'
           '    "no data"))',
       new='  pass  # mutation: no catch-all class for unmatched values',
       test='test_renderer_seeding',
       why='the no-data class that catches unmatched values'),
  dict(name='tile-outline-flag', file=BRIDGE,
       old='  opts.update({"outline_color": "35,35,35,255", "outline_width": "0.1"}\n              if outline else {"outline_style": "no"})',
       new='  opts.update({"outline_style": "no"})  # mutation: never outline',
       test='test_integration_weave_and_icons',
       why='the Draw tile boundaries switch reaching the symbols'),
  dict(name='gpkg-style-embed', file=DIALOG,
       old='        bridge.embed_style(out)',
       new='        pass  # mutation: styles not written into the file',
       test='test_integration_gpkg_style_round_trip',
       why='a GeoPackage carrying its own cartography'),
  # --- second wave, aimed at the integration and UI-vs-library
  # tests: each severs a control from the library call it drives.
  # These are the mutations that tell us whether those tests are
  # really comparing behaviour or merely agreeing with themselves.
  dict(name='switch-clip-ignored', file=DIALOG,
       old='    ragged = not self.opt_clip.isChecked()',
       new='    ragged = True  # mutation: the clip switch stops mattering',
       test='test_ui_library_clipped_edges',
       why='the Clip by map units switch reaching the tiling'),
  dict(name='switch-join-ignored', file=DIALOG,
       old='    join_proto = self.opt_join_prototiles.isChecked()',
       new='    join_proto = False  # mutation: whole-tileable join ignored',
       # pointed at the SLICE scenario, not the icons one: in icon mode
       # each unit already sits inside a single polygon, so joining on
       # whole tileables changes no data and no test there could catch
       # this. Measured, not assumed.
       test='test_ui_library_slice_modifiers',
       why='the whole-tileable join switch reaching the tiling'),
  dict(name='switch-icons-ignored', file=DIALOG,
       old='    as_icons = self.opt_icons.isChecked()',
       new='    as_icons = False  # mutation: icon mode ignored',
       test='test_ui_library_icons_and_join',
       why='icon mode reaching the tiling'),
  dict(name='switch-retain-ignored', file=DIALOG,
       old='    retain = self.opt_retain.isChecked()',
       new='    retain = False  # mutation: retain-tileables ignored',
       test='test_ui_library_slice_modifiers',
       why='the retain-complete-tileables switch reaching the tiling'),
  dict(name='grid-rows-cols-ignored', file=CATALOG,
       old='      kwargs["nrows"], kwargs["ncols"] = (\n        (nrows, ncols) if nrows and ncols else tightest_grid(spec["n"]))',
       new='      kwargs["nrows"], kwargs["ncols"] = tightest_grid(spec["n"])',
       test='test_ui_library_grid_rows_cols',
       why='the grid row and column spinners reaching the unit'),
  dict(name='weave-inset-not-scaled', file=DIALOG,
       old='      unit = unit.inset_tiles(\n        self.mod_t_inset.value() * self.opt_aspect.value() * spacing / 100)',
       new='      unit = unit.inset_tiles(self.mod_t_inset.value() * spacing / 100)',
       test='test_ui_library_weave_parameters',
       why="a weave's tile inset being scaled by strand width"),
  dict(name='skew-ignored', file=DIALOG,
       old='      unit = unit.transform_skew(self.mod_skew_x.value(),\n                                 self.mod_skew_y.value())',
       new='      pass  # mutation: skew never applied',
       test='test_ui_library_modifier_chain',
       why='skew reaching the unit'),
  dict(name='prototile-inset-ignored', file=DIALOG,
       old='        unit = unit.inset_prototile(\n          self.mod_p_inset.value() * spacing / 100)',
       new='        pass  # mutation: group inset never applied',
       test='test_ui_library_modifier_chain',
       why='the group (prototile) inset reaching the unit'),
  dict(name='selective-reseed-inverted', file=DIALOG,
       # RE-ANCHORED 2026-08-16: the condition became a named flag,
       # `kept_by_hand`, so that the paired no-data layer could be put
       # through the same gate. The three entries that stood on the
       # old `if` line matched nothing for the length of that commit,
       # which is a mutation that applies nothing and reports nothing.
       old='      kept_by_hand = ((unchanged or carried_while_deferring)\n'
           '                      and not reclaimed)',
       new='      kept_by_hand = not unchanged  # mutation: WRONG renderer',
       test='test_integration_interleaved_session',
       why='hand styling kept for unchanged elements only'),
  dict(name='outline-layer-not-on-top', file=DIALOG,
       old='      group.insertLayer(0, outline_layer)',
       new='      group.addLayer(outline_layer)  # mutation: buried at the bottom',
       test='test_integration_weave_and_icons',
       why='region outlines drawn on top of the elements'),
  # RE-ANCHORED 2026-08-25: the name is worked out by
  # `element_table_name` now rather than spelled at the call, so the
  # mutation goes on what the writer is HANDED. The claim is
  # unchanged -- every element gets its own table inside the file --
  # and giving them all one name is still how it fails.
  dict(name='gpkg-layer-naming', file=DIALOG,
       old='        out = bridge.write_gpkg_layer(mem, path, table_name,',
       new='        out = bridge.write_gpkg_layer(mem, path, "tiles_x",',
       test='test_ui_library_categorical_to_gpkg',
       why='each element getting its own layer inside the GeoPackage'),
  dict(name='categorical-template-ignored', file=DIALOG,
       old='          out, a, templates.get(a.get("class_source")),',
       new='          out, a, None,  # mutation: imported mapping dropped',
       test='test_ui_library_categorical_template',
       why='an imported colour mapping reaching the map'),
  # --- controls whose EFFECT nothing asserted until the sweep
  dict(name='offset-angle-ignored', file=CATALOG,
       old='      kwargs["offset_angle"] = (spec["offset_angle"] if offset_angle is None\n                                else offset_angle)',
       new='      kwargs["offset_angle"] = spec["offset_angle"]  # mutation',
       test='test_ui_library_dissection_angles',
       why='the dissection inner-angle control reaching the unit'),
  dict(name='point-angle-ignored', file=CATALOG,
       old='      kwargs["point_angle"] = (spec["point_angle"] if point_angle is None\n                               else point_angle)',
       new='      kwargs["point_angle"] = spec["point_angle"]  # mutation',
       test='test_ui_library_star_point_angle',
       why='the star point-angle control reaching the unit'),
  dict(name='glyph-flag-ignored', file=DIALOG,
       old='        self.mod_scale_x.value(), self.mod_scale_y.value(),\n        self.mod_glyph.isChecked())',
       new='        self.mod_scale_x.value(), self.mod_scale_y.value(),\n        False)  # mutation: glyph scaling ignored',
       test='test_ui_library_glyph_scaling',
       why='the glyph checkbox changing what scaling means'),
  dict(name='single-instance-rule', file=DIALOG,
       old='    self._retire_previous_instance()',
       new='    pass  # mutation: two live dialogs allowed',
       test='test_single_dialog_instance',
       why='only one dialog live per QGIS session'),
  # Re-anchored 2026-08-10: the same line now also names
  # SPATIAL_INDEX. The mutation drops ONLY the FID rename, so this
  # entry still asks about the fid collision alone rather than
  # doubling as a spatial-index test (which has its own entry,
  # memory-layers-lose-their-index).
  dict(name='gpkg-fid-collision', file=BRIDGE,
       # RE-ANCHORED 2026-08-25: the column's name is a constant now,
       # because a region read back out of one of our own files
       # arrives carrying it and the dialog has to know not to offer
       # it. The claim is unchanged.
       old='  options.layerOptions = [f"FID={GPKG_FID_COLUMN}", "SPATIAL_INDEX=YES"]',
       new='  options.layerOptions = ["SPATIAL_INDEX=YES"]'
           '  # mutation: let an fid attribute collide with the key',
       test='test_gpkg_fid_attribute',
       why='exporting data that carries an attribute called fid'),
  dict(name="crs-reattach", file=DIALOG,
       old="    self._adopt_existing_group()",  # placeholder, replaced below
       new="    self._adopt_existing_group()",
       test="test_real_world_data",
       why="the output CRS surviving the worker round trip"),
  # ---- the 2026-08-09 interface round (nine settled changes plus the
  # QGIS-side restyle watcher), each proved able to fail
  dict(name="reverse-allowed-on-categorized", file=DIALOG,
       old='    can_reverse = has_ramp and mode != "Categorized"',
       new='    can_reverse = has_ramp'
           '  # mutation: categorized rows reverse again',
       test="test_reverse_ramp_column",
       why="Reverse is greyed on Categorized rows entirely and "
           "re-enables when a quantitative style is chosen; category "
           "colours are named assignments, not a scale with a "
           "direction (user decision, 2026-08-09)"),
  # Re-anchored 2026-08-10: `renderer.ranges()` is now read once into
  # `count` (the list hands back temporaries, so calling it twice is
  # its own hazard), and the Ramp Display Range arrived as an `elif`
  # beside it. The mutation still sends the constant case past the
  # midpoint recolour and back to whatever QGIS coloured it.
  dict(name="constant-class-takes-ramp-start", file=BRIDGE,
       old='  if distinct == 1 and count == 1:',
       new="  if False and count == 1:  # mutation: keep QGIS's endpoint colour",
       test="test_a_constant_column_draws_one_class_and_says_so",
       why="a constant column's single class draws the MIDDLE of its "
           "ramp (of the display window, where one has been narrowed); "
           "the ramp's start is near-white on sequential ramps and "
           "reads as no data (user decision, 2026-08-09)"),
  dict(name="custom-display-never-shows", file=DIALOG,
       old="        show_custom = bool(picks) or has_source",
       new="        show_custom = False"
           "  # mutation: the cell always names a ramp",
       test="test_a_customized_element_reads_custom",
       why="a categorized row with hand-picks or an imported class "
           "source must read Custom, or the cell names a ramp an "
           "override is outranking -- a control lying about the map"),
  dict(name="same-ramp-pick-keeps-picks", file=DIALOG,
       old="    ramp_combo.activated.connect(picked)",
       new="    pass  # mutation: re-choosing the same ramp is ignored",
       test="test_a_customized_element_reads_custom",
       why="re-choosing the ramp already underneath the Custom display "
           "fires only ``activated`` (the index is unchanged) and must "
           "still destroy the picks; without the connection the cell "
           "exits Custom while the overrides quietly survive"),
  dict(name="custom-swatch-goes-stale", file=DIALOG,
       # Narrowed 2026-08-10: the graduated branch added a second,
       # identical guard, so this anchor matched twice, only the first
       # was mutated, and the categorical branch went on invalidating
       # correctly -- the entry reported SURVIVED whatever the tests
       # did. Anchored now to the CATEGORICAL site by the line above
       # it, which is the branch the named test drives.
       old="""    picks = assignment.get("category_colours") or {}
    key = (field, assignment.get("ramp"), assignment.get("reverse"),
           assignment.get("class_source"),
           tuple(sorted(picks.items())))
    cached = self._custom_swatch_cache.get(tile_id)
    if cached is not None and cached[0] == key:""",
       new="""    picks = assignment.get("category_colours") or {}
    key = (field, assignment.get("ramp"), assignment.get("reverse"),
           assignment.get("class_source"),
           tuple(sorted(picks.items())))
    cached = self._custom_swatch_cache.get(tile_id)
    if cached is not None:  # mutation: serve any cached swatch""",
       test="test_a_customized_element_reads_custom",
       why="the Custom swatch is rebuilt whenever anything deciding "
           "the element's colours changes; a stale cache shows the "
           "previous pick, not the map"),
  dict(name="row-gutter-returns", file=DIALOG,
       old="    self.table.verticalHeader().setVisible(False)",
       new="    pass  # mutation: Qt's row-number gutter returns",
       test="test_the_table_headers_read_as_designed",
       why="Qt's row-number gutter drew 1, 2, 3, 4 beside tile ids "
           "a, b, c, d: two columns of identifiers, one meaningless "
           "(user report, 2026-08-09)"),
  dict(name="table-may-scroll-sideways", file=DIALOG,
       old="    self.table.setMinimumWidth(needed)",
       new="    pass  # mutation: the table takes whatever width falls out",
       test="test_the_window_fits_the_narrowest_screen",
       why="the table never scrolls horizontally: a horizontal "
           "scrollbar on a table is invisible in practice and the "
           "columns to its right go unfound (the settled layout rule)"),
  dict(name="dock-edits-never-arrive", file=DIALOG,
       # RE-ANCHORED 2026-08-20: styleChanged now routes through
       # _on_style_signal, which stamps the arrival so the repaint
       # hook can tell a heard edit's echo from an in-place edit.
       old="""    layer.styleChanged.connect(
      lambda lid=layer.id(), tid=str(tile_id):
        self._on_style_signal(lid, tid))""",
       new="    pass  # mutation: QGIS-side restyles go unnoticed",
       test="test_qgis_side_restyles_reach_the_dialog",
       why="recolouring an element layer in QGIS's styling dock must "
           "reach the dialog -- adopted as hand-picks or followed as "
           "a standard ramp -- or the ramp cell goes on naming a ramp "
           "that no longer decides the map (user decision, 2026-08-09)"),
  dict(name="custom-tooltip-reworded", file=DIALOG,
       # RE-ANCHORED 2026-08-18. The tooltip named two causes when
       # there are three: a graduated row also reads Custom when only
       # the Ramp Display Range is narrowed, with no picks and no
       # class file. Found by a hunt pointed at the prose.
       old='CUSTOM_RAMP_TOOLTIP = ("Hand-picked colours, a class file, '
           'or a narrowed "\n                       '
           '"range. Choose a ramp to replace them.")',
       new='CUSTOM_RAMP_TOOLTIP = "Colours chosen by hand."'
           '  # mutation: reworded',
       test="test_a_customized_element_reads_custom",
       why="the Custom tooltip is the user's own words, settled "
           "verbatim on 2026-08-09 and corrected on 2026-08-18 to name "
           "the third thing that sets Custom"),
  dict(name="opacity-header-grows-a-sign", file=DIALOG,
       old='       "Reverse", "Opacity", "Categ colourmap src", '
           '"Edit colours"])',
       new='       "Reverse", "Opacity %", "Categ colourmap src", '
           '"Edit colours"])',
       test="test_the_table_headers_read_as_designed",
       why="the header says Opacity without the % sign the spin "
           "boxes already carry (user decision, 2026-08-09)"),
  # ---- the quant-customization round (settled by grilling,
  # 2026-08-09 evening): the range arithmetic, the involution, the
  # destruction list, the graduated watcher, persistence, the column
  dict(name="quant-range-formula", file=BRIDGE,
       old="    along = i / (count - 1) if count > 1 else 0.5",
       new="    along = i / count if count > 1 else 0.5"
           "  # mutation: top class never reaches hi",
       test="test_the_ramp_display_range_reinterpolates",
       why="the window arithmetic is the whole feature: divide by k "
           "instead of k-1 and the last class never reaches the upper "
           "handle, so every narrowed ramp is quietly wrong at the end "
           "a reader trusts most"),
  dict(name="quant-reverse-permutation", file=DIALOG,
       old="          str(count - 1 - int(index)): colour",
       new="          str(int(index)): colour"
           "  # mutation: picks stay put while the ramp turns",
       test="test_reverse_permutes_quant_customization",
       why="Reverse turns the ramp around underneath positional picks; "
           "without the permutation a pick made on the dark end "
           "reappears on the light end and reversing twice no longer "
           "restores the user's work"),
  dict(name="quant-scheme-change-keeps-picks", file=DIALOG,
       old="""      self._clear_quant_customization(
        tid_here, "a new style", reset_range=False)""",
       new="      pass  # mutation: reclassification keeps stale picks",
       test="test_quant_picks_die_when_the_ramp_is_asked_anew",
       why="a new scheme cuts new classes, so an old positional pick "
           "lands on a class it was never chosen for; keeping it "
           "silently paints the wrong data in the user's colour"),
  dict(name="quant-ramp-pick-keeps-window", file=DIALOG,
       old="""  def _clear_quant_customization(self, tile_id, because,
                                 reset_range=True):""",
       new="""  def _clear_quant_customization(self, tile_id, because,
                                 reset_range=False):""",
       test="test_quant_picks_die_when_the_ramp_is_asked_anew",
       why="choosing a ramp anew must also restore the full display "
           "window -- 'until reselected anew' is the settled rule -- "
           "or a narrowed window quietly survives into a ramp nobody "
           "narrowed"),
  dict(name="quant-dock-edits-go-unnoticed", file=DIALOG,
       old="    if isinstance(renderer, QgsGraduatedSymbolRenderer):",
       new="    if False:  # mutation: graduated dock edits ignored",
       test="test_qgis_side_graduated_restyles_reach_the_dialog",
       why="without the graduated branch a dock recolour is neither "
           "adopted nor followed, so the dialog names a ramp the map "
           "no longer uses and the next Generate destroys the user's "
           "dock work without a word"),
  dict(name="quant-style-not-stamped", file=DIALOG,
       old="""      layer.setCustomProperty(
        "weavingspace_quant_style",""",
       new="""      (lambda *_a: None)(
        "weavingspace_quant_style",""",
       test="test_quant_customization_survives_the_project",
       why="the dialog's record dies with the session; only the "
           "custom property reaches the project file, and without it "
           "a reopened project silently repaints yesterday's choices"),
  dict(name="quant-column-narrows-to-categorical", file=DIALOG,
       old='    has_editable = any(m in ("Categorized", "Graduated") '
           'and has_var',
       new='    has_editable = any(m == "Categorized" and has_var',
       test="test_the_editor_column_appears_for_quant_rows",
       why="narrowing the condition back to categorical-only removes "
           "the Customize button from every graduated row, deleting "
           "the whole quant editor from the UI while every test of "
           "the editor itself still passes"),
  dict(name="editor-close-swallows-pending-range", file=EDITOR,
       old="    if timer is not None and timer.isActive():",
       new="    if False:  # mutation: a pending movement dies with "
           "the window",
       test="test_unclassed_opens_locked_with_live_range",
       why="a range movement still in the debounce when the window "
           "closes is the user's last deliberate act; it must land "
           "synchronously at close, not vanish, and not fire later "
           "from a timer into a dialog that believes the editor gone"),
  dict(name="spacing-suggestion-refuses-itself", file=BRIDGE,
       # RE-ANCHORED 2026-08-25: the loop learned to stop on a
       # SENTINEL as well as on an acceptable count, since neither
       # UNTILEABLE nor UNCOUNTABLE is a size and no spacing changes
       # either. The claim is unchanged.
       old="""  for _ in range(60):
    widened = estimate_tile_count_bounds(unit, bounds, scale,
                                         covered_area=area,
                                         covered_edge=edge)""",
       new="""  for _ in range(0):  # mutation: the inverse-square law decides
    widened = estimate_tile_count_bounds(unit, bounds, scale,
                                         covered_area=area,
                                         covered_edge=edge)""",
       test="test_the_tile_estimate_is_honest_where_shapes_are_awkward",
       why="the refusal names a spacing that WOULD work; the "
           "inverse-square law alone ignores the estimate's border "
           "term and named spacings estimating up to 3.9% over the "
           "hard cap, so following the plugin's own advice was "
           "refused again and the plugin read as contradicting itself"),
  dict(name="corrupt-wheel-raises-at-the-user", file=DEPS,
       old="""      try:
        _extract_wheel(os.path.join(WHEELS_DIR, chosen))
      except Exception:""",
       new="""      if True:
        _extract_wheel(os.path.join(WHEELS_DIR, chosen))
      if False:""",
       test="test_the_deps_installer_declines_a_corrupt_wheel",
       why="a bundled wheel truncated by a copy let BadZipFile out "
           "through open_dialog, so pressing the toolbar button gave "
           "a traceback rather than a sentence -- on the Linux "
           "installs that are the only ones to meet this path"),
  dict(name="non-finite-values-reach-the-classifier", file=BRIDGE,
       old="""  awkward = any(
    v is None or v == NULL or (isinstance(v, float)
                               and (v != v or abs(v) > FINITE))
    for v in values)""",
       new="""  awkward = any(v is None or v == NULL for v in values)""",
       test="test_classification_survives_inf_nan_and_huge",
       why="QGIS 4.0.3 SEGFAULTS -- the application gone with the "
           "user's unsaved project -- when Natural breaks meets an "
           "infinity or a near-limit magnitude, and returns NaN class "
           "bounds for quantiles and equal intervals over NaN, so the "
           "layer paints nothing while the run reports success"),
  dict(name="legend-labels-ignore-tiny-spreads", file=BRIDGE,
       old="          method.setLabelPrecision(precision)",
       new="          pass  # mutation: five classes all read 0 - 0",
       test="test_extreme_magnitudes_render_readable_legends",
       why="QGIS labels to four decimals by default, so a column "
           "around 1e-9 gets distinct colours whose legend entries "
           "all read '0 - 0': a legend claiming one meaning for five "
           "different classes of the map"),
  dict(name="closed-dialog-keeps-tiling", file=DIALOG,
       old="""    for timer in (getattr(self, "_live_timer", None),
                  getattr(self, "_preview_timer", None)):""",
       new="""    for timer in ():  # mutation: debounces outlive the window""",
       test="test_unload_with_windows_open_and_work_in_flight",
       why="cancelling the task is not enough: a live-update timer "
           "armed just before the window closed fires ~900ms later "
           "and starts a fresh tiling that writes layers into the "
           "project for a window nobody can see -- which is exactly "
           "what unloading the plugin asks not to happen"),
  dict(name="reload-forgets-the-live-dialog", file=DIALOG,
       old="      return app.property(_LIVE_KEY)",
       new="      pass  # mutation: the record dies with a reload",
       test="test_a_reloaded_module_retires_the_old_dialog_cleanly",
       why="QGIS's Plugin Reloader re-executes this module, resetting "
           "the module global; without the record parked on the "
           "application the new dialog retires nothing and the "
           "predecessor keeps its timers running against the group "
           "the newcomer just adopted"),
  dict(name="user-filter-dies-at-regeneration", file=DIALOG,
       old="      if tid in old_subsets:",
       new="      if False:  # mutation: the user's filter is dropped",
       test="test_a_user_subset_survives_regeneration",
       why="a subset string is the user's own work, set in Layer "
           "Properties; discarding it at every regeneration throws "
           "away a deliberate choice silently, while the hand styling "
           "beside it survives"),
  dict(name="swatches-built-two-ways", file=DIALOG,
       old="    stripes = SWATCH_STRIPES",
       new="    from qgis.core import QgsSymbolLayerUtils\n"
           "    return QgsSymbolLayerUtils.colorRampPreviewIcon("
           "ramp, RAMP_SWATCH)\n"
           "    stripes = SWATCH_STRIPES",
       test="test_every_swatch_in_the_ramp_column_is_built_the_same_way",
       why="named ramps drawn as QGIS gradients beside hand-striped "
           "Custom swatches make one column read as two kinds of "
           "control; the striped form is also the honest one, since a "
           "classed map paints steps rather than a gradient"),
  dict(name="swatch-ignores-extra-colours", file=DIALOG,
       old="  shown = list(colours)[:SWATCH_STRIPES] or [\"#c0c0c0\"]",
       new="  shown = list(colours) or [\"#c0c0c0\"]"
           "  # mutation: stripes squeezed below legibility",
       test="test_every_swatch_in_the_ramp_column_is_built_the_same_way",
       why="a swatch is 64px wide; past eight stripes each is under "
           "8px and stops reading as a colour, so a twenty-class "
           "element would show a smear instead of its palette"),
  dict(name="memory-layers-lose-their-index", file=BRIDGE,
       old="  provider.createSpatialIndex()",
       new="  pass  # mutation: every repaint scans every tile",
       test="test_output_layers_carry_spatial_indexes",
       why="a memory layer has no spatial index unless one is built; "
           "without it each canvas repaint, identify click and snap "
           "linearly scans every tile of every element layer -- "
           "measured fifteen times slower on twenty thousand tiles"),
  dict(name="legibility-check-ignores-the-box", file=DIALOG,
       old="    if not self.opt_colour_warnings.isChecked():\n"
           "      return None",
       new="    if False:  # mutation: the opinion arrives unasked\n"
           "      return None",
       test="test_colour_legibility_warnings_are_opt_in",
       why="the legibility warnings are opt-in (user decision, "
           "2026-08-09, REPEATED after an ungated sighting): the gate "
           "now lives inside _legibility_note so every caller "
           "inherits it, and this mutation removes it at that single "
           "choke point"),
  dict(name="legibility-warning-arrives-twice", file=DIALOG,
       old='      self.iface.messageBar().pushSuccess("WeavingSpace", '
           'note)\n'
           "      # colour_clash is NOT pushed here: it rides "
           "_pending_colour_note",
       new='      self.iface.messageBar().pushSuccess("WeavingSpace", '
           'note)\n'
           "      if colour_clash is not None:  # mutation: doubled\n"
           '        self.iface.messageBar().pushWarning("WeavingSpace",'
           ' colour_clash)\n'
           "      # colour_clash is NOT pushed here: it rides "
           "_pending_colour_note",
       test="test_colour_legibility_warnings_are_opt_in",
       why="a checked box earns ONE warning per run; the immediate "
           "push beside the settled-dust send delivered every "
           "legibility warning twice to a real message bar, which is "
           "how a bar becomes noise"),
  dict(name="mid-run-dock-edit-forgotten", file=DIALOG,
       old="    for tid in self._preserved_this_run:",
       new="    for tid in ():"
           "  # mutation: preserved layers never re-examined",
       test="test_a_dock_edit_during_a_run_is_not_lost",
       why="a dock recolour made mid-run rides across on the "
           "preserved renderer with no record behind it; without the "
           "re-examination the cell lies and the next re-seed "
           "silently destroys the user's work"),
  # Re-anchored 2026-08-10: the one-at-a-time record moved off the
  # module global (a plugin reload re-executes the module and resets
  # it) onto the QApplication, read through _live_dialog(). The gate
  # is the same gate, now comparing self against that reading.
  dict(name="retired-dialog-keeps-watching", file=DIALOG,
       old="    if live is not None and live is not self:",
       new="    if False:"
           "  # mutation: every past dialog reacts to dock edits",
       test="test_a_retired_dialog_stops_watching",
       why="a retired instance's styleChanged connections outlive its "
           "retirement because the layers do; ungated, one dock edit "
           "is adopted twice and announced twice"),
  dict(name="missing-count-counts-tiles", file=DIALOG,
       old="            field, missing, int(layer.featureCount()))",
       new="            field, missing, int(len(gdf)))"
           "  # mutation: tiles counted as areas again",
       test="test_every_notice_describes_the_map_it_came_from",
       why="the missing-values notice says 'X of Y areas' and must "
           "count the user's areas; counting the tiled frame told a "
           "24-area layer it had 96, and the reader went looking for "
           "areas that do not exist"),
  dict(name="customize-button-says-custom", file=DIALOG,
       old='        button = QPushButton("Customize")',
       new='        button = QPushButton("Custom")'
           '  # mutation: state and action share a word',
       test="test_the_edit_colours_column_appears_with_categories",
       why="the Edit-colours button is a verb, Customize, because "
           "Custom is the ramp cell's display for colours already "
           "customized; one word cannot name a state in one column "
           "and an action in the next"),
  # ---- the element-count range, carried past the web app's
  # dictionary on 2026-08-10. Each anchor is narrowed with enough of
  # its surroundings to match exactly once, since a replacement takes
  # the first occurrence and an anchor that matches twice mutates
  # something nobody chose.
  dict(name="element-ceiling-back-to-the-old-limit", file=CATALOG,
       old="MAX_ELEMENTS = 26",
       new="MAX_ELEMENTS = 20  # mutation: the old hand-written limit",
       test="test_every_element_count_up_to_the_ceiling_is_offered",
       why="the chooser must offer every count the catalogue can "
           "build, up to the 26 where single-character element ids "
           "stay distinct without case; capping it lower takes "
           "designs away from users with no sign anything is missing"),
  dict(name="seventeen-elements-left-out-again", file=CATALOG,
       old="for _n in range(2, MAX_ELEMENTS + 1):",
       new="for _n in [_c for _c in range(2, MAX_ELEMENTS + 1)"
           " if _c != 17]:  # mutation: skip 17 as the web app did",
       test="test_every_element_count_up_to_the_ceiling_is_offered",
       why="17 elements was the count the user noticed missing; a gap "
           "in the middle of the range reads as a design the library "
           "cannot do, when in fact four families build it"),
  dict(name="colouring-offered-where-it-cannot-build", file=CATALOG,
       old="HEX_COLOURING_COUNTS = tuple(range(2, 17)) + (19, 37)",
       new="HEX_COLOURING_COUNTS = tuple(range(2, 53))"
           "  # mutation: offer every count",
       test="test_the_catalogue_offers_only_designs_that_build",
       why="hex-colouring is a hand-built arrangement per count, and "
           "an unsupported count does not raise -- the library prints "
           "a complaint and substitutes a default unit, so the user "
           "gets a map quietly carrying the wrong number of variables"),
  dict(name="adopted-signature-stamped-on-the-wrong-element",
       file=DIALOG,
       old="""    return next((a for a in self._assignments()
                 if a["id"] == tile_id), None)""",
       new="""    return next((a for a in self._assignments()
                 if a["id"] != tile_id), None)  # mutation""",
       test="test_a_dock_refinement_survives_the_next_restyle",
       why="after adopting a dock recolour the element's signature has "
           "moved, so unless it is recorded against the RIGHT element "
           "the restyle fast path re-seeds this layer at the next "
           "style change anywhere in the table -- destroying the "
           "stroke width, outline style or anything else the user set "
           "in QGIS's own dock alongside the colours"),
  dict(name="category-shift-cries-wolf-on-first-sight", file=BRIDGE,
       old="  if previous is None or previous == current or current < 2:",
       new="  if previous == current or current < 2:"
           "  # mutation: warn the first time a field is seen",
       test="test_a_changed_category_count_warns_that_colours_moved",
       why="the first sight of a field is not a change, so warning "
           "then would fire on every ordinary first run. A warning "
           "that cries wolf is one people learn to ignore, which "
           "costs the real ones too. This entry exists mainly to "
           "prove the NEGATIVE half of its test can fail: it read "
           "the note line once, and the line is cleared shortly "
           "after a run, so it was satisfied by silence"),
  dict(name="range-editor-repaints-from-another-element",
       file=DIALOG,
       old="""    return next((a for a in self._assignments()
                 if a["id"] == tile_id), None)""",
       new="""    return next((a for a in self._assignments()
                 if a["id"] != tile_id), None)  # mutation""",
       test="test_the_range_editor_repaints_with_its_own_elements_colours",
       why="the editor never computes colours, it paints what the "
           "dialog hands back. Looking up the wrong element hands "
           "back another element's class colours -- or an empty list "
           "on a one-element map, which leaves the window showing "
           "colours the map has left. Nothing raises and the map is "
           "right; the window is simply telling a small lie, which is "
           "the same fault the Custom ramp cell exists to prevent"),
  dict(name="graduated-signature-stamped-on-the-wrong-element",
       file=DIALOG,
       old="""    return next((a for a in self._assignments()
                 if a["id"] == tile_id), None)""",
       new="""    return next((a for a in self._assignments()
                 if a["id"] != tile_id), None)  # mutation""",
       test="test_a_graduated_dock_refinement_survives_the_next_restyle",
       why="the graduated mirror of the categorized adoption: without "
           "the signature recorded against the right element, the "
           "next style change re-seeds this layer and throws away the "
           "stroke width or outline the user set in QGIS's dock "
           "alongside the class colours"),
  dict(name="colouring-count-above-the-ceiling-moved", file=CATALOG,
       old="HEX_COLOURING_COUNTS = tuple(range(2, 17)) + (19, 37)",
       new="HEX_COLOURING_COUNTS = tuple(range(2, 17)) + (19, 38)"
           "  # mutation: a count the library cannot hand-build",
       test="test_the_catalogue_offers_only_designs_that_build",
       why="37 sits above MAX_ELEMENTS, so the loop over the MENU "
           "never reached it and an automatic mutant moved it freely. "
           "The list is a measured fact about which arrangements the "
           "library hand-builds, and it goes on the menu the day the "
           "element ceiling rises -- at which point a wrong count "
           "reaches a user as a plausible map carrying the wrong "
           "number of variables"),
  dict(name="unclassed-swatch-stops-short", file=DIALOG,
       old="        step = (len(shades) - 1) / 7",
       new="        step = (len(shades) - 1) / 8"
           "  # mutation: the last sample falls short",
       test="test_an_unclassed_swatch_reaches_both_ends_of_its_ramp",
       why="eight stripes span seven gaps, so dividing by eight lands "
           "the last sample before the top class and the Custom cell "
           "shows a shorter ramp than the map draws. A truncated ramp "
           "does not look broken, so a user comparing two elements' "
           "cells judges by a picture that misrepresents one of them"),
  dict(name="unchanged-colours-read-as-a-dock-recolour", file=DIALOG,
       old="    if all(expected.get(key) == colour "
           "for key, colour in actual.items()):",
       new="    if all(expected.get(key) != colour "
           "for key, colour in actual.items()):"
           "  # mutation: agreement no longer means quiet",
       test="test_a_dock_edit_that_changes_no_colour_is_announced_as_nothing",
       why="this comparison is how the dialog stays quiet about its "
           "own seeding. Flipped, an edit that changed no colour at "
           "all -- a stroke width, an outline style -- falls through "
           "to the ramp-following branch, so the user is told the "
           "plugin has followed a ramp they never chose and the "
           "element's signature is restamped underneath them"),
  dict(name="missing-baseline-reads-as-clean", file=MUTATE_AUTO,
       old="  if probe.returncode != 0 or not probe.stdout.strip():",
       new="  if False:  # mutation: answer even when the ref is absent",
       test="test_the_new_code_guard_refuses_a_baseline_it_cannot_find",
       why="without the refusal every target file's diff fails the "
           "same way, changed_lines returns empty, and the caller "
           "prints '0 line(s) changed ... nothing mutable has "
           "changed; the suite is unaffected'. That is a clean bill "
           "of health from an instrument that never looked, and it "
           "was reported for real on 2026-08-12 against a tag the "
           "runner's checkout could not see"),
  dict(name="general-tilings-offset-moved", file=CATALOG,
       old='type="tiling", tiling_type="hex-slice", n=n, offset=0)',
       new='type="tiling", tiling_type="hex-slice", n=n, offset=1)'
           '  # mutation: cuts start off the corners',
       test="test_every_declared_offset_is_pinned",
       why="an offset moves where a slice family's cuts fall, so the "
           "element count is identical and the design is not. The "
           "offsets in GENERAL_TILINGS were declared with nothing "
           "reading them: the rule-stating test looped over "
           "TILINGS_BY_N alone, which is the one door a table test "
           "left open"),
  dict(name="new-counts-offer-nothing", file=CATALOG,
       old="""  for _family, _spec_for in GENERAL_TILINGS.items():
    _families.setdefault(f"{_family} {_n}", _spec_for(_n))""",
       new="""  for _family, _spec_for in list(GENERAL_TILINGS.items())[:1]:
    _families.setdefault(f"{_family} {_n}", _spec_for(_n))""",
       test="test_every_element_count_up_to_the_ceiling_is_offered",
       why="all four of stripes, grid, hex-slice and square-slice "
           "build at every count; dropping three of them leaves the "
           "new counts on the chooser with almost nothing to pick, "
           "which is worse than not offering them"),
  dict(name="consent-gates-the-download", file=PLUGIN,
       old="""    if box.clickedButton() is not approve:
      return False""",
       new="""    if False:  # mutation: download whatever the user clicked
      return False""",
       test="test_pypi_provisioning_is_reached_only_through_consent",
       why="the consent dialogue is the ONLY thing standing between "
           "a user and code being downloaded onto their machine, and "
           "a dialogue whose answer is not read is not consent. A "
           "QGIS plugin repository reviewer looks straight at this; "
           "so does the test"),
  dict(name="duplicated-catalogue-key", file=CATALOG,
       old="  5: {",
       new="  6: {",
       test="test_every_element_count_still_has_its_designs",
       why="two entries under one key is silently resolved by Python "
           "keeping the last, and the count loses every hand-written "
           "design filed under it. The backfill loop hides the older "
           "form of this defect by refilling the count with the four "
           "families that build everywhere, so the test looks past "
           "the count's existence to what is actually in it"),
  dict(name="a-pin-is-never-adopted-onto-the-edge", file=DIALOG,
       # NARROWER THAN ITS NEIGHBOUR BELOW ON PURPOSE: that entry
       # removes the whole adoption, this one removes only the
       # clause that keeps a pin off the ladder's own floor.
       old=r"""      if abs(edges[0] - float(mine[0][1])) > 1e-9 \
          and abs(edges[0] - floor_here) > 1e-9:""",
       new="""      if abs(edges[0] - float(mine[0][1])) > 1e-9:""",
       test="test_a_pin_is_never_adopted_onto_the_ladders_own_edge",
       why="a low pin sitting exactly on the floor names a first "
           "class of ZERO WIDTH. The maintainer's QGIS segfaulted "
           "on rc11 after adding a class in the styling panel with "
           "exactly that record in the dump, and this project "
           "already holds that a degenerate ladder can bring QGIS "
           "down rather than raise. An empty class is reported in "
           "words and never pinned"),
  dict(name="a-pasted-ladder-carries-its-pins", file=DIALOG,
       # RE-ANCHORED 2026-08-19 when the block gained its edge guard:
       # a pin is never adopted onto the ladder's own floor or
       # ceiling, since that is a class of no width.
       old="""    if len(mine) == len(bounds) and edges:
      if abs(edges[0] - float(mine[0][1])) > 1e-9 \\
          and abs(edges[0] - floor_here) > 1e-9:
        wanted.setdefault("low", edges[0])
      if abs(edges[-1] - float(mine[-1][0])) > 1e-9 \\
          and abs(edges[-1] - ceiling_here) > 1e-9:
        wanted.setdefault("high", edges[-1])""",
       new="    pass  # mutation: an adopted ladder keeps nobody's name",
       test="test_a_style_pasted_between_elements_carries_its_pins",
       why="a style pasted from one element layer onto another brings "
           "every boundary and, without this, no statement that any "
           "of them is a person's. The receiving element then shows "
           "no mark against the ends somebody set, and "
           "`_release_copied_breaks` -- which keeps only low and high "
           "-- has nothing to degrade to when the class count moves"),
  dict(name="the-clear-mark-is-drawn-where-it-can-be-seen", file=WIDGETS,
       # ANCHORED ON THE RAISE, which is the whole of it: a child that
       # has fallen behind the line edit is painted over by it, which
       # is what the cross did for its entire life as paint.
       old="""    self._cross.setVisible(self._marked)
    if self._marked:
      self._cross.raise_()""",
       new="    self._cross.setVisible(False)",
       test="test_a_bound_can_be_given_back_from_every_control",
       why="the cross that gives a bound back was painted by the spin "
           "box into pixels its own QLineEdit occupies, and Qt paints "
           "a child after its parent -- so it had never once been "
           "visible on any build. Measured: 721 dark pixels for the "
           "heavy outline and ZERO inside the cross's rectangle. The "
           "click was repaired a day earlier and the paint left "
           "underneath it, so the affordance worked and could not be "
           "found"),
  dict(name="a-bound-shows-a-prefix-past-a-magnitude", file=WIDGETS,
       old="    if SI_BELOW <= size < SI_ABOVE:\n"
           "      return super().textFromValue(value)",
       new="    if True:\n      return super().textFromValue(value)",
       test="test_a_bound_is_readable_and_typable_at_every_magnitude",
       why="a class bound follows the data across twelve orders of "
           "magnitude, and every digit of 1023192923 in a column "
           "sized for 1.56 is a bound the box cannot show: measured "
           "at 38 pixels of overflow, with the last digits elided. "
           "Without the prefix the number is unreadable and the "
           "column has to be sized for a case nobody has yet"),
  dict(name="a-prefixed-number-can-be-typed-back", file=WIDGETS,
       old="""      if trimmed.endswith(prefixes):
        state, _fixed, _at = super().validate(trimmed[:-1], position)
        if state != QValidator.State.Invalid:
          return QValidator.State.Acceptable, text, position""",
       new="      pass  # mutation: refuse what the box itself displays",
       test="test_a_bound_is_readable_and_typable_at_every_magnitude",
       why="retyping the value a box DISPLAYS is one of the two ways "
           "to give a bound back to the classification, and the other "
           "is a mark that had never once been visible. A validator "
           "that refuses its own display eats the keystroke in "
           "silence, which is the family this project has met five "
           "times and every one of them passed a guard driving "
           "setValue"),
  dict(name="every-end-a-person-set-is-marked", file=DIALOG,
       old="""      boxed = [pair for pair, end in (((0, "left"), "floor"),
                                      ((0, "right"), "low"),
                                      ((-1, "left"), "high"),
                                      ((-1, "right"), "ceiling"))
               if pinned.get(end) is not None]""",
       new="""      boxed = [pair for pair, end in (((0, "right"), "low"),
                                      ((-1, "left"), "high"))
               if pinned.get(end) is not None]""",
       test="test_the_swatch_marks_every_end_a_person_set",
       why="the mutation is the code this replaced: two of the "
           "record's four ends. A floor or a CEILING somebody had set "
           "drew nothing at all, so the swatch was silent about a "
           "bound the person had chosen -- reported by the maintainer "
           "against rc10, who had pinned an upper bound and found no "
           "mark for it anywhere"),
  dict(name="a-candidate-is-named-by-its-number", file=RELEASE,
       # ANCHORED ON THE ASK, not on build.py's arithmetic: the fault
       # was release.py deriving the number a SECOND way, and a
       # catalogue entry standing on the helper would survive that
       # coming back.
       old="  number = build_module().latest_candidate(version)\n"
           "  return None if number is None else f\"{version}rc{number}\"",
       new="  import glob as _g\n"
           "  built = sorted(_g.glob(os.path.join(\n"
           "    ROOT, 'dist', 'weavingspace_qgis-*rc*.zip')))\n"
           "  return (os.path.basename(built[-1])[len('weavingspace_qgis-'):-4]\n"
           "          if built else None)",
       test="test_the_tenth_candidate_is_named_the_tenth",
       why="the mutation is the code this replaced, verbatim: sorting "
           "dist/ as TEXT, where rc10 sits between rc1 and rc2, and "
           "over every version at once. It named the tenth candidate's "
           "dossier and receipt after the NINTH and wrote them over "
           "the published rc9's own -- one name across two trees, "
           "which is the harm the numbering exists to prevent"),
  dict(name="stage-log-says-it-is-running", file=RELEASE,
       old="  if capture:\n    # Stamp the stage log as IN PROGRESS",
       new="  if False:  # mutation: leave the old log in place\n"
           "    # Stamp the stage log as IN PROGRESS",
       test="test_a_stage_log_never_shows_the_previous_run",
       why="a stage writes its log when it FINISHES, so without the "
           "stamp the file holds the PREVIOUS run's verdict for the "
           "twenty-five minutes the suite takes, and whoever checks "
           "on progress reads it as current -- which nearly happened "
           "with a stale '275 passed, 1 failed' on 2026-08-11"),
  dict(name="ramp-lookup-is-case-blind", file=BRIDGE,
       # re-anchored 2026-08-12: the lookup was rewritten around
       # _RAMP_NAME_BY_LOWER, whose keys are lowered, so folding the
       # case off the REQUEST is now the whole of the behaviour and
       # the old loop no longer exists. The entry had been
       # unjudgeable since -- reported neither caught nor survived,
       # which is worse than either.
       old="    wanted = name.lower()",
       new="    wanted = name  # mutation: exact lookup only",
       test="test_a_palette_is_usable_whatever_case_qgis_spells_it",
       why="installation skips a palette whose name matches an "
           "existing ramp IGNORING CASE, so the lookup must match the "
           "same way or the plugin declines to install its own ramp "
           "and then cannot find the one it deferred to. Linux QGIS "
           "ships Cividis against our cividis, and four palettes were "
           "unavailable to every Linux user while the chooser went on "
           "offering them. The direction this line decides is the "
           "MIXED-CASE REQUEST -- the stored names are remembered "
           "already lowered, so a lowercase request resolves without "
           "it. A ramp name travels in saved projects, so a request "
           "can arrive spelled the way another machine's QGIS spells "
           "it"),
  dict(name="style-name-overruns-its-column", file=BRIDGE,
       old="  name = layer.name()[:30]",
       new="  name = layer.name()  # mutation: let GDAL truncate it",
       test="test_an_embedded_style_name_fits_the_column_it_is_written_to",
       why="GDAL gives layer_styles.styleName thirty characters, and "
           "output layers are named after the element and its "
           "variable, so a long column name overruns it and is "
           "truncated with a warning on every write -- storing a "
           "value that does not say what this code thinks it says"),
  dict(name="style-saved-with-the-deprecated-call", file=COMPAT,
       old='  saver = getattr(layer, "saveStyleToDatabaseV2", None)',
       new="  saver = None  # mutation: always the deprecated spelling",
       test="test_the_style_is_saved_through_the_current_api",
       why="QGIS 4.0.3 already deprecates saveStyleToDatabase, and a "
           "deprecated call is what a later release withdraws. Both "
           "spellings write the same style today, so every test about "
           "the style's CONTENTS passes either way and only a test "
           "about which call is reached can notice the regression"),

  # The five below close survivors from batch 11 (2026-08-12). Each is
  # here for the reason this file exists: those tests were written
  # afterwards and verified to PASS, which says nothing at all about
  # whether they would fail when the behaviour breaks.
  # NO entry for the five `_refresh_preview_colours` survivors the
  # 2026-08-12 census turned up (dialog.py 3432, 3524, 3552, 3934,
  # 3960). They are REDUNDANT CALL SITES, and it took three falsified
  # harm claims to establish it, which is worth recording so nobody
  # spends the afternoon again.
  #
  # First claim: the design preview would keep the colours of a style
  # the chooser had abandoned. Measured -- the correction changes no
  # colour the preview shows, so a stale preview and a fresh one are
  # identical.
  #
  # Second: with live update on, a style corrected on a text field
  # would leave the map behind. Wrong, and wrong in the software's
  # favour: by the time the style is refused the variable change has
  # already corrected the row, so the design is where it was and
  # redrawing would be work for nothing.
  #
  # Third: the same, reached by moving the variable instead. That
  # entry was written, and SURVIVED -- the variable combo's own
  # handler queues the run whatever this call does.
  #
  # So they are accepted, and they lower the rate honestly. There are
  # fifteen call sites of _refresh_preview_colours (the runbook said
  # six until today), which is the whole explanation: deleting one
  # leaves fourteen doing the work, and no test can discriminate.
  # Deleting the redundant ones is the better fix and is a change to
  # the plugin rather than to its tests, so it belongs to a decision
  # somebody makes deliberately, not to a campaign chasing a number.
  # NO entry for the blockSignals survivors either, and the reason is
  # the same shape as the _refresh_preview_colours family above: a
  # harm was stated and did not hold. The 2026-08-12 census returned
  # TWENTY-ONE of them -- eleven "call removed", ten "bool" -- across
  # _on_n_changed, _on_family_changed, _adapt_to_the_layer,
  # _populate_class_source_combo, _on_mode_chosen and
  # _follow_variable.
  #
  # The claim tested was the most plausible one available: refilling
  # every variable chooser (when a column appears in QGIS) empties each
  # combo before putting the choice back, and hand-picked colours are
  # keyed by element AND FIELD, so a handler running against that empty
  # instant could take the colours with it. An entry was written for
  # it and SURVIVED: the field is restored before anything reads it.
  #
  # ACCEPTED -- dialog.py:2136, the class-source dropdown's LABEL for
  # a chosen file: os.path.basename(current[5:]) strips "file:".
  # Measured 2026-08-13: basename discards the leading separator, so
  # [5:] and [6:] give the identical label for every path carrying
  # one -- "/schemes/landcover.qml", "/tmp/a.qml" and
  # "relative/b.qml" all agree. It would differ only for a bare
  # filename with no directory ("file:a.qml" -> ".qml"), which a file
  # chooser cannot produce. Named rather than glossed, because an
  # acceptance that hides its one exception is how folklore starts.
  #
  # ACCEPTED -- k_spin.setRange(0, 9999), both survivors. That range
  # belongs to the UNCLASSED branch only, where the cell reports a
  # fixed 50 steps and is disabled: informative, not editable. The
  # range's only job there is to admit 50, and n -> n+1 cannot stop it.
  # The editable branch uses setRange(2, 20) -- the documented ceiling
  # -- and that line is NOT among the survivors, so it is already
  # guarded. Worth writing down because the first reading was that
  # this escaped CONTROL_DEFAULTS for the same reason the Auto
  # button escaped the tooltip test (a widget in a table cell rather
  # than on the dialog). That blind spot is real and cost two
  # survivors elsewhere; it is not the explanation here.
  #
  # ACCEPTED -- the ramp DISPLAY RANGE's upper default, in its three
  # places (bridge.py's range_bounds signature and its
  # assignment.get fallback, and the dialog's stored-range fallback).
  # Measured 2026-08-13: QGIS CLAMPS a ramp lookup, so color(1.01),
  # color(1.5) and color(1.0) all return #08306b on Blues. Raising the
  # upper bound past 100 therefore changes no colour on any map, which
  # is the only thing that default exists to control.
  #
  # The LOWER bound was then measured too, 2026-08-13, rather than
  # being folded into the paragraph above on the strength of its
  # neighbour. It IS observable -- 0% against 1% into Blues gives
  # #f7fbff against #f5fafe, and Greys #ffffff against #fefefe -- so
  # it is not equivalent. It is still accepted: two parts in 255 in a
  # single channel is far below one dE, against the ~2.3 this project
  # treats as just noticeable and the 0.3-0.5 its gallery actually
  # scores. A test that could catch it would be asserting an exact
  # constant, which raises the number and detects nothing.
  #
  # This corrects an earlier triage in this campaign. bridge.py:811 was
  # reported as a REAL GAP after batch 11 on the reasoning that "a
  # default past the end of the ramp is exactly this software's
  # characteristic failure" -- which sounded right, was never checked,
  # and is false. Two minutes with the ramp would have said so. The
  # lower bound is a different matter and is NOT covered by this: 0
  # becoming 1 moves where the first class samples, and nothing here
  # has measured that.
  #
  # ACCEPTED, NOT EQUIVALENT -- the style-correction blocks in
  # _on_mode_chosen and _follow_variable (dialog.py 3928, 3951, 3957).
  # Demonstrated 2026-08-13 against a scenario driving both
  # corrections: a quantitative style refused on a field of words, and
  # a variable moved to words underneath one. All three sites give the
  # same answer -- 149 lines of snapshot with EXACTLY ONE line
  # differing, `preview_refreshes` 8 against 9. Every element of state
  # is identical: assignments, class sources, category colours, ramp
  # ranges, preview colours, note line, every cell widget, and both
  # corrected style choosers reading "Categorized".
  #
  # So the mutation costs one extra repaint and changes nothing a user
  # could see. That is NOT equivalence: something differs, and a test
  # counting how often a private method ran could catch it. But such a
  # test would pin an implementation detail that is legitimately true,
  # which is the shape this project already rejected for the live
  # timer. They therefore stay in the DENOMINATOR as survivors and
  # lower the rate honestly, rather than being moved to EQUIVALENT,
  # which would excuse them on a false basis. The distinction is the
  # whole difference between a rate that means something and one that
  # has been tidied.
  #
  # THAT CONCLUSION WAS PREMATURE, and the correction is the most
  # useful thing in this file. Running the demonstration properly --
  # comparing everything a snapshot could see rather than the one
  # dimension that had been imagined -- showed the refill mutant is
  # NOT equivalent: it seeds every element's remembered single colour,
  # which sits in the signature, so the next Generate re-seeds every
  # element and discards the user's own styling. It is now
  # `variable-refill-blocks-its-signals` above, and it reports
  # `caught`.
  #
  # So the lesson is not "blockSignals mutants are harmless". It is
  # that a harm GUESSED AT and not found is worth nothing either way:
  # the first claim here was wrong AND the mutant was real, and only
  # the wide comparison could tell those apart. The remaining sites --
  # _on_n_changed, _on_family_changed, _populate_class_source_combo,
  # _on_mode_chosen, _follow_variable -- each want the same treatment
  # before anything is said about them.
  # test_hand_picks_survive_a_column_appearing_in_qgis is kept: it
  # asserts a guarantee nothing else covered, and it is not claimed to
  # close anything. (2026-08-13.)
  # NO entry for dialog.py:3571, mapLayer(token[6:]) inside
  # _template_for. The harm was stated -- break the lookup and
  # _on_layer_style_edited can no longer tell the plugin's own seeding
  # from a user's edit, so it adopts its own colours as hand-picks,
  # which outrank the class source they came from -- and the entry
  # SURVIVED. The reason is that nothing in the covering flow performs
  # a dock edit at that point, so the broken lookup is never consulted
  # where it would record anything.
  #
  # That is the SIXTH harm claim falsified in this campaign, against
  # two that held. The lesson is now thoroughly paid for: a harm
  # reasoned out from reading the code is a hypothesis, and in this
  # stratum it is wrong about three times in four. Demonstrate first
  # -- eq_probe.py/eq_run.sh in the session scratchpad -- and write
  # the test only for what the comparison actually shows moving.
  #
  # The assertion added to test_integration_categorical_session is
  # KEPT: "the plugin must not adopt its own seeding as hand-picks" is
  # true and worth holding, and it is not claimed to close this.
  #
  dict(name="variable-refill-blocks-its-signals", file=DIALOG,
       old="      chosen = chosen_by_row.get(row, combo.currentText())\n"
           "      combo.blockSignals(True)",
       new="      chosen = chosen_by_row.get(row, combo.currentText())\n"
           "      combo.blockSignals(False)  # mutation: let them fire",
       test="test_a_column_appearing_in_qgis_keeps_hand_styling",
       why="a column added in QGIS refills every element's variable "
           "chooser. Unblocked, the handlers run against the half-built "
           "state and seed each element's remembered single colour, "
           "which sits in the signature -- so every element looks "
           "changed and the next Generate re-seeds all of them, "
           "discarding styling the user did in QGIS's own panel. Found "
           "by comparing a WIDE snapshot rather than the dimension "
           "that had been imagined: an earlier entry asserting the "
           "hand-picked CATEGORY colours would be lost survived, "
           "because the field is restored before anything reads it"),
  dict(name="toggle-knob-is-drawn", file=DIALOG,
       old="    painter.drawEllipse(int(x), inset, diameter, diameter)",
       new="    pass  # mutation: no knob at all",
       test="test_a_toggle_switch_shows_which_way_it_is_set",
       why="the knob is the whole message of a switch: it is what says "
           "whether a map option is on. Without it the widget is a "
           "coloured bar that never appears to move, while isChecked() "
           "goes on reporting correctly and every functional test "
           "passes -- the state right and the picture wrong, which is "
           "the only half a user reads"),
  dict(name="toggle-knob-stands-out-from-its-track", file=DIALOG,
       old="    painter.setBrush(QBrush(knob))",
       new="    pass  # mutation: knob painted in the track's colour",
       test="test_a_toggle_switch_shows_which_way_it_is_set",
       why="the same failure reached the other way. Left with the "
           "track's brush the knob is drawn in the track's own colour, "
           "so it is invisible against it and the switch reads as a "
           "plain bar in both states"),
  # NO entry for bridge.py:1290, assignment.get("k", 5). It was a
  # batch-12 survivor and was offered to the differential pair written
  # afterwards, on the theory that a map of six classes beside a row
  # saying five is exactly what that pair compares. It SURVIVED, and
  # the reason is not a weakness in the pair: the default fires only
  # when an assignment carries no k, and in any ordinary session every
  # graduated row has one from its spin box. The mutation therefore
  # changes nothing because the line it changes never runs.
  #
  # That makes it a candidate for DELETION rather than defence -- this
  # project prefers removing a line that does not earn its keep to
  # writing a test protecting it -- but confirming the default is
  # genuinely unreachable is a separate piece of work from the
  # campaign, and guessing is what today has been an argument against.
  # Recorded, not closed. (2026-08-13.)
  dict(name="per-row-class-ceiling-is-pinned", file=DIALOG,
       # Re-anchored 2026-08-13: the setValue line this named was
       # rewritten that night, leaving the entry matching NOTHING --
       # and an entry whose anchor is absent is worse than no entry,
       # because a sweep goes on printing a verdict for it.
       old="""      k_spin.setRange(2, 20)
      # clamp the PROPERTY, not only the display""",
       new="""      k_spin.setRange(2, 21)
      # clamp the PROPERTY, not only the display""",
       test="test_every_per_row_control_keeps_its_declared_range",
       why="a SURVIVOR of batch 12. The 2-20 class ceiling is a design "
           "decision recorded in CLAUDE.md, and nothing pinned it "
           "because CONTROL_DEFAULTS walks attributes stored on the "
           "dialog and this spin box lives in a table cell -- the same "
           "blind spot that hid the Auto button's tooltip. This is "
           "REGRESSION cover rather than detection: it cannot say "
           "twenty is right, only that the decision changed, which is "
           "worth saying because the number was chosen for stated "
           "reasons. The anchor carries a second line because two "
           "sites read setRange(2, 20) -- and only ONE of them is "
           "closed by this. The anchor was first written against "
           "dialog.py:2822, the row-rebuild path that restores a "
           "remembered choice, and it SURVIVED: the test drives the "
           "mode-sync path at 2468 instead. Two sites, two "
           "scenarios, and a test exercising one says nothing about "
           "the other. 2822 remains an open batch-12 survivor and "
           "wants a scenario that rebuilds a row from a stored k"),
  dict(name="category-shift-warns-at-two", file=BRIDGE,
       old="  if previous is None or previous == current or current < 2:",
       new="  if previous is None or previous == current or current <= 2:",
       test="test_a_changed_category_count_warns_that_colours_moved",
       why="a SURVIVOR of batch 12, and a boundary the existing test "
           "walked past: it checked 4 against 5 and an unchanged "
           "count, never the edge the guard actually names. Two is "
           "where the warning still matters -- colours are sampled by "
           "position, so a field collapsing from five categories to "
           "two draws both from the ends of the palette, as large a "
           "move as this message exists to report. Widened to <=, a "
           "user meets exactly that change in silence"),
  dict(name="one-feature-constant-collapse", file=BRIDGE,
       old='  return distinct_numeric_count(values, limit=2) == 1',
       new='  return False  # mutation: no column is ever constant',
       test="test_a_region_of_one_feature_degenerates_honestly",
       why="a region of ONE feature makes every mapped column constant "
           "on the map, whatever variation the data has elsewhere. "
           "Without this the legend cuts five classes all reading "
           "'0 - 0' in five different colours, and nothing says the "
           "column has one value -- a reader trusts the legend, so "
           "they read variation that is not there"),
  dict(name="all-null-column-classified-as-zero", file=BRIDGE,
       old="""  awkward = any(
    v is None or v == NULL or (isinstance(v, float)
                               and (v != v or abs(v) > FINITE))
    for v in values)""",
       new="""  awkward = False  # mutation: hand the nulls to the classifier""",
       test="test_a_column_with_no_values_at_all_invents_no_class",
       why="QGIS's classifier counts a NULL as zero, so a column that "
           "is entirely empty -- a join that matched nothing, a field "
           "never filled -- comes back with class breaks sitting on "
           "0 - 0. Every area is then coloured as though it had been "
           "measured at nothing, which is a confident and wrong "
           "statement about every place on the map"),
  dict(name="empty-region-refused-silently", file=DIALOG,
       old='        QMessageBox.critical(self, "WeavingSpace", str(e))',
       new="        pass  # mutation: refuse the layer without saying so",
       test="test_a_region_with_no_features_is_declined_in_words",
       why="a region layer with no features cannot be tiled, and the "
           "refusal is the only thing the user gets: without it "
           "Generate leaves the project exactly as it was and is "
           "indistinguishable from a button that did nothing"),
  dict(name="tiles-doubled-by-a-repeated-join", file=BRIDGE,
       old="  provider.addFeatures(feats)",
       new="  provider.addFeatures(feats + feats)  # mutation: joined twice",
       test="test_two_areas_on_the_same_ground_do_not_double_the_tiles",
       why="two features covering the same ground must give one tile, "
           "whichever of them wins it. A join that matches twice draws "
           "every tile twice in two colours, one over the other -- the "
           "map looks complete, the counts look plausible, and the "
           "reader sees whichever value happened to be drawn last"),
  dict(name="cardinality-threshold", file=DIALOG,
       old="          if idx >= 0 and len(mem.uniqueValues(idx)) > 60:",
       new="          if idx >= 0 and len(mem.uniqueValues(idx)) > 61:",
       test="test_the_cardinality_warning_fires_on_the_side_it_should",
       why="above sixty distinct values, categorized styling is "
           "usually the sign of a field that is not categorical at all "
           "-- an identifier, a name, a measurement stored as text -- "
           "and the legend is unreadable either way. The number is the "
           "whole of the behaviour: move it and either the warning "
           "stops arriving, or it starts firing on ordinary data, "
           "which is how a warning becomes something people dismiss "
           "unread"),
  dict(name="class-count-reaches-the-renderer", file=BRIDGE,
       old='      assignment.get("k", 5), outline, assignment.get("reverse", False),',
       new='      5, outline, assignment.get("reverse", False),',
       test="test_a_class_count_at_either_end_of_its_range_reaches_the_map",
       why="the per-row Classes spinner runs 2 to 20 and the number "
           "has to reach the map. A spinner that accepts 20 over a "
           "renderer that quietly cuts five is consistent with every "
           "control test in the suite, and the user gets a legend that "
           "says nothing they asked for"),
  dict(name="cat-colours-keyed-by-element", file=DIALOG,
       old="""        a["category_colours"] = self._category_colours.get(
          a["id"], {}).get(a["var"])""",
       new="""        a["category_colours"] = next(
          iter(self._category_colours.get(a["id"], {}).values()), None)""",
       test="test_the_field_goes_away_under_an_open_colour_editor",
       why="hand-picked colours are recorded per element AND per "
           "field. Keyed by element alone, colours chosen for a "
           "column that has since been deleted in QGIS follow the "
           "element onto whatever variable it shows next -- so a map "
           "of landcover_2010 comes out wearing the colours somebody "
           "chose for landcover, with nothing on screen to say so"),

  dict(name="cat-colours-keyed-by-field", file=DIALOG,
       old="""        a["category_colours"] = self._category_colours.get(
          a["id"], {}).get(a["var"])""",
       new="""        a["category_colours"] = next(
          (v.get(a["var"]) for v in self._category_colours.values()
           if v.get(a["var"])), None)""",
       test="test_the_element_count_changes_under_an_open_colour_editor",
       why="keyed by field alone, a colour picked for one element "
           "paints every other element showing the same variable -- "
           "including, after the element count drops, an element that "
           "inherits a choice made for a design the user has left "
           "behind. Two elements the cartographer deliberately "
           "distinguished come out identical"),

  dict(name="geometry-signature-of-the-run", file=DIALOG,
       old="""    self._last_geometry_sig = (geometry_sig if geometry_sig is not None
                               else self._geometry_signature())""",
       new="""    self._last_geometry_sig = self._geometry_signature()""",
       test="test_a_region_edit_is_undone_while_a_run_is_in_flight",
       why="a finished run must record the geometry it DREW, not what "
           "the table says at the moment it lands. Recording the "
           "latter makes an edit undone during a run look like a map "
           "that is already current, so the next Generate takes the "
           "restyle fast path and the user goes on looking at "
           "features they rolled back"),

  dict(name="surplus-elements-dropped", file=DIALOG,
       old="""    # drop the previous run's element layers
    for tid, lid in old_ids.items():
      if project.mapLayer(lid) is not None:""",
       new="""    # drop the previous run's element layers
    for tid, lid in old_ids.items():
      if tid in new_ids and project.mapLayer(lid) is not None:""",
       # ONE literal. This was two adjacent strings, which Python
       # concatenates silently into a name no test has -- and the
       # standards checker's regex read only the first of them, so
       # it saw a name that exists. Two counting rules, wrong
       # together, which is the shape that makes a broken entry
       # invisible. Repaired 2026-08-13.
       test="test_two_generates_with_different_families_keep_their_elements_apart",
       why="a run must clear the whole of the previous one, not only "
           "the elements it happens to share. Going from a "
           "seven-element family to a four-element one otherwise "
           "leaves e, f and g in the project, still tagged as this "
           "plugin's output -- so the map carries elements the table "
           "does not have, and a later dialog adopts them"),

  dict(name="group-deleted-under-a-run", file=DIALOG,
       old="      if group is not None:",
       new="      if group is not None or group is None:",
       test="test_the_output_group_is_deleted_while_a_run_is_in_flight",
       why="the dialog must notice that the user deleted its output "
           "group and make a new one. Without the check it goes on "
           "with the group it did not find, and every run from then "
           "on dies before any layer is added: Generate appears to "
           "work and no map arrives. Re-anchored 2026-08-17, when the "
           "lookup gained the line that follows a rename and the two "
           "the entry stood on stopped being adjacent"),

  # SPANS TWO GUARDS, and that is the finding rather than a shortcut.
  # A restyle arriving while the GeoPackage is being written is
  # stopped twice over -- once because a task is still held (
  # _finish_run clears it only after _add_output_layers returns) and
  # once because writing to a GeoPackage releases the old layer
  # handles first, so the records point at layers that have gone.
  # Measured: breaking EITHER on its own leaves
  # test_a_restyle_arrives_while_the_geopackage_is_written green,
  # because the other still holds. So there is no single-line break
  # this test can catch, and an entry pretending otherwise would
  # report SURVIVED and be read as a hole in the test. Both are
  # defeated here, in one contiguous span; the guards between them are
  # left standing, including the one unobservable-layer-retiles
  # already owns.
  dict(name="cardinality-warning-fires-at-sixty-one", file=DIALOG,
       old="          if idx >= 0 and len(mem.uniqueValues(idx)) > 60:",
       new="          if idx >= 0 and len(mem.uniqueValues(idx)) > 61:",
       test="test_the_cardinality_warning_fires_on_the_side_it_should",
       why="a SURVIVOR of batch 11, triaged then as a threshold nobody "
           "could state a harm for and accepted on that basis. That was "
           "half right: the harm is thin at any one count, but the "
           "BOUNDARY is a real claim -- a field with sixty-one "
           "categories is warned about and one with sixty is not -- and "
           "a test standing either side of it is a boundary test rather "
           "than a pinned constant. Written from the idea list without "
           "knowing it would land on a known survivor"),
  # THREE ENTRIES FOR ONE DEFECT, because three separate things had to
  # be true and each was wrong on its own. Two earlier attempts at
  # this were reverted for guessing; the trace behind
  # WEAVINGSPACE_ADOPT_DUMP named all three.
  dict(name="adoption-outranks-the-project-being-replaced", file=DIALOG,
       old="    if self._project_is_being_replaced or \\\n"
           "        tile_id not in self._opacity_choices:",
       new="    if tile_id not in self._opacity_choices:",
       test="test_a_second_project_does_not_take_the_first_ones_opacity",
       why="tile ids repeat across projects, so 'fill in only where "
           "the dialog has nothing' declines the incoming layer's own "
           "opacity in favour of the outgoing project's -- the user's "
           "40 per cent found and refused"),
  dict(name="the-previous-table-only-fills-a-gap", file=DIALOG,
       old="      if prev is not None and \"opacity\" in prev \\\n"
           "          and tid not in self._opacity_choices:",
       new="      if prev is not None and \"opacity\" in prev:",
       test="test_a_second_project_does_not_take_the_first_ones_opacity",
       why="writing the previous table back unconditionally makes the "
           "WIDGETS the authority, and after a project is replaced "
           "those widgets belong to the project that has gone: it put "
           "100 back over the 40 adoption had just recovered"),
  dict(name="the-opacity-cell-follows-its-record", file=DIALOG,
       old="    elif row_id and row_id in self._opacity_choices:",
       new="    elif False:",
       test="test_a_second_project_does_not_take_the_first_ones_opacity",
       why="the cell is CREATED and was never updated, which is "
           "invisible while its own handler is the only writer -- so a "
           "cell standing from the outgoing project went on showing "
           "100 over a layer drawn at 40, and the table and the map "
           "disagreed in silence"),
  dict(name="reopened-opacity-is-read-from-the-layer", file=DIALOG,
       # RE-ANCHORED 2026-08-18: the condition above this gained the
       # "or the project is being replaced" arm, so the old anchor's
       # first line no longer exists. The behaviour it guards is the
       # ASSIGNMENT, which is unchanged.
       old="      self._opacity_choices[tile_id] = max(0, min(100, round(\n"
           "        layer.opacity() * 100)))",
       new="      pass  # mutation: the dialog forgets the layer's opacity",
       test="test_a_project_round_trip_changes_nothing_a_user_chose",
       why="QGIS persists layer opacity in the project, and until "
           "2026-08-13 the dialog never read it back: a reopened "
           "project showed 100% in the table while the layer was still "
           "at the 60% chosen. Losing a setting would be better than "
           "this -- _add_output_layers pushes the dialog's belief onto "
           "the layer, so any later restyle silently undid a choice "
           "still visible in QGIS's own layer panel. Found by a "
           "differential written before anybody knew what it would "
           "catch: the round trip compares every choice at once rather "
           "than the three a test would think to name"),
  dict(name="ramp-cell-and-map-agree-differentially", file=BRIDGE,
       old="    renderer.setSourceColorRamp(ramp.clone())",
       new="    pass  # mutation: the renderer forgets which ramp made it",
       test="test_the_ramp_cell_agrees_with_the_map",
       why="the SAME mutation as the entry below, deliberately, and "
           "named for a different test. That one was written from the "
           "defect, already knowing the answer. This one was written "
           "from a SHAPE -- the table and the map are two descriptions "
           "of which ramp colours an element, so they must agree -- "
           "with no knowledge of any particular fault. If it catches "
           "the same mutation, the shape finds this class of defect "
           "rather than the author having found this one, which is the "
           "whole argument for pointing differentials at the other "
           "pairs (ROADMAP.md, 'two views of one truth')"),
  dict(name="categorized-renderer-records-its-ramp", file=BRIDGE,
       old="    renderer.setSourceColorRamp(ramp.clone())",
       new="    pass  # mutation: the renderer forgets which ramp made it",
       test="test_the_dock_reapplying_the_same_ramp_discards_the_hand_picks",
       why="the graduated path has always recorded its source ramp and "
           "the categorized path did not, which cost a real defect: "
           "_on_layer_style_edited recognises a clean classify by "
           "asking the renderer which ramp it carries, so against a "
           "renderer that carried none the answer was always None, the "
           "clean-ramp branch was unreachable, and a ramp applied in "
           "QGIS's dock was adopted as Custom hand-picks instead of "
           "replacing them. It also left QGIS's own Categorized panel "
           "showing no ramp for our element layers"),
  dict(name="ramp-swap-only-on-a-mode-change", file=DIALOG,
       old="      moved = row_tid is None or "
           "self._synced_modes.get(row_tid) != mode",
       new="      moved = True  # mutation: swap on every sync, as before",
       test="test_a_ramp_you_are_offered_is_the_ramp_you_get",
       why="_sync_row substitutes a qualitative palette when a row turns "
           "categorical carrying a sequential ramp, which is right for a "
           "MODE CHANGE and wrong for a pick made on a row already in "
           "that mode. Unconditional, it ran on every data-tab change, "
           "so a ramp the dropdown had just offered was swapped straight "
           "back out after the pick had destroyed the element's "
           "hand-picked colours, with a message bar reporting a ramp "
           "change that never happened. Found by the stochastic hunt "
           "2026-08-13; present since the initial commit"),
  dict(name="class-source-contents-are-in-the-signature", file=DIALOG,
       old='            a.get("class_source_stamp"), a.get("single_colour"),',
       new='            None, a.get("single_colour"),  # mutation',
       test="test_an_edited_class_source_reaches_the_map",
       why="both signatures carried the class source's TOKEN and nothing "
           "about the file's contents, so a scheme rewritten on disk "
           "left every signature equal: the restyle path skipped the "
           "element as already correct, the run path carried the old "
           "renderer over, and a user who edited their scheme and "
           "pressed Generate got the old colours back with nothing said. "
           "Measured 2026-08-13"),
  dict(name="an-unreadable-class-source-keeps-its-colours", file=DIALOG,
       old='        elif a.get("class_source") in unreadable:',
       new='        elif False:  # mutation: repaint from a file that failed',
       test="test_a_moved_class_source_survives_a_restyle",
       why="the restyle fast path swallowed a class source it could not "
           "read and seeded the element from nothing, painting automatic "
           "colours over the user's imported scheme with no notice and "
           "the cell still naming the file. Its re-tile twin keeps the "
           "map and names the file, which is the settled behaviour: a "
           "file that has gone is a reason to stop consulting it, not a "
           "reason to repaint somebody's map"),
  dict(name="categorized-adoption-recovers-its-colours", file=DIALOG,
       old="      if recovered:\n        self._category_colours.setdefault(tile_id, {})[field] = recovered",
       new="      pass  # mutation: recover nothing for a categorized row",
       test="test_a_reopened_project_keeps_an_imported_class_scheme",
       why="a reopened project keeping a categorical scheme that came "
           "from an imported QML. Nothing stamps the file token, so the "
           "row comes back on a default ramp; unless the COLOURS are "
           "recovered off the renderer the next Generate re-seeds from "
           "that ramp and paints the imported scheme away. The "
           "graduated twin has recovered its colours positionally all "
           "along, five lines from a categorized branch that returned "
           "having recovered nothing"),
  dict(name="an-inset-that-eats-the-design-is-named", file=DIALOG,
       old="      self.mod_t_inset.value()) if self.mod_t_inset.value() else None",
       new="      self.mod_t_inset.value()) if False else None  # mutation",
       test="test_an_inset_that_eats_the_design_says_so",
       why="a tiles inset large enough to swallow elements being "
           "reported in terms of the inset. Without the check, a "
           "partial collapse reaches the user as the library's own "
           "'ValueError: You have passed make_valid=False along with "
           "1978 invalid input geometries', and a total collapse as "
           "'Assign at least one variable' -- both true of something, "
           "neither about the control the user just moved"),
  dict(name="size-guard-estimate-bounds-the-count", file=BRIDGE,
       old="  covered = ground + edge * tile_diag + 4 * tile_diag * tile_diag",
       new="  covered = (ground + edge * tile_diag) / 3  # mutation: under",
       test="test_size_guard",
       why="the guard's whole job is to be an UPPER bound on the tile "
           "count, and this radius sets it. A third instead of a half "
           "takes the estimate to four ninths of the truth, so a "
           "design that should be refused is attempted and QGIS stops "
           "responding while the library works -- which is the defect "
           "in this test's own Regression line. It survived the "
           "original test because that case is extreme enough for "
           "four ninths of it to still exceed the limit, and because "
           "the estimate was allowed to sit anywhere up to ten times "
           "the real count"),
  dict(name="reverse-preset-scheme-ramp", file=BRIDGE,
       old='    ramp.setColors([(colour, "") for colour in reversed(ramp.colors())])',
       new="    pass  # mutation: leave the scheme in its original order",
       test="test_reverse_runs_a_qualitative_palette_backwards",
       why="get_ramp reverses three different ways, and this is the "
           "branch for QGIS's named colour lists -- which is what "
           "every categorical palette this plugin installs is. Gradient "
           "ramps invert two lines below and were the only branch "
           "tested, so removing this left Reverse reading as ticked "
           "while the map did not change, for tab10 and every other "
           "qualitative palette"),
  # NO entry for dialog.py:4797 (_live_pending = False -> True), and
  # the absence is deliberate. It was written as one, on the stated
  # harm that a memory never cleared would have each finished run arm
  # the next and the map rebuild itself for as long as the dialog was
  # open. The entry SURVIVED, and re-reading the code says why: the
  # re-armed timer reaches _maybe_live_generate, which returns at
  # "nothing changed since the last run" before it can call _generate,
  # so the second cycle costs one debounce and stops. The harm does
  # not exist as described, so the survivor is ACCEPTED and lowers the
  # rate honestly rather than being closed by a test contorted until
  # it killed something. test_a_queued_live_rerun_happens_once_and_stops
  # is kept anyway -- it pins a settled design decision, one run at a
  # time with the rerun spent when it lands -- but it is not claimed
  # to close this mutant. (2026-08-12.)
  dict(name="auto-spacing-button-tooltip", file=DIALOG,
       old='    auto.setToolTip("A coarse value from the layer extent, good for iterating")',
       new="    pass  # mutation: the Auto button explains nothing",
       test="test_every_control_explains_itself",
       why="the README promises every control carries a tooltip. This "
           "one survived because the button is a local variable, never "
           "stored on the dialog, and the test walked a hand-kept list "
           "of attribute names; it walks the widget tree now"),
  dict(name="edit-colours-button-tooltip", file=DIALOG,
       old="      button.setToolTip(tip)",
       new="      pass  # mutation: the Edit colours button says nothing",
       test="test_every_control_explains_itself",
       why="the same hole, reached differently: this button lives in a "
           "table cell rather than on the dialog. Its tooltip is the "
           "one that explains why the button is DISABLED, which is "
           "exactly when a user goes looking for an explanation"),
  dict(name="manual-wheel-tags-universal-last", file=DEPS,
       old='  tags.append("py3-none-any")',
       new="  pass  # mutation: no universal wheel tag at all",
       test="test_support_logic",
       why="_manual_tags is the fallback for QGIS builds carrying "
           "neither packaging nor pip, and it is unreachable on any "
           "machine that has either -- which is every machine this "
           "suite runs on. Drop the universal tag and a pure-python "
           "wheel matches nothing, so provisioning fails on precisely "
           "the platform least able to repair it by hand"),
  # Written 2026-08-13 alongside the four tests for ideas 29-32 of
  # docs/TEST-IDEAS.md -- the map's own edges, where a wrong map
  # looks exactly like a right one. Every anchor was re-checked
  # against this tree before splicing, since dialog.py moved the
  # same day.
  # ---- ideas 29-32, "the map itself"
  #
  # Anchored on the COLLAPSE rather than on the Unclassed line above
  # it, because the behaviour at stake is an ORDERING -- Unclassed
  # fixes k at 50, and the constant-column collapse then overrides it
  # -- and an ordering cannot be undone by editing one site. Excluding
  # k == 50 from the collapse is that ordering lost, and nothing else:
  # a row asking for the ordinary five classes still collapses, so
  # test_a_constant_column_draws_one_class_and_says_so goes on passing
  # and this entry stays aimed at the one scheme that arrives here
  # with a class count already fixed.
  dict(name="constant-column-beats-unclassed-fifty", file=BRIDGE,
       old='  if distinct == 1 and not pinned_here:\n    k = 1',
       new='  if distinct == 1 and not pinned_here and not unclassed:\n    k = 1  # mutation: the collapse no longer beats the fifty',
       test="test_unclassed_over_a_constant_column",
       why="Quant: Unclassed cuts fifty linear intervals, so over a "
           "column that is 7 everywhere the legend claims fifty grades "
           "of a variable with one value, and every feature falls in "
           "class 0 -- the ramp's near-white end, which a reader takes "
           "for missing data rather than for one value"),
  # RE-ANCHORED 2026-08-25, from the dialog into `size_band`: the
  # ceiling is a BAND EDGE now rather than a refusal, and the
  # comparison that decides it moved with it. The claim is exactly
  # what it was -- which side of the line the boundary falls on.
  dict(name="size-guard-refuses-at-the-cap", file=BRIDGE,
       old="""  if estimate > MAX_TILES_HARD:""",
       new="""  if estimate >= MAX_TILES_HARD:  # mutation: escalate at the cap""",
       test="test_the_size_guard_at_its_refusal_boundary",
       why="MAX_TILES_HARD is the largest tile count asked about in "
           "the ORDINARY words, not the first one asked about in the "
           "heavy ones; one step either way and a design the plugin "
           "draws without comment is escalated, or one that may take "
           "the machine is waved through mildly. Every other test of "
           "this guard stands orders of magnitude from the line and "
           "cannot see which side of it the comparison falls"),
  dict(name="unassigned-row-carries-no-field", file=DIALOG,
       old="""      var = var_combo.currentText()
      var = None if var == "---" else var
      mode_raw = (mode_combo.currentText() if mode_combo""",
       new="""      var = var_combo.currentText()
      var = var if var else None  # mutation: "---" reads as a field
      mode_raw = (mode_combo.currentText() if mode_combo""",
       test="test_an_unassigned_element_beside_elements_sharing_one_field",
       why="an element the user deliberately left empty must draw as "
           "flat fill and say 'no data' in its layer name; read as a "
           "field called '---' it is styled like everybody else, so a "
           "design where every other element shares one column comes "
           "back looking exactly as though the user had assigned it"),
  # The second half of the same test, and a defect this project has
  # actually shipped once: one renderer seeded for every element.
  # Aimed at _add_output_layers' loop, not at seed_renderer itself,
  # since the fast restyle path calls the same function correctly.
  dict(name="each-element-keeps-its-own-renderer", file=DIALOG,
       old="""        bridge.seed_renderer(
          out, a, templates.get(a.get("class_source")),""",
       new="""        a = assignments[0] if assignments else a  # mutation: one
        bridge.seed_renderer(
          out, a, templates.get(a.get("class_source")),""",
       test="test_an_unassigned_element_beside_elements_sharing_one_field",
       why="elements that classify the SAME column can only be told "
           "apart by their ramps, so a renderer shared between them "
           "produces a perfectly plausible map in which several parts "
           "of the pattern agree because they were told to, not "
           "because the data does"),
  dict(name="tile-inset-is-percent-of-spacing", file=DIALOG,
       old="        unit = unit.inset_tiles(self.mod_t_inset.value() * spacing / 100)",
       new="        unit = unit.inset_tiles(self.mod_t_inset.value() * spacing / 1000)",
       test="test_an_inset_that_swallows_tiles_leaves_no_half_map",
       why="the inset is a percentage of the spacing, and a tenth of "
           "that is a control that looks alive and barely moves the "
           "map; it also silently voids every test that reaches the "
           "point where an inset consumes a tile, which is why the "
           "test names this in its own guard rather than only in an "
           "assertion at the end"),
  dict(name="tile-boundaries-reach-the-symbol", file=BRIDGE,
       old="""  opts.update({"outline_color": "35,35,35,255", "outline_width": "0.1"}
              if outline else {"outline_style": "no"})""",
       new="""  opts.update({"outline_style": "no"})  # mutation: never stroke""",
       test="test_an_inset_that_swallows_tiles_leaves_no_half_map",
       why="Draw tile boundaries is the only control that separates "
           "one tile from its neighbour where the fills are close, and "
           "losing it is invisible on any map whose tiles differ in "
           "colour anyway -- so it is checked on the geometry where it "
           "matters, a design inset until its tiles are slivers"),
  # --- 0.24.3: one legend per variable, and a ramp that comes home
  dict(name="breaks-come-from-the-whole-map", file=BRIDGE,
       old="  if classify_from is None:",
       new="  if True:  # mutation: classify each element's own tiles",
       test="test_one_variable_gets_one_legend_wherever_it_appears",
       why="an element layer holds only its own tiles, so cutting the "
           "breaks from it gives every element a different legend for "
           "the same column -- one colour meaning four different "
           "numbers on a map made for reading elements against each "
           "other. The mutation is exactly the behaviour that shipped "
           "until 2026-08-14"),
  # REPLACES `classes-never-outnumber-the-values`, whose behaviour was
  # withdrawn on 2026-08-16. That entry guarded the class REDUCTION,
  # which cured the wrong-colour symptom by shortening the ladder --
  # and shortening re-samples the ramp, moving colours nobody chose.
  # A NUDGE replaced it and was itself withdrawn hours later, so
  # neither mechanism exists now: the symptom is left visible and
  # reported in words by `empty_classes_message`. Kept as the reason
  # this entry sits here rather than beside a reduction that is gone.
  dict(name="a-copy-carries-the-pin-flags", file=DIALOG,
       old='      if source_record.get(end) is None:\n        continue',
       new='      if True:  # mutation: the flags stay behind\n        continue',
       test="test_a_copied_classification_carries_the_whole_row",
       why="the pin FLAG is a different statement from the boundary "
           "VALUES, and a copy must carry both: without the flag a "
           "pinned source arrives unpinned, its swatch draws no box "
           "and unpinning that end does nothing"),
  dict(name="a-copied-ladder-is-fitted", file=BRIDGE,
       old="  bounds.append((interior[-1], max(high, interior[-1])))",
       new="  bounds.append((interior[-1], interior[-1]))  # mutation",
       test="test_a_copied_ladder_is_fitted_to_the_column_it_lands_on",
       why="the receiving column's own max is the top class's upper "
           "bound, so without it a ladder copied onto a WIDER column "
           "stops short and everything above the copied ladder's last "
           "break falls outside every class and paints as no data"),
  dict(name="an-unworn-class-is-marked", file=BRIDGE,
       old="        worn.add(index)",
       new="        pass  # mutation: every class looks worn",
       test="test_a_copied_ladder_is_fitted_to_the_column_it_lands_on",
       why="a copied ladder can leave classes the receiving data "
           "cannot reach, and those are kept rather than dropped, so "
           "the emptiness has to be visible: unmarked, the legend "
           "shows swatches no tile uses with nothing to say so"),
  dict(name="the-landing-re-reads-the-pins", file=DIALOG,
       old="""          a["pinned"] = self._pinned_bounds.get(
            a["id"], {}).get(a["var"])""",
       new="""          pass  # mutation: trust the snapshot the run began with""",
       test="test_a_pin_set_during_a_run_is_not_lost",
       why="the colour editor is usable while a tiling is in flight "
           "and the restyle path declines during one, so a pin set in "
           "that window is seeded from the run's stale snapshot, "
           "destroyed as it lands, and stamped ABSENT on the layer so "
           "a reopened project cannot bring it back either. The same "
           "defect was found for categorical colours, then for "
           "graduated ones, and this is its third arrival"),
  dict(name="a-blank-row-is-reported", file=DIALOG,
       old="""        note = bridge.unmappable_areas_message(""",
       new="""        note = None if True else bridge.unmappable_areas_message(""",
       test="test_a_row_with_no_geometry_is_named",
       why="layer_to_gdf drops a geometry-less row and until 2026-08-14 "
           "said nothing, so a user comparing their attribute table "
           "against the map found a row unaccounted for with nothing "
           "on screen to explain it"),
  dict(name="a-pin-is-keyed-by-its-field", file=DIALOG,
       old="""        "pinned": (self._pinned_bounds.get(tid_text, {}).get(var)""",
       new="""        "pinned": (next(iter(self._pinned_bounds.get(
                     tid_text, {}).values()), None)""",
       test="test_a_pin_belongs_to_an_element_and_a_field",
       why="pins are keyed by element AND field like the hand-picked "
           "colours, so without the field a bound set for one column "
           "is applied to whatever column the row is switched to -- "
           "numbers from one distribution deciding another's classes"),
  dict(name="a-copy-degrades-to-its-pins", file=DIALOG,
       old="""      kept = {key: value for key, value in record.items()
              if key in ("low", "high")}""",
       new="""      kept = {}  # mutation: a count change throws the pins away too""",
       test="test_a_session_of_pinning_and_copying_holds_together",
       why="a copy is made for one class count and one set of breaks, "
           "so a new count retires the copied VALUES -- but the pin "
           "flags and their two bounds are a smaller and more durable "
           "statement and must survive, with the scheme recomputing "
           "the middle around them"),
  dict(name="a-pin-redraws-its-own-window",
       file="weavingspace_qgis/category_editor.py",
       # RE-ANCHORED 2026-08-17: `_pin_toggled` gained a
       # `_sync_pin_controls` call after this line when an Unclassed
       # end came to be named by two controls, so the old anchor --
       # which ran straight into `def _bound_edited` -- matched
       # nothing and reported nothing, which reads exactly like
       # success. Found by check_standards at push time.
       # RE-ANCHORED AGAIN 2026-08-19, and by the same move: the mark
       # sweep `_refresh_marks` was added after the sync when the Pin
       # column's checked state was replaced by an outline on the box.
       # TWICE NOW this entry has been broken by a line appended below
       # its anchor, which is the argument for anchoring on the CALL
       # being guarded rather than on the block that follows it.
       old="    self._redraw_bounds(answer)\n"
           "    self._sync_pin_controls(which, pair)\n"
           "    self._refresh_marks()\n\n"
           "  def _bound_edited",
       new="    pass\n\n  def _bound_edited",
       test="test_pinning_redraws_the_window_it_was_typed_into",
       why="a pin recomputes every break between the pinned ones, so "
           "without this the window prints the ladder from before it "
           "and the other end's control offers a bound the map no "
           "longer has -- which is applied if that pin is clicked"),
  dict(name="a-late-layer-choice-is-noticed", file=DIALOG,
       old="    QTimer.singleShot(0, self._settle_layer_choice)",
       new="    pass  # mutation: never re-check after the combo settles",
       test="test_the_plugin_opened_before_the_data_still_works",
       why="the layer chooser can emit its signal before it has a "
           "current layer, so the assignment table is built from no "
           "fields -- a user who opens the plugin before loading data "
           "is offered no variables at all and told to assign one"),
  dict(name="a-rebuilt-table-asks-the-layer", file=DIALOG,
       old='    # than trusted from a stamp.\n    self._refresh_deferring_rows()',
       new='    # than trusted from a stamp.\n    pass  # mutation: the rebuilt rows never ask the layer',
       test="test_deferral_survives_a_project_round_trip",
       why="rows are built from the dialog's records, so a project "
           "reopened after an element was styled in QGIS comes back "
           "naming a plugin style over a rule-based map, and the next "
           "Generate destroys the user's work"),
  dict(name="deferral-closes-the-open-editor", file=DIALOG,
       old="        if self._open_editor is not None:\n"
           "          self._open_editor.reject()",
       new="        if False:\n          self._open_editor.reject()",
       test="test_deferral_closes_the_colour_editor_under_it",
       why="the window's rows describe a renderer that has just been "
           "replaced, and its controls apply immediately, so leaving "
           "it open invites an edit that lands on nothing"),
  # TWO ENTRIES, BECAUSE THE TWO ROUTES NEEDED DIFFERENT REPAIRS and
  # fixing the first left the second untouched. A restyle keeps the
  # layer, so the records are LEFT ALONE; a re-tile hands the element
  # a new layer, so they are CARRIED.
  dict(name="deferral-keeps-the-dialogs-opacity", file=DIALOG,
       old="        if carried_while_deferring:\n"
           "          out.setOpacity(max(0, min(100, a.get(\"opacity\", 100))) / 100.0)\n"
           "        elif old_layer_opacity.get(tid) is not None:",
       new="        if old_layer_opacity.get(tid) is not None:",
       test="test_deferral_keeps_opacity_and_the_twins_own_styling",
       why="the Opacity cell stays LIVE while an element defers, so "
           "carrying the old layer's value at the landing overrides "
           "the number the user just set: an element faded to 30 per "
           "cent comes back from a re-tile at full strength with the "
           "table still reading 30"),
  dict(name="a-deferring-twin-keeps-its-own-styling", file=DIALOG,
       old="    if not self._element_is_deferring(tile_id):\n"
           "      colours, kinds = self._absence_colours_and_kinds(",
       new="    if True:\n"
           "      colours, kinds = self._absence_colours_and_kinds(",
       test="test_deferral_keeps_opacity_and_the_twins_own_styling",
       why="the run-landing path carries a paired layer's renderer "
           "whenever its element is kept by hand, and this path "
           "repainted it unconditionally -- so hand styling on a "
           "missing-value layer survived a re-tile and was destroyed "
           "by a restyle, which is the more ordinary act of the two"),
  dict(name="deferral-leaves-the-stamp-alone", file=DIALOG,
       old="    if bridge.expressible_style(layer.renderer()) is None:\n"
           "      return\n"
           "    picked = assignment.get(\"category_colours\")",
       new="    picked = assignment.get(\"category_colours\")",
       test="test_deferral_does_not_erase_the_work_behind_it",
       why="a deferring element is reported with no picks and no pins, "
           "which at this site is indistinguishable from a user who "
           "cleared everything -- so restyling an element in QGIS "
           "removes its pinned bounds and hand-picked colours from the "
           "saved project while the open window still shows them"),
  dict(name="deferral-carries-the-stamp-across-a-retile", file=DIALOG,
       old="      if bridge.expressible_style(out.renderer()) is None:\n"
           "        for name, value in (old_stamps.get(tid) or {}).items():\n"
           "          out.setCustomProperty(name, value)",
       new="      if False:\n"
           "        for name, value in (old_stamps.get(tid) or {}).items():\n"
           "          out.setCustomProperty(name, value)",
       test="test_deferral_does_not_erase_the_work_behind_it",
       why="a re-tile hands a deferring element a NEW layer, so "
           "declining to write its records means they are never "
           "written at all -- the renderer is carried across and the "
           "record behind it is not, which loses the same work by the "
           "other road"),
  dict(name="a-type-change-defers-to-qgis", file=DIALOG,
       old='    if now_deferring:\n      if not was_deferring:',
       new='    if False:\n      if not was_deferring:',
       test="test_a_renderer_the_row_cannot_name_defers_to_qgis",
       why="without this a renderer TYPE changed in the styling panel "
           "goes through the colour branches, which adopt category "
           "picks onto a row still reading Graduated while the ramp "
           "cell names a ramp that decides nothing"),
  dict(name="the-row-follows-the-dock-both-ways", file=DIALOG,
       old="    self._refresh_deferring_rows()\n    if now_deferring:",
       new="    if now_deferring:\n      self._refresh_deferring_rows()",
       test="test_the_row_follows_the_dock_back_out_of_deferring",
       why="reconciling only when the new renderer is unnameable "
           "leaves the row saying Deferring, with its controls inert, "
           "over a map the plugin could describe -- and the next "
           "Generate seeds straight over it"),
  dict(name="an-element-can-be-taken-back", file=DIALOG,
       old="      kept_by_hand = ((unchanged or carried_while_deferring)\n"
           "                      and not reclaimed)",
       new="      kept_by_hand = (unchanged or carried_while_deferring)",
       test="test_taking_an_element_back_from_qgis_restyles_at_once",
       why="picking back the style an element had before it was "
           "deferred restores its old signature exactly, so without "
           "the reclaim test both seeding paths keep the renderer "
           "they are being asked to replace and the element can never "
           "be taken back"),
  # TWO ARMS OF ONE ACT, taking an element back from QGIS with a plain
  # fill: the colour has to travel and the mode has to last. Fixing
  # either alone loses the fill, by a different door.
  dict(name="the-deferral-exit-carries-the-fill", file=DIALOG,
       old="                self._single_colours[item.text()] = "
           "symbol.color().name()",
       new="                pass  # mutation: the mixed colour is dropped",
       test="test_taking_an_element_back_keeps_the_fill_you_mixed",
       why="moving the row to Single colour changes the ASSIGNMENT, "
           "which is the condition under which Generate re-seeds an "
           "element -- so without the colour travelling with the "
           "label, the plugin paints its own default over the fill "
           "mixed in the dock: 1,764 interior pixels of #0b1e2d became "
           "1,926 of #3c8bc2"),
  dict(name="the-deferral-exit-marks-the-combo-touched", file=DIALOG,
       old="        combo.setProperty(\"touched\", True)\n"
           "        combo.setProperty(\"last_style\", label)\n"
           "        combo.blockSignals(False)",
       new="        combo.setProperty(\"last_style\", label)\n"
           "        combo.blockSignals(False)",
       test="test_taking_an_element_back_keeps_the_fill_you_mixed",
       why="`_refresh_table` restores a row's style only where the "
           "combo carries `touched`, so a style written here with "
           "signals blocked survives until the first spacing nudge and "
           "then reverts -- taking the user's plain fill with it at the "
           "next Generate. The identical line had been added to "
           "`_row_follows_the_renderer` hours earlier and this writer "
           "of the same widget was never grepped for"),
  dict(name="a-variable-change-ends-deferral-in-the-row", file=DIALOG,
       old="    if mode_combo.currentText() == self.DEFERRING:\n"
           "      mode_combo.blockSignals(True)",
       new="    if False:\n      mode_combo.blockSignals(True)",
       test="test_a_deferring_element_moved_to_words_still_draws",
       why="the row keeps a mode no downstream guard knows, so the "
           "text-field guard never fires and a graduated renderer is "
           "seeded over words -- every tile outside every class, and "
           "a run that reports success"),
  dict(name="the-fast-path-respects-deferral", file=DIALOG,
       old='        if a.get("mode_raw") == self.DEFERRING \\\n            and bridge.expressible_style(layer.renderer()) is None:',
       new='        if False:',
       test="test_a_deferring_element_keeps_its_renderer_across_a_generate",
       why="a dock edit moves the element's signature by itself, "
           "because _signature carries the mode and the mode is now "
           "Deferring -- so without this arm the very next Generate "
           "re-seeds a graduated renderer over the work somebody just "
           "did in the styling panel, saying only 'no re-tiling "
           "needed'"),
  dict(name="a-deferring-element-keeps-its-renderer", file=DIALOG,
       old='      kept_by_hand = ((unchanged or carried_while_deferring)\n'
           '                      and not reclaimed)',
       new='      kept_by_hand = unchanged and not reclaimed',
       test="test_a_deferring_element_keeps_its_renderer_across_a_generate",
       why="a Generate rebuilds every element layer, so without this "
           "the renderer somebody built in QGIS is destroyed by the "
           "next spacing change -- which is the whole of what "
           "deferring promises not to do"),
  dict(name="the-deferring-swatch-comes-from-the-layer", file=DIALOG,
       old="    if self._element_is_deferring(tile_id):\n      layer = QgsProject.instance().mapLayer(",
       new="    if False:\n      layer = QgsProject.instance().mapLayer(",
       test="test_a_deferring_row_shows_the_colours_qgis_is_drawing",
       why="the plugin no longer decides a deferring element's "
           "colours, so a swatch built from its records shows colours "
           "the map does not have -- a control describing a map it "
           "will not draw"),
  # THE THREE BELOW ARE THE SAME QUESTION ASKED OF THE DESIGN VIEW,
  # and they are anchored here rather than beside the preview code so
  # that the pair is visible: the entry above was written on
  # 2026-08-15 for the ramp cell, and `_table_id_colours` was not
  # looked at until a hunt measured it on 2026-08-17. Each arm is one
  # argument in one expression, so each needs its own entry -- a
  # single anchor covering the block would report `caught` while two
  # of the three axes sat dead.
  # RE-ANCHORED and JOINED BY A SECOND 2026-08-17, when a hunt found
  # the fourth arm of this expression an hour after the first three
  # were fixed: the branch now covers hand-picked colours as well as
  # deferral, so it needs an entry per arm.
  # ONE RULE REPLACED SIX BRANCHES on 2026-08-17: the preview shows
  # what the map draws. The two entries this supersedes -- a deferring
  # layer and hand-picked colours -- were separate arms of an `elif`
  # that no longer exists, and their behaviours are now the same line.
  dict(name="the-preview-reads-the-map", file=DIALOG,
       old="      base = self._drawn_preview_colour(a[\"id\"])",
       new="      base = None",
       test="test_the_design_view_paints_colours_the_map_contains",
       why="the design view goes back to describing the ROW instead of "
           "the MAP, which was wrong six times in one day: a deferring "
           "element at 102/255, a narrowed window at 142, hand-picked "
           "colours at 144, a constant column at 53, plus the row's "
           "Reverse and a column with nothing to classify"),
  dict(name="the-preview-follows-the-rows-direction", file=DIALOG,
       old="          base = bridge.ramp_swatch_colour(\n              a[\"ramp\"], bool(a.get(\"reverse\", False)),\n              tuple(a.get(\"range_bounds\", (0, 100))))",
       new="          base = bridge.ramp_swatch_colour(\n              a[\"ramp\"], False,\n              tuple(a.get(\"range_bounds\", (0, 100))))",
       test="test_the_design_view_paints_colours_the_map_contains",
       why="a reversed element previews in the FORWARD ramp's colour, "
           "which on a diverging ramp is the opposite end -- the "
           "preview keeps the colour it had while the ladder turns "
           "round underneath it, so it lands at the other end of the "
           "classes"),
  dict(name="the-preview-follows-the-display-window", file=DIALOG,
       old="          base = bridge.ramp_swatch_colour(\n              a[\"ramp\"], bool(a.get(\"reverse\", False)),\n              tuple(a.get(\"range_bounds\", (0, 100))))",
       new="          base = bridge.ramp_swatch_colour(\n              a[\"ramp\"], bool(a.get(\"reverse\", False)),\n              (0, 100))",
       test="test_the_design_view_paints_colours_the_map_contains",
       why="narrowing the Ramp Display Range moves every colour the "
           "map draws and none the preview draws: measured on Reds at "
           "0-20%, the design view painted 15,460 pixels of #e7342a "
           "the map holds none of, 142/255 from anything that element "
           "actually paints"),
  dict(name="the-signature-follows-the-column", file=DIALOG,
       old="            a.get(\"value_digest\"),",
       new="",
       test="test_a_retyped_column_reclassifies_the_map",
       why="without the column's own digest an element keeps the "
           "renderer built for the values as they were, so a column "
           "retyped in QGIS goes on being drawn with the old data's "
           "breaks while its tiles carry the new values"),
  dict(name="adoption-takes-the-newest-group", file=DIALOG,
       old="    group = self._newest_output_group(root)",
       new="    group = root.findGroup(GROUP_BASE_NAME)",
       test="test_a_reopened_plugin_adopts_the_group_it_last_wrote",
       why="the bare name cannot find 'WeavingSpace tiles 2', so a "
           "reopened plugin adopts the result the user chose to KEEP "
           "and the next Generate overwrites it, while the map they "
           "were working on is orphaned"),
  dict(name="a-missing-ramp-still-draws-categories", file=BRIDGE,
       old="  ramp = ramp_or_default(ramp_name, reverse)[0]",
       new="  ramp = get_ramp(ramp_name, reverse)",
       test="test_a_ramp_the_library_lacks_still_draws_a_map_and_says_so",
       why="a ramp name the style library does not hold makes "
           "get_ramp answer None, and the next line asks it for a "
           "colour: the categorized renderer raises AttributeError "
           "from inside a function that promises a renderer, which is "
           "how a whole map failed on a container that never had the "
           "plugin's palettes"),
  dict(name="a-missing-ramp-still-draws-classes", file=BRIDGE,
       old="  renderer.setSourceColorRamp("
           "ramp_or_default(ramp_name, reverse)[0])",
       new="  renderer.setSourceColorRamp(get_ramp(ramp_name, reverse))",
       test="test_a_ramp_the_library_lacks_still_draws_a_map_and_says_so",
       why="the graduated twin fails more quietly than the "
           "categorized one: a None source ramp raises nothing and "
           "leaves every class wearing the placeholder grey, so the "
           "map reads as no data everywhere while the data is fine"),
  dict(name="a-substituted-ramp-is-announced", file=DIALOG,
       old="            self._report_quietly("
           "bridge.missing_ramp_message(name))",
       new="            pass",
       test="test_a_ramp_the_library_lacks_still_draws_a_map_and_says_so",
       why="a map drawn in substitute colours has no other symptom: "
           "the row still names the ramp, the swatch still draws, and "
           "the user has no way to learn that the colours are not the "
           "ones they chose"),
  dict(name="the-unclassed-list-is-not-composited", file=EDITOR,
       old="      faded = self.table.palette().color(",
       new="      from qgis.PyQt.QtWidgets import QGraphicsOpacityEffect\n"
           "      self.table.setGraphicsEffect("
           "QGraphicsOpacityEffect(self.table))\n"
           "      faded = self.table.palette().color(",
       test="test_the_unclassed_list_fades_without_a_graphics_effect",
       why="a graphics effect renders the table into an offscreen "
           "pixmap while QAbstractScrollArea scrolls by blitting, so "
           "the two disagree and previously-painted class bounds stay "
           "visible behind the current ones -- the ghost numbers the "
           "maintainer photographed. The suite cannot see the artefact "
           "itself, which lives in the backing store, so what it holds "
           "is that the mechanism is absent"),
  dict(name="a-rename-during-a-run-keeps-the-group", file=DIALOG,
       old="    force_new = (self.opt_new_group.isChecked() or "
           "renamed_mid_run\n"
           "                 or theirs\n"
           "                 or self._new_group_chosen or (",
       new="    force_new = (self.opt_new_group.isChecked()\n"
           "                 or theirs\n"
           "                 or self._new_group_chosen or (",
       test="test_the_output_group_is_renamed_while_a_run_is_in_flight",
       why="renaming the output group while a tiling runs is how a "
           "user keeps that result, exactly as 'Create as new group' "
           "is -- so the landing must start a fresh group. Without "
           "this term the run finds the renamed group by its layers "
           "and replaces the keepsake, or empties it and leaves a "
           "named, empty group with nothing to undo"),
  dict(name="the-group-is-found-by-its-layers", file=DIALOG,
       old="      group = self._group_of_our_layers(root)",
       new="      group = None",
       test="test_a_renamed_group_is_still_the_group_the_next_run_replaces",
       why="falling back to the NAME alone cannot find a group the "
           "user renamed in the layers panel, so the next run builds "
           "a rival over the same GeoPackage tables -- and the miss "
           "also empties `_element_layer_ids`, which is read as "
           "`old_ids` immediately afterwards, so nothing is replaced "
           "and the abandoned group redraws the new data under the "
           "old class breaks"),
  dict(name="adoption-knows-a-renamed-group", file=DIALOG,
       old="    for node in root.children():",
       new="    for node in [n for n in root.children()\n"
           "                 if n.name().startswith(GROUP_BASE_NAME)]:",
       test="test_a_renamed_group_is_adopted_when_the_plugin_reopens",
       why="reading the group's NAME rather than its layers' custom "
           "property makes a renamed group invisible to a reopened "
           "plugin, so the next run starts a rival and leaves the "
           "user's own file-backed layers stale beneath it with the "
           "GeoPackage link dropped"),
  dict(name="the-bound-box-is-sized-from-the-data",
       file="weavingspace_qgis/category_editor.py",
       old="    box.setDecimals(max(_LEAST_DECIMALS, min(12, places)))\n"
           "    box.setRange(-_WIDEST_BOUND, _WIDEST_BOUND)",
       new="    box.setDecimals(6)\n"
           "    box.setRange(-1e12, 1e12)",
       test="test_a_pinned_bound_can_hold_the_numbers_a_column_carries",
       why="fixed limits cannot hold the numbers ordinary geographic "
           "columns carry: an area of 1.875e12 square metres pinned "
           "at 1e12 and a rate of 4e-07 pinned at zero, both silently, "
           "because pin_problem is asked about the number the control "
           "produced and that number is inside the data"),
  # THREE GUARDS THAT HAD A TEST AND NO ENTRY, written 2026-08-18.
  # The ledger's OWES column called these `test`, which means the test
  # exists and nothing has ever proved it fails when the behaviour it
  # names is broken -- and this project's own measurement is that
  # roughly one test in five, written that way, cannot fail at all.
  dict(name="deferral-keeps-the-no-data-split", file=DIALOG,
       old="    if mode in (\"Categorized\", \"Single colour\") or not mode:\n"
           "      return False",
       new="    if not mode:\n      return False",
       test="test_a_deferring_element_keeps_its_no_data_layer",
       why="a deferring element's mode reads 'Deferring to QGIS', which "
           "is neither Categorized nor Single colour, so without this "
           "the split is judged by a mode no branch below expects and "
           "the element's missing-value areas stop being drawn -- "
           "28,828 unpainted pixels of 490,000, holes in the map"),
  dict(name="the-scale-boxes-do-not-eat-a-keystroke", file=DIALOG,
       old="      box.setKeyboardTracking(False)\n"
           "      box.valueChanged.connect(self._queue_preview)",
       new="      box.setKeyboardTracking(True)\n"
           "      box.valueChanged.connect(self._queue_preview)",
       test="test_a_scale_between_minus_one_and_one_can_be_typed",
       why="`_skip_zero_scale` rewrites the box it is watching, so with "
           "tracking on it fires on the leading nought of -0.5, "
           "announces a landing on zero and steps past it: a mirrored "
           "design comes back UN-MIRRORED at a size that looks exactly "
           "right, with nothing said"),
  dict(name="the-printed-bounds-follow-the-pinned-ladder",
       file="weavingspace_qgis/category_editor.py",
       old="      for col, bound in enumerate(pair):\n"
           "        cell = self.table.item(row, col + offset)\n"
           "        if cell is not None:\n"
           "          cell.setText(self._format_bound(bound))",
       new="      for col, bound in enumerate(pair):\n"
           "        pass  # mutation: the written cells keep their old text",
       test="test_an_unclassed_row_pins_from_either_control",
       why="pinning an end moves every boundary in the ladder, and the "
           "class list goes on printing the numbers it held before -- "
           "so the window a user pins from describes a classification "
           "the map has stopped drawing. This is the entry that was "
           "owed: a hunt deleted this whole loop and the test passed, "
           "because its helper read the SPIN BOXES as well as the "
           "written cells and any change satisfied it"),
  dict(name="a-pin-rewrites-the-cells-it-moved",
       file="weavingspace_qgis/category_editor.py",
       old="      for col, bound in enumerate(pair):\n"
           "        cell = self.table.item(row, col + offset)\n"
           "        if cell is not None:\n"
           "          cell.setText(self._format_bound(bound))",
       new="      for col, bound in enumerate(pair):\n"
           "        pass",
       test="test_an_unclassed_row_pins_from_either_control",
       why="a pin recomputes every break between the pins, so a table "
           "that does not rewrite its cells goes on printing a ladder "
           "the map has left behind -- and this entry exists because "
           "the test SURVIVED this exact deletion until 2026-08-17, its "
           "helper reading the spin boxes as well as the cells and so "
           "being satisfied by boxes it already asserted directly"),
  dict(name="the-row-follows-the-layers-renderer",
       file="weavingspace_qgis/dialog.py",
       # RE-ANCHORED TWICE ON 2026-08-20. The count was briefly read on
       # both sides of this call, which separated the follow from the
       # isinstance below; deleting that delta put them back together,
       # so the anchor returns to the pair it had before.
       old="    self._row_follows_the_renderer(tile_id, renderer)\n"
           "    if isinstance(renderer, QgsGraduatedSymbolRenderer):",
       new="    if isinstance(renderer, QgsGraduatedSymbolRenderer):",
       test="test_a_row_follows_a_style_pasted_onto_its_layer_in_qgis",
       why="without it the table goes on describing the map the plugin "
           "last drew: a break retyped in QGIS's Symbology panel or a "
           "whole style pasted across elements reaches the layer and "
           "never the row, and the next Generate destroys it -- the "
           "field report against rc5"),
  dict(name="the-followed-row-keeps-its-new-signature",
       file="weavingspace_qgis/dialog.py",
       old="      self._last_signatures[tile_id] = self._signature(refreshed)\n"
           "      # ...AND THE STAMP AND THE FILE, which this method must do",
       new="      pass\n"
           "      # ...AND THE STAMP AND THE FILE, which this method must do",
       test="test_a_row_follows_a_style_pasted_onto_its_layer_in_qgis",
       why="the row moves with no signal, so without re-recording the "
           "signature the next restyle compares the layer against a row "
           "it has never seen and re-seeds the renderer it just "
           "followed, which is the damaging half of the same report"),
  dict(name="a-followed-count-reaches-the-record-too",
       file="weavingspace_qgis/dialog.py",
       # RE-ANCHORED 2026-08-19: the release of a copied ladder went in
       # between these two lines, so the pair no longer sits together.
       # Anchored on the WRITE alone, which is what this proves.
       old="        self._class_counts[tile_id] = int(count)",
       new="        pass  # mutation: write the spinner and not the record",
       test="test_a_row_follows_a_style_pasted_onto_its_layer_in_qgis",
       why="`_refresh_table` rebuilds a row's class count from "
           "`_class_counts` before the previous assignment, so writing "
           "the spinner alone leaves a followed count alive until the "
           "first spacing nudge and then reverts it -- destroying at "
           "the next Generate the classification the user set in "
           "QGIS's own Symbology panel, which is the report the follow "
           "exists to close"),
  dict(name="a-categorical-count-never-becomes-a-chosen-one",
       file="weavingspace_qgis/dialog.py",
       old="    if mode == \"Graduated\" and scheme != \"Unclassed\" \\\n"
           "        and counter is not None and hasattr(renderer, \"ranges\"):",
       new="    if counter is not None and hasattr(renderer, \"ranges\"):",
       test="test_a_row_follows_a_style_pasted_onto_its_layer_in_qgis",
       why="letting a categorized renderer's category count into the "
           "Classes cell is the leak that put a greyed 32 in front of "
           "the tester and clamped it to the 2-20 ceiling at the next "
           "rebuild, which is the 20 and 20 in their second screenshot"),
  dict(name="a-number-box-keeps-three-decimals",
       file="weavingspace_qgis/dialog.py",
       old="      box.setDecimals(max(_LEAST_FIGURES_DECIMALS,\n"
           "                          min(needed, max(0, 3 - digits))))",
       new="      box.setDecimals(min(needed, max(0, 3 - digits)))",
       test="test_every_number_box_holds_a_value_finer_than_its_step",
       why="without the floor the sweep puts the rotation, skew and "
           "angle boxes at ZERO decimals, so typing 22.5 into Rotate "
           "swallows the 5 and the tile unit is built at 22 degrees "
           "with nothing said -- decimals govern storage as well as "
           "display"),
  dict(name="a-ramp-combo-is-built-in-the-rows-direction",
       file="weavingspace_qgis/dialog.py",
       old="      icon = _ramp_icon(name, reversed_here)",
       new="      icon = _ramp_icon(name)",
       test="test_a_reversed_row_keeps_its_reversed_swatch_through_a_rebuild",
       why="drawing every item forward makes the flip last only until "
           "the next rebuild -- and a Generate rebuilds -- so a "
           "reversed element is read by a forward swatch and its next "
           "ramp is chosen from a dropdown showing every ramp the "
           "wrong way round"),
  dict(name="the-display-range-boxes-do-not-clamp-each-other",
       file="weavingspace_qgis/category_editor.py",
       old="    self.lower_spin.setRange(0, 100)",
       new="    self.lower_spin.setRange(0, hi)",
       test="test_the_display_range_keeps_every_digit_a_user_types",
       why="clamping one percent box by the other's current value "
           "makes the validator eat every digit past it, so from a "
           "window of (0, 40) typing 60 keeps 6 and the element is "
           "recoloured and stamped from a ramp window nobody asked "
           "for"),
  dict(name="the-landing-asks-the-live-row-not-the-snapshot",
       file="weavingspace_qgis/dialog.py",
       old="      live_mode = a.get(\"mode_raw\")\n"
           "      live_row = self._assignment_for(tid)\n"
           "      if live_row is not None:\n"
           "        live_mode = live_row.get(\"mode_raw\")",
       new="      live_mode = a.get(\"mode_raw\")",
       test="test_a_style_pasted_mid_run_survives_the_landing",
       why="deferral can begin WHILE a run is in flight, and the "
           "launch snapshot still names a style -- so the landing "
           "reads that as the user taking the element back and "
           "re-seeds over a style they pasted a moment earlier, with "
           "nothing said but the tile count"),
  dict(name="a-graduated-dock-edit-reaches-the-file",
       file="weavingspace_qgis/dialog.py",
       old="      if self._last_path:\n"
           "        bridge.embed_style(layer)\n"
           "      # A RETYPED BOUNDARY LANDS HERE, because moving a number moves",
       new="      return  # our own seeding, or an edit that changed no colour\n"
           "    if len(expected) != len(actual):",
       test="test_a_dock_edit_of_any_kind_reaches_the_exported_file",
       why="a COLOUR comparison cannot see a retyped break or an "
           "added stroke, so this guard returns before every embed "
           "exit and the GeoPackage a colleague opens carries the "
           "style from before the edit -- with Generate unable to "
           "heal it, since the row never moved"),
  dict(name="a-categorized-dock-edit-reaches-the-file",
       file="weavingspace_qgis/dialog.py",
       # RE-ANCHORED 2026-08-20: this exit now names itself in the
       # dump before returning, so the two lines are no longer
       # adjacent.
       old="      if self._last_path:\n"
           "        bridge.embed_style(layer)\n"
           "      _dump(\"DROP\", tile_id, \"clean-classify\")\n"
           "      return  # our own seeding, or an edit that changed no colour\n"
           "\n"
           "    # a clean classify from a standard ramp?",
       new="      return  # our own seeding, or an edit that changed no colour\n"
           "\n"
           "    # a clean classify from a standard ramp?",
       test="test_a_dock_edit_of_any_kind_reaches_the_exported_file",
       why="the categorized twin of the same guard, repaired hours "
           "later than the graduated one and only because a hunt went "
           "looking: a fill comparison cannot see a stroke, a legend "
           "label or a deleted category"),
  dict(name="the-vendor-gate-compares-the-commit",
       file="tools/sync_release_content.py",
       old="    if commit:\n"
           "      for claim in set(re.findall(r\"commit ([0-9a-f]{7,40})\", text)):",
       new="    if False:\n"
           "      for claim in set(re.findall(r\"commit ([0-9a-f]{7,40})\", text)):",
       test="test_the_documents_numbers_match_the_code",
       why="the stamp records a version AND a commit precisely because "
           "upstream does not always bump the version when the code "
           "moves, and this gate compared the version alone -- so two "
           "documents named a superseded commit for eight days while "
           "the checker whose docstring promises that comparison "
           "reported success every time"),
  dict(name="a-refusal-is-punctuated-by-the-locale", file=BRIDGE,
       old="  text = QLocale().toString(float(value), 'g', 6)",
       new="  text = f\"{float(value):.6g}\"",
       test="test_a_refusal_names_a_number_the_box_beside_it_accepts",
       why="a refusal is a stronger copy path than a report -- the "
           "number in it is the one a user must clear to get their "
           "map -- and a hard-coded decimal point beside a box that "
           "parses through the locale means the plugin says 7.16 "
           "where its own cell says 7,16, so retyping the refusal "
           "pins 716, which pin_problem then ACCEPTS"),
  dict(name="a-printed-bound-is-punctuated-by-the-locale",
       file="weavingspace_qgis/category_editor.py",
       old="    text = QLocale().toString(float(value), 'g', 10)",
       new="    text = f\"{float(value):.10g}\"",
       test="test_a_bound_the_editor_prints_can_be_typed_into_its_own_box",
       why="a hard-coded decimal point beside spin boxes that parse "
           "through QLocale means the cell prints 4.052 and typing it "
           "back pins 4052 -- accepted, drawn and stamped on the "
           "layer, so a user copying the plugin's own number gets a "
           "map a thousand times out and it survives a save"),
  dict(name="the-advised-spacing-is-punctuated-by-the-locale",
       file=BRIDGE,
       old="  text = QLocale().toString(float(value), 'f', places)",
       new="  text = f\"{value:,.{places}f}\"",
       test="test_the_spacing_advice_can_be_typed_back_in_any_locale",
       why="hand-built punctuation beside a spin box that parses "
           "through QLocale means the plugin advises 23.4 and the box "
           "takes 234, so a user who types what they are told draws a "
           "map ten times too coarse and is told nothing"),
  dict(name="the-spacing-advice-is-rounded-the-safe-way",
       file=BRIDGE,
       old="  return _rounded_up_to_figures(spacing * scale, 3)",
       new="  return spacing * scale",
       test="test_the_tile_estimate_is_honest_where_shapes_are_awkward",
       why="an unrounded suggestion is printed to three figures by the "
           "sentence instead, and printing rounds a FLOOR downward: "
           "1.2150048 was said as '1', which estimates 286,676 tiles "
           "against a cap of 200,000, so a user typing the plugin's own "
           "advice met the identical refusal"),
  dict(name="the-spacing-advice-keeps-its-magnitude",
       file="weavingspace_qgis/dialog.py",
       # RE-ANCHORED 2026-08-25: the refusal became a question whose
       # wording escalates by band, and the advice moved into it. The
       # claim is unchanged -- a spacing printed with no decimals says
       # "0" on a small region.
       old="          f\"A spacing of about {bridge.spacing_in_words(suggestion)} \"",
       new="          f\"A spacing of about {suggestion:,.0f} \"",
       # RE-AIMED 2026-08-25, and it should always have been aimed
       # here: the entry mutates what the DIALOG prints, and the test
       # it named asks `spacing_in_words` directly and never reads a
       # message at all, so it could not see the mutation and this
       # entry could only ever survive. The boundary test parses the
       # number out of the sentence the user is shown and requires it
       # to be a spacing that works, which is the claim.
       test="test_the_size_guard_at_its_refusal_boundary",
       why="printing a spacing with no decimal places says '0' for any "
           "region under about ninety map units across, which reads as "
           "'any spacing works' and is a number the spacing box's own "
           "1e-6 minimum cannot even hold"),
  dict(name="each-element-gets-its-own-legend-notice", file=DIALOG,
       old="      if note is not None and note not in said:\n"
           "        said.add(note)",
       new="      if note is not None and field not in said:\n"
           "        said.add(field)",
       test="test_every_element_is_told_about_its_own_legend",
       why="keying the dedup on the COLUMN was right while the notice "
           "was about a column and wrong the moment it became per "
           "element: one element reporting one empty class of five "
           "silences its neighbour drawing twenty with two empty, "
           "under a sentence quoting a class count that neighbour "
           "does not have"),
  dict(name="the-restyle-path-says-a-column-is-constant", file=DIALOG,
       old="      if region_values and bridge.numeric_values_are_constant(\n"
           "          region_values):\n"
           "        note = bridge.constant_field_message(field)\n"
           "      else:\n"
           "        note = self._legend_size_note(field, a, tid)",
       new="      note = self._legend_size_note(field, a, tid)",
       test="test_every_element_is_told_about_its_own_legend",
       why="a class-count change is symbology, so the restyle path is "
           "the one that MEETS a constant column -- and "
           "`_legend_size_note` returns None at one distinct value by "
           "design, so without this the spinner reads 8 over a map "
           "drawing one class and nothing whatever is said"),
  dict(name="unclassed-is-exempt-from-the-emptiness-notice", file=DIALOG,
       old="    if assignment.get(\"scheme\") == \"Unclassed\":\n"
           "      return None",
       new="    if False:\n      return None",
       test="test_an_unclassed_row_is_not_warned_about_its_fifty_steps",
       why="Unclassed is fifty linear intervals reproducing a "
           "CONTINUOUS ramp, so most of its steps hold no tile on any "
           "ordinary column -- that is what the style is. Without the "
           "exemption every such element is told a third of its "
           "classes are empty, on a map behaving exactly as designed, "
           "which is how a warning becomes one people ignore"),
  dict(name="emptiness-is-still-reported-in-words",
       file="weavingspace_qgis/dialog.py",
       old="    return bridge.empty_classes_message(field, len(unworn), asked)",
       new="    return explained",
       test="test_a_class_no_tile_wears_is_said_out_loud",
       why="falling back to the distinct-value sentence is exactly the "
           "state the swatch removal left behind: it fires on a "
           "condition that is neither necessary nor sufficient for a "
           "class going unworn, so a pin below the data draws four "
           "colours of five and the plugin says nothing at all"),
  dict(name="the-renderer-is-asked-which-classes-are-empty",
       file="weavingspace_qgis/dialog.py",
       old="    unworn = (self._classes_nothing_wears(tile_id, assignment)\n"
           "              if tile_id is not None else None)",
       new="    unworn = None",
       test="test_a_class_no_tile_wears_is_said_out_loud",
       why="never asking the renderer returns unworn_classes to having "
           "no caller, which is the defect itself: the measurement "
           "exists, is tested, and reaches nothing a user can see"),
  dict(name="a-bound-box-holds-what-the-guard-allows",
       file="weavingspace_qgis/category_editor.py",
       old="    box.setRange(-_WIDEST_BOUND, _WIDEST_BOUND)",
       new="    box.setRange(-magnitude * 100.0, magnitude * 100.0)",
       test="test_a_pin_may_be_typed_far_outside_the_element_it_pins",
       why="sizing the range from THIS element's own extremes silently "
           "truncates a bound set deliberately wider: on tiles reaching "
           "11, typing 1200 keeps 120, the map is drawn from 120 and "
           "pin_problem is never asked, because the number it would "
           "refuse never reaches it -- so two elements given one typed "
           "limit draw two different ladders, which is the opposite of "
           "what wide limits are for"),
  dict(name="the-decimals-are-measured-from-the-unpinned-ladder",
       file="weavingspace_qgis/category_editor.py",
       old="    measured = unpinned or edges",
       new="    measured = edges",
       test="test_a_far_pin_does_not_flatten_the_box_a_small_one_needs",
       why="since the outside-the-data refusal was lifted, the ladder "
           "as it stands may be dominated by a bound that is "
           "deliberately not data -- so a rates column pinned high at "
           "40 asks for eight decimals, and its own 6e-10 low bound "
           "reads back as ZERO the next time the table is rebuilt, "
           "moving nine of twenty features with nothing said"),
  dict(name="a-bound-box-can-hold-a-small-number-on-a-big-column",
       file="weavingspace_qgis/category_editor.py",
       old="    box.setDecimals(max(_LEAST_DECIMALS, min(12, places)))",
       new="    box.setDecimals(max(0, min(12, places)))",
       test="test_a_pin_may_be_typed_far_outside_the_element_it_pins",
       why="nine significant places below a span of 1e12 is negative, "
           "so the floor is all that stops the box clamping to zero "
           "decimals, where a typed bound of 0.5 is stored as 0 or 1 "
           "and the map is drawn from the rounded number"),
  # RETIRED 2026-08-17 with the swatch hatching: `the-swatch-is-
  # painted-after-the-restyle`, which mutated the order in
  # `_apply_style_change` and was caught by
  # test_a_copy_hatches_the_classes_it_leaves_unreachable. Both the
  # test and the behaviour are gone -- the swatch no longer asks any
  # layer which classes nothing wears, so the order it guarded no
  # longer decides anything. An entry left standing on either would
  # have matched nothing and reported nothing, which reads exactly
  # like success.
  dict(name="one-class-colouring-needs-one-class", file=BRIDGE,
       old="  if distinct == 1 and count == 1:",
       new="  if distinct == 1 and count:",
       test="test_a_copied_ladder_on_one_value_still_wears_its_ramp",
       why="a copied ladder puts several classes on a one-value "
           "column, and colouring index 0 alone leaves the rest on "
           "the placeholder grey set_class_bounds builds them with, "
           "so the element draws as no data while its cell names a "
           "ramp"),
  dict(name="unclassed-fifty-is-not-a-chosen-count", file=DIALOG,
       old="    if not unclassed_source:\n"
           "      self._class_counts[target_id] = len(classes)",
       new="    if True:\n"
           "      self._class_counts[target_id] = len(classes)",
       test="test_a_copy_from_unclassed_leaves_the_chosen_count_alone",
       why="`_class_counts` is the record that means CHOSEN, and "
           "Unclassed's fifty is fixed by the style; written there it "
           "is clamped to twenty at the next rebuild, replacing the "
           "count the user picked with no notice"),
  dict(name="a-pin-is-read-under-a-copied-ladder", file=BRIDGE,
       old="""  if low_pin is not None and copied:""",
       new="""  if False and copied:""",
       test="test_a_pin_still_works_on_a_copied_ladder",
       why="the record holds copied VALUES and pin FLAGS, and each "
           "worked alone -- so nothing noticed that together the pin "
           "did nothing: the button stayed down, the number was "
           "stamped, the map did not move, and the pin then fired "
           "later when the copy was released"),
  dict(name="a-copy-moves-the-controls-too", file=DIALOG,
       old="    self._sync_target_controls(\n      target_id,",
       new="    self._skip_target_controls(\n      target_id,",
       test="test_a_copy_leaves_one_number_in_every_control",
       why="`_assignments` reads the class count off the spinner, so "
           "writing the record without moving the widget leaves four "
           "descriptions of one setting and a fifth after a reopen"),
  dict(name="a-project-change-drops-the-last-project", file=DIALOG,
       old="    QgsProject.instance().cleared.connect("
           "self._forget_the_last_project)",
       new="    pass",
       test="test_a_new_project_does_not_inherit_the_last_one_s_pins",
       why="the dialog outlives the project and tile ids repeat across "
           "families, so without this a bound pinned in the project "
           "just closed lands on the project just opened, where the "
           "plugin itself refuses that number when typed"),
  dict(name="a-copied-pin-is-checked-against-its-new-data", file=DIALOG,
       old="""      if bridge.pin_problem(trial["low"], trial["high"], judged,
                            source.get("k", 5)):""",
       new="""      if False:""",
       test="test_a_copy_leaves_behind_a_pin_the_data_cannot_carry",
       why="every typed bound goes through pin_problem; the copy path "
           "is the only route by which one could arrive unexamined, "
           "and because a copy degrades to its pins that bound "
           "outlives the copy it came in on"),
  dict(name="the-reference-uses-the-colours-in-force",
       file="tools/visual_reference_report.py",
       old="  _register_recorded_colormaps()",
       new="  pass  # mutation: score against matplotlib's own colours",
       test="test_the_ramp_a_row_names_is_the_ramp_the_map_draws",
       why="without registering the recorded colours the comparison "
           "asserts the plugin's palettes ARE matplotlib's, which is "
           "false on every fresh QGIS and made the gate pass on one "
           "seeded profile alone"),
  dict(name="categorical-colour-is-decided-map-wide", file=BRIDGE,
       old="  n = max(len(everywhere), 1)",
       new="  n = max(len(values), 1)",
       test="test_one_colour_means_one_value_across_elements",
       why="the palette is sampled against the category COUNT, so "
           "taking it from the element rather than the map gives one "
           "colour two meanings the moment an element lacks a value"),
  dict(name="a-category-keeps-its-place-map-wide", file=BRIDGE,
       old="    i = positions.get(v, own_index)",
       new="    i = own_index",
       test="test_one_colour_means_one_value_across_elements",
       why="a value's colour comes from its position in the whole "
           "map's list; using its position in this element's list is "
           "the same defect by the other coordinate"),
  dict(name="the-classes-cell-reports-its-own-element", file=DIALOG,
       old="    drawn = QgsProject.instance().mapLayer(\n"
           "      self._element_layer_ids.get(tile_id, \"\")) if tile_id else None",
       new="    drawn = None",
       test="test_the_classes_cell_reports_its_own_element",
       why="the cell is a greyed REPORT, so reading the region makes "
           "it describe somebody else's element -- four rows showing "
           "6 while one of them draws 5"),
  dict(name="the-constant-notice-counts-the-region", file=DIALOG,
       old="          if bridge.numeric_values_are_constant(region_values):",
       new="          if bridge.numeric_values_are_constant(gdf[field]):",
       test="test_the_constant_notice_counts_the_users_areas",
       why="the renderer this sentence describes is seeded from the "
           "region's values, so counting the TILES makes it disagree "
           "with the legend beside it -- and saying it suppresses the "
           "true notice as well"),
  dict(name="a-copied-ladder-counts-its-own-classes", file=BRIDGE,
       old="  breaks = (pinned or {}).get(\"breaks\")\n"
           "  if breaks:\n    return len(breaks) + 1, False",
       new="  breaks = (pinned or {}).get(\"breaks\")\n"
           "  if False:\n    return len(breaks) + 1, False",
       test="test_a_copied_ladder_is_not_reported_as_a_reduction",
       why="a copy's unreachable classes are kept by design, so the "
           "column's distinct count describes nothing -- reporting it "
           "tells a user their map has fewer classes than it draws"),
  dict(name="the-reduction-sees-the-pinned-pool", file=BRIDGE,
       old="  if pins and wants_middle and not unclassed and not "
           "cuts_from_the_ends:",
       new="  if False:",
       test="test_a_pin_leaves_no_class_for_a_tile_to_miss",
       why="a pin removes a class from the ladder AND its samples from "
           "the pool, so without re-asking the reduction's question "
           "the scheme cuts more classes than the middle has values "
           "and the legend gains a swatch no tile wears"),
  dict(name="the-firing-control-is-the-one-that-is-read", file=EDITOR,
       old="      self._bound_edited(which, pair)",
       new="      self._bound_edited(which)",
       test="test_an_unclassed_row_pins_from_either_control",
       why="with an end already pinned, dropping the firing pair makes "
           "_bound_edited fall back to the FIRST registered control -- "
           "the clamp strip -- so the Pin column's box takes the first "
           "number a user types and silently discards every one after "
           "it, applying the strip's stale value to the map"),
  # RETIRED 2026-08-19, NOT RE-ANCHORED, because the behaviour it
  # guarded was deliberately reversed rather than moved. It required
  # an Unclassed row to carry a Pin COLUMN; the maintainer's
  # instruction that day removed the column from every style and gave
  # every end a floor and a ceiling instead. An entry re-anchored onto
  # code that no longer makes its claim would report `caught` about
  # nothing, which is worse than the silence check_standards catches.
  #
  # WHAT REPLACED IT, so the ground is not left bare: the same test
  # now requires an Unclassed end to be named by TWO LIMIT CONTROLS
  # that agree, which is the promise the column was serving, and
  # `an-unclassed-end-keeps-two-controls` below breaks that instead.
  dict(name="a-retyped-ladder-keeps-its-ends", file=DIALOG,
       old='    wanted["floor"] = float(bounds[0][0])',
       new='    wanted["floor"] = wanted.get("floor")',
       test="test_a_break_retyped_in_qgis_reaches_the_plugin",
       why="a ladder retyped in QGIS keeps the ends a person typed; "
           "without this they fall back to the column's own extremes, "
           "so 0 typed over a column starting at 3.1 comes back 3.1 "
           "and the legend describes numbers nobody chose"),
  dict(name="a-ladder-that-excludes-everything-is-not-adopted",
       file=DIALOG,
       old="      wanted.pop(\"floor\", None)\n"
           "      wanted.pop(\"ceiling\", None)",
       new="      pass  # mutation: adopt the ends regardless",
       test="test_a_qgis_symbology_edit_reaches_the_plugin_on_every_shape",
       why="a ladder retyped far from the data would otherwise have "
           "its ceiling adopted, excluding every value and leaving the "
           "element with no classes at all -- measured on a column of "
           "about 1e9 retyped to 0-80, five classes down to none"),
  dict(name="a-dock-edit-under-a-run-is-replayed", file=DIALOG,
       # RE-ANCHORED 2026-08-19: the capture gained a count guard, so
       # only a genuine retype is deferred and a reclassification --
       # which adoption refuses anyway -- is left to the signature
       # rule that already preserves it.
       old="        self._adoption_deferred[tile_id] = (\n"
           "          dict(assignment), list(bounds), list(colours))",
       new="        pass  # mutation: drop the edit instead of keeping it",
       test="test_a_qgis_symbology_edit_reaches_the_plugin_on_every_shape",
       why="a boundary retyped while a run is finishing must survive "
           "the landing; without this the rest conditions throw the "
           "edit away and the next re-seed writes the plugin's own "
           "ladder over what the user typed"),
  dict(name="an-adopted-ladder-moves-the-row-signature", file=DIALOG,
       # RE-ANCHORED 2026-08-19, hours after it was written, by the
       # commit that gave this exit the stamp its four siblings carry:
       # the anchor ran through the next `def`, and a `def` is exactly
       # what stops following a line when something is inserted above
       # it. Anchored on the CALL now, with the comment that follows
       # it for uniqueness, since the bare block is an idiom matching
       # in four places.
       old="""      self._last_signatures[tile_id] = self._signature(refreshed)
      # ...AND THE STAMP AND THE FILE, which this exit forgot, exactly""",
       new="""      pass  # mutation: leave the signature naming the old row
      # ...AND THE STAMP AND THE FILE, which this exit forgot, exactly""",
       test="test_a_dock_reclassification_lands_while_a_run_is_finishing",
       why="adopting a retyped ladder puts breaks, floor and ceiling "
           "into the record, which the signature carries -- so without "
           "this the next landing compares a row holding them against "
           "a signature recorded before they existed, reads the "
           "element as CHANGED and re-seeds it. Measured 2026-08-19: a "
           "twelve-class classify made in QGIS's dock while a run was "
           "landing came back as the plugin's five, because a "
           "five-class retype adopted a moment earlier had moved the "
           "row and told nothing"),
  dict(name="the-clearing-cross-can-be-clicked", file=WIDGETS,
       # ANCHORED ON THE EVENT FILTER, which is the only thing that
       # makes the mark reachable: `mousePressEvent` below it looks
       # like the handler and is never called for these pixels, since
       # the spin box's own QLineEdit covers them and takes the press.
       old="""      here = watched.mapTo(self, point)
      if self._clear_rect().adjusted(-3, -3, 3, 3).contains(here):
        self.cleared.emit()
        return True""",
       new="      pass  # mutation: let the line edit swallow the click",
       test="test_a_bound_can_be_given_back_from_every_control",
       why="the cross inside a bound box is the only way to give a "
           "bound back other than retyping the computed number, and "
           "without this the click reaches the line edit instead and "
           "merely drops a text cursor into the number. Measured "
           "2026-08-19: 0 of 8 controls clickable, classed and "
           "Unclassed, table and strip, on a mark drawn since the day "
           "it was written"),
  dict(name="equal-intervals-cut-from-a-limit", file=BRIDGE,
       # ANCHORED ON THE GATE, which is where the fault was: the span
       # chain inside the branch already knew about floors and
       # ceilings and said so, and nothing ever reached it.
       old="""  cuts_from_the_ends = bool(
    (pins or floor is not None or ceiling is not None)""",
       new="""  cuts_from_the_ends = bool(
    (pins)""",
       test="test_two_columns_with_one_pair_of_limits_draw_one_ladder",
       why="giving several variables one pair of limits is how a "
           "colour comes to mean the same number on every map, and is "
           "the reason floors and ceilings exist. Without the term "
           "each column is cut over its own data instead: two elements "
           "limited alike to 0-12 drew 0-1-2-3-4-12 and "
           "0-2.4-4.8-7.2-9.6-12, disagreeing everywhere between ends "
           "their legends agree on"),
  dict(name="icon-mode-says-whose-value-an-icon-carries", file=DIALOG,
       old="""        note = (bridge.icon_misattribution_message
                if icons_at_launch else bridge.coverage_message)(""",
       new="""        note = (bridge.coverage_message
                if True else bridge.coverage_message)(""",
       test="test_icon_mode_says_whose_value_an_icon_carries",
       why="the count asks whose VALUE reached a tile, which in "
           "ordinary tiling coincides with appearing on the map and in "
           "ICON MODE does not: one unit goes on each area, so an icon "
           "IS drawn and the area is wearing a neighbour's number. Told "
           "four areas are missing, a reader goes looking for holes, "
           "finds none, and learns to distrust the warning, while what "
           "is in front of them is a wrong map that looks right"),
  dict(name="a-pin-is-judged-against-the-pool-the-map-uses", file=DIALOG,
       # ANCHORED ON THE NARROWING, which is the whole of the fix: the
       # judge and the call were both there already and were being
       # asked about the wrong values.
       old="""    judged = [v for v in values
              if bridge.absence_kind(v, record.get("floor"),
                                     record.get("ceiling"))
              != bridge.OUTSIDE_RANGE_KEY]""",
       new="    judged = list(values)",
       test="test_a_limit_that_refuses_a_pin_retires_the_pin_and_says_so",
       why="a floor or ceiling narrows what the scheme classifies and "
           "bridge judges the pin against THAT pool, so a pin the "
           "narrowed pool cannot carry is dropped there. Asked the "
           "un-narrowed question this site answers 'fine' and says "
           "nothing, and the record, the layer stamp and the saved "
           "project all go on claiming a pin the map does not draw -- "
           "which a reopen restores"),
  dict(name="a-picked-style-is-not-put-back-to-deferring", file=DIALOG,
       # ANCHORED ON THE GUARD, which is the whole fix: the refresh
       # itself is right and was simply asking the layer a question
       # only the row can answer during the reclaim. RE-ANCHORED
       # 2026-08-19 when the guard stopped reading `style_touched`,
       # a flag that is true for the rest of the session, and started
       # reading `_picked_back`, which empties as soon as the layer
       # agrees.
       old="""      if deferring and combo.currentText() != self.DEFERRING \\
          and not picked:""",
       new="""      if deferring and combo.currentText() != self.DEFERRING:""",
       test="test_integration_interleaved_session",
       why="picking a plugin style is how somebody takes an element "
           "back from QGIS, and the layer still holds the dock's "
           "renderer at that moment because the re-seed has not "
           "happened yet. Without the guard `_element_is_deferring` "
           "answers True and the row is put back to 'Deferring to "
           "QGIS' with signals blocked, after which every path "
           "downstream correctly preserves the dock's renderer over "
           "the user's choice -- the element cannot be taken back at "
           "all"),
  dict(name="a-reclaim-is-recorded-not-inferred", file=DIALOG,
       # THE WRITER, anchored apart from the reader above, because the
       # pair is enforced by nothing but attention: one anchor covering
       # both would survive whatever the tests do.
       old="""    taken_back = mode_combo.property("tile_id")
    if taken_back and self._element_is_deferring(taken_back):
      self._picked_back.add(taken_back)""",
       new="    pass  # mutation: infer the reclaim instead",
       test="test_integration_interleaved_session",
       why="nothing about the pair 'the row names a style, the layer "
           "holds something unnameable' says which of the two moved "
           "last, and that is the only question. Unrecorded, the "
           "reclaim is indistinguishable from a paste in the styling "
           "panel, so the refresh puts the row straight back to "
           "'Deferring to QGIS' and an element styled in QGIS can "
           "never be taken back"),
  dict(name="a-dock-edit-outranks-an-earlier-pick", file=DIALOG,
       old="""    if not self._applying_style \\
        and self._element_layer_ids.get(tile_id) == layer_id:
      self._picked_back.discard(tile_id)""",
       new="    pass  # mutation: let the older pick stand",
       test="test_a_style_picked_by_hand_still_follows_a_paste_in_qgis",
       why="a claim on an element must die the moment the person says "
           "something newer in QGIS. Left standing, a row whose style "
           "had ever been picked by hand goes on naming that style "
           "over a rule-based map, with every renderer control live, "
           "and the next Generate reclaims the element and paints "
           "over the work somebody did in the styling panel"),
  dict(name="a-count-from-qgis-releases-a-copy", file=DIALOG,
       old='        self._release_copied_breaks(tile_id, "a new class count")',
       new="        pass  # mutation: keep the copied ladder",
       test="test_a_count_set_in_qgis_releases_a_copied_ladder",
       why="a copy degrades to its pins when the class count changes, "
           "and both table doors into `_class_counts` say so. This is "
           "the door QGIS opens: without it a count set in the "
           "Symbology panel is accepted and announced, and then "
           "silently undone, because the renderer builder "
           "short-circuits on the copied breaks and draws the copy's "
           "classes while the spinner reads the new number"),
  dict(name="limits-are-re-asked-when-the-data-moves", file=DIALOG,
       # ANCHORED ON THE TEST, not on the drop beneath it: what was
       # missing is that the question is asked AT ALL on this path.
       old="""    if limits and bridge.limits_leave_nothing(
        values, record.get("floor"), record.get("ceiling")):""",
       new="    if False:",
       test="test_limits_the_data_moved_out_from_under_are_dropped",
       why="pin flags have a data-moved guard and edge values had "
           "none, because this method returned before looking whenever "
           "low and high were both absent -- which is exactly the "
           "record an adopted ladder writes. A ladder retyped in QGIS "
           "and then met by an edit to that column put every area onto "
           "the paired layer as 'outside the range', drew the element "
           "flat in silence, and Generate could not heal it"),
  dict(name="an-adopted-ladder-keeps-a-pin-it-still-carries", file=DIALOG,
       # ANCHORED ON THE LOOP that decides, not on the comparison
       # inside it: what is at stake is that a surviving pin is kept
       # at all, which is the behaviour that was missing.
       old="""    for end in ("low", "high"):
      here = wanted.get(end)
      if here is None:
        continue
      if not any(abs(round(float(here), 6) - edge) < 1e-6
                 for edge in edges):
        wanted.pop(end, None)""",
       new="""    wanted.pop("low", None)
    wanted.pop("high", None)""",
       test="test_a_pin_survives_a_dock_edit_to_another_boundary",
       why="a pin is a person saying this break is mine, and adopting "
           "a ladder that still runs through it says nothing about "
           "their having changed their mind. Dropping both ends "
           "unconditionally demoted a pin whenever ANY other boundary "
           "was retyped in QGIS -- silently, and then destructively at "
           "the next class count change, which found nothing left to "
           "degrade to and blamed a copy that never happened"),
  dict(name="a-limit-edit-is-announced-either-way", file=DIALOG,
       # ANCHORED ON THE GATE that decides whether anything is said,
       # not on either sentence: what is at stake is that the question
       # asked here is the SAME one `_restyle_only` asks, and mutating
       # a sentence would prove the wording instead.
       old='      if which in ("floor", "ceiling") and not self.live_check.isChecked():',
       new='      if which in ("floor", "ceiling") and value is not None \\\n          and not self.live_check.isChecked() \\\n          and self._limits_exclude_anything(\\\n            self._assignment_for(tile_id) or {}):',
       test="test_a_limit_edit_that_draws_nothing_new_still_says_so",
       why="`_restyle_only` refuses EVERY limit edit, since the "
           "geometry signature carries the floor and ceiling as "
           "values, so with live update off the map does not move "
           "until the next Generate. Asked the narrower question -- "
           "do the limits currently exclude anything -- the plugin "
           "said nothing for every edit that stops excluding: a floor "
           "set wide of the data, or lowered, or given back, changed "
           "nothing and announced nothing, which reads exactly like "
           "the control not working"),
  dict(name="a-copy-that-carries-a-range-is-still-stamped", file=DIALOG,
       old="    self._stamp_what_was_copied(taken)",
       new="    pass  # mutation: leave the stamp to the restyle",
       test="test_a_copy_carries_the_range_and_refuses_what_it_would_empty",
       why="a limit is a GEOMETRY change, so once a copy carries the "
           "range `_restyle_only` correctly declines the element -- "
           "and the restyle is what writes the stamp. Measured "
           "2026-08-19: a copy of breaks alone came back stamped and "
           "the identical copy carrying a floor and ceiling stamped "
           "nothing, so the copy reached the map and died at the next "
           "reopen. Nothing on a renderer records that a break was "
           "CHOSEN rather than computed, so the stamp is all a "
           "reopened project has"),
  dict(name="the-size-guard-measures-ground", file=BRIDGE,
       old="""    ground, edge = covered_area, covered_edge or 0.0""",
       new="""    ground, edge = w * h, 2 * (w + h)""",
       test="test_the_size_guard_measures_ground_not_the_bounding_box",
       why="ignoring what the caller measured puts the estimate back "
           "on the bounding rectangle, which knows nothing of a "
           "region strung thinly across it. On a maintainer's own "
           "data -- 3,011 areas filling 11.8% of the circle enclosing "
           "them -- that estimated 585,765 tiles against 70,659 "
           "drawn and REFUSED a map the library renders in five "
           "seconds, so the user could not make it at all"),
  dict(name="the-border-is-the-dissolved-edge", file=BRIDGE,
       old="""    united = region_gdf.union_all()
    return float(united.area), float(united.length)""",
       new="""    return float(region_gdf.area.sum()), float(region_gdf.length.sum())""",
       test="test_the_size_guard_measures_ground_not_the_bounding_box",
       why="a region arrives as ROWS, and rows are how somebody cut "
           "the data rather than a fact about the ground: summing "
           "each polygon's perimeter counts every shared internal "
           "edge twice. Measured at 6.25x what the library draws on "
           "adjacent cells, which refuses maps outright, against "
           "1.28x for the dissolved boundary"),
  dict(name="the-value-cache-keeps-every-column", file=DIALOG,
       old="""      self._values_cache = {
        older: cached for older, cached in self._values_cache.items()
        if older[0] == key[0] and older[2:] == key[2:]}
      self._values_cache[key] = bridge.classification_source(
        field_name, values)""",
       new="""      self._values_cache = {
        key: bridge.classification_source(field_name, values)}""",
       test="test_every_column_is_scanned_once_not_once_per_element",
       why="replacing the dict evicts every OTHER column's entry, so "
           "elements carrying different columns each rescan the whole "
           "layer on every tick. Measured on the reporter's own data, "
           "3,011 polygons and 23 columns: 46 scans per keystroke, "
           "1,041,176 calls and 3.5 seconds of CPU against 119,352 "
           "and 172 ms at 0.24.2, and one Generate at 62.7 seconds "
           "against 2.5. It is the mutation that RESTORES the defect, "
           "which is why the entry reads as it does"),
  dict(name="a-copy-carries-the-range-it-was-given", file=DIALOG,
       # ANCHORED ON THE CARRY, not on the refusal beside it: the
       # refusal is a separate claim with a separate entry below, and
       # one anchor covering both would report caught whichever of the
       # two the test actually noticed.
       old="""    for edge in ("floor", "ceiling"):
      if source_record.get(edge) is not None:
        record[edge] = float(source_record[edge])""",
       new="""    for edge in ():
      if source_record.get(edge) is not None:
        record[edge] = float(source_record[edge])""",
       test="test_a_copy_carries_the_range_and_refuses_what_it_would_empty",
       why="a copy claims to reproduce a classification, and since "
           "floors and ceilings arrived the ladder's outer edges are "
           "part of one. Without this loop the copy leaves the "
           "source's range behind AND destroys the target's, so the "
           "one thing the range feature was asked for -- giving one "
           "pair of limits to several variables, which is how a "
           "colour comes to mean the same number on every map -- "
           "cannot be done by the control built for it"),
  dict(name="a-copy-refuses-a-target-the-range-empties", file=DIALOG,
       old="    if bridge.limits_leave_nothing(target_values, floor, ceiling):",
       new="    if False and bridge.limits_leave_nothing("
           "target_values, floor, ceiling):",
       test="test_a_copy_carries_the_range_and_refuses_what_it_would_empty",
       why="a range that leaves a receiving column no drawable value "
           "at all gives that element NO CLASSES: it draws flat, and "
           "no control on its row names the number that did it. It is "
           "the one thing a limit must never be allowed to do, and it "
           "is the only ground on which a copy refuses a target -- an "
           "out-of-data limit draws perfectly well and is the point"),
  dict(name="a-copy-judges-a-pin-by-the-narrowed-pool", file=DIALOG,
       # THE THIRD DOOR onto the ruling of 2026-08-19. Rows 13 brought
       # two sites into step; carrying limits through a copy opened
       # another, so this anchors the narrowing that keeps all three
       # asking the judge one question.
       old="""    judged = [value for value in target_values
              if bridge.absence_kind(value, record.get("floor"),
                                     record.get("ceiling"))
              != bridge.OUTSIDE_RANGE_KEY]""",
       new="    judged = list(target_values)",
       test="test_a_copy_carries_the_range_and_refuses_what_it_would_empty",
       why="a pin is judged against the pool the map is actually cut "
           "from, narrowed by the floor and ceiling, never the whole "
           "column (maintainer's ruling, ledger row 13). Asking the "
           "un-narrowed question here accepts a pin the map does not "
           "draw, which the record and the layer stamp then claim and "
           "the next retirement pass drops without a word"),
  dict(name="a-partial-copy-names-what-it-left-out", file=DIALOG,
       old="""    for why, ids in grouped.items():
      singular, plural = why
      parts.append(f"{self._name_them(ids)} "
                   f"{singular if len(ids) == 1 else plural}")""",
       new="""    for why, ids in grouped.items():
      singular, plural = why""",
       test="test_a_copy_carries_the_range_and_refuses_what_it_would_empty",
       why="a partial success reported as a success is the shape this "
           "project keeps meeting, and with several targets it is "
           "reachable in one press: without this the notice names the "
           "elements that took the copy and says nothing whatever "
           "about the ones that could not, so a user reads a plain "
           "success over a map where two elements never changed"),
  dict(name="a-limit-keeps-its-ramp-colours", file=BRIDGE,
       # ANCHORED ON THE GATE, not on the recolour it guards: the
       # recolour was always right and was simply never reached with a
       # limit in force. Mutating inside it would prove the arithmetic
       # while leaving the actual defect -- nothing recoloured at all
       # -- unguarded.
       old="  elif ((lo, hi) != (0, 100) or pins or limits) and count:",
       new="  elif ((lo, hi) != (0, 100) or pins) and count:",
       test="test_a_limit_keeps_the_colours_the_ramp_gives",
       why="setting a limit rebuilds the ladder through "
           "set_class_bounds, which builds every class with a "
           "placeholder grey, and this recolour is the only thing "
           "that ever gives them ramp colours. Without the term the "
           "whole element drew #c0c0c0 -- five Reds classes became "
           "five identical greys on a floor that excluded nothing "
           "whatever, and on a map of areas that reads as no data"),
  dict(name="a-moved-limit-moves-the-signature", file=DIALOG,
       # RE-ANCHORED 2026-08-25: the term gained the element's own
       # variable, because trimming made a PERMUTATION a geometry
       # change and a set could not see one. The claim is unchanged.
       old="""      tuple((a["id"], a.get("var"), self._needs_a_no_data_split(a),
             self._limits_key(a))
            for a in self._assignments()),""",
       new="""      tuple((a["id"], a.get("var"), self._needs_a_no_data_split(a))
            for a in self._assignments()),""",
       test="test_a_moved_limit_re_splits_the_tiles",
       why="a limit is a geometry change, and the split predicate "
           "answers yes for a floor of 1 and a floor of 2.5 alike. "
           "Without the values the signature never moves, the restyle "
           "path takes the change, and it can neither make nor unmake "
           "a split -- so the areas a raised floor newly excludes stay "
           "on the element layer with no class to place them and draw "
           "as holes, while the notice says to press Generate"),
  dict(name="an-adopted-ladder-is-stamped", file=DIALOG,
       old="""      layer_now = QgsProject.instance().mapLayer(
        self._element_layer_ids.get(tile_id) or "")
      if layer_now is not None:
        self._stamp_category_colours(layer_now, refreshed)
        if self._last_path:
          bridge.embed_style(layer_now)""",
       new="      pass  # mutation: adopt without stamping",
       test="test_an_adopted_ladder_is_stamped_for_a_reopen",
       why="nothing on a renderer records that a break was CHOSEN "
           "rather than computed, so this stamp is all a reopened "
           "project has. The signature recorded three lines above -- "
           "which is what stops the landing clobbering the ladder -- "
           "also makes _restyle_only skip the element, so without the "
           "stamp a Generate cannot heal what a reopen has lost"),
  dict(name="icon-mode-counts-its-icons", file=DIALOG,
       old="""    if as_icons:
      est = bridge.estimate_icon_count(self._unit, len(region))
    else:
      est = bridge.estimate_tile_count(self._unit, region)""",
       new="    est = bridge.estimate_tile_count(self._unit, region)",
       test="test_icon_mode_is_not_counted_as_a_tiling",
       why="the tiling estimate mirrors the library's grid and scales "
           "with 1/spacing squared, while icon mode puts ONE unit on "
           "each area and the spacing only decides how big it is "
           "drawn. Asked the wrong question the guard answered 208,521 "
           "for a design that draws 100, refused the run outright, and "
           "advised a larger spacing, which would have drawn bigger "
           "icons rather than fewer of them"),
  dict(name="a-limit-narrows-what-is-classified", file=BRIDGE,
       old='      clause += f\' AND "{field}" >= {float(floor):.17g}\'',
       new="      pass  # mutation: classify past the floor",
       test="test_a_qgis_symbology_edit_reaches_the_plugin_on_every_shape",
       why="a floor must narrow the pool the scheme cuts from, or the "
           "ladder is computed over values the map no longer draws -- "
           "a legend describing areas that have left for the paired "
           "layer"),
  dict(name="an-unclassed-end-keeps-two-controls", file=EDITOR,
       old="          if self._pins_offered:",
       new="          if self._pins_offered and not self._locked:",
       test="test_an_unclassed_row_pins_from_either_control",
       why="without it an Unclassed row loses the editable bound in "
           "its own table and is left with the clamp strip alone -- "
           "which is what was reported as 'pins do not work on "
           "unclassed', a user who learned the control in one place "
           "meeting fifty rows that do not offer it"),
  dict(name="a-pin-click-moves-the-other-control", file=EDITOR,
       old="    # the ladder the map now draws, so the window and the "
           "map agree\n    self._redraw_bounds(answer)\n"
           "    self._sync_pin_controls(which, pair)",
       new="    # the ladder the map now draws, so the window and the "
           "map agree\n    self._redraw_bounds(answer)",
       test="test_an_unclassed_row_pins_from_either_control",
       why="an Unclassed end is named by TWO controls, so clicking "
           "the table's pin must light the strip's; without this the "
           "strip goes on reading unpinned over a map that is pinned, "
           "and clicking it applies a number the map left behind"),
  dict(name="a-typed-bound-moves-the-other-control", file=EDITOR,
       old="    # every break between the pins has just moved, so the "
           "rest of the\n    # window must say so too\n"
           "    self._redraw_bounds(answer)\n"
           "    self._sync_pin_controls(which, pair)",
       new="    # every break between the pins has just moved, so the "
           "rest of the\n    # window must say so too\n"
           "    self._redraw_bounds(answer)",
       test="test_an_unclassed_row_pins_from_either_control",
       why="the twin of the entry above, anchored separately because "
           "one anchor covering both would survive whatever the tests "
           "do: typing a bound in the strip must move the table's box "
           "and pin, or the two describe different maps"),
  dict(name="the-ramp-starts-where-the-map-does", file=BRIDGE,
       old="    drawable = last - first + 1",
       new="    first, last, drawable = 0, count - 1, count",
       test="test_the_ramp_spans_the_classes_a_tile_can_wear",
       why="a pin outside the column leaves its outermost class with "
           "zero width, and spreading the ramp across those spends "
           "the palest and darkest shades on classes no tile can wear "
           "-- the map then draws from the middle of the ramp and a "
           "reader comparing two of them cannot tell"),
  dict(name="equal-intervals-are-cut-from-the-pin", file=BRIDGE,
       old="  if cuts_from_the_ends and copied is None:",
       new="  if False:",
       test="test_equal_intervals_stay_equal_under_a_pin",
       why="without it the scheme cuts from the samples between the "
           "pins and the outermost class is stretched out to reach "
           "the pin, so the classes are not equal and two variables "
           "given the same limits draw different ladders -- which is "
           "the whole reason for giving them the same limits"),
  dict(name="the-reduction-lets-a-pinned-span-alone", file=BRIDGE,
       # RE-ANCHORED 2026-08-19, with its two neighbours: the flag was
       # renamed `cuts_from_the_ends` when a LIMIT was allowed to open
       # it, the old name having stopped being true of what it decides.
       old="  if pins and wants_middle and not unclassed and not "
           "cuts_from_the_ends:",
       new="  if pins and wants_middle and not unclassed:",
       test="test_equal_intervals_stay_equal_under_a_pin",
       why="cut from the pins, three classes over -5..40 are the same "
           "three whatever the column holds, so reducing k to the "
           "middle's distinct count gives a sparse column a different "
           "ladder from a full one under identical limits"),
  dict(name="the-map-is-seeded-with-its-pins", file=BRIDGE,
       old="""      assignment.get("quant_colours"), classify_from,
      assignment.get("pinned")))""",
       new="""      assignment.get("quant_colours"), classify_from, None))""",
       test="test_a_pinned_element_draws_what_the_library_draws",
       why="the pin reaches the map through seed_renderer, and without "
           "it the element draws the scheme's own breaks while the "
           "table, the swatch and the editor all say otherwise -- "
           "caught in PIXELS here, against the library's own render"),
  dict(name="a-pin-decides-its-own-break", file=BRIDGE,
       old="  if pins and copied is None:\n    # THE LADDER'S OUTER EDGE",
       new="  if False:\n    # THE LADDER'S OUTER EDGE",
       test="test_a_pinned_class_bound_reaches_the_map",
       why="a bound set by hand must be the bound the map draws; "
           "without this the samples are filtered out of the "
           "classification and the pinned classes are never put back, "
           "so the row draws fewer classes than it asked for and none "
           "of them where the user said"),
  dict(name="the-ladder-snaps-to-the-pin", file=BRIDGE,
       old="      middle[0] = (float(low), middle[0][1])",
       new="      middle[0] = middle[0]  # mutation: leave the gap",
       test="test_a_pinned_class_bound_reaches_the_map",
       why="a pin at 10 over data that resumes at 14 leaves 10 to 14 "
           "in no class at all, so a value arriving there later paints "
           "as no data on a map that looks perfectly fine"),
  # THE CLASS COUNT NEVER DESTROYS A PIN (maintainer's ruling,
  # 2026-08-17). Three entries because the rule is kept in three
  # places -- the control that refuses, the guard that must not
  # retire, and the keyboard tracking the refusal makes necessary --
  # and one anchor over any of them would report `caught` with the
  # other two axes dead.
  dict(name="a-class-count-refuses-instead-of-retiring", file=DIALOG,
       old="          refusal = self._class_count_refused(tid_here, v) \\\n"
           "              if tid_here else None",
       new="          refusal = None",
       test="test_a_class_count_is_refused_rather_than_destroying_a_pin",
       why="the spinner accepts a count too small to carry the row's "
           "pins, so the retirement guard pops the whole record and "
           "the layer's stamp with it -- and tells the user their "
           "data has changed when the only thing that moved is the "
           "control they are holding"),
  # REPLACED 2026-08-17, hours after it was written. The entry it
  # supersedes mutated a re-ask in `_retire_an_undrawable_pin` that
  # suppressed retirement on EVERY route while only the Classes
  # spinner had been given a refusal -- so a count arriving by any
  # other door left the record claiming bounds the map was not
  # drawing, silently. The doors are guarded at the doors now, and
  # this is the second one.
  dict(name="a-restored-count-is-raised-to-fit-the-pins", file=DIALOG,
       old="      if carried and int(k_spin.property(\"user_k\")) - 1 "
           "< carried:",
       new="      if False:",
       test="test_a_class_count_is_refused_rather_than_destroying_a_pin",
       why="a count remembered from before the pins comes back through "
           "_sync_row with signals blocked, so the spinner's refusal "
           "never runs -- an excursion through Unclassed and back then "
           "leaves two pins on a two-class ladder, and the row, the "
           "colour editor and the saved project all claim bounds of 10 "
           "and 60 over a map drawing 0/21/121"),
  dict(name="the-classes-spinner-does-not-eat-a-keystroke", file=DIALOG,
       old="      k_spin.setKeyboardTracking(False)",
       new="      k_spin.setKeyboardTracking(True)",
       test="test_a_class_count_is_refused_rather_than_destroying_a_pin",
       why="the handler writes back to its own box, so a spinner asked "
           "one keystroke at a time refuses the leading digit of 20 on "
           "a doubly-pinned row and reverts the box under the person "
           "typing -- the defect the refusal itself created, and "
           "invisible to setValue"),
  # RE-ANCHORED 2026-08-17, when the count rule moved out of
  # `pin_problem` into `pin_count_problem` so that the Classes spinner
  # could tell this refusal apart from the ones about the DATA. The
  # standards check caught the orphan on the first run after the move,
  # which is what it is for: an entry whose text has gone mutates
  # nothing and reports nothing, and a clean exit reads exactly like
  # success.
  dict(name="a-pin-outranks-the-one-value-collapse", file=BRIDGE,
       old="  if distinct == 1 and not pinned_here:",
       new="  if distinct == 1:",
       test="test_a_pin_outranks_the_one_value_collapse",
       why="a pinned bound on a column holding one value is accepted, "
           "stamped and silently ignored, while the identical bounds "
           "arriving as a copied classification draw five classes -- "
           "two settled rules giving opposite answers according to "
           "which control the user reached for"),
  # THE TAIL OF `_restyle_only`, two defects three lines apart and both
  # about ORDER. One test drives both; two entries, because a single
  # anchor over the block would report `caught` with one axis dead.
  # TWO QUESTIONS THE RETIREMENT GUARD MUST NOT BE ASKED, both of them
  # destroying work rather than crashing. One test drives both.
  dict(name="a-copy-is-not-judged-against-its-new-column", file=DIALOG,
       old="    if record.get(\"breaks\"):\n      return None",
       new="    if False:\n      return None",
       test="test_the_retirement_guard_is_asked_the_right_question",
       why="a copy is a claim about the LADDER and not about what the "
           "receiving values support, which is the carve-out "
           "make_graduated_renderer has carried since copying arrived "
           "-- without it the whole record is popped, copied breaks "
           "included, at the instant of copying, and the copy reports "
           "success"),
  dict(name="the-guard-is-asked-with-the-live-row", file=DIALOG,
       old="    live = self._assignment_for(tile_id)\n"
           "    if live is not None and live.get(\"var\") == field:\n"
           "      assignment = live",
       new="    live = self._assignment_for(tile_id)",
       test="test_the_retirement_guard_is_asked_the_right_question",
       why="two of the three callers hand in the LAUNCH SNAPSHOT, so "
           "pins the editor accepted against the live class count are "
           "retired the instant the run lands -- the record cleared, "
           "the stamp REMOVED so a reopen cannot recover them, and the "
           "sentence blaming the user's data"),
  dict(name="the-restyle-restamps-after-retiring", file=DIALOG,
       old="        if layer_now is not None:\n"
           "          fresh = self._assignment_for(tid)\n"
           "          self._stamp_category_colours(layer_now, fresh or a)\n"
           "          if self._last_path:\n"
           "            bridge.embed_style(layer_now)",
       new="        if layer_now is not None:\n"
           "          pass  # mutation: the retired number stays stamped",
       test="test_a_retired_pin_leaves_neither_a_stamp_nor_a_silent_neighbour",
       why="this path stamps BEFORE it retires, where its twin retires "
           "first and says at that line why -- so the user is told the "
           "bound has been recalculated while the retired number goes "
           "onto the layer anyway, and reopening the saved project "
           "restores a pin the row shows and the map ignores"),
  dict(name="every-element-is-asked-about-its-own-pin", file=DIALOG,
       old="      retired = self._retire_an_undrawable_pin(field, a)",
       new="      retired = (None if field in said\n"
           "                 else self._retire_an_undrawable_pin(field, a))\n"
           "      said.add(field)",
       test="test_a_retired_pin_leaves_neither_a_stamp_nor_a_silent_neighbour",
       why="the dedup set is about a per-COLUMN legend notice and the "
           "retirement is per ELEMENT, so sharing it means an element's "
           "dead pin is retired or kept according to what a different "
           "element carrying the same column happened to trigger -- the "
           "same act, opposite answers, decided by something no user "
           "can see"),
  dict(name="an-undrawable-pin-is-refused", file=BRIDGE,
       old="  available = int(asked) - 1\n  if available >= pins:\n"
           "    return None",
       new="  available = int(asked) - 1\n  if True:\n    return None",
       test="test_a_pin_that_cannot_be_drawn_is_refused",
       why="a k-class ladder has k-1 boundaries, so two pins on a "
           "two-class row name two boundaries where there is one and "
           "the pinned classes do not meet: measured, that draws 0-10 "
           "beside 60-121 with everything between in no class"),
  dict(name="pins-are-stamped-on-the-layer", file=DIALOG,
       old="""                    "pinned": {
                      key: ([float(x) for x in value]
                            if isinstance(value, (list, tuple))
                            else float(value))
                      for key, value in pinned.items()},""",
       new="""                    "pinned": {},""",
       test="test_a_pin_survives_a_project_round_trip",
       why="nothing on a renderer records that a break was chosen "
           "rather than computed, so an unstamped pin is lost on "
           "reopening and the next Generate recomputes over it"),
  dict(name="the-follow-compares-in-the-rows-own-direction", file=DIALOG,
       old="        assignment.get(\"k\", 5), assignment.get(\"outline\", False),\n"
           "        reverse=assignment.get(\"reverse\", False),\n"
           "        classify_from=self._classification_values(assignment[\"var\"]))",
       new="        assignment.get(\"k\", 5), assignment.get(\"outline\", False),\n"
           "        classify_from=self._classification_values(assignment[\"var\"]))",
       test="test_a_forward_ramp_does_not_match_a_reversed_row",
       why="the trial renderer is what decides whether a dock edit "
           "changed anything, so built without the row's tick a "
           "REVERSED row compares itself against the FORWARD ramp -- a "
           "genuine forward ramp set in QGIS matches, the plugin sees "
           "no change, the row goes on claiming reversed, and the next "
           "unrelated edit redraws the element end for end in the "
           "project and in the exported file"),
  dict(name="a-reversed-ramp-is-recognised", file=DIALOG,
       old="""    for flipped in (False, True):""",
       new="""    for flipped in (False,):  # mutation: a reversed ramp names nothing""",
       test="test_a_project_round_trip_changes_nothing_a_user_chose",
       why="reversing produces a ramp clone matching no name in the "
           "library, so without the reversed pass a reopened project "
           "brings the element back as Custom picks: the map is right "
           "and the tick the user set is gone"),
  dict(name="the-label-answers-for-every-row", file=EDITOR,
       old="""    for key, _stored, label, _fill in bridge.ABSENCE_KINDS:
      if value == key:
        return label
    return str(value)""",
       new="""    for key, _stored, label, _fill in bridge.ABSENCE_KINDS:
      if value == key:
        return label
    return "no data"  # mutation: the dead twin's fallback, back again""",
       test="test_the_editor_lists_every_value_and_the_no_data_row",
       why="_label_for answers for EVERY categorical row, not only the "
           "absence rows: a fixed fallback labels forest, water and "
           "urban alike as no data, which is exactly what shipped for "
           "a few hours on 2026-08-16 when a second definition of the "
           "method silently replaced the first"),
  dict(name="a-swatch-is-not-redrawn-per-appearance", file=DIALOG,
       old="""  cached = _RAMP_ICON_CACHE.get(key)""",
       new="""  cached = None  # mutation: every lookup misses""",
       test="test_a_ramp_swatch_is_drawn_once_and_follows_the_library",
       why="a table rebuild wants ~240 swatches and each was redrawn "
           "on the GUI thread every time: 306,558 draws and 2.45M "
           "fillRect calls in one test, three-quarters of the cost "
           "that pushed every CI suite leg past its 600s stall "
           "ceiling on 2026-08-16"),
  dict(name="the-swatch-cache-hears-the-style-library", file=DIALOG,
       old="""      if signal is not None:
        signal.connect(_forget_ramp_icons)""",
       new="""      if signal is not None:
        pass  # mutation: the cache goes deaf""",
       test="test_a_ramp_swatch_is_drawn_once_and_follows_the_library",
       why="economy without invalidation is a STALE swatch: a ramp "
           "removed or renamed in the Style Manager keeps its old "
           "picture forever, silently, since nothing else redraws it"),
  dict(name="a-typed-spacing-outlives-a-change-of-dataset", file=DIALOG,
       old="""      if not self._spacing_is_mine:
        self._auto_spacing()""",
       new="""      if True:  # mutation: derive over the user's own number
        self._auto_spacing()""",
       test="test_a_spacing_a_person_typed_outlives_a_change_of_dataset",
       why="this is the whole of the maintainer's ruling of "
           "2026-08-25: without the guard a spacing somebody typed is "
           "replaced by the auto-derived one the moment they choose "
           "another dataset, which a probe measured as 137 typed and "
           "500 on return, with nothing said"),
  # A THIRD ENTRY STOOD HERE AND WAS DELETED ON 2026-08-25, with the
  # code it guarded. `the-plugins-own-spacing-is-not-somebodys-choice`
  # mutated a `_deriving_spacing` flag that stopped `_spacing_typed`
  # claiming the plugin's own `setValue` -- and it SURVIVED, because
  # `_auto_spacing` clears ownership on the line after the write
  # regardless. Two mechanisms, one rule, and neither killable alone.
  # The flag went; the assignment below is the single owner and is
  # proved by `auto-hands-the-spacing-choice-back`, which mutates it.
  dict(name="auto-hands-the-spacing-choice-back", file=DIALOG,
       old="""      self._spacing_is_mine = False
    else:
      # No usable extent: a layer with no CRS, or an empty one. Leave""",
       new="""      pass  # mutation: Auto keeps the number the user's
    else:
      # No usable extent: a layer with no CRS, or an empty one. Leave""",
       test="test_a_spacing_a_person_typed_outlives_a_change_of_dataset",
       why="pressing Auto is the user asking the plugin to choose, so "
           "it must give ownership back; without this the box stays "
           "'theirs' forever after one typed number and every later "
           "dataset keeps a spacing derived for a different one"),
  # THE WORKING STATE, ONE ENTRY PER AXIS. The catalogue proves a
  # test's PRIMARY assertion and structurally cannot see the rest, and
  # this test carries several -- the design coming back, the elements
  # coming back, and the record existing on the group at all. Each is
  # aimed at the narrowest thing its own cells name.
  dict(name="a-group-gives-back-its-design", file=DIALOG,
       old="""      widget = getattr(self, attribute, None)
      if widget is not None:
        self._write_control(widget, kind, design[key])""",
       new="""      widget = getattr(self, attribute, None)
      if False:  # mutation: the design is recorded and never restored
        self._write_control(widget, kind, design[key])""",
       test="test_an_output_group_carries_the_whole_working_state",
       why="ruling 4 of 2026-08-25: selecting a group must RESTORE its "
           "design rather than leave the dialog inferring one. Without "
           "the write the record is stamped faithfully and read back "
           "faithfully and changes nothing on screen, which is the "
           "hardest kind of dead feature to notice"),
  dict(name="a-group-gives-back-its-elements", file=DIALOG,
       old="""    previous = self._restoring_assignments or self._assignments()
    self._restoring_assignments = None""",
       new="""    previous = self._assignments()  # mutation: ignore the record
    self._restoring_assignments = None""",
       test="test_an_output_group_carries_the_whole_working_state",
       why="the rebuild that answers a restore must read the RECORD "
           "and not the rows it is about to replace; reading the table "
           "carries the outgoing map's variables and schemes onto the "
           "design being returned to, which is the exact incoherence "
           "the ruling exists to remove"),
  dict(name="a-landing-records-the-working-state", file=DIALOG,
       old="""    self._stamp_working_state(group, launch_state)""",
       new="""    pass  # mutation: the group is left with no record at all""",
       test="test_an_output_group_carries_the_whole_working_state",
       why="a group with no record cannot be resumed, and nothing on "
           "screen says so: the dropdown would offer it and choosing "
           "it would restore nothing"),
  dict(name="the-record-describes-the-map-that-was-tiled", file=DIALOG,
       old="""      if isinstance(launch_state, dict):
        for key in ("design", "output_path", "region"):""",
       new="""      if False:  # mutation: record the controls as they stand now
        for key in ("design", "output_path", "region"):""",
       test="test_an_output_group_carries_the_whole_working_state",
       why="the design half must come from the launch snapshot. Read "
           "live at the landing, a spacing typed while the tiling ran "
           "goes into the record -- so the group claims a design its "
           "own layers were not drawn at, which is a false statement "
           "stored in somebody else's project"),
  # THE CHOOSER AND THE BINDING, again one entry per axis. Rulings 1,
  # 2 and 3 of 2026-08-25 are three separate promises and a single
  # mutation would prove only whichever assertion fires first.
  dict(name="a-dataset-selects-its-own-group", file=DIALOG,
       old="""    theirs = [entry for entry in groups if source and entry[2] == source]""",
       new="""    theirs = list(groups)  # mutation: any group will do""",
       test="test_the_output_group_chooser_binds_to_the_dataset",
       why="ruling 2: choosing a dataset must select a group made from "
           "THAT dataset. Taking any group binds the dialog to another "
           "dataset's map, and the next Generate replaces it -- which "
           "is the harm the whole ruling exists to prevent, arriving "
           "through the control that was meant to prevent it"),
  dict(name="recency-decides-among-a-datasets-groups", file=DIALOG,
       old="""    group = theirs[0][0]          # newest first, so this is ruling 3""",
       new="""    group = theirs[-1][0]  # mutation: oldest wins""",
       test="test_the_output_group_chooser_binds_to_the_dataset",
       why="ruling 3: where a dataset owns several groups the most "
           "RECENT is selected. A-B-A and 'create as new group' both "
           "leave one dataset owning two, and picking the older one "
           "restores a design the user moved on from and replaces the "
           "map they were last working in"),
  dict(name="choosing-a-group-selects-its-dataset", file=DIALOG,
       old="""          if same and layer is not self.layer_combo.currentLayer():
            self.layer_combo.setLayer(layer)""",
       new="""          if False:  # mutation: the group does not move the dataset
            self.layer_combo.setLayer(layer)""",
       test="test_the_output_group_chooser_binds_to_the_dataset",
       why="the binding is SYMMETRIC (ruling 2), and this is the half "
           "that is easy to leave out. Without it a group can be "
           "selected while the region chooser still names another "
           "dataset, so the restored design would be tiled from data "
           "it was never made for"),
  dict(name="the-chooser-asks-the-layers-not-the-name", file=DIALOG,
       old="""    found = []
    for node in root.children():
      if not hasattr(node, "children"):
        continue""",
       new="""    found = []
    for node in root.children():
      if not node.name().startswith(GROUP_BASE_NAME):  # mutation: by name
        continue""",
       test="test_the_output_group_chooser_binds_to_the_dataset",
       why="a group's name is a LABEL and never an identity -- this "
           "project has paid for that twice already, in adoption and "
           "in the replace-in-place lookup. Keyed on the name, the "
           "chooser loses a group the moment somebody renames it in "
           "the layers panel, which is an ordinary thing to do"),
  dict(name="a-dataset-with-no-group-claims-none", file=DIALOG,
       old="""      self._detach_from_the_group()
      self._refresh_group_combo()
      return False""",
       new="""      pass  # mutation: go on claiming the last dataset's group
      self._refresh_group_combo()
      return False""",
       test="test_the_output_group_chooser_binds_to_the_dataset",
       why="the chooser would name a map this dataset's run will not "
           "land in, which is exactly the invisible rule ruling 1 "
           "replaces -- and the records left standing are the ones a "
           "landing reads to decide what to REMOVE, so the dialog "
           "would be one Generate from deleting the other map"),
  # THE OUTPUT CONTRACT, ruling 6. Three axes: what a table HOLDS,
  # what it is CALLED, and whether the record that tidies old tables
  # follows the new names.
  dict(name="an-element-table-is-trimmed-to-what-it-displays",
       file=DIALOG,
       old="""      if mapped_variables:
        sub = sub[[column for column in sub.columns
                   if column not in mapped_variables
                   or column == a.get("var")]]""",
       new="""      if False:  # mutation: every element carries every variable
        sub = sub[[column for column in sub.columns
                   if column not in mapped_variables
                   or column == a.get("var")]]""",
       test="test_an_element_table_carries_only_what_it_displays",
       why="the file a user sends on carried attributes the map never "
           "drew -- a probe found a column named secret_code in all "
           "four tables of a map that displayed none of it, and a "
           "colleague measured an 800 KB dataset becoming a 19 MB "
           "GeoPackage because 23 elements each held all 26 columns"),
  dict(name="a-table-is-named-for-the-variable-it-displays",
       file=BRIDGE,
       old="""    cleaned = cleaned.strip("_")
    if cleaned:
      base = f"{base}_{cleaned[:48]}\"""",
       new="""    cleaned = cleaned.strip("_")
    if False:  # mutation: the variable never reaches the name
      base = f"{base}_{cleaned[:48]}\"""",
       test="test_an_element_table_carries_only_what_it_displays",
       why="opening the GeoPackage directly -- what you do with a file "
           "somebody sent you -- showed 'filename - tiles_a' and the "
           "variable was nowhere, which is where the maintainer met it "
           "on rc16"),
  dict(name="a-table-name-is-sanitised", file=BRIDGE,
       old="""      character if character.isascii() and (character.isalnum()
                                            or character == "_")
      else "_" for character in str(variable))""",
       new="""      character  # mutation: the column name goes in raw
      for character in str(variable))""",
       test="test_an_element_table_carries_only_what_it_displays",
       why="a column name is the user's and a table name is sqlite's. "
           "Real field names carry spaces, accents, brackets and the "
           "occasional SQL keyword, and this suite already stages "
           "'with space' and 'rate (%) 2021'"),
  dict(name="a-table-name-collision-is-refused", file=BRIDGE,
       old="""  suffix = 2
  while f"{base}_{suffix}".lower() in folded:""",
       new="""  return base  # mutation: let two elements share one table
  suffix = 2
  while f"{base}_{suffix}".lower() in folded:""",
       test="test_an_element_table_carries_only_what_it_displays",
       why="a GeoPackage FOLDS CASE: writing tiles_a and then tiles_A "
           "leaves one table holding the second element's data, with "
           "both writes reporting success (measured 2026-08-14). "
           "Sanitising makes collisions likelier rather than rarer, "
           "since 'rate %' and 'rate (%)' both become rate__"),
  dict(name="the-stale-table-drop-follows-the-new-names", file=DIALOG,
       old="""      current = {tables_this_run[tid] for tid in new_ids
                 if tid in tables_this_run}""",
       new="""      current = {f"tiles_{tid}" for tid in new_ids}  # mutation""",
       test="test_an_element_table_carries_only_what_it_displays",
       why="rebuilding the names from element ids alone says tiles_a "
           "where the run wrote tiles_a_v1, so every table of the NEW "
           "design looks stale and the drop removes the map it has "
           "just made -- the worst direction for a mistake in a "
           "routine whose whole job is deleting things"),
  # THE RESUMABLE FILE, ruling 5. Four axes: the record reaching the
  # file, the version refusal, the source found by reference, and
  # embedding staying an opt-in.
  dict(name="a-saved-map-carries-its-state", file=DIALOG,
       old="""      if not bridge.write_working_state(path, resumable):
        self._report_quietly(""",
       new="""      if False:  # mutation: the file keeps no record of its design
        self._report_quietly(""",
       test="test_a_saved_map_can_be_opened_and_carried_on",
       why="without it a finished map can be looked at and not carried "
           "on with: the file holds tables and styles and nothing "
           "about the design that produced them, so a demo re-tiles "
           "from scratch and a colleague receives a result they cannot "
           "continue. RE-ANCHORED AND RE-JUDGED on 2026-08-26, when "
           "the call gained a caller that reads its answer: the "
           "mutation still has to remove the WRITE and not merely the "
           "report, or it would prove its sibling entry rather than "
           "this one"),
  dict(name="a-forward-incompatible-file-is-refused", file=DIALOG,
       old="""    if not isinstance(version, int) or version > WORKING_STATE_VERSION:
      # FORWARD-INCOMPATIBLE, REFUSED WHOLE.""",
       new="""    if False:  # mutation: read a newer record as far as it goes
      # FORWARD-INCOMPATIBLE, REFUSED WHOLE.""",
       test="test_a_saved_map_can_be_opened_and_carried_on",
       why="half-reading a record from a later build restores a design "
           "nobody chose while looking exactly like a design somebody "
           "did, which is this software's characteristic failure "
           "wearing a file format"),
  dict(name="a-resumed-map-finds-its-source-by-reference", file=DIALOG,
       old="""      found = QgsVectorLayer(wanted, os.path.basename(str(wanted)), "ogr")
      if found.isValid():""",
       new="""      found = QgsVectorLayer(wanted, "x", "ogr")
      if False:  # mutation: never load the recorded source""",
       test="test_a_saved_map_can_be_opened_and_carried_on",
       why="the whole of ruling 5's default is that the source comes "
           "back BY REFERENCE, which is also what makes ruling 6's "
           "trimming safe -- a resumed map that cannot reach its data "
           "can be looked at and never redrawn"),
  dict(name="an-embedded-source-is-an-opt-in", file=DIALOG,
       old="""    if box is None or not box.isChecked() or not path:
      return False""",
       new="""    if box is None or not path:  # mutation: always embed
      return False""",
       test="test_a_saved_map_can_be_opened_and_carried_on",
       why="embedding by default puts somebody's data inside every map "
           "of it, which is ruling 8's concern arriving at a different "
           "boundary, and makes every file as large as its source"),
  dict(name="our-own-key-is-not-somebodys-variable", file=DIALOG,
       old="""    return [f.name() for f in layer.fields()
            if f.name() != bridge.GPKG_FID_COLUMN]""",
       new="""    return [f.name() for f in layer.fields()]  # mutation""",
       test="test_a_saved_map_can_be_opened_and_carried_on",
       why="a region read back from one of our own GeoPackages carries "
           "`weavingspace_fid`, our primary key. It is numeric and not "
           "in the id-like list, so the default picker took it, the "
           "run named a table for it, and the write failed outright -- "
           "16 of 61 features and the whole landing lost. Measured "
           "2026-08-25 on the resume path that made it reachable"),
  # THE SIZE GUARD, ruling of 2026-08-25. Three axes: the sentinels
  # being told from sizes, the bands, and the heavy question saying
  # what a refusal never said.
  dict(name="a-sentinel-is-not-a-size", file=BRIDGE,
       old="""  return isinstance(estimate, int) and estimate >= 0""",
       new="""  return True  # mutation: read a sentinel as a tile count""",
       test="test_the_size_guard_warns_where_it_used_to_refuse",
       why="this is the whole reason the ceiling could not simply "
           "soften. A unit that does not tile the plane and a layer "
           "whose extent cannot be measured are facts rather than "
           "quantities, and read as counts they become things a user "
           "clicks straight past -- and are told to try a larger "
           "spacing, which helps neither"),
  dict(name="the-heavy-band-asks-rather-than-refuses", file=BRIDGE,
       old="""  if estimate > MAX_TILES_HARD:
    return "heavy\"""",
       new="""  if estimate > MAX_TILES_HARD:
    return "refuse"  # mutation: decide for the user again""",
       test="test_the_size_guard_at_its_refusal_boundary",
       why="the maintainer ruled the ceiling a warning rather than an "
           "absolute: different machines have different maximums and "
           "different designs have different needs at the same count. "
           "As a refusal it had already declined a map the library "
           "renders in five seconds"),
  dict(name="the-heavy-question-says-what-it-may-cost", file=BRIDGE,
       old="""  return (f"This will generate roughly {estimate:,} tiles. A map this "
          f"large may use all the memory on this computer, and QGIS "
          f"may stop responding while it is drawn, so save your "
          f"project first. {advice} Continue anyway?")""",
       new="""  return many_tiles_question(estimate)  # mutation: the mild wording""",
       test="test_the_size_guard_warns_where_it_used_to_refuse",
       why="past the old refusal the question has to say what a "
           "refusal never said -- that this may exhaust memory, that "
           "QGIS may stop responding, and to save the project first. "
           "Without that the escalation is a number in a sentence "
           "nobody reads differently"),
  dict(name="the-live-gate-tells-a-sentinel-from-a-count", file=DIALOG,
       old="""    if not bridge.is_a_size(est):""",
       new="""    if False:  # mutation: hand a sentinel to the ceiling test""",
       test="test_the_size_guard_warns_where_it_used_to_refuse",
       why="both sentinels are NEGATIVE, so `est > LIVE_UPDATE_MAX_TILES` "
           "is False for them: read as a number, a design that cannot "
           "be drawn sails through the gate into a run that cannot "
           "draw it, and the note the user sees is about a tile count "
           "that does not exist"),
]

# The CRS entry needs its own anchor, found at import time so a
# refactor renames it here loudly rather than silently skipping.
CRS_ANCHOR = "result_crs"


def resolve_crs_mutation():
  """Point the CRS mutation at the line that reattaches the CRS after
  the worker thread (found by anchor rather than hard-coded, since it
  is the one mutation whose exact text has moved between versions)."""
  path = os.path.join(ROOT, DIALOG)
  with open(path, encoding="utf-8") as f:
    for line in f:
      stripped = line.rstrip("\n")
      if stripped.strip().startswith("gdf.crs = " + CRS_ANCHOR):
        indent = stripped[:len(stripped) - len(stripped.lstrip())]
        return dict(name="crs-reattach", file=DIALOG, old=stripped,
                    new=f"{indent}gdf.crs = None  # mutation",
                    test="test_real_world_data",
                    why="the output CRS surviving the worker round trip")
  return None


RUNNER = """
import importlib.util, os, sys
ROOT = {root!r}
sys.path.insert(0, ROOT)
spec = importlib.util.spec_from_file_location(
    "rt", os.path.join(ROOT, "tests", "run_tests.py"))
rt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rt)
from qgis.core import QgsApplication
QgsApplication.setPrefixPath(os.environ.get("QGIS_PREFIX_PATH", "/usr"), True)
app = QgsApplication([], True)
app.initQgis()
# the suite patches modal dialogs away in main(), which this runner
# does not call: without it a mutation that provokes a message box
# waits for a click that offscreen can never come, and reports as a
# timeout rather than as the caught mutation it really is
rt._enable_stack_dumps()
rt._no_modal_dialogs()
rt.check({test!r}, getattr(rt, {test!r}))
app.exitQgis()
sys.exit(1 if rt.FAILED else 0)
"""


BASELINE = {}
BASELINE_OUTPUT = {}


def test_interpreter():
  """The Python the tests must run under, which is QGIS's own.

  Returns:
    A path to an interpreter that can `import qgis`. `QGIS_PY` from the
    environment when it is set -- `tools/macos_qgis_env.sh` exports it,
    and the macOS CI job sources the same script -- and otherwise this
    process's own interpreter.

  WHY THIS EXISTS, and it invalidated a day's verdicts before anybody
  looked. Every test was launched with `sys.executable`. This module is
  invoked as `env -u PYTHONHOME -u PYTHONPATH python3`, because a plain
  `python3` that has inherited the QGIS environment dies at bootstrap
  -- a trap written down twice in CLAUDE.md -- and the interpreter that
  leaves you with is the system one, which HAS NO QGIS. So every test
  died at `import qgis.core`, exit 1, and a test that "failed" is
  scored `caught`.

  THE WHOLE CATALOGUE THEREFORE REPORTED SUCCESS FOR ANY ENTRY
  WHATEVER, including entries whose behaviour was not guarded at all
  and one whose test could not fail by construction. Measured
  2026-08-19: `/Library/Developer/CommandLineTools/usr/bin/python3 -c
  "import qgis.core"` gives ModuleNotFoundError, while the same test in
  the same sandbox under QGIS's own Python passes in 2.4 seconds.

  A CHECK THAT CAN ONLY CONFIRM IS NOT A CHECK -- this project's own
  rule, and the catalogue was one: it could report `caught` and nothing
  else. `require_a_usable_interpreter` below refuses to run rather than
  producing verdicts nobody can trust.
  """
  return os.environ.get("QGIS_PY") or sys.executable


def child_environment():
  """The environment a QGIS interpreter needs, rebuilt for a child.

  Returns:
    A copy of this process's environment with `PYTHONHOME` put back
    from `QGIS_PYTHONHOME` where the launcher saved it, so a child
    running `QGIS_PY` can find its own standard library.

  THE DOCUMENTED INVOCATION STRIPS EXACTLY WHAT THE CHILD NEEDS, and
  that is the whole reason this exists. This module must be run as
  `env -u PYTHONHOME -u PYTHONPATH python3`, because a plain python3
  carrying the QGIS environment dies at bootstrap -- but the QGIS
  interpreter this module LAUNCHES cannot start WITHOUT a PYTHONHOME,
  the cask's build carrying the paths of the machine it was built on.
  So the fix of 2026-08-19, which made the module resolve `QGIS_PY`
  and refuse when it cannot import qgis, refused every time: its
  probe inherited the stripped environment and the interpreter never
  started. Measured 2026-08-19: "Could not find platform independent
  libraries <prefix>", PYTHONHOME not set.
  `tools/macos_qgis_env.sh` therefore exports the value twice, once
  as `PYTHONHOME` for whoever sources it and once as
  `QGIS_PYTHONHOME` for whoever must strip the first and hand it to a
  child. A copy under a second name is not tidy; it is the only thing
  that survives `env -u`.
  Falling through when neither is set is deliberate: on Linux and
  Windows the interpreter starts without a PYTHONHOME at all, and
  inventing one there would be its own class of failure.
  """
  environment = dict(os.environ)
  saved = environment.get("QGIS_PYTHONHOME")
  if saved:
    environment["PYTHONHOME"] = saved
  return environment


def require_a_usable_interpreter():
  """Refuse to judge anything unless the tests can actually import QGIS.

  Returns:
    None. Exits with a message naming the interpreter and how to fix
    it, because a catalogue that runs and reports is worse than one
    that refuses: its verdicts get written into a ledger.
  """
  python = test_interpreter()
  probe = subprocess.run(
    [python, "-c", "import qgis.core"], capture_output=True, text=True,
    env=child_environment())
  if probe.returncode == 0:
    return
  sys.exit(
    f"REFUSING TO JUDGE: {python} cannot import qgis, so every test "
    f"would die at its first import and every entry would be reported "
    f"`caught` whatever the mutation did.\n\n"
    f"Source the environment first, which exports QGIS_PY:\n"
    f"  eval \"$(bash tools/macos_qgis_env.sh 2>/dev/null "
    f"| grep -E '^[A-Z_]+=' | sed 's/^/export /')\"\n"
    f"then run this module with `env -u PYTHONHOME -u PYTHONPATH "
    f"python3`, which is still right for the module itself.")


def test_passes_clean(name):
  """Whether the named test passes with NO mutation applied.

  Args:
    name: the test function's name, as an entry's `test` field gives
      it.

  Returns:
    True when it passes on the unmutated sandbox, False when it
    fails, None when it hangs. Cached per name, so a catalogue with
    many entries pointing at one test pays for one run.

  WHY THIS EXISTS, and it is the reason to read the verdicts below
  with it. A mutation is judged CAUGHT when its test FAILS -- and
  until 2026-08-19 nothing established that the test PASSED first. A
  test that fails in this runner for any other reason was therefore
  reported as proof that a behaviour is guarded.

  MEASURED THAT DAY, on a quiet machine so contention is not the
  explanation: a guard that had been written round a call the product
  now refuses -- so its comparison could not move whatever the
  mutation did -- came back `caught` here, twice, while breaking the
  same line by hand and running the same test through
  `tools/run_some.py` gave PASS. The catalogue's whole promise is
  that a green entry means a test can fail; an entry that cannot tell
  those two apart makes the promise unfalsifiable.

  THE RUNNER IS THE SAME ONE, deliberately: it is that runner's
  answer, not another's, that the verdict is being read against.
  """
  if name not in BASELINE:
    passed, output = run_test(name)
    BASELINE[name] = passed
    BASELINE_OUTPUT[name] = output
  return BASELINE[name]


def run_test(name):
  """True when the named test passes in a fresh interpreter."""
  code = RUNNER.format(root=BASE[0] or ROOT, test=name)
  # Run through the watchdog rather than a bare timeout: a mutation
  # that drives the code into a modal dialog or a dead event loop
  # stops using CPU, and that is detectable in seconds instead of
  # waiting out a timeout that tells us nothing about where.
  watchdog = os.path.join(BASE[0] or ROOT, "tools", "watchdog.py")
  try:
    python = test_interpreter()
    result = subprocess.run(
      [python, watchdog, "--stall", "45", "--timeout", "420",
       "--quiet", "--", python, "-c", code],
      cwd=BASE[0] or ROOT, capture_output=True, text=True, timeout=600,
      env=child_environment())
    if result.returncode in (124, 125):
      raise subprocess.TimeoutExpired(cmd="mutation", timeout=420,
                                      output=result.stdout)
  except subprocess.TimeoutExpired:
    # A mutation can push the code down a path that opens a modal
    # QMessageBox, and offscreen there is nobody to dismiss it: the
    # test then waits forever. That is not a surviving mutation (the
    # test certainly did not pass), but it must not stall the run, so
    # it is reported in its own right and the campaign continues.
    return None, ("stalled: the test stopped using CPU and never "
                  "returned (the watchdog's stack dump says where)")
  return result.returncode == 0, result.stdout + result.stderr


def apply_mutation(mutation, base=None):
  """Write the mutated source inside the sandbox.

  Args:
    mutation: the catalogue entry to apply.
    base: the sandbox root. The real project is never written to, so
      an interrupted campaign cannot leave a broken line behind --
      which is not hypothetical, a killed run did exactly that.

  Returns:
    (path, original text), so one mutation cannot contaminate the
    next inside the sandbox.

  Raises:
    SystemExit: the anchor is missing (the catalogue has drifted from
      the code) or AMBIGUOUS (it matches several places, so mutating
      the first would leave the rest doing the work). Both need a
      human decision rather than a silent skip, and the ambiguous
      case is the more dangerous because it reports SURVIVED rather
      than erroring.
  """
  path = os.path.join(base or ROOT, mutation["file"])
  with open(path, encoding="utf-8") as f:
    original = f.read()
  found = original.count(mutation["old"])
  if found == 0:
    raise SystemExit(
      f"ANCHOR MISSING for mutation '{mutation['name']}' in "
      f"{mutation['file']}:\n  {mutation['old'][:100]}\n"
      "The code moved; update tools/mutation_check.py.")
  if found > 1:
    # An AMBIGUOUS anchor is worse than a missing one, because it
    # fails quietly: only the first occurrence is mutated and the
    # identical siblings go on doing the work, so the behaviour never
    # actually breaks and the entry reports SURVIVED. Five entries sat
    # in that state until a full sweep exposed them (2026-08-10), each
    # reading as a gap in the tests when the fault was in the
    # catalogue. Refuse, and say which choice the author has to make:
    # narrow the anchor to the site the `why` describes, or -- if the
    # sites really are interchangeable -- delete the redundant code
    # rather than write a test defending it.
    raise SystemExit(
      f"AMBIGUOUS ANCHOR for mutation '{mutation['name']}': it "
      f"matches {found} places in {mutation['file']}, so only the "
      f"first would be mutated and the others would keep the "
      f"behaviour alive -- the entry would report SURVIVED whatever "
      f"the tests do.\n  {mutation['old'][:100]}\n"
      "Narrow the anchor with surrounding context, or delete the "
      "redundant call site.")
  with open(path, "w", encoding="utf-8") as f:
    f.write(original.replace(mutation["old"], mutation["new"], 1))
  return path, original


def main():
  """Break each catalogued behaviour in turn and see whether its test objects.

  Returns:
    None. Exits 1 when any non-equivalent mutation SURVIVED -- its
    test passed with the behaviour deliberately broken, which means
    that test does not in fact defend what it claims to. Prints a
    verdict per entry and a summary of survivors and hangs. The
    project's own source is never written to: everything happens in a
    throwaway copy made by tools/sandbox.py and discarded at the end.

  A mutation marked equivalent is expected to survive, so it is
  reported and not counted against the run; it stays in the catalogue
  rather than being deleted because if a future QGIS makes its branch
  live again, it will start being caught, and that is worth knowing.

  Two details that each cost something to learn. The CRS reattach
  mutation is resolved at run time because its anchor line moves;
  when it cannot be found the run says so out loud rather than
  quietly checking one behaviour fewer. And the signal handlers are
  not decoration: a SIGTERM skips the ``finally`` that puts a file
  back, which has already left mutated source on disk once.
  """
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--only", help="run just this mutation by name")
  args = parser.parse_args()

  catalogue = [m for m in MUTATIONS if m["name"] != "crs-reattach"]
  crs = resolve_crs_mutation()
  if crs:
    catalogue.append(crs)
  else:
    print("NOTE: the CRS reattach line was not found; that mutation is "
          "skipped and tools/mutation_check.py needs a new anchor.")
  if args.only:
    catalogue = [m for m in catalogue if m["name"] == args.only]
    if not catalogue:
      sys.exit(f"no mutation named {args.only}")

  # A kill (SIGTERM) skips `finally`, which would leave a mutated file
  # on disk -- exactly the trap that caught this tool once. Restore on
  # the usual signals as well as on the way out.
  import signal
  state = {"path": None, "original": None}

  def restore(*_args):
    if state["path"] and state["original"] is not None:
      with open(state["path"], "w", encoding="utf-8") as f:
        f.write(state["original"])
      print(f"\nrestored {state['path']} before exiting")
    raise SystemExit(130)

  for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
    signal.signal(sig, restore)

  require_a_usable_interpreter()
  sys.path.insert(0, HERE)
  from sandbox import discard, make_sandbox
  BASE[0] = make_sandbox("catalogue")
  print(f"mutating a copy at {BASE[0]}\n")

  survivors, hung, unjudgeable = [], [], []
  print(f"Checking {len(catalogue)} mutations "
        f"(each should make its test FAIL)\n")
  for mutation in catalogue:
    path, original = apply_mutation(mutation, BASE[0])
    state["path"], state["original"] = path, original
    try:
      passed, output = run_test(mutation["test"])
    finally:
      with open(path, "w", encoding="utf-8") as f:
        f.write(original)
      with open(path, encoding="utf-8") as f:
        assert f.read() == original, f"failed to restore {path}"
      state["path"], state["original"] = None, None
    if mutation.get("equivalent"):
      # An EQUIVALENT mutant changes no behaviour, so no test can
      # catch it and a survivor here means nothing. Kept in the
      # catalogue rather than deleted, because the reasoning is worth
      # preserving: if a future QGIS makes the branch live again, this
      # entry should start being caught, and that is a signal.
      verdict = "equivalent" if passed else "caught (now live!)"
    elif mutation.get("accepted"):
      # ACCEPTED is not equivalent, and the difference matters. An
      # equivalent mutant changes nothing observable; an accepted one
      # changes something real that no test we can write is able to
      # reach -- a defence whose occasion lives outside the harness.
      # Both are expected to survive, so neither is a failure, but
      # only equivalence is a claim about behaviour.
      #
      # This exists because an accepted entry judged as an open
      # survivor is flagged by every sweep forever. The catalogue
      # sweep of 2026-08-12 duly reported NEEDS ATTENTION on
      # fit-to-design-on-show, a case the maintainer had accepted
      # PERMANENTLY on 2026-08-10 with the evidence written down; the
      # flag cost a re-judge on 2026-08-13 that reached the same
      # answer for the third time. A warning that fires on a settled
      # decision is how people learn to stop reading warnings.
      #
      # Being CAUGHT is the interesting outcome, and it is announced:
      # it means a test now reaches what nothing could reach before,
      # so the acceptance can be withdrawn and the entry becomes an
      # ordinary guard.
      verdict = "accepted" if passed else "caught (now testable!)"
    else:
      verdict = ("HUNG" if passed is None
                 else "SURVIVED" if passed else "caught")
      # ...AND A `caught` IS ONLY BELIEVED WHERE THE TEST PASSES
      # CLEAN. Otherwise the entry proves nothing about the behaviour
      # it names: the test was failing in this runner already, and the
      # mutation is being credited with a failure it did not cause.
      # UNJUDGEABLE rather than SURVIVED, because the behaviour may
      # well be guarded and the fault is in the test or the harness --
      # which is a different work item and must not be counted as a
      # gap in the software.
      if verdict == "caught" and test_passes_clean(mutation["test"]) \
          is not True:
        verdict = "UNJUDGEABLE"
        output = (output or "") + (
          "\n\nTHE TEST DOES NOT PASS ON UNMUTATED CODE in this "
          "runner, so its failure says nothing about the mutation. "
          "Fix the test, or the harness, before reading this entry.")
    print(f"{verdict:>11}  {mutation['name']}  "
          f"[{mutation['test']}]  — {mutation['why']}")
    if verdict == "UNJUDGEABLE":
      # THE BASELINE'S OWN OUTPUT, because "unjudgeable" without a
      # reason is a second thing nobody can act on. This is the run
      # that failed on clean code, so its message names what is
      # actually wrong.
      unjudgeable.append(mutation)
      # THE CLEAN RUN IS NOT REPEATED HERE: `test_passes_clean` has
      # already made it and cached both the verdict and the output.
      # A first draft re-ran it, which doubled the cost of exactly the
      # entries that are already costing somebody an investigation.
      #
      # THE OUTPUT IS OFTEN EMPTY TODAY, because the watchdog runs the
      # child with `--quiet`. That is worth fixing and is not fixed
      # here: the verdict is the load-bearing part, and printing a
      # blank reason is better than printing a confident wrong one.
      print("             the test does not pass on UNMUTATED code in "
            "this runner, so nothing here is evidence about the "
            "behaviour; the failure below is the CLEAN run's")
      for line in (BASELINE_OUTPUT.get(mutation["test"]) or "").splitlines():
        if line.strip():
          print(f"             {line}")
    elif passed and (mutation.get("equivalent") or mutation.get("accepted")):
      pass  # expected: nothing to catch, for two different reasons
    elif passed:
      survivors.append(mutation)
      print("          the test passed with the behaviour broken; "
            "it needs a stronger assertion")
    elif passed is None:
      hung.append(mutation)
      # A stall is not a survivor and not a kill: the run never
      # finished, so the test said nothing either way. This line used
      # to carry the survivor's diagnosis above, telling whoever read
      # a hang the exact opposite of what had happened, while the
      # branch that really did mean "passed with the behaviour
      # broken" printed nothing at all.
      print("          the run never finished, so this mutation has "
            "no verdict; re-run it alone with --only")

  discard(BASE[0])
  print()
  if hung:
    print(f"{len(hung)} mutation(s) HUNG (a modal dialog with nobody to "
          "dismiss it, most likely): "
          + ", ".join(m["name"] for m in hung))
  if survivors:
    print(f"{len(survivors)} mutation(s) SURVIVED: "
          + ", ".join(m["name"] for m in survivors))
    sys.exit(1)
  # Say what actually happened rather than "all caught": an entry that
  # is expected to survive did not fail, which is not the same thing,
  # and a summary that calls it a kill is the kind of flattering count
  # this project keeps finding in its own instruments.
  if unjudgeable:
    # NEVER FOLDED INTO "caught". An entry whose test cannot pass on
    # clean code says nothing about the software, and reporting it as
    # a kill is how a catalogue comes to overstate what it holds.
    print(f"\n{len(unjudgeable)} entr(y/ies) UNJUDGEABLE, because the "
          f"test does not pass unmutated in this runner:")
    for m in unjudgeable:
      print(f"  {m['name']}  [{m['test']}]")
  expected = sum(1 for m in catalogue
                 if m.get("equivalent") or m.get("accepted"))
  if unjudgeable:
    print(f"{len(catalogue) - len(unjudgeable)} of {len(catalogue)} "
          f"judged; see above")
  elif expected:
    print(f"all {len(catalogue) - expected} judgeable mutation(s) were "
          f"caught; {expected} expected to survive (equivalent or "
          f"accepted) and did")
  else:
    print(f"all {len(catalogue)} mutations were caught")


if __name__ == "__main__":
  main()
