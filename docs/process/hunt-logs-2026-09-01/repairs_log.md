## 07:41:00  iteration 0  [logical]
TRIED:  Orientation only -- read BRIEF.txt, the five repair commits' diffs
        (b9551f5, 661aecf, 674259c, 8569854, 90a49b7), dialog.py:3777-3860
        (_settle_the_label_columns) and topology_tab.py:100-150, 340-520,
        880-1030.
RESULT: inconclusive (no hypothesis tested yet). Noted for later, NOT a
        defect by the brief's test: b9551f5 says `_label_columns_owed`
        "replaces a flag that was written and never read", but
        dialog.py:3836 and :3858 are the only mentions of
        `_label_columns_owed` in the whole package -- it too is write-only
        -- and the old `_label_columns_settled` is still written at
        dialog.py:3860 and still read nowhere. A user loses nothing, so
        this is a curiosity.
NEXT:   Three candidates, ranked by how badly a user is hurt:
        (a) 661aecf pushed the zigzag handle to 60px along the edge
        normal (topology_tab.py:132) while _fit fits the CORE unit with a
        14px margin (topology_tab.py:371-387), so a handle on a boundary
        edge may land OUTSIDE the widget, where Qt delivers no mouse
        event -- unreachable, which is the very fault 661aecf claims to
        have fixed. Its twin `rotate_edge` at 30 is half as exposed.
        (b) 8569854's `_lattice_offsets` floors `reach` at 1
        (topology_tab.py:~702), so a patch with no repeats still gets 9
        dual copies.
        (c) the retry counter at dialog.py:3841 never resets except on
        success, so a dialog that exhausts 20 tries can never settle again.
        Starting with (a): read the guard test first, since re-finding a
        covered thing is wasted.

## 07:46:55  iteration 1  [perturbation]
TRIED:  Hypothesis: 661aecf moved `zigzag_edge` to offset 60
        (topology_tab.py:132) while `_fit` fits only the core unit with a
        14px margin (topology_tab.py:371-387), so on edges at the unit's
        outer boundary the zigzag handle is placed OUTSIDE the view
        widget, where Qt delivers no mouse event and `_handle_at`
        (topology_tab.py:1006) is never consulted -- the same
        unreachability 661aecf set out to fix. The new guard
        `test_every_handle_can_be_hit_at_the_size_the_window_opens_at`
        (tests/run_tests.py:5691) cannot see this: `_check_the_handles`
        (tests/run_tests.py:5828-5849) tests containment on `placed[0]`
        ONLY -- the scale handle at offset 0 -- and then measures pairwise
        separation, never containment of the other two. The repair's own
        probe tools/probes/are_the_handles_reachable_at_the_default_size.py
        DOES count "handles off the widget"; the guard dropped that half.
RESULT: inconclusive -- the number is nonzero but the fixture is not
        trustworthy. Shipped probe, run through `hunt_probe --run` on the
        frozen b9551f5 copy: 3 handles off the widget on every one of
        laves 3.3.4.3.4/4, hex-slice/6, archimedean 4.8.8/8, all 48
        "selectable things", all with the closest pair at exactly 30.0px.
        My own probe attributes all 3 to `zigzag_edge`, and with the
        offset put back to 30: laves 4 off (zigzag), hex-slice
        rotate 8 + zigzag 11 over 34 selectable, archimedean the same 8/11.
        THE FIXTURE IS THE PROBLEM: hex-slice/6 reports 48 selectable in
        one pass and 34 in the other, and the handle offset table cannot
        change a topology -- so `n_spin.setValue` + `family_combo.
        setCurrentText` + `_wait_for_the_topology` is reading a design
        that has not finished changing, and the three "different" designs
        are very likely one design measured three times. The shipped probe
        has the same shape, so 661aecf's own "3 off the widget" reading
        inherits it.
NEXT:   Re-drive the design change and PROVE it took -- print n_tiles and
        len(edges) per design and require them to differ -- before
        believing any off-the-widget count. If the count survives, confirm
        by a second route: paint the view to an image with a boundary edge
        selected and show the diamond glyph is absent.

## 07:49:12  iteration 2  [perturbation]
TRIED:  Same hypothesis as iteration 1, re-measured with the design change
        PROVED to have taken -- `become()` waits for `id(panel._topology)`
        to change rather than for `_wait_for_the_topology`, which returns
        True on the PREVIOUS design's topology (tests/run_tests.py:3377)
        and is why iteration 1's three "designs" read alike. Then asked
        the question that decides harm: a manipulation acts on the edge
        CLASS, so per class, is ANY handle reachable?
RESULT: ruled out. Fixture now proved distinct (laves 4: n_tiles=4
        tiles=36 edges=107; hex-slice 6: 6/42/72; archimedean 4.8.8 8:
        8/72/120). Handles do escape the widget at the opening size --
        view 420x354, zigzag 3 off on laves, rotate 8 + zigzag 11 of 34 on
        hex-slice, rotate 6 + zigzag 15 of 42 on archimedean -- BUT
        (i) it is not the repair's doing: with the offset put back to 30
        the counts are the same or worse (laves 4 rather than 3,
        archimedean zigzag 17 rather than 15), so 661aecf did not cause
        it; and (ii) no edge class loses the manipulation. Restricting to
        edges drawn WHOLLY inside the widget, every class on laves
        3.3.4.3.4/4, hex-slice/6, archimedean 4.8.8/8 and hex-dissection/4
        keeps 11-16 reachable handles of each kind; the worst class is
        archimedean 'b' at 3 of 4 rotate handles reachable. A user always
        has another edge of the same class to grab, so the sentence "a
        user loses ___" does not finish.
