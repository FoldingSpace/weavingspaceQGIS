# Hunt log: the prose, 2026-08-16 (hunt name `prose`)

Direction: **the prose as claims**, the last of the "not yet tried"
list. Every user-facing sentence — user guide, help tab, tooltips,
README, `docs/index.html`, `metadata.txt` `about` and `changelog` —
asserts something about behaviour. Ask what would have to be true,
then go and measure it. Nothing here was settled by reading more
prose.

Frozen at `ed7231f` ("A project opened under an open dialog is taken
over, not worked around"). Every probe ran through
`tools/hunt_probe.py --run` against that copy; HEAD had not moved when
this was written.

Ruled-out claims are listed as well as broken ones. The ruled-out list
is the part that shrinks the next person's queue.

## 12:24  iteration 0  [reading]
TRIED:  Assemble the corpus. USER-GUIDE.md (241 lines), help_content.py,
        49 `setToolTip` sites in dialog.py and category_editor.py,
        README.md, docs/index.html, metadata.txt `about` + `changelog`.
RESULT: `dev/state-of-play.md` is itself stale — it was written before
        `4cab431`/`c9208e0`/`a01c26a`, so its "the absence renderer is
        still SINGLE SYMBOL" note no longer holds. Noted so it is not
        used as an oracle.
NEXT:   census the tooltips against the fifteen-word rule, from the
        live widgets rather than the source.

## 12:31  iteration 1  [tooltip census]  probe p1_tooltips.py
TRIED:  Build a dialog on a 144-area layer, walk every child widget,
        read `toolTip()`, count words with tags stripped.
RESULT: 54 widgets carry a tooltip; NONE exceeds fifteen words (the
        longest is 14, the layer chooser). Every one names the control
        it sits on. CLAIM SOUND — CLAUDE.md's fifteen-word rule and
        the README's "every control has a tooltip".
        ONE BROKEN STRING: the Clip checkbox reports
        `'Trims the pattern to the region outline. The sloleft step.'`
        "sloleft" is not a word. USER-GUIDE:200 has "the slowest
        step"; `git log -S` puts the corruption in `766cada`.
NEXT:   the claims about the colour editor, which is where 0.24.3
        moved most.

## 12:44  iteration 2  [who owns a class bound]  probe p4_bounds.py
TRIED:  USER-GUIDE:169 — "the bounds belong to the data, so only the
        colours are yours to change". Open the editor through the
        button a user clicks, list every bound cell, then type into
        one and read the element's breaks back.
RESULT: CONFIRMED BROKEN. The table is `['Pin', 'Lower', 'Upper',
        'Colour']`; rows 0 and 4 carry editable `QDoubleSpinBox`es
        (row 0 Upper, row 4 Lower), rows 1–3 carry `NoPinHere`.
        Typing 5.4 into row 0's Upper set
        `dialog._pinned_bounds = {'a': {'v3': {'low': 5.4}}}` and
        moved every break: `(0,4)(4,14.2)(14.2,30)(30,55)(55,121)`
        became `(0,5.4)(5.4,16)(16,32)(32,55.5)(55.5,121)`.
NEXT:   the changelog's own claims, which reach more readers than the
        guide.

## 12:58  iteration 3  [two renderers]
TRIED:  CLAUDE.md's rule that the changelog must read in the plugin
        manager AND as GitHub markdown. Ran
        `release_notes.entry_for(metadata_field('changelog'), '0.24.3')`.
RESULT: RULED OUT. One opening paragraph plus fifteen bullets, one per
        category, every category converted. The two renderers agree.

## 13:06  iteration 4  [the absence categories]  probe p6_absence.py
TRIED:  metadata.txt 0.24.3 — "no data, infinity, and negative
        infinity each get their own colour and their own line in the
        legend, and each sits in that element's colour editor to be
        changed." Generate on a column holding NULL, NaN, +inf, -inf;
        read the paired layer's renderer; then open the editor.
RESULT: The LEGEND half is SOUND. `a – no data` carries a categorized
        renderer with three categories: `no-value`/"no data"/#dddddd,
        `neg-infinity`/"negative infinity"/#8c9fc7,
        `pos-infinity`/"infinity"/#c78c8c.
        The EDITOR half is BROKEN, and it is a product defect:
        `IndexError: list index out of range` at
        `category_editor.py:522`, inside `CategoryColourDialog.__init__`.
NEXT:   reproduce it with nothing instrumented, and find which kinds
        trigger it.

## 13:19  iteration 5  [clean reproduction]  probe p7_editor.py
TRIED:  Same route, patching only `CategoryColourDialog.exec` so a
        headless run does not block. Six columns, one per shape of
        absence.
RESULT: CONFIRMED. `NULL only` opens fine. `NULL + NaN` opens fine.
        `+inf only` raises `IndexError` out of a Qt slot and PyQt
        aborts the process (exit 250) — which for a user is QGIS's
        Python error window and no editor at all, not merely a missing
        infinity row. Mechanism: `dialog._edit_quant_colours` appends
        one `order` entry per absence kind present, while
        `category_editor` line ~497 special-cases only
        `bridge.NO_DATA_KEY`; the two infinity rows fall through to
        the class branch and index `self._bounds[row]` past its end.
        `grep _layer_with_infinities tests/run_tests.py` returns two
        call sites, neither of which opens the editor.
        This is the fifth-and-sixth-reader shape again: the predicate
        widened, `bridge.cannot_be_placed` was given one owner, and
        the EDITOR's row builder was not among the readers updated.

## 13:31  iteration 6  [the group a reopen makes]  probe p5_group.py
TRIED:  metadata.txt 0.24.3 — "The next Generate makes its own group
        as well, rather than drawing over the map that project already
        holds." Run, save the project, clear, reopen under the same
        open dialog, and count output groups.
RESULT: CONFIRMED BROKEN. After the reopen the dialog holds
        `_group_name == 'WeavingSpace tiles'` — the incoming project's
        OWN group — where the sentence requires it to hold nothing and
        build a second. Second route, independent of my probe:
        `test_a_project_opened_under_an_open_dialog_is_taken_over`
        PASSES at `ed7231f`, and it asserts exactly ONE output group
        after that Generate, bearing the project's own name. The
        sentence describes the half-fix `ed7231f` deliberately
        removed, and it ships in the plugin manager and on the release
        page.

## 13:40  iteration 7  [the web app rule]
TRIED:  CLAUDE.md's hard rule: never explain the plugin in terms of
        the web app, the help tab and user guide's further-reading
        links excepted.
RESULT: CONFIRMED BROKEN, in two files. README.md:22 and
        docs/index.html:224 both read "The plugin echoes and extends
        our earlier (also handwritten) web-based interface", linking
        `geospatialstuff.com/mapweaver/app/`, under "An experimental
        prototype" and "A prototype, and how it was made" — not under
        further reading, and phrased as an explanation of what the
        plugin IS. `tools/check_standards.py` passes on this tree:
        its rule greps `\b(web app|MapWeaver)\b`, and "web-based
        interface" matches neither. A rule that asserts its own
        enforcement, unenforced for this phrasing.
        RULED OUT alongside it: both MapWeaver URLs resolve
        (`dosull.github.io/mapweaver/app/` 301s to
        `geospatialstuff.com`), so the inconsistency is cosmetic.

## Claims checked and found SOUND

- Fifteen-word tooltip rule: 54 tooltips, longest 14 words.
- Every control explains itself, and every tooltip names its own
  control (read against the labels, one by one).
- No American spelling anywhere in the user-facing set (`color`,
  `behavior`, `center`, `analyz*` — the only hits are a CSS property
  and an HTML `align="center"` attribute).
- The changelog reads in both renderers: paragraph plus fifteen
  bullets.
- The three absence categories: three names, three colours, and only
  the kinds actually present.
- `metadata.txt` "the classes left empty are hatched in the swatch and
  counted in a notice" — the notice exists
  (`bridge.py:1339-1347`) and says "hatched", in both its pinned and
  unpinned forms.
- USER-GUIDE's `"Customize"` button — that is the button's real text.
- USER-GUIDE "the handles may meet but never cross" and "fifty linear
  steps" — both hold in the source that builds them.

## Noticed, and NOT counted as findings

- `bridge.missing_values_message` ends "They draw as no data, outside
  the class breaks", while the map now draws three named kinds. Its
  own docstring argues at length that "no value" would be false of an
  infinity, and then the sentence says "no data" of all of them. An
  imprecision, not a falsehood.
- The user guide has not caught up with 0.24.3 at all: no mention of
  the paired no-data layer, the three absence categories, the pin
  column, copying a classification, hatched empty classes, the
  released pin, or the missing-values notice. Omission is not a false
  claim, so none of that is filed as a finding — but the guide now
  describes a smaller plugin than the one a user meets.
- USER-GUIDE:107 "a narrow Classes column appears ... while any
  element is graduated" and :137 "An 'Edit colours' column appears
  ... whenever any element is categorized": both columns in fact
  appear for graduated AND categorized rows
  (`_update_dynamic_columns`). Incomplete rather than false, so ruled
  out under the "vague is not a finding" rule.
