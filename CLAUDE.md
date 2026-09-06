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

THE FULL ACCOUNTS ARE IN `CLAUDE-archived.md`, and an entry here that
ends in a bracketed id (C-17) has its episode there: what was measured,
what was tried first, what the superseded form of a rule was. You do not
need to read it to work. Read it when an id is quoted at you, when a
rule surprises you and you want to know what it cost, or before you
change one. The pass that keeps the two apart is docs/DOC-ARCHIVING.md.

## How to add to this file

This file is read whole at the start of every session, so it is kept
short by a line budget and a SHAPE that `tools/doc_archive.py` checks
at every push and release. The shape is what makes the cheap edit the
right one; to add to the file:

1. DECIDE WHAT KIND OF THING YOU HAVE. A rule never to be broken goes
   under Hard rules; a way of working under Required practices; a
   decision the maintainer made under Design decisions, with its whole
   statement; a fact paid for once under the Lessons THEME it belongs
   to. Nothing goes at the end of the file, and nothing gets a section
   of its own.
2. WRITE IT AS ONE CLAUSE IN THE ENTRY IT EXTENDS, with about one
   clause of evidence -- "a name a user can edit is never a key (C-16)".
   Do not open with a date, and do not narrate: the day, the wrong
   first hypothesis and the measurement are the ACCOUNT.
3. MINT AN ID FOR THE ACCOUNT, `python3 tools/doc_archive.py --mint C
   "title"`, write the account under it in CLAUDE-archived.md, and end
   the clause with the id. The check refuses a stub nothing quotes.
4. WHERE NO THEME FITS, put the clause under "Inbox: lessons not yet
   themed", which holds six at most. Folding the inbox into the themes
   is the whole of the pass, and it is cheap while the inbox is small.

A new section, an entry past sixty lines, an inbox past six, or an
entry that opens with a date fails `tools/check_standards.py` with the
fix in the message. When a rule changes, change it where it stands and
move its superseded form to the archive; ids are never renumbered or
reused. (Maintainer's ask, 2026-09-05: the documents are to be
self-fixing at low cost for whoever edits them next.)

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
  Plugin users cannot see it, so explaining a control in its terms
  explains nothing. Two sanctioned uses: the help tab and user guide
  may name and link MapWeaver among further reading, and README.md and
  docs/index.html may say where the plugin came from (provenance is
  not explanation). `check_standards` greps for `web app` and
  `MapWeaver`, so the provenance sentence passes by its wording; if the
  rule is tightened, declare the exemption in the checker in the same
  commit. (Explicit user instruction, 2026-08-07; C-269.)
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
- **EVERY ARTEFACT CARRIES ITS VERSION IN ITS NAME, in `dist/` and on
  GitHub alike, and NO CHECK MAY WRITE INTO `dist/`.** (Maintainer's
  rule, 2026-08-29, on finding the newest file in `dist/` was an
  unversioned zip.) Two halves, and the first is the one that bites:
  `check_before_push` replays CI's packaging step, so the PUSH GATE
  mutates `dist/` from an ungated tree every time anybody runs it. The
  measurement that day, and the ruling that the README follows the
  artefact rather than the other way round: C-1.
- **EVERYTHING FOR THIS PROJECT LIVES INSIDE THE PROJECT DIRECTORY,
  worktrees included.** (Maintainer's rule, 2026-08-29: the scratch
  folder is shared by everyone.) Retire a worktree when its work is
  merged or abandoned; removing a worktree does not delete its branch,
  which is what makes that safe, since `check_roadmap --merge` looks
  for `for-<version>/*` branches. Carry `dev/`, `dist/` and `reports/`
  across by hand when moving a live tree, since git protects none of
  them. (C-270.)
- **User-facing documentation is clear and concise.** Say what the
  control does and what the user should know about it, then stop. The
  guide and help tab are reference material somebody reads while
  trying to finish a map, not an argument for the technique; the
  reasoning belongs in the article, and the maintainer's reasoning
  belongs in docstrings. This applies to new sections and to edits of
  old ones. (User instruction, 2026-08-08.)
- **Tooltips are VERY SHORT: fifteen words at most, usually under
  twelve.** A tooltip is a nudge at the point of use, not a paragraph
  in a yellow box; the user guide and the Help tab carry the fuller
  explanation and both already exist. Enforced by
  `test_every_control_explains_itself`, which also requires every
  control to HAVE one (the README promises it) and rejects a tooltip
  of one or two words that merely repeats the label. The rule arrived
  after twenty of the thirty-six tooltips there were THEN had drifted
  to between nineteen
  and sixty-one words. (User instruction, 2026-08-09.)
- **When writing about VISUALIZATION, say "display", never "wear".**
  An area DISPLAYS an icon; a tile DISPLAYS a class colour. The
  metaphor had spread through this project's own prose and reached a
  user once, in the icon-mode notice, where the maintainer ruled it
  out. It binds new prose; the internal uses are not swept. (Maintainer's
  rule, 2026-08-19; C-271.)
- **Canadian spelling in all user-facing text**: colour, colourmap,
  behaviour, and -ize verbs (symbolize, categorize, organize). Code
  identifiers that mirror a QGIS or matplotlib API keep that API's
  spelling (`colors_to_use`, `setColor`); everything a user reads uses
  the user's spelling.

## Required practices

- **A DAY THAT FINDS MANY DEFECTS GETS A LEDGER, and the ledger is
  COMMITTED.** `docs/process/defects-2026-08-17.md` is the model: one
  row per defect with what a user lost, where it lives, and an OWES
  column naming which of test-and-catalogue-entry it still lacks. It
  exists because ROADMAP.md holds only what is outstanding, the
  handover is rewritten every session, and a conversation ends -- so a
  fix without a guard is invisible everywhere else and reads as
  finished. Write it past about ten defects in a session. (C-272.)
- **WHEN A ROUND OF HUNTS IS PROPOSED, THE CONSISTENCY SWEEP IS
  PROPOSED BESIDE IT, WITH A REASON FOR CHOOSING ONE.** (Maintainer's
  instruction, 2026-08-26: the creativity offered once must be on offer
  again in the rc process, alongside the hunts rather than instead of
  them.) Every rc round so far has reached for hunts by default, and
  the record says that is right only when the ground is FRESH. THE
  ALTERNATIVE IS TO ENUMERATE WHAT HUNTS SAMPLE: three invariants that
  need no oracle and leave no claim to judge -- AGREEMENT (every store
  holding a fact agrees about it), COLLATERAL (an act about one element
  moves no other), and RETURN (doing a thing and undoing it comes
  back) -- run by `python3 tools/consistency_sweep.py`. The costs on
  both sides, and the sweep's first findings: C-2, and
  docs/process/HUNT-RECORD.md under "WHAT TO RUN INSTEAD OF A HUNT".
  Hunts keep the directions that cannot pattern-match, which is what
  the portfolio rule already reserves a third of a round for.
- **Documentation standard**: every module, class and non-trivial
  function this project writes -- the package, `tools/`, `tests/`,
  `build.py`, `release.py`; `vendor/` alone excluded -- carries a
  docstring for a weavingspace-literate, QGIS-naive maintainer: an
  Args block saying what each argument means and what omitting it
  does, a Returns block saying what the caller gets and what was
  mutated, Raises where a caller could be surprised, and the reason for
  any non-obvious choice at the line it is made. The checker enforces
  it. What a docstring does NOT carry is the account -- the day, the
  first attempt, the measurement -- which goes to
  docs/DOCSTRINGS-archived.md under a minted D-id the docstring
  quotes; the archiving check reads the package as that archive's
  live half. (User instruction, 2026-08-09; C-273.)
- **Generated documents are regenerated, never remembered.**
  `docs/TEST-MAP.md` and `docs/BUG-REGISTER.md` come from the suite,
  are never hand-edited, and are regenerated whenever a test is added,
  removed or renamed:

      python3 tools/test_map.py
      python3 tools/bug_register.py

  `tools/check_standards.py` recounts both and fails on a stale count,
  so a complaint from it means run the two commands, not edit a
  number. (Enforced 2026-08-09; C-274.)
