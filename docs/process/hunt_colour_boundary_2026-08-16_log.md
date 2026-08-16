# Hunt log: colour across boundaries (one-boundary shape)

Brief: `python3 tools/bug_hunt_brief.py --shape one-boundary --area
"colour: palettes, ramps and the style library"`. The shape asked for,
`boundary`, is not offered; `one-boundary` is the closest and is the
one used.

Frozen tree: `tools/hunt_probe.py`. Prepared at 7bd34a6; by the first
probe the shared frozen copy had been re-prepared at 3b34364 by a
sibling, and every reading below is against 3b34364. Probes are in the
session scratchpad (`probes/p1_two_profiles.py` ... `p5_three_sessions.py`).

## 18:12:00  iteration 1
TRIED:  the premise. `QgsStyle.defaultStyle()` sampled at five points
        for Reds, YlGn, Greys, Set2 and tab10, first on this machine's
        own profile and then under
        `QGIS_CUSTOM_CONFIG_PATH=$(mktemp -d)`.
RESULT: confirmed. Seeded profile 63 ramps, fresh profile 35.
        YlGn seeded  #ffffe5 #d8efa3 #78c679 #228544 #004529
        YlGn fresh   #ffffcc #c2e699 #78c679 #31a354 #006837
        Reds seeded  #fff5f0 #fcbba2 #fa694c #cb1b1e #67000d
        Reds fresh   #fff5f0 #fcbea5 #fb7050 #d32020 #67000d
        Greys seeded #ffffff .. #000000; fresh #fafafa .. #050505
        Set2 and tab10 ABSENT from a fresh profile until the plugin
        installs them. One name really does mean two things.
NEXT:   push a project across that gap and see whether the receiving
        side refuses, substitutes, or draws something unseen.

## 18:26:00  iteration 2
TRIED:  the .qgz and .qml crossings. Graduated (YlGn, quantile, k=5),
        the same reversed, and categorized (YlGn) built on the seeded
        profile, written to a .qgz and to QMLs; reopened under a
        throwaway profile with a dialog constructed there to answer
        `_ramp_match`.
RESULT: ruled out. Every colour survives byte-identically: grad
        #ffffe5 #d8efa3 #78c679 #228544 #004529 on both sides, rev the
        same reversed, cat the same per value. `_ramp_match` answers
        `(None, False)` on all three, so the row reads Custom rather
        than claiming a YlGn it cannot reproduce. The QML confirms
        why: it mentions "YlGn" zero times and carries colour1,
        colour2 and every stop as literal RGB. The file crossings
        carry COLOURS.
NEXT:   so look for the crossing that carries a NAME and drops
        colours. `_adopt_row_symbology` is it: its categorized branch
        asks whether the ramp explains what is drawn (dialog.py
        3817-3838), its graduated branch returns the moment a name
        matches (dialog.py 3878).

## 18:47:00  iteration 3
TRIED:  a hand colour put on each styling path the way QGIS's dock
        puts it (renderer clone, updateRangeSymbol /
        updateCategorySymbol, set back whole), then a fresh dialog
        asked to adopt each layer. Ramp YlGn on the seeded profile.
        (First run segfaulted on `edited.ranges()[2].symbol()` -- the
        dangling-temporary lesson, hold the list.)
RESULT: confirmed, and it is the twin asymmetry again.
        CATEGORIZED map #ffffe5 #abcdef #78c679 #228544 #004529 ->
        dialog recovers ramp YlGn AND `{'c': {'b': '#abcdef'}}`.
        GRADUATED map #ffffe5 #d8efa3 #abcdef #228544 #004529 ->
        dialog recovers ramp YlGn, k 5, quant picks None.
        Seeding again from what it recovered draws
        #ffffe5 #d8efa3 #78c679 #228544 #004529: the hand colour gone.
NEXT:   second independent route -- a whole session, read off the
        layer rather than the dialog's dicts.

## 19:04:00  iteration 4
TRIED:  one process: generate to a GeoPackage, `dlg.close()`, dock
        recolour, project round trip, new dialog, Generate.
RESULT: ruled out as a reproduction. The colour SURVIVED
        (`quant picks: {'v1': {'2': '#abcdef'}}`). Closing a Qt dialog
        does not disconnect `rendererChanged`, so the closed dialog
        still heard the edit, adopted it and stamped it. My fixture,
        not the software.
NEXT:   do it as three separate QGIS processes, which is what a user
        actually does: make, refine another day, generate the day
        after.

## 19:19:00  iteration 5
TRIED:  three QGIS processes against one project file. (1) generate a
        graduated element on Reds to a GeoPackage, save. (2) open the
        project with NO plugin dialog constructed at all, recolour
        class 2 as the styling dock does, save. (3) open the project,
        open the plugin, re-point the row at v1, Generate. Colours
        read with `bridge.renderer_fill_colours` off the layer.
RESULT: confirmed.
        after generate      #fff5f0 #fca082 #e32f27 #67000d
        after the dock edit #fff5f0 #fca082 #abcdef #67000d
        as reopened         #fff5f0 #fca082 #abcdef #67000d
          row says ramp Reds, reverse False, k 4, quant picks None
        after Generate      #fff5f0 #fca082 #e32f27 #67000d
        The stamp is None throughout, as it must be: nothing was
        running to write it. The categorized twin of this session is
        already guarded by
        `test_a_dock_recolour_outlives_a_retile_a_save_and_a_reopen`,
        which is categorized only.
NEXT:   date it, then re-check HEAD.

## 19:31:00  iteration 6
TRIED:  `git log -S` on the two branches.
RESULT: confirmed. `_adopt_row_symbology` arrived whole in d824a37
        (2026-08-13) with the graduated `if named: return`. The
        categorized branch gained "a named ramp is not proof that the
        ramp decides the colours" in f1da490, later the same day and a
        descendant of d824a37. The graduated half was never revisited.
NEXT:   report. HEAD re-checked: 3b34364, the commit the frozen copy
        holds; it moved from 7bd34a6 to 3b34364 between --prepare and
        the first probe and has not moved since.
