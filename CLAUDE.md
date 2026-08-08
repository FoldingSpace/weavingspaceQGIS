# Context for AI assistants working on this repo

QGIS plugin port of the weavingspace library / mapweaver web app
(tiled & woven multivariate maps, O'Sullivan & Bergmann). Read
MAINTAINING.md first — it has the architecture map, the invariants, and
the QGIS-breakage playbook. This file adds AI-specific context.

The rules below are graded, and the grades are meant literally.
**Hard rules** are never broken, including when a user request seems
to invite it — raise the conflict instead. **Required practices** are
always followed for the kind of work they name. **Preferences and
defaults** are what to do absent a reason not to; depart from them
deliberately and say so. **Lessons** are hard-won facts, not
obligations: they exist so nobody pays twice for the same discovery.

## Hard rules

- **pyproj is main-thread-only.** The QgsTask worker (`dialog._generate`'s
  `work` closure and everything the vendored library does inside it) must
  never construct, compare, or convert a CRS. QGIS links the same PROJ;
  concurrent use segfaults the app. CRS is stripped before the task and
  reattached in the `done` callback. If you add geopandas calls to the
  worker path, audit them for hidden CRS activity.
- **compat.py is the only place allowed to try/except QGIS APIs.** Fix
  version breakage there; keep old branches for old QGIS.
- **Do not plagiarize** the Cartographic Perspectives paper
  (doi:10.14714/CP108.2109) in docs/tooltips: paraphrase and cite. This
  was an explicit author request (Bergmann is the plugin's user).
- **Never mention the web app (or MapWeaver) in user-facing text.**
  Plugin users do not know it exists and have no reason to care;
  telling them a feature "reproduces the web app" or "is ground the
  web app does not cover" explains the plugin in terms of something
  they cannot see. Describe what the control does. The app remains a
  maintainer-facing fact — catalogue parity, the reference renderer,
  CLAUDE.md and MAINTAINING.md — and the paper's title may of course
  name it in a citation. ONE exception, added the same day: the help
  tab and user guide may name and link MapWeaver among the further
  reading, as another platform for making these maps with the same
  library. Never as an explanation of what a control does.
  (Explicit user instruction, 2026-08-07.)
- **Human-facing prose follows the Bergmann–O'Sullivan voice.** All
  user-facing text (USER-GUIDE.md, help_content.py, tooltips, dialog
  messages, README, docs/index.html) was written through the
  `luke-david-style` skill, which requires reading two files FIRST: a
  forensic profile of the authors' joint voice, and a list of the
  words and structures that make prose read as machine-written. Both
  live in the user's own directory, deliberately outside this
  repository, and are named in .gitignore so a copy cannot be
  committed by accident; ask the user for their location. Run any new
  or edited user-facing prose through the same pipeline; in
  particular, avoid em-dash habits and bullet-heavy structure.
- deps.py must never install numpy 2.x or shadow an adequate
  QGIS-shipped package; wheels extract only into the plugin's `libs/`.
- **Nothing sensitive is ever committed or pushed.** No credentials,
  API keys, tokens, private key material, `.env` files, or anything
  else that would be a problem in public. Machine-specific paths
  (`/Users/<anyone>`) count too: not secret, but they leak a directory
  layout for no reason and mark a file as written for one machine
  rather than for a reader. `tools/check_no_secrets.py` enforces this
  over exactly the files a commit would contain, and `release.py` runs
  it twice — once before the expensive work and once immediately
  before committing, because a leaked key is the single failure a
  later release cannot undo. Entries in its ALLOWED list need a
  written reason, like every other exception here. The private style
  guide governing this project's prose stays outside the repository
  and is named in `.gitignore` so a stray copy cannot arrive by
  accident. (Firm user instruction, 2026-08-07.)
- **GitHub is the only distribution channel.** The repository is
  `FoldingSpace/weavingspaceQGIS` (public); builds reach users as
  GitHub Release assets, and reach the user directly as a chat
  attachment when they ask. Still no claude.ai artifacts, no
  third-party file hosts, no upload services. Pushing happens through
  `release.py --push` or at the user's explicit request, never as a
  side effect of other work: commit and tag are local and reversible,
  a push is neither. (Revised 2026-08-07; the earlier form of this
  rule forbade publishing anywhere at all, which held until the
  repository existed.)
- **Canadian spelling in all user-facing text**: colour, colourmap,
  behaviour, and -ize verbs (symbolize, categorize, organize). Code
  identifiers that mirror a QGIS or matplotlib API keep that API's
  spelling (`colors_to_use`, `setColor`); everything a user reads uses
  the user's spelling.

## Required practices

- **Documentation standard**: all new code carries docstrings and
  section comments written for a weavingspace-literate, QGIS-naive
  maintainer — explain each QGIS/Qt concept at its point of use. This
  is an explicit user requirement; match the density of the existing
  modules. Specifically:
  - document INPUTS AND OUTPUTS, not just purpose: an Args block that
    says what each argument means and what happens when it is
    omitted, a Returns block that says what the caller gets and
    whether anything was mutated, and Raises where a caller could
    reasonably be surprised;
  - say what a value means in this project's terms ("the passing
    pattern as typed, e.g. 1,2,2,1"), not its type alone;
  - add comments in the MIDDLE of longer functions, at the points a
    reader would otherwise stop and wonder — why this order, why this
    guard, why this apparently redundant step;
  - when a choice has a reason that is not obvious from the code
    (thread safety, an upstream semantic, a Qt quirk, a bug this
    prevents), the reason belongs at that line.
- **The standards are ENFORCED at release, not merely intended.**
  `release.py` runs `tools/check_standards.py` before anything else,
  and refuses to build a zip when it fails. It checks what this file
  says: every reachable function and class documented, functions of
  two or more arguments documenting them, no mutation markers left in
  shipped source, no user-facing text explaining anything in terms of
  the web app (links under further reading excepted), Canadian
  spelling in prose, and a mutation catalogue whose entries all name
  tests that still exist. Each of those rules was kept faithfully
  right up until the day it was forgotten; the check exists because
  intentions do not survive a long session. When a rule genuinely
  should change, change it in the checker deliberately — do not
  weaken it to make a release pass.
- **Releases go through `python3 release.py`**; never hand the user a
  zip that did not come out of it (details under "The test suite").
  Every release writes reports/v<version>/testing-report.md listing
  each test individually with its result and measured values; report
  those per-test results to the user whenever something is published
  (an explicit user requirement, 2026-08).
- **A release publishes CONTENT, not only a zip, and the content is
  re-checked every time.** README.md and docs/index.html show the
  dialog and a set of maps; those are claims about how the plugin
  currently looks and what it currently produces, and they rot
  silently. So `release.py` re-photographs them from THIS release's
  gallery (`tools/make_site_images.py`) and then audits every other
  claim the published files make (`tools/sync_release_content.py`):
  the citation version, a changelog entry for this version, images
  that exist and were actually regenerated, relative links that
  resolve, the vendored library version against the stamp the
  vendoring tool wrote, and the repository URLs against metadata.txt.
  Mechanical corrections are applied automatically; anything needing
  words stops the release. Prefer small judicious edits to published
  prose over rewriting it — accumulated small changes are cheaper to
  read than a document that is new every release. (User instruction,
  2026-08-07.)
- **Upstream library updates go through
  `tools/vendor_weavingspace.py`** (details under "The original
  library").
- **Check upstream before running the test suite.** Fetch the
  weavingspace repo, compare its version AND its head commit with what
  we vendor (upstream does not always bump the version string when
  code changes), and OFFER any new version to the user rather than
  taking it silently. Say what actually changed: compare structurally
  (AST with docstrings stripped) so the offer can distinguish a
  licence-header release from a behavioural one. This rule has already
  paid for itself twice — it caught a licence-only bump, and it caught
  upstream adopting our own convex-hull optimisation, which let us
  retire a patch instead of carrying a duplicate of it forever.
  (Standing user instruction, 2026-08-07.)
- **The testing documents are binding, and are read BEFORE tests are
  written or changed.** `docs/TESTING.md` holds the shapes that earn
  their keep here and the lessons each paid for once; nearly every
  rule in it exists because its absence cost this project real time.
  `docs/MUTATION-TESTING.md` holds the campaign and its commitments,
  and `docs/MUTATION-LOOP.md` is the runbook for running that campaign
  again from scratch: how to launch a cycle (`tools/loop/cycle.sh`),
  how to supervise it so the machine is never idle and no watcher goes
  silent or repeats itself (`tools/loop/health.sh`, a stage monitor
  and a ten-minute heartbeat), how to triage a survivor into one of
  five kinds, and when the campaign may be called finished.
  Treat both as you would the hard rules above: when you find yourself
  about to do something they warn against, the document is right and
  the shortcut is not. When one of them turns out to be wrong, change
  the document deliberately and say why, exactly as with the
  standards checker.
- **New code is held to account at every release, not only during a
  campaign.** `release.py` re-records per-test coverage and then runs
  `tools/mutate_auto.py --since <previous tag> --require 70`, which
  mutates ONLY the lines that changed and stops the release if the
  tests written alongside them fail to catch 70% of those mutants.
  Cost is proportional to the change, so it runs every time, which is
  the point: a mutation score decays not through decisions but
  through changes that nobody measured. This does not replace the
  periodic full campaign — changed lines are where new gaps arrive,
  but a refactor elsewhere can quietly stop an old test reaching what
  it names, and only full sampling finds that.
- **Mutation testing has commitments, and they bind.** The full
  reasoning is in `docs/MUTATION-TESTING.md`; what must not be
  forgotten while working: close a survivor with the test the
  BEHAVIOUR deserves, never one aimed at the mutated token, and if
  you cannot state the harm a user would suffer, it is not a gap —
  mark it equivalent (with evidence) or accept it and say why. Prefer
  DELETING a line that does not earn its keep to writing a test that
  defends it. Equivalence claims are demonstrated, not asserted:
  apply the mutation in a sandbox and compare everything a test could
  see, then record the evidence in `EQUIVALENT` in
  `tools/mutate_auto.py`. Keep exclusions narrow and declared in the
  source — the only one is table column widths in pixels, and an
  earlier "pixel geometry" version of it was too broad, since
  geometry in this application usually means the map. Report rates
  per module as well as blended, so deterministic logic cannot hide
  behind Qt plumbing. Certify OUT OF SAMPLE: improvement rounds fix
  what they find, then a final batch runs with the suite frozen, and
  the number quoted is the conservative Clopper–Pearson bound rather
  than the raw fraction. None of this is optional politeness — every
  one of these rules exists because its absence would have let a
  number rise while the software stayed the same.
- **Every test that produces a map checks it visually, and those
  checks appear in the release PDF.** Two shapes: `visual_pair` when
  the settings can be restated independently (render the dialog's map
  beside one built by calling the library directly, compare interior
  pixels), and `visual_gamut` when they cannot (assert every interior
  pixel is a colour the ramps in force can make). A map-producing test
  that only counts features is not finished. (Standing user
  instruction, 2026-08-06.)

## How we decide things

- **Reach for `/grill-me` when a decision carries weight.** Anything
  that changes the UI's shape, the output contract, what gets stored
  in a file, or a rule other work will lean on deserves the
  one-question-at-a-time treatment BEFORE any code is written: look
  the facts up yourself, put each decision to the user with a
  recommendation, and implement nothing until they confirm shared
  understanding. This is the user's stated preference, and the
  sessions that went that way (per-element layer output, the
  categorical colour sources, grid and stripes, layer opacity)
  produced designs that stuck; the ones that skipped it produced work
  that had to be unpicked. Small mechanical changes do not need it.
- **A feature does not have to exist in the web app or the library.**
  The plugin is allowed its own ideas where they fit QGIS: the
  Reverse-ramp column, per-element opacity, grid and stripes, the
  GeoPackage output. The test is whether it fits how QGIS works and
  how this plugin already behaves, not whether it has a precedent
  elsewhere.
- **Prefer the QGIS-native mechanism over a bespoke one — as a
  default, not a law.** When QGIS already models a thing, use its
  model: layer opacity rather than alpha baked into ramp colours,
  standard renderers rather than a plugin styling UI, QgsStyle ramps
  rather than our own palette widget. Native mechanisms round-trip
  through QML and GeoPackage styles for free, survive our own
  re-seeding, and are editable where users already look. TWO things
  override it: an approach the original library already takes (its
  semantics are the reference, and matching them keeps the plugin
  honest about what these maps are), and a plainly better piece of
  interface design that you can argue for. Those overrides are a
  large part of why `/grill-me` exists — the case for departing from
  the QGIS default is exactly the kind of decision to put to the user
  one question at a time, with the trade-off named, rather than
  settling it silently in either direction.

## Lessons learned here (do not relearn these the hard way)

**Qt/QGIS UI.**
- Data & colours handlers must NEVER trigger _rebuild_unit or
  _refresh_table. The rebuild replaces every table cell widget, and a
  rebuild debounced from one chooser pick lands mid-interaction with
  the next ("race among choosers": open dropdowns die, picks commit to
  dead widgets). Data-tab changes go through _refresh_preview_colours;
  a regression test asserts widget *identity* survives the debounce.
- A widget setCellWidget()ed into a hidden column can paint at the
  table's origin; and "blank" cells must be made by *removing* the
  widget, since some render paths paint hidden cell widgets anyway.
- sizeHint is stale before a real layout pass: invalidate child
  layouts and re-measure after showEvent, or you size to phantom rows.
- grab() of a never-shown dialog renders unreliable widget visibility
  offscreen; probe state programmatically, screenshot only after
  show().
- QgsMapLayerComboBox re-emits layerChanged whenever project layers
  churn (i.e. after every generation): its handler must be idempotent
  and guarded (auto-spacing fires once per layer id; outputs are
  tagged with a custom property and excluded so the plugin never
  offers its own output as a region).
- Label anchors: centroid for the visual centre; representative_point
  only as the inside-the-polygon fallback for concave shapes (it comes
  from a bbox-midheight scanline and reads off-centre).

**Testing.** The full record now lives in `docs/TESTING.md`, which is
REQUIRED READING before writing or changing tests, together with
`docs/MUTATION-TESTING.md` for the campaign that keeps the suite
honest. Both are binding, not background. The four that get violated
first, kept here so they are unmissable:
- Tests must run with an EMPTY project. Everything shares the one
  QgsProject singleton, so a test that leaves layers behind changes
  which layer the next dialog picks; a single real failure once
  cascaded into four unrelated ones.
- A test that PASSES is not a test that WORKS. It has to fail when the
  behaviour it names is broken, and the only way to know is to break
  it. Every test written to close a mutation gap gets an entry in
  `tools/mutation_check.py`, which does exactly that and runs at
  release. Six tests written in one session were verified to pass,
  and most of them then failed to kill the very mutants they were
  written for.
- The highest-value shape here is UI-against-library: drive the
  dialog, build the same map by calling weavingspace directly with
  what those settings MEAN, compare geometry element by element and
  then interior pixels. Write the expected side from the settings,
  never from `_build_unit`, or the test agrees with the bug.
- Every test that produces a map checks it visually (`visual_pair` or
  `visual_gamut`), and those checks appear in the release PDF.

**Process.**
- Check upstream's actual semantics before reimplementing behaviour:
  "unclassed" turned out to be matplotlib's linear Normalize (so 50
  equal intervals, not a new scheme), and categorical colours follow
  ListedColormap's sampling: code/(k-1) mapped through int(x*N),
  clamped — 5 on tab10 = entries 0,2,5,7,9. An earlier "derivation"
  used round() and got 0,2,4,7,9, painting the middle category purple
  instead of brown; only the colourspace comparison against an actual
  upstream render caught it. The reference is upstream's *rendered
  output*, not upstream's code read in a hurry, and certainly not
  intuition.
- After changing behaviour, re-audit nearby docstrings: this project's
  standard makes stale documentation actively harmful, and an audit
  found three lies (libs "appended", live update "after first
  Generate", the removed shared-file box).
- When batch-editing via heredoc Python scripts: assert every anchor
  BEFORE any write, and beware a trailing comma turning a string into
  a tuple (it aborted two patch runs here); for single replacements
  prefer the Edit tool.
- When waiting on a long background run, key the wait on the PROCESS
  ENDING, not on log text you predicted. A watcher polling for "tests
  recorded" sat in a sleep loop for twelve hours because the tool
  actually prints "recorded 75 tests", and its fallback pattern
  ("Error") missed the crash line too, which read "Fatal Python
  error". Silence from a watcher is not evidence that the work is
  still running. Wait on the pid, and if a log must be matched,
  include a case-insensitive alternation broad enough to catch the
  failure modes as well as the success line.
- A watcher that REPEATS itself misleads as badly as one that goes
  silent: a monitor grepping a whole log each pass re-reported the
  same historical failure every 45 seconds as though it were news,
  which makes the current state unreadable. Track an offset per file
  and emit only what is new. Between this and the twelve-hour poll
  above, the rule is: a watcher must report change, not state.
- macOS code-signing (library validation) refuses PyPI C extensions
  inside the signed QGIS process; side tooling that needs matplotlib
  runs in .venv-reference, never in QGIS's Python.

## Testing (do this after every substantive change)

Self-contained suite, synthetic data, runs under QGIS's bundled Python:

    bash tests/run_tests_macos.sh          # macOS, auto-detects the app

On this project's dev machine QGIS 4.0.3 lives at
`/Applications/QGIS-final-4_0_3.app` (vcpkg build, Python 3.12,
`PYTHONHOME=Contents/Frameworks`, `PROJ_LIB=Contents/Resources/qgis/proj`,
`QT_QPA_PLATFORM=offscreen` works headless).

Dialog tests run offscreen with a stub iface (see `tests/run_tests.py`);
QMessageBox popups block headless runs, so live/silent code paths exist —
don't add unconditional modal dialogs to generation paths.

## Design decisions already settled (don't relitigate silently)

Confirmed with the user via an explicit design review:
- One layer per tile element in a layer-tree group; the old single-layer
  rule-based renderer output was deliberately removed.
- Generate replaces the group in place; hand styling survives unless
  that element's dialog assignment changed (signature comparison in
  `dialog._add_output_layers`). "Create as new group" is the comparison
  escape hatch.
- Renderers are seeded standard QGIS objects (graduated/categorized/
  single); refinement belongs to QGIS's styling dock, not a plugin UI.
- Ramps come from QgsStyle; missing mapweaver palettes are installed
  into it once, tagged "mapweaver" (additive only).
- Optional GPKG output embeds styles; live update renders a first map
  as soon as a layer and variables are in place (no button press) and
  is gated: memory-mode output only, estimated tiles ≤
  LIVE_UPDATE_MAX_TILES, and no-op runs skipped via _run_signature.
- Preview shows the bare tile unit by default (shells=0) with subtle
  centroid-anchored tile-id labels, like the web app's design view.
- "Quant: Unclassed" (50 linear intervals) is the sanctioned
  reproduction of a continuous ramp — derived from upstream semantics
  (n_classes=0 → matplotlib linear Normalize), not invented; see
  bridge.make_graduated_renderer.
- A style-only change NEVER re-tiles. `_geometry_signature()` decides:
  when it is unchanged, `_restyle_only()` re-seeds the existing layers
  in place. Ramp, scheme, class count, single colour, class source,
  reversal and opacity are all symbology; family, spacing, modifiers,
  switches, region layer, output path and the set of mapped variables
  are geometry. "Create as new group" always takes the full path.
- One run at a time, and the run is not over until its layers exist.
  `_finish_run()` clears the task only after `_add_output_layers`,
  because output building is main-thread work that a queued live run
  would otherwise start a second tiling underneath.
- Per-element colour controls sit in the table and belong to the
  ELEMENT, not the row widget: ramp, Reverse, class source, single
  colour and opacity all survive table rebuilds through dicts keyed by
  tile id. Columns appear only while they mean something (Classes
  whenever any row has a class count, including greyed categorical
  counts; Reverse while any element has a ramp).
- An element left on "---" stays unassigned through rebuilds and draws
  as plain fill. Class counts for quantitative styles run 2–20 (the
  ceiling is ours; the app has no such control at all).
- The region-outlines layer is drawn cased, a wide white line under a
  narrow black one, so boundaries stay legible over pale and dark
  parts of the pattern alike.
- The repository is public at `FoldingSpace/weavingspaceQGIS`, with
  the project page served by GitHub Pages from `docs/` on the main
  branch (so a single push updates code, documentation and page
  together). `reports/`, `dist/` and `.venv-reference/` are NOT
  committed: reports run to tens of megabytes per version and git
  keeps every blob forever, so each release attaches its report, PDF
  and zip to a GitHub Release instead. Copyright on the plugin is
  Luke Bergmann's, with the vendored library's own MIT notice
  reproduced separately in LICENSE.md; `metadata.txt` names Bergmann
  alone as author, since plugin bug reports should reach whoever can
  act on them. `deps.py`'s PyPI download is disclosed plainly in the
  metadata, the README and the page rather than left to be
  discovered, which is also what the QGIS plugin repository's
  reviewers will want to see.

## Cross-version compatibility targets

QGIS 4+ only (PyQt6, Python 3.12+), on the major platforms. Enums in
scoped form (`Qt.AlignmentFlag.AlignCenter`); `QAction` imports from
qgis.PyQt.QtWidgets (QGIS 4 shims it there). compat.py holds the QGIS
4 spellings and absorbs future transitions.

## The original library: its role and how to upgrade it

The vendored `weavingspace_qgis/vendor/weavingspace/` (upstream
v0.0.7.61) does ALL the mathematics and cartography — unit
construction, tiling geometries, weave matrices, transforms, and
`Tiling.get_tiled_map()`'s grid/overlay/join. Plugin code never
computes a tiling; it is the QGIS shell around that library
(parameters in, GeoDataFrame⇄layer conversion, symbology, threading,
guards). Keep that boundary: behaviour that belongs to the tiling
belongs upstream, and where the plugin must reproduce an upstream
behaviour in QGIS terms (unclassed ramps, categorical colour
sampling), derive it from upstream's actual semantics and document the
derivation at the implementation.

Upgrading upstream is a script, not a project:

    python3 tools/vendor_weavingspace.py /path/to/weavingspace/weavingspace
    python3 release.py

The tool copies the new upstream and re-applies the remaining patch
family (optional matplotlib/scipy imports), asserting on exact
upstream anchors and NAMING any
patch whose anchor no longer matches instead of writing a broken
vendor. Never hand-edit vendor files: a hand edit is lost at the next
re-vendor. New patches go into the tool, documented like the existing
ones. The catalogue in `catalog.py` holds the web app's
`tilings_by_n` dict verbatim (mapweaver repo, app.py) PLUS two
sanctioned library extras appended by a loop after the literal
(stripes, grid — user-approved 2026-08-06; users are deliberately
NOT told which families the app lacks). When syncing against a new
app release, update the literal only and leave the loop alone.
The custom ("this") weave type, with its tie-up/treadling/threading
matrices, is DEPRIORITIZED rather than rejected: it needs a
matrix-entry UI and its own documentation, and the user may return to
it.

## QGIS breaking changes: the playbook

A future QGIS transition (4→5, as 3→4 before it) WILL break APIs. The
standing arrangement: every version-sensitive QGIS/Qt call goes
through `compat.py` (nothing else may try/except a QGIS API), which
currently holds plain QGIS 4 spellings. When breakage arrives: run the
test suite under the new QGIS — the first failing test names the
broken area — then add a fallback branch to the relevant compat
helper, keeping the old branch and noting the QGIS version in its
docstring. If something breaks outside compat.py, moving that call
into compat.py is part of the fix. Likely fracture points are listed
in MAINTAINING.md (enum access, QgsField construction,
QgsVectorFileWriter options, saveStyleToDatabase, classification class
names, qgis.PyQt shims).

## The test suite: what it is for and how it runs

Six pieces, all modern Python (the functional suite, visual gallery
and mutation campaigns run under QGIS's bundled 3.12; the reference
comparison in `.venv-reference`, Python 3.14). The first two are the
tests themselves; the rest ask how good those tests are:

1. `tests/run_tests.py` — the regression record of every bug this
   project has fixed (PROJ threading, size guard, auto-render, chooser
   race, spacing persistence, per-row symbology, GPKG round trips).
   Every fixed bug gets a test here; a bug without a regression test
   is not fixed.
2. `tests/visual_tests.py` — canonical weavingspace outputs rendered
   through the plugin pipeline, with coarse image checks plus CIELAB
   distance-to-ramp criteria, writing reports/v<version>/index.html.
3. `tools/coverage_report.py` — which plugin lines the functional
   suite never reaches (stdlib `sys.monitoring`, since PyPI packages
   cannot load in the signed QGIS process). Reported in every
   release, never gating.
4. `tools/mutation_check.py` — breaks each guarded behaviour in turn
   and requires its test to fail. Not part of the release gate (it
   rewrites source files); run it before substantial releases.
5. `tools/mutate_auto.py` — the same question asked without a human
   choosing the targets: mutants generated from the syntax tree,
   sampled at random, each run against only the tests that cover its
   line, inside a throwaway clone. This is the MEASUREMENT (the
   hand-picked catalogue measures our judgement); its commitments and
   campaign history are in `docs/MUTATION-TESTING.md`.
6. `tools/visual_reference_report.py` — each gallery render scored in
   Lab colourspace (pixel-weighted nearest-neighbour ΔE both
   directions, p90, background fraction) against the ORIGINAL
   renderer, `TiledMap.render`, on identical inputs; where quantile
   classing alone explains a mismatch, the gallery's Quant: Unclassed
   render is scored instead. Writes visual-comparison.pdf.

The suite, the gallery, the coverage report and the reference
comparison run, in order and gated, via `python3 release.py`, which
refuses to build the zip on any failure and leaves the HTML report and
the PDF under reports/v<version>/. Around them sit the publication
steps, in this order: standards check, secrets audit, the four test
stages above, the testing report, a re-photographing of the published
images, the published-content audit, the zip, then commit and tag —
and, with `--push` only, the push and the GitHub Release with the zip,
testing report and PDF attached. `--push` is the single point at which
anything leaves the machine. Rerun the comparison alone with
`./.venv-reference/bin/python3 tools/visual_reference_report.py
reports/v<version>/` after a gallery run has populated the PNGs.

On "three-way" comparison (library vs web app vs plugin): the PDF's
reference column IS both of the first two at once, because MapWeaver
pins this same library version and draws through this same
TiledMap.render call inside pyodide — a browser screenshot would
re-photograph the identical code path with UI chrome added, so no
separate column exists. CONDITION TO WATCH, now triggered but harmless: as of 2026-08-07 the
vendor is 0.0.7.61 while the app still pins 0.0.7.59. The two were
compared structurally (AST with docstrings stripped) before the
bump: 0.0.7.61 adds MIT licence headers and NOTHING else, so the
rendering path is byte-for-byte the same behaviour and the single
reference column still speaks for both. Re-check with the same AST
comparison at the next upstream bump; if a release ever changes
behaviour while the app lags, a live browser capture becomes a
genuinely independent third column and should be added then.
