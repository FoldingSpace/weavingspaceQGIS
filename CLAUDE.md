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
  A SECOND SANCTIONED USE, settled 2026-08-16: PROVENANCE. README.md
  and docs/index.html say the plugin "echoes and extends our earlier
  (also handwritten) web-based interface", inside the paragraph about
  who wrote this and how, and the maintainer ruled that fine. The rule
  forbids explaining what the software DOES in terms of something the
  reader cannot see; it does not forbid saying where the software came
  from. A prose hunt raised it on 2026-08-16 and the answer is here so
  the next one need not.
  WORTH KNOWING WHILE YOU READ THAT: `check_standards` greps for
  `web app` and `MapWeaver`, so that sentence passes because of its
  wording rather than because the checker understands the exemption.
  If the rule is ever tightened, tighten the checker and declare this
  as an exception in the same commit -- an exemption that survives
  only by synonym is not an exemption anybody decided.
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
  unversioned zip.) Two halves, and the first is the one that bites.
  `check_before_push` replays CI's `standards` job, one step of which
  is "The plugin still packages"; that runs `build.py`, which writes
  `dist/weavingspace_qgis.zip` into whatever worktree it is invoked
  from. So the PUSH GATE mutates the artefact directory, from an
  ungated tree, every time anybody runs it. Measured that day: an
  unversioned 649,327-byte zip sitting an HOUR NEWER than the gated
  `weavingspace_qgis-0.24.4rc5.zip` at 649,330 -- not the same bytes
  -- beside three versioned candidates and their receipts. Sorted by
  date, which is what a person does in a file browser, the first thing
  in a directory of gated artefacts was the one with no version, no
  receipt and no gate behind it.
  THE CANDIDATE PATH WAS ALREADY RIGHT, WHICH IS THE TELL: every
  pre-release attaches `weavingspace_qgis-<version>rc<n>.zip`, and
  only the RELEASE path attached an unversioned one. The convention
  existed and had been applied to half the process.
  AND THE README FOLLOWS THE ARTEFACT, not the other way round. The
  unversioned name was defended here on the ground that README tells
  people to download it; the maintainer's answer was that the README
  can and should change. A gated artefact's name is a fact about which
  tree it came from, and prose is the cheaper of the two to move.
  This is the same family as "a candidate number is spent by anything
  bearing it": one name over two trees confuses everybody, and an
  artefact with no name at all is that hazard with the label removed.
- **EVERYTHING FOR THIS PROJECT LIVES INSIDE THE PROJECT DIRECTORY.**
  (Maintainer's rule, 2026-08-29: "nothing associated with this
  project should be outside of the weavingspace-qgis-plugin ... the
  claude scratch is shared by everyone".) Worktrees included -- they
  may live anywhere git allows, and that is not a reason to scatter
  them through a shared folder. Five had accumulated there and a dozen
  more under `/private/tmp`.
  RETIRE A WORKTREE WHEN ITS WORK IS MERGED OR ABANDONED, and know
  that REMOVING A WORKTREE DOES NOT DELETE ITS BRANCH -- which is what
  makes retirement safe here, since `check_roadmap --merge` looks for
  `for-<version>/*` BRANCHES and would fail if one went missing. Check
  that after any clean-up rather than trusting it.
  AND MOVING THE LIVE ONE IS USUALLY THE WRONG SHAPE: the tidiest end
  is to check its branch out in the project directory itself and
  retire the outside folder, which puts everything in one place
  instead of relocating a second copy. Anything gitignored --
  `dev/`, `dist/`, `reports/` -- has to be carried across first, and
  every colliding file backed up rather than overwritten, because
  those directories are exactly where the things git is not protecting
  live.
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
  metaphor of a thing wearing its symbology had spread through this
  project's own prose -- some fifty-odd uses across the package and
  the binding documents -- and it reached the user exactly once, in
  the icon-mode coverage notice written on 2026-08-19, which is where
  the maintainer met it and ruled it out. It reads as ours rather than
  as plain description, and a reader meeting "these areas wear an icon"
  has to translate before they can act. (Maintainer's rule,
  2026-08-19.) The existing internal uses are NOT swept: rewording a
  phrase that appears inside settled-rule language in CLAUDE.md,
  docs/TESTING.md and the generated documents is its own decision, and
  the rule binds new prose from here.
- **Canadian spelling in all user-facing text**: colour, colourmap,
  behaviour, and -ize verbs (symbolize, categorize, organize). Code
  identifiers that mirror a QGIS or matplotlib API keep that API's
  spelling (`colors_to_use`, `setColor`); everything a user reads uses
  the user's spelling.

## Required practices

- **A DAY THAT FINDS MANY DEFECTS GETS A LEDGER, and the ledger is
  COMMITTED.** `docs/process/defects-2026-08-17.md` is the model: one
  row per defect with what a user lost, where it lives, when it
  arrived, and an OWES column naming exactly which of
  test-and-catalogue-entry it still lacks -- plus the open ones, with
  their reproductions and any attempted fix that FAILED and why not to
  repeat its shape.
  IT EXISTS BECAUSE THE OTHER THREE PLACES CANNOT HOLD IT. ROADMAP.md
  carries only what is outstanding, so a defect fixed without a guard
  drops out of it; `dev/state-of-play.md` is gitignored and rewritten
  every session; and a conversation ends. On 2026-08-17 twenty-six
  defects were found in one day and eleven fixes went in without
  guards -- exactly the state that is invisible everywhere else and
  reads as finished.
  Write it when a session passes roughly ten defects, point at it from
  ROADMAP.md and from the handover, and keep the OWES column honest:
  `--` means the fix rests on its hunt's reproduction alone, which is
  not what this project calls fixed.

- **WHEN A ROUND OF HUNTS IS PROPOSED, THE CONSISTENCY SWEEP IS
  PROPOSED BESIDE IT, WITH A REASON FOR CHOOSING ONE.** (Maintainer's
  instruction, 2026-08-26: the creativity offered once must be on offer
  again in the rc process, alongside the hunts rather than instead of
  them.) Every rc round so far has reached for hunts by default, and
  the record says that is right only when the ground is FRESH: 573,967
  tokens bought one confirmed defect when a round was aimed at old
  code, and four hunts of eight landed on one line when it was aimed
  at new. A hunt samples the space by intuition and its real cost is
  the verification queue, which runs in the maintainer's context.
  THE ALTERNATIVE IS TO ENUMERATE WHAT HUNTS SAMPLE. This project's
  defects are not evenly distributed over shapes -- most of one day's
  ledger is ONE FACT HELD IN SEVERAL STORES, MENDED IN ONE -- and a
  shape that recurs that reliably can be swept mechanically, by three
  invariants that need no oracle and leave no claim to judge:
  AGREEMENT (every store holding a fact agrees about it), COLLATERAL
  (an act about one element moves no other), and RETURN (doing a thing
  and undoing it comes back). One flag covers every kind of act: a
  CONTROL act must change something, a BOUNDARY CROSSING -- closing
  the plugin and opening it again, saving and reopening, choosing a
  group -- must change nothing. Full argument, cost and first findings
  in docs/process/HUNT-RECORD.md under "WHAT TO RUN INSTEAD OF A HUNT".
  Hunts keep the directions that cannot pattern-match, which is what
  the portfolio rule already reserves a third of a round for.
- **Documentation standard**: all new code carries docstrings and
  section comments written for a weavingspace-literate, QGIS-naive
  maintainer — explain each QGIS/Qt concept at its point of use. This
  is an explicit user requirement; match the density of the existing
  modules. It applies to **everything this project writes** — the
  plugin package, `tools/`, `tests/`, `build.py` and `release.py`
  alike — and not merely to code inside the plugin folder. The
  checker enforced it on the package only until 2026-08-09, which
  left the tooling ungoverned while that tooling grew to rewrite
  shipped source, decide the mutation score and write into a user's
  QGIS profiles. `vendor/` is the one exclusion, because it is
  upstream's code held verbatim: our conventions there would either
  be discarded at the next re-vendor or fail forever. (User
  instruction, 2026-08-09.) Specifically:
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
- **Generated documents are regenerated, never remembered.**
  `docs/TEST-MAP.md` and `docs/BUG-REGISTER.md` are produced from the
  suite — the map from the `check()` registrations, the register from
  the `Regression:` lines — so neither is ever hand-edited and both
  are regenerated whenever the suite gains, loses or renames a test:

      python3 tools/test_map.py
      python3 tools/bug_register.py

  A generated document nobody regenerates is worse than none, because
  it keeps its authority while losing its accuracy, and the map is
  consulted precisely when deciding where to write tests next. This
  used to rely on somebody noticing — the register drifted for a
  whole session and was corrected only when the user asked — so it no
  longer relies on anyone: `tools/check_standards.py` recounts both
  with the GENERATORS' OWN rules and fails when either document
  disagrees with the suite, and `release.py` regenerates both. If you
  add a test and the standards check complains, it is telling you to
  run the two commands above, not to edit a number. (Made enforced
  2026-08-09, after the user pointed out they kept having to ask.)
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
- **EVERY CANDIDATE IS PUBLISHED TO GITHUB AS A PRE-RELEASE, and that
  is part of the process rather than a separate permission.**
  (Maintainer's instruction, 2026-08-21, making standard what had been
  done by hand ten times.) A candidate that passes every gate is
  published with `python3 tools/publish_candidate.py --notes <file>`:
  a tag `v<version>rc<N>` on the candidate's own commit, a release
  titled `<version>rcN — release candidate`, marked PRE-RELEASE so it
  never becomes Latest and never displaces a real version, carrying
  the three things a tester needs -- the zip they install, the
  per-test report, and the colourspace comparison PDF.
  THIS DOES NOT LOOSEN THE RULE BELOW IT. Publishing a RELEASE --
  tagging on `main`, making something Latest -- remains the
  maintainer's explicit call, and `release.py` still refuses anywhere
  but `main`. What changed is that a CANDIDATE, which promotes
  nothing and leaves `main` untouched, no longer waits on a second
  permission: testers cannot test what has not been sent to them, and
  the ten that went out before this were each published by somebody
  remembering to.
  THE TOOL REFUSES rather than guesses, and each refusal is one of the
  ten hand-published candidates' chances to go wrong: no receipt
  matching the tree, so only a GATED candidate can be published; a tag
  already taken, since a candidate number is spent by anything bearing
  it; CI on that exact commit not green, because the body SAYS it is
  and a body claiming a verdict nobody read is worse than one that
  says nothing (override with `--despite-ci <reason>`, which prints
  the reason IN the release); and no notes, because a candidate
  nobody described is a candidate nobody knows what to test.
  THE NUMBERS IN THE BODY ARE READ, not typed: the suite and gallery
  counts come out of the testing report, and the CI sentence out of
  `gh`. Guarded by `test_a_candidate_is_published_only_when_it_is_
  gated`.

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
- **Work for a LATER version lives on a branch named for that
  version, and everything owed by a version is written in
  ROADMAP.md.** Two ways work goes missing, both closed by the same
  gate. A branch written for a release and never merged: branches are
  named `for-<version>/<slug>`, so work parked for 0.24.1 cannot
  reach 0.24.0 by accident and work meant for 0.24.0 cannot be left
  out of it. And an idea nobody wrote down: ROADMAP.md holds
  branch-backed entries AND things wanted with no code yet, because
  an idea that lived only in a conversation is gone when the
  conversation is.
  `tools/check_roadmap.py --merge` is the FIRST stage of every
  release -- before standards, before the suite -- and it merges
  branches due for this version, refuses when the version's roadmap
  section still lists outstanding work, and stops rather than
  resolving a merge conflict, because a conflict is a question about
  intent. DEFERRING an entry to a later version is legitimate and is
  the USER'S decision: it is made by moving the entry to a later
  section, an edit no tool may make on their behalf. Delete an entry
  when it lands; a roadmap nobody prunes becomes a diary.
  (User instruction, 2026-08-11.)
- **THE PLATFORM QUESTIONS RUN FIRST ON EVERY LEG, so a second
  machine's answer costs minutes rather than an hour.**
  `tools/platform_probe.py` runs before the functional suite on
  Windows, macOS and the Linux matrix, and holds the tests whose
  verdict is decided by something this development machine cannot
  vary honestly: font metrics, locale, and how a window manager
  assembles a dialog. Together they take seconds.
  IT WAS PAID FOR ON 2026-08-29. The assignment table's columns were
  taught to grow to their content, the window's ceiling stopped
  binding on any platform whose fonts are wider than this Mac's, and
  Windows reported it SEVENTY-FIVE MINUTES into its job -- in three
  tests and two locales, every one quoting 1729px against a 1480px
  budget. The fix cost another round to confirm. Nothing local could
  have caught it: in the suite's own environment the window's minimum
  is SMALLER than the table's, so the cap has nothing to bind and the
  case is unreachable here at any font.
  IT DOES NOT REPLACE THE SUITE and nothing may be moved out of the
  suite into it. This is the release gates' cheapest-first ordering
  applied to CI: a fast refusal earns its place precisely because the
  expensive measurement still follows.
  THE LIST OF TESTS LIVES IN THE TOOL, not in `ci.yml`, because a
  list of names in YAML is a hand-kept list nothing can check -- and
  a name in it that no longer exists in the suite is a FAILURE there
  rather than a skip, since a probe silently running four tests where
  it names five is the matches-nothing-reports-nothing fault this
  file already records twice.

- **EVERY CI PLATFORM IS KEPT AS CLOSE TO THE LOCAL SUITE AS
  PRACTICAL.** Linux, Windows and macOS alike: the standard is PARITY
  OF COVERAGE with what this machine runs, not the existence of a job.
  A platform that only proves the plugin loads has been smoke-tested
  rather than tested -- and `compat.py` exists precisely because QGIS
  moves its APIs, so the functional suite, the visual gallery and the
  colourspace comparison belong on every platform CI can reach.
  Windows is where most of this plugin's users are, and until
  2026-08-15 it ran nothing but an install-and-load. (Maintainer's
  instruction that day: Windows and Linux should test as much as
  macOS does, within only the limits GitHub imposes that we cannot
  code around; restated that night, once a macOS runner existed, as
  every platform staying as close to the local suite as practical.)
  THE MACOS LEG EARNED ITS PLACE ON ITS FIRST COMPLETE RUN, and the
  reason is worth keeping: it is the only leg that runs the package a
  macOS user actually installs, in a profile nobody has seeded, and
  it immediately found three faults this machine cannot show -- a
  bundled interpreter that will not start without PYTHONHOME, a
  QGIS_PREFIX_PATH that had been wrong for months and left QGIS with
  NO COLOUR RAMPS AT ALL, and eight palettes dropped as duplicates of
  ramps a fresh QGIS does not have. Each was masked here by a style
  library the plugin seeded years ago, which is the same masking that
  let the colourspace gate pass on one machine's profile.
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
  still running a command this check can SEE. `macos` was missing
  from that last list on the day the job was added, so the newest
  platform was the one that could go quiet without failing anything;
  corrected 2026-08-15 and proved by hushing it in a throwaway copy. That last clause was added
  2026-08-15 with the Windows job: a job whose invocation is
  rewritten into a shape the pattern no longer matches drops out of
  the existence check without failing anything, which is the
  matches-nothing-reports-nothing fault the mutation catalogue had
  found the same day. Nothing there is a hand-kept
  list, so the two cannot drift apart quietly.
  THAT LAST SENTENCE WAS FALSE FOR SIXTEEN DAYS and is true now. The
  stage list `EXPECTED_STAGES` in `release.py` IS hand-kept and was
  the only thing this check read, so a stage added there and
  forgotten got no CI job, no written exemption and no complaint --
  and two were already outside it, the release notes and the
  pre-commit secrets audit. The sibling test compares listed against
  called and never called against listed, so it could not see it
  either. `check_standards` now reads every `run(...)` name out of
  `release.py` and requires each to be listed, which is what makes
  the sentence true by construction. Found 2026-08-28 by an
  instruments audit that planted a stage the gate had to catch, with
  the control run first -- which is the practice to copy, because
  every claim it made came as a pair.
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
  are not.** Two different questions, and they were conflated: the
  rule above is about keeping a pre-candidate PUSH small, and it had
  leaked into .gitignore as though the repository should be quiet
  about how the work is done. It should not. `docs/process/` carries
  the test-campaign records, the perceptual colour findings and the
  note sent upstream -- including its retraction of a diagnosis that
  blamed somebody else's commit, because a project publishing only
  its correct diagnoses is publishing a fiction.
  What stays out is what has no reader but the next session:
  one-shot patch scripts, scratch, and `dev/state-of-play.md`, which
  is rewritten every session and whose durable content is promoted
  into these binding documents as it earns its place -- publishing it
  would duplicate them in a less reliable form. The test is not "is
  this tidy" but "who reads this, other than us tomorrow".
  (User instruction, 2026-08-11.)
- **EVERY push to a branch CI watches is a push that gets watched,
  not only the pre-candidate one.** The rule below was written for
  the pre-candidate push and read as though ordinary commit pushes
  were a different kind of act. They are not: `ci.yml` runs on all of
  them. On 2026-08-12 the branch went red at 07:52 on the text-review
  gate and stayed red for EIGHTEEN pushes across six hours, while
  work continued on top of it, and it surfaced only because the
  maintainer forwarded a GitHub notification. Nothing in the process
  was looking. So: after a run of commits, ask what the last push
  did -- `gh run list --branch <branch> --limit 1` is one second --
  and never let a session end without knowing the branch's colour.
  The specific trap here is worth naming, because it will recur: the
  local checks all passed the whole time. `check_standards` and
  `check_no_secrets` are green on a tree whose text-review queue is
  full, because approving prose is the USER'S act and no local gate
  may do it. A gate only a person can satisfy is exactly the one that
  goes unsatisfied for six hours. So the local habit is now ONE
  command, and it reads its own contents out of `ci.yml`:

      python3 tools/check_before_push.py

  It runs every step of the `standards` job in order -- currently the
  rule check, the secrets audit, the text-review check, the
  published-content audit and the packaging check -- and says out
  loud which steps it could not run rather than passing over them. A
  hand-kept list of somebody else's checks drifts, silently, and the
  drift is found by the thing the list was meant to prevent; add a
  step to that job and it runs here from the next invocation with
  nobody editing anything. It does NOT run the QGIS jobs, which is
  what CI is for. (2026-08-12.)
- **Linux CI runs BESIDE the local gates, not after them, and its
  fixes are made in a WORKTREE, and the push is watched.** A CI
  watcher is armed in the same breath as the push and reports
  twice -- run appeared, run finished with each job's verdict --
  because its SILENCE after a push means the run was never
  created (usually org Actions policy), which is worth knowing in
  a minute rather than twenty. Push the branch first so GitHub's
  runners (about twenty minutes) are already answering while
  `release.py --rc` reads the working tree for ninety; then fix
  whatever CI reports in `git worktree add ../ws-ci-fixes`, never in
  the frozen tree, and merge when both have answered. A candidate is
  promoted only when local gates and the Linux matrix are both
  green. The worktree part is not fussiness: editing a tree that a
  gate or a sweep is reading produced two spoiled measurements in one
  night. Procedure in docs/PUBLISHING.md. (User instruction,
  2026-08-10.)
- **What CI needs is never paid for out of what a user is promised.**
  The QGIS containers ship no scientific stack, so CI must provision
  geopandas and the rest before the suite can run -- and the plugin
  can already do that, behind the consent dialogue. The forbidden
  shortcut is a flag or environment variable letting CI skip the
  dialogue, because it would put a consent-free download path into
  the SHIPPED plugin, which is the one thing a plugin repository
  reviewer looks hardest at. The provisioning therefore lives in
  `tools/ci_provision.py`, outside `build.shipped_files()`: a
  maintainer running a program that installs packages is consent,
  software installing them unasked is not.
  `test_pypi_provisioning_is_reached_only_through_consent` holds the
  line across every shipped file and is in the mutation catalogue.
  Calling the plugin's OWN provisioner rather than pip is deliberate
  and is the point of the Linux leg: wheel-tag matching, the numpy
  1.x floor, the support-package fetch and the pyproj data
  redirection only ever execute there. Full reasoning in
  docs/PUBLISHING.md. (2026-08-11, after the first Linux run.)
- **Do not re-run a gate the release is about to run.** The gates
  are ordered cheapest-first for exactly this reason: standards and
  secrets take seconds, and the FUNCTIONAL SUITE IS THE FOURTH STAGE,
  so a failing suite aborts a candidate about twenty-four minutes in
  having cost little more than the suite itself. Running that suite
  standalone "to be safe" beforehand therefore buys no earlier
  warning and doubles the wait; the same goes for the coverage
  record, the gallery and the reference comparison. Run a subset
  while iterating (`tools/run_some.py`), then go straight to
  `release.py --rc` and let the gates do the whole-tree work once.
  The habit this replaces cost roughly forty minutes per candidate
  and was justified by a belief about the gate order that was simply
  wrong. What DOES belong before a candidate is the cheap work the
  gates only CHECK rather than perform: regenerate `docs/TEST-MAP.md`
  and `docs/BUG-REGISTER.md` (the standards check compares them
  against the suite and stops the build on a stale count), and settle
  the text-review queue, which is the user's act and cannot be done
  by a gate at all. (User instruction, 2026-08-10, after noticing the
  duplication.)
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
  output and would act on it.** Three left within a day (2026-08-11
  and 12), about eighty minutes of every candidate between them: the
  new-code mutation guard, which quoted a blended figure it was told
  never to quote and could not finish inside the window it gated; the
  per-test coverage record, whose only consumer had just left; and
  the coverage report, half an hour that gates nothing by its own
  docstring and that six candidates in one night never once read.
  `--quick` was retired with the last of them, having nothing left to
  skip. What did NOT leave is the contrast worth remembering: the
  visual gallery at 7 seconds and the colourspace comparison at 16,
  because both catch a WRONG MAP, which is this software's
  characteristic failure -- a wrong map looks exactly like a right
  one. Twenty-three seconds against eighty minutes. Before adding
  anything to a release, and periodically for everything already in
  it, ask who reads the output and what they would do differently; if
  the answer is nobody, or nothing before the artefact ships, it
  belongs on demand or on somebody else's machine, reporting.
  Details in docs/PUBLISHING.md.
- **`--resume` exists so a defect in the MACHINERY does not cost a
  re-run of the SOFTWARE's gates, and it is opt-in.** Three
  candidates were abandoned in one evening (2026-08-11), each after
  most gates had passed, and not one of the three faults was in the
  plugin. `release.py --resume` skips a stage that passed before
  against exactly the inputs it has now; without the flag nothing is
  ever skipped, because a full run is what a release means. What
  counts as unchanged is `STAGE_DEPENDS`, narrower than the tree and
  wider than what ships: editing `tests/run_tests.py` retires the
  suite's answer though no shipped byte moved, and a fix to
  `tools/coverage_per_test.py` retires the coverage record and
  nothing else. The documents the suite READS are in that list,
  because `test_every_documented_command_still_exists` opens them and
  has failed twice on prose. A skip must be honest as well as fast:
  the four stages whose output is used may only be skipped when that
  output survives in `reports/stage-logs/`, and the saved text is
  handed back, since a report quoting an empty capture describes
  nothing. Every skip announces the time the stage first passed.
  Guarded by `test_resuming_skips_only_what_still_holds`. A candidate
  meant for PROMOTION is built by a run that measured this tree;
  resume is for recovering from an interruption, not for avoiding
  measurement. (2026-08-11.)
- **A release is published FROM `main`, and release.py refuses
  anywhere else.** `--push` runs `git push origin HEAD`, so it sends
  whatever branch you are standing on, and a tag does not care what
  branch it is on. Promote from a pre-candidate branch and the result
  is a perfectly real GitHub Release sitting beside a project page
  and a README that still describe the PREVIOUS version, because
  Pages serves `docs/` from `main` and the repository's front page is
  `main`'s README. Nothing in git objects; only somebody visiting the
  page finds out. So the sequence has a checkout in the middle of it
  -- `git checkout main && git merge --ff-only pre-<version>rc<n>` --
  and `release.py` stops before committing or tagging if you are
  elsewhere, naming that exact command. It refuses rather than
  merging on anyone's behalf, because merging is a decision, and
  `--ff-only` is the guard: if it will not fast-forward, something
  reached `main` that this candidate never saw. The fast-forward
  leaves the tree byte-identical, so the receipt still matches and
  nothing is re-measured. Guarded by
  `test_a_release_publishes_from_the_branch_the_page_is_served_from`.
  (Found 2026-08-11 while writing the sequence out, before it had
  been done wrongly rather than after.)
- **A release PROMOTES a candidate; it never re-derives one.** A
  candidate that passes every gate writes a receipt
  (`dist/CANDIDATE-<label>.receipt.json`) holding a digest of exactly
  the files that ship, taken with `build.py`'s own `shipped_files()`
  so the two rules cannot drift. `release.py` then REFUSES unless a
  receipt matches the tree in front of it, and having found one it
  skips the suite, gallery, coverage and reference comparison — those
  measured this artefact already, and re-running them would measure
  whatever the tree looks like now rather than what somebody
  installed. Change one shipped byte after the candidate and the
  release stops and says which case it is. The digest deliberately
  ignores tests, tooling and documentation: those cannot change what
  a reviewer ran, and a gate that fires on a comment in the suite is
  a gate people learn to route around. Guarded by
  `test_a_release_needs_a_matching_candidate` and
  `test_the_release_digest_watches_what_ships`. (User instruction,
  2026-08-09: a release must not be triggerable except on a clean
  candidate, and must not redo work the candidate already did.)
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
  THAT CAN RUN IT, AND MUST REFUSE OTHERWISE.** `mutation_check`
  launched every test with `sys.executable` -- and this project's own
  rule is to invoke that module as `env -u PYTHONHOME -u PYTHONPATH
  python3`, because a plain python3 carrying the QGIS environment dies
  at bootstrap. The interpreter that leaves you with is the SYSTEM
  one, which has no QGIS, so every test died at `import qgis.core` and
  a test that "failed" is scored CAUGHT. On 2026-08-19 the catalogue
  therefore reported success for seventeen entries in a row, including
  one whose test was later proved unable to fail by construction.
  THE SHAPE IS THE ONE THIS FILE ALREADY NAMES TWICE: a check that can
  only confirm is not a check. Ask of any harness what it does when
  the thing it drives cannot start at all -- if the answer is
  indistinguishable from success, that is the defect, whatever else is
  true. The tool now resolves `QGIS_PY` and refuses to judge anything
  when that interpreter cannot import qgis, naming the command that
  fixes it. A harness that stops is worth more than one that reports,
  because its verdicts get written down.
- **A catalogue entry that matches nothing REPORTS nothing, which
  reads exactly like success.** Each entry in `tools/mutation_check.py`
  finds its `old` text in a source file and replaces it. When that
  text is edited away, the entry applies no mutation, finds no
  survivor and exits clean: the behaviour it names is unguarded while
  the catalogue still lists it, and the count of entries goes on
  overstating how much is actually held. Found 2026-08-15 with SEVEN
  of 243 entries in that state — five orphaned by the constant-column
  rework the day before, two by the same evening's own fixes — and
  the first re-anchored entry then SURVIVED, because either of two
  branches now delivers its result and mutating one alone changed
  nothing its test could see. `tools/check_standards.py` now reads
  every entry with `ast` (the entries name their file through module
  constants, so a literal-only reader finds none, which its own count
  caught on the first run) and fails when an anchor is absent. Two
  habits go with it: when you edit a line, expect to re-anchor the
  entry standing on it, and when a mutation is CAUGHT, check it was
  applied rather than trusting a clean exit.

- **One changelog, TWO RENDERERS, and it must read in both.** The
  `changelog=` entry is shown by QGIS's plugin manager, which
  displays the metadata text as it stands, and by the GitHub release
  page, which renders MARKDOWN -- where single newlines fold into one
  paragraph. The categorized shape settled on 2026-08-13 therefore
  worked in the plugin manager and arrived on the release page as a
  wall of prose, because `release_notes.entry_for` collapsed the
  entry with `" ".join(...)` before GitHub ever saw it. Found and
  fixed 2026-08-14; the entry is now emitted as an opening paragraph
  plus one bullet per category, and `test_the_release_notes_keep_
  their_categories` holds the line.
  The general rule, which is what the next person needs: WHEN ONE
  TEXT IS SHOWN BY TWO RENDERERS, CHECK IT IN BOTH BEFORE BELIEVING
  IT READS. Same words is a virtue -- it is why the plugin manager
  and the release page cannot drift -- but it is not the same as
  same appearance, and this project reached for the first and assumed
  the second. That applies beyond the changelog: `about` in
  metadata.txt, the README against the project page, and any
  message that might one day be shown in a rich widget as well as a
  plain one.
  AND A THIRD RENDERER IS THE ONE THAT CUTS THE ENTRY OUT. (Row 31
  of 2026-08-27.) The entry is delimited rather than stored: an entry
  ends at a lookahead for a line opening with digits. Opening the
  0.24.4 section INDENTED the previous version's header instead of
  stripping its `changelog=` prefix, so `    changelog=0.24.3 You
  decide...` was no longer a header to that pattern, and the 0.24.4
  entry ran on through the whole of 0.24.3 -- thirty-one bullets of
  an already-shipped release under this one's heading, and a field
  name in the middle of what the plugin manager displays.
  ITS OWN TEST COULD NOT SEE IT, and that is the transferable half:
  the test reads the CURRENT version's entry and requires a paragraph
  then bold bullets, which TWO ENTRIES JOINED END TO END satisfy
  exactly. A shape assertion cannot tell one record from two. Where a
  tool cuts one record out of a document holding several, assert the
  CUT -- that the piece stops where the next begins and carries none
  of its neighbour's furniture -- and not merely that the piece is
  shaped like a piece. The guard walks every version header in the
  field now, and the catalogue entry
  `an-entry-stops-where-the-next-version-starts` stands on the
  boundary itself.
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
- **A ceiling a healthy run can reach is worse than no ceiling, and
  is sized from the SLOWEST machine ever measured.** Made twice on
  2026-08-11, hours apart: a forty-minute CI job limit sized against
  a twenty-four-minute macOS suite (the Linux legs took 52-54 THAT
  DAY -- measured again on 2026-08-31 at 60, 66 and 68 minutes for the
  three of them, the suite having grown to 727 tests since, which is
  why the figure is dated rather than stated flat: an entry warning
  against sizing a ceiling from a stale number is the last place a
  stale number should sit -- and
  one leg was cancelled mid-run), and a six-hundred-second per-test
  watchdog against a test that had already been measured at 550 on a
  Linux runner. Both produced a red result that meant nothing, which
  is precisely how people learn to ignore red results -- the same
  argument this project already makes for keeping the visual gallery
  out of CI. Before setting any limit, find the slowest MEASURED
  figure and multiply, rather than reasoning from the machine in
  front of you; and when the same code takes 392s, 486s and 550s on
  three legs of one run, the spread is the runner and the limit has
  to clear all of it. A stall watchdog is for catching a HANG, not
  for enforcing a performance budget.
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
  finish -- a sweep reporting shards done from logs left by a run
  killed hours earlier, a catalogue sweep announcing CLEAN after
  judging one entry of 156 because its listing had crashed, a census
  measuring a tree that had since changed beside a second census, and
  a worker from an abandoned run still writing into the log a new run
  was appending to. Each would have produced a number somebody
  believed, and none showed up in a final "done" line. Full procedure
  in `.claude/skills/long-job-supervision`. (User instruction,
  2026-08-10, after watching the beats catch them.)
- **Five procedures live as SKILLS, and the rules here name them so
  they get invoked.** `.claude/skills/second-machine` is read before
  adding CI to anything, when a suite that passes locally fails
  elsewhere, and before concluding that a second machine's failure
  is a defect in the code -- most are assumptions, and today's first
  Linux run was seventy failures of which sixty-nine were one
  missing package and exactly one was a real product defect.
  `.claude/skills/long-job-supervision` now also covers HOW to shard
  rather than only that one should, because the first sharded run
  here produced slices that disagreed about the size of the suite. `.claude/skills/tests-that-can-fail` is read
  before writing or reviewing a test, and whenever a new test passes
  first time — it catalogues the ways a test passes without
  exercising anything, which this project has produced at a rate of
  roughly one in five. `.claude/skills/dependency-bug-workaround` is
  read before compensating for a bug in QGIS or any other dependency;
  it is why the NULL class-break workaround carries a canary test that
  will announce the day QGIS fixes it. Skills record the documents
  they were derived from with a sha256, and
  `tools/check_standards.py` fails when a source has changed since —
  a skill teaching a superseded procedure is worse than none, because
  it is followed with confidence. Naming them here is deliberate: the
  `long-job-supervision` skill already described the CPU-versus-elapsed
  check and the "wait on the process, not on predicted log text" rule,
  and both were rediscovered the hard way in a session that never
  invoked it. Authorship was not the problem; invocation was.
- **The testing documents are binding, are read BEFORE tests are
  written or changed, and are UPDATED the moment one of them is proved
  incomplete.** A lesson learned and not written down is a lesson
  about to be paid for twice, which is the provenance of a good many
  entries in these files. `docs/TESTING.md` holds the shapes that earn
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
- **New code is held to account, but the guard REPORTS REMOTELY and
  no longer gates a candidate.** (Changed deliberately 2026-08-11;
  full reasoning in docs/MUTATION-LOOP.md.) It ran fifty minutes
  against 2,274 changed lines and reached 61.5%, and three things
  were wrong with it as a gate, none of them the threshold being
  inconvenient. It measured the WRONG THING: a blended figure over
  changed lines is what MUTATION-TESTING.md says never to quote,
  since logic runs high and Qt plumbing runs low, and that release
  was mostly plumbing (bridge 4/5 against dialog 10/17). It COST
  more than a candidate can carry: two mutants timed out at
  twenty-one minutes each, three more ran past twenty against
  covering sets of 153 and 221 tests, and fifty minutes bought 28
  verdicts of 80 — and the sample scales with the diff, so a big
  release is when it is slowest. And its RED meant "write tests over
  the next few days", which is a work list rather than a gate; this
  project already made that argument for the visual gallery and the
  catalogue sweep. `release.py` now prints what it would have
  sampled and names the dispatch command; the run happens on GitHub
  and its survivors are triaged into the NEXT candidate. What is not
  claimed is that survivors do not matter: ten came out of the
  half-run that prompted this and they are the 0.24.1 list.
- **The historical form of that rule, for context.** It used to be
  that `release.py` re-recorded per-test coverage and then ran
  `tools/mutate_auto.py --since <previous tag> --require 70`, which
  mutates ONLY the lines that changed and stopped the release if the
  tests written alongside them failed to catch 70% of those mutants.
  The sample SCALES with the diff — floor 12, one mutant per twenty
  changed lines, cap 80 (`release.mutation_sample_size`, pinned by
  its own test) — because a fixed dozen was sized for routine
  releases and became decorative against a 1,700-line round. With no
  release tag to diff against the guard cannot run and now says so
  LOUDLY; the baseline tag `pre-0.24.0` exists precisely so that
  state never recurs. Cost stays proportional to the change, so it
  runs every time, which is the point: a mutation score decays not
  through decisions but through changes that nobody measured. This
  does not replace the periodic full campaign — changed lines are
  where new gaps arrive, but a refactor elsewhere can quietly stop an
  old test reaching what it names, and only full sampling finds that.
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
  DECISION THEY HAVE TO MAKE.** (2026-08-29, and it cost them two
  exchanges.) They asked that the window not take up the whole screen.
  That was written up as re-opening the settled layout rule of
  2026-08-09, needing a fourth priority ordered among three, and
  ending in a question put back to them: how much shorter than the
  screen? Their answer was that they had not meant anything about
  screen height and just did not want it filling the screen. The ask
  was a ceiling on GROWTH, today's size was fine, and no number was
  owed at all.
  THE FAULT IS NOT THE WRONG ANSWER, IT IS INVENTING A QUESTION. A
  request elaborated into a ruling acquires open questions that belong
  to the elaboration rather than to the request, and handing those
  back reads as diligence while actually asking somebody to do work
  the reading created. This file already says a decision is only as
  good as the measurement under it; the other half is that a QUESTION
  is only as good as the request under it.
  THE CHEAP CHECK: state the ask back in the plainest form that could
  be acted on, and see whether anything is still missing. Where the
  plain form is buildable, build it. Reserve the grilling for
  decisions that genuinely fork.
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
  DUTY.** (Maintainer's framing, 2026-08-25, offered while the
  dataset-switch rules were being reopened, and it is the sharpest
  thing said about them.) Much of this plugin's instinct to REMEMBER
  comes from the one context where remembering is an obligation: the
  boundary with QGIS. There the plugin is a guest in somebody else's
  application, and what it holds is the user's own work -- hand
  styling done in the dock, a group they renamed, the stamps in a
  saved project, the tables in a GeoPackage a colleague will open.
  Losing any of that DESTROYS something, and that is why "preserve, do
  not repaint", the follow rules, adoption, and ruling 8's per-dataset
  banks all lean the same way.
  NONE OF THAT REASONING REACHES THE DIALOG'S OWN CONTROLS. What the
  design chooser, the family list, the spacing box and the assignment
  table carry from one act to the next is the plugin talking to its
  user about the plugin, with no third party's work at stake:
  forgetting there costs somebody a few clicks, never a map. So those
  questions are settled on their own merits -- what makes the next
  thirty seconds clear -- and a "we must never lose anything" argument
  imported from the QGIS boundary is not evidence about them.
  WHAT THIS DOES NOT SAY is that the dialog should forget. It says the
  two questions are INDEPENDENT, and that an answer for one must be
  argued rather than inherited from the other. On the settled side:
  hand-picked colours, pinned bounds, everything stamped onto a layer
  or written to a file, and the rule that a landing never writes over
  a map made from another dataset. On the open side, as of this date:
  whether the design travels a change of dataset, what a retained
  scheme follows, and what the design-floor question offers. The
  spacing was the first of the open ones to be decided, and decided on
  its own merits rather than by analogy -- a number a person TYPED
  survives, a number the plugin DERIVED does not.
  ICON MODE WAS ON THAT LIST AND IS NOT OPEN, corrected 2026-08-27.
  Ruling 4 of 2026-08-25 puts icon mode in the working state a group
  restores, the restore whitelist carries it, and a hunt drove six
  boundaries -- group switch and return, project save and reopen,
  GeoPackage resume, dataset switch, off-and-re-generate -- reading
  the node property with plain json, the file with bare GDAL and the
  .qgz out of its own zip. All agreed. A binding file that lists a
  settled question as open is read as current and invites somebody to
  implement forgetting, which is why the clause is struck rather than
  left as harmless untidiness.

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
  **AND WHEN A BATCH OF TESTS IS WRITTEN IN ONE SITTING, POINT A HUNT
  AT THE TESTS, MUTATING PER ASSERTION.** The catalogue proves a
  test's PRIMARY axis and structurally cannot see the rest: it breaks
  one behaviour, the first assertion kills it, and the entry reports
  `caught` while the second and third axes sit dead. Measured here at
  one in five or six, three rounds running, and every time inside a
  test whose first assertion was live and well aimed. The trigger is
  the SITTING rather than any one test, and the procedure -- including
  how an adversarial reader gets it wrong in the other direction, by
  demanding a contract nobody agreed -- is in docs/TESTING.md under
  "THE TRIGGER". Added 2026-08-17 at the maintainer's asking, because
  the practice was already written down twice and skipped both times
  for want of a moment to do it.
- The highest-value shape here is UI-against-library: drive the
  dialog, build the same map by calling weavingspace directly with
  what those settings MEAN, compare geometry element by element and
  then interior pixels. Write the expected side from the settings,
  never from `_build_unit`, or the test agrees with the bug.
- Every test that produces a map checks it visually (`visual_pair` or
  `visual_gamut`), and those checks appear in the release PDF.

**Adding a thing that PAIRS with an existing thing.** (2026-08-16, the
No Data layer. Six defects in one day, all one shape, and the shape
recurs whenever a feature gives an element a second layer, a second
record or a second table.)
- **A PAIRED ARTEFACT INHERITS THE IDENTITY OF WHAT IT IS PAIRED
  WITH**, so every reader keyed on that identity silently gains a
  second answer, and every writer that maintained the original has a
  twin that does not. The no-data layer carries its element's
  `weavingspace_tile_id` because it belongs to that element -- and
  adoption, keyed on that id alone, let the twin OVERWRITE its own
  element, so the next Generate removed the twin and orphaned the real
  layer. Yesterday's map then sat on top of the new one for good.
  GREP THE PROPERTY, NOT THE FEATURE: every reader of the id, every
  per-element dict, every count of a group's children.
- **A NAME THE USER CAN EDIT IS NOT AN IDENTITY, AND MUST NEVER BE A
  KEY.** Every record in `dialog.py` keys on a custom property except
  the output group, which was found with
  `findGroup(self._group_name)` -- so renaming the group in the layers
  panel, which is an ordinary thing to do, made it invisible and the
  next run built a rival over the same four GeoPackage tables, the
  abandoned group redrawing the new data under the old class breaks.
  Adoption had the same fault from the other side, skipping any group
  whose name it did not recognise. Both now ask the LAYERS: within a
  session by asking which group this dialog's own layers are in, and
  on reopening by looking for a group holding a layer that carries our
  custom property. Measured 2026-08-17 through both doors and guarded
  by `test_a_renamed_group_is_still_the_group_the_next_run_replaces`
  and `test_a_renamed_group_is_adopted_when_the_plugin_reopens`.
  The general form, which reaches past groups: anything a user can
  rename -- a layer, a group, a field alias, a file -- is a LABEL, and
  a label is what you show them, never what you look them up by. When
  a lookup takes a string, ask who else can change that string.
- **ENUMERATE WHAT A CLEAR SITE LEAVES**, not what it clears. Three
  places in dialog.py clear per-element state and no two cleared the
  same set; the first two were fixed and the commit message NAMED the
  third, which was then not looked at. Reading the list of records a
  site clears tells you nothing about the record missing from it.
- **WHEN A FIX WIDENS A SIGNATURE, ASK WHETHER THE NEW TERM IS COARSER
  THAN WHAT IT STANDS FOR.** A boolean per element ("does this need a
  split") is INVARIANT UNDER A PERMUTATION, so swapping two elements'
  variables left each holding the other's split -- values drawn as no
  data and gaps drawn as nothing. It carries the field now.
- **WHEN A FIX IS INSERTED INTO AN EXISTING SEQUENCE, CHECK ITS ORDER
  AGAINST THE TWIN**, not merely that the line is present. `setOpacity`
  went in after `embed_style`, so the layer in the project was right
  and the GeoPackage kept 1.0: the map a user sends on was not the map
  they made, and the project's copy being correct is exactly what hid
  it.
- **A GUARD THAT TESTS SIGN DOES NOT TEST FINITENESS.** `span > 0` is
  perfectly true of infinity, and log10 of it overflows through a Qt
  slot, so the button silently does nothing and QGIS shows a Python
  error window.
- **DECIDE ABOVE THE THING, NOT INSIDE IT.** "This cannot be classified
  at all" was implemented inside `make_graduated_renderer`, which
  promises a QgsGraduatedSymbolRenderer and whose callers read its
  ranges; returning a different class from it crashed the dialog on
  the very column the change was about. It belongs in `seed_renderer`.

**Changing something a classifier or a renderer decides.** (2026-08-16,
three withdrawn attempts at one fix in a single afternoon.)
- **MAGNITUDE IS A FIXTURE DIMENSION.** Every fixture in this suite
  lived between 0 and about 50, so arithmetic that is correct there
  and wrong at 1e12 or 1e-9 shipped green three times. A relative
  epsilon is an ABSOLUTE gap: 1e-9 of 2e12 is two thousand, wide
  enough to swallow a real value and draw it as a hole. When a change
  depends on the size of a number, the sweep crosses magnitudes or it
  proves nothing.
- **A LEGEND IS RENDERED BY SOMEBODY ELSE'S FORMATTER.** A bound moved
  by an amount "too small to see" is printed by QGIS at four decimals
  once the value passes about 1e5, so a map of populations or dollars
  showed `100,000,000,000 - 999,999,999,000`. Check what the label
  says, not only what the number is.
- **DO NOT MAKE MEMBERSHIP DEPEND ON THE LAST BIT.** Stepping a bound
  by one ulp made a tile's class depend on a float's final bit, and
  the GeoPackage round trip duly painted 2,413 of 48,948 pixels
  differently. Anything that stores, reloads or recomputes a number
  can move that bit.
- **WHEN THREE ATTEMPTS FAIL, THE APPROACH IS WRONG, NOT THE
  CONSTANT.** Each fix here was a smaller step than the last and each
  found a new way for a real value to fall into the gap it created.
  The withdrawal, with the symptom left VISIBLE instead (empty classes
  hatched), was the right answer and should have come sooner.

**Carrying a record across a run.** (2026-08-16, the paired layer's
renderer, found by a hunt hours after the carry-over was written.)
- **ASK WHETHER THE RECORD DESCRIBES THE DATA OR ONE RUN'S OUTPUT.** An
  element's class breaks come from the whole region and survive a
  re-tile, so keeping them is safe. Its paired layer's CATEGORIES
  enumerate the kinds of absence one tiling happened to produce -- a
  different spacing hands the same element a kind it did not have, and
  a carried categorized renderer has no entry for it AND NO CATCH-ALL,
  so those tiles paint nothing. Gating the twin on the element's own
  question put holes in the map.
- **A CARRIED RENDERER IS KEPT ONLY WHILE IT CAN DRAW WHAT IS THERE**,
  and rebuilt otherwise. Losing a custom fill is visible and undoable;
  an unpainted area is neither, so that is the right way to fail.
- **A RENDERER WITH NO CATEGORIES COVERS EVERYTHING.** A single symbol
  paints every feature whatever its value, which is what somebody
  usually sets in Layer Properties -- treating "no categories" as
  "covers nothing" threw away the very styling the carry-over exists
  to preserve.

**Process.**
- **TARGETED RUNS CANNOT FIND WHAT THEY DO NOT NAME**, and three
  candidate builds aborted proving it (2026-08-16). Each abort was the
  same fault -- something counts or renders an element and looks only
  at `_element_layer_ids` -- and each time it was fixed in the
  instances a keyword search turned up, because the keyword matched
  what had just been fixed. The tests that finally caught the worst of
  it mention neither colour nor class nor no data. Two habits follow:
  when a change alters what a map CONTAINS, grep every reader that
  counts, measures or renders it and fix the SET rather than the
  instance; and do not mistake a green subset for a green suite. The
  full suite in `release.py` is the only thing that found it.
- **A TEMPORARY LIST FROM A QGIS GETTER FREES ITS CONTENTS.**
  `renderer.ranges()[0].symbol()` and `categories()[0].symbol()` read
  memory that has just been released: one segfaulted QGIS outright,
  the other returned a plausible WRONG COLOUR (#000000) that looked
  exactly like the Qt double-ownership bug and sent an hour after the
  wrong cause. Bind the list to a name first, then subscript it.
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
  prefer the Edit tool. Two more ways this bit on 2026-08-13, both
  cheap to avoid. **A slice needs its end searched FORWARD from its
  start** -- `s.index(a)` and `s.index(b)` both search from zero, so
  if b occurs before a the slice `s[:start] + s[end:]` DUPLICATES a
  span instead of removing it, silently, in a file too large to
  eyeball. It happened to two files at once and was caught only by
  counting definitions afterwards. **And assert the postcondition, not
  just the anchor**: `assert "the_removed_name" not in s` before
  writing caught a bad edit that every anchor check had passed. When
  an assertion like that fires, do not widen it to get past -- one
  here was genuinely too broad (`n=n)` matches legitimate code) and
  narrowing it was right, but the reflex to loosen is how a guard
  becomes decoration.
- **A file worth rebuilding is a file worth not editing with string
  surgery.** `dev/state-of-play.md` was truncated to zero the same
  night by a `.split()/.join()` expression that looked fine. It is
  gitignored, so there was no copy to recover; it was rebuilt from the
  session that broke it and carries a provenance note saying so.
  Prefer Edit for prose, and where a script must rewrite a whole file,
  write it to a temporary path and compare lengths before replacing.
- When waiting on a long background run, key the wait on the PROCESS
  ENDING, not on log text you predicted. A watcher polling for "tests
  recorded" sat in a sleep loop for twelve hours because the tool
  actually prints "recorded 75 tests", and its fallback pattern
  ("Error") missed the crash line too, which read "Fatal Python
  error". Silence from a watcher is not evidence that the work is
  still running. Wait on the pid, and if a log must be matched,
  include a case-insensitive alternation broad enough to catch the
  failure modes as well as the success line.
- **SEED a watcher with what is already true before it reports
  anything.** Ten watcher faults on this project by 2026-08-12 and
  the last three were all this one: a poller started with an empty
  "seen" set announces its first sighting as news, so historical CI
  failures and a stage log from the previous night arrive as though
  they had just happened. Each was written within an hour of somebody
  reading the entry describing it, which is the actual finding: a
  watcher is written while attention is on the thing being watched,
  and that is exactly when nobody reviews it. Two other members of
  the family, for completeness -- key on the THING and not a snapshot
  of it (a watcher pinned to one commit sha sat silent while two more
  pushes superseded it), and report every terminal state rather than
  only success.
- **Two watchers must never share a log file.** The eleventh watcher
  fault here, 2026-08-14: a CI watcher was re-armed for a new commit
  while its predecessor was still running, both wrote to the same
  path, and the OLD one appended `FINISHED: cancelled` underneath the
  NEW one's header. Read literally, the file said the live run had
  been cancelled. It had not; the run it described was a different
  one, deliberately cancelled twenty minutes earlier. Key each
  watcher's output to WHAT IT WATCHES (the sha, the run id, the job
  name) rather than to what it is, and when a log looks wrong, ask the
  source directly before believing it. The file was annotated by hand
  rather than rewritten, because a log that silently corrects itself
  is worth less than one that says where it was unreliable.
  **The same fault twice in five days, and the second time it was a
  RELAUNCH.** 2026-08-14: a sharded suite was started, appeared to
  die, and was started again over the same `shardN.log` paths -- but
  one shard of the first run had outlived the kill, so two runs of
  the same shard, on two different commits, appended to one file. The
  counts stopped making sense before anybody wondered why. Two rules
  follow, both cheap. Key a run's logs to the RUN (a timestamp, the
  commit, anything unique), never to the shard number alone, so a
  second launch cannot land in the first one's file. And verify the
  kill rather than assuming it: `pgrep` for the work itself, not for
  the wrapper that started it, because a launcher can exit while what
  it launched carries on -- which this project already learned once
  from a stochastic hunt that relaunched itself with nohup.
  **And a watcher outlives the thing it watched.** 2026-08-14, the
  twelfth: a CI poller armed for `pre-0.24.1rc1` was still running two
  releases later and announced `CI GREEN <sha>` while the work was on
  `pre-0.24.3rc1`. Nothing about the message said which branch, so the
  obvious reading -- that the current branch had gone green on a
  machine nobody had pushed to -- was wrong and comfortable. The rule
  already exists ("stop the watcher when the work finishes"); what it
  needs is the other half, which is that every watcher NAMES ITS
  SUBJECT in each line it emits. A verdict without its branch is a
  verdict about whatever the reader is thinking of.
- **A WHOLESALE SPAN REWRITE TAKES ITS NEIGHBOURS.** Deleting
  everything between two anchors removed TWO tests on 2026-08-16, not
  the one intended, because another sat between them -- and one
  registration then named a function that no longer existed, which
  would have broken the suite at `main()`. It was caught by running
  the tests, not by the edit. After any span deletion, count the
  definitions and check BOTH directions of the registration list;
  `test_the_report_generators_survive_hostile_docstrings` asserts both
  and is the cheapest thing to run.
- **AND THE OPPOSITE EDIT IS QUIETER: A SECOND DEFINITION REPLACES THE
  FIRST AND NOTHING GOES MISSING.** Also 2026-08-16, hours later.
  Widening `_label_for` for the three kinds of absence was done by
  writing a NEW method below the old one instead of changing it.
  Python binds a name once per statement, so the last wins: the dead
  one sat above the live one, in its own place, with its own docstring
  describing behaviour the software no longer had. The survivor's
  fallback was the fixed word "no data" -- and the categorical branch
  calls it for EVERY row, so the window whose whole job is to say
  which value draws in which colour labelled forest, water and urban
  alike. A deletion leaves a hole somebody trips over; an addition
  leaves two plausible functions and no symptom at the site.
  `test_nothing_defines_the_same_name_twice` now checks the whole tree
  at module and class level, exempting the decorated idioms where
  redefining a name is Python's own (a property's setter, a
  `singledispatch` registration, `typing.overload`). WHEN A HELPER
  MUST ANSWER DIFFERENTLY FOR TWO CALLERS, that is the signal to look
  at the callers, not to write a second helper: the parentheses that
  mark the categorical catch-all now live at that call site, and the
  one method answers plainly.
