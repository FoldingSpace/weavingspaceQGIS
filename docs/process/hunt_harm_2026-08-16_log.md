# Hunt log: backwards from harm, whole plugin, 2026-08-16

Brief: `python3 tools/bug_hunt_brief.py --shape harm` is not a known
shape (choices are asymmetry, one-boundary, two-stores, unreachable,
write-only). Closest to "backwards from harm" is **one-boundary** —
"the richest defects here live where something is written out and read
back" — so the brief was generated as

    python3 tools/bug_hunt_brief.py --shape one-boundary --area "the whole plugin"

and read in full. The DIRECTION followed is the one given in the task:
start from the user's losses, not from the code.

Frozen tree: `/var/folders/93/3nql803d21v_t9n6f1n8w6000000gn/T/weavingspace-hunt/tree`
at **7bd34a6**, re-frozen at **3b34364** when HEAD moved mid-run.

## The ranked list of harms, written before any of them was tested

Ordered by what I would guess costs the user most, worst first. The
record says not to trust this ordering — the GeoPackage data loss was
ranked thirteenth of eighteen by the hunt that found it — so the plan
is to test from BOTH ends and to spend most of the budget on the ones
I believe are safe.

**Their data on disk.**

1. The output GeoPackage is an existing file holding other tables, and
   writing the map destroys them. (Known, fixed once; test whether the
   guard covers every door — QML/style writing, cancel, live update.)
2. The output path names the REGION LAYER'S OWN FILE, so tiling a
   layer destroys the layer being tiled. Second door into (1).
3. Two elements resolve to the same table name inside one GeoPackage,
   so the later silently replaces the earlier and one variable is gone
   from the file though the map on screen shows it.
4. A run that fails or is cancelled part-way leaves a TRUNCATED output
   file where a complete earlier one was.
5. The null workaround sets a subset string on a layer and an
   exception on the way through leaves it set, so a user's layer looks
   like it lost most of its features.
6. Writing a style to disk (QML export / saveStyleToDatabase)
   overwrites a hand-written .qml or a style the user saved.

**Their styling work and their project.**

7. Generate replaces the output group IN PLACE, so anything the user
   put inside that group themselves — an annotation layer, a copy of
   the region, a reordered child — is removed with it.
8. Live update fires unasked and destroys hand styling that a full
   Generate would have preserved (signature comparison).
9. A hand-picked colour / pinned bound made while a run is in flight
   is destroyed at the landing. (Known shape, fixed three times; test
   the newest writer.)
10. A project saved and reopened loses something the dialog claims
    persists (custom properties absent, tags missing so plugin output
    is offered as a region layer and the next map tiles on itself).

**Their time.**

11. A design whose tile count is enormous runs for many minutes and
    then refuses, or produces nothing, with no earlier warning.
12. Live update starts an expensive run behind the user's back on a
    source it cannot count.

**Their trust — a map that is wrong but looks right.**

13. Class breaks or category colours computed from one thing and drawn
    from another, so one colour means two values.
14. The legend disagrees with the pixels (swatches for classes no tile
    uses; hatching that is a run behind).
15. An element silently draws flat fill because a guard upstream
    rejected it, and nothing says so.
16. The output GeoPackage, reopened elsewhere, draws differently from
    what the user saw (styles not embedded, breaks recomputed).
17. CRS: a memory layer with no CRS shipped as EPSG:4326, or the
    spacing re-derived wrongly after a CRS change.

I believe 1-6 are the expensive ones and I believe 1, 2, 5 and 7 are
already guarded. Those four are therefore where I will start.

## 18:12:11  iteration 1
TRIED:  harm 1/2 read forward only — the file-recreation door is closed
        at dialog.py:7108 (`first=(first_gpkg_layer and not
        os.path.exists(path))`), and drop_gpkg_layer (bridge.py:2338)
        removes only tables in `self._gpkg_tables_written[path]`
        (dialog.py:7284), so the known GeoPackage loss is fixed at
        7bd34a6 and its stale-table twin is narrow.
RESULT: ruled out (by reading, not yet by probe) for the case the
        suite already covers. BUT the only guard that WARNS about an
        output file holding data is dialog.py:6227-6235, and it fires
        on `self.opt_new_group.isChecked() and path_now ==
        self._last_path`. `_last_path` is set only at dialog.py:7288
        after a successful run and initialised None at dialog.py:858 —
        it is not restored from a project. So the warning cannot fire
        on a file this dialog has not already written in this session.
NEXT:   probe the door the warning cannot see: an existing GeoPackage
        holding an EARLIER map's tiles_* tables (previous session, or
        a second file the user alternates with) chosen as the output.
        If those tables are replaced with no warning, the user's
        previous map is destroyed on disk and the layers still open on
        it silently show the new one.

## 18:13:33  iteration 2
TRIED:  a Generate into a .gpkg holding an earlier map's tiles_a /
        tiles_b (probe p_prevmap.py, dialog.py:7108).
RESULT: confirmed as MECHANISM, not yet as defect. ACTUAL VALUES:
        before {site_boundaries:9, tiles_a:9, tiles_b:9}; after
        {site_boundaries:9, tiles_a:55, tiles_b:55, tiles_c:55,
        tiles_d:55, layer_styles:4}. site_boundaries intact (the known
        fix holds). tiles_a/tiles_b replaced, fields changed from
        (v1,v2,v3,landcover) to (tile_id,prototile_id,v1,v2,v3). No
        warning, no note ("note line:" empty). `_last_path` was None.
        NOTE: HEAD moved under me between --prepare (7bd34a6) and this
        run; the harness re-froze at 3b34364. The diff is
        docs/process/HUNT-RECORD.md only, no plugin source.
