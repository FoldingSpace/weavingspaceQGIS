# Hunt 2 — unreachable branches — weavingspace QGIS plugin
Worktree: /private/tmp/claude-501/-Users-luke-claude-scratch/9a569ef7-3f5e-4a44-8ecf-716f080f3573/scratchpad/hunt2-unreach

## 03:14:27  iteration 1  [perturbation]
TRIED: use the SHIPPED reports/per-test-coverage.json (main repo) as an un-taken-branch finder; then, finding it stale, launched tools/coverage_report.py (branch coverage) over the whole suite in my worktree, pid 52485.
RESULT: inconclusive on the record — it was written 2026-08-13 08:22 and dialog.py has drifted (508 of 2362 recorded lines now land on blank/comment lines); bridge.py drifted 2 lines. Live branch-coverage run started instead.
NEXT: while it runs, read guards by hand and trace callers, starting with bridge.py's symbology path (highest harm: a wrong map).

## 03:18:40  iteration 2  [logical]
TRIED: catalog.get_over_under (weavingspace_qgis/catalog.py:353-366) — its docstring says "an odd-length list is trimmed to even length as WeaveUnit expects", implemented as `length = 2 * len(numbers) // 2`.
RESULT: confirmed dead — Python parses that as (2*len)//2 == len for every len, so the trim NEVER fires; `if length == 0` is unreachable too (an empty split raises ValueError first). tests/run_tests.py:24468 pins the untrimmed result and its own comment calls length 1 "even"; the UI-vs-library sweep (tests/run_tests.py:30792) restates the SAME expression, so its oracle agrees with the bug by construction.
NEXT: find out whether the state the trim was written to prevent actually harms — hand WeaveUnit an odd-length passing pattern directly and compare with the trimmed one; if the weave is fine, this is a docstring lie, not a defect.

## 03:20:48  iteration 3  [logical]
TRIED: three "precondition never arrives" candidates by tracing callers: (a) WeaveUnit with an odd-length passing pattern; (b) _add_output_layers' run_sig/geometry_sig=None fallback (dialog.py:5137); (c) any layer.extent() call reached without compat.layer_data_is_available (the documented segfault guard).
RESULT: (a) ruled out as harm — the vendored WeaveUnit accepts (1,2,2)/(1,2,3) and weaves 100/144 tiles without raising, so the never-firing trim costs nothing; (b) CONFIRMED dead — _on_generated has exactly one caller (dialog.py:4612) and always passes both signatures, and _run_signature() cannot return None, so the documented "synchronous path" fallback at 5137/5139 cannot run; (c) ruled out — all four extent() sites (1522, 1817, 2018 and via layer_to_gdf at 4478) sit behind the guard.
NEXT: stop guessing one guard at a time; the branch-coverage run (pid 52485) is the right instrument for this shape. Wait for its un-taken-branch listing, then trace callers for each candidate.

## 03:25:15  iteration 4  [perturbation: ask the dependency, not the code]
TRIED: bridge.get_ramp's third reversal branch (bridge.py:222-225, "anything else is sampled at even steps and rebuilt", reached only when `hasattr(ramp,"invert")` is False) — instantiated every QgsColorRamp subclass QGIS exposes and asked whether invert exists and whether it inverts.
RESULT: confirmed unreachable — hasattr(ramp,"invert") is True for all six classes (QgsColorRamp declares it), so nothing upstream can produce the state that branch guards. AND the failure it was written for arrives anyway: QgsLimitedRandomColorRamp inherits a NO-OP invert(), so get_ramp(name, reverse=True) hands back an unreversed ramp (samples identical before/after). The style library here holds only Gradient (51) and Preset (12) ramps, but the plugin's combo lists every ramp in the user's library unfiltered (dialog.py:2404 over bridge.ramp_names()).
NEXT: second independent route — install a random ramp into the style, drive a real dialog's Reverse box through its own signal, and read the class colours off the OUTPUT LAYER's renderer rather than off get_ramp.

