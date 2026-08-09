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
PLUGIN = "weavingspace_qgis/plugin.py"
CATALOG = "weavingspace_qgis/catalog.py"
COMPAT = "weavingspace_qgis/compat.py"
PERCEPTION = "weavingspace_qgis/perception.py"
EDITOR = "weavingspace_qgis/category_editor.py"
WORKER = "weavingspace_qgis/worker.py"
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
       old="""    if layer.setSubsetString(combined):
      restore = previous""",
       new="""    if False:  # mutation: classify the nulls along with the data
      restore = previous""",
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
  dict(name="constant-column-classes", file=BRIDGE,
       old="""  if index >= 0 and numeric_values_are_constant(layer.uniqueValues(index)):
    k = 1""",
       new="""  if False:  # mutation: cut k classes over one distinct value
    k = 1""",
       test="test_a_constant_column_draws_one_class_and_says_so",
       why="a column that is 7 everywhere gets five classes all "
           "reading 7 - 7 in five colours, a legend showing variation "
           "the data does not have"),
  # TWO entries, because there are two signatures and they gate
  # different paths: _geometry_signature decides whether pressing
  # Generate re-tiles or merely repaints, and _run_signature decides
  # whether a live update runs at all. One entry pointed at the wrong
  # one survived, which is the failure this file is for.
  dict(name="fingerprint-in-geometry-signature", file=DIALOG,
       old="""      self._layer_fingerprint(), self._data_version,
    )

  def _restyle_only(self) -> bool:""",
       new="""    )

  def _restyle_only(self) -> bool:""",
       test="test_data_changed_in_qgis_while_the_plugin_is_open",
       why="without the layer's CONTENTS here, deleting half the "
           "features leaves every term identical, so pressing Generate "
           "is answered by repainting tiles built from data that no "
           "longer exists"),
  dict(name="fingerprint-in-run-signature", file=DIALOG,
       old="""      self._layer_fingerprint(), self._data_version,
    )

  @staticmethod""",
       new="""    )

  @staticmethod""",
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
       old="""    self._build_ui()
    self._update_layer_exclusions()""",
       new="""    self._build_ui()""",
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
       old="self.progress.setVisible(False)",
       new="self.progress.setVisible(True)",
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
       old="self._live_pending = False",
       new="self._live_pending = True",
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
  dict(name="stale-field-assignment", file=DIALOG,
       old='      if prev and prev["var"] in fields:',
       new='      if prev and prev["var"] is not None:',
       test="test_the_user_changes_the_data_underneath",
       why="an element stops being mapped to a field the user has "
           "deleted from the layer, rather than carrying a name that "
           "no longer exists into the next run"),
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
       old="      combo.clear()",
       new="      pass  # mutation: entries appended, never replaced",
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
  dict(name="palette-end-colour", file=BRIDGE,
       old="        QColor(stops[0]), QColor(stops[-1]), False, gradient_stops)",
       new="        QColor(stops[0]), QColor(stops[-2]), False, gradient_stops)",
       test="test_installed_palettes_span_their_declared_colours",
       why="every installed sequential and diverging ramp reaching "
           "the colour it declares at its dark end, which is the end "
           "carrying the highest values on the map"),
  dict(name="conditional-column-hidden-index", file=DIALOG,
       old="    self.table.setColumnHidden(7, True)",
       new="    self.table.setColumnHidden(8, True)"
           "  # mutation: hides the wrong column",
       test="test_dialog_structure",
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
  dict(name="fit-to-design-on-show", file=DIALOG,
       old="    QTimer.singleShot(0, self._fit_to_design)",
       new="    pass  # mutation: the window keeps its built size",
       test="test_the_window_fits_its_design_tab_when_shown",
       why="the window opening tall enough to show the Design tab it "
           "contains; sizeHint is not truthful before a layout pass, "
           "so the fit has to be deferred and then actually happen"),
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
       old="    painter.setRenderHint(QPainter.RenderHint.Antialiasing)",
       new="    pass  # mutation: hard edges",
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
  dict(name="family-list-signals-blocked", file=DIALOG,
       old="    self.family_combo.blockSignals(True)",
       new="    self.family_combo.blockSignals(False)"
           "  # mutation: handlers fire mid-refill",
       test="test_repopulating_the_family_list_fires_no_handlers",
       why="the unit being rebuilt once for a kind change rather than "
           "once per family added to the list"),
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
  dict(name="editor-value-alignment", file=EDITOR,
       old="""      cell.setTextAlignment(Qt.AlignmentFlag.AlignRight
                            | Qt.AlignmentFlag.AlignVCenter)""",
       new="""      pass  # mutation: values fall back to left-aligned""",
       test="test_the_editor_is_laid_out_as_specified",
       why="values set right against colours set left, so the eye "
           "runs down one gap rather than across a ragged one"),
  dict(name="category-colour-override", file=BRIDGE,
       old="""    if str(v) in overrides:""",
       new="""    if False:  # mutation: hand-picked colours ignored""",
       test="test_editing_a_category_colour_reaches_the_map",
       why="a colour chosen in the Categorical colour editor being "
           "the colour the map actually draws"),
  dict(name="category-colours-in-signature", file=DIALOG,
       old="""            a.get("reverse", False), a.get("opacity", 100),
            tuple(sorted(picked.items())))""",
       new="""            a.get("reverse", False), a.get("opacity", 100))"""
           """  # mutation: picks invisible to the restyle path""",
       test="test_editing_a_category_colour_reaches_the_map",
       why="the fast path noticing a hand-picked colour at all; "
           "without it the element is skipped as unchanged"),
  dict(name="category-colours-reread-after-run", file=DIALOG,
       old="""    for a in assignments:
      if a.get("mode") == "Categorized" and a.get("var"):
        a["category_colours"] = self._category_colours.get(
          a["id"], {}).get(a["var"])""",
       new="""    pass  # mutation: the run's stale snapshot wins""",
       test="test_a_colour_picked_during_a_run_is_not_lost",
       why="a colour picked while a tiling was finishing surviving "
           "that tiling, rather than being overwritten by the "
           "settings the run started with"),
  dict(name="category-colours-cleared-by-ramp", file=DIALOG,
       old="""        self._clear_category_colours(tid, "a new colour ramp")""",
       new="""        pass  # mutation: hand-picks outlive the ramp change""",
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
  dict(name="edit-colours-column-visibility", file=DIALOG,
       old="""    self.table.setColumnHidden(COL_EDIT_COLOURS, not has_categorical)""",
       new="""    self.table.setColumnHidden(COL_EDIT_COLOURS, False)"""
           """  # mutation: always on""",
       test="test_the_edit_colours_column_appears_with_categories",
       why="the column appearing only where there are categories to "
           "colour, rather than as a dead control on every map"),
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
       old="      layer.id() if layer is not None else None,",
       new="      layer.id() if layer is None else None,",
       test="test_switching_region_layer_counts_as_a_change",
       why="a different region layer counting as a change, rather "
           "than leaving the previous layer's map on screen"),
  dict(name="chooser-race", file=DIALOG,
       old='lambda _i, c=mode_combo: c.setProperty("touched", True))',
       new="lambda _i, c=mode_combo: None)",
       test="test_style_follow_and_memory",
       why="the hook that remembers a hand-picked style"),
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
       old='      elif prev is not None and prev["var"] is None:',
       new='      elif False:  # mutation: a default variable comes back',
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
  dict(name='no-data-class', file=BRIDGE,
       old='  categories.append(QgsRendererCategory(\n    None, _fill_symbol(NO_DATA_FILL, outline), "no data"))',
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
       old='      if unchanged:',
       new='      if not unchanged:  # mutation: keep the WRONG renderer',
       test='test_integration_interleaved_session',
       why='hand styling kept for unchanged elements only'),
  dict(name='outline-layer-not-on-top', file=DIALOG,
       old='      group.insertLayer(0, outline_layer)',
       new='      group.addLayer(outline_layer)  # mutation: buried at the bottom',
       test='test_integration_weave_and_icons',
       why='region outlines drawn on top of the elements'),
  dict(name='gpkg-layer-naming', file=DIALOG,
       old='        out = bridge.write_gpkg_layer(mem, path, f"tiles_{tid}",',
       new='        out = bridge.write_gpkg_layer(mem, path, "tiles_x",',
       test='test_ui_library_categorical_to_gpkg',
       why='each element getting its own layer inside the GeoPackage'),
  dict(name='categorical-template-ignored', file=DIALOG,
       old='        bridge.seed_renderer(out, a, templates.get(a.get("class_source")))',
       new='        bridge.seed_renderer(out, a)  # mutation: imported mapping dropped',
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
  dict(name='gpkg-fid-collision', file=BRIDGE,
       old='  options.layerOptions = ["FID=weavingspace_fid"]',
       new='  pass  # mutation: let an fid attribute collide with the key',
       test='test_gpkg_fid_attribute',
       why='exporting data that carries an attribute called fid'),
  dict(name="crs-reattach", file=DIALOG,
       old="    self._adopt_existing_group()",  # placeholder, replaced below
       new="    self._adopt_existing_group()",
       test="test_real_world_data",
       why="the output CRS surviving the worker round trip"),
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


def run_test(name):
  """True when the named test passes in a fresh interpreter."""
  code = RUNNER.format(root=BASE[0] or ROOT, test=name)
  # Run through the watchdog rather than a bare timeout: a mutation
  # that drives the code into a modal dialog or a dead event loop
  # stops using CPU, and that is detectable in seconds instead of
  # waiting out a timeout that tells us nothing about where.
  watchdog = os.path.join(BASE[0] or ROOT, "tools", "watchdog.py")
  try:
    result = subprocess.run(
      [sys.executable, watchdog, "--stall", "45", "--timeout", "420",
       "--quiet", "--", sys.executable, "-c", code],
      cwd=BASE[0] or ROOT, capture_output=True, text=True, timeout=600)
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
    SystemExit: the anchor is missing, meaning the catalogue has
      drifted from the code and needs a human decision rather than a
      silent skip.
  """
  path = os.path.join(base or ROOT, mutation["file"])
  with open(path, encoding="utf-8") as f:
    original = f.read()
  if mutation["old"] not in original:
    raise SystemExit(
      f"ANCHOR MISSING for mutation '{mutation['name']}' in "
      f"{mutation['file']}:\n  {mutation['old'][:100]}\n"
      "The code moved; update tools/mutation_check.py.")
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

  sys.path.insert(0, HERE)
  from sandbox import discard, make_sandbox
  BASE[0] = make_sandbox("catalogue")
  print(f"mutating a copy at {BASE[0]}\n")

  survivors, hung = [], []
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
    else:
      verdict = ("HUNG" if passed is None
                 else "SURVIVED" if passed else "caught")
    print(f"{verdict:>8}  {mutation['name']}  "
          f"[{mutation['test']}]  — {mutation['why']}")
    if passed and mutation.get("equivalent"):
      pass  # expected: nothing to catch
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
  print(f"all {len(catalogue)} mutations were caught")


if __name__ == "__main__":
  main()