NEXT:   replacing tiles_* on the ordinary path is the DESIGNED
        "Generate replaces the group in place". The sharp case is
        "Create as new group", where the plugin refuses this at
        dialog.py:6227 in as many words. Test that same refusal on a
        FRESH dialog (a reopened project), which is the ordinary way a
        user returns to yesterday's map.

## 18:14:31  iteration 3
TRIED:  "Create as new group" on a FRESH dialog (a reopened project)
        pointed at the GeoPackage yesterday's map is in — the case
        dialog.py:6227's warning is written for but cannot see, because
        it compares against `self._last_path` (dialog.py:858, 7288).
        Probe p_newgroup.py.
RESULT: confirmed. ACTUAL VALUES: Monday's run (spacing 900, v1) wrote
        tiles_a=25, tiles_b=24, tiles_c=25, tiles_d=24. A fresh dialog
        (`_last_path: None`) with opt_new_group CHECKED, spacing 500,
        v2, into the same file: tiles_a..d all 78. No warning, note
        line empty. Groups now ['WeavingSpace tiles 2',
        'WeavingSpace tiles'] — two groups, ONE map, because both read
        the same four tables. Monday's own layer objects still report
        25/24/25/24 from cache, so the layer panel shows a map that is
        no longer in the file.
NEXT:   confirm by a second route (reload the stale layers; and the
        in-session door: new group + a DIFFERENT existing .gpkg), and
        find when it started with `git log -S`.

## 18:16:20  iteration 4
TRIED:  two second routes for iteration 3 (probe p_confirm.py): reload
        the stale layer, and the IN-SESSION door (one dialog: Generate
        into A, then tick "Create as new group" and point at B, an
        existing .gpkg holding an earlier map — dialog.py:6229 compares
        B against `_last_path` = A and says nothing).
RESULT: confirmed. B before {tiles_a:25, tiles_b:24, tiles_c:25,
        tiles_d:24}; B after {113, 112, 113, 112}. Note line empty, no
        warning. Second route on the panel: the surviving layer object
        reports featureCount() 25, and after `.reload()` reports 113 —
        same source `b.gpkg|layername=tiles_a`. So the layer panel
        shows a map the file no longer holds until something reloads
        it, which is the same "featureCount from cache" mechanism the
        original GeoPackage defect's own test docstring names.
        `git log -S "You asked to keep the previous result"` and
        `-S opt_new_group`: both land on 3bd5f52, the initial commit.
NEXT:   the same session-only-record shape has a second consequence:
        `_gpkg_tables_written` (dialog.py:865) is the record that lets
        drop_gpkg_layer clear a shrunken design's dead tables. It is
        also memory-only. Test a 7-element map then a 3-element map
        across a reopen.

## 18:16:55  iteration 5
TRIED:  a seven-element design written to a .gpkg, then a three-element
        design into the same file from a FRESH dialog (probe
        p_stale.py, dialog.py:7284).
RESULT: confirmed. Monday wrote tiles_a..tiles_g (27,27,27,26,27,27,27)
        and the record held ['a'..'g']. A fresh dialog's record is {}.
        Tuesday's three-element run left the file holding tiles_a..g —
        DEAD tables tiles_d, tiles_e, tiles_f, tiles_g, plus
        layer_styles still at 7, so all seven open symbolized. NEGATIVE
        CONTROL in the same probe: the identical shrink inside ONE
        dialog leaves exactly ['layer_styles','tiles_a','tiles_b',
        'tiles_c']. So the drop works and only the record does not
        survive a reopen. This is the exact harm drop_gpkg_layer's own
        docstring (bridge.py:2356-2360) says it exists to prevent.
NEXT:   check what the file widget itself warns, so the severity claim
        is honest.

## 18:17:20  iteration 6
TRIED:  does QgsFileWidget warn on an existing file (probe p_widget.py)?
RESULT: ruled out as a defence for finding 2 and a partial one for
        finding 1. storageMode 3 (SaveFile), confirmOverwrite True,
        lineEdit readOnly False. So BROWSING to an existing file pops
        the system "already exists — replace it?" prompt, and TYPING or
        pasting a path pops nothing. Two consequences. Finding 1's
        doors are reachable without any prompt only by typing a path;
        with a browse the user is asked, though what they are asked is
        whether to replace the FILE, which is not what happens. Finding
        2 is made WORSE by that prompt, not better: the user agreed to
        replace the file and got four styled tables of a dead design
        left inside it.
NEXT:   re-read HEAD and report.

## 18:17:41  iteration 7 (housekeeping, and an admission)
TRIED:  re-reading HEAD before reporting, as the brief requires.
RESULT: HEAD is 3b34364, the same commit the last four probes ran
        against. It moved ONCE under this hunt, from 7bd34a6 to
        3b34364 between `--prepare` and the first `--run`; the harness
        re-froze and every measurement above is from 3b34364. The diff
        is docs/process/HUNT-RECORD.md only — no plugin source — so
        nothing here is a fix landing mid-run.
        THE ADMISSION, since the brief asks for it: the entries for
        iterations 4 and 5 were both written at 18:17:20, after both
        probes had run, and their `## HH:MM:SS` times (18:16:20,
        18:16:55) are when the work happened rather than when the
        entry was typed. The hypotheses themselves were written down
        first, in the preceding NEXT lines. Iterations 1, 2, 3, 6 and
        this one were logged at the clock time shown.
NEXT:   report. Two findings, one root cause: two records that decide
        what happens to a FILE (`_last_path`, `_gpkg_tables_written`)
        live only in the dialog instance, and a file outlives a
        session.