- **A BINDING DOCUMENT IS SPLIT IN TWO, AND THE SPLIT IS PART OF
  UPDATING IT.** (Maintainer's instruction, 2026-09-05.) The live half
  keeps the RULE plus about one clause of evidence; `<NAME>-archived.md`
  keeps the ACCOUNT under an id the live half quotes (`C-`, `M-`,
  `R-`, `T-`, `P-`). A ruling keeps its whole statement, a procedure
  every step, a debt whatever names it. The rule is usually the LAST
  sentence of an entry, so read to the end before cutting; when you
  append a long account, split it as you write it. Nothing is deleted
  and ids are never renumbered. `python3 tools/doc_archive.py` checks
  the pairing and the line budgets and runs in `check_standards`;
  `--stranded` reports rules a pass took by mistake, and `--mint`
  takes the next id and writes the stub. ROADMAP.md's outstanding
  entries and MAINTAINING.md's architecture are exempt from the
  budget. Since 2026-09-05 the SHAPE of growth is checked as well --
  the how-to-add block, fixed sections, a capped inbox, an entry cap
  and no date-led entries -- so the standards gate teaches the split at
  the moment somebody departs from it. Procedure:
  docs/DOC-ARCHIVING.md. (C-275.)
- **Text review is the USER'S act, never the assistant's.** The
  `tools/text_review.py` queue exists so a person reads every sentence
  a user will meet before it ships; an assistant approving its own
  prose defeats the tool's entire purpose, however carefully that
  prose was written. Generate the delta, present it, and wait.
  `--apply` and `--approve` run only on the user's say-so, and an
  approval made in error is undone with
  `git checkout -- docs/text-approved.json`. (User correction,
  2026-08-09, after the assistant approved its own five strings.)
- **The standards are ENFORCED at release, not merely intended.**
  `release.py` runs `tools/check_roadmap.py --merge` first and
  `tools/check_standards.py` immediately after,
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
- **EVERY CANDIDATE IS PUBLISHED TO GITHUB AS A PRE-RELEASE**, with
  `python3 tools/publish_candidate.py --notes <file>`: a tag on the
  candidate's own commit, a release marked pre-release so it never
  becomes Latest, carrying the zip, the per-test report and the
  comparison PDF. It refuses without a receipt matching the tree, on a
  taken tag, with CI not green on that commit, or without notes;
  `--despite-ci <reason>` prints the reason in the release. A RELEASE
  -- tagging on `main` -- stays the maintainer's explicit call.
  (Maintainer's instruction, 2026-08-21; C-3, C-276.)
- **The pre-candidate push is PART of the release process, not a
  separate permission.** Once the tree is ready, the sequence runs
  without asking: merge, regenerate the derived documents, secrets
  check, push `pre-<version>rc<n>`, arm the CI watcher, start
  `release.py --rc`. Ask only if the process is INTERRUPTED --
  a gate goes red, CI reports something needing a decision, or the
  tree is not in the state the procedure assumes. Pushing to
  `main`, tagging, and publishing a release remain the user's
  explicit call. (User instruction, 2026-08-10.)
- **After a release, the next version is the PATCH by default.**
  N.X.Y is followed by work toward N.X.(Y+1): 0.24.2 leads to
  `pre-0.24.3rc1` and a version bumped to 0.24.3, never 0.25.0 unless
  the maintainer says so. What follows a release is mostly the triage
  of what it did not fix, which is patch-shaped work; reaching for a
  minor bump by default claims a release is bigger than it is, and the
  claim gets made by whoever types the branch name at the end of a
  long session. Details in docs/PUBLISHING.md. (User instruction,
  2026-08-14.)
- **Work for a LATER version lives on a `for-<version>/<slug>` branch,
  and everything a version owes is in ROADMAP.md**, code or not.
  `tools/check_roadmap.py --merge` is the first stage of every
  release: it merges branches due for the version, refuses while the
  section lists outstanding work, and stops on a conflict. Deferring
  an entry is the maintainer's act, made by moving it; delete an entry
  when it lands. (User instruction, 2026-08-11; C-277.)
- **THE PLATFORM QUESTIONS RUN FIRST ON EVERY CI LEG.**
  `tools/platform_probe.py` holds the tests whose verdict is decided
  by the machine -- font metrics, locale, how a window is assembled --
  and takes seconds where the suite takes an hour (C-4). Nothing moves
  out of the suite into it, and its list lives in the tool rather than
  in `ci.yml`, so a name that no longer exists fails rather than
  skips. (C-278.)
- **EVERY CI PLATFORM IS KEPT AS CLOSE TO THE LOCAL SUITE AS
  PRACTICAL.** Linux, Windows and macOS alike: the standard is PARITY
  OF COVERAGE with what this machine runs, not the existence of a job.
  A platform that only proves the plugin loads has been smoke-tested
  rather than tested -- and `compat.py` exists precisely because QGIS
  moves its APIs, so the functional suite, the visual gallery and the
  colourspace comparison belong on every platform CI can reach.
  Windows is where most of this plugin's users are, and until
  2026-08-15 it ran nothing but an install-and-load. The macOS leg is
  the only one that runs the package a macOS user installs, in a
  profile nobody has seeded, and it found three faults this machine
  cannot show on its first complete run. (C-5, C-256.)
  WHAT COUNTS AS INFEASIBLE IS NARROW, and must be written down at
  the exemption: a limit the platform imposes that no amount of code
  gets round. Cost is not one -- the repository is public, so
  standard runners are free and jobs run in parallel, and a leg that
  adds nothing to the critical path costs nothing to keep. "Not done
  yet" is not one either.
  WHEN THE MAC GAINS A STAGE, THE RUNNERS GAIN IT IN THE SAME COMMIT,
  for the same reason the derived documents are regenerated in the
  commit that changes the suite: a parity rule that waits for
  somebody to remember has already drifted. The exemption list in
  `tools/check_standards.py` is where a divergence lives, and it is
  read at every push.

- **CI stays in step with the Mac, and that is CHECKED before
  the branch is pushed, not discovered on a runner.**
  `tools/check_standards.py` reads `release.py`'s own stage list and
  requires every stage to be either covered by a named CI job or
  exempt with a written reason; it also requires every harness under
  `tests/` to be run by the workflow or exempt, every script the
  workflow names to exist, and the six jobs -- standards, suite,
  install, gallery, windows, macos -- to be present, each of them
  still running a command this check can SEE. Nothing there is a
  hand-kept list, so the two cannot drift apart quietly -- a sentence
  that was FALSE for sixteen days, because `EXPECTED_STAGES` in
  release.py was exactly that. (C-6, C-257.)
  It runs in a second,
  before the pre-candidate push, which is the only moment early
  enough to matter: the push precedes the local gates, so a broken
  or hollowed-out workflow otherwise surfaces fifty minutes later or
  not at all, since a job that was silently dropped fails nothing.
  The EXEMPTIONS carry the weight, because each is a claim that a
  second machine cannot answer a question -- and the visual gallery
  was exempt for months on a belief about fonts that was simply
  false, costing this project a rendering gate on three QGIS
  versions until 2026-08-12. When the check complains, change the
  workflow or write the reason; deleting the stage to silence it is
  never the answer. (User instruction, 2026-08-12.)
- **A branch is not created until the secrets check has passed, and
  carries only what CI needs.** The check runs BEFORE the branch
  exists, not after: a secret that reaches a public branch is public
  whatever happens next, and deleting the branch does not undo it.
  The pre-candidate branch is named for the candidate it precedes
  (`pre-0.24.0rc5`), and nothing rides along that a Linux test run
  has no use for -- `dist/` and `reports/` are gitignored, so
  candidates and dossiers cannot travel. (User instruction,
  2026-08-10.)
- **The process is PUBLIC; only working files and private material
  are not.** `docs/process/` carries the campaign records, the findings
  and the notes sent upstream, retractions included; what stays out is
  what has no reader but the next session -- one-shot scripts, scratch,
  and `dev/state-of-play.md`, whose durable content is promoted into
  these documents. The test is "who reads this, other than us
  tomorrow". A document may not NAME a `dev/` file: the command gate
  passed here on three of them and reddened six runner legs (T-144).
  (User instruction, 2026-08-11; C-279.)
- **EVERY push to a branch CI watches is a push that gets watched.**
  The branch once stayed red for eighteen pushes across six hours
  because approving prose is the user's act and no local gate could
  satisfy it: a gate only a person can satisfy is exactly the one that
  goes unsatisfied. Never end a session without the branch's colour,
  and before a push run the one command that reads its steps out of
  `ci.yml` and says which it could not run (C-258, C-280):

      python3 tools/check_before_push.py
- **Linux CI runs BESIDE the local gates, its fixes are made in a
  WORKTREE, and the push is watched.** Push first so the runners answer
  in twenty minutes while `release.py --rc` reads the tree for ninety;
  arm the watcher in the same breath, because silence means the run
  was never created; fix what CI reports in `git worktree add
  ../ws-ci-fixes`, never in the tree a gate is reading. A candidate is
  promoted only when both are green. (User instruction, 2026-08-10;
  C-281.)
- **What CI needs is never paid for out of what a user is promised.**
  CI must provision geopandas; the plugin can, behind the consent
  dialogue; the forbidden shortcut is any flag letting CI skip that
  dialogue, which would put a consent-free download into the SHIPPED
  plugin. So `tools/ci_provision.py` calls the plugin's own provisioner
  from outside `build.shipped_files()`, and
  `test_pypi_provisioning_is_reached_only_through_consent` holds the
  line. Reasoning in docs/PUBLISHING.md. (C-282.)
- **THE FULL SUITE IS NOT RUN UNLESS IT IS ABSOLUTELY NECESSARY.**
  (Maintainer's instruction, 2026-09-05, restating the rule below for
  every context and not only the hour before a candidate.) Iterate
  with `tools/run_some.py` on the tests a change touches and their
  neighbours; the candidate's own gate is where the whole suite runs,
  once. A run "owed" over a series of commits is discharged by that
  gate, not by a second launch beforehand.
- **Do not re-run a gate the release is about to run.** The gates
  are cheapest-first and the suite is the fourth stage, so running it
  standalone beforehand buys no earlier warning and doubles the wait.
  What DOES belong before a candidate is what the gates only CHECK:
  regenerate the two derived documents and settle the text-review
  queue. (User instruction, 2026-08-10; C-283.)
- **A substantial release goes out as a CANDIDATE first.**
  `python3 release.py --rc` runs the same correctness gates and then
  stops, writing `dist/weavingspace_qgis-<version>rc<n>.zip` and
  committing nothing. The gates answer whether the plugin is correct;
  only somebody making a map with it can say whether it is any good to
  use, and that feedback has to arrive before the version is tagged
  rather than after. The candidate announces itself as `<version>rcN`
  in QGIS's plugin manager (substituted inside the archive; the
  version on disk is untouched) so a tester always knows which build
  they have. (User instruction, 2026-08-08; details in
  docs/PUBLISHING.md.)
- **A stage stays in the release path only while somebody reads its
  output and would act on it.** Three left within a day (2026-08-11 and
  12), about eighty minutes of every candidate between them; `--quick`
  was retired with the last of them, having nothing left to skip. What
  did NOT leave is the contrast worth remembering: the visual gallery
  at 7 seconds and the colourspace comparison at 16, because both catch
  a WRONG MAP, which is this software's characteristic failure. Before
  adding anything to a release, and periodically for everything already
  in it, ask who reads the output and what they would do differently;
  if the answer is nobody, it belongs on demand or on somebody else's
  machine, reporting. Which three left and why: C-7.
  Details in docs/PUBLISHING.md.
- **`--resume` exists so a defect in the MACHINERY does not cost a
  re-run of the software's gates, and it is opt-in.** It skips a stage
  that passed before against exactly the inputs `STAGE_DEPENDS` names,
  which is narrower than the tree and wider than what ships, and only
  where the stage's output survives in `reports/stage-logs/`. A
  candidate for promotion is built by a run that measured this tree.
  (C-284.)
- **A release is published FROM `main`, and release.py refuses
  anywhere else.** `--push` pushes whatever branch you stand on, and
  Pages serves `docs/` from `main`, so a release from the candidate's
  branch leaves the page and README describing the previous version.
  The sequence has `git checkout main && git merge --ff-only
  pre-<version>rc<n>` in the middle; `--ff-only` is the guard. (C-285.)
- **A release PROMOTES a candidate; it never re-derives one.** The
  candidate writes a receipt digesting exactly the files that ship,
  taken with `build.py`'s own `shipped_files()`; `release.py` refuses
  without a matching receipt and skips the gates that measured this
  artefact already. Tests, tooling and documentation are outside the
  digest, since they cannot change what a reviewer ran. (User
  instruction, 2026-08-09; C-286.)
- **A candidate number is spent by anything bearing it.**
  `next_candidate` counts zips, dossiers AND receipts, so deleting an
  artefact cannot hand its number back. It used to count zips alone,
  and a dossier for `0.24.0rc3` sitting beside no zip would have made
  the next build a second, different rc3 — one name, two trees. A gap
  in the sequence confuses nobody; a reused name confuses everybody.
  Guarded by `test_a_candidate_number_is_never_reused`.
- **Releases go through `python3 release.py`**; never hand the user a
  zip that did not come out of it (details under "The test suite").
  Every release writes reports/v<version>/testing-report.md listing
  each test individually with its result and measured values; report
  those per-test results to the user whenever something is published
  (an explicit user requirement, 2026-08).
- **Approved prose goes STALE, and the changelog is where it costs
  most.** 0.24.1's changelog was approved in the morning and ended
  "Nothing else about the plugin has changed". Four hours later the
  documentation audit found and fixed a modal dialog on the live path
  -- a user-visible behaviour change -- and the sentence shipped
  anyway, into the zip, the plugin manager and the release page. No
  gate could see it: `metadata.txt` was not in the text-review queue
  at all, though its changelog and `about` are the most-read prose
  this project ships. It is in the queue now (2026-08-12), so a
  changed entry re-enters review. The habit that goes with it: when a
  release changes behaviour AFTER its changelog was approved, the
  changelog is stale by definition -- re-read it against the diff
  before promoting, not against memory of what the release was for.
- **A rule that asserts its own enforcement must BE enforced.**
  `check_standards.py` claimed to require every harness under
  `tests/` to be run by CI or exempt, and CLAUDE.md and
  docs/PUBLISHING.md both repeated the claim. The check did not
  exist. A rule nobody implements is worse than a rule nobody wrote,
  because it is believed and therefore not checked by hand either.
  Implemented 2026-08-12 and proved to fail by adding a harness the
  workflow does not name. When you write that something is enforced,
  open the checker in the same commit.
- **A HARNESS THAT LAUNCHES A TEST MUST LAUNCH IT WITH AN INTERPRETER
  THAT CAN RUN IT, AND MUST REFUSE OTHERWISE.** `mutation_check` once
  launched every test with the system interpreter, every test died at
  `import qgis`, and a test that "failed" scored CAUGHT seventeen times
  in a row. A check that can only confirm is not a check: ask of any
  harness what it does when the thing it drives cannot start. It
  resolves `QGIS_PY` and refuses to judge otherwise. (C-287.)
- **A catalogue entry that matches nothing REPORTS nothing, which
  reads exactly like success.** Seven of 243 entries were once
  anchored on text edited away, and the first re-anchored one then
  survived because either of two branches delivered its result.
  `check_standards` reads every entry with `ast` and fails on an
  absent anchor. When you edit a line, expect to re-anchor the entry
  standing on it; when a mutation is caught, check it was applied.
  (C-288.)
- **One changelog, THREE RENDERERS, and it must read in all of them.**
  QGIS's plugin manager shows `changelog=` as it stands, the release
  page renders it as Markdown where single newlines fold, and
  `release_notes.py` cuts the entry out by a lookahead for a line
  opening with digits -- one indented header once ran the entry on
  through the whole previous version. When one text is shown by two
  renderers, check it in both; where a tool cuts one record out of
  several, assert the CUT. (C-259, C-8, C-260, C-289.)
- **Release notes are COMPOSED, never generated, and the half a
  person writes is the `changelog=` entry in metadata.txt.** A
  release page has two readers: somebody deciding whether to
  upgrade, who wants a paragraph, and somebody evaluating the
  project, who wants to know what was measured. One text for both
  serves neither. `tools/release_notes.py` puts the reviewed
  changelog paragraph first -- the same words the plugin manager
  shows, so the two cannot drift -- then generates what was measured,
  what is attached, and the `**Full changelog**` compare link a
  GitHub reader looks for. It REFUSES when the changelog entry is
  missing, because a release whose notes were written by a script is
  a release nobody described. Write that entry as what a user can now
  do or no longer worry about, not as a list of commits, and put it
  through `tools/text_review.py` like every other sentence a user
  meets. The testing report is ATTACHED, not the body: it used to be
  the body, which made the announcement a per-test listing.
  (User instruction, 2026-08-11.)
- **Published images show real data displayed as a map.** Every image
  in README.md and docs/index.html shows a named place with
  recognisable geography, region outlines and a legend where the
  classes need one -- not an abstract pattern. A reader is asking what
  they could produce with their own data at the end of an afternoon,
  and a field of coloured hexagons answers a different question: it
  shows the mechanics rather than the output, and quietly argues
  against the plugin's own claim that several attributes of real
  places can be read from one map. Figures from the published article
  are better still where their licence allows, attributed in the
  caption. (User instruction, 2026-08-08; details in
  docs/PUBLISHING.md.)
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
- **Launching a long job has three steps and they happen together:
  shard it, watch it, then leave it.** Ask first whether the work
  parallelises -- sweep cases, mutation judgements and per-file work
  all do, whole test suites do not -- because four shards turn ninety
  minutes into twenty-five; then arm the watcher; then go and do
  something else. Both halves were written down on 2026-08-10 and
  both were skipped the same evening on a ninety-minute sweep, until
  the user asked why. A rule that is only written is not a practice.
- **A CEILING A HEALTHY RUN CAN REACH IS WORSE THAN NONE, and is
  sized from the SLOWEST machine ever measured, times a margin.** The
  same code took 392s, 486s and 550s on three legs of one run; the
  spread is the runner and a limit must clear all of it. A stall
  watchdog catches a HANG and is never a performance budget. The Linux
  suite legs took 60 to 68 minutes on 2026-08-31 at 727 tests, and a
  figure in prose ages, so compare a running job with the same job on
  the previous round. (C-290.)
- **Durations are monotonic; only timestamps are wall clock.** A
  laptop closed for two hours makes wall clock advance while a
  process accumulates no cpu, and those two readings together are
  indistinguishable from a hang -- so `release.py` would have aborted
  a healthy candidate carried to a meeting. `time.monotonic()` stops
  with the machine on macOS, which is why it is the only clock any
  watchdog, stage duration or progress figure may read; a wall-clock
  reading is kept only where a human compares it with their watch.
  Never subtract one from the other. The mutation campaign learned
  this in batch 8, `release.py` was written afterwards and repeated
  it, and two test fixtures then staged wall-clock starts against
  monotonic code -- so the rule travels badly and is written here for
  that reason. (2026-08-11.)
- **Instrument a child process BEFORE it crashes.** A subprocess that
  dies in C leaves exit -11 and two empty streams, which says nothing
  whatever; `faulthandler.enable()` and a printed line per phase turn
  that into a named call. Adding them costs three lines up front and
  a full CI round -- fifty minutes here -- after the fact. The same
  applies to any failure message that will be read remotely: say what
  was FOUND (the values, the environment, the exception), never only
  which assertion was reached. (2026-08-11, after a missing geopandas
  spent two rounds disguised as a locale defect.)
- **Anything that outlasts a turn gets a thirty-minute heartbeat.**
  Not when asked: by default. A beat reports what is running with CPU
  against elapsed, progress against the total, the newest result, and
  whether the files it is reading actually belong to THIS run. It is
  a defect-finding instrument rather than a courtesy: on 2026-08-10
  four faults were found by beats and none by waiting for a job to
  finish, and each would have produced a number somebody believed
  (C-9). Full procedure
  in `.claude/skills/long-job-supervision`. (User instruction,
  2026-08-10, after watching the beats catch them.)
- **Five procedures live as SKILLS, and are invoked, not merely
  owned.** `.claude/skills/second-machine` before adding CI or reading
  a second machine's failure; `long-job-supervision` before launching
  anything that outlasts a turn, and for how to shard;
  `tests-that-can-fail` before writing or reviewing a test;
  `dependency-bug-workaround` before compensating for a bug in QGIS or
  any dependency; and `mutation-campaign`. Each records its source
  documents with a sha256 and `check_standards` fails when a source
  has changed. The CPU-versus-elapsed check was rediscovered the hard
  way in a session that never invoked the skill that already carried
  it. (C-291.)
- **The testing documents are binding, read BEFORE tests are written
  or changed, and UPDATED the moment one is proved incomplete.**
  `docs/TESTING.md` holds the shapes that earn their keep and the
  lessons each paid for; `docs/MUTATION-TESTING.md` the campaign's
  commitments; `docs/MUTATION-LOOP.md` the runbook. When you are about
  to do what one of them warns against, the document is right; when
  one is wrong, change it deliberately and say why. (C-292.)
- **New code is held to account, but the guard REPORTS REMOTELY and
  no longer gates a candidate.** (Changed deliberately 2026-08-11;
  full reasoning in docs/MUTATION-LOOP.md.) Three things were wrong
  with it as a gate, none of them the threshold being inconvenient: it
  measured a blended figure over changed lines, which
  MUTATION-TESTING.md says never to quote; it cost more than a
  candidate can carry, and the sample scales with the diff; and its RED
  meant "write tests over the next few days", which is a work list
  rather than a gate. `release.py` now prints what it would have
  sampled and names the dispatch command; the run happens on GitHub and
  its survivors are triaged into the NEXT candidate. The figures: C-10.
- **The historical form of that rule, for context**: `mutate_auto.py`
  run over the lines that changed since the previous tag, stopping the
  release below 70%, with a sample that scaled with the diff. C-11.
- **Census and sample answer different questions, and a census
  carries a firmer rule.** Sample to learn how good the suite is (the
  population estimate, and the only thing fit to certify); census a
  cost stratum with `--max-cost` to learn what to fix (exact rate,
  complete survivor list). A RE-census is a controlled before/after
  only while the plugin source is unchanged, since mutants are
  generated from that source — if it changed, the delta does not
  exist and a fresh baseline is required. Because a census hands over
  a named list of survivors, it is unusually easy to write tests
  aimed at mutants rather than behaviours: every test added in
  response to a survivor must name the harm a user would suffer AND
  be a test we would have wanted anyway. If neither holds, ACCEPT the
  survivor and record why — accepting is a legitimate outcome, and a
  campaign that never accepts anything is chasing a number rather
  than testing. Full reasoning in docs/MUTATION-TESTING.md.
- **Mutation testing has commitments, and they bind**
  (docs/MUTATION-TESTING.md): close a survivor with the test the
  BEHAVIOUR deserves, never one aimed at the token; if you cannot
  state the harm a user would suffer, mark it equivalent with evidence
  or accept it and say why; prefer deleting a line that does not earn
  its keep; demonstrate equivalence in a sandbox and record it in
  `EQUIVALENT`; report rates per module as well as blended; certify
  out of sample with the Clopper-Pearson bound. (C-293.)
- **Every test that produces a map checks it visually, and those
  checks appear in the release PDF.** Two shapes: `visual_pair` when
  the settings can be restated independently (render the dialog's map
  beside one built by calling the library directly, compare interior
  pixels), and `visual_gamut` when they cannot (assert every interior
  pixel is a colour the ramps in force can make). A map-producing test
  that only counts features is not finished. (Standing user
  instruction, 2026-08-06.)

## Working economically in a long session

A long session ends when the context window fills, and it fills faster
than it looks. None of the rules below trade away rigour; they are
about not paying twice for the same information. Measured on the
2026-08-09 session, which filled the window in about four hours.

- **Batch edits per file.** Every edit causes the harness to re-inject
  a large slice of that file. Six small edits to dialog.py cost six
  re-injections; one pass costs one. Plan the whole change to a file,
  then make it.
- **Write scripts to the scratchpad and run them; do not paste long
  heredocs.** An inline script is echoed back in full. The same script
  written to a file and run costs a line. (It also survives the
  quoting traps: nested triple quotes break a heredoc.)
- **Grep for the answer, do not read for it.** Targeted `grep -n` with
  a little context beats reading a wide region, and beats re-reading
  something already seen. Trust your own notes.
- **Give one file one owner.** Two agents, or an agent and you,
  editing the same file collide AND double the re-injections. Assign
  whole files.
- **Ask subagents for short reports.** "Under 150 words unless
  something is wrong, then say what" keeps the findings and drops the
  narration. Four verbose agent reports cost several thousand words in
  one session. Agents are cheap in context (only the report returns)
  and expensive in tokens; they cannot be steered once started, so
  they suit well-bounded work on files nobody else is touching. The
  documentation pass was exactly that shape, and turned up five real
  defects nobody had gone looking for.
- **Background the long computations, keep the editing in front of
  you.** A suite, a coverage record or a mutation batch consumes no
  context while it runs, so start it early and do something else. But
  the preference is not unconditional, and the costs are real:
  a failure is discovered late (gate every chain so it stops at the
  first red stage rather than wasting hours); polling is not free, so
  a heartbeat should be stopped when nothing is running; and above
  all, background work LOCKS THE TREE — source cannot be edited while
  coverage records, which serialises everything else. Contention also
  degrades the measurement: four workers plus a suite is how a batch
  loses mutants to timeouts. Background what is long and
  self-contained; foreground what you need to react to.
- **Do not read binaries.** Summarise a zip with `zipfile`, an image
  with `sips`. Read an image only when a visual judgement IS the task
  (choosing an icon, checking a rendered page) — then it earns its
  cost.
- **Write the handover before the window is tight, not after.**
  `dev/state-of-play.md` is the durable record; the rules themselves
  belong in this file and in docs/, which survive compaction on their
  own.

## How we decide things

- **BEFORE PUTTING A DECISION TO THE MAINTAINER, CHECK IT IS A
  DECISION THEY HAVE TO MAKE.** A request elaborated into a ruling
  acquires open questions that belong to the elaboration, and handing
  those back reads as diligence while asking somebody to do work the
  reading created; a question is only as good as the request under it.
  The cheap check: state the ask back in the plainest form that could
  be acted on, and where that is buildable, build it. Reserve the
  grilling for decisions that genuinely fork. (2026-08-29; C-12, C-315.)
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
- **TWO RELATIONSHIPS, AND ONLY ONE OF THEM MAKES PERSISTENCE A
  DUTY.** (Maintainer's framing, 2026-08-25.) At the boundary with
  QGIS the plugin is a guest holding the user's own work -- dock
  styling, a renamed group, stamps in a saved project, tables a
  colleague will open -- and losing any of it DESTROYS something,
  which is why "preserve, do not repaint", the follow rules, adoption
  and the per-dataset banks all lean one way. None of that reasoning
  reaches the dialog's own controls, where forgetting costs a few
  clicks and never a map, so those questions are settled on what makes
  the next thirty seconds clear. The two questions are INDEPENDENT: an
  answer for one is argued, never inherited from the other. Spacing was
  decided that way -- a number a person TYPED survives, a number the
  plugin DERIVED does not -- and icon mode is settled by ruling 4 of
  2026-08-25 (C-261). (C-316.)

## Lessons learned here (do not relearn these the hard way)

### Qt, QGIS and the libraries: facts about the toolkit

Facts about the toolkit that were each paid for once; the accounts
are C-265 and the ids beside each rule.

- **LAYOUT IS LAZY, SO MEASURE ONLY WHAT HAS BEEN LAID OUT.** `sizeHint`
  is stale before a layout pass; `grab()` of a never-shown window
  reports phantom visibility; a `QTabWidget` lays out only its current
  page, so every child of another page reports its parent's width
  (C-156); `isVisible` is False in a window nobody has shown, so it
  cannot ask whether something is hidden (C-145). `setCurrentIndex`,
  pump, then measure, and screenshot only after `show()`.
- **A WIDGET INSIDE A LAYOUT KEEPS NO SIZE YOU HAND IT, SO THE WINDOW
  IS THE LEVER**, and a floor on one pane is taken out of the pane
  beside it (C-191, C-192). A stacked widget's minimum is the largest
  of its pages, which is how one tab sets the whole window's size
  (C-160). A layout pass that widens what it measures is a feedback
  loop, where a margin is not (C-159). A width in pixels is a claim
  about a font, and the offscreen platform every runner uses supplies
  a 9pt one (C-140). A `ResizeToContents` column re-measures on every
  `setItem`, ten seconds a message at five hundred rows (C-166).
- **A CELL WIDGET IN A HIDDEN COLUMN CAN PAINT AT THE TABLE'S ORIGIN**,
  so a blank cell is made by removing the widget; and Data & colours
  handlers must never trigger a table rebuild, since a rebuild lands
  mid-interaction and picks commit to dead widgets -- they go through
  `_refresh_preview_colours`, and a test asserts widget identity
  survives the debounce.
- **SIGNALS AND LIFETIMES.** `QgsMapLayerComboBox` re-emits
  `layerChanged` whenever the project's layers churn, so its handler
  is idempotent and the plugin's own outputs are excluded by a custom
  property. A signal connected to `QgsProject.instance()` outlives the
  window that made it, and so does a combo (C-25); a widget that
  retains layer OBJECTS must be rebuilt when layers are removed,
  because a dead pointer's address is reused (C-116); Qt drops a
  connection to a bound method when its receiver dies and keeps one to
  a lambda, which then segfaults (C-139). A single-shot timer that a
  gate returns without re-arming is lost, not late (C-165). A QLabel is
  a store: one label, one meaning (C-208).
- **THE STYLING DOCK IS HEARD ONLY WHERE IT CALLS `setRenderer`.**
  `styleChanged` fires on a renderer installed whole and not on an
  edit made to the held one, whose `triggerRepaint()` is the only
  trace (C-105); `ranges()` and `categories()` hand back copies, so
  editing one is a no-op and a probe that does it measures nothing
  (C-106); a temporary list from a QGIS getter frees its contents, so
  `renderer.ranges()[0].symbol()` reads released memory -- bind the
  list to a name first.
- **PyQGIS ANSWERS BY RETURN VALUE.** `provider.addFeatures` returns a
  tuple, so `if not ...` never fires (C-152); OGR's `CommitTransaction`
  refuses by return code and no `except` can catch it (C-220); a
  `getFeatures()` honours the layer's subset filter, so a save wrote
  the filtered view as the map (C-226); `findData` compares through
  QVariant, where a tuple never equals an equal tuple, while a string
  matches (C-239). A `processEvents()` loop lets no wall time pass, so
  a QgsTask never finishes inside one (C-157).
- **A PAINT-TIME FIT MUST NOT RE-DERIVE ITS TRANSFORM FROM A GESTURE'S
  OWN PREVIEW** -- the drag froze its origin and the fit moved the
  frame under it (C-198).
- **THE LIBRARIES.** macOS code-signing refuses PyPI C extensions inside
  the signed QGIS process, so side tooling that needs matplotlib runs
  in `.venv-reference`. Label anchors: the centroid for the visual
  centre, `representative_point` only as the inside-the-polygon
  fallback (C-13). A numerical centre found to an ABSOLUTE tolerance
  breaks a symmetry differently at every scale: the library's polylabel
  at one map unit gave the default design's dual three edge classes at
  a spacing of 3000 and ten at 2900, and a tolerance relative to the
  tile's own size gives the snub square's two at every spacing (the
  Topology tab audit, docs/TOPOLOGY.md). Ask of any numerical answer
  that feeds a symmetry or an equality what its tolerance is measured
  in.

### Records, stores, keys, landings and the file

This plugin keeps one fact in several stores -- a control, a group's
record, a layer's stamp, the file's record, a session dict -- and most
of its defects are two of them disagreeing. The accounts are C-266
and the ids beside each rule.

**Identity and keys.**
- **A NAME THE USER CAN EDIT IS NOT AN IDENTITY, AND NEVER A KEY**
  (C-16); an element id is a letter every map shares, so ownership is
  not a name prefix (C-126); a string that carries a path inside it is
  a path, respelt by a project save (C-50); "already there" and
  "empty" are questions for the FILE, not for a string that names it
  or a byte count -- an OGR data source with no layer is 65,536 bytes
  (C-143, C-222). A layer built on another layer's source IS that
  layer to anything that looks up by source (C-117).
- **A PAIRED ARTEFACT INHERITS THE IDENTITY OF WHAT IT IS PAIRED
  WITH**, so every reader keyed on that identity gains a second answer
  and every writer of the original has a twin that does not (C-15). A
  choice stored as `layer:<id>` dangles at the next re-tile, and a
  dangling reference is not a disagreement, which is why nothing
  complains (C-119).
- **WHEN A NAME OR A FORMAT CHANGES, FIND EVERY READER BY SYMBOL AS
  WELL AS BY LITERAL** (C-48), sweep the silent readers first (C-213),
  and grep for whoever DECOMPOSES a label you have recomposed.

**Which moment a field is about.**
- **A RECORD ASSEMBLED FROM TWO MOMENTS MUST SAY WHICH MOMENT EACH
  FIELD CAME FROM** (C-58): the design half from the launch snapshot,
  the elements live. A stamp taken away from a landing may carry only
  what a landing decided (C-49); a launch state beats the carry, so
  handing a key over is not the same act as letting it fall through
  (C-231); a resume stamps the group with the region it LANDED ON, and
  stamps the layers too (C-228); a gesture's position is measured from
  where the handle was TAKEN, since each frame rewrites the boxes the
  next frame would read (C-321). Ask of any writer that copies a
  record: which moment is each field about, and does this writer
  stand at that moment?
- **WHEN A REPAIR GIVES ONE STORE A NEW WRITE, ENUMERATE EVERY STORE
  THAT ALREADY HELD THAT FACT** (C-57). A restore is a landing for
  everything that asks whether the controls describe the map (C-141);
  a record filled by a landing and cleared by nothing answers for a map
  it has never seen (C-227); a record seeded by adoption assumes a
  project (C-135); a per-file fact must not live on a session-wide
  control (C-132); one reading kept in a session-wide slot compares
  against whichever dataset the chooser holds (C-124).
- **AN OWNERSHIP QUESTION THAT OUR OWN ACT MAKES TRUE IS NOT AN
  OWNERSHIP QUESTION** -- a file was theirs on press one and ours on
  press two (C-196) -- and the repair spared everything because the
  record spells the key `var`, not `variable` (C-197).

**Clearing, absence and the interval between.**
- **NAME THE ACTOR THAT EMPTIES A THING AND THE ACTOR THAT FILLS IT,
  AND WHERE THEY DIFFER, ASK WHAT HAPPENS IN BETWEEN.** (Maintainer's
  instruction, 2026-09-05.) A transient picture is cleared by the thing
  that REPLACES it, not by the act that requested the replacement: a
  preview cleared at the drop put the old design back for the whole of
  an asynchronous rebuild (C-244), and a build landing tore the tab's
  parameter boxes down to their defaults. Both halves are healthy code
  and only the interval is wrong, which is why an eye passes over it
  and a test premise does not.
- **CLEARING IS RIGHT WHEN THE USER LET SOMETHING GO, AND WRONG WHEN
  THE PLUGIN MERELY STOPPED DECIDING** (C-69); before clearing on an
  absence, ask what makes the record absent (C-56), and when a new
  guard reads an old record, which paths leave it deliberately empty
  (C-107). A blank the plugin imposed is not a choice the user made
  (C-60). When a fix is about staleness, ask what else it discards: a
  cache of one is no cache when there are twenty-three of anything
  (C-94). Enumerate what a clear site LEAVES, not what it clears.
- **A WATCHER MAY ONLY ADOPT WHAT A PERSON LEFT BEHIND**, at rest and
  never mid-run, mid-write or mid-landing (C-89). A background result
  may land on a gesture (C-201), and the click before the press is not
  a gesture (C-240): when a docstring names a hazard, check every path
  through the function honours it.

**Records that enumerate.**
- **A KEY OR A GUARD THAT ENUMERATES A RECORD'S FIELDS IS A SECOND
  DEFINITION OF THE RECORD, AND IT GOES STALE.** The shelf key named
  two of a design's terms and the dual moved neither (C-232); the
  save's staleness guard compared three fields of twenty-six (C-174);
  a preview colour built from the ramp NAME was wrong six ways (C-71);
  a copy wrote the record wholesale and never read the keys added
  since (C-95). When a record gains a key, grep every site that
  enumerates its keys; when a handle, verb or mode list gains a
  member, grep every table keyed by that list and guard the SHAPE
  (C-223). A hand-kept list drifts even where a comment says to keep it
  in step (C-177). When a fix widens a signature, ask whether the new
  term is coarser than what it stands for: a boolean per element is
  invariant under a permutation. When a repair gives a function a new
  INPUT, widen the record and the key that decide whether the map is
  redrawn in the same commit (C-328); and when one store becomes the
  owner a record reads, find the reader still on a hard-coded default
  (C-330); and an empty value written through a truthiness gate is an
  ABSENT key on the way back, which fires the legacy fallback on the
  commonest journey (C-332).
- **A DISPLAY RULE IS DISPLAY-ONLY ONLY IF NOTHING RE-READS THE
  DISPLAY** (C-133); a count quoted to a person is asked of the
  geometry, not of two totals (C-131); a guard that rebuilds a layer
  from its source string loses everything the user set on it (C-130).

**Deferred work, flags and predicates.**
- **ASK WHAT CONSUMES A REMEMBERED INTENT, AND WHETHER THAT CONSUMER
  CAN DECLINE FOR A REASON UNRELATED TO THE ACT DEFERRED.** An armed
  timer is not a run that will start, and where a document calls one
  reading "a second reading of one question", diff the two term by
  term (C-175); a flag read by one
  consumer outlives the journeys that consumer never runs on (C-212);
  a wanted write that fails still clears, so enabling the write is
  half a repair (C-178); a store written BEFORE the act it stands for
  outlives a refused act, so settle it where every exit of the act
  ends (C-323) -- and launched is not landed: spend it at the landing,
  and put it back BEFORE a cancel, since the task's own end reaches the
  landing first -- at EVERY site that cancels the task, the project
  door included (C-331).
- **A PREDICATE THAT MERGES TWO FACTS IS RIGHT FOR A WAIT AND WRONG
  FOR A QUESTION** (C-224), and a question built on it merges the same
  two states (C-233). A control one act moves as a side effect is read
  by another act as a decision (C-234). A wait only an outer frame can
  end is not a wait (C-221), and a frame must not report the outcome of
  an act it cannot see (C-225). A save that pumps the event loop takes
  its buttons down, and when a justification enumerates the doors it
  closes, count the doors again whenever the interface gains one
  (C-144).

**Doors, twins and sequences.**
- **A GUARD ADDED TO ONE DOOR BELONGS AT EVERY DOOR INTO THE SAME
  ROOM** (C-52); the create-new door clears the output path as the
  dataset door does, since a saved file is one map (C-327); a flag's
  writers ARE the door list, and the chooser was the third door into
  the room the two Load doors guard (C-329); a binding that returns
  nothing lets two stores name two maps, so a helper that "forces"
  an order answers whether it could (C-333). Presence
  is not order: a call put back after its twin
  calls it before is worse than one still missing (C-55); a fix written
  into two paths in one commit is diffed hunk against hunk (C-66), and
  a fix inserted into a sequence is checked for its order against the
  twin, not merely for being present. A refresh with one caller works
  once -- grep the constructor as well as the updater, and ask what
  rebuilds the widget. When three repairs to a mechanism fail, suspect
  the promise (C-150); a fix that widens a scope re-aims every trial
  that compared against the old one (C-154). Retirement is a fact about
  the object, not an absence in a registry (C-115).

**Numbers, renderers and what a record describes.**
- **A RANGE IS NOT THE ONLY THING THAT EATS A KEYSTROKE**: a validator,
  a lowered `decimals`, or a `valueChanged` handler that rewrites its
  own box, each invisible to `setValue` (C-65); a settle hung on
  `editingFinished` never fires when the widget a person moves to next
  takes no focus, so settle where the RECORD reads the box, at its one
  owner, since a settle at one door left every other door open (C-322). A legend is rendered by
  somebody else's formatter, so check what the label says; never make
  class membership depend on a float's last bit; a ladder may hold
  several classes with identical bounds, so a lookup by bounds must
  not stop at the first match (C-109).
- **ASK WHETHER A RECORD DESCRIBES THE DATA OR ONE RUN'S OUTPUT.**
  Class breaks survive a re-tile; a paired layer's categories enumerate
  the absences one tiling produced, so a carried renderer is kept only
  while it can draw what is there, and a renderer with no categories
  covers everything. One polygon doing two jobs changes both when you
  shrink it (C-82). An unbound return is a failure nobody hears.

### Guards, tests, fixtures, probes and the catalogue

docs/TESTING.md is the binding record and is read before a test is
written or changed; these are the rules that shape everyday work here.
The accounts are C-267 and the ids beside each rule.

**What a test is.**
- **A TEST THAT PASSES IS NOT A TEST THAT WORKS**: it must fail when the
  behaviour it names is broken, and every test written to close a gap
  gets a catalogue entry in `tools/mutation_check.py` that breaks the
  behaviour and requires the failure (C-14). Tests run with an EMPTY
  project, since everything shares one `QgsProject`. The highest-value
  shape is UI against library, the expected side written from the
  settings and never from `_build_unit`; every map-producing test
  checks the map visually.
- **A TEST FOR A PROMISE IS A MATRIX, NOT A CASE**: atomic routes,
  synthetic shapes chosen for failure modes, and an axis for what
  happens NEXT, because arrival and survival are different promises
  (C-83). A matrix catches only what its cells may complain about
  (C-86), and a green subset is not a green suite -- four regressions
  shipped past every targeted run and a hunt aimed at the very code,
  because a hunt asks what MIGHT be broken and the suite asks what IS
  (C-254).
- **A TEST THAT SUPPLIES ITS OWN INPUT MEASURES THE FUNCTION, NOT THE
  PRODUCT** (C-153); a test's positive control can be the very defect
  under repair (C-158); a suite can hold a control at a value no user
  holds, so ask of any test family what it holds constant (C-134); a
  test that matches a phrase copied out of the product is broken by
  the maintainer's own rewording (C-179), and a harness that matches a
  sentence the product says is retuned by the next sentence (C-209).

**Fixtures, premises and moments.**
- **MAGNITUDE IS A FIXTURE DIMENSION**: arithmetic right between 0 and
  50 and wrong at 1e12 shipped green three times, and a relative
  epsilon is an absolute gap. A record holding two claims is tested
  with both in force (C-64). A test leg that runs after the state it
  is about measures nothing (C-146); a settle returns before the result
  is adopted, so a premise asked in the same breath reads the old
  state (C-194); an assertion that names a moment is a claim about when
  its own reading was taken (C-237); a wait helper that does not widen
  by `CONTENTION` is a ceiling sized on the fastest machine (C-238).
  An intermittent failure under load can be the suite intermittently
  reaching a real defect (C-136).
- **A GUARD MEASURES THE GROUND, NOT THE BOX ROUND IT** (C-93); a guard
  that tests sign does not test finiteness, and an oracle in absolute
  values is blind to the sign (C-324); a comparator sensitive to
  representation cannot answer a question about appearance (C-162),
  and an exact question is not asked with a tolerance (C-163). When two
  things should draw the same map, compare what they drew, not what
  they look like (C-99).

**Guards and gates.**
- **A GUARD YOU HAVE NOT WATCHED FIRE IS A GUARD YOU HAVE NOT GOT**
  (C-80), and a check that can only confirm is not a check (C-97). A
  guard must not repair what it measures nor run where there is
  nothing to see (C-84). A gate that checks half of what it names is
  worse than none (C-70); one that opens a door must ask for what is
  behind it (C-176); a guard whose condition is right can still be
  aimed at nothing (C-113), and one computed as a delta is armed for
  one invocation (C-108). When a guard starts answering differently,
  follow its return value into every tuple it is a member of (C-111).
- **AT EVERY EARLY EXIT, NAME WHAT THE GUARD IS FOR AND READ WHAT LIES
  BELOW IT** (C-67); every exit from a long method names itself, and a
  modal refusal lands in a different store from the message bar, so
  read both (C-255). A guard that runs before a re-read must be asked
  with re-read values too. A stage or key that names a function which
  does not exist reports nothing, and that reads as costing nothing
  (C-81).
- **ATTRIBUTION BEATS DELTA, AND THE THIRD NARROW GUARD IS THE SIGNAL
  TO STOP PATCHING ROUTES** and ask whether the question is right
  (C-51). A repair aimed at an act is re-aimed at the act's absence
  (C-112); a dependency's cheap answer is a cached answer, honest only
  after something invalidates it (C-101, C-102); a guard whose
  precondition is a lossy digest is only as good as what the digest
  omits (C-125), and its override must be keyed by the same subject.
  A guard that compares three of twenty-six fields is a second
  definition of the record (C-164); the drop was wrong four times
  because it asked whether it MAY remove rather than what the artefact
  DESCRIBES (C-155). A recovery must report which of its routes
  answered (C-142); enumerate the producers of a second claimant, not
  just the one you built (C-118); when a fix threads a "who fired
  this" argument through a family, grep the calls they make to each
  other (C-73). A guard can be aimed at a state without knowing what
  produces it (C-243).
- **PROSE GATES ARE MOVED BY PROSE**: re-wrapping a paragraph disarmed a
  regular expression of literal spaces (C-171); a triple-backtick
  fence shifts every inline span below it (C-173), and the entry
  describing that fault blinded the gate next, so describe a
  delimiter and never quote it (C-188); the vendor-claim gate reads
  `commit <sha>` anywhere in three files (C-183). A re-vendor's real
  question -- did the library's own output move -- is one no gate
  here asks, since the comparison's expected side is the same library
  (C-184).

**The catalogue.**
- **AN ENTRY MUST BREAK THE ROUTE THE GUARD WALKS, NOT A ROUTE**
  (C-167): break every route at once, or the catalogue measures the
  other one (C-120); two sufficient fixes to one outcome make every
  single-site entry survive, which is information (C-193); an inert
  mutation and a redundantly held one both report SURVIVED and need
  opposite repairs (C-121), and a treatment whose control also fails
  has measured nothing. A ruling that gives a fact a second writer
  puts an older entry to sleep, so when a ruling adds a writer,
  re-judge the entries over the old one; three shapes recur -- a limb
  of a fallback chain, one of two readings of one fact, one term of a
  tuple -- and the repair is to anchor the whole decision.
- **`mutation_check` APPLIES EXACTLY ONE REPLACEMENT** (C-123); a
  backslash-newline inside a non-raw anchor is a line continuation
  (C-147); a guard that lands without a test of its own looks guarded
  because the neighbour it re-anchored still passes (C-104). Coverage
  says a line ran, not that its branch was taken; the per-test record
  is keyed by a test's display name, not its function name; ranking
  candidates under a cap decides what was asked (C-122). When you add a
  step to a sequence, ask what it resets (C-169).

**Instruments and probes.**
- **A UNIFORM VERDICT IS ALMOST ALWAYS THE INSTRUMENT**: run it
  against a case whose answer you already know. An instrument that
  holds a file changes what it measures (C-114); one that dies after
  reporting looks exactly like the thing it measures dying (C-219); a
  probe's control can move the thing both arms are about (C-236); a
  guard over the whole tree cannot tell your own edit from what it is
  watching for (C-210); a name that carries a number sorts as text,
  rc10 before rc2 (C-100).
- **AN AUDIT READS EVERY STORE AFTER EVERY ACT**, and the Topology tab
  audit of 2026-09-05 found three defects three matrices had passed
  over, each two stores disagreeing after an ordinary act
  (`tools/probes/audit_the_topology_tab_as_a_person_meets_it.py`).

### Watchers, long jobs, gates and the shell

Twenty-five watcher faults and a dozen shell traps were paid for one
at a time between 2026-08-10 and 2026-09-02. The accounts are C-264
and the ids beside each rule; the procedure they distil into is
`.claude/skills/long-job-supervision`.

- **A WATCHER REPORTS CHANGE, NOT STATE, AND WAITS ON THE PROCESS
  ENDING, NOT ON LOG TEXT IT PREDICTED.** A poll for "tests recorded"
  sat twelve hours because the tool prints "recorded 75 tests" (C-20);
  a monitor grepping a whole log re-reported one old failure every
  pass. Track an offset per file and key the wait on the pid.
- **SEED IT WITH WHAT IS ALREADY TRUE, KEY IT ON THE THING RATHER THAN
  A SNAPSHOT, AND GIVE IT ITS OWN LOG.** An empty "seen" set announces
  history as news (C-21); a poller pinned to one commit sha sits silent
  through the pushes that supersede it (C-185), and `gh run list
  --commit` wants the full forty characters (C-33); two watchers on one
  file interleave their verdicts (C-22).
- **ITS OUTPUT MUST BE ABLE TO EXPRESS THE FAILURE.** A work line
  through `head -2` cannot show a dead shard, and was written twice
  (C-148); `|| echo 0` after `grep -c` APPENDS to the 0 grep already
  printed (C-29, C-149); substituting "nothing" for a failed `gh` call
  reports one verdict twice (C-37); a truncated notification hides
  every line below the cut, so the headline carries what is live
  (C-190); a watcher is a program and can die partway (C-28), and
  `/bin/bash` here is 3.2 with no associative arrays (C-211).
- **HAND-RUN IT ONCE BEFORE ARMING IT, FROM THE REPOSITORY, INTO A
  FILE.** Three faults were caught that way in one morning (C-186):
  `gh` reads the repository from the working directory, so a watcher
  in a scratch folder asks about nothing (C-203); `tail` buffers to
  EOF, so a watcher piped into it prints nothing (C-235); the shell
  splits `for job in $JOBS` at the space in a job name (C-230); a
  downloaded artefact's mtime is when it arrived, not when its work
  happened (C-172). A watcher over a JOB ends with that job; one over
  the SESSION says "nothing running" in words and outlives any run.
- **A LAUNCHER'S EXIT DESCRIBES THE LAUNCHER.** `nohup ... &` exits 0
  while the runner has minutes left, so wait on the runner's pid and
  read the "N passed, M failed" line; and a launcher that reports an
  error may already have started the job, so `pgrep` for the WORK
  before relaunching (C-30). Read the line that assigns a tool's
  verdict before trusting the word: the sweep prints `caught` or
  `ATTENTION` and never SURVIVED (C-31), and its own summary line
  matches any filter looking for verdicts (C-32).
- **A GATE PIPED INTO ANYTHING, OR CHAINED THROUGH AN ECHO, IS NOT A
  GATE.** `gate | tail` returns tail's status and `gate; echo; git
  commit` commits off the echo; each put a tree the gate had just
  refused onto the public branch one command after the words were on
  screen (C-26, C-27), and it was done a third time by somebody who had
  quoted the rule that morning (C-200).
- **SILENCE PLUS EXIT 0 IS NOT A PASS, AND AN EMPTY LOG IS NOT
  EVIDENCE OF ABSENCE.** The suite ends through `os._exit`, so its
  buffered PASS line is lost to a pipe (C-34); `print()` inside a Qt
  slot goes nowhere under captured output (C-88).
- **THE TWO INTERPRETERS ARE NOT INTERCHANGEABLE, AND THE ENVIRONMENT
  NEEDS `set -a`.** Tests run under `$QGIS_PY`; edits and
  `tools/mutation_check.py` under `env -u PYTHONHOME -u PYTHONPATH
  python3`. Swapped, one dies at `import qgis` and the other at
  `encodings` having applied no edit (C-35, C-88);
  `tools/macos_qgis_env.sh` prints bare assignments, so an `eval`
  without `set -a` exports nothing (C-214); `mutation_check` runs its
  child with `QT_QPA_PLATFORM=offscreen` as the suite does (C-168).
  This machine's `/usr/bin/grep` is ugrep, and `-q` with `-v` answers
  wrongly: count matches instead.
- **A COMPLETED JOB'S LOG IS READABLE WHILE ITS RUN GOES ON**, through
  `gh api repos/<owner>/<repo>/actions/jobs/<id>/logs` with
  `--allow-escape-sequences`, where `gh run view --log-failed` waits
  for hour-long siblings.
- **SHARDS ARE READ SEPARATELY, AND THE PARTITION IS THE PROOF.** Each
  shard names the same total or something ran twice or not at all
  (C-215), and check your own arithmetic before reporting one broken;
  `exists` then `remove` is a race between shards that killed a
  recorder before its first test (C-36).
- **EDITING SOURCE BY SCRIPT: assert every anchor before any write,
  prefer the Edit tool for one replacement, and never rewrite a span or
  a whole file by string surgery.** A trailing comma makes a tuple of a
  string (C-19); a span deletion took a neighbouring test with it
  (C-23); a second definition written below the first loses nothing and
  answers wrongly (C-24); `lines[-1]` on a file ending in a newline is
  the empty string, so the edit appends (C-189); a `.split()/.join()`
  truncated the gitignored handover to zero with no copy to recover.
### Method: reading, measuring, repairing and releasing

How this project reads, measures and repairs. The accounts are C-268
and the ids beside each rule.

**A reading is a hypothesis.**
- **A SITE OR A HARM NAMED BY READING IS A HYPOTHESIS, AND IT READS
  EXACTLY LIKE ONE SOMEBODY PROVED.** A refusal's location was reasoned
  from the source and copied into four documents, all naming a method
  the path never reaches (C-129); three of nine hunt claims described
  the code correctly and cost a user nothing, because a second
  mechanism answered first (C-53); a claim's mechanism is usually
  right and its harm usually is not, and a claim that has stopped
  reproducing is not a claim that is tested (C-138). A cause inferred
  from a curve's shape stood in four documents until GDAL was asked
  (C-205). Measure the site; walk the harm to a loss.
- **A REPORT ABOUT A VERSION OR A BEHAVIOUR IS FIRST A QUESTION ABOUT
  WHICH BUILD IS INSTALLED** (C-137). When a reproduction will not
  reproduce, measure the session that is broken: a dump in the
  reporter's hands answered in a minute what six reproductions here
  could not (C-85). A reproduction can stop reproducing because a
  neighbouring rule moved its door (C-68), and the design a claim is
  driven on can refute a real defect (C-199).
- **A RECORDED DECISION OR QUESTION IS A HYPOTHESIS TOO**: check its
  premise still holds before spending anybody's attention on it -- the
  `publish_candidate` question had been moot since every measuring
  step went `continue-on-error`. A workflow's name is not its
  contract; when a gate surprises you, open the gate rather than the
  prose about it (C-217), and a gate can be satisfied by a sentence
  denying it (C-54).

**A measurement is a measurement only under its own conditions.**
- **A RATE FROM TOO FEW DRAWS IS NOT A MEASUREMENT**: ask how many draws
  would tell it from zero, and print each arm's conditions beside its
  verdict (C-242). A comparison across two runs on a busy machine is
  not a measurement (C-206); when CI timings move, compare the suspect
  on a machine you control before believing the ordering (C-110). A
  projection is not a measurement, so quote a division as a division
  and say which way it is likely to be wrong. A figure with no
  instrument beside it is folklore: name the code that made it in the
  same sentence and re-run it before quoting it again (C-202). Profile
  the thing a person waits for, since the cost is often not where the
  subject is (C-182).
- **PROVE THE QUANTITY THE FAILURE MEASURES, NOT ONE THAT SOUNDS
  EQUIVALENT** -- is this the number the red run prints? (C-151.)
  Verify against what shipped, not what you wrote, where a publish
  step stands between the file and the reader. Every excerpt from a
  log is dated before it is read, since a glob is how a stale log
  reads as current (C-98). OGR hands back a datetime in its own
  format, so a value copied out of a row is a display (C-207).

**Repairing.**
- **WHEN A CHANGE BREAKS A TEST, BISECT BY DISABLING AFTER ONE
  HYPOTHESIS FAILS** (C-87); when three attempts fail, the approach is
  wrong rather than the constant, and leaving the symptom visible beats
  a fourth. Decide above the thing, not inside it: a function that
  promises one class must not return another. Targeted runs cannot
  find what they do not name (C-17). A fix applied to a twin that does
  not have the fault, or where the fault cannot be reached, is dead
  code that reads as protection (C-103, C-195); a dedupe written for
  an unreachable harm is deleted, not kept (C-170). When a helper must
  answer differently for two callers, look at the callers rather than
  write a second definition (C-24). After changing
  behaviour, re-audit the nearby docstrings.
- **CHECK UPSTREAM'S ACTUAL SEMANTICS BEFORE REIMPLEMENTING** -- the
  unclassed ramp is a linear Normalize, categorical sampling is
  `int(x * N)` and not `round()` (C-18). Upstream moves without
  bumping its version, so record the commit (C-180); a dependency's
  refusal can stop being true while the rule it justified stands
  (C-229); a patch that rewrites another patch's output takes its
  marker with it (C-241). The label/key separation touched thirteen
  product sites and 121 suite sites (C-204).

**Releasing and documents.**
- **A DOCUMENTATION EDIT CANNOT INVALIDATE A CANDIDATE**, because the
  receipt digests only what ships (C-216) -- and a documentation edit
  CAN turn a running suite red, because
  `test_every_documented_command_still_exists` opens four documents,
  which is why they are in `STAGE_DEPENDS` (C-187, C-218). A GitHub
  release body preserves single newlines, so never hard-wrap one
  (C-96); a list item needs the space after its marker.

## Inbox: lessons not yet themed

A lesson that fits none of the five themes above goes here as one
clause with its id, and this section holds six at most: past that the
check asks for them to be folded into the themes. It is empty now.

## Testing (do this after every substantive change)

Self-contained suite, synthetic data, runs under QGIS's bundled Python:

    bash tests/run_tests_macos.sh          # macOS, auto-detects the app

The environment is DISCOVERED by `tools/macos_qgis_env.sh`, which the
macOS CI job also calls, so the runner and this machine cannot disagree
about how to start QGIS's Python. It picks `QGIS_PREFIX_PATH` by asking
QGIS AGAINST A THROWAWAY PROFILE: the prefix decides where QGIS finds
the style database every stock ramp lives in, and a wrong one let the
plugin start, tile and render with NO RAMPS AT ALL for months, unseen
here because this machine's profile carried 63 ramps the plugin had
seeded. A measurement about a fresh install is made somewhere nobody
has been. (C-317.)

Dialog tests run offscreen with a stub iface (see `tests/run_tests.py`);
QMessageBox popups block headless runs, so live/silent code paths exist —
don't add unconditional modal dialogs to generation paths.

## Design decisions already settled (don't relitigate silently)

Confirmed with the user via an explicit design review:
- One layer per tile element in a layer-tree group; the old single-layer
  rule-based renderer output was deliberately removed.
- Generate replaces the group in place; hand styling survives unless
  that element's dialog assignment changed (signature comparison in
  `dialog._add_output_layers`). Choosing "Create new" in the group
  chooser is the comparison escape hatch -- and since 2026-08-30 it is
  the ONLY door to a second map, the standing "Create as new group"
  checkbox having been retired (see the ruling below).
- Renderers are seeded standard QGIS objects (graduated/categorized/
  single); refinement belongs to QGIS's styling dock, not a plugin UI.
- **COLOUR BELONGS TO QGIS.** Ramps come from QgsStyle, and where a
  name means something there already, QGIS's meaning wins; the plugin
  installs only palettes QGIS LACKS, tagged "mapweaver", additive only
  -- and "lacks" is answered by the style library, never by what QGIS
  can generate. (`/grill-me`, 2026-08-15; C-38, C-294.)
- Optional GPKG output embeds styles; live update renders a first map
  as soon as a layer and variables are in place (no button press) and
  is gated: memory-mode output only, estimated tiles ≤
  LIVE_UPDATE_MAX_TILES, and no-op runs skipped via _run_signature.
- Preview shows the tile unit with ONE ring of neighbouring copies by
  default (shells=1), with subtle centroid-anchored tile-id labels.
  This changed from shells=0 on 2026-08-08 at the user's instruction:
  the bare unit hides insetting and the joins between tiles, which are
  exactly the properties someone is inspecting the design view to
  judge. The unit alone remains one click away.
- "Quant: Unclassed" (50 linear intervals) reproduces a CONTINUOUS
  RAMP rather than a class count anybody chose. The fifty steps come
  from upstream's semantics (n_classes=0 → a linear Normalize), which
  is why it is fifty and not invented; see
  bridge.make_graduated_renderer. What it samples is whatever ramp
  QGIS resolves the name to, which since 2026-08-15 is explicitly
  QGIS's business rather than matplotlib's -- the derivation settles
  the SHAPE of the reproduction, not whose colours fill it.
- A style-only change NEVER re-tiles. `_geometry_signature()` decides:
  when it is unchanged, `_restyle_only()` re-seeds the existing layers
  in place. Ramp, scheme, class count, single colour, class source,
  reversal and opacity are all symbology; family, spacing, modifiers,
  switches, region layer, output path and the set of mapped variables
  are geometry. A run asked for a NEW GROUP always takes the full
  path.
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
- **AT MOST THREE SIGNIFICANT FIGURES IN ANY NUMBER BOX.** (Maintainer's
  rule, 2026-08-17, after a tester met spacing showing six decimal
  places of metres.) Figures rather than decimal places, deliberately: a
  figures rule bounds what a reader takes in whatever the magnitude,
  where a decimals rule lets 1234.567 through at four and clips 0.0008
  to nothing. (C-39.)
- The region-outlines layer is drawn cased, a wide white line under a
  narrow black one, so boundaries stay legible over pale and dark
  parts of the pattern alike.
- The design view draws NO outline around its tiles. The preview
  exists to judge whether the shapes read as distinct elements by
  colour and form, and a dark hairline round every tile competes with
  exactly that; it also thickens relative to the tiles as the spacing
  gets finer, so a detailed pattern became a mesh. Tile boundaries on
  the MAP are a separate control and unaffected. (User instruction,
  2026-08-09.)
- The colour-legibility warnings (two elements a reader may not be
  able to separate, in ordinary vision or with a red-green
  deficiency) are OPT-IN, behind "Warn about lack of legibility in
  colour choices" on Map options, unchecked by default. They are a
  second opinion on a cartographic choice rather than a fault, and
  while somebody is still trying ramps they would fire on nearly
  every intermediate state, which is how a warning becomes something
  people learn to ignore. Both places the check can fire — after a
  run, and on closing the Categorical colour editor — are gated by
  the same box. (User instruction, 2026-08-09.)
- **The Categorical colour editor** (`category_editor.py`, the "Edit
  colours" column) lets a user set a colour per value. Settled by
  `/grill-me` on 2026-08-08; the decisions are the user's and should not
  be quietly revisited. Values come from the REGION layer, so the button
  works before anything is generated — accepting that at a coarse
  spacing it can list a value no tile carries. (C-40.)
- **A CATEGORICAL SCHEME COPIES LIKE A GRADUATED ONE, AND IT
  OVERWRITES.** (Maintainer's rulings, 2026-08-20, after a tester
  reported the control simply missing: it was kept off the categorical
  half by two gates, the editor building its Copy row only where
  GRADUATED bounds exist and the categorized call site passing neither
  the targets nor the callback.) The copy takes the style, the ramp, the
  Reverse, the per-value colours, the catch-all and the class source,
  which travels as a FILE REFERENCE so the two elements go on agreeing
  -- accepting that a moved file then costs two elements rather than
  one. (C-41.)
- **ONE THRESHOLD FOR "TOO MANY CATEGORIES", AND BOTH DOORS ASK IT.**
  (Same day.) Nothing capped the count: `bridge.py` takes
  `n = max(len(everywhere), 1)`, so a categorical style on a
  CONTINUOUS column draws one class, one legend line and one swatch
  per value -- thousands on real data, and the likeliest cause of a
  report that switching datasets felt slow. `bridge.MANY_CATEGORIES`
  is a hundred, and it is a QUESTION rather than a refusal: a column
  of a hundred and twenty codes is a reasonable thing to categorize
  and only the person looking at it knows whether their legend can
  carry it. Two doors reach that state -- copying a scheme onto an
  element, and retaining one across a change of region dataset -- and
  they share the number so there is one thing to explain and one thing
  to guard.
- **A NEW REGION DATASET: THE RULE IS THE COLUMN NAME.** (Same day.)
  Changing the region layer KEEPS an element's setup where the new data
  has a column of that name and DROPS it where it does not, the element
  then auto-assigning as the recovery rule of 2026-08-15 already says
  for a layer whose file has moved. (C-42.)
- **A CHANGE OF REGION DATASET: THE EIGHT RULINGS OF 2026-08-21 AND
  24.** (Settled by grilling on a demo that surprised its own designer
  and a colleague's file silently overwritten; preamble and sequencing
  in C-295.)
  1. THE OUTPUT PATH CLEARS on any change of region layer, same-schema
     included, and the clearing is announced; re-generating the same
     dataset still overwrites in place.
  2. THE NEXT GENERATE AFTER A SWITCH BUILDS A FRESH GROUP through the
     door a person uses to ask for one; the previous dataset's map
     stays; A-B-A makes a third group.
  3. A DROPPED COLUMN TAKES ITS WHOLE SCHEME -- mode, ramp, Reverse,
     class count and class source -- exactly the set a COPY overwrites.
  4. OPACITY STAYS WITH THE ELEMENT; the single colour is kept silently
     as an unworn style.
  5. THE DESIGN NEVER RESETS, WITH ONE DOOR: where the new dataset
     SEEMINGLY has fewer usable columns than elements the plugin ASKS,
     naming both numbers and what Yes does; Yes recomposes to that
     count, No keeps the design with columns shared. The question says
     concretely what it will do and hedges the count, since the
     heuristic is a guess. (This modal is on the layer-change path; the
     no-modal rule guards generation paths.)
  6. THE MEMORY IS KEPT AND WIDENED: everything a switch deactivates is
     recorded by element AND field and comes back on return. What stays
     ACTIVE changes; what is REMEMBERED does not.
  7. THE SAME-NAME CARVE-OUT STANDS: setups follow surviving column
     names, and the hundred-values question guards a column that keeps
     its name while changing its kind.
  8. NO RESIDUE OF ONE DATASET -- COLUMN NAMES INCLUDED -- MAY STEER OR
     REACH ANOTHER. (2026-08-24.) Field-keyed memory lives in
     PER-DATASET BANKS keyed by layer id, swapped by
     `_swap_dataset_memory`. A carve for "variables in common" was
     built and ended the same day: hand-picks are keyed by VALUE
     STRINGS and pins hold data-derived NUMBERS, so carrying them to a
     same-named column would put one dataset's confidential values
     into another's file, and nothing tells "same wards, next year"
     from a coincident name. So the STYLE keeps by name and VALUE-LADEN
     RECORDS NEVER CROSS; sharing a ladder across files is an explicit
     act; guarded at the file's bytes. Accepted: a re-added layer is a
     new identity, and keep-by-name outranks the bank.
  A CHANGE OF DATASET IS LEAVING A DATASET THIS SESSION HAS BUILT FROM
  -- `switched_from_work` in `_on_layer_changed` is the one place the
  boundary lives -- so a recovery, an auto-landing in a busy project
  and a pre-generate fiddle are not switches. Three lessons from
  enforcing it: when a ruling starts producing a second artefact by
  default, re-drive every path that assumed one; when a rule is about
  "the thing in force", ask what NULLS the record you read and whether
  that is a user's act or a cleanup; and the chooser is never the only
  door. (C-245.)
- **THE OUTPUT GROUP IS THE UNIT OF WORK: THE RULINGS OF 2026-08-25.**
  (Grilled on a colleague's demo report: three scopes answered one act
  three ways with none named on screen -- "too hard to be reliable".
  It completes the rulings above and retires `_fresh_group_for_new_data`
  and much of the bank's job. Full account C-296; C-246, C-247.)
  1. THE DIALOG CARRIES A DROPDOWN OF OUTPUT GROUPS beside the region
     chooser, with a "create new" entry; the group already exists in
     QGIS and already carries its identity in `weavingspace_region`.
  2. DATASET AND GROUP ARE BOUND SYMMETRICALLY, with signals blocked.
  3. WHERE A DATASET OWNS SEVERAL GROUPS, choosing it selects the most
     RECENT, read off the project's layer order rather than remembered.
  4. THE WHOLE WORKING STATE BELONGS TO THE GROUP -- design, spacing,
     modifiers, icon mode, every element's variable, style, ramp,
     Reverse, class count, class source, colours, pins and opacity --
     in the group's custom properties; selecting a group RESTORES it,
     so nothing is inferred. THE RESTORE WHITELIST IS THE RECORD'S REAL
     DEFINITION: a key missing from it is dropped in silence on
     reopen, so widen the list in the same commit as the record.
  5. THE GEOPACKAGE IS RESUMABLE, the source coming back BY REFERENCE,
     with EMBEDDING THE SOURCE an explicit opt-in.
  6. ELEMENT TABLES ARE TRIMMED to the symbolised variable plus the
     identifiers, named `tiles_<tid>_<variable>`; adoption still reads
     the old `tiles_<tid>`; a GeoPackage folds case. Trimming is safe
     only because of 5: a variable switch re-tiles from the source.
  Under the binding, A-generate-B-generate-back-to-A lands on A's own
  group, which is what ruling 2 was reaching for through a proxy.
  REJECTED, so nobody re-litigates it silently: rewind to one shot
  (save, never resume), which had the strongest argument and cost the
  one behaviour the colleague singled out as working; and keeping
  inference with the design in the bank, which would move the design
  under the user twice on A-B-A. Decided on the two-relationships
  principle: persistence is a duty at the QGIS boundary and a design
  question at the dialog's own controls.
- **TWO RULINGS OF 2026-08-26.** THE FILE SHOWS THE LIMIT OF WHAT IT
  CONTAINS: work for fields the map does not display never reaches
  the GeoPackage; the PROJECT carries the whole working memory home in
  each group-record element's `kept` map, which rides the .qgz and
  never the file, and `_file_safe_state` strips the file's record at
  every write. Resuming from the file alone restores the displayed
  design and not the unworn-field memory, which is correct under the
  principle. AND THE SWITCH DOOR SPEAKS: a switch that re-points
  elements whose column the new data lacks says so, naming the new
  layer; a switch where every column survives stays quiet, and so do
  recovery and group selection. (C-297.)
- **TWO MORE RULINGS OF 2026-08-26**, each settling two rules that
  gave one act two answers. THE RETURN LEG RESTORES THE CHOSEN
  VARIABLE: the shelf entry IS the earlier choice and is popped on
  restore, so A-B-A gives the person's column back whether or not a
  run happened to land. THE STYLE FOLLOWS THE FIELD, NOT THE ELEMENT:
  the mode banks per element AND field (`_mode_by_field`), so a
  field's return wears its own style and no forced re-click retires
  the picks. Parity was measured first, which is what made these
  rulings rather than defects. (C-298.)
- **THE FIVE RULINGS OF 2026-08-27, SETTLED BY GRILLING AND BUILT.**
  (Converting the suite to press Save found four real defects on
  ordinary journeys, C-248; the two decisions taken while building
  are C-249; full account C-299.)
  1. SAVING IS A POSITIVE ACT. A path chooser records and does nothing;
     SAVE writes the map as it stands -- tables, styles, the resumable
     record, the stale-table drop and the embedded source together --
     and LOAD reads one back. Generate DRAWS; auto-generate never
     writes. Save asks before overwriting a file the plugin did not
     write. Live update's output-path gate is deleted, having nothing
     left to guard.
  2. UNTICKING "INCLUDE THE SOURCE DATA" MEANS IT IS NOT IN THIS FILE:
     the `weavingspace_region` table is dropped at Save, and only that
     table.
  3. AN OUTPUT PATH NEVER DECIDES WHICH GROUP A RUN LANDS ON; the
     chooser alone does.
  4. A RAMP IS REMEMBERED UNDER THE MODE THE ROW IS IN, not under the
     ramp's own family -- a row remembers what it wore in each mode.
  5. DONORS ARE SEEDED BEFORE THEIR FOLLOWERS, reading the donor's NEW
     layer, so a change reaches its follower in the same run; seeding
     order is separate from panel order, and a cycle keeps the one-run
     lag and settles.
- **THE GROUP CHOOSER IS THE ONLY DOOR TO A NEW GROUP.** (Maintainer's
  decision, 2026-08-29; built 2026-08-30.) Two controls armed one fact:
  the chooser's "Create new" entry, which is ONE-SHOT, and a "Create as
  new group" checkbox on Map options, which was a STANDING preference
  read at every landing. Nothing on screen said which was which, and the
  READERS DISAGREED -- five sites asked only the checkbox, one only the
  flag, and exactly one asked both, that one only since ledger row 36 of
  2026-08-28, where the chooser went on describing a landing that would
  not happen. (C-43.)

- **THREE TABS ARE EXPERIMENTAL UNTIL DESIGNATED OTHERWISE, BEHIND A BOX
  THAT STARTS UNTICKED.** (Maintainer's ruling, 2026-08-30.) Messages,
  Topology and Legend are gated by an "Experimental features" checkbox
  on Map options -- the third tab, which is where the ruling put it.
  Until it is ticked the tabs cannot be activated and their titles are
  greyed; `QTabWidget.setTabEnabled` is both halves of that in one call,
  so "greyed" and "not activatable" cannot come apart later. (C-44.)

- **NUMBERS STORED AS TEXT ARE CLASSIFIABLE.** (Maintainer's ruling,
  2026-08-29.) A graduated renderer over WORDS returns no ranges; over
  NUMERIC STRINGS it classifies exactly as the integer twin, so the old
  rule was wider than its evidence and cost a choropleth to anybody
  whose numbers came through a CSV join. `_field_is_numeric` is the
  one owner, STRICT -- "mostly numbers" is a column with something
  else in it -- and it asks that every value parse to a number of its
  OWN, since "3", " 3" and "3 " are three legend classes drawn as one.
  (C-250, C-300.)
- **A SAVE PRESSED WHILE A RE-TILE IS COMING IS KEPT, NOT REFUSED.**
  (Maintainer's ruling, 2026-08-29, overruling a repair of the day
  before.) With live update on, changing the design arms the live timer,
  and a press inside that window used to write the map on screen -- the
  one the person had just changed away from. ASK OF ANY REFUSAL WHAT IT
  COSTS THE PERSON WHO DOES NOT READ IT. (C-45.)

- **A ROW ARRIVING IN CATEGORIZED SWAPS A SEQUENTIAL RAMP AWAY, AND
  RULING 4 REMEMBERS THE RAMP UNDER THE MODE**: a test that leaves a
  categorized row wearing `YlGn` has taught it that choice, and the
  flip hands it back. Neither rule was wrong. (C-46, C-301.)
- **A FULL SUITE FINDS WHAT A TARGETED RUN CANNOT REACH**: the first
  one on the branch found the user guide naming an element ceiling an
  order of magnitude under what the plugin draws (C-47, C-302).
- **TWO ELEMENT CEILINGS, NOT ONE.** (Maintainer's ruling, 2026-08-27.)
  Weaves keep `a`..`z`, since a weave is specified as one character per
  strand; tilings run `a`..`z` then `aa`..`zz`, capped at sixteen by
  sixteen because `tightest_grid` makes 256 exactly that. And `"aa" <
  "z"`, so `bridge.element_order` is the one owner of the sort and
  every site reads it. (C-251, C-303.)
- **AN OUTPUT GROUP IS NAMED FOR THE DATASET IT WAS MADE FROM** --
  `WeavingSpace tiles — nyc blocks`, a counter only where the name is
  taken -- and the name is a LABEL, never an identity: the lookup asks
  the layers and renaming is the user's business. When you change how
  a label is composed, grep for whoever decomposes it. (2026-08-26;
  C-252, C-304.)
- **A KEPT SCHEME IS HELD, NOT OWNED.** An element whose class-source
  file cannot be read keeps the colours it is drawing, RECORDED as held
  (`_kept_for_unreadable`) rather than as picks, banked and stamped
  like a pick, and released the moment the file answers again, BEFORE
  anything is seeded from them. It reconciled two registered tests
  that each demanded half: when two settled rules give one act two
  answers, the answer is usually both, with the thing that tells them
  apart written down. (2026-08-26; C-253, C-305.)
- **THE SIZE GUARD ASKS; ONLY WHAT IS NOT A SIZE IS REFUSED.**
  (Maintainer's ruling, 2026-08-25: "Warning not absolute. Find a
  different approach to sentinel if appropriate.") Above
  `MAX_TILES_CONFIRM` a run is confirmed in ordinary words; above
  `MAX_TILES_HARD` the SAME question is put in stronger ones -- this may
  use all the computer's memory, QGIS may stop responding, save your
  project first -- with the safe button as the default, on the
  dependency-consent precedent. (C-59.)

- **A region layer with no CRS is tiled as it is, and its output says
  so.** QGIS permits a layer with no CRS and users sometimes want one
  (a floor plan, a scanned map, a diagram), so the plugin gets on with
  it: no reprojection, no warning, tiles in the layer's own
  coordinates. What it must NOT do is invent a CRS on the way out. A
  memory layer whose URI names no CRS is given EPSG:4326 by QGIS, so
  `gdf_to_layer` clears it explicitly when the frame has none;
  otherwise coordinates in the thousands ship labelled as degrees,
  placing the map off the edge of the world and inviting QGIS to
  reproject it. (User instruction, 2026-08-09: "if there's no CRS
  that's fine just proceed" and "no CRS shouldn't have a warning".)
- **A quantitative style never stands on a text field.** A graduated
  renderer over words comes back with no ranges at all, so every tile
  falls outside every class and the layer paints NOTHING — a group of
  full-looking layers drawing an empty map, reported as success. The
  correction is made in `_assignments`, which every consumer reads,
  and again in `_on_mode_chosen` so the chooser never goes on
  describing a map the plugin will not draw. The user is told.
- **A constant numeric column gets ONE class, and a notice.** Asked for
  five classes over a column that is 7 everywhere, QGIS returns five,
  all reading "7 - 7" in five different colours. The map was never
  wrong; the legend was, and the legend is what a reader trusts.
  `make_graduated_renderer` collapses to k=1 and the dialog reports it
  -- UNLESS the element is pinned, for which see the ruling below.
  (C-61.)
- **ONE COLOUR MEANS ONE THING, wherever it appears — and the rule is
  about MEANING, not about breaks.** That wording matters and cost a
  year: it was written down as being about class BREAKS, so when the
  graduated half was fixed on 2026-08-14 nobody looked at the
  categorized half, which had the identical fault and had been shipping
  since 0.23.0. Categorical colours follow ListedColormap sampling —
  code/(k-1) through int(x * N) — so the NUMBER of categories decides
  which colours are drawn, and a value one element happens not to
  contain re-colours everything after it. (C-62.)
- **CLASS BOUNDS A PERSON SET, and the record that holds them.** Added
  0.24.3, settled by `/grill-me`. A user may PIN the first and/or last
  class and type its inner bound: the samples inside a pinned class
  leave the pool, the scheme cuts the row's count minus one class per
  pin, and the pinned classes are put back around the result with the
  outermost computed edge SNAPPED to the pin so the ladder has no gap.
  (C-63.)
- **THE PLUGIN'S TABLE FOLLOWS THE LAYER'S RENDERER, AND THE SCOPE OF
  THAT IS THE WHOLE OF ITS SAFETY.** (Maintainer's ruling, 2026-08-17,
  on breaks retyped in QGIS's panel reaching the plugin not at all,
  and the next Generate destroying them.) (C-72, C-306.)
- **AN UNCLASSED END IS NAMED BY TWO CONTROLS, AND THEY MUST AGREE.**
  (Maintainer's instruction, 2026-08-17, reversing a decision of the
  same week.) Unclassed used to get no Pin column -- fifty faded slivers
  are a preview, and pinning row 0 of fifty is a strange way to say "the
  ramp starts at 10" -- so a clamp strip above the table said it better.
  (C-74.)
- **ONE HATCHING NOW, AND THE OTHER WAS WITHDRAWN.** Thin 45-degree
  diagonals say "no pin can go here" in the PIN COLUMN, and that is the
  only place they are drawn. The ramp swatch used the same mark for "no
  tile wears this class" until 2026-08-17, when the maintainer ruled it
  out: users are not used to it, so it confuses rather than helps.
  (C-75.)
- **A tiles inset that swallows elements is refused in terms of the
  inset.** Insetting shrinks every tile by a fixed distance, so past
  some value the narrower elements disappear. Left to itself the
  library's overlay refuses the surviving slivers and the user meets
  "ValueError: You have passed make_valid=False along with 1978 invalid
  input geometries"; when every element goes, the table empties and the
  variable guard fires instead, telling them to assign a variable to a
  design with nowhere to put one. (C-76.)
- **The plugin follows the layer, and adapts where the answer is
  unambiguous.** QGIS is live and the dialog is not modal to it, so a
  user can delete features, simplify geometry in place, rename or retype
  a field, reassign a CRS or filter the layer while the plugin is
  pointed at it. Both signatures therefore carry a fingerprint of what
  the layer CONTAINS, and the dialog connects to the layer's own signals
  for edits a fingerprint cannot see (a value retyped, a vertex moved
  inside the bounding box). (C-77.)
- **NULLs are kept out of class breaks, and that is a WORKAROUND with an
  expiry test.** QGIS's classifier counts a NULL as zero while its own
  `minimumValue()` excludes nulls, so QGIS disagrees with itself and the
  classifier wins: a column with gaps gets a spurious 0-0 class and
  every break shifted toward zero, on a map that looks perfectly
  plausible. (C-78.)
- **The dependency consent dialogue states what can be checked.**
  `deps.py` downloads wheels from PyPI where QGIS lacks the scientific
  stack or carries a version below the floor — most often Linux, where
  QGIS uses the system Python, but the trigger is "missing OR too old"
  and can fire anywhere. That is the most intrusive thing this plugin
  does and the thing a QGIS plugin repository reviewer will examine
  hardest, so the dialogue (`plugin.dependency_consent_box`) names the
  packages, the source (PyPI), the exact destination folder, what is NOT
  touched, how to undo it, and what declining costs — and the buttons
  say what they do, with the SAFE one as the default so a stray Return
  cannot start a download. (C-79.)
- **Raster sources are not a case here.** A COG, a WMS or any other
  raster cannot be a region layer: the region chooser filters to
  polygon layers, and the tiling joins data to POLYGONS. Raster-backed
  data reaches this plugin only after somebody has vectorised it,
  which produces an ordinary vector layer covered by everything above.
  Worth writing down because "what about cloud raster data" is a
  reasonable question with a short answer.
- **A layer the plugin cannot count is a snapshot, and says so.** WFS,
  OGC API - Features, an ArcGIS service and PostGIS can all change
  server-side with no local event, and may report `featureCount()` as
  -1 or an estimate. An explicit Generate always re-tiles such a
  layer; live update does not chase it, because polling somebody's
  WFS endpoint unattended is not a thing to do behind their back, and
  the user is told once that live update cannot track this source. A
  layer with QGIS's own auto-refresh enabled IS followed, since
  turning that on is the user declaring the data dynamic.
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

- **CLASS BOUNDS: THE RECORD HOLDS FOUR ENDS, AND TWO OF THEM ARE WEAKER
  THAN THE OTHER TWO.** (Maintainer's decisions, 2026-08-19.) `pinned`
  gained `floor` and `ceiling` beside `low`, `high` and `breaks`. `low`
  and `high` name BOUNDARIES BETWEEN CLASSES -- the first class's upper
  and the last class's lower -- so each takes its class out of the pool
  the scheme cuts from, can cross its neighbour, and can be refused.
  (C-90.)

- **A LIMIT MAY EXCLUDE, AND WHAT IT EXCLUDES IS DRAWN.** A floor or
  ceiling inside the data puts values out of bounds, and those areas
  become a FOURTH KIND OF ABSENCE beside no data and the two infinities:
  drawn, in a colour a user picks, with their own legend line. (C-91.)

- **NO PIN COLUMN: A HEAVY OUTLINE ON THE BOX SAYS THE NUMBER IS
  YOURS.** (Maintainer's instruction, 2026-08-19.) One convention for
  all four ends rather than two, no table width, and nobody reading a
  glyph at twelve pixels. (C-92.)

- **PRESERVE, DO NOT REPAINT.** (Maintainer's ruling, 2026-08-19.)
  With live update off the map is deliberately NOT refreshed on its
  own -- the table and the map may disagree until the user asks -- and
  what must hold is that the change is NOT LOST. When a dock edit must
  survive a landing, the answer is to stop the landing CLOBBERING it,
  by making the row follow the renderer so nothing re-seeds; it is
  never to repaint from a timer, which is the plugin acting unasked.
  Reconcile through the door the landing already uses rather than a
  second one invented for the case.


- **A CONSENT DIALOGUE THAT ENUMERATES IS DIFFED AGAINST WHAT THE CODE
  FETCHES** -- it named the scientific packages and the provisioner
  also fetched their pure-python support distributions, seven for
  three, against the metadata's own promise (C-128, C-307). And a gate
  that reads raw source text can be moved by a comment (C-127, C-308).
- **A HANDLE IS A POSITION, NOT A DELTA, AND A CONTROL'S SHAPE SAYS
  WHAT IT DOES.** Travel passed through a lever is a gain factor nobody
  can see and was tuned wrong twice; a hover state is not a substitute
  for a glyph that reads as its own effect (maintainer's standard,
  2026-08-31: easy to use, easy to learn, perceivable). (C-161, C-181,
  C-309.)
- **A VARIABLE SWITCH TAKES THE RESTYLE PATH: THREE RULINGS OF
  2026-09-05, NOT YET BUILT.** (1) Where a switch makes or unmakes a
  no-data twin it DECLINES and rebuilds, since `_restyle_only` cannot
  make or unmake a paired layer. (2) So it is an EXTENSION of the
  restyle path: the bare variable name leaves the geometry signature
  and `_needs_a_no_data_split` stays in it. (3) It does not ship
  without a differential over THAT path -- feature by feature, field
  names included, on nulls in different places, a constant column,
  two values against five classes, and a permutation of two elements'
  variables -- because the three previous narrowings of the signature
  were each a wrong map that looked right, and the existing
  differential exercises the full-run path. (C-310.)
- **THE ZIGZAG HANDLE: FOUR RULINGS OF 2026-09-05.** (Field reports 3
  and 4, one glyph; the offset was a static 60px while the comment
  claimed it was the amplitude. Full account C-311.) (1) THE DISTANCE
  FROM THE EDGE IS THE AMPLITUDE, so the zero sits on the edge and
  `_handle_at` is nearest-wins -- HALF of the library's `h`, which is
  peak to peak, since a handle at the whole of it showed a wave 2.1
  times the one the map got (C-320). (2) ALONG-EDGE TRAVEL SETS THE COUNT,
  past a deadband of a tenth of the edge sized from the glyph, and
  the count SNAPS because the stops are the counts. (3) THE HANDLE
  SITS ON THE WAVEFORM'S FIRST PEAK, `length / (2n)` along, so the
  preview passes through it. (4) THE ALONG-POSITION IS CLAMPED 15px
  clear of both vertices, and above the count where the clamp bites
  the readout says it is no longer exact. (5) THE WAVE IS GHOSTED ON
  THE EDGE while zigzag is chosen, cresting at the handle, with four
  painted, never-clicked cues -- deeper, shallower, tighter, wider --
  each a miniature of what it produces, computed at paint time and
  stored nowhere. Two more, grilled later the same day (C-319): (6) A
  CLICK THAT SLIPS UNDER HALF A SEAT IS A CLICK: the amplitude's
  threshold is travel from where the handle was grabbed, sized from the
  glyph as the count's deadband is, since 1% of the edge was under a
  pixel at the window's floor and recorded an invisible wave. (7) THE
  COUNT IS EVEN, 2 TO 8, a typed odd count settling up, on the
  library's own word that zigzag works only for even n; and the
  readout's clamp STANDS, the box carrying the count past where the
  drag is exact.
- **THE DUAL: FIVE RULINGS OF 2026-09-05.** (Field report 5; the
  measurements are R-79, the refusals and the gaps distinction C-312.)
  (1) "Map the dual instead" is a BUTTON, "Generate the dual and tile
  it", landing in a new group named `<group> — dual`. (2) THE DUAL IS
  COMPLETED HERE AND OFFERED UPSTREAM, one tile per source vertex; the
  button refuses in words a design with no topology or a dual short
  of full cover, so a map with holes never ships. (3) It goes into
  0.24.4 and rc16 waits for it. (4) THE DUAL GROUP'S RECORD IS THE
  SOURCE DESIGN PLUS THE EXISTING `map_dual` TERM, shown as a label;
  Generate on it re-tiles the dual; it is one-shot and does not follow
  its source -- and it is the dual of the design AS EDITED, since the
  record carries the source's edits and the tab shows them (C-325);
  DUALS CHAIN (maintainer's ruling of 2026-09-06, superseding the
  refusal C-326 records): the button is offered on a dual group and
  takes the dual of the dual, the record carrying one frozen edit
  list per dualisation and the shelf key, the stamp and both
  signatures a DEPTH; the way back to an earlier geometry is that
  group in the chooser (C-334). (5) ITS ELEMENTS ARE
  ASSIGNED FRESH. Refused: a frozen
  snapshot, and a derived group that follows its source. A design's
  gaps are a different question from the dual's holes (R-40 stands).
- **THREE CONFLICTS SETTLED THE SAME DAY, AND FOUR STRUCK.** THE SHELF
  KEY STAYS NARROW AND REPORTS AT REPLAY: each edit records the class
  alphabet it was made against, and where a design's classes have
  moved the replay applies what matches and says which edits now aim
  at a changed design -- a spacing or modifier tweak never puts
  somebody's edits away. THE RECORD'S READER ASSIGNS THE FIRST n
  ELEMENTS and keeps the surplus as memory, so a record may be a
  superset and is never a lie. THE COMPARISON PDF MEASURES THE VENDOR
  at its recorded commit and says so; the web-app claim is dropped
  rather than re-measured. STRUCK because their premise had dissolved:
  the mutation workflow (R-31), the element slider (built 2026-09-01),
  the colourspace limit (dE 0.3-0.4 here and green on three
  fresh-profile runners), and the window ceiling (1480 since
  2026-08-29). The eight as they stood: R-79.

- **THE SIX DECISIONS OF 2026-09-01.** All four approved features into
  0.24.4 (measurements in C-313; C-262). MULTI-CLASS SELECTORS: click
  to select, a list to confirm, each following the other with signals
  blocked; the record needs nothing, an edit's `classes` being a string
  selector. CAIRO IS A RENAME, NOT A FAMILY, so the chooser's items
  carry the catalogue KEY as data and show a LABEL, the record stores
  the key, and no saved file moves. THE DUAL IS BUILT HERE AND OFFERED
  UPSTREAM, behind one function with a canary, since `Tileable` has no
  constructor for supplied geometry. THE SYMMETRIES ARE DRAWN in our
  painter from upstream's data and GATE `push_vertex` with the reason
  where a class's stabiliser leaves it nowhere to go -- necessary, not
  sufficient. THE ELEMENT SLIDER KEEPS ITS RANGE AND THE FLIP SPEAKS
  when a weave crosses 12 into tilings.
- **NOTHING ENDS WHILE A SAVE IS OUTSTANDING.** (Maintainer's ruling,
  2026-09-01.) A waiting window holds a quit or a window close while a
  save is promised or being written, says what it waits for, and
  offers Cancel; a quit is DELAYED rather than vetoed. Cancel abandons
  the save; "save it" at a close means WAIT FOR THE REDRAW, never write
  what is on screen. Account in MAINTAINING.md. (C-314.)

## Cross-version compatibility targets

QGIS 4+ only (PyQt6, Python 3.12+), on the major platforms. Enums in
scoped form (`Qt.AlignmentFlag.AlignCenter`); `QAction` imports from
qgis.PyQt.QtWidgets (QGIS 4 shims it there). compat.py holds the QGIS
4 spellings and absorbs future transitions.

## The original library: its role and how to upgrade it

The vendored `weavingspace_qgis/vendor/weavingspace/` (upstream
v0.0.7.89) does ALL the mathematics and cartography — unit
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

The tool copies the new upstream and re-applies every plugin patch,
asserting on exact upstream anchors and NAMING any patch whose anchor
no longer matches instead of writing a broken vendor. FOUR FAMILIES
ARE CARRIED, not one: the optional matplotlib/scipy imports (1a-1e),
which are about our packaging, and THREE PERFORMANCE PATCHES offered
upstream -- the join lookup's pandas idiom (3), the grid disc that
reaches only what the region occupies (4a-4d), a caller's declared
rotations (5a-5d) and the overlay that clips only what straddles (6).
The table in MAINTAINING.md says which is which and where each was
offered; the measurements and probes are in docs/PERFORMANCE.md.
EACH OF THE THREE IS EXACT rather than merely fast, proved tile by
tile, which is what makes them safe to re-apply without re-deciding
them -- and a patch that stops changing the output is one upstream has
taken, so retire it rather than re-anchoring it. Never hand-edit vendor files: a hand edit is lost at the next
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
   rewrites source files); run it IN FULL before substantial
   releases, via `tools/mutation_catalogue_sweep.py`, which shards
   the catalogue across concurrent clones (judging parallelises
   safely; suites do not) and names anything needing a solo re-run.
   Details and the honesty caveats in docs/MUTATION-LOOP.md.
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
   IT IS GIVEN THE COLOURS IN FORCE rather than naming matplotlib's,
   since 2026-08-15: the gallery writes `ramp-colours.json` beside its
   renders and the comparison registers those under their own names,
   so both sides draw with whatever ramp QGIS resolved. What it tests
   is therefore where the breaks fall, how categories are sampled, the
   reduction, insetting, weaving and geometry — everything that can be
   wrong except whose palette answered to the name, which is no longer
   a claim this project makes. It also means the gate can no longer
   pass because of one machine's seeded style library, which is how it
   passed before.

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

THE REFERENCE COLUMN MEASURES THE VENDOR, AND SAYS SO. (Maintainer's
ruling, 2026-09-05.) The PDF's reference is `TiledMap.render` from the
vendored library at the commit `VENDOR-VERSION.txt` records, and that
is the whole of its claim: the web app pins a library thirty versions
behind, so a sentence saying the column "speaks for both" measured
nothing, and a live browser capture was refused rather than deferred.
(C-263, C-318.)