## 03:27:00  iteration 5  [logical: chase the harm, not the branch]
TRIED: second route on the get_ramp finding — drove a real dialog (rt._quant_dialog), generated, ticked Reverse through the switch's own toggled signal, regenerated, and read class colours off the OUTPUT LAYER via bridge.renderer_fill_colours. Control ramp "Reds" alongside a QgsLimitedRandomColorRamp added to the style library the way Style Manager does.
RESULT: Reds reversed exactly (#fff5f0..#67000d -> #67000d..#fff5f0), so the driving is sound. The random ramp changed too — but by RE-RANDOMISING, not reversing: QGIS 4 exposes no setSeed, so every clone draws new colours and a reversal is undetectable. So the unreachable branch is confirmed twice over, and its stated guarantee is false, but I cannot show a user losing anything by it. Recording as harm unclear rather than dressing it up.
NEXT: back to the instrument — the branch-coverage run should be near done; take its never-taken branches and trace callers, which is the only way to cover ground faster than one guard an hour.

## 03:29:58  iteration 6  [logical]
TRIED: the same species as the get_ramp find — every hasattr/getattr guard in the package (16 of them), asking which can never be False, plus three "notice that can never fire" candidates: bridge.categorical_shift_message's `previous is None` gate, dialog._class_counts vs _category_counts (two dicts, similar names), and _adopt_row_symbology's single-symbol test at dialog.py:3102.
RESULT: ruled out. _category_counts is keyed by FIELD and written at 4681 right after the read at 4680, so the second run can fire it; _class_counts is keyed by TILE and written only by the enabled spin handler (2899), which also writes user_k in the same breath, so the landing re-read at 5167 cannot desync k from _assignments; the 3102 test is right for all three renderer kinds the plugin makes. No second always-true hasattr with a real failure behind it.
NEXT: coverage nearly done; read its never-taken branch list for bridge/dialog and trace the callers of anything that looks like a guard rather than an error path.

## 03:30:42  iteration 7  [perturbation: ask QGIS whether the state exists]
TRIED: dialog._watch_layer's defensive `if signal is not None` (dialog.py:1650) — a watched signal name QGIS does not have is skipped silently, which would cost exactly one unheard kind of layer edit and a stale map that looks right. Probed all twelve names plus repaintRequested against a real QgsVectorLayer.
RESULT: ruled out — all thirteen exist and all thirteen connect. The guard is unreachable on QGIS 4.0.3 but hides nothing: no blind spot behind it.
NEXT: coverage at 178/311 and still busy (8:56 CPU / 16:15 elapsed). Keep hand-tracing while it finishes; next candidate is the live-update gate's no-op test in _maybe_live_generate.

## 03:32:56  iteration 8  [logical: a guard beside its unguarded twin]
TRIED: the design preview's two colour lookups (dialog.py:651 and 684). The LABEL lookup guards `if tid in self._ids` and falls back to "#cccccc"; the POLYGON lookup twenty lines above does the same self._ids.index(tid) with no guard, inside paintEvent — a Qt slot, where a ValueError would vanish into sys.excepthook and simply stop the preview drawing.
RESULT: ruled out — show_unit sets self._ids = sorted({p[0] for p in polys}) from the very list the polygon loop walks (dialog.py:573), so the unguarded lookup cannot miss and the guarded twin's fallback is the unreachable one. Harmless either way: it decides label ink, not the map.
NEXT: coverage at 201/311. Finish it, read the never-taken branches, and separately re-run the one test that FAILED under the recorder ("race: restyle during a run") in a plain run, since a failure seen only under the recorder is a harness artefact and one seen in both is a finding.

## 03:34:05  iteration 9  [perturbation: believe the instrument's own failure]
TRIED: the FAIL the coverage run threw off ("race: restyle during a run"), on the theory that a failure seen only under the recorder is a harness artefact. Re-ran it plainly with tools/run_some.py on a clean project, ran its twin, and ran it again at the previous commit in a second worktree (hunt2-prev, b148baa).
RESULT: confirmed, and dated. test_race_restyle_during_run FAILS at HEAD in both harnesses (tests/run_tests.py:23612, "with live update off, nothing should repaint by itself") while test_a_ramp_chosen_during_a_run_reaches_the_map PASSES; the two assert opposite outcomes for the same act. It PASSES at b148baa. `git log -S` puts the cause in bce8953, the landing-time re-read at dialog.py:5156-5168, and the contradicting assertion has stood since the initial commit.
NEXT: finish the branch-coverage read for the assigned shape, then write up: one confirmed unreachable branch (bridge.py:220-225) with harm unclear, and this red-at-HEAD contradiction.

## 03:35:54  iteration 10  [logical]
TRIED: _adapt_to_the_layer (dialog.py:1657-1795), the path that runs when a column vanishes from the region layer — asking which of its guards can never see the state it names.
RESULT: all reachable, but noted one asymmetry while there: at dialog.py:1782 the element's hand-picked CATEGORY colours for the vanished field are popped, and the graduated twin (_quant_colours) is not. Both are keyed {tile: {field: ...}}, so after a column disappears and returns, a graduated element gets its positional picks back and a categorical one does not. Harm unclear — the survivors are inert while the field is absent — but it is the same one-of-a-pair shape docs/TESTING.md warns about.
NEXT: coverage still running (206/311, the long tests now). Verify the mid-run reproduction once more against a clean project, then write up.

## 03:37:51  iteration 11  [logical]
TRIED: bridge.layer_to_gdf's two remaining guards — the QGIS-NULL normalisation at bridge.py:290 and the `if target_crs:` reprojection at 298 — plus a caller census for both.
RESULT: the NULL normalisation is ALREADY declared unreachable on QGIS 4 in its own comment and recorded as an equivalent mutant, which is the maintainer handling this shape properly; `target_crs` is passed by nothing in the shipped package (dialog.py:4491 is the only call site and omits it), so 299 runs only from tests. Neither costs a user anything.
NEXT: coverage still busy on one long test (13:14 CPU / 22:52, 99.9%). Wait it out, read the branch section, then report.

## 03:39:00  iteration 12  [logical]
TRIED: the Custom-display and Edit-colours block at the tail of _sync_row (dialog.py:2634-2707), looking for a condition the row state cannot produce.
RESULT: ruled out except for one already-declared legacy: `choice not in (self.BROWSE, self.SHARED)` at 2690 tests a SHARED sentinel the class-source combo has not offered since the dialog-wide style box was removed (dialog.py:2139 says so), so that half is dead by design. Everything else is reachable.
NEXT: coverage still on one long test (14:40 CPU / 24:33). Waiting on the process rather than on predicted log text; then the branch listing, then the report.

## 03:40:35  iteration 13  [logical]
TRIED: two more "the state never arrives" candidates on the run path: the coverage dict's initial {"missing": None} reaching bridge.coverage_message (dialog.py:4667 -> bridge.py:697, where `None <= 0` would raise inside the done callback), and _on_n_changed's silent kind-flip at dialog.py:1348 ("some counts exist only as tilings or only as weaves").
RESULT: both reachable-or-safe. work() always writes coverage["missing"] before returning a map, and the None case is fenced by `gdf is not None and len(gdf) > 0`; and the catalogue really does have counts 13-26 with tilings only (measured over TILINGS_BY_N), so the kind-flip fires whenever a user asks for a weave at 13 or more elements.
NEXT: the coverage run has been on one test for nine minutes at 99.9% CPU, which matches the documented long sweeps. Give it a bounded wait; if the branch listing does not arrive, report what twelve traced guards found.

## 03:41:55  iteration 14  [logical]
TRIED: the ramp installer and its cache (bridge.ensure_ramps_installed, _RAMP_NAME_BY_LOWER at bridge.py:113-186) — whether the case-insensitive fallback can be entered with a stale map, and whether the `except Exception: pass` in save() hides a palette that never arrives.
RESULT: ruled out. The cache is cleared at install time and refreshed on every miss, and a name removed from the style library resolves to None either way. Also re-confirmed the exact lines of the one confirmed find: guard at bridge.py:220, dead fallback at 223-225.
NEXT: the full-suite failure is confirmed in both harnesses and in isolation, so it is not an ordering artefact. Waiting out the second long sweep for the branch listing; report is otherwise ready.

## 03:54:15  iteration 15  [perturbation: the instrument itself was the finding]
TRIED: the coverage run finished (359 passed, 1 failed, 41 minutes) and wrote NO coverage.md and printed no coverage line. Asked why, and found tools/coverage_report.py:263 wrapping runpy.run_path in `except SystemExit`, on a docstring that says "the suite calls sys.exit() when it finishes, which is caught here so the report can still be written".
RESULT: CONFIRMED unreachable, with harm. tests/run_tests.py:36184 calls os._exit, not sys.exit, since commit 0d13f7e (2026-08-11) — os._exit ends the process outright, so the except never fires, the finally never runs, and write_report/the printed summary/sys.exit(status) after it are all dead. Proved a second way in a second, with no QGIS: coverage_report_dead_repro.py runs runpy over a script ending in os._exit and nothing after it executes. The sibling tool tools/coverage_per_test.py:206 monkeypatches os._exit for exactly this reason, with a comment explaining it; this twin was never taught. CLAUDE.md:1193, docs/TESTING.md:290, docs/PUBLISHING.md:419 and MAINTAINING.md:76 all still name it as how to find out which lines the suite never reaches.
NEXT: report. Three things to hand over: this, the red test at HEAD, and the get_ramp fallback (harm unclear).