- **A SIGNAL CONNECTED TO THE PROJECT OUTLIVES THE WINDOW THAT MADE
  IT, AND SO DOES A COMBO.** 0.24.3 added two hooks onto
  `QgsProject.instance()` -- `_settle_layer_choice` and the pair around
  `layersRemoved` -- and neither carried the retirement gate
  `_on_project_read` already had. A dialog the user has finished with
  stays connected until its C++ object is destroyed, which in a
  session that opens the plugin several times may be much later or
  never, so EVERY project change reached EVERY dialog ever opened and
  each rebuilt a full weave unit for a window nobody was looking at.
  Measured 2026-08-16: `_layers_removed` fired 231 times across 22
  dialogs, exactly sum(0..21) -- QUADRATIC in how often the plugin had
  been opened.
  THE FOURTH ROUTE WAS NOT A PROJECT SIGNAL AT ALL, and gating the
  first three left it open: `QgsMapLayerComboBox` re-emits
  layerChanged whenever the project's layers churn, and every retired
  dialog still owns a combo doing that. Only a guard test written
  afterwards found it, by counting rebuilds rather than trusting the
  three fixes. Unit rebuilds over one test: 461 at 0.24.2, 1,282 with
  the new hooks, 801 with the project gates, **173 once
  `_on_layer_changed` was gated too** -- below the baseline, because
  the gate also stops work 0.24.2 was doing for dead windows.
  So: when you connect a NEW signal to anything that outlives this
  dialog -- the project, the style library, a layer, or one of our own
  widgets that QGIS re-fires -- add `if _dialog_is_gone(self) or
  _live_dialog() is not self: return`, and grep for the other routes
  into the same handler before believing you have them all.
