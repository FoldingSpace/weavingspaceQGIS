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
  # Re-anchored 2026-08-10: the one pass over the column now answers
  # two questions at once, so the constancy test has moved up into a
  # `constant` local and this gate merely reads it. Mutating the GATE
  # rather than the local keeps this entry aimed at the class count
  # alone; the ramp-midpoint behaviour that shares the local has its
  # own entry (constant-class-takes-ramp-start).
  dict(name="constant-column-classes", file=BRIDGE,
       old="""  if constant:
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
       old="""    super().showEvent(event)
    QTimer.singleShot(0, self._fit_to_design)""",
       new="""    super().showEvent(event)
    pass  # mutation: the window keeps its built size""",
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
        if value == bridge.NO_DATA_KEY:""",
       new="""        pass  # mutation: values fall back to left-aligned
        if value == bridge.NO_DATA_KEY:""",
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
  # Re-anchored 2026-08-10: the same line now also names
  # SPATIAL_INDEX. The mutation drops ONLY the FID rename, so this
  # entry still asks about the fid collision alone rather than
  # doubling as a spatial-index test (which has its own entry,
  # memory-layers-lose-their-index).
  dict(name='gpkg-fid-collision', file=BRIDGE,
       old='  options.layerOptions = ["FID=weavingspace_fid", "SPATIAL_INDEX=YES"]',
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
       old="  if constant and count:",
       new="  if False and count:"
           "  # mutation: keep QGIS's endpoint colour",
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
       old="""    layer.styleChanged.connect(
      lambda lid=layer.id(), tid=str(tile_id):
        self._on_layer_style_edited(lid, tid))""",
       new="    pass  # mutation: QGIS-side restyles go unnoticed",
       test="test_qgis_side_restyles_reach_the_dialog",
       why="recolouring an element layer in QGIS's styling dock must "
           "reach the dialog -- adopted as hand-picks or followed as "
           "a standard ramp -- or the ramp cell goes on naming a ramp "
           "that no longer decides the map (user decision, 2026-08-09)"),
  dict(name="custom-tooltip-reworded", file=DIALOG,
       old='CUSTOM_RAMP_TOOLTIP = ("Colours set by hand or by a class '
           'file. "\n                       '
           '"Choose a ramp to replace them.")',
       new='CUSTOM_RAMP_TOOLTIP = "Colours chosen by hand."'
           '  # mutation: reworded',
       test="test_a_customized_element_reads_custom",
       why="the Custom tooltip is the user's own fourteen words, "
           "settled verbatim on 2026-08-09"),
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
       old="      along = i / (count - 1) if count > 1 else 0.5",
       new="      along = i / count if count > 1 else 0.5"
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
           "no longer wears and the next Generate destroys the user's "
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
       old="""  for _ in range(60):
    if estimate_tile_count_bounds(unit, bounds, scale) <= MAX_TILES_HARD:
      break
    scale *= 1.02""",
       new="""  pass  # mutation: the inverse-square law has the last word""",
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