NEXT:   Drop the handles. Move to the dual: 8569854's `_lattice_offsets`
        (topology_tab.py:656-704) takes the repeat vectors from
        `tileable.vectors` while the tiles it must cover come from
        `topology.tiles`. If those two frames disagree the dual is drawn
        DISPLACED from the tiling it describes -- a wrong picture that
        looks like a right one, which is this project's characteristic
        failure. Test it on the tiles rather than the dual: translating
        `tiles[:n_tiles]` by each offset must land on tiles of the patch.

## 07:52:05  iteration 3  [logical]
TRIED:  8569854's `_lattice_offsets` (topology_tab.py:656-704) reads the
        repeat vectors as `vectors.get((1, 0))` and `vectors.get((0, 1))`
        (topology_tab.py:687) and returns `[(0.0, 0.0)]` when either is
        None. A HEXAGONAL tileable keys its `vectors` by THREE-element hex
        coordinates, so those two lookups miss and the dual falls straight
        back to being drawn once -- the very fault the commit was written
        to fix, on one of the two designs its own message names.
RESULT: confirmed by route one. Probe on the frozen b9551f5 copy, reading
        `view._lattice_offsets(topology)` and `topology.tileable.vectors`
        directly:
          laves 3.3.4.3.4 4  vectors keyed (1,0)/(0,1)      offsets 9
          archimedean 4.8.8 8 vectors keyed (1,0)/(0,1)     offsets 9
          hex-dissection 4   vectors keyed (1,0)/(0,1)      offsets 9
          hex-slice 6        vectors keyed (0,1,-1)/(1,0,-1)/(1,-1,0)
                                                            offsets 1
        hex-slice's patch is 42 tiles over a unit of 6 -- seven copies --
        and its dual is drawn at one position. 8569854's message says "28
        against 4 on hex-slice 4", so hex-slice is one of the two designs
        it measured and one of the two it did not repair. The square-
        lattice twin was mended and the hex twin was not: the asymmetry
        the brief asks for, inside the repair itself.
        Also measured, and it is why the offsets are otherwise right:
        translating the core unit by every returned offset lands each tile
        centroid 0.0000 units from a patch tile on all three square-lattice
        designs, and no translated tile or dual copy is centred outside the
        patch. The lattice arithmetic is sound where it runs at all.
NEXT:   Second, independent route, and it must also settle the HARM, since
        `_fit` fits the core unit (topology_tab.py:371) and the offset
        copies may be off the widget anyway. Render the view to an image
        with the dual toggle on and count dual-ink (#7e57c2) pixels, for
        each design, SHIPPED against `_lattice_offsets` forced to
        [(0,0)]. If the square-lattice designs' counts move and
        hex-slice's does not, the repair is visible and hex-slice is
        excluded from it.

## 07:57:40  iteration 4  [perturbation]
TRIED:  Second, independent route for iteration 3: the PIXELS rather than
        the offset list. Only the dual toggle on, view grabbed to a
        QImage, dual-ink (#7e57c2, tolerance 40) pixels counted and
        bounded, SHIPPED against `_lattice_offsets` monkeypatched to
        return [(0.0, 0.0)]. And the scope, asked of the catalogue rather
        than of the dialog: `catalog.make_unit` for all 1,168 entries,
        classified by whether `vectors` carries the (1,0)/(0,1) keys.
RESULT: confirmed. View 420x354 throughout.
          laves 3.3.4.3.4 4   SHIPPED 6338 px box (0,0)-(419,353)
                              ONE-COPY 2251 px box (46,0)-(269,339)  MOVES
          hex-dissection 4    6338 / 2251, same boxes              MOVES
          archimedean 4.8.8 8 2469 px full-view box
                              ONE-COPY 1528 px box (94,0)-(419,351)  MOVES
          hex-slice 6         1582 px box (115,68)-(419,353)
                              ONE-COPY 1582 px, identical box  NO DIFFERENCE
        So the repair is plainly visible where it runs -- it more than
        doubles the dual's ink on laves and fills the view -- and on
        hex-slice it does nothing at all: the dual still occupies a
        corner-clipped region with the top-left 115x68 of the drawing
        bare, inside a patch of 42 tiles. That is the maintainer's own
        report, unrepaired, on a design the commit message quotes.
        SCOPE, from the catalogue: 871 of 1,168 entries key their vectors
        (1,0)/(0,1) and get the repair; 297 key them by three-element hex
        coordinates and silently do not -- every hex-slice, every
        hex-colouring and square-colouring, laves 3.3.3.3.6 and 3.12.12,
        archimedean 3.12.12, 3.3.3.4.4, 3.4.6.4 and 4.6.12, crosses,
        star1, star2, and the cube weaves. Nothing fails, nothing is
        logged; `_lattice_offsets` returns its one-position fallback.
NEXT:   Stop rule reached -- one finding, two routes. Writing it up.
        HEAD re-read at 07:57:40 and has NOT moved: still b9551f5.