- **A GATE WHOSE EXIT NOBODY BRANCHES ON IS NOT A GATE EITHER, and
  the second visit pushed.** 2026-08-25: `check_standards; echo; 
  check_before_push; echo; git commit && git push` -- both gates
  printed their failures, both echoes exited 0, and the commit chained
  off the ECHO. A tree the push gate had just called CI-red reached
  the public branch one command after the words appeared on screen,
  which is the 2026-08-15 fault with the pipe replaced by a
  semicolon. The failure was an orphaned anchor, fixed forward in the
  next commit; the rule is the same one, stated wider: capture the
  gate's OWN exit and branch on it (`STD=$?; [ "$STD" -ne 0 ] &&
  stop`) in the same script that would commit -- reading the words is
  not a gate, and neither is printing the number.
- **A GATE PIPED INTO ANYTHING IS NOT A GATE.** `check_before_push |
  tail -2` returns TAIL's exit status, so a shell `&&` after it fires
  whatever the gate said. That is how a tree failing the standards
  check reached the branch on 2026-08-15, one command after the gate
  reported the failure on screen -- the words were right there and the
  exit code was gone. Run the gate on its own line and read its
  status, or use `set -o pipefail`; never let a pipe stand between a
  gate and the thing it gates. The same applies to `grep`-ing a test
  runner's output: the runner's verdict is lost the moment it is
  piped.

- **A WATCHER IS A PROGRAM, AND A PROGRAM CAN DIE.** The thirteenth
  fault here, 2026-08-15: a CI poller with associative arrays, a
  nested here-string loop and two embedded Python readers exited 1
  partway through a run, having reported two jobs of eleven. Its
  silence afterwards was indistinguishable from "nothing has changed
  yet", which is the same failure mode as every other entry in this
  list, reached by a new road -- the watcher's OWN complexity. It was
  survivable only because the harness reports a monitor's exit; a
  watcher launched any other way would simply have gone quiet.
  So: keep the script trivially simple, guard every external call so
  a transient failure cannot end the loop, and prefer re-deriving the
  whole state each pass over accumulating it in shell variables.
  When a watcher does die, ASK THE SOURCE DIRECTLY before saying
  anything about what it was watching -- the last line it printed is
  not the current state, and reporting it as though it were is how a
  green summary gets written over a red run.

- **A FALLBACK THAT APPENDS INSTEAD OF REPLACING, AND THE FIFTEENTH
  WATCHER FAULT.** 2026-08-20: a nagging watcher was written to exit
  when its work list emptied, and it read the count as `left=$(grep -c
  . "$LIST" || echo 0)`. `grep -c` PRINTS `0` and EXITS 1 when nothing
  matches, so the guard meant for an unreadable file fired on the
  ordinary empty one and the substitution captured `0\n0`. `[ "$left"
  -eq 0 ]` then errors on a two-line string rather than being false,
  the exit branch never ran, and the loop went on emitting `0 still
  owed ... keep working` -- a line contradicting itself, which is the
  worst kind, because it reads as a bug in the reader.
  THE SHAPE, past shell: a fallback written with `||` runs when the
  command FAILS, not when it produces nothing, and a command that
  prints a perfectly good answer while exiting non-zero defeats it by
  adding to the output rather than replacing it. Ask of any `|| echo
  <default>` whether the command it guards can both succeed at
  printing and fail at exiting. And measure the empty case: one line
  in a terminal showed `left=[0\n0]` where an hour of reading had
  shown nothing.
  The rule this joins is already written above -- keep a watcher
  trivially simple, and prefer re-deriving the whole state each pass.
  This one was fourteen lines long and still found a new road.
- **THIS MACHINE'S `/usr/bin/grep` IS ugrep, AND `-q` WITH `-v`
  ANSWERS WRONGLY.** Measured 2026-08-24: `printf 'alpha\nbeta\n' |
  grep -qv alpha` exits 1 though `-v` alone selects a line. A CI
  watcher built its exit on `grep -qv completed` and declared two
  workflows finished while five jobs ran. Count matches
  (`grep -v ... | wc -l`) instead of trusting quiet mode's exit here.
- **`nohup ... &` EXITS 0 AS THE LAUNCHER, and a report of that exit
  describes the wrong process.** A five-test run "completed, exit 0"
  with three verdicts printed: the notification was the launching
  shell's, while the QGIS runner had minutes left. Wait on the
  RUNNER'S pid (`until ! kill -0 $PID`), and read the summary line
  before believing a verdict count -- no "N passed, M failed" means
  nothing has finished, whatever exited.
- **AND THE MIRROR IMAGE: A LAUNCHER THAT FAILS MAY HAVE STARTED THE
  JOB FIRST.** (2026-08-27.) `LOG=... && nohup python3 release.py
  --rc > "$LOG" 2>&1 &` mis-scoped its variable and reported an
  error, so the launch was read as having not happened and the
  candidate was launched again. The `&` had already backgrounded a
  release. TWO of them then ran for a quarter of an hour on one tree,
  each running the three-shard suite into the other's contention,
  sharing `dist/`, `reports/` and the candidate numbering, with the
  second truncating the log the first was writing past -- so the
  shard counts read off that log and reported as progress described a
  race. The rule above says an exit status describes the launcher
  rather than the job; this is the same sentence read the other way,
  and it is the more expensive direction. BEFORE RELAUNCHING
  ANYTHING, ASK WHAT THE FAILED LAUNCHER STARTED: `pgrep -f` for the
  work itself, never for the wrapper.
  AND THE READING THAT WOULD HAVE CAUGHT IT WAS POINTED AT THE WRONG
  PROCESS. The beat reported the parent's cpu, which for a sharded
  run is near zero however healthy it is, so cpu-against-elapsed --
  the one measurement that tells blocked from busy -- said neither
  for sixteen minutes. It sums the children now. When a watcher
  reports cpu, ask which process the figure is about; a parent that
  only waits is not the job.
- **READ THE LINE THAT ASSIGNS A TOOL'S VERDICT BEFORE TRUSTING THE
  WORD.** (2026-08-27.) The catalogue sweep prints `caught` or
  `ATTENTION`, and its own source is `verdict = "caught" if
  proc.returncode == 0 else "ATTENTION"` -- so ATTENTION mostly means
  a SURVIVOR, the word SURVIVED never appears in a sweep log at all,
  and `grep -c SURVIVED` answers zero however bad the news is. Read as
  "too slow to settle", 43 flags looked like contention across four
  shards; re-run one at a time on an idle machine they came back 0
  caught, 34 survived, 9 unjudgeable. A count of a word the tool never
  prints is a reassuring zero, which is the absence-of-evidence fault
  wearing a verdict's clothes.
- **AND A SUMMARY THAT NAMES WHAT IT SUMMARISES IS CAUGHT BY ANY
  FILTER LOOKING FOR IT.** The same sweep ends with `NEEDS ATTENTION
  (re-run each alone): <every flagged name>`, so a `grep ATTENTION`
  over the log picks up the summary beside the verdicts -- and `sed`
  leaves a non-matching line untouched, so a whole sentence arrived as
  one "name" and the loop word-split it into fifty. It also put a
  count at "560 of 559". When you filter a log for a marker, exclude
  the line that REPORTS on the marker, and check any total against the
  count the run declared for itself.
- **`gh run list --commit` MATCHES THE FULL FORTY-CHARACTER SHA, AND A
  SHORT ONE RETURNS NOTHING AT ALL.** (Same day, and it is the
  sixteenth watcher fault here.) A watcher keyed to `eb1ed8b` waited
  two hours and then reported that no run had ever been created; a
  second, written after reading that, reported the same within two
  minutes. Both were wrong. Asked with the full sha, `eb1ed8b` has
  `tests` and `mutation`, both green, and the live commit had two runs
  in flight the whole time. An empty list from a filter that cannot
  match is indistinguishable from an empty list because nothing
  exists, and the first diagnosis written from it -- that GitHub
  creates runs for pushes rather than commits, so an intermediate
  commit gets none -- was invented to explain an artefact and is
  simply false. `git rev-parse` the short sha before asking, or filter
  by `--branch` and compare `headSha` yourself.
- **A `PASS` LINE IS LOST TO A PIPE, SO SILENCE PLUS EXIT 0 IS NOT A
  PASS.** `tests/run_tests.py` ends through `os._exit`, so when stdout
  is not a terminal the buffered `PASS <name>` is discarded and
  `tools/run_some.py` exits 0 having said nothing, while a FAILURE's
  traceback reaches unbuffered stderr and survives. Read literally
  that is a run reporting nothing, and it looks exactly like success.
  `PYTHONUNBUFFERED=1` is what makes the verdict reach the pipe. Same
  `os._exit` that stopped `tools/coverage_report.py` writing a report
  at all until 2026-08-13.
- **AND THE TWO INTERPRETERS ARE NOT INTERCHANGEABLE.** Tests run
  under `$QGIS_PY`; edits and `tools/mutation_check.py` run under
  `env -u PYTHONHOME -u PYTHONPATH python3`. Swapping them fails in
  two directions that both read as a broken test: `env -u ... python3`
  hands you the SYSTEM interpreter, which dies at `import qgis`, and a
  bare `python3` under a sourced QGIS environment dies at `Failed to
  import encodings` having applied no edit at all. Both were done in
  one proof script on 2026-08-27, which is why they are written
  together.
- **`exists` THEN `remove` IS A RACE, AND EVERYTHING HERE SHARDS.**
  (2026-08-28.) `tests/run_tests.py`'s `main()` cleared its scenario
  record by asking whether the file was there and then removing it.
  Three coverage recorders start within a second of each other; all
  three saw it, two removed it, and the third died with
  FileNotFoundError BEFORE RUNNING A SINGLE TEST. Nothing announced
  that: the survivors ran on, the progress count rose, and the record
  would have been missing a third of the suite -- which overstates
  survivors, because a test missing from the record is never offered
  the chance to notice a mutant. Asking the question cannot fix it;
  only not caring can (`contextlib.suppress(FileNotFoundError)`).
  IT WAS FOUND BY AN ASYMMETRY: one shard had recorded nothing while
  its siblings were at nineteen and thirty. So when work is sharded,
  read the shards SEPARATELY -- a total climbing healthily is the sum
  of two shards doing fine and one that died at startup.
  AND GUARD THE SHAPE RATHER THAN THE SITE. The family test scans
  `tests/` and `tools/` for the pattern, reading each file WHOLE
  because it spans two lines and no per-line grep can see it, and it
  immediately found a second instance in
  `tools/make_test_fixtures.py` -- a site likelier to be run once, and
  therefore exactly the one a repair at the reported site leaves
  standing.
- **A WATCHER THAT SUBSTITUTES "NOTHING" FOR A FAILED CALL REPORTS
  ITSELF TWICE.** (Same day, the seventeenth watcher fault.) A CI
  poller deduplicated by comparing this pass's verdicts against the
  last, and guarded `gh` with `|| echo "[]"` so a transient failure
  could not kill the loop. That guard empties the comparison set, so
  the next successful poll finds everything new and re-announces a
  verdict already reported. The rule this project already carries --
  report change, not state -- has a precondition nobody wrote down:
  the record of what you have already said must survive a failed
  reading. On an error, keep the previous state and skip the pass.
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

The environment that script needs is DISCOVERED, by
`tools/macos_qgis_env.sh`, which the macOS CI job also calls -- so the
runner and this machine cannot disagree about how to start QGIS's
Python. It finds the bundle, finds an interpreter that actually
STARTS (the cask's carries the paths of the machine it was built on
and dies without a PYTHONHOME), and picks `QGIS_PREFIX_PATH` by asking
QGIS, AGAINST A THROWAWAY PROFILE.
That last part is the whole trick and it is worth understanding
before touching the script. The prefix decides `pkgDataPath`, which is
where QGIS finds the style database every stock ramp lives in. This
project had it wrong for months -- `Contents/MacOS` yields a doubled
path that does not exist -- and QGIS started, imported, tiled and
rendered with NO RAMPS AT ALL. It never showed here because the
profile on this machine has carried 63 ramps since the plugin seeded
it. Asked with a seeded profile every candidate answers "ramps
present", so the measurement has to be made somewhere nobody has
been. The bundle itself is the prefix: 35 ramps on a fresh profile,
`/Applications/QGIS-final-4_0_3.app`, Python 3.12, offscreen works
headless.

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
  name means something there already, QGIS's meaning wins. The plugin
  installs only palettes QGIS LACKS -- 36 of them, tab10, the
  matplotlib-only families and the eight ColorBrewer QUALITATIVE sets
  -- tagged "mapweaver", additive only.
  Settled by `/grill-me` on 2026-08-15 after measuring that 35 of the
  palette file's 63 entries were also stock ColorBrewer names, so they
  had never installed on any fresh QGIS since 0.23.0: the plugin's
  maps were already drawn with QGIS's colours and the project had
  simply not noticed.
  **"LACKS" IS ANSWERED BY THE STYLE LIBRARY, NEVER BY WHAT QGIS CAN
  GENERATE**, and getting that wrong the same evening cost eight
  palettes. The 35 were identified as ColorBrewer SCHEME names, which
  QGIS can synthesize through `QgsColorBrewerColorRamp`; eight of them
  -- Accent, Dark2, Paired, Pastel1, Pastel2, Set1, Set2, Set3 -- are
  not entries in `QgsStyle.defaultStyle()` at all. A fresh QGIS 4.0.3
  holds 35 ramps and every one is sequential or diverging, so dropping
  those eight removed every qualitative palette from every fresh
  install, and `get_ramp("Set2")` returned None. Restored the same
  night after macOS and Windows CI failed on it identically. The
  question to ask of any deduplication against a dependency is what it
  HAS, not what it could make. The colourspace gate passed only because the
  development machine's style library had been seeded by the plugin
  years earlier -- a gate certifying fidelity against a profile no
  user has.
  PARITY WITH THE LIBRARY IS A DESCRIPTION, NOT A PROMISE. The plugin
  defers to QGIS for renderers, the styling dock, the project format
  and the ramp list; colour is the same kind of thing. A user wanting
  matplotlib's exact palettes installs them; the plugin does not ship
  them under alternative names. Profiles already seeded keep what they
  have -- additive only has never meant destructive -- so a machine
  that installed an early version draws those 35 differently from a
  fresh one until its owner clears them.
  The comparison in `tools/visual_reference_report.py` is therefore
  handed THE COLOURS IN FORCE, exported beside the gallery by
  `tests/visual_tests.py`, and no longer asserts whose palette they
  are. It still tests where the breaks fall, how categories are
  sampled, the reduction, insetting, weaving and geometry -- and it
  cannot again pass because of one profile. What it gave up is covered
  by `test_the_ramp_a_row_names_is_the_ramp_the_map_draws`.
  **ITS REMAINING REDS ARE THE SAME FACT AGAIN, and they are not a
  Linux problem.** Measured the same night by holding everything
  constant but the profile: this Mac scores the "web-app parity" cases
  at dE mean 2.6-3.1 on its own seeded library, and at 3.7-4.1 with
  p90 6.7-7.1 on a THROWAWAY profile -- the Linux figures to the
  decimal. A fresh QGIS resolves Reds and YlGn to ColorBrewer-anchored
  gradients of nine stops, or five, where the seeded library holds the
  plugin's sixteen-stop versions, so the two differ EVERYWHERE rather
  than at edges. The earlier explanation, a platform offset blamed on
  antialiasing and missing fonts, was wrong.
  The 4.0 limit was therefore calibrated against renders from a
  profile no user has. Whether a parity comparison should still fail a
  build for that is the maintainer's decision and a real one:
  re-deriving a limit whose baseline was never representative is not
  the same act as loosening a threshold to get a green run, but it is
  near enough that nobody should make the change quietly. Reproduce in
  thirty seconds by rendering the gallery under
  `QGIS_CUSTOM_CONFIG_PATH=$(mktemp -d)` and scoring it.
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
- **AT MOST THREE SIGNIFICANT FIGURES IN ANY NUMBER BOX.**
  (Maintainer's rule, 2026-08-17, after a tester met spacing showing
  six decimal places of metres.) Figures rather than decimal places,
  deliberately: a figures rule bounds what a reader takes in whatever
  the magnitude, where a decimals rule lets 1234.567 through at four
  and clips 0.0008 to nothing.
  `dialog._limit_the_figures_on_show` sweeps every `QDoubleSpinBox`
  once at construction, so a control added next year obeys the rule
  without anybody remembering -- which the five-rules-in-five-places
  arrangement it replaced was not. THE STEP DECIDES AND THE CAP BOUNDS
  IT: a box shows the decimals its own `singleStep` needs, and never
  more than three figures. Counting from the VALUE instead gives every
  box sitting at zero three decimals, since zero has no digits to
  count, which is how the offset angle read "0.000" degrees on the
  first attempt.
  TWO GOOD REASONS TO DEPART, both real. Spacing spans 1e-6 to 1e12,
  so no construction-time setting suits a floor plan at half a metre
  and a country at fifty kilometres; it is exempt by identity (never
  by `objectName`, which is empty on every box here) and TRIMS ITS
  TEXT instead, in `SpacingSpinBox.textFromValue`, keeping six
  decimals of precision and printing none of the zeros it does not
  need.
  THE MECHANISM THAT PRECEDED IT ROUNDED A NUMBER A PERSON TYPED, and
  the mistake is the one to remember: it sized `decimals` from the
  spacing auto-fitting had computed, and a QDoubleSpinBox at zero
  decimals cannot REPRESENT 500.5. Typing 500.5 gave 501, typing
  215.509124 gave 216, and the map was tiled from the rounded number
  with nothing said. `decimals` governs display AND input AND
  storage, so ANY rule that lowers it to tidy a display destroys
  data; a display rule belongs in `textFromValue`, which touches
  neither the value nor the validator. Four tests said so and the
  branch carried it for a day because nothing ran them. And a box
  holding a number a PERSON TYPED, or one taken from the data, must
  not round it away: the class-bound boxes size their decimals from
  the data deliberately (catalogue entry
  `the-bound-box-is-sized-from-the-data`), since clipping a pinned
  -0.9276 to -0.928 would change the value the map is drawn from.
  Any such box declares its exemption at the site, with the reason
  there, and is still as tight as it honestly can be.
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
  `/grill-me` on 2026-08-08; the decisions are the user's and should
  not be quietly revisited. Values come from the REGION layer, so the
  button works before anything is generated — accepting that at a
  coarse spacing it can list a value no tile carries. Colours are
  keyed `{tile_id: {field: {value: colour}}}`, so switching an
  element's variable away and back restores the work and two fields
  sharing a value name cannot bleed into each other. Choosing a ramp
  or importing a QML CLEARS that element's hand-picks for the current
  field, so the ramp control means what it says; the loss is reported,
  never silent. Overrides outrank both template and ramp in
  `make_categorized_renderer`, and the catch-all is editable under
  `bridge.NO_DATA_KEY`. The window is modal to the plugin dialog only,
  leaving the QGIS canvas live so the recolour can be watched. The
  editor NEVER holds a layer: it writes to the dialog's record and
  lets the restyle path find whatever layers exist, which is what
  makes it safe to use while a run is in flight. Two consequences that
  cost a bug each: the picks must be in `_signature` or the fast path
  skips the element as unchanged, and `_add_output_layers` must
  RE-READ them rather than trust the snapshot the run was launched
  with, or a colour chosen during a run is destroyed when it lands.
  They persist as a layer custom property so a saved project survives
  a QGIS restart. **Both consequences apply to the GRADUATED editor
  too, and saying "category colours" here is how that went unnoticed
  for five days.** The quant editor writes positional class colours
  and the ramp's display window through the same window, and
  `_add_output_layers` re-read only the categorical half until
  2026-08-13: a class colour picked during a run was destroyed when
  the run landed AND stamped absent onto `weavingspace_quant_style`,
  so reopening the project could not bring it back either. The rule
  is about HAND-PICKED COLOUR on either styling path, not about the
  categorical editor. When a rule here names one of a pair, check the
  other before believing it is a rule about one thing.
  **It happened a THIRD time on 2026-08-14**, and the third is the one
  that should settle the phrasing. Pinned bounds and copied ladders
  are written through that same window while a run can be in flight,
  and the landing re-read colours and the display window and not them
  -- so a pin made during a run was destroyed as the run landed and
  stamped absent onto the layer. The rule is not about colour and not
  about the editor: EVERYTHING the colour editor writes must be
  re-read at the landing, and anything added to that window later
  joins the list. It was found by the maintainer asking whether the
  new features had been tested for races, which is worth more than
  the fix.
- **A CATEGORICAL SCHEME COPIES LIKE A GRADUATED ONE, AND IT
  OVERWRITES.** (Maintainer's rulings, 2026-08-20, after a tester
  reported the control simply missing: it was kept off the categorical
  half by two gates, the editor building its Copy row only where
  GRADUATED bounds exist and the categorized call site passing neither
  the targets nor the callback.) The copy takes the style, the ramp,
  the Reverse, the per-value colours, the catch-all and the class
  source, which travels as a FILE REFERENCE so the two elements go on
  agreeing -- accepting that a moved file then costs two elements
  rather than one.
  FOUR THINGS NEVER TRAVEL, and the first is the only one that would
  cost a map. THE VARIABLE: carrying it makes the target a duplicate
  of the source, and a map whose whole purpose is reading several
  variables against each other quietly loses one. THE OPACITY, as
  through every other change of scheme. THE OUTLINE, which decides
  whether tile EDGES are drawn and is not a colour. And THE RECORDS OF
  THE STYLE THE ROW IS NOT WEARING -- pinned bounds, breaks, floor,
  ceiling, the remembered class count, the single colour -- kept, and
  kept SILENTLY, so a row switched back to a quantitative style finds
  its work where it left it.
  VALUES THE RECEIVING COLUMN DOES NOT HOLD ARE KEPT rather than
  dropped, on the graduated precedent that a copy reproduces a
  classification and a silently shortened one does not. THE CASE IT IS
  REALLY FOR is a column typed numeric that is genuinely categorical
  -- land-cover codes and the like -- where the colours land because
  `_category_colours` keys on the value as TEXT.
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
  Changing the region layer KEEPS an element's setup where the new
  data has a column of that name and DROPS it where it does not, the
  element then auto-assigning as the recovery rule of 2026-08-15
  already says for a layer whose file has moved. The records
  themselves are left alone, which is free rather than sloppy: they
  are keyed by tile id AND FIELD, so a setup for an absent column sits
  idle and returns if the user switches back. The ruling governs what
  stays ACTIVE, not what is remembered.
  RECORDED HERE AS MEASURED SOUND, AND MEASURED BROKEN HOURS LATER, at
  every door. The two tests written that afternoon passed and both were
  VACUOUS: their fixture assigned a variable and never touched the
  STYLE chooser, so `_refresh_table` re-derived a quantitative style
  from the new column's type on every switch and nothing was ever
  RETAINED to be wrongly retained. Driven the way a user drives it --
  the style picked through the combo, which is what marks it as
  theirs -- a categorical scheme cut for four land-cover words came to
  rest on a column of areas in square metres and drew a colour for
  each. That is the colleague's report, live while three documents said
  the ground had been measured.
  THERE ARE THREE DOORS, not two, and the third is the one that speaks:
  a column DELETED in QGIS re-points its elements at a surviving column
  and TELLS the user so, which is right, while the scheme rode along
  outside that account. `_adapt_to_the_layer` re-defaults the row
  before the table is rebuilt, so the guard in `_refresh_table` cannot
  see it -- one ruling, three doors, and the third needs its own
  answer. All three are closed and each carries a registered test.
  WHAT THE EARLIER READING GOT RIGHT is the shape of its own
  correction: a fixture that leaves the plugin to DERIVE the thing
  under test measures the derivation. Written up in docs/TESTING.md
  beside the conditional-assertion fault it arrived with.
- **A CHANGE OF REGION DATASET: THE SEVEN RULINGS OF 2026-08-21.**
  (Settled by a full grilling, on the maintainer's report that the
  current model surprised its own designer during a demo of several
  datasets in a row, plus a colleague's report of a saved file
  silently overwritten. The proposal grilled was "reset everything,
  carry symbology for variables in common"; made precise, most of it
  converged on machinery already built the day before, and these
  seven are what remained to decide.)
  1. THE OUTPUT PATH CLEARS on any change of region layer --
     same-schema included, because B's map written over A's file
     destroys a result either way -- and the clearing is announced.
     Re-generating the SAME dataset still overwrites in place, which
     is the settled replace-in-place contract, untouched.
  2. THE NEXT GENERATE AFTER A SWITCH BUILDS A FRESH GROUP, through
     the same door a person uses to ask for one (the checkbox then,
     the chooser's "Create new" since 2026-08-30). The previous
     dataset's result stays in the project; a demo accumulates its
     maps side by side. A-B-A makes a third group.
  3. A DROPPED COLUMN TAKES ITS WHOLE SCHEME: mode, ramp, Reverse,
     class count and class source all re-derive -- exactly the set a
     COPY overwrites, so switching and copying agree about what a
     scheme is. One partition, used twice.
  4. OPACITY STAYS WITH THE ELEMENT, as through every other change of
     scheme; the single colour becomes a record of an unworn style,
     kept silently under the existing ruling.
  5. THE DESIGN NEVER RESETS, WITH ONE DOOR: when the new dataset
     SEEMINGLY cannot fill it -- fewer seemingly-usable columns
     (non-identifier, text included) than elements -- the plugin ASKS,
     naming both numbers and what Yes does ("Change to a design with 2
     elements?"). Yes recomposes to that element count with its
     default family, one column each; No keeps the design with
     columns shared, as today. Modifiers survive either way. The
     maintainer's wording rulings: the question says CONCRETELY what
     it will do, and the column count is hedged ("seemingly"), because
     the usable-column heuristic is a guess.
  6. THE MEMORY IS KEPT AND WIDENED: everything the switch deactivates
     is recorded by element AND field -- the hand-picks and pins
     always were; the scheme limbs join them -- and switching back
     restores it. What stays ACTIVE changes; what is REMEMBERED does
     not. The scheme memory is session-scoped, unlike the stamped
     colour records, which is an implementation choice to revisit if
     a reopened project turns out to need it.
  7. THE SAME-NAME CARVE-OUT STANDS AS BUILT: setups follow surviving
     column names, and the hundred-values question guards a column
     that keeps its name while changing its kind.
  SEQUENCING: all of it into 0.24.3, as rc17, on the maintainer's
  explicit choice over splitting or deferring -- accepting that scope
  grows on a version whose candidate is out for feedback.
  A MODAL JOINS THE LAYER-CHANGE PATH with ruling 5, where the
  threshold question set the precedent; the no-modal rule guards
  GENERATION paths and is untouched.
  8. NO RESIDUE OF ONE DATASET -- COLUMN NAMES INCLUDED -- MAY STEER
     OR REACH ANOTHER. (Maintainer's ruling, 2026-08-24, widening a
     question first asked about the shelf: "make sure there is no
     leakage between datasets/gpkg -- leakage of column names, for
     example".) The session's field-keyed memory -- hand-picked
     colours, pinned bounds, the scheme shelf -- lives in PER-DATASET
     BANKS keyed by layer id, swapped on any change of layer by
     `_swap_dataset_memory`; the three attributes are views into the
     current bank. A dropped scheme files under the dataset it was
     made ON (the rebuild runs after the swap, hence the pending
     pointer). A CARVE FOR "VARIABLES IN COMMON" WAS BUILT
     AND ENDED THE SAME DAY by the maintainer's own question: a
     categorical scheme's hand-picks are keyed by VALUE STRINGS and a
     pin holds data-derived NUMBERS, so carrying them to a same-named
     column would put one dataset's confidential values into another's
     .qgz and GeoPackage through the landing stamp. Nothing tells
     "same wards, next year" from "unrelated data with a coincident
     name", so silence sides with the confidential case: the STYLE
     keeps by name (mode, ramp, Reverse, class count -- choices, not
     data) and VALUE-LADEN RECORDS NEVER CROSS; sharing a ladder
     across files is an explicit act. Files were measured clean
     (stamps carry only the displayed field) and are guarded AT THE
     FILE: a test builds a second dataset SHARING the confidential
     column's name and reads the GeoPackage's bytes, requiring none of
     the first dataset's value strings or other column names. Consequences accepted and
     documented: a re-added layer is a new identity and forfeits
     session memory, and KEEP-BY-NAME OUTRANKS THE BANK -- an element
     that comes home carrying a surviving column name keeps it rather
     than consulting the shelf, which is the composition of rulings 6
     and 7 rather than a new one.
  A LANDING NEVER WRITES OVER A MAP MADE FROM ANOTHER DATASET, and
  that is ruling 2 finishing the job it started. Making a second
  output group the ordinary result of a demo left ADOPTION's older
  assumption wrong -- it takes the newest group and runs at
  construction, before the user has chosen anything -- so reopening a
  project holding two datasets' maps and generating on the first
  DELETED the second. Every output layer carries
  `weavingspace_region` now (the region's source, which survives a
  reopen where a layer id does not), and the landing refuses a group
  whose stamps name another dataset. Output made before the stamp
  carries none and keeps the older rules. When a ruling starts
  producing a SECOND artefact by default, re-drive every path that
  assumed one.
  AND THE CHOOSER IS NOT THE ONLY DOOR. Two hunts of 2026-08-25
  found the same defect from different directions: REMOVING the region
  layer and picking another skipped every protection, so Generate
  overwrote the previous dataset's GeoPackage unasked. `switched`
  asked about the WATCHED LAYER OBJECT, which a removal nulls; and
  the layer COUNT decided which of two routes ran, so the same act
  answered differently in a project with two polygon layers and one
  with three. It asks about the DATASET IN FORCE now
  (`_memory_layer_id`), and the bank swap RETURNS on an empty chooser
  rather than banking and forgetting -- the second fault, which hid
  the first. When a rule is about "the thing in force", ask what NULLS
  the record you are reading, and whether the answer is a user's act
  or somebody else's cleanup.
  WHAT COUNTS AS "A CHANGE OF DATASET" WAS DRAWN BY THE FULL SUITE on
  the rulings' first whole run, which failed three tests the targeted
  runs had all passed: leaving a dataset THIS SESSION HAS BUILT FROM.
  One clause, and it covers all three failures. A recovery is not a
  switch -- reopening a project whose region file moved and pointing
  at live data re-finds the same work -- because a reopened session
  has not landed anything yet. A combo AUTO-LANDING in a busy project
  is not a dataset the user chose, for the same reason. And a
  pre-generate fiddle is a first choice: nothing is built, so there
  is nothing to protect. A SECOND CLAUSE WAS TRIED AND DELETED:
  liveness of the outgoing layer, whose catalogue entry could only
  survive, since every measured journey is decided by the landing
  alone -- and in the one it would change, land a run then lose the
  source then pick new data, protecting the landed result is what the
  rulings ask anyway. `switched_from_work` in `_on_layer_changed` is
  the one place the boundary lives; the retained-scheme question
  deliberately stays on the plain switch, because it is about what
  the TABLE carries rather than about protecting output.

- **THE OUTPUT GROUP IS THE UNIT OF WORK: THE RULINGS OF 2026-08-25.**
  (Settled by a full grilling, on a colleague's report from a real
  demo of several datasets in a row, and on a probe that measured
  every claim in it. It COMPLETES the rulings above rather than
  reversing them, and it retires some of their machinery.)
  WHAT THE REPORT FOUND, and the probe confirmed on this branch: the
  design travels a change of dataset intact, the value-laden records
  are banked per dataset, and the output group is remembered nowhere
  -- three scopes answering ONE act in three ways, none of them named
  anywhere on screen. A-B-A leaves THREE groups, the first and third
  stamped for the same dataset, so one dataset already owns two maps
  with nothing to tell them apart. Returning to a dataset gives its
  colours and pins back and somebody else's design. The colleague's
  diagnosis is the sentence to keep: inferring all of this "is OK as
  far as it goes, but it's too hard to be reliable and not produce
  weird seeming behaviour relatively often".
  1. THE DIALOG CARRIES A DROPDOWN OF OUTPUT GROUPS, on the first tab
     beside the region chooser, with a "create new" entry. It is not a
     memory feature: the group is a QGIS-side artefact that already
     exists, already carries an identity in `weavingspace_region`, and
     was already being chosen on every run by a rule the user could
     neither see nor override.
  2. DATASET AND GROUP ARE BOUND SYMMETRICALLY -- choosing either
     selects the other. Built with signals blocked, as
     `_sync_pin_controls` already does, or setting a control right
     fires the handler that set it right.
  3. WHERE A DATASET OWNS SEVERAL GROUPS, choosing it selects the most
     RECENT, read off the project's own layer order rather than
     remembered. A fact about the project beats a guess about intent,
     and it survives a reopen where a session record would not.
  4. THE WHOLE WORKING STATE BELONGS TO THE GROUP: family, kind,
     element count, spacing, modifiers, icon mode, and every element's
     variable, style, ramp, Reverse, class count, class source,
     colours, pins and opacity. Selecting a group RESTORES all of it,
     so nothing is inferred -- the direct answer to the diagnosis
     above. Stored in the group's own custom properties, so it
     persists with the project for free.
     THE RESTORE WHITELIST IS THE RECORD'S REAL DEFINITION, exactly as
     it is for `_adopt_dock_bounds`: a key missing from it is dropped
     in SILENCE on every reopen, so the record is right all session
     and wrong the moment the project comes back. Widen that list in
     the same commit as the record, always.
  5. THE GEOPACKAGE IS RESUMABLE, and the source comes back BY
     REFERENCE -- the path is already recorded on every output layer
     -- with EMBEDDING THE SOURCE as an explicit opt-in, for a file
     somebody else is meant to carry on with. That keeps the ordinary
     file small and private and makes portability a choice the user
     makes, which is the same shape as the dependency consent and as
     ruling 8's "sharing a ladder across files is an explicit act".
  6. ELEMENT TABLES ARE TRIMMED to the symbolised variable plus the
     identifiers, and named `tiles_<tid>_<variable>`. Adoption goes on
     reading the old `tiles_<tid>`, because files and projects already
     exist that use it. Names are sanitised and collisions handled: a
     GeoPackage folds case, so `tiles_a` and `tiles_A` become one
     table with both writes reporting success (measured 2026-08-14).
     TRIMMING IS ONLY SAFE BECAUSE OF 5. The colleague's argument for
     carrying every column was that a tiling may be missing data in
     some variables, so the full set hedges a lossy encoding. With the
     source recoverable, switching a variable RE-TILES from the source
     rather than reading a column carried along just in case.
  WHAT THIS RETIRES. `_fresh_group_for_new_data` goes: the protection
  it gave comes from WHICH GROUP IS SELECTED now, not from arming a
  flag. Much of the per-dataset bank's job goes with it, though not
  all -- styling done before anything is generated has no group to
  belong to yet. A group belongs to exactly one dataset, so per-group
  is a NARROWER scope than ruling 8's per-dataset banks, and nothing
  here weakens that ruling.
  WHY IT DOES NOT REVERSE RULING 2. That ruling arms a fresh group on
  a switch so the map of the dataset you LEFT survives. Under the
  binding, A-generate-B-generate-back-to-A lands on A's own group and
  replaces that map in place while B's is untouched -- which is what
  the colleague asked for, and what ruling 2 was reaching for through
  a proxy.
  WHAT WAS REJECTED, recorded so nobody re-litigates it silently. The
  colleague offered a genuine alternative -- REWIND TO ONE SHOT: work
  on the current dataset, save it as now so it can be reloaded but not
  resumed, and forget everything on an unsaved switch. It had the
  strongest single argument in the room, that nine of the eleven
  defects of 2026-08-25 were in exactly the machinery it deletes. It
  was not taken because it costs the one behaviour the colleague
  himself singled out as working (symbology coming back on a return)
  and makes the several-datasets demo worse rather than better, which
  is the session the whole report came from. THE MIDDLE OPTION was
  also refused: keep inferring and mend the asymmetries by putting the
  design in the per-dataset bank. It is much the cheapest, and it
  fails on its own terms -- A-B-A would then move the design under the
  user TWICE, where a design you SELECT never moves on its own.
  AND THE PRINCIPLE THAT DECIDED IT is the one above, in "How we
  decide things": persistence is a duty at the QGIS boundary and a
  design question at the dialog's own controls. Every argument of the
  form "but we would be destroying their work" was struck out of the
  user-plugin half of this decision, because nothing of theirs is
  destroyed there.

- **TWO RULINGS OF 2026-08-26, SETTLED BY GRILLING, on the leads two
  hunt rounds corroborated.**
  THE FILE SHOWS THE LIMIT OF WHAT IT CONTAINS. People redistribute
  their work, and what they see in the GeoPackage must be the limit of
  what is in it -- so work for fields the map does not display never
  reaches the file. The PROJECT is the user's own and carries the
  whole working memory home: each group-record element gains a `kept`
  map (the other fields' pins and hand-picks, per field, this
  dataset's fields only, so ruling 8 stands), which rides the .qgz
  through the layer-tree node and never the GeoPackage. The seam that
  makes the split possible: layer custom properties EMBED into the
  file's saved styles, so the stamps stay one-field; the group record
  does not embed, so it may widen; and the file's own record is
  stripped through `_file_safe_state` at every write, guarded at the
  helper so a new call site cannot forget. Consequence accepted and
  documented: resuming from the GeoPackage without the project
  restores the displayed design and never the unworn-field memory --
  under the principle, correct rather than a loss. Saving alone wipes
  no session memory, which was already true and is now stated.
  AND THE SWITCH DOOR SPEAKS. A change of region dataset that
  re-points elements whose chosen column the new data lacks announces
  it in the deleted-column door's own sentence family, naming the NEW
  layer -- at a switch it is the layer that moved, not the column. An
  ordinary switch where every column survives by name stays quiet;
  recovery and group selection stay silent, since a recovery is not a
  switch. Ends the asymmetry where two doors into one loss differed
  only in which of them said so.

- **TWO MORE RULINGS OF 2026-08-26, from the bulletproofing round.**
  Both settle a case where two settled rules gave one act two answers.
  THE RETURN LEG RESTORES THE CHOSEN VARIABLE. A-B-A without a
  Generate used to keep the re-pointed column wherever the datasets
  shared a name -- keep-by-name, the composition of rulings 6 and 7 --
  while the same journey WITH a landed group gave the person's choice
  back through the group record. Two rules, two answers, decided by
  whether a run happened to land. The shelf's remembered field wins
  the return now: the shelf entry IS the earlier choice, it is popped
  on restore, and a row whose current column was itself chosen has no
  shelf entry for another field to beat.
  THE STYLE FOLLOWS THE FIELD, NOT THE ELEMENT. A touched mode rode
  the element across a variable change, so a row returning from
  Categorized landcover to v1 arrived wearing Categorized -- and the
  re-click the user was then forced into is a genuine reclassify,
  which retires the positional picks the kept-silently ruling of
  2026-08-20 preserves. The mode banks per element AND field
  (`_mode_by_field`), exactly as ruling 6 keys the scheme limbs, so a
  field's return wears its own style and no forced re-click happens.
  A person's own mode click still retires picks, as 2026-08-09 says.
  MEASURED PARITY FIRST, which is why this is a ruling rather than a
  defect report: the in-session return destroyed the picks exactly as
  the reopened one did, so it was two rules colliding rather than a
  persistence fault.

- **THE FIVE RULINGS OF 2026-08-27, SETTLED BY GRILLING. ALL FIVE ARE
  BUILT, AND ON ONE LINE.** They are recorded here because the
  reasoning is what a later session will not have.
  WHAT EACH CARRIES, because a ruling written down reads exactly like
  a ruling implemented. Rulings 3, 4 and 5 -- the output path, the
  ramp memory and the seeding order -- each have a registered test and
  catalogue entries proved `caught`, with ONE exception measured to a
  close at the entry itself: the restyle half of ruling 5 is HELD
  REDUNDANTLY rather than unproved, by a class source stamped on the
  donor's content and by the reseeded term behind it. Rulings 1 and
  2 -- saving as a positive act, and the untick that drops the
  source -- carry twenty proved entries between them and a matrix of
  eleven routes to a press.
  WHAT THE CONVERSION COST AND FOUND, kept because it is the argument
  for doing it that way again. Fifty-eight Save presses went in by
  script where the old code's write used to happen; twenty-four tests
  were converted BY HAND because what they assert changed rather than
  moved; four tests were written that did not exist. It found FOUR
  REAL DEFECTS, three on ordinary journeys -- a run claiming a save it
  never made, a Save during the first run telling somebody to press
  Generate, a region chooser excluding a newly loaded layer for being
  allocated where a destroyed one had been, and a map opened with Load
  being DESTROYED by being saved. Ledger rows 27 to 30.
  TWO DECISIONS WERE TAKEN WHILE BUILDING IT, both small, both the
  kind that should be visible rather than discovered later.
  A SAVE PRESSED WHILE A RUN IS IN FLIGHT IS REFUSED IN WORDS. What
  is on screen mid-run is the PREVIOUS map, so writing it answers a
  different question from the one the press asked -- silently, over
  the file the person has just named. The run lands in seconds and
  the press costs nothing to repeat. It is the same door the group
  chooser and the resume already guard with `self._task is not None`,
  which is this file's own rule that a guard added to one door
  belongs at every door into the same room.
  AND `_may_overwrite` ASKS ABOUT THE DATASET, NOT THE GROUP, which
  leaves one case silent: a SECOND map of the SAME dataset, saved
  onto the first map's file, replaces it without a question. Three
  things decide that -- the file's record carries `region` and
  `output_path` and no group identity at all, so the question is not
  available to ask; the ruling's own boundary is "a file the plugin
  did not write", and that is a file the plugin wrote from that data;
  and the chooser is a save-mode dialogue, so the platform has
  already asked about replacing an existing file. The method's own
  docstring claimed the group until this was noticed, which is this
  file's "a gate that checks half of what it names" met again, from
  the documentation side. If the group should be the unit, the record
  needs a group identity first.
  1. SAVING IS A POSITIVE ACT. A path chooser records what you WOULD
     save to or load from and does nothing on its own. A SAVE button
     beside the output path writes the map as it stands -- tables,
     styles, the resumable record, the stale-table drop and the
     embedded source together -- and a LOAD button beside the other
     chooser reads one back. Generate DRAWS. Auto-generate never
     writes. SAVE ASKS BEFORE OVERWRITING a file the plugin did not
     write: with Save a deliberate press, asking every time is noise,
     and a file somebody else's map is in is not.
     WHAT IT RETIRES. Live update's output-path gate is DELETED rather
     than explained: its reason was that a live run must not rewrite
     somebody's file on every keystroke, and under this ruling no run
     writes at all, so a gate that cannot fire would sit in the source
     reading as protection. It also overrules the Save & open tab
     already written on the `../ws-save-load` worktree, which resumes
     the instant a file is chosen.
     THE QUESTION IT ANSWERED WAS A DIFFERENT ONE. The maintainer was
     asked how live update should ANNOUNCE its silent pause, and
     answered by moving the ground under the question. Recorded that
     way round because it is what a grilling is for, and because the
     three options offered were all worse than the answer.
  2. UNTICKING "INCLUDE THE SOURCE DATA" MEANS IT IS NOT IN THIS FILE.
     The `weavingspace_region` table is dropped at Save -- only that
     table, the one the plugin wrote itself, never anything else a
     user keeps in the file. It follows the ruling of 2026-08-26 that
     the file shows the limit of what it contains: a private copy
     somebody has switched off is exactly what they would be surprised
     to find in a file they send on. Today the copy stays while the
     record says it is gone, so the privacy AND the resume are both
     lost; measured on the file's own bytes.
  3. AN OUTPUT PATH NEVER DECIDES WHICH GROUP A RUN LANDS ON. The
     chooser alone does, which is what the ruling of 2026-08-25 gave
     it, and "create new" remains the way to ask for a second map.
     Clearing the path currently forks a group silently -- and
     unattended under live update, from an ordinary design tweak.
     Under ruling 1 the fork's own justification disappears, since a
     run no longer writes anything to overwrite.
  4. A RAMP IS REMEMBERED UNDER THE MODE THE ROW IS IN, not under the
     family the RAMP belongs to. A row remembers what it WORE in each
     mode: pick `Accent` while Graduated, pick `Reds` back, and the
     categorical slot is untouched. The comment at that site argues
     for the present rule and is to be REWRITTEN rather than edited --
     its worry, that a categorized row carrying `YlOrRd` would hand
     that back on the next flip, is answered by the row having worn
     it. Decided on the dialog-controls side of the two-relationships
     framing: what makes the next thirty seconds clear, not what loses
     nothing.
  5. DONORS ARE SEEDED BEFORE THEIR FOLLOWERS, reading the donor's NEW
     layer, so a change reaches its follower in the same run rather
     than one later. THE OBVIOUS ANSWER IS RULED OUT BY DEFERRAL: the
     template cannot be computed from the donor's ROW, because a donor
     may be deferring and its renderer made by hand in the dock, which
     is exactly when following it is most useful -- so the donor's new
     layer must exist first. SEEDING ORDER IS SEPARATED FROM PANEL
     ORDER, which reads `a..z` then `aa..`. Two elements taking from
     each other have no valid order and keep the one-run lag, with the
     reason at the code; driven 2026-08-27, a cycle SETTLES rather
     than churning.

- **THE GROUP CHOOSER IS THE ONLY DOOR TO A NEW GROUP.** (Maintainer's
  decision, 2026-08-29; built 2026-08-30.) Two controls armed one
  fact: the chooser's "Create new" entry, which is ONE-SHOT, and a
  "Create as new group" checkbox on Map options, which was a STANDING
  preference read at every landing. Nothing on screen said which was
  which, and the READERS DISAGREED -- five sites asked only the
  checkbox, one only the flag, and exactly one asked both, that one
  only since ledger row 36 of 2026-08-28, where the chooser went on
  describing a landing that would not happen.
  THE REASONING IS ABOUT THE INTERFACE RATHER THAN THE MECHANISM, and
  that is why it settles rather than patches: a control two panels
  from the chooser can never make the boundary between "once" and
  "always" read clearly, and a boundary that will never be clear is
  one nobody should have to hold in their head. It composes with
  ruling 1 of 2026-08-25, which made the group the unit of work and
  gave the chooser the job of saying where a run lands; a standing
  checkbox elsewhere was a second rule about the same fact.
  THE STANDING "ALWAYS NEW" BEHAVIOUR WENT WITH IT, deliberately.
  Asking for a second map is an act you perform when you want one.
  AND THE LANDING NEEDED A DELETION RATHER THAN A REWIRING, because
  `force_new` already read the flag as one of its four terms. The
  cost was in the SUITE, as predicted: twenty-four sites, eleven
  catalogue anchors of which two were retired outright, and two
  committed probes.

- **THREE TABS ARE EXPERIMENTAL UNTIL DESIGNATED OTHERWISE, BEHIND A
  BOX THAT STARTS UNTICKED.** (Maintainer's ruling, 2026-08-30.)
  Messages, Topology and Legend are gated by an "Experimental
  features" checkbox on Map options -- the third tab, which is where
  the ruling put it. Until it is ticked the tabs cannot be activated
  and their titles are greyed; `QTabWidget.setTabEnabled` is both
  halves of that in one call, so "greyed" and "not activatable"
  cannot come apart later.
  THE TABS STAY VISIBLE rather than being removed: somebody should be
  able to see that there is more here and what ticking the box would
  give them.
  IT IS A PREFERENCE ABOUT THE PLUGIN, NOT A FACT ABOUT A MAP, so it
  does not go in a group's working state -- which would carry one
  person's appetite for experiments into another person's project
  through a saved file. That is the two-relationships framing in this
  file applied to a control.
  THE MESSAGES TAB SHIPPED FIRST, in 0.24.4 on the maintainer's ask
  of the same day. Everything the plugin has said this session, newest
  first, with the ANSWER beside any question -- because half this
  plugin's modals decide something, and a log holding the question
  alone describes a decision nobody can reconstruct. It exists because
  the message bar and the modals are two stores nothing brought
  together, which is harness fault eleven of this project's own record
  met from the user's side.

- **NUMBERS STORED AS TEXT ARE CLASSIFIABLE.** (Maintainer's ruling,
  2026-08-29, narrowing a rule to its own evidence.) A quantitative
  style never stands on a text field, and the stated reason was that a
  graduated renderer over text comes back with no ranges, so every
  tile falls outside every class and the layer paints nothing.
  MEASURED ON QGIS 4.0.3, that is true of WORDS and false of NUMERIC
  STRINGS: a String column running "10" to "120" classifies exactly as
  its integer twin -- five ranges, the same bounds, twelve of twelve
  features symbolised. The rule was true of the example that prompted
  it and wider than its evidence, and it cost a choropleth to anybody
  whose numbers arrived through a CSV join or a GeoJSON: at three
  thousand areas, three thousand and one categories.
  `_field_is_numeric` IS THE ONE OWNER and answers the wider question
  now, so all eight readers move together -- which is what stops the
  row and the assignment disagreeing. A column declared numeric
  answers True as it always did; a column declared text answers True
  where every one of its values parses.
  STRICT, AND THAT IS THE HALF THAT KEEPS IT SAFE. "Mostly numbers" is
  a column with something else in it, and a graduated renderer drops
  those rows in silence -- the very failure the old rule was written
  about, arriving through the door opened to relax it. Both answers
  are asserted in one test, because a reader meeting either alone
  would take it for the whole rule.
  AND THERE IS A SECOND HALF, FOUND BY THE FIRST FULL SUITE AFTER THIS
  WAS BUILT: no two distinct TEXTS may collapse onto one number.
  Python reads `float(" 3")` as 3.0, so a column holding "3", " 3" and
  "3 " -- three values a legend shows as three classes, and which
  `test_awkward_attribute_values_keep_their_meaning` exists to keep
  apart, since "tidying is a silent edit of somebody's data" -- passed
  the parse test and was then drawn as ONE. The ruling was made so a
  quoted CSV column could be classed as numbers; it was never made to
  merge values a reader can tell apart. So the question is not "does
  every value parse" but "does every value parse to a number of its
  OWN", which also refuses "3" beside "3.0" without needing a rule of
  its own.
  NO TARGETED RUN COULD HAVE FOUND IT, and that is the transferable
  part: every fixture written FOR the ruling held clean numbers,
  because that is what the ruling is about. The case that broke it
  lived in a test about hostile data that nobody would have thought to
  run. A green subset is not a green suite, and this is that rule
  arriving from the direction of a NEW FEATURE rather than a
  regression.
  AND IT IS CACHED, keyed by layer, column, fingerprint and data
  version exactly as `_classification_values` is. `_field_is_numeric`
  is asked once per field for the variable lists and once per element
  inside `_assignments`, which every keystroke reaches, so an
  unguarded scan would rebuild the cache-of-one defect of 2026-08-19.

- **A SAVE PRESSED WHILE A RE-TILE IS COMING IS KEPT, NOT REFUSED.**
  (Maintainer's ruling, 2026-08-29, overruling a repair of the day
  before.) With live update on, changing the design arms the live
  timer, and a press inside that window used to write the map on
  screen -- the one the person had just changed away from. Ledger row
  54 closed that by REFUSING the press in words, on the reasoning that
  a press the dialog remembers is a promise about a map nobody has
  seen yet, and that the run lands in under a second.
  THE MAINTAINER'S REASON IS ONE NO MEASUREMENT HERE WOULD HAVE
  PRODUCED, and it generalises past this control: **most people will
  not read the sentence.** A refusal that depends on being read is a
  save that quietly did not happen, and the person closes QGIS
  believing their map is on disk. So the press is KEPT, the notice
  says the map will be saved after it is redrawn rather than asking
  for a second press, and `_honour_a_queued_save` performs it once the
  new map has landed.
  ASK OF ANY REFUSAL WHAT IT COSTS THE PERSON WHO DOES NOT READ IT.
  Where the answer is work lost, the refusal is the wrong shape and
  the act belongs deferred and completed; where it is a WRONG MAP
  drawn, a refusal is still right. The in-flight refusal is unchanged
  for exactly that reason -- what is on screen mid-run is the PREVIOUS
  map, so writing it answers a different question from the one the
  press asked, silently, over the file they have just named.
  THE MECHANISM IS THE THIRD DEFERRED KIND, and it obeys the rule the
  queued-press entry ends with: consumed by taking and clearing the
  intent at the point of use, never handed to a gated path, and asked
  from three places because a landing alone cannot cover a run that
  DECLINES -- the live tick has ten gates and `_generate` eight.
  Account in MAINTAINING.md under "Three queues".

- **AND THE SECOND ONE FOUND A COLLISION BETWEEN TWO SETTLED RULES.**
  (2026-08-27, the run over the three rulings.)
  `test_a_ramp_you_are_offered_is_the_ramp_you_get` went red on its
  second half: a row turned categorical kept `YlGn`, "a ramp chosen
  for numbers". Neither the rule nor the code was wrong. The older
  rule is that a row ARRIVING in Categorized swaps a sequential ramp
  away, because a sequential ramp over categories is a cartographic
  error nobody asked for; ruling 4 of the same day remembers a ramp
  under THE MODE THE ROW IS IN. The test's own first half leaves row 1
  wearing YlGn as a CATEGORIZED row -- deliberately, that being its
  subject -- so under the ruling that row now remembers YlGn as its
  categorical choice, and the flip hands it back. The ruling's wording
  anticipates precisely this: it "would hand that back on the next
  flip -- and that is now the wanted answer, because the row wore it
  there and nobody took it off".
  WHAT TELLS THE TWO APART IS WHETHER THE ROW HAS A MEMORY FOR THE
  MODE IT IS ENTERING, and that sentence is the whole of the
  reconciliation. The second half is staged on a row that has never
  been categorized now, and both answers are asserted in the same
  test, because they differ by one thing only and a reader meeting one
  would take it for the whole rule.
  THE GENERAL FORM, which this file already carries from the other
  side: when a ruling changes what is REMEMBERED, look for the rules
  that DERIVE the same thing, and expect a test that stages the
  remembering to be the one that fails. Its fixture is no longer
  staging what its docstring names.

- **A FULL SUITE FINDS WHAT A TARGETED RUN CANNOT REACH, AND THE FIRST
  ONE HERE FOUND A DOCUMENT.** (2026-08-27.) The first full suite ever
  to complete on `for-0.24.4/copy-select-all` returned 636 passed and
  1 failed, and the failure was `test_the_documents_numbers_match_the_
  code`: the element ceiling had split in two the previous day while
  the user guide went on naming one, so a tiling user was being told a
  limit an order of magnitude under what the plugin would draw for
  them. No test aimed at the ceiling work could have found it, because
  none of them reads the guide.
  TWO INSTRUMENTS EXITED 0 WITH THE ANSWER INSIDE THEM the same hour:
  the suite itself, which reports a failure and still exits clean
  through its runner, and the mutation catalogue, which REFUSED to
  judge eight entries for want of `QGIS_PY` and printed the command
  that fixes it. Both times the verdict was in the output and not in
  the status, which is this file's own standing rule met twice in one
  session.

- **TWO ELEMENT CEILINGS, NOT ONE.** (Maintainer's ruling, 2026-08-27,
  and this one IS built.) Weaves keep `a`..`z`; tilings run `a`..`z`
  then `aa`..`zz`, capped at sixteen by sixteen. The asymmetry follows
  the two blockers `catalog.py` sets out at length, which stop in
  different places: the doubled ids are open for tilings because
  upstream supplies them and a GeoPackage keeps `tiles_aa` and
  `tiles_ab` apart, and shut for weaves because a weave is SPECIFIED
  as a string with one character per element, so "ab" already means
  two strands. 256 rather than the doubled alphabet's 702 because
  `tightest_grid` makes that exactly sixteen by sixteen.
  MEASURED BEFORE IT MOVED: all four formula families build a unit
  with exactly n DISTINCT ids at 27, 52, 53, 100, 196 and 256, at
  0.01-0.05s each. The catalogue went from 247 entries to 1,168 and
  the sweep that builds every one of them still passes.
  AND `"aa" < "z"`, WHICH IS THE HALF A DOUBLED ALPHABET BREAKS
  QUIETLY. Python compares strings character by character, so the
  twenty-seventh element sorted SECOND -- second in the assignment
  table, in the layers panel, in the design view's labels, in the
  legibility check's pairs, and second again in a resumed panel, where
  table names carry the same fault. Nothing was lost; a user simply
  could not find their twenty-seventh variable.
  `bridge.element_order` is the one owner of that question and every
  site reads it. `tools/probes/element_order_through_a_roundtrip.py`
  prints the three orders -- the dock, the file, and the dock after a
  resume -- because they are three different questions, and the file's
  own listing is right only by the accident of creation order.

- **WHEN YOU CHANGE A NAME OR A FORMAT, FIND EVERY READER -- BY SYMBOL
  AS WELL AS BY LITERAL.** (2026-08-26, twice within an hour, on one
  small change.) Naming output groups for their dataset was swept
  through the suite by grepping the string "WeavingSpace tiles", which
  found six sites and mended them; the RELEASE GATE then failed on two
  more that pin the same name through `GROUP_BASE_NAME`. A name with a
  symbol has two spellings in a tree and a search for one is a search
  for half.
  THE OTHER FACE IS DECOMPOSITION. The group chooser composes its
  label as `<name> — <dataset>`, and six places in the suite recovered
  the name by splitting on that separator -- correct until the
  separator moved INSIDE the name, after which every group answered
  "WeavingSpace tiles". They share one helper now.
  SO ASK BOTH QUESTIONS: who writes this string, and who takes it
  apart? This file already says to grep every reader of a custom
  property and every route into a handler; a name and a label are the
  same rule wearing text.

- **A FOURTH RULING OF 2026-08-26: AN OUTPUT GROUP IS NAMED FOR THE
  DATASET IT WAS MADE FROM.** `WeavingSpace tiles — nyc blocks`, the
  plugin's own name first so its groups sort together, the dataset
  after it, and a counter only where that name is taken. The
  maintainer met a panel of `WeavingSpace tiles` and `WeavingSpace
  tiles 2` after tiling two datasets in a row and asked why the
  layers panel could not say what the dialog's own chooser had been
  saying since the group became the unit of work.
  ONE FACT, TWO PLACES, AND ONLY ONE OF THEM ANSWERED. The chooser
  composed its label as `<group name> — <dataset>`; the panel had the
  counter. So the name now carries the dataset and the chooser
  appends it only where the name does not already have it -- a group
  somebody renamed, or output made before this ruling, for which the
  chooser is the only place the dataset appears.
  THE NAME IS STILL A LABEL AND NEVER AN IDENTITY. The lookup asks
  the layers; renaming stays the user's business and is never undone.
  And the dataset is taken from THE LAYER THIS RUN TILED where the
  caller knows it, falling back to the chooser only where it does
  not, which is the rule the region stamp already follows for the
  same reason.
  ITS COST WAS IN THE SUITE, and worth knowing: six call sites
  recovered a group's name from a chooser label by splitting on the
  separator, which was right until the separator moved inside the
  name. They route through one helper now. When you change how a
  label is composed, grep for whoever DECOMPOSES it.

- **A THIRD RULING OF 2026-08-26: A KEPT SCHEME IS HELD, NOT OWNED.**
  An element whose class-source file cannot be read keeps the colours
  it is drawing, and it keeps them by having them RECORDED -- a
  renderer alone lasts until the next run, restyle or reopen, and then
  the element falls back to automatic colours with nothing said. They
  are recorded as HELD rather than as picks: `_kept_for_unreadable`
  shadows the hand-picked record entry for entry, banks with it under
  ruling 8, and travels in the layer's own stamp so the plugin being
  closed and opened again keeps the distinction. The moment the file
  can be read again it takes its colours back, BEFORE anything is
  seeded from them -- a held colour outranks a template, so a late
  release repaints the map with the colours the file had before it
  went away.
  IT SETTLED A COLLISION BETWEEN TWO REGISTERED TESTS, which is why it
  is a ruling and not a fix. One required the element to own those
  colours ("a missing file is a reason to stop consulting the file,
  not a reason to repaint somebody's map"); the other, written the day
  before, required the record to stay empty, because colours that
  outrank a template make restoring an edited scheme change nothing.
  Both harms were real and measured. WHEN TWO SETTLED RULES GIVE ONE
  ACT TWO ANSWERS, THE ANSWER IS USUALLY BOTH -- with the thing that
  tells them apart written down.

- **A STAMP TAKEN AWAY FROM A LANDING MAY CARRY ONLY WHAT A LANDING
  DECIDED.** (2026-08-26, ledger rows 55-57, three regressions in one
  mechanism.) `_stamp_working_state` takes the design, the output path
  and the region from the launch snapshot when it is given one and
  from the LIVE CONTROLS when it is not -- which was harmless while
  landings were the only writers, and became three defects the day
  round nine added two writers that never stand at a landing. Move the
  design controls after a map lands and one adopted dock edit made the
  group claim a design its layers were never drawn at; switch the
  chooser and the group was filed under a dataset it was not made
  from, which is the fact the landing's refusal and the group binding
  both read. Those three keys are CARRIED from the record already on
  the group now, and only a landing may move them.
  TWO MORE CONDITIONS BELONG TO THE SWITCH-OUT STAMP ITSELF, and both
  are about attribution rather than timing. A dataset that has been
  REMOVED leaves nothing to stamp: the table is blank because its
  fields went with it -- a blank the plugin imposed -- and this
  handler runs for every dialog whose combo re-emits, including one
  the user has closed, so it wrote that blank over a good record and
  the next dialog opened in that project met a table describing
  nothing. And the group must be the OUTGOING DATASET'S OWN MAP, asked
  of the layers' stamps: `_group_of_our_layers` answers where this
  dialog's layers are, which is where the last run landed.
  ASK OF ANY WRITER THAT COPIES A RECORD: which moment is each field
  about, and does this writer stand at that moment?

- **A GREEN SUBSET IS NOT A GREEN SUITE, AND THIS PROJECT BELIEVED ONE
  TWICE IN ONE DAY.** (2026-08-26.) Round nine was verified by
  targeted runs -- every fix's own test, every neighbour anybody
  thought of -- and shipped FOUR regressions, each one an ordinary
  journey: open the plugin in a project that already holds a map and
  every row came up blank with Generate refusing for want of a
  variable. What found them was the mutation workflow's coverage leg,
  which runs the WHOLE suite: green at `6d6ea2d`, red at `64cb0fa`,
  four named tests, all four reproduced here on the first attempt.
  The rule already written is that a change to a core path is verified
  by the whole suite and that the candidate is where that happens.
  What this adds is the failure mode when the rule is skipped: the
  four survived a hunt round aimed at exactly that code, because a
  hunt asks what MIGHT be broken and the suite asks what IS.

- **A STRING THAT CARRIES A PATH INSIDE IT IS A PATH.** (2026-08-26,
  the Windows red of six CI rounds.) `same_destination` exists
  because one file has two spellings -- Windows short names, case
  folding, separators -- and it was applied faithfully to output
  PATHS while seven sites went on comparing LAYER SOURCES with `==`.
  A source only looks like an opaque token; it is a path plus
  `|layername=`, and a project save respells the path half. So a
  reopened project's own output group read as ANOTHER dataset's, and
  the guard protecting a kept result refused the ordinary recovery
  run -- through a MODAL, so the message bar stayed empty and the
  user met a Generate that wrote nothing and said nothing.
  `same_source` is the one owner now: file half through
  `same_destination`, tail case-folded.
  AN EIGHTH SITE WAS FOUND THE SAME NIGHT, and how it survived the
  sweep is the lesson. The seven were all a STAMP compared with a
  STAMP; the eighth compares a stamp with the SOURCE OF THE LAYER IN
  FORCE, in the gate that decides whether a saved record's pins and
  hand-picked colours may come home. Same question, same boundary, a
  different pair of operands -- so a search for the first shape found
  nothing, and three Windows-only reds turned on it. WHEN YOU FIND A
  FAMILY, SWEEP FOR THE QUESTION RATHER THAN FOR THE PHRASING.
  ASK OF ANY IDENTIFIER WHETHER A FILESYSTEM EVER TOUCHED IT. Where
  it did, the string that comes back is not the string that went
  out, and `==` is a bug waiting for the platform that shows it.

- **ATTRIBUTION BEATS DELTA, AND THREE NARROW GUARDS ARE THE SIGNAL
  TO STOP PATCHING ROUTES.** (2026-08-26, ledger row 48, and it is
  the sharpest thing the bulletproofing round taught.) The
  categorized adoption walk asked what CHANGED -- adopt any colour
  differing from what the plugin would seed NOW -- and a landing that
  keeps a renderer over an unreadable class source makes that
  question lie: `expected` falls back to automatic colours while the
  map honestly wears the template, so the template's own colours were
  adopted as a person's hand-picks and outranked the template
  forever. THREE successive fixes each closed one route and left
  another: a skip in the landing's re-examination, a skip in the
  deferred-adoption replay, then a colour-precise marker -- and the
  reworked test caught a fresh route past every one. What ended it
  was asking the question the state can answer at ANY moment:
  `_painted_categories` records what the plugin itself painted, the
  categorical twin of `_painted_ladders`, so the walk asks WHOSE
  colour this is. All three narrow guards were then deleted.
  THE RULE: when the third narrow guard leaks, stop asking which
  route is missing and ask whether the question is right. This file
  already says the same about `_table_id_colours`, which was wrong
  six times until it stopped enumerating and read what the map draws.

- **EVERY EXIT FROM A LONG METHOD NAMES ITSELF, AND A MODAL REFUSAL
  IS THE QUIETEST OF ALL.** (2026-08-26.) Live update has named its
  ten gates since two diagnoses were lost to its silence; `_generate`
  has EIGHT exits and named none, so a Windows-only failure where the
  recovery run left no file, no layers and no message could not be
  read off a log at all. Each exit dumps now, and the
  keep-the-previous-result guard prints its whole decision rather
  than the fact of it.
  THE MODAL IS THE PART TO REMEMBER: that guard refuses through a
  QMessageBox, which in a headless suite lands in the shim's MODALS
  and never reaches the message bar -- so a run refused there is
  indistinguishable from a run that was never launched. The ledger
  already carried this as harness fault eleven; it recurs because
  the two stores are read by different code. Read both.

- **A GUARD ADDED TO ONE DOOR BELONGS AT EVERY DOOR INTO THE SAME
  ROOM.** (2026-08-25, and it is the sharpest thing the group-unit
  build taught.) A regression showed that taking a group over while a
  run was IN FLIGHT erased the evidence the landing was about to read,
  so `self._task is not None` was added to `_bind_group_to_dataset`.
  Two other methods reach the same work -- `_on_group_chosen` and
  `_resume_from_gpkg` -- and neither got it, because the fix was made
  where the failure was REPORTED rather than where the behaviour
  lives. A hunt found the asymmetry within the hour, working backwards
  from harm.
  ITS PREDICTED HARM WAS MEASURED FALSE ON 2026-08-26, and correcting
  that here matters more than the tidiness of the rule. The hunt
  reasoned that picking a group mid-run would repoint the records the
  landing reads as `old_ids` and that the run would then remove the
  layers of the group just switched TO. The first half is true and the
  second is not: driven both ways -- another dataset's group, and the
  same dataset's other group, where the region stamps cannot tell them
  apart -- every layer survived, because the landing's own refusal to
  write over a map made from another dataset forces a new group and
  empties `old_ids` on the way past. `tools/probes/a_group_chosen_mid_
  run_deletes_its_map.py` is that measurement, and it is committed so
  nobody re-derives it.
  THE RULE IS UNTOUCHED BY THAT, and it is worth saying why rather
  than quietly rewriting the entry. The asymmetry is real, and it is
  held REDUNDANTLY rather than harmlessly -- exactly the state this
  file records from the other side, where an omission ruled benign
  went live three hours after a fix removed the accident that was
  hiding it. A guard that is missing and currently costs nothing is a
  countdown, not a defence.
  THE HABIT: when a guard goes in, grep for every caller of the thing
  it protects and ask which of them can be in the same state. This
  project already says the same about signals ("grep for the other
  routes into the same handler"), about clear sites ("enumerate what a
  clear site LEAVES"), and about pairs; this is the same rule wearing
  a fourth set of clothes, and the fourth time is the one that should
  make it a reflex.

- **A HARM NAMED BY READING IS A HYPOTHESIS, EXACTLY LIKE A SITE.**
  (2026-08-26, judging nine hunt claims.) This file already says that
  a location reasoned out of the source reads exactly like one
  somebody proved. Three of those nine described the code CORRECTLY --
  a guard really was missing from two of three doors, an embedded
  region really does load under a source string the gate can never
  match, both measured -- and not one of them costs a user anything,
  because in every case a second mechanism answers first.
  THE TELL IS THAT THE CLAIM STOPS AT THE LINE. A guard is missing:
  therefore what? Walk it to the end. Where the answer really is a map
  deleted, driving it says so unmistakably -- four layers of one
  dataset's tiles removed by a run on another, the same day. Where you
  cannot reach a loss, the honest finding is that the behaviour is
  HELD REDUNDANTLY, which names what would have to move before the
  asymmetry starts costing something; this project has already watched
  a masked omission go live three hours after the mask was removed.
  AND CHECK THE CLAIM'S DIRECTION, not only its subject. The one
  finding that mattered most was reported the wrong way round: a
  record and a layer stamp disagreed about which dataset a map came
  from, and the claim named the record as the wrong half where the
  record was right. Following the reading rather than the measurement
  would have moved the field that was already correct. Of one fact
  written twice, ask which of the two writers had a REASON.

- **A GATE CAN BE SATISFIED BY A SENTENCE DENYING IT.** (2026-08-26.)
  `check_roadmap` is the first stage of every release and refuses a
  candidate while the version's section lists work; it decided that by
  searching for the words "nothing outstanding". The section carried,
  honestly, "the reason this section does not yet say 'nothing
  outstanding'" -- followed by a page of owed work -- and the gate read
  the denial as the declaration and cleared the tree.
  A QUOTED PHRASE IS A MENTION, NOT A STATEMENT, and stripping quoted
  spans before looking is what keeps the phrase prose-first (the
  reason it was chosen over a marker) while making it impossible to
  satisfy by discussing it. The general form joins "a check that can
  only confirm is not a check": when a gate reads PROSE for a
  decision, ask what the document says ABOUT that prose, because a
  file that explains its own conventions will quote them.
  It had never had a test. It has one now, which plants the exact
  sentence in all three quoting styles AND requires a plain
  declaration to still pass, since a gate nothing can satisfy is as
  useless as one anything can.

- **PRESENCE IS NOT ORDER, AND A CALL PUT BACK IN THE WRONG PLACE IS
  WORSE THAN ONE STILL MISSING.** (2026-08-26, and FOUR hunts of eight
  found it independently -- the most this method has ever converged
  here.) `_resume_from_gpkg`'s take-over branch was missing
  `_recover_the_source`; the repair added it AFTER
  `_apply_working_state`, where the twin calls it BEFORE and says why
  at its own call site: a variable cannot be restored to a column the
  region layer in force does not have.
  FOUR CONSEQUENCES, one per hunt. Every element's variable re-derived
  against the other dataset's columns, so the table described a map
  the layers did not draw. `same_data` computed against the stale
  chooser, so the pins and the categorical colours were skipped
  outright and a pinned ladder came back re-derived. The group then
  stamped with that loss. And `_take_over_group` adopting the resumed
  layers' stamps while `_memory_layer_id` still named the OTHER
  dataset, writing one map's hand-picked value strings into that
  dataset's bank and its GeoPackage -- ruling 8's cross-dataset leak,
  reached from a direction it was not written for.
  THE REPAIR TURNED VISIBLY WRONG INTO INVISIBLY WRONG, which is one
  hunt's phrase and the reason this is a rule rather than a ledger
  row: before it, the chooser sat on the wrong dataset where a person
  could see it; after it, every symptom moved inside the records.
  THE TELL: WHEN A TWIN'S CALL SITE CARRIES A COMMENT, THAT COMMENT IS
  USUALLY ABOUT THE POSITION. Copying the call and not the comment
  copies the half that does not encode the reasoning. This file
  already says to check a fix's ORDER against its twin rather than
  merely that the line is present; what is new is that the check
  survives being applied by somebody who knows the rule -- it was
  broken here in the same hour by the same hand that had just quoted
  it.

- **BEFORE CLEARING ON AN ABSENCE, ASK WHAT MAKES THE RECORD ABSENT.**
  (Same day, and it is the other half of the same evening.) A restore
  was taught to CLEAR a record where the incoming one is silent about
  it -- the cure for a real defect three hunts had reported, where one
  output group's colours rode onto another. But `_assignments` reports
  the pins, the hand-picked class colours and the ramp window as empty
  for ANY ROW NOT WEARING GRADUATED, and the categorical colours as
  empty for any row not wearing Categorized. So a record is silent
  about them whenever the element is merely on another style, which is
  not the same claim as "this group has none" -- and the clearing
  destroyed a pinned bound belonging to an element somebody had
  switched to categories, stamping its absence so a reopen could not
  recover it. That is the ruling of 2026-08-20 broken by the fix for
  a different one.
  SO ENUMERATE THE READERS THAT CAN PRODUCE THE ABSENCE. Here there
  were two: a person who chose nothing, and a mode that cannot carry
  the thing at all. This file already asks what an absent key MEANS
  when a guard READS one; deleting on that absence needs the same
  question asked harder.
  AND THE FIX WAS INERT UNTIL THE WHITELIST KNEW ABOUT IT.
  `WORKING_STATE_ELEMENT` is the record's real definition, `mode` was
  not in it, so the gate read None and cleared nothing whatever. Two
  tests going red is how that was found. WIDEN THE WHITELIST IN THE
  SAME COMMIT AS THE CODE THAT READS IT -- said here for the third
  time, after `_adopt_dock_bounds` and the copy.
  A FOURTH ON 2026-08-30, and the first where the rule was applied
  BEFORE the defect rather than after it: the topology edit list is
  not a widget, so it rides neither whitelist's table and is written
  and read by hand -- `_capture_working_state` and
  `_restore_recorded_topology_edits` went in together, with a test
  that sends the record through `json.dumps` because that is what the
  GeoPackage does to it, and a catalogue entry standing on the write
  and the read SEPARATELY. Two entries rather than one deliberately:
  either half alone leaves a record that is faithful in the file and
  dropped in silence on the way back, and an entry that can be
  satisfied by its sibling is an entry that reports `caught` about
  nothing.

- **WHEN A REPAIR GIVES ONE STORE A NEW WRITE, ENUMERATE EVERY STORE
  THAT ALREADY HELD THAT FACT.** (Same day, the round's last two
  findings, and the shape this project meets most often.) A restyle
  was taught to write the GROUP's record, with a comment arguing
  exactly why. The FILE's record was given its write hours later, by a
  different commit, on the landing path alone -- so it inherited the
  gap the first write had just closed: the file's STYLES were updated
  by a restyle and its RECORD was not, and a colleague opening that
  GeoPackage without the project resumed a design the user had
  abandoned, their first Generate repainting the map back to it. The
  file disagreed with itself.
  AND THE SECOND STORE IS SOMETIMES A WIDGET. A class source restored
  into `_class_choices` by a group switch was read by nobody, because
  `_sync_row` repopulated the combo without re-selecting it from the
  record -- and `_assignments` reads the WIDGET, so the next rebuild
  wrote the stale answer back over the restore. Its neighbour in the
  same table had been given that exact fix eight days earlier.
  The list of stores is short and never empty. It is the one nobody is
  looking at that costs the map.

- **A RECORD ASSEMBLED FROM TWO MOMENTS MUST SAY WHICH MOMENT EACH
  FIELD CAME FROM.** (Same day.) The working state deliberately takes
  its DESIGN from the launch snapshot and its ELEMENTS live, and both
  halves are right for good reasons written at the code.
  MEASURED ON 2026-08-26, AND THE FAULT WAS THE OTHER WAY ROUND. This
  entry said `region` travelled with the design half and therefore
  filed a new dataset's hand-picked colours under the old dataset's
  source. Driven -- switch the region layer mid-run, then read both
  stores -- the RECORD was right: it takes `region` from the launch
  snapshot, and the launch snapshot is what the tiles were drawn from.
  What was wrong was the second, quieter writer of the same fact:
  `_add_output_layers` read `weavingspace_region` off the region
  CHOOSER as the run landed, so every output layer claimed whichever
  dataset the user happened to be looking at. A's tiles came out
  stamped as B's; the chooser then labelled A's map with B's name, the
  binding handed that group to B, and the refusal whose whole job is
  to stop a landing writing over another dataset's map read the same
  wrong stamp and let a run on B replace it. Four of four layers
  destroyed. It is asked of `source_layer` now -- the layer this run
  tiled, which the landing has held as a parameter all along.
  SO THE RULE STANDS AND ITS EVIDENCE IS DIFFERENT. Ask of any record
  built from two readings: for each field, WHICH reading is it about?
  A field that describes the DATA belongs with the data's moment, and
  one that describes the DESIGN belongs with the design's. And where
  one fact is written TWICE, ask which of the two writers has a
  reason -- the hunt that reported this named the wrong half, and
  following the reading rather than the measurement would have moved
  the field that was already correct.

- **THE SIZE GUARD ASKS; ONLY WHAT IS NOT A SIZE IS REFUSED.**
  (Maintainer's ruling, 2026-08-25: "Warning not absolute. Find a
  different approach to sentinel if appropriate.") Above
  `MAX_TILES_CONFIRM` a run is confirmed in ordinary words; above
  `MAX_TILES_HARD` the SAME question is put in stronger ones -- this
  may use all the computer's memory, QGIS may stop responding, save
  your project first -- with the safe button as the default, on the
  dependency-consent precedent. One question whose wording escalates
  by band, rather than two gates, because a second gate saying no at a
  second number is the arrangement that was already wrong once.
  WHAT THE REFUSAL STOOD ON was a comment claiming the run would
  exhaust memory and kill QGIS: a figure NOTHING IN THIS REPOSITORY
  MEASURES, and one the maintainer's own argument disposes of --
  different machines have different maximums, and different designs
  have different needs at the same tile count. It had already been
  wrong in the expensive direction, refusing a map the library renders
  in five seconds (ledger row 23, 2026-08-19).
  THE SENTINEL IS WHY IT COULD NOT SIMPLY SOFTEN, and this is the part
  that generalises. `MAX_TILES_HARD + 1` was ALSO the answer for two
  cases that are not about size: a unit whose vectors are degenerate,
  so the design does not repeat across the plane, and an estimate that
  comes back non-finite, which is what a layer with no CRS produces.
  Sharing a value meant sharing a SENTENCE -- both told somebody to
  try a larger spacing, which helps neither -- and it meant that
  softening the ceiling would turn a broken design into something a
  user clicks straight past. They are `bridge.UNTILEABLE` and
  `bridge.UNCOUNTABLE` now, NEGATIVE on purpose: every gate here asks
  `est > <ceiling>`, so a sentinel smaller than every ceiling cannot
  be waved through by a comparison somebody forgot to widen. It has to
  be handled explicitly or it does nothing at all.
  THE GENERAL FORM: when one value stands for several different
  answers, softening the treatment of any of them softens all of them.
  Ask what else shares a sentinel before changing what a threshold
  means.

- **A BLANK THE PLUGIN IMPOSED IS NOT A CHOICE THE USER MADE.** An
  element left on "---" stays unassigned through rebuilds, because
  cycling a default back in would undo a deliberate switching-off. But
  a table built when NO FIELDS were on offer leaves every row blank
  for a reason that has nothing to do with anybody's intent, and
  honouring those blanks is how a plugin opened before its data ends
  up refusing to draw and blaming the user for not assigning a
  variable -- the field report of 2026-08-15. `_fieldless_build`
  tells the two apart.
  THE SAME ROAD REACHES RECOVERY, which is where the rule had to be
  decided rather than inferred. A region layer whose file has moved
  loses its elements' variables; when the user then points the chooser
  at a live layer, the elements AUTO-ASSIGN as they would on any other
  day, rather than staying blank. That reverses the contract
  `test_a_project_whose_region_layer_has_moved` had held since it was
  written, and the test said so itself rather than quietly bending --
  it required the change to be re-decided, and the maintainer decided
  it on 2026-08-15. What the test now guards is sharper than what it
  gave up: the assignments must name columns THE NEW LAYER HAS, since
  carrying the lost layer's columns onto different data is the real
  harm nearby. Catalogue entry
  `a-blank-a-failure-imposed-is-not-a-choice`.
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
- **A constant numeric column gets ONE class, and a notice.** Asked
  for five classes over a column that is 7 everywhere, QGIS returns
  five, all reading "7 - 7" in five different colours. The map was
  never wrong; the legend was, and the legend is what a reader trusts.
  `make_graduated_renderer` collapses to k=1 and the dialog reports
  it -- UNLESS the element is pinned, for which see the ruling below.
  (User instruction, 2026-08-09.)
  **THE GENERAL FORM WAS WITHDRAWN ON 2026-08-16, AND SO WAS THE
  NUDGE THAT BRIEFLY REPLACED IT. Read this before the history below
  it.** Reducing k re-samples
  the ramp: class i takes `ramp.color(i/(k-1))`, so a shorter ladder
  spreads its survivors across the whole ramp and every colour moves
  with nobody choosing to move it. Measured that day, five asked over
  four distinct values on Reds: the map drew the FOUR-class ladder
  exactly, and neither middle colour was one the five-class ladder
  would have used. It is also unstable -- a column that gains a value
  later re-colours every class -- which is the thing
  one-colour-one-meaning exists to forbid. The maintainer's rule is
  that an empty class is INVISIBLE, NOT DELETED.
  WHAT CURED THE ORIGINAL SYMPTOM WAS TRIED AND IS ALSO GONE, and this
  paragraph described it as current until 2026-08-18.
  `bridge._nudge_off_shared_bounds` moved every finite-width range's
  upper bound down by one unit in the last place where the classifier
  had returned DEGENERATE ranges, so a value on a shared boundary fell
  into the degenerate range that means exactly it. It was withdrawn
  hours after the reduction was, in the same afternoon, and the
  function no longer exists -- `unworn_classes` says "the experiment
  is gone" at its own docstring. Measured 2026-08-18 on {10 x8, 20,
  30} at k=5: three degenerate ranges, no bound moved, and 20 lands in
  class 4. The three withdrawn attempts and what each taught are in
  docs/TESTING.md under "Three ways to move a class boundary"; what
  survives is that an empty class is INVISIBLE, NOT DELETED, and that
  emptiness is reported in words.
  A BINDING FILE THAT NAMES A DELETED FUNCTION IS WORSE THAN ONE THAT
  SAYS NOTHING, because it is read as the current design and its
  mechanism looked for. This one contradicted itself: the withdrawal
  was already recorded four hundred lines above.
  IT IS SCOPED, and the scope is the whole safety of it: on ordinary
  data every range has width, nothing is degenerate, and no bound
  moves. Shrinking bounds generally would push any value sitting
  exactly on a break up into the next class, reversing QGIS's
  convention across every classed map for no benefit.
  The ONE-VALUE COLLAPSE survives as a deliberate carve-out
  (maintainer's ruling the same day): five ranges all reading "7 - 7"
  in five colours is a legend claiming variation the data lacks, and
  marking four of them would not cure that.
  A PIN OUTRANKS IT (maintainer's ruling, 2026-08-17, ledger row 43).
  Pinned bounds give a constant column REAL ranges, so the sentence
  the collapse exists to prevent cannot be produced, and the two doors
  into a pinned ladder had disagreed: a copied ladder of -5/10/25/40
  drew five classes while the same bounds as pins drew one, silently,
  with the pin accepted and stamped. `bridge.py` reads
  `if distinct == 1 and not pinned_here`.
  The break values are otherwise QGIS's own, moved by an ulp its label
  formatter rounds away, so the legend still reads "1 - 5", the
  renderer is an ordinary graduated one, and pressing Classify
  restores QGIS's untouched answer.
  **The history of the withdrawn reduction, kept because the first
  attempt at it failed too and the reasons still instruct.**
  Five classes over three distinct values puts two swatches in the
  legend that no tile uses and draws the highest value mid-grey
  (measured 2026-08-13 with a render context); upstream's own
  `_plot_subsetted_gdf` reduces k in exactly that case. It was
  implemented and reverted the same night, because it counted the
  distinct values on the ELEMENT layer, which holds only that
  element's tiles -- so two elements carrying the same variable could
  draw different class counts, and
  `test_metamorphic_variable_permutation` failed at once. What made
  the second attempt work is the entry below: the count and the
  breaks both come from the whole map now, so every element agrees.
  Nineteen tests moved on the first attempt, which is the measure of
  how deep the assumption ran.
- **ONE COLOUR MEANS ONE THING, wherever it appears — and the rule is
  about MEANING, not about breaks.** That wording matters and cost a
  year: it was written down as being about class BREAKS, so when the
  graduated half was fixed on 2026-08-14 nobody looked at the
  categorized half, which had the identical fault and had been
  shipping since 0.23.0. Categorical colours follow ListedColormap
  sampling — code/(k-1) through int(x * N) — so the NUMBER of
  categories decides which colours are drawn, and a value one element
  happens not to contain re-colours everything after it. Measured
  2026-08-15: four elements on one column and one tab10 ramp, three
  finding six values and the fourth five, so `#1f77b4` meant 'bare' on
  three elements and 'crops' on the fourth. Settled by `/grill-me` the
  same day. If a rule here names a mechanism, ask what it is FOR
  before deciding what it covers.
  Both halves work the same way: the whole map's values decide, the
  element's own values are what it draws. A graduated element wears
  breaks cut once from the region; a categorical element takes each
  value's colour from that value's position in the region's sorted
  list while carrying ONLY the categories it actually holds — listing
  a value no tile of it draws would tell a reader something false
  about that element. The Classes cell on a categorized row reports
  what its own element draws, so rows sharing a column may read 6, 6,
  6, 5 and all four are true; no notice is raised when they differ,
  because elements differ routinely and a warning that fires
  constantly is one people learn to ignore. HAND-PICKED colours stay
  per element: what this rule forbids is a colour shifting with
  nobody choosing it, and a hand-pick is a person choosing. A
  reopened project is trusted rather than repainted, so a project
  saved before this keeps its old colours until something re-seeds.
  Class breaks
  are cut ONCE, from the region layer's values, and every element
  carrying that column wears them. Until 2026-08-14 they were cut
  from each ELEMENT layer, which holds only that element's tiles:
  measured on QGIS 4.0.3 at n=12 with k=5 and no reduction involved,
  four elements carrying one variable produced four different
  legends (element a's second class ran 3.4-14.0 where element c's
  ran 4.0-13.6), so one colour meant four different numbers on a map
  whose whole purpose is reading elements against each other. It
  survived because the standard fixture asks for more classes than it
  has distinct values, which collapses quantile breaks onto the
  values themselves and makes elements agree by accident.
  This DEPARTS from upstream, which classifies each element's subset
  separately, and the departure is deliberate under the rule that the
  plugin may have its own ideas where they fit this kind of map.
  Three consequences to keep straight. The user's region layer is
  never filtered for it: the null workaround hides rows, so the
  values are copied into a geometry-less scratch layer the plugin
  owns (`bridge.classification_source`), built once per column rather
  than once per element. Unclassed rides the same rule, its fifty
  steps spanning the whole column's range rather than one element's.
  And the reference comparison stays a real differential because
  `TiledMap.render` accepts the same breaks through
  `classification_kwds` -- computed there by mapclassify over the
  region, never read off our renderers -- except where a case maps
  DIFFERENT columns to different elements, since those kwargs are
  broadcast to every element and one set of bins cannot be right for
  all of them. Guarded by
  `test_one_variable_gets_one_legend_wherever_it_appears`.
  **PINNING IS AN EXCEPTION TO THIS RULE, and the maintainer decided
  so deliberately.** A pinned bound moves the breaks on the element
  that carries it, so a colour on that element can stop meaning the
  numbers it means elsewhere -- which is precisely what the rule
  above forbids when nobody chose it. The difference is that
  somebody did choose it. A pin is a person saying "this break is
  mine", exactly as a hand-picked colour is, and the rule has always
  been about a colour shifting with NO ONE deciding. So a pin is not
  a hole in one-colour-one-meaning; it is the same carve-out as a
  hand-pick, arriving through a different control. Read the rule as:
  the plugin never moves a meaning on its own, and a person may.
  (Maintainer's ruling, 2026-08-15.)
- **CLASS BOUNDS A PERSON SET, and the record that holds them.**
  Added 0.24.3, settled by `/grill-me`. A user may PIN the first
  and/or last class and type its inner bound: the samples inside a
  pinned class leave the pool, the scheme cuts the row's count minus
  one class per pin, and the pinned classes are put back around the
  result with the outermost computed edge SNAPPED to the pin so the
  ladder has no gap. Done by extending the subset string
  `make_graduated_renderer` already sets and restores for nulls, so
  QGIS keeps deciding every break we do not pin. A user may also COPY
  a whole classification to another element, which is every boundary
  pinned at once and shares the same record.
  **That record holds two things and they are not the same claim**:
  the boundary VALUES a person set, and a per-end PIN FLAG saying
  which ends they pinned. For pins alone the two coincide; a copy
  separates them, and collapsing them would make every copy look
  fully pinned and leave "unpin" with nothing to do. A copy therefore
  DEGRADES TO ITS PINS: a new class count or scheme retires the
  copied values and keeps the flags and their bounds, since a pin is
  a smaller and more durable statement than an imported ladder.
  Keyed by tile id AND field like the hand-picked colours, stamped on
  the layer because nothing on a renderer records that a break was
  chosen rather than computed, and carried in both signatures.
  What is REFUSED is only what cannot be DRAWN, and there are three:
  crossed bounds, nothing left for the middle to cut, and a ladder
  asked to carry more pinned boundaries than its k-1. A BOUND OUTSIDE
  THE DATA IS NOT ONE OF THEM. It was until 2026-08-17, when the
  maintainer met the refusal and reversed it: giving one pair of
  limits to several variables is exactly the thing somebody wants,
  since it is how a colour comes to mean the same number on every map,
  which is this plugin's own claim about what these maps are for. Such
  a bound draws perfectly well; its outer class simply goes unworn,
  which `unworn_classes` already computes.
  THE GROUPING WAS THE ERROR AS MUCH AS THE POLICY, and that is the
  part that generalises: listed in one sentence beside the undrawable
  three, a preference reads as a rule, and nobody re-examines it.
  When you find four refusals written together, ask whether they are
  the same kind of thing.
  Relaxing the guard was also only half the fix --
  `_apply_pinned_bounds` built the outer class from the column's own
  extreme, so the ladder snapped back to the data and the accepted
  number changed nothing visible. Guarded by
  `test_a_pin_may_sit_outside_the_data_it_classifies`, which caught
  exactly that, because it drove the renderer rather than the guard.
  What is ACCEPTED and explained is a pin leaving fewer distinct
  values than classes -- that is the reduction above, and two answers
  to one question is what these rules exist to avoid.
  **EQUAL INTERVALS ARE CUT FROM THE PIN, NOT STRETCHED TO IT.**
  (Maintainer's rule, 2026-08-17: with Equal intervals or Unclassed
  every class has the SAME WIDTH, and the one exception is a pinned
  end, whose class takes whatever width the user's bound gives it.)
  Measured false the day it was stated, and the MECHANISM was the
  fault rather than the arithmetic: the scheme cut k-pins classes
  from the samples between the pins, which is each column's own data,
  and `_apply_pinned_bounds` then stretched the outermost computed
  class out to reach the pin. Two columns pinned alike to -5..40 at
  k=5 drew widths 0, 10, 4, 31, 0 and did not agree with each other.
  So the middle is cut over the span the pins declare. Equal widths
  follow by construction, the gap the stretch existed to close cannot
  open, and two columns with the same limits draw the SAME LADDER --
  which is the whole reason for giving them the same limits. The
  stretch still runs and is a no-op there, deliberately, so the outer
  pinned classes go on being built in one place for every scheme.
  Two consequences. The DISTINCT-VALUE REDUCTION is exempted on that
  path: three classes over -5..40 are the same three whatever the
  column holds, so reducing k would hand a sparse column a different
  ladder from a full one under identical limits. And the rule reaches
  Equal intervals and Unclassed ONLY -- quantiles, Jenks and pretty
  breaks are statements about where the data sits, so cutting them
  over a span the data does not occupy would mean nothing. Guarded by
  `test_equal_intervals_stay_equal_under_a_pin` over three columns,
  including one whose middle holds too few distinct values to fill
  the ladder, and by two catalogue entries.
  Two things the map may then show that nothing else here would. A
  copied ladder can leave classes the receiving column cannot reach;
  those are KEPT rather than dropped, because a copy reproduces a
  classification and a silently shortened one does not, and
  `empty_classes_message` says in words how many are empty, on the
  count `unworn_classes` measures from the ladder actually drawn.
  The swatch
  hatched those stripes as well until 2026-08-17; see the entry
  below. And a pinned row is NOT Custom: its
  colours are still its ramp's, so the cell goes on naming the ramp
  and the swatch merely BOXES the pinned end.
- **What ELEVEN defects taught about that feature pair, 2026-08-15.**
  Six hunts pointed at the pinned bounds and copy-to alone found
  eleven, every one a wrong map rather than a crash, and four rules
  come out of them that generalise past this feature.
  A RECORD HOLDING TWO CLAIMS must be tested with both in force: the
  pin record holds copied boundary VALUES and per-end pin FLAGS, each
  worked alone, and together the pin did nothing while the button
  stayed down and the number was stamped.
  TWO DOORS INTO ONE STATE, one guarded, is where the next one lives:
  `pin_problem` used to refuse every pin on a constant column -- it does
  NOT since the out-of-data guard was lifted on 2026-08-17, and the
  same stale sentence survives in the suite at the test that records
  this lesson -- a copy is not
  guarded that way, and the colouring branch downstream had been
  written for the guarded door -- so a copied ladder on a one-value
  column drew flat placeholder grey.
  A CONTROL MUST BE ABLE TO REPRESENT ITS DOMAIN, which every guard
  here checked past: the bound box had a fixed range of 1e12 and six
  decimals, so a province area in square metres pinned an order of
  magnitude out and a rate pinned at zero, both silently, because
  `pin_problem` is asked about the number the CONTROL produced.
  A UNIT-TESTED MECHANISM PLUS AN UNDRIVEN CALLER IS A MOTIONLESS
  AXIS: `bridge.unworn_classes` was careful and covered, and the
  dialog path calling it had never once produced hatching, because
  the swatch was painted before the restyle and asked its question of
  the previous map. When a feature's promise is visual, drive it to
  the pixels. (The hatching itself was withdrawn on 2026-08-17; the
  lesson is about the shape and outlives the feature.)
  Two consequences are now settled behaviour rather than accident.
  A copy CHECKS each pin flag against the receiving column and leaves
  behind what that column cannot reach, saying so; and an Unclassed
  source's fifty never reaches `_class_counts`, which is the record
  that means CHOSEN.

- **A RANGE IS NOT THE ONLY THING THAT EATS A KEYSTROKE.** Four
  defects on 2026-08-17 were controls silently refusing what a person
  typed, and each was invisible to `setValue`, which clamps without
  complaint. The mechanisms differ and the tell is identical:
  a validator refusing a keystroke past `maximum` (the pinned-bound
  box at 100x the data; the Ramp Display Range's two percent boxes,
  each clamped by the OTHER's current value, so from a window of
  (0, 40) typing 60 kept SIX); `decimals` lowered to tidy a display,
  so Rotate at zero places turned 22.5 into 22; and a
  `valueChanged` HANDLER THAT REWRITES ITS OWN BOX -- `_skip_zero_scale`
  fired per keystroke because keyboard tracking was on, so typing
  -0.5 announced a landing on zero after the leading nought and the
  design came back UN-MIRRORED at a size that looks exactly right.
  So: any box whose `valueChanged` is watched by something that
  writes back to it needs `setKeyboardTracking(False)`; a no-crossing
  rule between two boxes is enforced when the number is COMPLETE, not
  by clamping ranges, because a validator is asked one keystroke at a
  time and `6` is a prefix of `60`; and a control must be able to
  represent its whole domain, which is where this rule started.
  TEST BY TYPING. Every guard on every one of those four drove
  `setValue` or `stepBy` and passed throughout; one docstring even
  said "dragging or stepping", so typing was never in view.

- **A REFRESH WITH ONE CALLER IS A REFRESH THAT ONLY WORKS ONCE.**
  `_refresh_ramp_icons` redraws a row's ramp swatch in its own
  direction and is called from exactly one place, the Reverse toggle;
  `_make_ramp_combo` built every item forward. So the flip lasted
  until the next rebuild -- and a Generate rebuilds, because adding
  output layers makes the layer combo re-emit, as do a spacing
  change, a family change and reopening the project. A user then read
  a reversed element by a forward swatch and chose its next ramp from
  a dropdown showing every ramp the wrong way round. Shipping since
  v0.23.0. GREP THE CONSTRUCTOR AS WELL AS THE UPDATER, and ask what
  rebuilds the widget.

- **WHEN A FIX IS WRITTEN INTO TWO PATHS IN ONE COMMIT, DIFF THE TWO
  HUNKS AGAINST EACH OTHER**, not each against its own neighbourhood.
  2026-08-17: `_add_output_layers` retires an undrawable pin and THEN
  stamps, saying at that line why ("the last moment before the value
  is stamped"); `_restyle_only` stamped and then retired. Both calls
  were born in one commit and the order was reversed on one side, so
  the twin's own explanation sat fifteen hundred lines from the path
  that got it wrong. The user was told the bound "has been
  recalculated" while the retired number went onto the layer anyway,
  so reopening the project restored a pin the row showed and the map
  ignored.
  A SECOND RULE FROM THE SAME BLOCK: **one dedup set must not gate
  two different things.** `field in said` was filled by whether a
  LEGEND NOTICE had fired for a column and it also gated the PIN
  RETIREMENT, which is per element -- so an element's dead pin was
  retired or kept according to what an earlier element had happened
  to trigger. Same act, opposite answers, decided by something no
  user can see.

- **A GUARD THAT RUNS BEFORE A RE-READ MUST BE ASKED WITH RE-READ
  VALUES TOO.** The rule that everything the colour editor writes is
  re-read at the landing was complete and still lost a user's work:
  `_retire_an_undrawable_pin` was handed the LAUNCH SNAPSHOT, so pins
  the editor had accepted against the live class count were retired
  as the run landed -- the stamp removed so a reopen could not
  recover them, and the sentence blaming the user's data. The same
  guard also judged a COPIED ladder against the receiving column,
  which is a carve-out `make_graduated_renderer` has carried since
  copying arrived: a copy is a claim about the ladder, not about what
  these values support.

- **A GUARD THAT ASKS ABOUT ONE THING MUST NOT STAND IN FRONT OF AN
  EXIT THAT IS ABOUT ANOTHER.** Three defects in one day, 2026-08-17,
  all this shape, and each cost a user their work rather than a crash.
  A COLOUR comparison at the head of `_graduated_layer_edited` stood in
  front of every `embed_style` exit, so a break retyped in QGIS reached
  the map, the project and the .qgz and never the GeoPackage a
  colleague opens -- since 2026-08-10, and invisible because the map
  was right. A "nothing nameable moved" test stood in front of the
  same. And the in-flight gate in `_on_layer_style_edited` stood in
  front of the TABLE learning that an element had begun deferring, so
  the landing read that as the user taking the element back and
  re-seeded it: a style pasted 250 ms into a run was destroyed, while
  the same paste a second either side survived.
  THE HABIT: at every early `return`, `continue` or `break`, name what
  the guard is FOR and then read what lies below it. Where the two are
  about different things, the exit belongs above the guard or the guard
  needs narrowing. This is the twin of the entry above it -- inserting
  a step BEFORE a handler can turn its opening guard from a
  fall-through into a return, which is how one commit disabled another
  five hours later without touching a line of it.
  ALL THREE WERE FOUND BY HUNTS AND NONE BY THE SUITE, on a build that
  had passed 481 tests, the gallery, the colourspace comparison and
  both CI jobs. A gate measures whether known behaviour still holds.

- **A REPRODUCTION CAN STOP REPRODUCING BECAUSE A NEIGHBOURING RULE
  CHANGED, AND THE DEFECT IS NOT DEAD -- ITS DOOR HAS MOVED.**
  2026-08-18, writing the guard for `_restyle_only`. Its committed
  probe reached pin retirement by moving the Classes spinner, and that
  route had been REFUSED hours earlier when a class count stopped
  being allowed to destroy a pin. Run as it stood, the probe now shows
  nothing, and the obvious reading -- "this cannot happen any more" --
  would have left two defects unguarded.
  What still reached the code was a record holding bounds the data
  cannot support, which is what a reopened project or a copied ladder
  hands over. So the guard stages the RECORD rather than the control.
  ASK WHICH DOOR THE PROBE USED AND WHETHER THAT DOOR IS STILL OPEN.
  Where it has been closed, the question is which other doors reach
  the same room, not whether the room still exists. A probe is
  evidence about one route; it was never evidence about the whole of
  a behaviour.

- **CLEARING IS RIGHT WHEN THE USER LET SOMETHING GO, AND WRONG WHEN
  THE PLUGIN MERELY STOPPED DECIDING.** (2026-08-18, three defects in
  the deferral family.) `_stamp_category_colours` clears both stamped
  records when there is nothing to record, which stops a layer
  carrying stale choices and is correct. `_assignments` reports a
  DEFERRING row with its picks and pins as None -- indistinguishable
  at that site from a user who cleared everything -- so restyling an
  element in QGIS erased its pinned bounds and hand-picked colours
  from the saved project while the open window still showed them.
  The same boundary was got wrong in the other direction twice more:
  the landing took the OLD layer's opacity for a deferring element
  when the Opacity cell stays live throughout, and
  `_restyle_no_data_layer` repainted a deferring element's paired
  layer when the landing carries that renderer across. Deferral means
  the plugin stops deciding an element's SYMBOLOGY. It does not mean
  the plugin stops deciding anything, and every rule about where that
  line falls has now been wrong at least once.
  THE TWO PATHS NEED DIFFERENT REPAIRS, and that is the part that
  generalises: on a RESTYLE the layer survives, so the records are
  left alone; on a RE-TILE the element gets a NEW layer, and leaving a
  new layer alone means the records are never written at all, so they
  must be CARRIED. Fixing one mends one route and the probe goes on
  failing on the other.

- **A GATE THAT CHECKS HALF OF WHAT IT NAMES IS WORSE THAN NO GATE**,
  because the other half is then believed to be checked. 2026-08-18:
  `sync_release_content.check_vendor_claims` promises in its own
  docstring that "prose claims about the vendored library match the
  recorded stamp", and did `stamp.split()[0]` -- the VERSION alone.
  The stamp is written "0.0.7.89 (bf1bbbf)" precisely because upstream
  does not always bump the version when the code moves, which is what
  MAINTAINING.md tells a re-vendorer, so the half that exists FOR that
  reason was the half nothing compared. Two documents named a
  superseded commit for eight days past a green gate.
  This is the sibling of "a rule that asserts its own enforcement must
  BE enforced". When you write a checker, enumerate what its own
  sentence promises and check each clause; and guard the gate itself,
  as `test_the_documents_numbers_match_the_code` now does by planting
  a wrong commit and requiring the checker to object.

- **WHEN A FIX WIDENS A CALL SO IT STOPS IGNORING X AND Y, ENUMERATE
  EVERY KEY OF THE RECORD THE CALLER COULD HAVE READ.** 2026-08-17 and
  18: `_table_id_colours` built each element's preview colour from the
  ramp NAME, and was wrong SIX TIMES -- a deferring element's layer,
  the Ramp Display Range, the row's Reverse, hand-picked class and
  category colours, a column with nothing to classify, and a constant
  column that the renderer colours from the middle of the window.
  Two were reported, a third was found by reading the line beside
  them, and three more arrived afterwards from hunts. Each repair
  added another condition to the same `elif`.
  A HUNT NAMES WHAT IT MEASURED; IT IS NOT A CENSUS. Three of the six
  colour keys `_assignments` carries were still unread after the
  commit that was supposed to settle it. The rule that finally closed
  the family was to stop enumerating: the preview READS WHAT THE MAP
  DRAWS, and falls back to the row's records only before there is a
  map. When one expression has been wrong three times, the question is
  not which condition is missing but whether it should be asking the
  question at all.

- **THE PLUGIN'S TABLE FOLLOWS THE LAYER'S RENDERER, AND THE SCOPE OF
  THAT IS THE WHOLE OF ITS SAFETY.** (Maintainer's ruling, 2026-08-17,
  on a field report against rc5: breaks retyped in QGIS's Symbology
  panel, then a style pasted across four element layers, reached the
  plugin not at all -- the rows went on describing THE MAP THE PLUGIN
  LAST DREW while QGIS drew something else, and the next Generate
  destroyed the lot.)
  It was ONE fault rather than three, and the tester established that
  themselves by setting the affected rows to a numeric style and
  repeating the paste. `_element_is_deferring` asks only whether a
  renderer is of a KIND the chooser can NAME, so deferring -- the only
  route by which a QGIS-side change reached the table -- opens only for
  renderers the plugin cannot express. A nameable renderer replaced by
  another nameable one was silently dropped.
  The ruling, chosen between following, deferring on any outside edit,
  and turning dock edits into pins: the row FOLLOWS the layer wherever
  the plugin can name what the layer holds, and defers only where it
  cannot. Pins could not have carried it -- the tester's element
  disagreed on the class COUNT and the RAMP as well as the breaks, and
  a pin names a bound. `_row_follows_the_renderer` reads the field, the
  style, the class count and the ramp back into the row BEFORE the
  colour handlers run, since each of those returns early when the row
  and the layer disagree.
  **A MECHANISM THAT MAKES A ROW DESCRIBE A LAYER IS SAFE ONLY WHERE
  THE ROW CAN REPRODUCE THAT LAYER**, and that is the part worth
  carrying past this feature. Run unscoped, the follow took a SINGLE
  SYMBOL somebody had mixed in the dock and made the row say "Single
  colour" -- which changes the assignment, which re-seeds the element
  on the next Generate, which paints the plugin's own colour over
  theirs. A hand-set #0b1e2d came back #3c8bc2. A field, a scheme, a
  class count and a named ramp are reproducible; an arbitrary fill is
  not, and describing it throws it away while looking like agreement.
  Single symbols keep the older and correct rule: hand styling survives
  unless the element's assignment changed.
  TWO SMALLER TRAPS, both found by the FULL suite and neither by a
  subset of eighteen tests aimed straight at this machinery. A widget
  written with signals blocked is not a row that CHANGED: `_refresh_table`
  restores a mode only when `style_touched` is set, so the followed
  style reverted at the first spacing change. And a row that moves with
  no signal must have its signature re-recorded, or the next restyle
  compares the layer against a row it has never seen and re-seeds the
  renderer it just followed.
  Guarded by `test_a_row_follows_a_style_pasted_onto_its_layer_in_qgis`,
  which drives the paste AND a Generate, and by three catalogue entries.

- **WHEN A FIX THREADS A "WHO FIRED THIS" ARGUMENT THROUGH A FAMILY OF
  HANDLERS, GREP THE CALLS THEY MAKE TO EACH OTHER.** 2026-08-17, and
  found by two independent hunts within an hour of each other, not by
  the suite. Giving an Unclassed end two pin controls meant every
  handler had to learn which control fired, so `source` was threaded
  through three signatures and every call site updated -- except one
  handler calling ANOTHER handler, `self._bound_edited(which)` inside
  `_bound_moved`. That call was an UNCHANGED CONTEXT LINE in the diff
  and therefore invisible in review, and it was on the branch taken
  only when the end is ALREADY pinned. The fallback then picked the
  first registered control, which is the strip, so the Pin column's
  box took the first number typed and silently discarded every one
  after it while the strip went on working.
  Two habits follow. The call sites you must check are not only the
  ones the SIGNALS reach: a family of handlers calls itself, and those
  calls do not appear in a search for the signal. And a fallback for
  "nobody said which" is exactly where a missing argument hides, since
  it turns a bug into a plausible answer -- prefer failing loudly to
  guessing when the caller should have known.
- **AN UNCLASSED END IS NAMED BY TWO CONTROLS, AND THEY MUST AGREE.**
  (Maintainer's instruction, 2026-08-17, reversing a decision of the
  same week.) Unclassed used to get no Pin column -- fifty faded
  slivers are a preview, and pinning row 0 of fifty is a strange way
  to say "the ramp starts at 10" -- so a clamp strip above the table
  said it better. It does say it better, and it was still reported as
  "pins do not work on unclassed". The reason is worth keeping,
  because it generalises past pins: A USER LEARNS A CONTROL IN ONE
  PLACE AND LOOKS FOR IT THERE. Meeting fifty faded rows and no Pin
  column, they conclude the feature is absent rather than moved. So
  the row now carries BOTH, and the strip's better wording is a
  second way in rather than the only one.
  THE COST IS A CLASSIC OF THIS CODEBASE: one piece of state, two
  descriptions. `_pin_widgets` maps each end to a LIST of (pin, box)
  pairs and `_register_pin` wires every one, so the handlers know
  which control fired; `_sync_pin_controls` then moves the others,
  with signals blocked, or setting a control right would fire the
  handler that set it right. Before this the registry held ONE pair
  per end, so a second builder would have left the first control
  wired, clickable, and applying the other's number.
  Guarded by `test_an_unclassed_row_pins_from_either_control`, which
  drives BOTH ways round and asserts the table's printed bounds and
  the pin's own PIXELS change, and by
  `test_two_pin_controls_agree_across_a_run_landing`, which pins
  mid-run because that is the moment this editor's state has been
  destroyed before. Three catalogue entries, the two sync calls
  anchored separately.
- **ONE HATCHING NOW, AND THE OTHER WAS WITHDRAWN.** Thin 45-degree
  diagonals say "no pin can go here" in the PIN COLUMN, and that is
  the only place they are drawn. The ramp swatch used the same mark
  for "no tile wears this class" until 2026-08-17, when the
  maintainer ruled it out: users are not used to it, so it confuses
  rather than helps. The emptiness is reported in words instead, by
  `empty_classes_message`, on the count `unworn_classes` measures.
  THAT SENTENCE WAS FALSE FOR A DAY and is the reason this one is
  precise: the removal named `few_values_message` as carrying the
  whole job, which fires on a column having fewer distinct values
  than classes -- neither necessary nor sufficient for a class going
  unworn, disagreeing in four cases of six -- and it deleted
  `unworn_classes`'s only caller in the same commit. The maintainer
  ruled on 2026-08-17 that the signal was meant to stay, so
  `dialog._classes_nothing_wears` asks the element's own renderer and
  the notice is composed from what it measures. WHEN A REMOVAL IS
  JUSTIFIED BY "X NOW CARRIES THE WHOLE JOB", RUN X AGAINST EVERY
  CASE THE REMOVED THING COVERED.
  THAT REVERSES PART OF A RULING MADE THE DAY BEFORE, and the pair is
  worth keeping together because the two answer DIFFERENT QUESTIONS.
  On 2026-08-16 the question was whether two hatchings could be told
  apart from each other, and the answer was that they could -- one
  texture saying "nothing available here" covers both honestly, and a
  second texture would ask somebody to distinguish two patterns at
  twelve pixels. That reasoning was sound and is untouched. The 17th
  asked a different question: whether the mark is legible to somebody
  MEETING IT for the first time. It is not. A design can be
  self-consistent and still fail its first reader, and answering the
  second question does not require the first to have been wrong.
  THE AMBIGUITY THAT WAS REAL WAS ARITHMETIC, not vocabulary, and it
  is the lesson worth carrying past the feature: the swatch's
  diagonals were drawn UNCLIPPED, each stroke a full swatch-height
  long and starting a height before the stripe, so marking ONE class
  painted a 49px band around a stripe 12.8px wide. Measured on the
  shipped 64x18 swatch at five classes: hatching class 3 put 44
  pixels into class 2 against 58 into class 3. When a drawn signal
  reads as ambiguous, measure where its ink actually lands before
  redesigning what it means -- a vocabulary argument is the more
  interesting explanation and was the wrong one.
- **A tiles inset that swallows elements is refused in terms of the
  inset.** Insetting shrinks every tile by a fixed distance, so past
  some value the narrower elements disappear. Left to itself the
  library's overlay refuses the surviving slivers and the user meets
  "ValueError: You have passed make_valid=False along with 1978
  invalid input geometries"; when every element goes, the table
  empties and the variable guard fires instead, telling them to assign
  a variable to a design with nowhere to put one. Both are true of
  something and neither is about the control they just moved.
  `bridge.inset_collapse_message` names the inset, and `_generate`
  checks it BEFORE the variable guard. It is asked only when the inset
  is non-zero, so a collapse from another cause is never blamed on it;
  the comparison is safe to refuse a run on because declared n equals
  the distinct tile-id count for 247 of 247 catalogue designs with no
  inset (measured 2026-08-13).
- **The plugin follows the layer, and adapts where the answer is
  unambiguous.** QGIS is live and the dialog is not modal to it, so a
  user can delete features, simplify geometry in place, rename or
  retype a field, reassign a CRS or filter the layer while the plugin
  is pointed at it. Both signatures therefore carry a fingerprint of
  what the layer CONTAINS, and the dialog connects to the layer's own
  signals for edits a fingerprint cannot see (a value retyped, a
  vertex moved inside the bounding box). Where an edit makes a setting
  untrue AND there is exactly one sensible response, the dialog makes
  it and says so: an element whose column has gone RE-DEFAULTS to a
  surviving field AND GIVES UP THE STYLE SOMEBODY CHOSE FOR IT (losing
  a column costs an element its variable, not its place on the map --
  unassigned draws as flat fill, so a deletion in QGIS would quietly
  cost the map two of its four variables; and a scheme cut for one
  column says nothing about another, so a categorical one left standing
  on a numeric column draws a colour for every distinct value, which is
  ledger row 9 of 2026-08-20), a
  column added in QGIS is offered straight away, the spacing is
  re-derived when the CRS changes, and the region layer being removed
  is reported rather than silently emptying the chooser. What it does
  NOT do is treat a vanished column and a new one as a rename: that is
  a coin flip that would map data nobody asked for. `repaintRequested` is
  deliberately not listened to in general, because it fires on style
  changes and re-tiling on those is the cost the restyle fast path
  exists to avoid.
  **What neither mechanism sees is an edit made straight through the
  DATA PROVIDER, and that is a stated limit rather than a bug.**
  Measured 2026-08-13: rewriting every value through
  `dataProvider().changeAttributeValues` leaves the count, the extent,
  the field names and the CRS identical and fires no watched signal,
  so the tiles keep the old values and a full Generate changes
  nothing. Scripts and other plugins write this way routinely.
  Following it would mean polling the data or widening the fingerprint
  to something that costs a scan on every debounce tick, and the
  maintainer's decision was to document it instead; the docstring that
  used to claim the case was covered has been corrected. Anybody
  reversing that decision is choosing what the scan costs, not
  discovering a gap.
- **NULLs are kept out of class breaks, and that is a WORKAROUND with
  an expiry test.** QGIS's classifier counts a NULL as zero while its
  own `minimumValue()` excludes nulls, so QGIS disagrees with itself
  and the classifier wins: a column with gaps gets a spurious 0-0
  class and every break shifted toward zero, on a map that looks
  perfectly plausible. Measured identically on the memory provider and
  on a GeoPackage through OGR (QGIS 4.0.3, 2026-08-09), so it reaches
  real data. `make_graduated_renderer` corrects the INPUT rather than
  the output: it hides the nulls with a subset string, lets QGIS's own
  classifier run, and restores the layer. Reimplementing quantiles,
  equal intervals, Jenks and pretty breaks here would mean owning four
  algorithms and inventing new ways to disagree with the styling panel
  the user opens next. It is safe because the layer being filtered is
  the ELEMENT OUTPUT layer, which the plugin creates and owns — never
  the user's region layer — and a provider that refuses the subset
  falls through to the old behaviour, since wrong breaks beat no map.
  The corrected breaks survive a project save and reload, a GeoPackage
  reopened elsewhere, and the plugin's own restyle path; they revert
  only if the user presses **Classify** in QGIS's Graduated panel,
  which recomputes with nulls counted as zero. That is why the notice
  exists as well as the fix. **When QGIS fixes this**,
  `test_qgis_still_counts_nulls_as_zero` fails — it asserts the bug,
  deliberately, going straight to QGIS. Treat that failure as good
  news: delete the marked block in `make_graduated_renderer` and the
  canary, keep `missing_values_message`, and do NOT relax the
  assertion to make the suite green. (User instruction, 2026-08-09.)
- **The dependency consent dialogue states what can be checked.**
  `deps.py` downloads wheels from PyPI where QGIS lacks the scientific
  stack or carries a version below the floor — most often Linux, where
  QGIS uses the system Python, but the trigger is "missing OR too old"
  and can fire anywhere. That is the most intrusive thing this plugin
  does and the thing a QGIS plugin repository reviewer will examine
  hardest, so the dialogue (`plugin.dependency_consent_box`) names the
  packages, the source (PyPI), the exact destination folder, what is
  NOT touched, how to undo it, and what declining costs — and the
  buttons say what they do, with the SAFE one as the default so a
  stray Return cannot start a download. It is built as its own
  function rather than inline so it can be tested and photographed
  without owning a machine that happens to be missing a package;
  `test_the_dependency_consent_says_what_it_will_do` asserts each
  promise. If you change the wording, keep every one of those
  elements: they are what make it consent rather than a prompt.
  (User instruction, 2026-08-09.)
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

On "three-way" comparison (library vs web app vs plugin): the PDF's
reference column IS both of the first two at once, because MapWeaver
pins this same library version and draws through this same
TiledMap.render call inside pyodide — a browser screenshot would
re-photograph the identical code path with UI chrome added, so no
separate column exists. CONDITION TO WATCH, AND THE GAP HAS WIDENED:
the vendor is 0.0.7.89 at upstream commit bf1bbbf since 2026-08-25,
while the app still pins 0.0.7.59 — thirty versions rather than the
two this paragraph used to describe. The earlier reading, kept
because it is what the claim rested on: relative to .59 the vendor
at 0.0.7.61 differed by MIT licence headers, comment blocks, the
STRtree tileable filter (the optimisation this project offered
upstream, output-identical over twenty configurations when offered),
and a one-word bugfix in get_regularised_prototiles_background
(prototile ids on the regularised-prototile frame — a path the plugin
does not draw through), none of which changes what TiledMap.render
paints for the gallery's cases.
WHAT THE BUMP MEANS FOR THE CLAIM, said plainly rather than assumed:
six of the twelve library modules changed behaviourally at 0.0.7.89,
so the sentence "the reference column speaks for both" is now a
claim about a thirty-version gap and is only as good as the
colourspace comparison that re-measures it every run. That gate is
against the VENDOR, which is the plugin's own reference and the right
one; what it no longer speaks for with any confidence is the WEB APP.
This is exactly the condition the paragraph named — a bump while the
app lags — so a live browser capture is the honest third column from
here, and the decision to add one is the maintainer's. Recorded
2026-08-26.

- **A TEST FOR A PROMISE IS A MATRIX, NOT A CASE, and this is the
  DEFAULT rather than a technique to reach for occasionally.** Where
  the thing under test is a family of behaviours -- "edit the
  symbology in QGIS and the plugin follows", "a number you type is the
  number used" -- enumerate the atomic actions as ROUTES, cross them
  with synthetic data SHAPES chosen for failure modes rather than
  realism, and add an axis for what happens NEXT, because arrival and
  survival are different promises. Run a spine of every route against
  two canonical shapes every time, sample the rest under a printed
  seed, keep the full crossing behind a flag, and report every failing
  cell rather than the first. Measured 2026-08-18: 36 cells, 58
  seconds, and 17 of them fail when the fix is removed. The guard this
  replaced changed field, class count and ramp TOGETHER and had passed
  for weeks while a retyped boundary reached nothing -- ONE COMPOUND
  CHANGE IS NOT COVERAGE OF MANY SMALL ONES. Written up at length in
  docs/TESTING.md; apply it when improving an existing test too, since
  a test that already passes is where a hole hides best.

- **A GUARD MUST NOT REPAIR WHAT IT MEASURES, NOR RUN WHERE THERE IS
  NOTHING TO SEE.** (2026-08-19, three in one sitting, every one
  caught by the catalogue rather than by reading.) A visual guard hid
  and re-showed the mark to get a contrast -- calling the very methods
  the mutation removed, so it mended the product and then measured the
  mended product. Its replacement ran after the surrounding test had
  given every bound back, so nothing was marked and the loop never
  executed. A third handed edge pairs to the icon builder, proving the
  DRAWING while the dialog asked for two ends of four. Drive the
  product, read the pixels, COUNT WHAT YOU LOOKED AT, and state the
  check as its inverse -- "name anything that draws nothing" rather
  than "the mark is drawn". Full shapes in docs/TESTING.md.
- **WHEN A REPRODUCTION WILL NOT REPRODUCE, MEASURE THE SESSION THAT
  IS BROKEN.** (2026-08-19.) Six reproductions of a reported defect
  were built here, against the reporter's own data, and every one
  worked. Two dumps behind `WEAVINGSPACE_ADOPT_DUMP` and one run by
  the person holding the failure answered it in a minute: the dump was
  EMPTY, so the plugin had never been told, because that session's
  Generate had failed and `styleChanged` is connected only when a run
  lands or a group is adopted. A reproduction that will not reproduce
  is a signal about the DIFFERENCE between two sessions; budget the
  instrument early rather than a seventh attempt. An empty dump is
  evidence only where the dump is known to fire -- here, because other
  lines from the same function appeared in the same terminal.
- **A MATRIX CATCHES ONLY WHAT ITS CELLS MAY COMPLAIN ABOUT.**
  (2026-08-19.) The symbology matrix crosses twelve routes with nine
  shapes, three aftermaths and three schemes, and it caught NONE of
  three defects that landed in one evening -- an affordance drawn
  under the widget that covers it, a ceiling with no edge to mark, a
  bound of 1e9 elided out of its box. The routes were all exercised.
  Every complaint a cell could make was about a RECORD, a layer, a
  stamp or a notice; nothing in it ever looked at a picture or asked
  whether a number could be typed back.
  So before adding cells, ask what a cell is ALLOWED TO NOTICE: an
  axis that crosses a question the verdict cannot ask is an axis that
  cannot fail. Every cell now also asks that what the record holds is
  MARKED where a user looks and DISPLAYED in full and typable back.
  Full reasoning in docs/TESTING.md.

- **WHEN A CHANGE BREAKS A TEST, BISECT BY DISABLING RATHER THAN BY
  REASONING, after ONE hypothesis fails.** Insert an early `return` at
  successive points through the new code; the first point that turns
  PASS into FAIL contains the culprit. To decide which FILE is at
  fault, swap the whole file for its last-good version. On 2026-08-18
  this bracketed a defect to a single statement after four plausible
  theories had each been implemented and each been wrong, and the
  culprit's own log then named what it wrote -- the plugin's own
  ladder, recorded as though a user had typed it.

- **TWO OF THIS PROJECT'S INSTRUMENTS LIE, and both cost hours on
  2026-08-18.** `print()` inside a Qt signal handler goes nowhere under
  a test that captures output, so an empty dump read as proof the code
  never ran when it ran every time -- AN EMPTY LOG IS NOT EVIDENCE OF
  ABSENCE. And a plain `python3` heredoc run AFTER sourcing the QGIS
  environment dies at bootstrap and applies NO edit, so the run that
  follows measures the unmodified file and reports fiction; use
  `env -u PYTHONHOME -u PYTHONPATH python3`, the same hazard that
  kills `release.py` and `mutation_check.py`. Related: an anchor
  matching TWICE applies nothing while the run still reports a result,
  and the categorized and graduated handlers share identical text.
  Assert the match count and parse the file after every edit.

- **A WATCHER MAY ONLY ADOPT WHAT A PERSON LEFT BEHIND.** Anything
  that reads state off a layer and records it must run at REST: not
  while the dialog is writing renderers (`_applying_style`), not while
  a run is in flight (`_task`), and not while a landing is still being
  reconciled (`_preserved_this_run`). During any of those the record
  and the layer are transiently out of step, and what sits on the
  layer is nobody's decision. Adoption recorded the plugin's own
  five-class ladder as a user's, pinned it, and a twelve-class
  reclassification made in the dock became five. Also: a getter-shaped
  name is not a getter -- `_current_graduated_classes` BUILDS a
  renderer -- and work added to a signal handler must not precede the
  work already there, since an exception in a Qt slot is swallowed and
  takes the rest of the handler with it.

- **CLASS BOUNDS: THE RECORD HOLDS FOUR ENDS, AND TWO OF THEM ARE
  WEAKER THAN THE OTHER TWO.** (Maintainer's decisions, 2026-08-19.)
  `pinned` gained `floor` and `ceiling` beside `low`, `high` and
  `breaks`. `low` and `high` name BOUNDARIES BETWEEN CLASSES -- the
  first class's upper and the last class's lower -- so each takes its
  class out of the pool the scheme cuts from, can cross its
  neighbour, and can be refused. `floor` and `ceiling` name the EDGES:
  no boundary moves, no class leaves the pool, and nothing can be
  refused for crossing. Keep them in separate registries. Putting an
  edge into `_pins_in_force` would corrupt the `k` arithmetic, which
  must stay 0, 1 or 2 -- one set gating two different things, which
  this project has paid for before.
  THE WHITELIST IN `_adopt_dock_bounds`'s RESTORE PATH IS THE
  RECORD'S REAL DEFINITION. A key missing from it is dropped in
  SILENCE on every reopen, so the record is right all session and
  wrong the moment the project comes back. When you widen the record,
  widen that line in the same commit.
  A LADDER RETYPED IN QGIS KEEPS THE ENDS A PERSON TYPED. The 0.24.3
  ledger argued the low end was harmless because the same areas fall
  in the same class; that is true about colour and FALSE ABOUT WHAT
  THE LEGEND SAYS, and it only ever considered the bottom. What is
  dropped is the pair of edges when NOTHING survives them -- a ladder
  retyped far from the data would otherwise adopt a ceiling that
  excludes every value and leave the element with no classes at all.

- **A LIMIT MAY EXCLUDE, AND WHAT IT EXCLUDES IS DRAWN.** A floor or
  ceiling inside the data puts values out of bounds, and those areas
  become a FOURTH KIND OF ABSENCE beside no data and the two
  infinities: drawn, in a colour a user picks, with their own legend
  line. Left to a graduated renderer an excluded value gets no symbol,
  which on a map of areas is a HOLE -- indistinguishable from a tiling
  gap and from a missing value, three facts wearing one appearance.
  THREE OF THE FOUR KINDS ARE FACTS ABOUT THE DATA AND THE FOURTH IS A
  CHOICE, which decides precedence: a value's own nature is asked
  first, so an infinity excluded by a ceiling is reported as an
  infinity. `bridge.absence_kind` is the one owner of that question;
  it replaced three copies in two files that each enumerated the keys
  by hand.
  A LIMIT IS A GEOMETRY CHANGE, because excluding values moves tiles
  onto the paired layer and `_restyle_only` can neither make nor
  unmake one. So the split PREDICATE is what learns about limits, not
  the split: it feeds the geometry signature, and answering no there
  sends a limit change down the restyle path where the exclusion is
  recorded, believed and never drawn.

- **NO PIN COLUMN: A HEAVY OUTLINE ON THE BOX SAYS THE NUMBER IS
  YOURS.** (Maintainer's instruction, 2026-08-19.) One convention for
  all four ends rather than two, no table width, and nobody reading a
  glyph at twelve pixels. A middle class simply has no spin box, which
  says "you cannot set this" the way every other table does. A cross
  inside the box gives a bound back, and typing the computed number
  back does the same -- compared at the box's DISPLAYED precision, or
  an edge of 3.0999999 can never be retyped and the second route is
  decorative. Painted, not stylesheeted: a stylesheet border REPLACES
  the platform frame rather than adding to it. Measured 47 dark pixels
  unmarked against 533 marked; a mark nobody can see is a flag.
  UNCLASSED NAMES ITS FLOOR AND CEILING, NOT TWO PINS, which reverses
  part of the ruling of 2026-08-17 deliberately. That ruling gave
  Unclassed a Pin column because a user met fifty faded rows and
  reported the feature missing -- right when a pin was the only
  control for an end. The original objection, that pinning row 0 of
  fifty is a strange way to say "the ramp starts at 10", is answered
  by a control that says exactly that. The strip's label had been
  wrong since it was written: "Ramp starts at" drove the LOW PIN,
  which on fifty steps is the ramp's start plus a fiftieth of the span.

- **PRESERVE, DO NOT REPAINT.** (Maintainer's ruling, 2026-08-19.)
  With live update off the map is deliberately NOT refreshed on its
  own -- the table and the map may disagree until the user asks -- and
  what must hold is that the change is NOT LOST. When a dock edit must
  survive a landing, the answer is to stop the landing CLOBBERING it,
  by making the row follow the renderer so nothing re-seeds; it is
  never to repaint from a timer, which is the plugin acting unasked.
  Reconcile through the door the landing already uses rather than a
  second one invented for the case.

- **A GUARD MEASURES THE GROUND, NOT THE BOX ROUND IT.** (2026-08-19,
  ledger row 23, and it cost a colleague their map rather than a
  little time.) The size guard estimated tiles from a CIRCLE enclosing
  the region's bounding rectangle, while the library tiles that circle
  and then CLIPS to the polygons. New Zealand is two long islands in a
  rectangle that is mostly sea -- 11.8% of that circle -- so the guard
  said 585,765 tiles where 70,659 were drawn and REFUSED a design the
  library renders in five seconds.
  FOUR MODELS WERE MEASURED against what is really drawn, because a
  region is not one shape: adjacent cells cut from a raster share
  edges needing no allowance, separated cells each carry their own.
  The bounding-box edge came out 1.20x on the first and 0.98x -- UNDER
  -- on the second; each polygon's own perimeter 6.25x and 2.38x; the
  DISSOLVED boundary 1.28x and 1.68x. Only the last is generous on
  both, and a guard that under-counts waves through a run that then
  takes the machine.
  THE GENERAL FORM, which reaches past this guard: a perimeter summed
  per row is a property of HOW THE DATA WAS CUT INTO ROWS rather than
  of the ground it covers, and so is a bounding box. When an estimate
  stands on the shape of the input, ask whether it is standing on the
  geometry or on the table.
  AND ITS FIXTURES MUST BE SPARSE. Every region fixture in this suite
  is a dense square, where the circle and the ground differ only by
  pi/2 and any honest threshold accepts both -- which is why nothing
  here ever caught it. The guard asserts its fixture IS sparse before
  comparing anything, and computes what the old arithmetic would have
  said, so its threshold cannot be one the current code merely happens
  to meet.

- **A CACHE OF ONE IS NO CACHE WHEN THERE ARE TWENTY-THREE OF
  ANYTHING.** (2026-08-19, ledger row 4.) `_classification_values`
  REPLACED its cache dict on every miss, on the sound reasoning that a
  stale fingerprint's values must never sit there being wrong -- and
  replacing it threw away every OTHER column's entry at the same time.
  With one element that is free; with twenty-three elements on
  twenty-three columns the hit rate is ZERO, so one keystroke rescanned
  3,011 features twenty-three times. Measured on the reporter's own
  data: 119,352 calls per tick at 0.24.2 against 1,041,176 at HEAD,
  172 ms of CPU against 3,543, one Generate at 2.5s against 62.7.
  THE SUITE COULD NOT SEE IT: four elements over thirty-six features
  against twenty-three over three thousand is a factor of 481 with no
  change of shape, so the cost was real all along and never large
  enough to show. WHEN A FIX IS ABOUT STALENESS, ASK WHAT ELSE IT
  DISCARDS -- the safety property here needed only that entries whose
  fingerprint has moved go, not that everything go.
  AND ITS GUARD COUNTS CALLS ACROSS SEVERAL COLUMNS. A one-column test
  reads zero warm scans whatever the code does, since there is nothing
  to evict it, and would pass with the cache deleted outright.

- **A COPY REPRODUCES THE WHOLE CLASSIFICATION, AND THE RECORD GREW
  UNDER IT.** (2026-08-19, ledger rows 21 and 22.) `_copy_classification`
  built its record from breaks and pin flags and never read `floor` or
  `ceiling`, then wrote that record WHOLESALE -- so a copy left the
  source's range behind AND destroyed the target's. The case that
  justified out-of-data bounds at all was giving one pair of limits to
  several variables, and the control built for it could not do it.
  WHEN A RECORD GAINS A KEY, GREP EVERY SITE THAT ENUMERATES ITS KEYS.
  `_adopt_dock_bounds`'s restore whitelist was widened the same day and
  is documented as "the record's real definition"; the copy was not,
  and nothing pointed at it.
  AND THE FIX MOVED THE COPY ONTO A PATH THAT REFUSES IT: a limit is a
  GEOMETRY change, so `_restyle_only` declines the element -- and the
  restyle is what writes the stamp. A copy of breaks alone came back
  stamped and the identical copy carrying a range stamped nothing, so
  it reached the map and would have died at the next reopen. WHEN A FIX
  MOVES A CHANGE FROM ONE PATH ONTO ANOTHER, ASK WHAT THE OLD PATH WAS
  DOING FOR IT BESIDES THE OBVIOUS.

- **A GITHUB RELEASE BODY PRESERVES SINGLE NEWLINES, so NEVER hard-wrap
  one.** Release notes written at the usual 72 columns arrive as
  literal line breaks, and on a phone that means a sentence broken
  mid-clause -- "nothing is promoted," ending a line, `main` starting
  the next -- because the renderer never gets to wrap to the viewport.
  Write each paragraph as ONE long line and let the reader's width
  decide; keep hard newlines only for headings and list items, which
  need them. Seen on rc9, 2026-08-18, and fixed by unwrapping.
  This is the SAME fault as the changelog's, from the other side: that
  entry is hard-wrapped because QGIS's plugin manager shows metadata
  text AS IT STANDS and would run a long line off the panel. TWO
  SURFACES, OPPOSITE RULES, and the deciding question is always
  whether the renderer reflows. Check a release page NARROW -- a phone
  or a half-width window -- before believing it reads, exactly as the
  changelog is checked in both renderers.

- **A CHECK THAT CAN ONLY CONFIRM IS NOT A CHECK.** Unwrapping the rc9
  release notes, the script reported "unwrapped: 14 blocks" and I read
  that as success -- but the number needed was how many were still
  WRONG, and nine of eleven paragraphs had been skipped because they
  open with bold and my list-item guard matched `*`. A count of things
  PROCESSED says nothing about things FIXED. State the check as its
  inverse -- show me anything still broken -- so a clean run is an
  assertion rather than an absence. The same fault appears in tests as
  a shape-blind expectation, and in probes as an empty log read as
  proof.

- **A LIST ITEM NEEDS THE SPACE.** `- `, `* `, `+ ` and `1. ` are
  bullets; `**bold` is a paragraph. Guarding on the bare character
  silently skipped most of a document.

- **A GLOB IS HOW A LOG'S DATE GETS SKIPPED.** (2026-08-19, and the
  THIRD time this project has read a stale log as current.) The rule
  already written is that every excerpt from a log must be dated
  before it is read. What defeats it in practice is
  `grep reports/stage-logs/*.log`, which sweeps up every run there has
  ever been: two failures from a stage log three days old were
  reported as the current candidate's, and the candidate was in fact
  clean. The run's own logs were sitting beside them under a
  timestamped name.
  SO NAME THE RUN, NEVER THE DIRECTORY. This project already keys
  every log to its run for exactly this reason -- a timestamp and a
  pid -- and that discipline is worth nothing if the reader globs.
  When you go looking for a running job's output, build the pattern
  from the job you started rather than from the folder it writes to,
  and if you cannot say which run a line came from, you have not read
  it yet.

- **WHEN TWO THINGS SHOULD DRAW THE SAME MAP, COMPARE WHAT THEY DREW,
  NOT WHAT THEY LOOK LIKE.** (2026-08-19, comparing the plugin against
  the library on the maintainer's own data.) The two paint with
  different colours by construction -- a two-colour matplotlib
  colormap against seeded QGIS renderers -- so pixels would report a
  difference that means nothing. Per-element TILE COUNTS mean
  everything: 70,659 tiles both sides and the same number on every one
  of twenty-three elements is the same map, and no oracle was needed
  to say so.
  AND THE COMPARISON ANSWERED A DIFFERENT QUESTION THAN IT WAS ASKED.
  The question was how long each takes; the answer was that the plugin
  would not draw it at all, because the size guard refused. A
  performance question is worth asking of real data for that reason
  alone: it drives the whole path at a size no fixture reaches, and
  what it finds need not be a time.

- **A NAME THAT CARRIES A NUMBER IS SORTED AS TEXT, AND rc10 COMES
  BEFORE rc2.** (2026-08-19, ledger row 25.) `release.py` named the
  candidate it had just built by sorting `dist/weavingspace_qgis-*rc*.zip`
  and taking the last entry. On the tenth candidate of 0.24.3 -- the
  first two-digit candidate this project has ever built -- the zip went
  out as `0.24.3rc10` while its dossier and receipt were written as
  `rc9`, ON TOP OF the published rc9's own. One name over two trees,
  which is precisely the harm `next_candidate` exists to prevent,
  arriving from the end nobody was watching. The same glob spanned
  every VERSION, so a 0.25.0 candidate would have been named from a
  leftover 0.24.3 one.
  THE DEEPER FAULT IS THAT THE FACT HAD TWO DERIVATIONS. `next_candidate`
  parses the number and takes `max() + 1`, and was right the whole
  time; naming re-derived the same fact in another file by another
  route. A rule with two implementations has two behaviours the day
  one of them is wrong, which this file already says about generated
  documents and about `shipped_files()`. It is `build.latest_candidate`
  now, beside its sibling and sharing what counts as an artefact.
  AND A FIXTURE MUST REACH THE CASE: nine candidates satisfy both
  derivations, so the guard stages TEN and computes what the text sort
  would have said, requiring it to disagree.
- **VERIFY AGAINST WHAT SHIPPED, NOT WHAT YOU WROTE.** The second pass
  at those notes was checked by reading the LIVE page back and
  measuring every line, not by inspecting the local file. Where a
  publish step exists between the file and the reader, the reader's
  copy is the only one that counts.

- **A DEPENDENCY'S CHEAP ANSWER IS A CACHED ANSWER, AND A GUARD BUILT
  ON ONE IS HONEST ONLY AFTER SOMETHING INVALIDATES IT.** (2026-08-20,
  ledger row 32.) `compat.layer_data_is_available` asked a layer
  whether it was valid and its provider whether it was valid, and its
  own Returns block promised that caught "a layer whose file has been
  deleted ... including the case where the layer itself still claims
  to be valid". Measured on QGIS 4.0.3, moving a GeoPackage out from
  under an open layer: isValid True, provider True, featureCount 36 --
  and `getFeatures()` yielding NOTHING. Only after an explicit
  `reload()` does the provider admit False and the count fall to -2,
  and nothing reloads a layer a user has not touched. So the guard
  passed, the run went on, and the refusal that reached the user was
  about their DATA when the fact was that their FILE had moved.
  THE HABIT: when a guard asks a dependency whether something is still
  true, ask what would have to HAPPEN for that answer to be refreshed.
  Where the answer is "somebody must act", the cheap question measures
  the last time somebody acted, not the world. The honest question
  here costs one feature: ask for it, and see whether it comes back.
  This is the third appearance of "a gate that checks half of what it
  names", and the first where the other half was a staleness rather
  than a missing clause.
- **AND ITS TEST HAD BEEN EXERCISING THE HONEST PATH ALL ALONG.** The
  sibling guard called `reload()` in its own setup before asking
  anything -- which is the one act that makes QGIS tell the truth, and
  the one act a user never performs. A test whose SETUP repairs the
  condition it is about passes forever; this project already knows
  that shape from a visual guard that called `show()` on the thing the
  mutation had hidden, and it arrives here wearing a data provider.
  Read a test's arrangement for calls that would refresh, reset or
  reopen the very thing under test.
- **A FIX APPLIED TO A TWIN THAT DOES NOT HAVE THE FAULT IS DEAD CODE
  THAT READS AS PROTECTION.** (2026-08-20, ledger row 34.) The rule
  that a colour equal to the renderer's SOURCE SYMBOL is QGIS's clone
  rather than somebody's decision is right on the graduated path, and
  was written onto the categorized path in the same edit out of the
  usual and correct suspicion about pairs. Measured,
  `make_categorized_renderer` sets no source symbol at all, so that
  guard could never fire: it would have sat in the catalogue as a
  permanent survivor and in the source as a claim that a door was
  watched. It was deleted and the measurement left at the site with
  what would reopen it. THE PAIRS RULE CUTS BOTH WAYS -- check whether
  the twin HAS the fault before giving it the fix, and when it does
  not, say so where the next person will look for the symmetry.
- **A GUARD THAT LANDS WITHOUT A TEST OF ITS OWN LOOKS GUARDED,
  BECAUSE THE NEIGHBOUR IT RE-ANCHORED STILL PASSES.** The edge rule
  for pinned bounds went in on 2026-08-19, correctly re-anchoring the
  catalogue entry standing on the line it changed -- and that entry
  proves ends are adopted AT ALL, not that they are kept off the
  ladder's edge. The commit therefore read as fixed-and-guarded while
  the new rule had nothing measuring it. When an edit re-anchors an
  entry, ask what that entry actually asserts: re-anchoring keeps an
  OLD claim true and never states the new one.

- **`styleChanged` FIRES ONLY ON `setRenderer`; AN EDIT MADE ON THE
  LIVE RENDERER IS SILENT, AND ITS `triggerRepaint()` IS THE ONLY
  TRACE.** (2026-08-20, ledger row 28, reported four times before it
  was measured.) The styling panel installs a whole renderer for some
  acts (adding a class, Classify, a paste) and edits the held renderer
  in place for others (a plain colour change) -- so the plugin
  followed the first kind and was structurally deaf to the second,
  while MAINTAINING.md asserted the opposite in as many words. The
  dock then calls `triggerRepaint()`, because the canvas has no other
  way to learn, and THAT emits `repaintRequested`. Element layers now
  listen to it, debounced, with three gates that each failed a test
  before it existed: our own repaints (`_applying_style`), the echo of
  a heard `setRenderer` edit (it fires both signals, and handling it
  twice adopts the displaced ladder), and a row that has moved (the
  layer is merely BEHIND a pending restyle, and reconciling then
  adopts our own outgoing style as somebody's picks). The REGION
  layer's `repaintRequested` stays unconnected -- that rule is about
  re-tiling and is untouched. The general lesson: when a dependency's
  signal is documented here as covering a family of edits, ask which
  member of the family was actually measured; this one had been
  measured only for the member that happens to announce itself.
- **`ranges()` AND `categories()` HAND BACK COPIES, so editing one is
  a NO-OP on the layer -- and a probe that does it measures nothing.**
  (2026-08-20, twice in one hour: a signal probe's row and a guard's
  first draft.) `ranges[0].symbol().setColor(...)` recoloured a
  temporary; the renderer never changed; "no signal fired" was
  reported about an edit that had not happened. Stage in-place edits
  through the renderer's own `updateRangeSymbol`/`updateCategorySymbol`
  and ASSERT the edit reached the layer before asserting anything
  else. This is the fixture-that-cannot-move trap inside an
  instrument, and it is the sibling of the freed-temporary segfault
  this file already records about the same getters.

- **ABSENT IS NOT MOVED: when a NEW guard reads an OLD record, ask
  which paths leave that record deliberately empty.** (2026-08-20,
  found by three hunts independently.) A guard added the day before
  skipped an element whose row signature differed from
  `_last_signatures` -- right in itself, since between a control
  change and the restyle that answers it the layer is merely BEHIND.
  It asked with `!= self._last_signatures.get(tile_id)`, and
  `_adopt_existing_group` leaves that record EMPTY on purpose, saying
  so in its own docstring: the dialog cannot know which assignments
  produced layers it has only just met. So `.get()` answered None for
  every adopted element, None never equals a real signature, and the
  new route was shut in every REOPENED project -- the commonest
  journey there is, and the one whose docstring promises hand styling
  survives. A missing entry is the absence of evidence; reading it as
  evidence of change inverts the guard exactly where the record is
  emptiest. Ask of any `.get()` in a guard what an absent key MEANS,
  and write the answer at the line.
- **A GUARD COMPUTED AS A DELTA IS ARMED FOR ONE INVOCATION.**
  (2026-08-20, ledger row 2, and it defeated a guard written the
  previous day.) `count_moved` was measured across
  `_row_follows_the_renderer` INSIDE ONE HANDLER CALL, to stop a class
  added in QGIS having its shuffled colours adopted. It is true on the
  signal carrying the change and FALSE on every signal after it,
  because the follow has already brought the row up to date and there
  is no delta left to see. Measured: a hand-picked colour survived the
  class being added and, one bare repaint later, the record held four
  colours with the user's displaced a class and three of the plugin's
  own recorded as theirs, stamped into the project. THREE routes reach
  the second pass -- a later repaint, a re-tile landing, and the
  window-activation backstop added in the same commit as the guard.
  So: when you add a guard that reads state the caller has just
  changed, ENUMERATE EVERY ROUTE TO A SECOND PASS in that same commit,
  and prefer a question the state can answer at any moment over one
  that asks "did this change just now".
  THE OBVIOUS DURABLE REPLACEMENT WAS TRIED AND WITHDRAWN the same
  hour, and its shape is worth not repeating: comparing the ladder's
  BOUNDS against what the row would draw is correct in the reported
  case and over-reaches everywhere else, because once a class has been
  added in the dock the ladder differs from ours PERMANENTLY and no
  hand-pick would ever be adopted for that element again.
  **SETTLED BY `/grill-me` THE SAME DAY, and the first thing the
  grilling did was reject the question.** The ledger asked whose
  LADDER it is, offering "theirs, so the element defers" against
  "ours, so store it". Those are not peers: deferral is INFERRED
  afresh from `bridge.expressible_style`, never stored, on a
  maintainer's condition of 2026-08-15, and a six-class graduated
  ladder is perfectly expressible -- so nothing about a
  reclassification makes an element defer, and taking that limb would
  have overturned that rule AND the follow ruling of 2026-08-17.
  The live question was narrower: not whose ladder, but which COLOURS
  on it the plugin put there. The maintainer chose the narrow reading.
  **THE PLUGIN NOW STORES THE LADDER IT PAINTED**, in
  `dialog._painted_ladders`, and asks of each class whether the colour
  is one of its own -- a question the state can answer at ANY moment,
  which is what a delta could not do. Written wherever the plugin
  paints and at group adoption; NEVER on a follow, which runs before
  attribution and would record the dock's ladder as ours. Not stamped:
  a reopened project re-derives its baseline from the layer, which
  keeps the record out of the restore whitelist. An ABSENT entry means
  "never seen" and DECLINES, which is neither "ours" nor "theirs".
  WHAT MAKES IT ANSWERABLE IS A MEASUREMENT: on QGIS 4.0.3, `addClass`
  inserts a degenerate `(0.0, 0.0)` class at index 0 wearing the
  source symbol's grey, and EVERY SURVIVING CLASS KEEPS ITS BOUNDS BIT
  FOR BIT. So a colour can be matched back to the class it was painted
  on exactly, with no tolerance.
- **A LADDER MAY HOLD SEVERAL CLASSES WITH IDENTICAL BOUNDS, so a
  lookup by bounds must not stop at the first match.** (2026-08-20,
  and it was a defect in the fix above, caught within the hour.) A
  constant column, a tied column and `{1, 5, 9}` at k=5 all produce
  degenerate ranges, and `addClass` then inserts another `(0.0, 0.0)`
  class -- which collides with any fixture whose first real class is
  also degenerate. Returning on the first match compared the plugin's
  own colour against the placeholder grey sharing its bounds, called
  it changed, and adopted it. FOUR PASSING TESTS DID NOT SEE IT; what
  found it was driving the product and PRINTING THE RECORD at each
  stage, which is this project's own prescription and was still not
  the first thing tried. Guarded by
  `a-ladder-may-hold-two-classes-at-one-bound`.
- **WHEN CI TIMINGS MOVE, COMPARE THE SUSPECT ON A MACHINE YOU
  CONTROL BEFORE BELIEVING THE ORDERING.** (2026-08-20.) Windows ran
  89 minutes against a 53-59 minute history; the largest grower was
  2.6x; and it was the one test that most exercises the path a fix
  landed the same day had opened. Every piece fitted. Measured
  locally, sequentially, in clean worktrees: 151s before against 147s
  after. The fix costs nothing. The tell was in the CI data all along
  -- several tests SHRANK in the same run, one by 57 seconds, and a
  uniform slowdown does not do that.
  TWO HABITS. Six minutes of local measurement beat a conclusion that
  would have sent somebody optimising a path that is not slow, or
  narrowing a repaint route doing exactly what it should. And RECORD
  THE HYPOTHESIS BEFORE THE VERDICT LANDS: written afterwards it would
  have been fitted to whatever number turned up, and writing it first
  is what made it falsifiable. The Windows job's own variance is worth
  knowing if a ceiling is ever sized against it: 53 to 89 minutes on
  near-identical trees, a 68% spread, far wider than the Linux legs.
- **WHEN A GUARD STARTS ANSWERING DIFFERENTLY, FOLLOW ITS RETURN VALUE
  INTO EVERY TUPLE IT IS A MEMBER OF, not only into its callers.**
  (2026-08-20, a regression from the previous day's own fix.)
  `compat.layer_data_is_available` was corrected to answer False for a
  moved file. That answer is also a term in `_layer_fingerprint`,
  which is a term in `_geometry_signature` and a CACHE KEY -- so a
  moved file made the fingerprint read `("unavailable",)`,
  `_restyle_only` bailed, and `_apply_style_change` discarded the
  refusal in silence: a colour picked after the source vanished was
  recorded, never painted and never mentioned, where before it
  repainted correctly because a restyle needs nothing from the region
  layer. The hunt that found it reported that the questions its brief
  actually asked -- the cost, the empty layer -- were both clean, and
  the defect was two hops away. A guard's callers are the easy half;
  the hard half is everywhere its ANSWER travels as data.
  **AND THE FINGERPRINT WAS ONLY HALF OF IT.** Fixed, the ramp still
  did not reach the map, because `_maybe_live_generate` asks the same
  availability question at its sixth gate and returned in front of its
  own repaint exit -- the guard-about-one-thing-in-front-of-an-exit-
  about-another shape, for the fourth time in this file. It refuses
  the TILING now and tries `_restyle_only()` first; nothing may fall
  through it, since `_extent_in_working_units` sits a few lines below
  and a dead extent segfaults QGIS. `_generate`'s own check needed
  NOTHING -- its fast path is already above it -- so the twin was
  measured and left alone rather than given a symmetrical repair, and
  a catalogue entry reverses its order so the asymmetry is guarded
  rather than remembered.
- **A REPAIR AIMED AT AN ACT MUST BE RE-AIMED AT THE ACT'S ABSENCE.**
  (2026-08-27, two hunts from different directions in one afternoon.)
  On 2026-08-26 the stale-table drop was taught to take a saved STYLE
  with the table it removes, which mends every case where something is
  deleted. Both of the day's file-residue defects are cases where
  NOTHING IS DELETED: once because the record of what to delete lives
  on a WINDOW rather than in the file, so a dialog that never adopted
  the output GeoPackage knows of nothing to drop; once because two
  column names sanitise to ONE table, so the table is replaced and
  nothing ever looks stale -- while `layer_styles` is keyed by the
  style's NAME, and the row written for the abandoned column sits
  beside the new one carrying its whole QML.
  So ask of any repair that fires on an act: what happens on the
  journey where that act never occurs? The drop was right and its
  coverage was the question nobody put.

- **A GUARD WHOSE CONDITION IS RIGHT CAN STILL BE AIMED AT NOTHING.**
  (2026-08-27.) The queued restamp's new guard reads `_fieldless_build`,
  and that flag was measured TRUE at exactly the moment the defect
  fires. Its first test passed anyway with the guard mutated away,
  because the journey it drove -- a recolour to a SINGLE SYMBOL --
  never reaches the adoption that queues the restamp at all. A single
  symbol is deliberately not followed (the scope of the follow ruling
  of 2026-08-17), so the test was aimed at a door the act never opens.
  The catalogue found it; reading did not. The repair was to drive the
  recolour the way this suite's other adoption tests drive it: clone
  the renderer the layer already has, move ONE class's colour, install
  the clone.
  AND THE PREMISE CHECK LIED FIRST. The rewritten test then failed on
  its own premise, which read `layer.renderer().ranges()[0].symbol()`
  -- the freed-temporary pattern this file already records twice. A
  premise that cannot be trusted is worse than none, because its
  failure is read as the product's.

- **AN INSTRUMENT THAT HOLDS A FILE CHANGES WHAT IT MEASURES, AND
  BYTES REMEMBER PAGES NOBODY REFERENCES.** (2026-08-27, twice inside
  one test.) A guard read a GeoPackage through a `QgsVectorLayer` it
  left alive, and the open handle made the NEXT run fail at the sqlite
  level: zero tables, read as the product's fault. Rewritten to read
  the file's raw BYTES, it then found an abandoned colour sitting in
  sqlite's freelist -- present with the dataset open, absent once
  everything had let go, with the style row itself gone in both
  readings.
  THE FILE A COLLEAGUE RECEIVES IS THE FILE AFTER IT IS CLOSED, and
  that is the only moment a byte-level claim about it means anything.
  Read through OGR and release at once, or clear the project first.

- **RETIREMENT IS A FACT ABOUT THE OBJECT, NOT AN ABSENCE IN A
  REGISTRY.** (2026-08-27.) Every long-lived handler here is gated by
  "am I the dialog in charge", and that record was only ever cleared
  by SUCCESSION -- so a plugin the user DISABLED left it naming a
  dialog they had disposed of, which went on adopting dock edits,
  rewriting the project's group record and speaking into QGIS's
  message bar about controls in a window there was no longer any way
  to open, until QGIS restarted.
  THE OBVIOUS LEVER IS THE WRONG ONE AND WAS MEASURED SO. The gate
  reads "if there IS a live dialog and it is not me, drop", so None
  means "nobody has said" and clearing the record makes EVERY dialog
  believe it is in charge rather than none: the sentence the fix had
  just been written for came straight back. `_dialog_is_gone` answers
  the retirement now, because it is the question every handler puts
  first. And closing the WINDOW deliberately does not retire, since
  `open_dialog` reuses the object -- a closed window is a hidden one
  somebody may bring back with its map intact.

- **A WIDGET THAT RETAINS LAYER OBJECTS MUST BE REBUILT WHEN LAYERS
  ARE REMOVED, AND A DEAD POINTER'S ADDRESS GETS REUSED.**
  (2026-08-27, found by the saving branch's first full suite.) The
  region chooser keeps the plugin's own output out of its list
  through `setExceptedLayerList`, which stores the layer OBJECTS.
  That list was rebuilt at construction, at a project read, at a
  resume and after a landing -- and never when layers were REMOVED.
  So after File > New the combo went on excluding a set of destroyed
  pointers, and a layer allocated where a dead one had been was
  excluded for being somebody else: the chooser offers NOTHING while
  the project plainly holds a polygon layer, and Generate refuses for
  want of a region with nothing on screen to explain it.
  THE SWEEP IS THE TRANSFERABLE PART. Ask which widgets are handed
  layer OBJECTS that they keep: here `setExceptedLayerList` is the
  only one, since `setLayer` names a current layer whose lifetime the
  combo follows and `setFilters` takes flags. One member, swept
  rather than assumed.
  AND IT IS GUARDED BY THE SUITE RATHER THAN BY AN ENTRY, deliberately
  and in writing at the fix: the harm needs an address to be reused,
  so the test that caught it fails in a full run and passes when run
  alone. An entry would report SURVIVED most times it was judged,
  which is a false negative and worse than no entry -- the one shape
  this catalogue must not carry.

- **A LAYER BUILT ON ANOTHER LAYER'S SOURCE IS THAT LAYER TO ANYTHING
  THAT LOOKS UP BY SOURCE.** (2026-08-27.) The map-unit outlines layer
  is built on the REGION'S OWN SOURCE, deliberately, since nothing is
  copied; and it carries `weavingspace_output`, which is what keeps it
  out of the region chooser. Each fact is right alone and they collide
  in a walk that filters by neither: recovery took whichever layer
  QGIS's map yielded first with a matching source, and `setLayer` on a
  layer the combo EXCLUDES leaves the chooser empty -- then returned,
  in front of its own two fallbacks. A resume reported success beside
  a blank chooser, every element's variable lost, and a Generate that
  launched nothing and said nothing.
  WHEN YOU RESOLVE AN IDENTIFIER TO AN OBJECT, ASK WHO ELSE ANSWERS TO
  IT, and whether the answer is one the caller is ALLOWED to use. Then
  check that the assignment took: a `setLayer` that did not land must
  fall through rather than return as though it had.

- **ENUMERATE THE PRODUCERS OF A SECOND CLAIMANT, NOT JUST THE ONE YOU
  BUILT.** (2026-08-27.) The paired-layer rule of 2026-08-16 says a
  paired artefact inherits the identity property of the thing it is
  paired with, so every lookup keyed on that property gains a second
  answer. Its fix enumerated the plugin's own twin and stopped there.
  QGIS's own DUPLICATE LAYER copies custom properties, so a copy of an
  output layer claims its element too -- and adoption, keeping the
  LAST claimant in panel order, adopted a copy sitting below the
  original. The next Generate replaced the copy and left the user's
  real layer standing over the new map, under an identical name, never
  updated again, with nothing said.
  NOTHING IS DELETED ON A GUESS: the two layers are indistinguishable,
  a GeoPackage-backed copy shares even its source, and keeping a copy
  of yesterday's map is a reasonable thing to do. The first in panel
  order wins and the plugin SAYS which one it will replace.

- **A DANGLING REFERENCE IS NOT A DISAGREEMENT, WHICH IS WHY NOTHING
  COMPLAINS.** (2026-08-27.) An element may take its classes from
  another element's LAYER, and the choice is stored as
  `layer:<layer id>` -- while a re-tile gives every element a new
  layer with a new id. So one Generate after the choice, the token
  named an object that no longer existed: the donor read as an
  UNREADABLE class source, the follower kept the colours it already
  had under the keep-the-map promise, and two elements went on drawing
  one column in two sets of colours for good. Every mechanism behaved
  exactly as designed.
  References are repointed as the layers are replaced -- in the record
  AND in the combo, since `_assignments` reads the WIDGET and healing
  the record alone was measured to last until the next rebuild. The
  donor's CONTENT is stamped too, as a QML class source has been since
  2026-08-13; a reference stamped by name alone can never notice the
  thing it points at moving.
  WHAT IS STILL OPEN, and is a ruling rather than a defect: a donor
  that MOVES is followed one run late, because the landing reads its
  template from the donor's outgoing layer while the donor is being
  re-seeded in the same pass. Curing it decides the ORDER elements are
  seeded in, and two elements may take their classes from each other
  -- driven 2026-08-27, and it settles rather than churning.

- **BREAK EVERY ROUTE AT ONCE, OR THE CATALOGUE MEASURES THE OTHER
  ONE.** (2026-08-27, three times in a day.) A fix written as two
  guards -- skip our own output AND check the chooser took -- survives
  having either one mutated, because the other still sends the walk to
  its fallbacks. An older entry that had caught for weeks began to
  SURVIVE the moment a new writer covered the same ground. And an
  entry aimed at the recorder half of a two-site fix passed with that
  half deleted outright, because the arm deciding the carry made the
  recorder's case unreachable.
  A SURVIVOR IS INFORMATION, NOT A NUISANCE: it says the behaviour is
  held redundantly, or that the entry is aimed at a case nothing can
  reach. Both are worth knowing, and the answer is the same -- mutate
  the SHARED thing, or say at the entry why it now needs both halves.

- **A RULING THAT GIVES A FACT A SECOND WRITER PUTS AN OLDER ENTRY TO
  SLEEP, AND NOBODY IS TOLD.** (2026-08-28, deciding all thirty-four
  survivors of the branch's full sweep; the round is written up in
  `docs/process/catalogue-triage-2026-08-28.md`.) Thirty-three of the
  thirty-four predated v0.24.3, and almost none was a weak test. The
  fortnight's rulings each added a store or a mechanism -- the group's
  working state, `_painted_ladders` attribution, a gate behind a
  timer, a follow that brings a row up to a layer's count before the
  colour handlers run -- and every one left an older single-site entry
  unable to fail. The catalogue's count went on describing 559
  guarded behaviours while a version's worth of them had quietly
  become second lines of defence.
  SO WHEN A RULING ADDS A WRITER, RE-JUDGE THE ENTRIES OVER THE OLD
  ONE, in the same round. This file already says to enumerate every
  store that holds a fact when a repair gives one store a new write;
  this is that rule pointed at the CATALOGUE rather than at the code.
  THREE SHAPES RECUR and each makes a single-site entry permanently
  red: one limb of a FALLBACK CHAIN (`group = lookup() or
  findGroup(name)`, `lost = pending or watched`), one of two READINGS
  of the same fact a few lines apart (a combo's default seeded, then
  re-selected from the record twenty-two lines below), and one TERM of
  a tuple whose siblings answer the same question (the run signature
  carries a layer's identity and its fingerprint). The repair is to
  anchor the whole decision, which cannot be split again by the next
  alternative somebody adds.

- **AN INERT MUTATION AND A REDUNDANTLY HELD ONE BOTH REPORT SURVIVED,
  AND THEY NEED OPPOSITE REPAIRS.** (Same day.) An entry excluding
  modes from the no-data split was mutated by adding a literal to a
  list read from `mode` -- while deferral lives in `mode_raw`, so the
  mutation matched nothing and changed nothing. That reads exactly
  like a test too weak to notice. THE DISCRIMINATOR IS TO KILL THE
  SITE OUTRIGHT: if the test then fails, the site is live and the
  mutation was inert; if it still passes, something else is answering.
  Four attempts went into that entry before the question was put that
  way round.

- **A TREATMENT WHOSE CONTROL ALSO FAILS HAS MEASURED NOTHING**, and
  it nearly cost twelve wrong retirements twice in one day. Breaking
  every entry on a test "to see whether the axis is live" includes the
  sibling entry that already CATCHES, so the failure is guaranteed
  before the survivors are touched; pairing a survivor with a catching
  sibling has the same defect. Run the control -- the co-broken thing
  alone -- and read the treatment only when the control passes. Every
  redundancy verdict of that round carries its control.

- **COVERAGE SAYS A LINE RAN, NOT THAT ITS BRANCH WAS TAKEN.** Sixteen
  tests execute `if len(expected) != len(actual):` and every one
  evaluates it false, so removing the guard changes nothing for them;
  exactly one test ever takes the branch. A per-test coverage record
  answers "could this test possibly notice" and not "does this test
  exercise the case", and for a GUARD the two questions differ.

- **THE PER-TEST COVERAGE RECORD IS KEYED BY A TEST'S DISPLAY NAME,
  NOT ITS FUNCTION NAME**, which is what `check()` registers it under.
  `mutate_auto.display_to_function` is the mapping; borrow it rather
  than writing a second one. Looking a catalogue entry's `test=` up in
  the record directly misses every time, and the answer -- "not in the
  record" for all thirty-four -- reads exactly like a finding about
  the entries.

- **RANKING CANDIDATES CANNOT CHANGE A VERDICT; UNDER A CAP IT DECIDES
  WHAT WAS ASKED.** Sampling "the eight most focused" tests covering a
  line by the SIZE of their coverage record put region outlines and
  legend labels to a mutation about layer removal, and "0 of 8 notice"
  read as evidence. Rank by word overlap with the mutated line first,
  as `rank_covering_tests` does, always include the entry's own test,
  and PRINT what the cap dropped.
  AND A NEGATIVE FROM A CAPPED SEARCH IS NEVER EVIDENCE OF ABSENCE. A
  test that fails under the mutation genuinely notices; silence only
  says the answer was not in the sample.

- **A UNIFORM VERDICT IS ALMOST ALWAYS THE INSTRUMENT.** Three of this
  project's own tools were found wrong in one day by that tell alone:
  thirty-four "not in the record", then "0 of 8" everywhere, then
  DIFFERS everywhere because a comparison counted `region_7c23c`
  against `region_bb6b7` as a changed decision. Before believing a
  result that came back the same for every input, run the instrument
  against a case whose answer you already know.

- **`mutation_check` APPLIES EXACTLY ONE REPLACEMENT, BY DESIGN**, so
  a fact held at two DISTANT sites cannot be guarded by any single
  entry. The run signature's identity and fingerprint terms are 47
  lines apart, and an anchor spanning both breaks on any edit between
  them. Where the sites are adjacent, widen the anchor; where they are
  not, the honest record is a retirement with the measurement and the
  redundancy written at the test. Whether the tool should take a LIST
  of replacements is a real question about campaign machinery and is
  recorded in ROADMAP.md rather than decided in passing.

- **A REPAIR'S OWN REPAIR NEEDS THE SAME SUSPICION, AND THE FIRST ONE
  CAN BE WORSE THAN THE DEFECT.** (2026-08-28, the moved-data notice,
  wrong three ways in one evening and every one of them mine.) It kept
  ONE reading in a session-wide slot and compared it against whichever
  dataset the region chooser held, so returning to an earlier map
  through the group chooser told somebody their file disagreed with
  itself when nothing had been touched. THE FIRST FIX FOR THAT TRADED A
  FALSE ALARM FOR A MISSED ONE: carrying the layer id ALONGSIDE one
  reading silenced the notice on a map whose data really had moved. The
  readings are keyed BY DATASET now, which is the shape this file
  already states twice -- a fact about a subject belongs keyed by that
  subject -- arriving for the third time in two days.
  AND A NOTICE CANNOT BE TESTED BY SILENCE. The quiet arm passes just
  as well when the sentence has been deleted outright, so the guard
  asserts BOTH answers in one test: quiet where nothing moved, speaking
  where it did. Where a rule has two answers, a reader meeting one
  takes it for the whole rule.
- **A GUARD WHOSE PRECONDITION IS A LOSSY DIGEST IS ONLY AS GOOD AS
  WHAT THE DIGEST OMITS.** (Same day.) The same notice read
  `_layer_fingerprint` -- the feature count, the extent, the field
  names, the CRS -- none of which an ordinary VALUE EDIT moves. So the
  case it was written for, and quoted in its own commit message
  ({7,17,27,37} beside a map drawn from {0,1,2,3}), was the one case it
  could not report: a keystroke unrelated to whether the data had moved
  decided whether anybody was told. It carries a per-dataset edit count
  beside the fingerprint now. THE COUNTERFACTUAL PAIR IS THE TECHNIQUE
  WORTH COPYING -- two journeys corrupting the data identically,
  differing by one keystroke, so the guard's own machinery supplies the
  positive control.
- **OWNERSHIP IS NOT A NAME PREFIX, AND AN ELEMENT ID IS A LETTER EVERY
  MAP SHARES.** (Same day.) The stale-table drop scoped itself to "this
  map's own elements" and decided that by `tiles_<id>`, so saving into
  a GeoPackage holding a colleague's map DELETED their `tiles_a_*` and
  `tiles_b_*` while leaving their `tiles_zz_*` and their own tables --
  one line after a question promising to "leave the rest of the file
  alone", and against the method's own Returns block. It is asked of
  the FILE now, through one helper both the question and the drop
  share.
  AND THE ANSWER IS TAKEN BEFORE THE WRITE. Ownership is partly "have
  we saved here in this session", which the very press about to happen
  makes true of any file at all -- so asking afterwards answers yes for
  a stranger's GeoPackage. When a guard reads state the act is about to
  change, take the reading first and pass it in.
- **A GATE THAT READS RAW SOURCE TEXT CAN BE MOVED BY A COMMENT.**
  (Same day.) `test_pypi_provisioning_is_reached_only_through_consent`
  holds a hard rule by indexing three markers in `plugin.py` and
  requiring their ORDER. A note added above the consent call, mentioning
  `provision_from_pypi` to explain what it fetches, put the download's
  index before the dialogue's and failed the gate with the code
  perfectly correct. It tokenizes and strips comments now.
  THE FAMILY IS THE ROADMAP GATE'S, from the other side: there a
  sentence QUOTING the phrase could satisfy the gate; here a sentence
  mentioning a marker could break it. When a gate reads prose for a
  decision, decide what counts as prose.
- **A CONSENT DIALOGUE THAT ENUMERATES MUST BE DIFFED AGAINST WHAT THE
  CODE ASKS FOR.** (Same day, and it is a HARD RULE breached since the
  initial commit.) The box named the missing scientific packages;
  `provision_from_pypi` also fetches the pure-python support
  distributions the main ones import at runtime -- its own docstring
  says so -- so somebody who read "Missing or too old: geopandas" and
  approved had SEVEN distributions fetched from pypi.org, against
  metadata.txt's promise that the plugin "shows exactly what it would
  fetch and asks first". The box is handed the full list now, computed
  by the same question the loop asks.
  ITS REGISTERED TEST COULD NOT SEE IT, which is the transferable half:
  the test asserted the box names what it was HANDED. A dialogue's
  promise is about what the software DOES, so the comparison has to
  reach the code's own requests -- recorded by stubbing the seam where
  the decision is taken, not the network.
- **AND AN UNBOUND RETURN IS A FAILURE NOBODY HEARS.** The same loop
  called `_fetch_dist` and discarded its `(fetched, reason)`, so a
  support package lost to a dropped connection left `LAST_FAILURES`
  empty, provisioning reporting success, and the user meeting "No
  module named 'dateutil'" with nothing to say why. The reason
  machinery written for exactly that case was bypassed by one unbound
  call, three lines from the loop that binds it correctly.

- **A SITE NAMED BY READING IS A HYPOTHESIS, AND IT READS EXACTLY LIKE
  ONE SOMEBODY PROVED.** (2026-08-20, the same defect.) Where that
  refusal lived was worked out from the source, written into the
  handover, and copied from there into ROADMAP.md, MAINTAINING.md and
  docs/TESTING.md in one documentation round -- all four naming
  `_generate`, which a debounced tick never reaches, and all four
  calling the refusal silent when it says a sentence that is false.
  One dump line at each of that path's ten gates answered it in a
  single run. So: when you write down WHERE a defect is, say how you
  know; and where a path can refuse for ten reasons, make each one
  NAME ITSELF -- live update pausing without saying why has cost this
  project two diagnoses now.

- **AND ITS OVERRIDE MUST BE KEYED BY THE SAME SUBJECT.** (Same
  evening, in the repair for the entry below.) Keying the FACT by file
  and then guarding it with a session-wide "has anybody touched the
  box" bool answers a different question: one tick anywhere in a
  session made every self-contained file opened afterwards strippable.
  The question is "has this person spoken SINCE THIS FILE was opened",
  which is a count against a count. When you key something by subject,
  read every condition that governs it and key those too.
- **A GUARD THAT REBUILDS A LAYER FROM ITS SOURCE STRING LOSES
  EVERYTHING THE USER SET ON THE LAYER.** (2026-08-28.) A CRS somebody
  assigned -- the ordinary repair for a shapefile with no `.prj` --
  lives on the layer, never in `source()`. The outlines overlay was
  rebuilt from the string, so it drew in the FILE's system while the
  tiles drew in the assigned one, fourteen thousand kilometres away
  and zero ink pixels over the map. GREP FOR `QgsVectorLayer(
  something.source()`, not for the word CRS: subset strings, scale
  ranges, custom properties and names are all in the same position.
- **A COUNT QUOTED TO A PERSON MUST BE ASKED OF THE GEOMETRY, NOT OF
  TWO TOTALS.** (2026-08-28.) The icon-mode sentence subtracted a TILE
  count from an AREA count to say which elements were short. A unit's
  tile sits off the centre it was placed at, so the difference is not
  the number of uncovered areas in either direction: it named b, c and
  d while a was missing from three areas and b from none. Where a
  project has already corrected a count twice -- this one had -- check
  the third against the map rather than against the code, because the
  test guarding it was written from the same arithmetic.
- **A PER-FILE FACT MUST NOT LIVE ON A SESSION-WIDE CONTROL.**
  (2026-08-28, round ten, and it was a repair of mine that put it
  there.) "Include the source data" is one checkbox and the answer it
  stands for belongs to a FILE: whether THAT GeoPackage carries a copy
  of the region. Reading the box alone meant a recipient who had never
  touched it stripped the copy a sender had deliberately included --
  the drop was written for the act of unticking and fired for the
  act's ABSENCE. Setting the box from the file's record cured that and
  bought two new harms in one line: the recipient's own next Save
  copied THEIR private region out unasked, and a person who had ticked
  the box on purpose had it silently unticked by opening any file
  without a copy in it.
  THE SHAPE IS GENERAL. When a control's value is asked about a
  subject the control does not name -- a file, a layer, an element --
  keep the fact keyed by that subject and let the control mean what it
  has always meant, which is a standing preference. Then say which one
  wins: here the file's record wins while the person has not spoken,
  and a deliberate untick still means exactly what it says.
- **A DISPLAY RULE IS ONLY DISPLAY-ONLY IF NOTHING RE-READS THE
  DISPLAY.** (2026-08-28.) `MarkableSpinBox.textFromValue` abbreviates
  a large number to "1.02M" and its docstring says it touches neither
  the stored value nor the validator. True of everything this project
  does and FALSE OF QT, which calls `interpret()` on Return and reads
  the display back through `valueFromText`. So pressing Return in a
  bound box, typing nothing, replaced a floor of 1,015,001 with
  1,020,000, moved every class break and moved four more of fifty
  areas out of range -- shipped in v0.24.3, on any column above about
  1e5 or below about 1e-4.
  This file already says a display rule belongs in `textFromValue`
  because `decimals` governs storage as well as display. What it did
  not say is that the framework may complete the circle anyway. Ask of
  any formatting override: who else calls the reader?
- **A SUITE CAN HOLD A CONTROL AT A VALUE NO USER HOLDS.**
  (2026-08-28.) Every resume test in this suite unticks live update,
  which is ON by default -- so the whole family was driven at a
  setting nobody has, and pressing Load with the default re-tiled the
  opened map into memory a second later and emptied the saved file.
  The hunt that found it swept all four debounce windows first and
  ruled every one out; the hiding place was not a race but a default.
  ASK OF ANY TEST FAMILY WHICH CONTROL IT HOLDS CONSTANT, and whether
  a person holds it there.
- **A RECORD SEEDED BY ADOPTION IS A RECORD THAT ASSUMES A PROJECT.**
  (2026-08-28.) The stale-table drop took its candidates from the
  session's own record of what it had written, plus the tables of
  elements the map still has -- and a DROPPED element is in neither.
  Its docstring called that "the shrank-design case the session record
  covers", which holds only while there is a group to adopt: that
  record is seeded by adoption and cleared when a project is replaced.
  Close QGIS without saving the .qgz, reduce the design, save to the
  same file, and the dropped elements' tables, columns and VALUES stay
  in the file somebody sends on. The file's own record is asked now.
  The general question: when a rule leans on a record, ask what SEEDS
  that record and what a journey without the seeding act looks like.
- **AN INTERMITTENT FAILURE UNDER LOAD CAN BE THE SUITE INTERMITTENTLY
  REACHING A REAL DEFECT.** (2026-08-28.) A per-test coverage
  re-record failed one test of 645, in a shard running beside two
  others on a loaded machine. Everything about it said harness: the
  candidate's own suite had passed it an hour earlier, it passed alone
  plain, alone under the recorder's instrumentation twice, and nine
  times across three concurrent copies. One failure against fourteen
  clean runs is exactly what flakiness looks like, and this file
  already carries the rule that a test tuned in one harness is
  re-tuned by another.
  IT WAS A DEFECT, and the tell was in the log rather than in the
  odds: `_settle` waits on the EVENT -- no task, no live timer, no
  preview timer -- and reports a timeout in different words, so the
  dialog had genuinely finished and the orphans were still there. A
  failure that survives the thing settling is not a race the test lost.
  WHAT SETTLED IT WAS STAGING THE CONDITION RATHER THAN CHASING THE
  FREQUENCY. The suite's case presses Generate about 150 ms after
  putting a run in flight and hopes the run is still going; on this
  Mac it usually is not. A probe that checked `_task is not None` in
  the same breath as the press reproduced it FIRST TIME, on both arms,
  deterministically. Where a case depends on a window, do not measure
  how often you land in it -- close the window.
  AND THE HARM WAS OVERSTATED, MEASURED THE SAME DAY. A person cannot
  reach it: `generate_btn.setEnabled(False)` runs before the task
  starts, and the only two sites that re-enable it are `_finish_run`
  and the zombie recovery, which clears `_task` first. Driven at a
  fine spacing and read mid-flight -- `task=True`, button disabled, a
  real `click()` setting nothing, a direct `_generate()` setting
  `_press_pending` at once. So the state is produced by the SUITE and
  not by a user: `test_two_generates_with_different_families_keep_
  their_elements_apart`, the test that failed under load, calls
  `dlg._generate()` three times, as `test_race_double_generate` has
  since long before this.
  THE FIX STANDS AS DEFENCE IN DEPTH and the mechanism below is exact;
  what was wrong was the sentence around it, written in four documents
  and in a candidate's tester notes that told people to press a button
  the interface greys out for the whole run. This is this file's own
  rule about a site named by reading, arriving at a HARM instead: the
  mechanism was measured and the reachability was assumed, and only
  one of those was checked. ASK OF ANY DEFECT WHETHER THE JOURNEY THAT
  REACHES IT IS ONE A PERSON CAN DRIVE, and measure that as separately
  as you measure the mechanism.
  THE DEFECT ITSELF IS THIS FILE'S OWN SHAPE: one flag gating two
  different things. `_generate` queued a press on `_live_pending`,
  `_finish_run` honoured that by starting the LIVE timer, and
  `_maybe_live_generate` returns at its second gate whenever live
  update is off -- so with the box unticked a button press was
  remembered and then thrown away in silence, the map keeping the
  elements of the run in flight while the table asked for the new
  design. A deferred live tick and a deferred button press are not
  the same fact. Guarded by `test_a_generate_pressed_during_a_run_is_
  not_swallowed`, which drives BOTH arms because the live-on arm was
  correct throughout, and by the catalogue entry
  `a-queued-press-is-a-press-not-a-live-tick`.

- **A REPORT ABOUT A VERSION OR A BEHAVIOUR IS FIRST A QUESTION ABOUT
  WHICH BUILD IS INSTALLED.** (2026-08-29.) The maintainer reported
  that the title bar "no longer shows the rc version properly". The
  plugin was right at every step: `_plugin_version()` reads `version=`
  out of the INSTALLED `metadata.txt`, `build.py` substitutes the
  candidate label into the copy inside the archive, and the published
  `0.24.4rc5` zip genuinely carries `version=0.24.4rc5`. What was
  wrong was the copy on the machine -- of two QGIS profiles, `default`
  held the candidate (whole plugin written at the candidate's own
  build time) and `testing` held a plain `0.24.4` written wholesale
  an hour and a half later. The title bar was faithfully reporting a
  build that was not the candidate.
  ASK WHAT IS INSTALLED BEFORE READING ANY CODE. One loop over
  `build.installed_copies()` printing each profile's `version=` line
  and its mtime answers it in seconds, and it is the same rule as
  measuring the session that is broken rather than building a seventh
  reproduction -- arriving at an INSTALL rather than at a dump.
  AND TWO HYPOTHESES OF MINE WERE WRONG BEFORE THAT ONE, both caught
  by checking rather than by reasoning. `build.py` INSTALLS ONLY UNDER
  `--rc`: the install block sits inside `if args.rc:` and returns
  before the plain path, so the packaging check cannot have overwritten
  a profile, and the gate's own log confirmed it printed no `updated`
  line. The profiles are also not symlinks or hard links into the
  working tree.
  IT WAS IDENTIFIED ON 2026-08-30, by taking a reading BEFORE
  overwriting the evidence -- the maintainer had asked for the
  candidate to be put back, which would have destroyed it. The build
  in that profile was BYTE-IDENTICAL to the unversioned
  `dist/weavingspace_qgis.zip` across all 31 members, against exactly
  one differing member versus the rc5 zip. So an UNGATED artefact had
  been installed over a gated candidate, and the title bar had been
  reporting it faithfully ever since. Nothing in the tree installs an
  unversioned zip, so it was a hand-run of `install_into`.
  THE LESSON IS THE ORDER. A fix that overwrites the evidence is a
  diagnosis you will never make: the reading cost five minutes and
  turned an open ledger row into a closed one, and it turned the
  unversioned-artefact rule from a tidiness argument into a measured
  harm. When an instruction would destroy the state a question is
  about, take the measurement first and say that you did.
- **A CLAIM'S MECHANISM IS USUALLY RIGHT AND ITS HARM USUALLY IS NOT,
  AND THE DOOR IT NAMES IS WHEREVER THE HUNT WAS STANDING.**
  (2026-08-29, taking sixteen owed claims to the end.) This file
  already says a harm named by reading is a hypothesis. What a whole
  verification session adds is the RATE: of fourteen claims closed,
  three had their harm corrected and one its door widened, while the
  mechanism each named was exact.
  THE HARM IS USUALLY QUIETER AND LATER than the claim says. "The
  recipient's first Generate repaints the follower" was really "the
  follower keeps the colours it inherited, and stops following its
  donor from then on" -- nothing looks wrong at all until somebody
  moves the donor, which may be days later. A control arm on the
  LINK rather than on today's colours is what showed it.
  AND THE DOOR IS WORTH ONE EXTRA ARM. A claim reported at the Load
  door bit hardest on the reopened-plugin door, which the hunt had no
  reason to try and which the code's own docstring calls something
  users do constantly. One arm, and it doubled what the repair was
  worth.
  TWO OF THE FOURTEEN WERE CLOSED BY A FIX WRITTEN FOR ANOTHER
  CLAIM, both checked on the tree the hunt read rather than assumed
  -- and both still owed a GUARD at their own door, because a claim
  that has stopped reproducing is not a claim that is tested.

- **A CALLABLE THAT OUTLIVES ITS DIALOG MUST ASK BEFORE IT TOUCHES
  IT, AND A LAMBDA IS NOT A BOUND METHOD.** (2026-08-29, a
  reproducible SEGMENTATION FAULT.) Qt drops a connection to a bound
  METHOD when the receiving QObject dies. A LAMBDA is an ordinary
  Python object: Qt keeps it alive and goes on calling it, and
  reaching `self.anything` through a deleted sip wrapper crashes the
  process rather than raising -- so it happens BEFORE any handler's
  own retirement gate can run. `cleared` and `readProject` are PROJECT
  signals and reach every dialog a session has ever opened; an element
  layer outlives the dialog that made it.
  THREE SITES, ONE SHAPE, and each was written by somebody who knew
  the rule: a handler with no gate at all that queued
  `singleShot(0, lambda: setattr(self, ...))`; a closure that DID
  guard and wrote to `self` on the line above the guard; and two layer
  signals plus the project read connected to bare lambdas. The second
  is this file's own row 25 of 2026-08-27 met again -- A GUARD WHOSE
  WHOLE JOB IS BEING SAFE ON A DEAD OBJECT MAY NOT TOUCH THAT OBJECT
  BEFORE ASKING WHETHER IT IS DEAD.
  WHAT IT COST is worth stating because it is not a wrong map: in a
  sharded suite it is a shard that stops with no verdict at all, and
  in QGIS it is the application closing on somebody who has opened the
  plugin a few times and then chosen File > New. It was found by
  running twelve tests in one process, not by any single test.
  GUARDED BY THE SHAPE. `test_nothing_long_lived_is_connected_to_a_
  bare_lambda` parses `dialog.py` and refuses a bare lambda on any
  signal from something the dialog does not own, or on any timer. Its
  scope is exactly the hazard, so it needs no exemptions: a lambda on
  a WIDGET's own signal is safe, the widget being a child that dies
  with its parent.

- **A WIDTH IN PIXELS IS A CLAIM ABOUT A FONT, AND SETTING A FONT IS
  NOT SWITCHING A PLATFORM.** (2026-08-29, and the second half is the
  part that will catch somebody again.) The assignment table's nine
  column widths were constants measured against the 9pt Sans Serif
  that `QT_QPA_PLATFORM=offscreen` supplies -- which every runner and
  every CI job sets. At a desktop 13pt the same columns need 1096px
  against the 947 they were pinned to, so every cell but one elided:
  "Quant: Equal inter..." on the chooser whose whole job is saying
  which style a row wears. They grow to their content now.
  I READ THE SLACK AT THE WRONG FONT AND SAID SO OUT LOUD, which is
  why this is here: the Colour ramp cell has 8px spare at 9pt and is
  10px SHORT at 13pt, and I offered "narrow the columns" as though
  there were room. A figure taken from the harness font is a figure
  about the harness.
  AND A FONT IS NOT A PLATFORM. Setting `QApplication.setFont` under
  offscreen reproduces the column metrics and NOT the window
  assembly: the dialog's minimum size hint reads 1279 at both 9pt and
  13pt, while cocoa gives 1334. So a guard can check what a COLUMN
  needs anywhere, and no guard here or on CI can see the window's own
  overshoot at all -- which is why the ceiling was re-derived from the
  measurement rather than defended by a check, and why the test says
  so instead of implying otherwise.

- **A RESTORE IS A LANDING, FOR EVERYTHING THAT ASKS WHETHER THE
  CONTROLS DESCRIBE THE MAP.** (2026-08-28.) `_last_geometry_sig` is
  how `_restyle_only` knows the tiles on screen are the tiles these
  controls ask for, and only `_add_output_layers` ever set it -- so on
  a map this dialog did not DRAW the restyle path was unreachable at
  its first line. A colour picked in the editor went into the record,
  the map kept what it had, and nothing was said: on a map opened with
  Load, and on one adopted by reopening the plugin, which is a journey
  the adoption's own docstring calls something users do constantly.
  IT IS SET WHERE THE RECORD IS APPLIED, which is the one place all
  three doors pass through and the moment the claim becomes true --
  the controls have just been written FROM the group's own record, so
  they describe the map its layers hold, exactly as a landing's
  snapshot describes what it drew. A group with no record never
  reaches that line and keeps a null signature, which is the honest
  answer rather than an omission.
  THE GENERAL FORM, and this project has the mirror of it already: ask
  of any record whose meaning is "these two things agree" WHO ELSE
  brings them into agreement. A landing is the obvious writer; a
  restore is the quiet one, and a fact only the obvious writer sets is
  a fact that is false on every journey the other one owns.

- **A RECOVERY MUST REPORT WHICH OF ITS ROUTES ANSWERED, AND WHAT IS
  STAMPED IS WHAT IT LANDED ON.** (2026-08-29, ledger row 23, and the
  two halves of that claim turned out to be one mechanism.) A
  self-contained GeoPackage records the region its SENDER drew from,
  which on their machine is an ordinary layer and on the recipient's
  is a path that does not exist -- so the data comes back from the
  copy inside the file, and the record and the layer in force stop
  describing the same thing. Both resume branches stamped the group
  with the RECORD, so nothing in the recipient's project ever answered
  to it: `_point_the_chooser_at` walks for a layer matching that
  source, finds none, and leaves the chooser silently wherever it was.
  WITH TWO SENDERS' MAPS OPEN THAT IS THE OTHER SENDER'S DATA.
  Returning to the first map through the group chooser took its group,
  its design and its output path -- and the second sender's region, so
  the next Generate re-tiled it from their data and the output path
  being RIGHT is what made it worse: the next Save would have written
  that over the first sender's own file.
  `_recover_the_source` returns the source it landed on now, and the
  stamps fall back to the record only where it landed on NOTHING --
  which keeps the reason the code was written that way, since a failed
  recovery must not file the resumed group under whatever dataset the
  chooser happens to hold. Both answers are asserted in one test,
  because a reader meeting either alone would take it for the whole
  rule.
  THE GENERAL FORM: where one fact has a RECORDED value and a
  RESOLVED one, ask which of them a later lookup will be able to
  find. A record describes where something came from; only the
  resolution describes where it IS.

- **"ALREADY THERE" IS A QUESTION FOR THE FILE, NOT FOR A STRING THAT
  NAMES IT.** (2026-08-29, ledger row 35.) A save treats a layer whose
  source already names a table in this file as saved already --
  correctly, since the second press on any map meets it -- and it
  asked the SOURCE STRING, which nobody rewriting the file can change.
  So when a colleague saved the shared GeoPackage while this map was
  open, moving one element to another column, that element was skipped
  as though it had been written AND its name went into the written
  set; the stale-table drop then removed the table the colleague HAD
  written, since it belongs to an element this map has and was not
  among the names just written. THE ELEMENT LEFT THE FILE ALTOGETHER,
  both people lost it, and the plugin said "Saved".
  NOTHING CAN BE WRITTEN IN ITS PLACE, and measuring that is what
  decided the repair's shape rather than any preference: a layer whose
  table was dropped under it answers `isValid` True, `dataProvider().
  isValid()` True and `featureCount()` 40, and yields ZERO features.
  This is the cached-answer trap of ledger row 32 met for the third
  time, and writing such a layer would replace a real table with an
  empty one.
  SO THE SAVE WRITES WHAT IT CAN, REMOVES NOTHING, AND SAYS SO. The
  drop's candidates are this session's record and the file's own, and
  its reasoning holds only while nobody else has touched the file:
  once a table has gone from under us, a table that looks like our
  abandoned one is just as likely to be their current one. Nothing is
  deleted on a guess.
  IT NEEDED TWO PROCESSES AND A RENDEZVOUS, because a running QGIS
  serves its own cached pages and the drop is gated on the file being
  the saver's own -- the first arrangement had the colleague meeting
  somebody else's file, where their drop returns at its first line and
  the precondition never existed at all. The SUITE stages the file
  state instead: what a colleague leaves behind is a state, not a
  race, and where a case depends on a window the answer is to close
  the window rather than to measure how often you land in it.

- **A SAVE THAT PUMPS THE EVENT LOOP MUST TAKE ITS BUTTONS DOWN, AND
  THE TWO ARE ONE DECISION.** (Maintainer's decision 3, 2026-08-29.)
  Every call the save's write loop makes is one of QGIS's or OGR's own
  per-layer APIs, and each opens the GeoPackage, so the seconds grow
  with the layers already in the file: 134 of them at the 256-element
  ceiling, with a 50 ms heartbeat recording ZERO beats. Making the
  save a single OGR session is a rewrite of the writer and is 0.24.5's;
  what a person meets in the meantime is a window that says what it is
  doing rather than one that looks like a hang.
  THE PUMP IS AT THE TOP OF THE BODY, where none of that loop's four
  `continue`s can skip it: a bar that stops moving on the elements
  that are skipped says the save has hung. And turning the event loop
  is exactly what would otherwise let somebody press Save or Generate
  into a half-written file, so both controls go down for the duration
  and are put back AS THEY WERE FOUND rather than enabled -- a save
  can be pressed while Generate is already refusing for its own
  reasons.
  THE COST IS UNTOUCHED AND THAT IS THE DECISION, not an omission.
  Responsiveness and cost are different questions, and answering the
  cheap one first is what stops a rewrite being done in a hurry.

- **`isVisible` IS FALSE IN A WINDOW NOBODY HAS SHOWN, SO IT CANNOT
  ASK WHETHER SOMETHING IS HIDDEN.** (2026-08-29.) A guard for the
  save's progress bar asserted `not progress.isVisible()` before and
  after, and BOTH halves passed with the repair mutated away -- the
  entry SURVIVED and said so. Offscreen, every widget in an unshown
  window answers False whatever anybody set; `setVisible` moves the
  explicit hidden flag, and `isHidden` is a question such a window can
  answer honestly. This project already carries the same trap about
  `grab()` and about probing state programmatically; this is it met
  from the ASKING side, and the catalogue is what found it.

- **A TEST LEG THAT RUNS AFTER THE STATE IT IS ABOUT MEASURES
  NOTHING.** (2026-08-29, paying back the catalogue triage's second
  bad trade.) A re-tile leg asserting that a taken-back element is
  re-seeded ran on the element the arm ABOVE had just reclaimed --
  whose layer wore the plugin's own renderer, so the landing found
  nothing to carry and the assertion held whatever the gate said. The
  repair is an ORDER: put the element back into QGIS's hands, move the
  spacing FIRST so the restyle path declines, and only then pick the
  style back, so the layer still holds the dock's renderer when the
  run lands. Pick first and the restyle re-seeds in place, and the
  re-tile that follows meets an element that was never deferring.
  BOTH PREMISES ARE ASSERTED, so the arm cannot go quietly back to
  measuring nothing. Ask of any leg what STATE it needs and whether
  the step before it destroys that state.

- **A BACKSLASH-NEWLINE INSIDE A NON-RAW ANCHOR IS A LINE
  CONTINUATION.** (2026-08-29.) A catalogue entry anchored on a source
  line ending in `\\` stored it as ONE collapsed line and matched
  nothing. `r"""..."""` keeps it. The tool refused by name rather than
  reporting a clean sweep, which is the whole reason `mutation_check`
  will not judge an absent anchor -- and the same reason
  `check_standards` fails on one.
  ITS SIBLING IS THE INDENTATION: wrapping a loop in `try/finally`
  moves every anchor inside it by two spaces, and EIGHT entries went
  orphaned in one edit. The gate named them, they were re-indented,
  and every one was RE-PROVED rather than assumed -- an anchor that
  matches again can still be aimed at nothing.

- **THE EIGHTEENTH WATCHER FAULT: A WORK LINE THAT CANNOT SHOW A DEAD
  WORKER.** (2026-08-29.) The five-minute beat reported running work
  through `ps | ... | head -2`, so with a release parent and THREE
  test shards it showed the parent and ONE shard. It was accurate and
  useless: this project has already been caught by a total climbing
  healthily while one shard had died at startup, and a watcher capped
  at one worker cannot report that however carefully it is read. It
  prints every worker with its own elapsed and cpu now, so a shard
  sitting at 0:00 beside siblings at minutes is visible at a glance.
  ASK OF ANY WATCHER WHETHER ITS OUTPUT CAN EXPRESS THE FAILURE, not
  merely whether it is correct about what it shows.

- **AND THE FIFTEENTH, COPIED FORWARD WITHOUT ITS REASON.** The same
  beat carried `owed=$(grep -c ... || echo "?")`, which is the exact
  fault this file has recorded since 2026-08-20: `grep -c` PRINTS `0`
  and EXITS 1 when nothing matches, so the fallback APPENDS to a
  perfectly good answer instead of replacing it. The beat duly
  reported "0\n? owed" the moment the owed list emptied -- and what
  emptied it was the edit recording that the work was done.
  IT CAME BACK BECAUSE THE LINE WAS COPIED AND THE REASON WAS NOT.
  That is the argument for writing the reason AT the line rather than
  only in this file: a rule in a binding document does not travel into
  the next throwaway script, and the fifteenth fault is the one this
  project has now paid for twice.
  Both are fixed in a NEW file rather than by editing the running one,
  because bash reads a script incrementally from a byte offset and
  editing one mid-loop can make it execute garbage.

- **WHEN THREE REPAIRS TO A MECHANISM FAIL, SUSPECT THE PROMISE.**
  (2026-08-29, and it cost most of an afternoon.) The assignment
  table's columns were taught to grow to their content, and the same
  commit asserted that no column ever elides. Both halves were written
  on this machine, where the columns and the window's 1480px budget
  never meet. Windows opened at 1729px, then 1790px, then 1729px
  again.
  FOUR REPAIRS WENT INTO THE MECHANISM. Bounding the table's minimum
  by live widget widths, which is not a meaningful subtraction before
  a layout pass; by the window's minimum less the table's, which is
  self-consistent and INERT, because A WINDOW OPENS AT ITS sizeHint
  AND A MINIMUM NEVER BOUNDS A PREFERRED SIZE; by a feedback loop on
  `sizeHint()`, which is not meaningful before assembly and so never
  fired; and finally by capping the columns' SUM, which worked.
  AND THE FIFTH CHANGE WAS THE ONE THAT MATTERED, and it was not to
  the code. With the sum capped the window FITTED on Windows and the
  no-elide promise failed instead: 'Style' wants 295px there against
  184 here, so the columns alone want about 1200px inside a 1480px
  window that also holds everything else. The two clauses cannot both
  hold where the fonts are wider, and the maintainer's ruling had
  already said which wins -- "widen the columns; ceiling near 1480".
  The assertion now permits eliding exactly where the budget binds.
  THIS FILE ALREADY SAYS three failed attempts mean the approach is
  wrong; what this adds is that the approach may be the ASSERTION
  rather than the code. A promise written on one machine is a claim
  about that machine's fonts.

- **PROVE THE QUANTITY THE FAILURE MEASURES, NOT ONE THAT SOUNDS
  EQUIVALENT.** (Same day, and it is why the four repairs above each
  looked finished.) The guard for the ceiling measured
  `minimumSizeHint()`; the tests that were failing measure
  `dlg.width()` after `show()`. It passed on every one of those
  repairs, so each looked proved. Rewriting it to measure what the
  failure measures reproduced the fault LOCALLY at 3587px -- in a
  state I had told the maintainer was unreachable on this machine,
  and which took one line to reach: force every column to 400px, and
  this machine is in the position wide fonts put Windows in.
  ASK OF ANY GUARD: is this the number the red run prints? Where it
  is not, the guard is about something else, however reasonable it
  looks.

- **A GUARD ON A PyQGIS CALL THAT RETURNS A TUPLE CAN NEVER FIRE.**
  (2026-08-30, and it cost this project categorical colour on every
  text column.) `if not provider.addFeatures(features):` reads as
  careful code. PyQGIS returns `(ok, features)`, and a two-element
  tuple is TRUTHY however `ok` reads -- measured `(False, [...])`,
  truthy, with zero features added. So the shared classification
  source came back EMPTY for any text column, and `if not everywhere:
  everywhere = values` then silently restored the per-element
  sampling that the one-colour-one-meaning ruling of 2026-08-15
  abolished. One colour meant different values on different elements
  of one map, and the same wrong renderers went into the saved file.
  Text is what categorical mapping is FOR.
  THE SWEEP: any PyQGIS setter or writer whose success you branch on
  -- `addFeatures`, `changeAttributeValues`, `deleteFeatures` and
  their kin -- may hand back a tuple or a bare bool depending on the
  call and the version. Unpack explicitly, or test
  `isinstance(x, tuple)` and take `x[0]`; never truth-test the return
  whole. And ask of any guard you did not watch fire whether it CAN.
- **A TEST THAT SUPPLIES ITS OWN INPUT MEASURES THE FUNCTION, NOT THE
  PRODUCT, AND CAN HIDE A SHIPPED DEFECT FOR MONTHS.** (Same day, and
  it is the transferable half of the entry above.)
  `test_one_colour_means_one_value_across_elements` -- the guard for a
  settled ruling -- passes `classify_from=layer`, the region layer,
  which is A SOURCE THE DIALOG NEVER SUPPLIES. The ruling was
  therefore verified against a FUNCTION while the product handed over
  something else entirely, and no differential crossed the gap:
  file-against-map agrees, because both sides carry the same wrong
  colours. This project already knows that a fixture leaving the
  plugin to DERIVE the thing under test measures the derivation; this
  is the mirror -- a fixture that SUPPLIES the thing under test
  measures nothing about how the product produces it. Ask of any test
  whose subject is a value: who computes this value in the shipped
  path, and does my test make them do it?
- **AND A FIX THAT WIDENS A SCOPE RE-AIMS EVERY TRIAL THAT COMPARED
  AGAINST THE OLD ONE.** (Same day, and the fix exposed it within the
  hour.) With maps painted map-wide, the reopen path's adoption trial
  was still computed from each ELEMENT's own values, so it reproduced
  nothing and the walk "recovered" every ramp colour as somebody's
  HAND-PICKS. After a reopen those rows read Custom, picks outrank
  the ramp, and one later edit left one colour meaning two things.
  Its graduated twin is safe BY LUCK, which is worth knowing rather
  than trusting: class colours are a function of the class COUNT,
  categorical colours of the map-wide VALUE LIST. When you widen what
  a value is computed FROM, grep every site that recomputes the same
  value to compare against it.
- **THE DROP HAS BEEN WRONG FOUR TIMES: THE MISSING FACT IS WHAT THE
  ARTEFACT DESCRIBES, NOT WHETHER WE MAY REMOVE IT.** (2026-08-30.)
  `_write_or_drop_the_topology` decides whether a saved unit and dual
  belong in the file. v1 dropped whenever the experimental box was
  unticked -- and the box is unticked on EVERY new dialog, so opening
  a saved map and pressing Save DELETED its motif. v2 guarded with a
  per-file memory plus a count of box touches, and ticking the box to
  LOOK at the tab counted as speaking about the file. v3 drops only
  where a build has ASSESSED this design and found no topology -- but
  with the box off no build runs, so ignorance is the PERMANENT state
  of the common journey and v3 makes ignorance mean "spare": save
  laves, switch to a design with no topology at all, Save, and the
  file keeps the laves motif while its record says
  `topology_written: True`.
  WHAT ALL THREE SHARE is that each asks whether we MAY drop, and none
  records WHAT THE TABLES ARE ABOUT. The fact needed is not "does this
  design have a topology", which needs a build nobody has run, but
  "WHICH DESIGN DO THE TABLES IN THIS FILE DESCRIBE" -- which the file
  can answer for itself, and which makes staleness DETECTABLE rather
  than inferred. Write the design key beside the tables at write time;
  drop when it differs from the design being saved; leave alone when
  absent.
  THIS FILE ALREADY SAYS three failed attempts mean the approach is
  wrong. What the fourth adds is the diagnostic: when every attempt is
  a different answer to one question, ask whether the QUESTION is
  answerable from the state you are asking it in. None of the three
  could be, and no fifth patch would have been either.
- **A QTabWidget LAYS OUT ONLY ITS CURRENT PAGE, so measuring the
  others measures the container.** (2026-08-30, and I reported the
  result to the maintainer before re-measuring it.) Sweeping every tab
  for controls stretched to the window returned 640px for a Save
  button, a Load button, a Clear button, two combos and a spin box
  across three tabs -- and 640px was the PAGE WIDTH. Those pages had
  never been current, so nothing in them had been through a layout
  pass and every child reported its parent's size, which reads exactly
  like a control with no width of its own.
  THE TELL WAS THE UNIFORM NUMBER, which this file already names: a
  verdict that comes back identical for every input is almost always
  the instrument. Six controls of four different kinds do not agree to
  the pixel. Made current and pumped, the same sweep found two tabs
  clean and one control 48px over.
  SO: `setCurrentIndex`, pump, THEN measure -- and the same caution
  reaches any stacked widget, any collapsed dock and anything else
  whose children Qt does not lay out until somebody looks at it.
- **A `processEvents()` LOOP LETS NO WALL TIME PASS, so a QgsTask
  never finishes.** (Same day.) A probe pumped four hundred
  iterations waiting for the topology build and concluded no topology
  could be built -- on a design whose own `can_build` answered True.
  The build runs on another thread and its callback needs the event
  loop AND some seconds; spinning the loop supplies the first and none
  of the second. Wait on the EVENT with a real `sleep` between passes
  and a ceiling sized from a measured figure, which is this file's
  standing rule about ceilings arriving inside a probe.
- **A TEST'S POSITIVE CONTROL CAN BE THE DEFECT YOU ARE ABOUT TO
  FIX.** (Same day.) `test_no_design_control_is_stretched_to_the_
  window` proved its own measurement was live by asserting the region
  chooser DOES take the width, "meant to take the width going". What
  that meant in practice was that the chooser had no width of its own
  and took whatever the STYLE handed it -- 861px under Fusion, a 33px
  stub under macOS. Giving it a width in characters made the control
  unable to fail, so the guard went red on a repair of the very thing
  it was guarding.
  A POSITIVE CONTROL IS A CLAIM ABOUT THE PRODUCT, not scaffolding.
  When one starts failing, ask whether it was standing on something
  that was wrong -- this file already records the same shape from the
  other side, where a fix removed the footing a green oracle had been
  resting on.
- **A LAYOUT PASS THAT WIDENS WHAT IT MEASURES IS A FEEDBACK LOOP; A
  MARGIN IS NOT.** (Same day, and it is the fourth failed repair to
  this one layout.) Two form blocks stacked in a QVBoxLayout end their
  label columns a few pixels apart, because a group box frames its own
  form and that inset is unknowable before a layout pass. Measuring
  the real right edges at show time and widening the short labels to
  reach the furthest is the obvious repair and it RUNS AWAY: a wider
  label grows its form's shared column, which moves the edge being
  aimed at, so the next show does it again -- 1296px to 1618px in one
  run.
  MOVING THE FORM'S LEFT MARGIN settles instead, because a margin does
  not feed a label's width, and the pass is flagged so even a wrong
  reading could only be taken once. The general question for any
  self-correcting layout pass: does the quantity I am adjusting feed
  the quantity I am measuring?
- **A STACKED WIDGET'S MINIMUM IS THE LARGEST OF ITS PAGES, AND THAT
  IS WHY ONE TAB CAN SET THE WHOLE WINDOW'S SIZE.** (Same day,
  maintainer's ask that the first tab open narrower.) The Design tab
  needs 550px and Data & colours 1004 because of the assignment
  table, so the window opened at 1296 whichever tab was in front, and
  a floor of 1180px in `_fit_to_design` made sure of it. Qt's own
  lever is a size policy: the page in front is `Preferred` and the
  others `Ignored`, so the stack follows the current page. The window
  opens at 825px now and GROWS when a wider tab is chosen.
  GROW-ONLY IS A DECISION rather than an omission: a window that also
  contracted would resize under the pointer on every tab click.
- **WHEN A CONTROL'S PARAMETER COMES FROM A GESTURE, THE HANDLE SHOULD
  BE A POSITION AND NOT A DELTA.** (Same day, recorded before it is
  built.) A drag that reports how far it has travelled has to pass
  that through a LEVER to become a parameter, and the lever is a gain
  factor nobody can see: half the edge's length was too twitchy, the
  full length still turned a 35px drag into a scale factor of 0.28.
  Every such number is tuned by somebody guessing.
  A HANDLE THAT IS A POSITION HAS NO LEVER. Put the end of a line
  where you want it and the scale factor is the distance from the
  middle over what it was; the angle of the handle about the middle
  IS the rotation. The geometry follows the pointer exactly, nothing
  needs tuning, and the handle becomes a READOUT as well as a control
  -- it already sits where the current value puts it. Reach for
  absolute before relative whenever the parameter has a geometric
  meaning on screen.
- **A COMPARATOR THAT IS SENSITIVE TO REPRESENTATION CANNOT ANSWER A
  QUESTION ABOUT APPEARANCE.** (2026-08-31, and it is the third wrong
  instrument in one function.) `_same_shape` exists to say whether a
  manipulation moved anything a person could see, and it asked
  `shapely.equals_exact`, which compares COORDINATE SEQUENCES: two
  rings covering identical ground read as different the moment one of
  them begins at another vertex. `transform_geometry` re-grids the unit
  it hands back and restarts those rings, so on archimedean 4.8.8 a
  manipulation that matched no class at all moved a coordinate by FIVE
  HUNDRED map units while the symmetric difference stayed at 2.4e-4.
  The comparison answered "something changed", the report stayed
  silent, and the registered test written to catch that silence failed.
  THE TWO EARLIER INSTRUMENTS FAILED THE OTHER WAY and are recorded at
  the function: areas rounded to nine places (an ABSOLUTE tolerance
  against tiles of area 62,500), then areas at all (a statistic is not
  a shape -- `push_vertex` moves vertices while leaving every area
  identical). What answers is the GROUND: symmetric difference over the
  unit's own area, measured at 1.5e-9 to 2.5e-9 for a manipulation that
  matched nothing against 1.9e-4 to 1.4e-1 for every real edit, which
  is three orders of clear air either side of the threshold.
  ASK OF ANY COMPARATOR WHAT IT IS ACTUALLY COMPARING -- the thing, or
  the way the thing is written down. Vertex order, ring direction, a
  start point, key order, whitespace and float formatting are all
  representation, and a dependency that rebuilds an object is entitled
  to change every one of them without changing anything.

- **AND AN EXACT QUESTION MUST NOT BE ASKED WITH A TOLERANCE.** (Same
  day, the other half of the same defect.) Whether a design holds the
  class an edit names is answerable EXACTLY, from the topology, by
  name, before any geometry exists. `apply` instead handed the selector
  to the library -- which walks its edges asking `label in selector`
  and simply matches none, neither raising nor complaining -- and then
  tried to infer from the resulting SHAPE whether anything had
  happened. Every difficulty above followed from that inference.
  THE TELL IS A MEASUREMENT STANDING IN FOR A LOOKUP. Where the state
  can answer a question directly, a threshold is not a cheaper way to
  ask it, it is a different and weaker question that inherits every
  fault of the instrument. The same shape reaches past geometry: asking
  whether a file changed by comparing bytes where a record could say
  so, or whether a control moved by watching a repaint.

- **A FINISHED JOB'S LOG IS READABLE WHILE ITS RUN GOES ON.**
  `gh run view --log-failed` refuses until the whole RUN completes,
  which on this project means waiting for hour-long siblings; `gh api
  repos/<owner>/<repo>/actions/jobs/<id>/logs` returns a completed
  job's output immediately. That is the difference between a
  fifteen-minute diagnosis and an hour of waiting, and it is what the
  platform probe's speed is worth in practice. Pass
  `--allow-escape-sequences` and strip them.

- **A GUARD THAT COMPARES THREE OF TWENTY-SIX FIELDS IS A SECOND
  DEFINITION OF THE THING IT GUARDS, AND IT GOES STALE.**
  (2026-08-31, and TWO hunts found it independently by different
  routes -- the most this method has converged here.) The save's
  staleness guard asked whether "the design on screen is the one the
  map was drawn at" by comparing family, element count and the
  topology edit list, while the KEY it writes beside the motif hashes
  `_topology_stamp()` -- the spacing and every modifier included. So
  any design term outside those three moved the key while the guard
  reported agreement, and the two harms are opposite and both silent:
  measured, spacing 500 to 900 with no Generate then Save kept a unit
  of area 797,396 beside tiles drawn at 246,110 with the record still
  saying 500, and the same journey moving the tile inset DELETED motif
  and dual from a file whose tiles carry them.
  THE REPAIR IS ONE OWNER, NOT A WIDER LIST. `_capture_design` is now
  the single answer to "what is the design", and both the record's
  writer and the guard call it -- so the comparison cannot drift the
  day somebody adds a modifier, which is exactly how the narrow
  version was born. A guard that ENUMERATES the fields of a record is
  a copy of that record's definition; ask instead whether the owner
  can be called.
  ITS FIRST REPAIR WAS WORSE THAN THE DEFECT, and only a two-arm
  verification caught it: asking `_geometry_signature` instead refused
  the CONTROL journey too, so no motif was written on either path. An
  edited landing adopts its unit AFTER the run, so that signature
  legitimately differs from the one the map was drawn at.

- **A SINGLE-SHOT TIMER THAT IS "DROPPED" IS LOST, NOT LATE -- AND THE
  COMMENT SAYING OTHERWISE IS THE WORSE HALF.** (Same day, in a repair
  written hours earlier by the same hand.) A gate refusing a live tick
  while a save writes returned without re-arming `_live_timer`, which
  is `setSingleShot(True)` and had just FIRED to reach the gate; its
  only two `start()` sites are a fresh control change and
  `_finish_run`. Meanwhile `_preview_timer` is not gated, so the
  preview and the assignment table followed the new design while the
  map did not, with nothing said -- measured, element count 4 to 6
  left the table showing a..f over a map holding a..d.
  THE COMMENT CLAIMED "the redraw is a moment late rather than lost".
  A false comment is worse than none: the next reader believes it
  instead of checking, and this one was believed for hours by its own
  author. When you write that something recovers by itself, name the
  mechanism that recovers it and check that mechanism can still fire.

- **A `ResizeToContents` COLUMN RE-MEASURES ON EVERY `setItem`.**
  (Same day, and it was a regression introduced by that morning's own
  fix.) The Messages tab's answer column was pushed off the viewport,
  so three columns were given resize MODES -- which cured the layout
  and cost ten to eighteen SECONDS per message once the log reached
  its 500-row ceiling, on the main thread, with live update making the
  plugin speak on every tweak. Measured at the ceiling: 8,563ms at
  Qt's default precision, 412ms with `setResizeContentsPrecision(20)`,
  and 5ms once the modes are SUSPENDED across the bulk rewrite and
  restored in a `finally`. Below the ceiling every arrangement is 4ms.
  THE CEILING IS THE CASE, AND A PROBE THAT FILLS PAST IT MEASURES
  NOTHING. `said.record` trims to 500, so a log already at 500 keeps
  its ROW COUNT UNCHANGED and every write is an overwrite -- which is
  what makes the columns re-measure. A first probe filled to 560, read
  4.8ms either way, and the catalogue entry aimed at the bound duly
  SURVIVED. The probe could not reach its own case, which is this
  file's oldest testing fault wearing a row count.

- **AN ENTRY MUST BREAK THE ROUTE THE GUARD WALKS, NOT A ROUTE.**
  (Same day, twice, and it cost four attempts on one entry.) A gate
  was given three callers -- the shelf writer, the family handler and
  the element-count handler -- and an entry mutating any ONE of them
  survived, because changing the element count REPOPULATES the family
  list and the family handler re-asks anyway. The three calls are kept
  as defence in depth, because which door fires today is incidental;
  the ENTRY was re-aimed at the single line where the answer is
  DECIDED. When an entry survives, ask whether it is aimed at a door
  or at the decision.

- **`mutation_check` MUST RUN ITS CHILD OFFSCREEN, AND THE DOCUMENTED
  INVOCATION DID NOT.** (Same day, three diagnostic rounds.) The
  command this file gives -- `env -u PYTHONHOME -u PYTHONPATH python3
  tools/mutation_check.py` -- passes no `QT_QPA_PLATFORM`, while the
  suite always sets `offscreen`. Most entries do not care; one that
  measures LAYOUT does, this project's own record saying a font is not
  a platform. Two font entries came back UNJUDGEABLE and read exactly
  like broken tests; they caught on the first run once the child got
  an offscreen platform. `child_environment()` now `setdefault`s it,
  so the trap is closed at the tool rather than remembered here.

- **WHEN YOU ADD A STEP TO A SEQUENCE, ASK WHAT IT RESETS.**
  (Same day, found by a hunt auditing a harness rather than a
  product.) The topology matrix grew a baseline Generate, placed
  between choosing a manipulation and clicking Apply. That Generate
  lands a topology build, the landing calls `set_unit`, and
  `_refresh_classes` then resets the class combo to the first vertex
  class and refills the verb list with vertex verbs only -- so every
  chosen EDGE verb was silently replaced by `push_vertex` and three
  cells could not fail. Demonstrated by breaking all three edge
  manipulations into no-ops: identical verdicts, while the sibling
  `immediately` cell went red under the same mutation.
  IT IS THE SELECT-THEN-ACT FAULT THE CELL'S OWN DOCSTRING RECORDS AS
  FIXED, re-entering through a step added later. A sequence that
  encodes an order is broken by anything inserted into it, and the
  insertion looks harmless because it is about something else.

- **A DEDUPE WRITTEN FOR AN UNREACHABLE HARM IS DELETED, NOT KEPT.**
  (Same day.) `_report_quietly` does not deduplicate, so a new notice
  on a gate reachable from every live tick looked certain to repeat --
  a warning that fires constantly being one people learn to ignore. A
  guard went in. The catalogue reported SURVIVED, and driving the live
  path with the gate dumps on said why: the key that gate compares
  carries the MODIFIERS, so moving the control changes it and each
  move honestly re-defers rather than re-explaining; four slider moves
  produced no second arrival at all. The mechanism was right and the
  harm was not, which is this project's own calibration arriving on
  its own repair. The dedupe was removed, with the measurement left at
  the site and the property it rested on held by a test arm.

- **RE-WRAPPING A PARAGRAPH DISARMED A PROSE GATE.** (Same day.) A
  guard finds a sentence in the user guide with a regular expression
  whose gaps were mostly literal spaces. Correcting a number made the
  word shorter, the paragraph was re-wrapped to tidy the ragged line,
  and the newline landed between "fifty-six" and "for a tiling" --
  where a literal space cannot match. The test failed with its own
  "this check has silently stopped checking anything", which is the
  right words in the right place and is why that assertion exists.
  EVERY GAP IS `\s+` NOW. A pattern that reads a sentence spanning a
  line break must not depend on WHERE the break falls, because
  re-wrapping is an edit nobody thinks of as semantic. Same family as
  the roadmap gate, from the other side: there a declaration was
  invisible because it had been wrapped through the middle.

- **A DOWNLOADED ARTEFACT HAS A FRESH MTIME AND AN OLD RESULT.**
  (Same day, the nineteenth watcher fault here and a new road.) The
  night's beat picks the newest failing log with `find -mmin -240`,
  which is the right guard against a glob sweeping up every run there
  has ever been -- and it assumes mtime is when the WORK happened.
  Pulling CI's shard logs down with `gh run download` put three files
  carrying a superseded run's failures into the beat's own directory,
  stamped with the minute they arrived, and the beat reported a fixed
  rc6 failure as tonight's trouble. The window filter cannot see it,
  because every fact it reads is genuinely fresh. Put somebody else's
  log where your watcher does not read, or name it so the pattern
  misses it -- and retire your OWN superseded logs, since a directory
  of stale failing logs makes any watcher lie.

- **A TRIPLE-BACKTICK FENCE SHIFTS EVERY INLINE SPAN BELOW IT, AND A
  PROSE GOES BLIND FROM THERE DOWN.** (2026-08-31, found by re-reading
  the procedural documents at the maintainer's asking, which is a
  direction docs/process/HUNT-RECORD.md carries a row for.) A fence
  line carries THREE backticks; a span pattern needs a non-backtick
  between a pair, so the first two cannot pair and the THIRD opens a
  span running to the next backtick. After that, every real span reads
  as prose and every scrap of prose reads as a span: on a three-line
  document two ordinary script references went invisible while "Then" and
  "and" were collected as commands.
  MEASURED ACROSS THE GATED DOCUMENTS: fifteen references hidden,
  TWELVE of them in MAINTAINING.md, which contributed ONE where it
  carries thirteen -- and the one the gate could not see named
  a gitignored path under dev/instruments that does not exist. That is the rc6 CI failure's SIBLING, left standing
  because the repair went to the instance CI named rather than
  sweeping for the question.
  THE PER-DOCUMENT CHECK COULD NOT CATCH IT EITHER: a document that
  contributes SOMETHING passes. Ask of any gate that reads prose what
  its own markup does to its reading, and blank fenced blocks with
  SPACES rather than removing them, so every offset -- and every line
  number a failure quotes -- is unchanged.

- **WHEN ONE FUNCTION IS MADE THE OWNER OF "WHAT IS X", CHECK EVERY
  OTHER KEY FOR TERMS THAT WERE NEVER X TERMS.** (2026-08-31, found by
  TWO hunts independently -- one from the boundaries, one backwards
  from harm.) `_capture_design` was extracted that morning as the one
  answer to "what is the design", and the save's staleness guard was
  moved onto it. The FILE's key went on hashing `_topology_stamp()`,
  which is built from `_unit_kwargs()` and carries `crs` off the region
  layer -- the one stamp term `_capture_design` cannot see. So
  reassigning a layer's CRS, the ordinary repair for a shapefile with
  no `.prj`, moved the key while the guard reported agreement, the drop
  read that as staleness, and nothing wrote a replacement.
  THE DIRECTION WAS CHECKED RATHER THAN FOLLOWED, which is what made
  the repair narrow: `make_unit` at EPSG:3857 and EPSG:27700 gives
  identical tile WKT and identical topology classes, and the tables are
  written in unit space with no CRS at all -- so the CRS describes
  nothing about them and the KEY was the wrong half, not the guard.
  The term left the FILE's key only; the stamp keeps it, because it
  also judges whether a landed build still describes the design on
  screen, and widening the repair into that question would change a
  second thing while measuring one.

- **AN ARMED TIMER IS NOT A RUN THAT WILL START.** (2026-08-31.)
  `_queue_live` arms the live timer on every output-affecting change
  WHATEVER the checkbox says, and `_maybe_live_generate` then declines
  at its second gate. `_a_queued_run_would_redraw` read only the timer
  where its sibling `_a_live_run_will_follow` asks about the checkbox
  on its FIRST LINE -- two readings of one question, one of which had
  never learned the other's opening move. A Save pressed inside the
  debounce with live update off was kept, the person was told the map
  would be saved once redrawn, nothing redrew it, and the write landed
  on the design they had changed AWAY from; closing the window in that
  second cleared the intent and wrote nothing at all.
  THE RULE THIS JOINS is the project's own about deferred work: ask
  what CONSUMES a remembered intent, and whether that consumer can
  DECLINE for a reason having nothing to do with the act deferred.
  WHEN A PROJECT DOCUMENTS ONE READING AS "A SECOND READING OF ONE
  QUESTION", DIFF THE TWO TERM BY TERM.

- **A GATE THAT OPENS A DOOR MUST ASK FOR WHAT IS BEHIND IT.**
  (2026-08-31, found by two hunts independently.) `opt_experimental`
  reached `_gate_experimental_tabs` and a touch counter; the topology
  build runs only from `_rebuild_unit`. So the gate OPENED the Topology
  tab and nothing filled it -- an empty class chooser beside an ENABLED
  Apply button -- and after a design change made with the box off, the
  tab offered the classes of a design nobody was looking at, so the
  edge somebody clicked was not the edge that moved.
  THE COST RULING SURVIVES BY HANGING THE WORK ON THE BOX rather than
  on the tab: the tick IS the asking, so nobody who has not asked pays
  the 0.75-4.4s. When a control gates VISIBILITY, ask what fills what
  it reveals, and whether that filler has any idea the control exists.

- **A HAND-KEPT LIST DRIFTS EVEN WHERE A COMMENT SAYS TO KEEP IT IN
  STEP.** (2026-08-31, twice in one day.) `check_standards.USER_FACING`
  decides which files the hard rules are enforced over, and its own
  comment asks that it match `text_review`'s SOURCES and DOCUMENTS.
  `metadata.txt` joined the review queue on 2026-08-12 and never joined
  this one -- so the `changelog=` and `about=` entries, which QGIS's
  plugin manager displays and which `release_notes.py` puts at the top
  of the GitHub release body, were unchecked for a HARD RULE and for
  Canadian spelling. Measured by planting one sentence in both places:
  caught in README.md, clean in the changelog.
  AND `sandbox.INCLUDE_FILES` carried CLAUDE.md and MAINTAINING.md but
  not README.md or ROADMAP.md, though the suite reads all four -- so
  any catalogue entry whose test touches them came back UNJUDGEABLE,
  which that list's own comment calls worse than a failure.
  THE REPAIR IS TO GUARD THE RULE, NOT THE INSTANCE: a test comparing
  the two lists cannot go quiet the next time a file joins one and not
  the other, which is exactly how both of these arose. Assert both
  lists are non-trivial while you are there -- two empty sets agree
  perfectly.

- **A WANTED WRITE THAT FAILS STILL CLEARS, SO ENABLING THE WRITE IS
  HALF A REPAIR.** (2026-08-31, and it is the third failed repair to
  one method in one day.) `_write_or_drop_the_topology` refused to
  write a motif while the experimental box was unticked, and stopping
  it asking the box changed nothing observable: on the commonest
  journey nothing has BUILT a topology, so `wanted` stayed false. Given
  a synchronous build, `wanted` went true -- and the both-or-neither
  test then found `_topology_dual` empty, declined the write, and the
  clear below ran exactly as before. The only evidence was a dump line.
  SO WHEN YOU ENABLE A GUARDED WRITE, ENUMERATE EVERYTHING THE WRITE
  ITSELF DEMANDS. Here the dual had to be built AND STAMPED beside the
  unit, which is a requirement written at the write and not at the
  gate. THREE REPAIRS FAILED BEFORE I READ WHAT THE BRANCH DID, having
  quoted this file's own rule about that twice the same day.

- **A TEST THAT MATCHES A PHRASE COPIED OUT OF THE PRODUCT IS BROKEN BY
  THE MAINTAINER'S OWN EDIT.** (2026-08-31, and the route is new.) An
  arm counted messages containing `"cannot carry"`. The maintainer
  reworded that notice, `tools/text_review.py --apply` wrote the new
  sentence into the source, and the filter matched nothing -- so the
  arm counted zero and its "at most once" assertion held whatever the
  code did. This file already says to compose an expected sentence from
  the function the product uses; where the sentence is a LITERAL and
  there is no function, match on what the sentence is ABOUT (here the
  control's name, "Topology tab"), never on a phrase from inside it.
  THE APPROVAL PIPELINE IS THE DELIVERY MECHANISM, which is what makes
  this worth its own entry: approving prose is the act that silently
  retunes every test transcribing it.

- **UPSTREAM MOVED TWELVE COMMITS WITHOUT BUMPING ITS VERSION, AND
  FIXED ONE OF OUR FINDINGS.** (2026-08-31.) The vendored stamp reads
  `0.0.7.89 (bf1bbbf)`; upstream's head is `6190917` with `topology.py`
  at +179/-207 and `_tiling_geometries.py` at +44/-67 -- and the
  version string is `0.0.7.89` at BOTH ends. That is exactly why the
  stamp records a commit as well as a version, and why the standing
  rule says to compare both before running the suite.
  `b3650e0` is *"fixed bug in zigzag edges code where it was doubling
  up tiling vertices"*, two lines: the endpoints were added once as
  `edge.vertices[0]`/`[-1]` and again from `ls.coords`, which includes
  them. This project measured that independently on 2026-08-30 and had
  it recorded as a conversation to have; it is answered at the source.
  THE RE-VENDOR IS ITS OWN ROUND, by the maintainer's decision: twelve
  commits touching `topology.py` heavily is not a licence-header bump,
  and the tab, the manipulations, the edit shelf and the topology
  matrix all stand on that module.


- **THE TWENTIETH AND TWENTY-FIRST WATCHER FAULTS ARE ONE RULE: KEY ON
  THE THING, NOT A SNAPSHOT OF IT.** (2026-08-31, both mine, both
  within ten minutes of arming a watcher, and both while the candidate
  was building.) This file already carries that rule from 2026-08-12,
  where a poller pinned to one commit sha sat silent while two more
  pushes superseded it. It came back twice in one morning.
  A WATCHER KEYED TO RUN IDS GOES BLIND AT THE NEXT PUSH. The beat
  named two CI run ids, which was accurate when it was written and
  false the moment a push created a third and fourth: it would have
  gone on reporting the old pair in flight while the runs answering for
  the tree in front of it were invisible. It lists runs BY BRANCH now
  and prints each one's own head sha.
  AND THE CI POLLER PRINTED A SHA IT NO LONGER FOLLOWED. Its own source
  is the evidence -- `SHA=$(git rev-parse HEAD)` captured ONCE at
  arming time and printed on every line, with `--limit 1` so it only
  ever looked at the newest run. It duly announced a run belonging to
  `8cbdff8` under the label `92cfaab`. A verdict with the wrong subject
  is a verdict about whatever the reader is thinking of, which is the
  twelfth fault's own sentence arriving at a SHA rather than a branch.
  THE CHEAP CHECK, before arming anything: name what would have to
  happen for this watcher's subject to change, and ask whether the
  watcher would notice. A push, a relaunch, a new run, a superseded
  commit -- if the answer is no, it is keyed to a snapshot.

- **THREE MORE FROM THE SAME MORNING, ALL CAUGHT BY HAND-RUNNING THE
  WATCHER ONCE BEFORE ARMING IT.** That is the practice this file has
  been recommending since the tenth fault, and it is the first time it
  has been done here before rather than after.
  `gh` GIVES A RUNNING JOB AN EMPTY STRING CONCLUSION, NOT NULL, and
  jq's `//` falls through only on null or false -- so
  `.conclusion // .status` printed `macos=` for every job still going,
  which is the one state that line exists to show. Test the empty
  string explicitly.
  AN UNANCHORED `FAIL` FILTER NAMED A CLEAN SHARD. The word appears
  inside test names ("a failed stage is not remembered"), so a log
  reading `242 passed, 0 failed` was reported as the newest failing
  one. A watcher whose alarms are mostly false is one people learn to
  silence, and it takes the true alarms with it.
  AND THE SHARD BLOCK GLOBBED, which is the stale-log fault for the
  fourth time. `release.py` CLEARS its stage logs when the suite
  finishes, so `ls | tail -3` fell back to a run from two days earlier
  and reported 2,621-minute-old logs as this run's. THE AGE LINE IS
  WHAT CAUGHT IT -- print an age beside anything read off disk, bound
  the search to the run, and SAY when there is nothing rather than
  reading somebody else's.

- **A DOCUMENTATION MERGE IS NOT A NO-OP FOR THE SUITE.** (Same day.)
  `test_every_documented_command_still_exists` opens CLAUDE.md,
  MAINTAINING.md, README.md and ROADMAP.md, which is exactly why those
  four are in `STAGE_DEPENDS` -- a documentation edit really can break
  a test, and it is the kind of change that feels as though it cannot.
  So a docs branch merged into a candidate's branch gets the prose
  gates run over the MERGED tree before the push, not merely
  `check_standards` in the worktree it was written in. Cheap: three
  tests, 160 quotations, 38 scripts and 19 long flags, in under a
  minute.
  AND THE RECEIPT CLAIM IS MEASURED RATHER THAN REASONED. "No shipped
  file moved, so the candidate's receipt still holds" is a reading
  until `release.tree_digest()` is recomputed and compared with the
  receipt, which is one line and settles it. The digest deliberately
  ignores documentation, so the answer is nearly always yes -- and
  nearly always is not a thing to publish an artefact on.

- **THE ENTRY DESCRIBING THE FENCE FAULT IS WHAT BLINDED THE GATE
  NEXT.** (2026-08-31, hours after the fence repair, and found by
  planting a control rather than by reading.) This morning's lesson was
  written as a bullet opening `- **A ` followed by three literal
  backticks and the word FENCE. `_prose_outside_fences` toggles only on
  a line that STARTS with the fence, and that line starts with a dash --
  so the three backticks stayed in the prose, and three is ODD. The
  span pattern pairs positionally over the whole document, so from that
  line to the end of the file every backtick pairs with the wrong
  neighbour.
  WHAT IT COST IS EXACTLY WHERE IT HURTS: the end of CLAUDE.md is where
  this project appends every new lesson. A quoted path added there
  formed no span at all -- its opening backtick was consumed closing
  the runaway span, and the leftover opened one that never closed.
  MEASURED, RED AND GREEN. With the odd count in place, a planted
  reference to a script under tools/ that does not exist -- described
  here rather than quoted, since this gate refuses a quoted path and
  cannot tell a demonstration from a recommendation -- sat at the end
  of the file and PASSED, reporting the same 160 quotations it reports
  on a clean tree. With the sentence rewritten to DESCRIBE the delimiter -- "a
  triple-backtick fence" -- the same plant fails with the file, the
  line and the name. Both documents carrying that sentence were odd;
  the other four were balanced.
  THE TELL WAS A COUNT THAT DID NOT MOVE. Adding sixteen backtick spans
  to the file left "160 quotations, 38 scripts, 19 long flags"
  unchanged, which is this file's own rule that a uniform verdict is
  almost always the instrument -- met as a verdict that would not
  BUDGE.
  SO: DESCRIBE A DELIMITER, DO NOT QUOTE IT, which is the rule this
  project already keeps for a path that no longer exists. And a
  document whose backtick count is odd is a document the gate reads
  wrongly from somewhere onward; the parity is one command to check and
  worth checking whenever a lesson is appended.

- **`lines[-1]` ON A FILE ENDING IN A NEWLINE REPLACES THE EMPTY
  STRING, SO THE EDIT APPENDS INSTEAD OF REPLACING.** (2026-08-31, and
  it reached the point of publication.) A paragraph of a candidate's
  release notes was rewritten by assigning to `lines[-1]` after
  `read().split("\n")`. A file ending in a newline yields a final EMPTY
  element, so the assignment replaced nothing and put the new paragraph
  AFTER the old one -- and the body carried the broken draft and its
  replacement, one after the other.
  WHAT LET IT THROUGH WAS THE VERIFICATION. It was `tail -1`, which
  showed the corrected paragraph and said nothing whatever about the
  broken one two lines above it. That is this file's own rule --
  ASSERT THE POSTCONDITION, NOT JUST THE ANCHOR -- with the anchor
  replaced by "the new text is present", which is the weaker half of
  the same question.
  SO ASSERT WHAT SHOULD BE GONE. `assert old not in text` and, where
  the thing is a section, assert HOW MANY of it remain: the repair
  here checks the broken phrase is absent AND that exactly one such
  paragraph exists. What caught it in the end was `--dry-run` printing
  the body, which is the standing rule about verifying against what
  ships rather than what you wrote, doing its job one step before a
  public page.

- **A WATCHER'S HEADLINE MUST CARRY WHAT IS LIVE, NOT WHAT MATTERS IN
  GENERAL.** (2026-08-31, the truncation fault three times in one day
  and the third is the interesting one.) A notification is TRUNCATED,
  so a line below the cut is a line nobody reads. First the candidate's
  CI run printed last, which hid a failing mutation leg for half an
  hour and a passing one for five minutes. Moving the candidate's runs
  to the top fixed that -- until the candidate was PUBLISHED, after
  which its two runs were green and static while the only moving thing
  on the branch, the tip's own round, sat below the fold again.
  THE HEADLINE IS ABOUT WHAT CAN STILL CHANGE. It names the tip as well
  as the candidate now, and drops the tip line when the two are the
  same commit. Ask of any watcher not merely whether its output CAN
  express the failure, but whether the reader REACHES that part of it
  -- and re-ask it whenever the thing being watched reaches a resting
  state, because a headline that was right while something was in
  flight becomes furniture the moment it settles.
