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
  unversioned zip.) Two halves, and the first is the one that bites:
  `check_before_push` replays CI's packaging step, so the PUSH GATE
  mutates `dist/` from an ungated tree every time anybody runs it. The
  measurement that day, and the ruling that the README follows the
  artefact rather than the other way round: C-1.
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
- **A BINDING DOCUMENT IS SPLIT IN TWO, AND THE SPLIT IS PART OF
  UPDATING IT.** (Maintainer's instruction, 2026-09-05, after these
  five documents reached 18,997 lines between them and this one reached
  7,048.) The live half keeps the RULE -- the lesson's headline, the
  decision, the procedure, the command -- and `<NAME>-archived.md`
  keeps the ACCOUNT of what it cost to learn, under an id the live half
  quotes: this file's ids are `C-1` upward, and MAINTAINING.md,
  ROADMAP.md, docs/TESTING.md and docs/PUBLISHING.md each have their
  own letter. Nothing is deleted; one grep gets the rest.
  WHEN YOU APPEND A LONG ACCOUNT, SPLIT IT AS YOU WRITE IT -- the rule
  into the live document, the account straight into the archive. That
  is the moment you still know which half is which, and it costs
  nothing then and an afternoon later.
  IT IS ASKED FOR RATHER THAN REMEMBERED. `python3 tools/doc_archive.py`
  checks that every pointer leads somewhere, that no account is
  stranded where nothing points at it, and that each live document is
  inside its budget; `check_standards` runs it, so it runs at every
  push and every release. IDS ARE NEVER RENUMBERED, because they are
  quoted in the documents, in commits and in conversations.
  WHAT IS EXEMPT is in docs/DOC-ARCHIVING.md, and the one to know is
  ROADMAP.md: nothing a version still OWES may move, because the
  release gate reads that file and a debt somebody has to look up is a
  debt that gets forgotten. Architecture is exempt too -- MAINTAINING.md
  lost two paragraphs to the first pass and that was the right answer.
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
  THE TOOL REFUSES rather than guesses: no receipt matching the tree,
  a tag already taken, CI not green on that commit, or no notes. The
  override is `python3 tools/publish_candidate.py --despite-ci
  <reason>`, which prints the reason IN the release. The numbers in the
  body are read rather than typed. What each refusal is for: C-3.

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
  IT WAS PAID FOR ON 2026-08-29, by a font-metrics failure Windows
  reported seventy-five minutes into its job and nothing local could
  have caught: C-4.
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
  THE MACOS LEG EARNED ITS PLACE ON ITS FIRST COMPLETE RUN: it is the
  only leg that runs the package a macOS user installs, in a profile
  nobody has seeded, and it found three faults this machine cannot show
  -- all three masked here by a style library the plugin seeded years
  ago. C-5.
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
  corrected 2026-08-15 and proved by hushing it in a throwaway copy.
  Nothing there is a hand-kept list, so the two cannot drift apart
  quietly -- a sentence that was FALSE for sixteen days, because
  `EXPECTED_STAGES` in release.py was exactly that. Both widenings, and
  the instruments audit that found the second: C-6.
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
  AND A THIRD RENDERER IS THE ONE THAT CUTS THE ENTRY OUT. The entry is
  delimited rather than stored -- it ends at a lookahead for a line
  opening with digits -- and one indented header ran the 0.24.4 entry on
  through the whole of 0.24.3. C-8.
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
  finish, and each would have produced a number somebody believed
  (C-9). Full procedure
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
  DECISION THEY HAVE TO MAKE.** (2026-08-29, and it cost the maintainer
  two exchanges: an ask that was a ceiling on GROWTH was written up as
  re-opening a settled rule, and ended in a question put back to them
  that they had never owed an answer to. C-12.)
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
  from a bbox-midheight scanline and reads off-centre). **Testing.** The
  full record now lives in `docs/TESTING.md`, which is REQUIRED READING
  before writing or changing tests, together with
  `docs/MUTATION-TESTING.md` for the campaign that keeps the suite
  honest. (C-13.)
- Tests must run with an EMPTY project. Everything shares the one
  QgsProject singleton, so a test that leaves layers behind changes
  which layer the next dialog picks; a single real failure once
  cascaded into four unrelated ones.
- A test that PASSES is not a test that WORKS. It has to fail when the
  behaviour it names is broken, and the only way to know is to break it.
  Every test written to close a mutation gap gets an entry in
  `tools/mutation_check.py`, which does exactly that and runs at
  release. (C-14.)
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
- **A PAIRED ARTEFACT INHERITS THE IDENTITY OF WHAT IT IS PAIRED WITH**,
  so every reader keyed on that identity silently gains a second answer,
  and every writer that maintained the original has a twin that does
  not. (C-15.)
- **A NAME THE USER CAN EDIT IS NOT AN IDENTITY, AND MUST NEVER BE A
  KEY.** Every record in `dialog.py` keys on a custom property except
  the output group, which was found with `findGroup(self._group_name)`
  -- so renaming the group in the layers panel, which is an ordinary
  thing to do, made it invisible and the next run built a rival over the
  same four GeoPackage tables, the abandoned group redrawing the new
  data under the old class breaks. (C-16.)
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
  same fault -- something counts or renders an element and looks only at
  `_element_layer_ids` -- and each time it was fixed in the instances a
  keyword search turned up, because the keyword matched what had just
  been fixed. (C-17.)
- **A TEMPORARY LIST FROM A QGIS GETTER FREES ITS CONTENTS.**
  `renderer.ranges()[0].symbol()` and `categories()[0].symbol()` read
  memory that has just been released: one segfaulted QGIS outright,
  the other returned a plausible WRONG COLOUR (#000000) that looked
  exactly like the Qt double-ownership bug and sent an hour after the
  wrong cause. Bind the list to a name first, then subscript it.
- Check upstream's actual semantics before reimplementing behaviour:
  "unclassed" turned out to be matplotlib's linear Normalize (so 50
  equal intervals, not a new scheme), and categorical colours follow
  ListedColormap's sampling: code/(k-1) mapped through int(x*N), clamped
  — 5 on tab10 = entries 0,2,5,7,9. An earlier "derivation" used round()
  and got 0,2,4,7,9, painting the middle category purple instead of
  brown; only the colourspace comparison against an actual upstream
  render caught it. (C-18.)
- After changing behaviour, re-audit nearby docstrings: this project's
  standard makes stale documentation actively harmful, and an audit
  found three lies (libs "appended", live update "after first
  Generate", the removed shared-file box).
- When batch-editing via heredoc Python scripts: assert every anchor
  BEFORE any write, and beware a trailing comma turning a string into a
  tuple (it aborted two patch runs here); for single replacements prefer
  the Edit tool. (C-19.)
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
  ("Error") missed the crash line too, which read "Fatal Python error".
  (C-20.)
- **SEED a watcher with what is already true before it reports
  anything.** Ten watcher faults on this project by 2026-08-12 and the
  last three were all this one: a poller started with an empty "seen"
  set announces its first sighting as news, so historical CI failures
  and a stage log from the previous night arrive as though they had just
  happened. (C-21.)
- **Two watchers must never share a log file.** The eleventh watcher
  fault here, 2026-08-14: a CI watcher was re-armed for a new commit
  while its predecessor was still running, both wrote to the same path,
  and the OLD one appended `FINISHED: cancelled` underneath the NEW
  one's header. (C-22.)
- **A WHOLESALE SPAN REWRITE TAKES ITS NEIGHBOURS.** Deleting everything
  between two anchors removed TWO tests on 2026-08-16, not the one
  intended, because another sat between them -- and one registration
  then named a function that no longer existed, which would have broken
  the suite at `main()`. (C-23.)
- **AND THE OPPOSITE EDIT IS QUIETER: A SECOND DEFINITION REPLACES THE
  FIRST AND NOTHING GOES MISSING.** Also 2026-08-16, hours later.
  Widening `_label_for` for the three kinds of absence was done by
  writing a NEW method below the old one instead of changing it. (C-24.)
- **A SIGNAL CONNECTED TO THE PROJECT OUTLIVES THE WINDOW THAT MADE IT,
  AND SO DOES A COMBO.** 0.24.3 added two hooks onto
  `QgsProject.instance()` -- `_settle_layer_choice` and the pair around
  `layersRemoved` -- and neither carried the retirement gate
  `_on_project_read` already had. (C-25.)
- **A GATE WHOSE EXIT NOBODY BRANCHES ON IS NOT A GATE EITHER, and the
  second visit pushed.** 2026-08-25: `check_standards; echo;
  check_before_push; echo; git commit && git push` -- both gates printed
  their failures, both echoes exited 0, and the commit chained off the
  ECHO. A tree the push gate had just called CI-red reached the public
  branch one command after the words appeared on screen, which is the
  2026-08-15 fault with the pipe replaced by a semicolon. (C-26.)
- **A GATE PIPED INTO ANYTHING IS NOT A GATE.** `check_before_push |
  tail -2` returns TAIL's exit status, so a shell `&&` after it fires
  whatever the gate said. That is how a tree failing the standards check
  reached the branch on 2026-08-15, one command after the gate reported
  the failure on screen -- the words were right there and the exit code
  was gone. (C-27.)

- **A WATCHER IS A PROGRAM, AND A PROGRAM CAN DIE.** The thirteenth
  fault here, 2026-08-15: a CI poller with associative arrays, a nested
  here-string loop and two embedded Python readers exited 1 partway
  through a run, having reported two jobs of eleven. (C-28.)

- **A FALLBACK THAT APPENDS INSTEAD OF REPLACING, AND THE FIFTEENTH
  WATCHER FAULT.** 2026-08-20: a nagging watcher was written to exit
  when its work list emptied, and it read the count as `left=$(grep -c .
  "$LIST" || echo 0)`. (C-29.)
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
- **AND THE MIRROR IMAGE: A LAUNCHER THAT FAILS MAY HAVE STARTED THE JOB
  FIRST.** (2026-08-27.) `LOG=... && nohup python3 release.py --rc >
  "$LOG" 2>&1 &` mis-scoped its variable and reported an error, so the
  launch was read as having not happened and the candidate was launched
  again. (C-30.)
- **READ THE LINE THAT ASSIGNS A TOOL'S VERDICT BEFORE TRUSTING THE
  WORD.** (2026-08-27.) The catalogue sweep prints `caught` or
  `ATTENTION`, and its own source is `verdict = "caught" if
  proc.returncode == 0 else "ATTENTION"` -- so ATTENTION mostly means a
  SURVIVOR, the word SURVIVED never appears in a sweep log at all, and
  `grep -c SURVIVED` answers zero however bad the news is. (C-31.)
- **AND A SUMMARY THAT NAMES WHAT IT SUMMARISES IS CAUGHT BY ANY FILTER
  LOOKING FOR IT.** The same sweep ends with `NEEDS ATTENTION (re-run
  each alone): <every flagged name>`, so a `grep ATTENTION` over the log
  picks up the summary beside the verdicts -- and `sed` leaves a
  non-matching line untouched, so a whole sentence arrived as one "name"
  and the loop word-split it into fifty. (C-32.)
- **`gh run list --commit` MATCHES THE FULL FORTY-CHARACTER SHA, AND A
  SHORT ONE RETURNS NOTHING AT ALL.** (Same day, and it is the sixteenth
  watcher fault here.) A watcher keyed to `eb1ed8b` waited two hours and
  then reported that no run had ever been created; a second, written
  after reading that, reported the same within two minutes. (C-33.)
- **A `PASS` LINE IS LOST TO A PIPE, SO SILENCE PLUS EXIT 0 IS NOT A
  PASS.** `tests/run_tests.py` ends through `os._exit`, so when stdout
  is not a terminal the buffered `PASS <name>` is discarded and
  `tools/run_some.py` exits 0 having said nothing, while a FAILURE's
  traceback reaches unbuffered stderr and survives. (C-34.)
- **AND THE TWO INTERPRETERS ARE NOT INTERCHANGEABLE.** Tests run under
  `$QGIS_PY`; edits and `tools/mutation_check.py` run under `env -u
  PYTHONHOME -u PYTHONPATH python3`. Swapping them fails in two
  directions that both read as a broken test: `env -u ... python3` hands
  you the SYSTEM interpreter, which dies at `import qgis`, and a bare
  `python3` under a sourced QGIS environment dies at `Failed to import
  encodings` having applied no edit at all. (C-35.)
- **`exists` THEN `remove` IS A RACE, AND EVERYTHING HERE SHARDS.**
  (2026-08-28.) `tests/run_tests.py`'s `main()` cleared its scenario
  record by asking whether the file was there and then removing it.
  Three coverage recorders start within a second of each other; all
  three saw it, two removed it, and the third died with
  FileNotFoundError BEFORE RUNNING A SINGLE TEST. Nothing announced
  that: the survivors ran on, the progress count rose, and the record
  would have been missing a third of the suite -- which overstates
  survivors, because a test missing from the record is never offered the
  chance to notice a mutant. (C-36.)
- **A WATCHER THAT SUBSTITUTES "NOTHING" FOR A FAILED CALL REPORTS
  ITSELF TWICE.** (Same day, the seventeenth watcher fault.) A CI poller
  deduplicated by comparing this pass's verdicts against the last, and
  guarded `gh` with `|| echo "[]"` so a transient failure could not kill
  the loop. (C-37.)
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
- **COLOUR BELONGS TO QGIS.** Ramps come from QgsStyle, and where a name
  means something there already, QGIS's meaning wins. The plugin
  installs only palettes QGIS LACKS -- 36 of them, tab10, the
  matplotlib-only families and the eight ColorBrewer QUALITATIVE sets --
  tagged "mapweaver", additive only. Settled by `/grill-me` on
  2026-08-15 after measuring that 35 of the palette file's 63 entries
  were also stock ColorBrewer names, so they had never installed on any
  fresh QGIS since 0.23.0: the plugin's maps were already drawn with
  QGIS's colours and the project had simply not noticed. **"LACKS" IS
  ANSWERED BY THE STYLE LIBRARY, NEVER BY WHAT QGIS CAN GENERATE**, and
  getting that wrong the same evening cost eight palettes. (C-38.)
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
  before.) With live update on, changing the design arms the live timer,
  and a press inside that window used to write the map on screen -- the
  one the person had just changed away from. (C-45.)

- **AND THE SECOND ONE FOUND A COLLISION BETWEEN TWO SETTLED RULES.**
  (2026-08-27, the run over the three rulings.)
  `test_a_ramp_you_are_offered_is_the_ramp_you_get` went red on its
  second half: a row turned categorical kept `YlGn`, "a ramp chosen for
  numbers". Neither the rule nor the code was wrong. The older rule is
  that a row ARRIVING in Categorized swaps a sequential ramp away,
  because a sequential ramp over categories is a cartographic error
  nobody asked for; ruling 4 of the same day remembers a ramp under THE
  MODE THE ROW IS IN. The test's own first half leaves row 1 wearing
  YlGn as a CATEGORIZED row -- deliberately, that being its subject --
  so under the ruling that row now remembers YlGn as its categorical
  choice, and the flip hands it back. (C-46.)

- **A FULL SUITE FINDS WHAT A TARGETED RUN CANNOT REACH, AND THE FIRST
  ONE HERE FOUND A DOCUMENT.** (2026-08-27.) The first full suite ever
  to complete on `for-0.24.4/copy-select-all` returned 636 passed and 1
  failed, and the failure was `test_the_documents_numbers_match_the_
  code`: the element ceiling had split in two the previous day while the
  user guide went on naming one, so a tiling user was being told a limit
  an order of magnitude under what the plugin would draw for them.
  (C-47.)

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
  more that pin the same name through `GROUP_BASE_NAME`. (C-48.)

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
  and the region from the launch snapshot when it is given one and from
  the LIVE CONTROLS when it is not -- which was harmless while landings
  were the only writers, and became three defects the day round nine
  added two writers that never stand at a landing. (C-49.)

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

- **A STRING THAT CARRIES A PATH INSIDE IT IS A PATH.** (2026-08-26, the
  Windows red of six CI rounds.) `same_destination` exists because one
  file has two spellings -- Windows short names, case folding,
  separators -- and it was applied faithfully to output PATHS while
  seven sites went on comparing LAYER SOURCES with `==`. A source only
  looks like an opaque token; it is a path plus `|layername=`, and a
  project save respells the path half. (C-50.)

- **ATTRIBUTION BEATS DELTA, AND THREE NARROW GUARDS ARE THE SIGNAL TO
  STOP PATCHING ROUTES.** (2026-08-26, ledger row 48, and it is the
  sharpest thing the bulletproofing round taught.) The categorized
  adoption walk asked what CHANGED -- adopt any colour differing from
  what the plugin would seed NOW -- and a landing that keeps a renderer
  over an unreadable class source makes that question lie: `expected`
  falls back to automatic colours while the map honestly wears the
  template, so the template's own colours were adopted as a person's
  hand-picks and outranked the template forever. (C-51.)

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
  ROOM.** (2026-08-25, and it is the sharpest thing the group-unit build
  taught.) A regression showed that taking a group over while a run was
  IN FLIGHT erased the evidence the landing was about to read, so
  `self._task is not None` was added to `_bind_group_to_dataset`.
  (C-52.)

- **A HARM NAMED BY READING IS A HYPOTHESIS, EXACTLY LIKE A SITE.**
  (2026-08-26, judging nine hunt claims.) This file already says that a
  location reasoned out of the source reads exactly like one somebody
  proved. Three of those nine described the code CORRECTLY -- a guard
  really was missing from two of three doors, an embedded region really
  does load under a source string the gate can never match, both
  measured -- and not one of them costs a user anything, because in
  every case a second mechanism answers first. (C-53.)

- **A GATE CAN BE SATISFIED BY A SENTENCE DENYING IT.** (2026-08-26.)
  `check_roadmap` is the first stage of every release and refuses a
  candidate while the version's section lists work; it decided that by
  searching for the words "nothing outstanding". The section carried,
  honestly, "the reason this section does not yet say 'nothing
  outstanding'" -- followed by a page of owed work -- and the gate read
  the denial as the declaration and cleared the tree. (C-54.)

- **PRESENCE IS NOT ORDER, AND A CALL PUT BACK IN THE WRONG PLACE IS
  WORSE THAN ONE STILL MISSING.** (2026-08-26, and FOUR hunts of eight
  found it independently -- the most this method has ever converged
  here.) `_resume_from_gpkg`'s take-over branch was missing
  `_recover_the_source`; the repair added it AFTER
  `_apply_working_state`, where the twin calls it BEFORE and says why at
  its own call site: a variable cannot be restored to a column the
  region layer in force does not have. (C-55.)

- **BEFORE CLEARING ON AN ABSENCE, ASK WHAT MAKES THE RECORD ABSENT.**
  (Same day, and it is the other half of the same evening.) A restore
  was taught to CLEAR a record where the incoming one is silent about it
  -- the cure for a real defect three hunts had reported, where one
  output group's colours rode onto another. (C-56.)

- **WHEN A REPAIR GIVES ONE STORE A NEW WRITE, ENUMERATE EVERY STORE
  THAT ALREADY HELD THAT FACT.** (Same day, the round's last two
  findings, and the shape this project meets most often.) A restyle was
  taught to write the GROUP's record, with a comment arguing exactly
  why. The FILE's record was given its write hours later, by a different
  commit, on the landing path alone -- so it inherited the gap the first
  write had just closed: the file's STYLES were updated by a restyle and
  its RECORD was not, and a colleague opening that GeoPackage without
  the project resumed a design the user had abandoned, their first
  Generate repainting the map back to it. (C-57.)

- **A RECORD ASSEMBLED FROM TWO MOMENTS MUST SAY WHICH MOMENT EACH FIELD
  CAME FROM.** (Same day.) The working state deliberately takes its
  DESIGN from the launch snapshot and its ELEMENTS live, and both halves
  are right for good reasons written at the code. MEASURED ON
  2026-08-26, AND THE FAULT WAS THE OTHER WAY ROUND. This entry said
  `region` travelled with the design half and therefore filed a new
  dataset's hand-picked colours under the old dataset's source. (C-58.)

- **THE SIZE GUARD ASKS; ONLY WHAT IS NOT A SIZE IS REFUSED.**
  (Maintainer's ruling, 2026-08-25: "Warning not absolute. Find a
  different approach to sentinel if appropriate.") Above
  `MAX_TILES_CONFIRM` a run is confirmed in ordinary words; above
  `MAX_TILES_HARD` the SAME question is put in stronger ones -- this may
  use all the computer's memory, QGIS may stop responding, save your
  project first -- with the safe button as the default, on the
  dependency-consent precedent. (C-59.)

- **A BLANK THE PLUGIN IMPOSED IS NOT A CHOICE THE USER MADE.** An
  element left on "---" stays unassigned through rebuilds, because
  cycling a default back in would undo a deliberate switching-off. But a
  table built when NO FIELDS were on offer leaves every row blank for a
  reason that has nothing to do with anybody's intent, and honouring
  those blanks is how a plugin opened before its data ends up refusing
  to draw and blaming the user for not assigning a variable -- the field
  report of 2026-08-15. `_fieldless_build` tells the two apart. (C-60.)
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
- **What ELEVEN defects taught about that feature pair, 2026-08-15.**
  Six hunts pointed at the pinned bounds and copy-to alone found eleven,
  every one a wrong map rather than a crash, and four rules come out of
  them that generalise past this feature. A RECORD HOLDING TWO CLAIMS
  must be tested with both in force: the pin record holds copied
  boundary VALUES and per-end pin FLAGS, each worked alone, and together
  the pin did nothing while the button stayed down and the number was
  stamped. (C-64.)

- **A RANGE IS NOT THE ONLY THING THAT EATS A KEYSTROKE.** Four defects
  on 2026-08-17 were controls silently refusing what a person typed, and
  each was invisible to `setValue`, which clamps without complaint. The
  mechanisms differ and the tell is identical: a validator refusing a
  keystroke past `maximum` (the pinned-bound box at 100x the data; the
  Ramp Display Range's two percent boxes, each clamped by the OTHER's
  current value, so from a window of (0, 40) typing 60 kept SIX);
  `decimals` lowered to tidy a display, so Rotate at zero places turned
  22.5 into 22; and a `valueChanged` HANDLER THAT REWRITES ITS OWN BOX
  -- `_skip_zero_scale` fired per keystroke because keyboard tracking
  was on, so typing -0.5 announced a landing on zero after the leading
  nought and the design came back UN-MIRRORED at a size that looks
  exactly right. (C-65.)

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
  stamps, saying at that line why ("the last moment before the value is
  stamped"); `_restyle_only` stamped and then retired. Both calls were
  born in one commit and the order was reversed on one side, so the
  twin's own explanation sat fifteen hundred lines from the path that
  got it wrong. (C-66.)

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

- **A GUARD THAT ASKS ABOUT ONE THING MUST NOT STAND IN FRONT OF AN EXIT
  THAT IS ABOUT ANOTHER.** Three defects in one day, 2026-08-17, all
  this shape, and each cost a user their work rather than a crash. A
  COLOUR comparison at the head of `_graduated_layer_edited` stood in
  front of every `embed_style` exit, so a break retyped in QGIS reached
  the map, the project and the .qgz and never the GeoPackage a colleague
  opens -- since 2026-08-10, and invisible because the map was right.
  (C-67.)

- **A REPRODUCTION CAN STOP REPRODUCING BECAUSE A NEIGHBOURING RULE
  CHANGED, AND THE DEFECT IS NOT DEAD -- ITS DOOR HAS MOVED.**
  2026-08-18, writing the guard for `_restyle_only`. Its committed probe
  reached pin retirement by moving the Classes spinner, and that route
  had been REFUSED hours earlier when a class count stopped being
  allowed to destroy a pin. (C-68.)

- **CLEARING IS RIGHT WHEN THE USER LET SOMETHING GO, AND WRONG WHEN THE
  PLUGIN MERELY STOPPED DECIDING.** (2026-08-18, three defects in the
  deferral family.) `_stamp_category_colours` clears both stamped
  records when there is nothing to record, which stops a layer carrying
  stale choices and is correct. `_assignments` reports a DEFERRING row
  with its picks and pins as None -- indistinguishable at that site from
  a user who cleared everything -- so restyling an element in QGIS
  erased its pinned bounds and hand-picked colours from the saved
  project while the open window still showed them. (C-69.)

- **A GATE THAT CHECKS HALF OF WHAT IT NAMES IS WORSE THAN NO GATE**,
  because the other half is then believed to be checked. 2026-08-18:
  `sync_release_content.check_vendor_claims` promises in its own
  docstring that "prose claims about the vendored library match the
  recorded stamp", and did `stamp.split()[0]` -- the VERSION alone. The
  stamp is written "0.0.7.89 (bf1bbbf)" precisely because upstream does
  not always bump the version when the code moves, which is what
  MAINTAINING.md tells a re-vendorer, so the half that exists FOR that
  reason was the half nothing compared. (C-70.)

- **WHEN A FIX WIDENS A CALL SO IT STOPS IGNORING X AND Y, ENUMERATE
  EVERY KEY OF THE RECORD THE CALLER COULD HAVE READ.** 2026-08-17 and
  18: `_table_id_colours` built each element's preview colour from the
  ramp NAME, and was wrong SIX TIMES -- a deferring element's layer, the
  Ramp Display Range, the row's Reverse, hand-picked class and category
  colours, a column with nothing to classify, and a constant column that
  the renderer colours from the middle of the window. (C-71.)

- **THE PLUGIN'S TABLE FOLLOWS THE LAYER'S RENDERER, AND THE SCOPE OF
  THAT IS THE WHOLE OF ITS SAFETY.** (Maintainer's ruling, 2026-08-17,
  on a field report against rc5: breaks retyped in QGIS's Symbology
  panel, then a style pasted across four element layers, reached the
  plugin not at all -- the rows went on describing THE MAP THE PLUGIN
  LAST DREW while QGIS drew something else, and the next Generate
  destroyed the lot.) It was ONE fault rather than three, and the tester
  established that themselves by setting the affected rows to a numeric
  style and repeating the paste. (C-72.)

- **WHEN A FIX THREADS A "WHO FIRED THIS" ARGUMENT THROUGH A FAMILY OF
  HANDLERS, GREP THE CALLS THEY MAKE TO EACH OTHER.** 2026-08-17, and
  found by two independent hunts within an hour of each other, not by
  the suite. Giving an Unclassed end two pin controls meant every
  handler had to learn which control fired, so `source` was threaded
  through three signatures and every call site updated -- except one
  handler calling ANOTHER handler, `self._bound_edited(which)` inside
  `_bound_moved`. (C-73.)
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

- **A GUARD YOU HAVE NOT WATCHED FIRE IS A GUARD YOU HAVE NOT GOT, AND
  AN EDIT CAN REPORT SUCCESS WITHOUT LANDING.** (2026-09-04.) A stage
  table reported TWO calls to a constructor against its parent's one.
  The matcher was suspected, a guard was written to refuse two functions
  of one name, the probe was re-run, the guard did not fire -- and
  docs/PERFORMANCE.md then recorded the matcher as CLEARED on the
  strength of that silence. (C-80.)
- **A STAGE, A ROW OR A KEY THAT NAMES A FUNCTION WHICH DOES NOT EXIST
  REPORTS NOTHING, AND THAT READS AS COSTING NOTHING.** (Same day.) A
  generation profile listed a stage under a name no function has -- the
  no-data split is not called what the probe called it -- so the row
  never appeared, its work read as free, and docs/PERFORMANCE.md
  honestly listed that split as UNMEASURED the whole time the probe
  claimed to measure it. (C-81.)
- **A WORK LINE THAT CANNOT SHOW A DEAD WORKER, MADE AGAIN.** (Same
  day, and this file has carried it since 2026-08-29.) A process list
  piped through a three-line tail, against four-plus matching
  processes, silently dropped a shard -- and its absence was read as an
  aborted worker, with a diagnosis about which known teardown abort it
  might be built on top before anything checked. All three shards were
  alive with healthy cpu. LIST EVERY WORKER, and when a worker seems to
  have gone, ask the process table without a cap before asking what
  killed it.
- **ONE POLYGON DOING TWO JOBS CHANGES BOTH WHEN YOU SHRINK IT.** (Same
  day, patch 4.) The tiling grid's extent said which cells were WANTED
  and also PHASED the lattice, since the meshgrid origin comes from its
  own bounds. Shrinking it moved every tile: one design drew 2,772 tiles
  both ways with 2,622 differing, every one still touching the region.
  (C-82.)
- **A PROJECTION IS NOT A MEASUREMENT, AND ITS DIRECTION OF ERROR IS
  KNOWABLE IN ADVANCE.** (Same day.) A third column of a performance
  table was published as arithmetic -- the factors measured, their
  composition not -- and put a Generate at about 0.73s against the
  1.038s later measured, because each avoided tile was costed at the
  average tile's share of the work. That is fair for a term that scales
  with tiles and too generous for one where the per-object geometry is
  uniform and the assembly is not. Quote a division as a division, say
  which way it is likely to be wrong, and replace it with a
  measurement rather than quietly swapping the number.

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

On "three-way" comparison (library vs web app vs plugin): the PDF's
reference column IS both of the first two at once, because MapWeaver
pins this same library version and draws through this same
TiledMap.render call inside pyodide — a browser screenshot would
re-photograph the identical code path with UI chrome added, so no
separate column exists. CONDITION TO WATCH, AND THE GAP HAS WIDENED:
the vendor is 0.0.7.89 at upstream commit 6190917 since 2026-08-31,
while the app still pins 0.0.7.59 — thirty versions rather than the
two this paragraph used to describe, and now twelve further commits
on top of them. The earlier reading, kept
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
  DEFAULT rather than a technique to reach for occasionally.** Where the
  thing under test is a family of behaviours -- "edit the symbology in
  QGIS and the plugin follows", "a number you type is the number used"
  -- enumerate the atomic actions as ROUTES, cross them with synthetic
  data SHAPES chosen for failure modes rather than realism, and add an
  axis for what happens NEXT, because arrival and survival are different
  promises. (C-83.)

- **A GUARD MUST NOT REPAIR WHAT IT MEASURES, NOR RUN WHERE THERE IS
  NOTHING TO SEE.** (2026-08-19, three in one sitting, every one caught
  by the catalogue rather than by reading.) A visual guard hid and
  re-showed the mark to get a contrast -- calling the very methods the
  mutation removed, so it mended the product and then measured the
  mended product. (C-84.)
- **WHEN A REPRODUCTION WILL NOT REPRODUCE, MEASURE THE SESSION THAT IS
  BROKEN.** (2026-08-19.) Six reproductions of a reported defect were
  built here, against the reporter's own data, and every one worked. Two
  dumps behind `WEAVINGSPACE_ADOPT_DUMP` and one run by the person
  holding the failure answered it in a minute: the dump was EMPTY, so
  the plugin had never been told, because that session's Generate had
  failed and `styleChanged` is connected only when a run lands or a
  group is adopted. (C-85.)
- **A MATRIX CATCHES ONLY WHAT ITS CELLS MAY COMPLAIN ABOUT.**
  (2026-08-19.) The symbology matrix crosses twelve routes with nine
  shapes, three aftermaths and three schemes, and it caught NONE of
  three defects that landed in one evening -- an affordance drawn under
  the widget that covers it, a ceiling with no edge to mark, a bound of
  1e9 elided out of its box. (C-86.)

- **WHEN A CHANGE BREAKS A TEST, BISECT BY DISABLING RATHER THAN BY
  REASONING, after ONE hypothesis fails.** Insert an early `return` at
  successive points through the new code; the first point that turns
  PASS into FAIL contains the culprit. (C-87.)

- **TWO OF THIS PROJECT'S INSTRUMENTS LIE, and both cost hours on
  2026-08-18.** `print()` inside a Qt signal handler goes nowhere under
  a test that captures output, so an empty dump read as proof the code
  never ran when it ran every time -- AN EMPTY LOG IS NOT EVIDENCE OF
  ABSENCE. And a plain `python3` heredoc run AFTER sourcing the QGIS
  environment dies at bootstrap and applies NO edit, so the run that
  follows measures the unmodified file and reports fiction; use `env -u
  PYTHONHOME -u PYTHONPATH python3`, the same hazard that kills
  `release.py` and `mutation_check.py`. (C-88.)

- **A WATCHER MAY ONLY ADOPT WHAT A PERSON LEFT BEHIND.** Anything that
  reads state off a layer and records it must run at REST: not while the
  dialog is writing renderers (`_applying_style`), not while a run is in
  flight (`_task`), and not while a landing is still being reconciled
  (`_preserved_this_run`). (C-89.)

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

- **A GUARD MEASURES THE GROUND, NOT THE BOX ROUND IT.** (2026-08-19,
  ledger row 23, and it cost a colleague their map rather than a little
  time.) The size guard estimated tiles from a CIRCLE enclosing the
  region's bounding rectangle, while the library tiles that circle and
  then CLIPS to the polygons. (C-93.)

- **A CACHE OF ONE IS NO CACHE WHEN THERE ARE TWENTY-THREE OF
  ANYTHING.** (2026-08-19, ledger row 4.) `_classification_values`
  REPLACED its cache dict on every miss, on the sound reasoning that a
  stale fingerprint's values must never sit there being wrong -- and
  replacing it threw away every OTHER column's entry at the same time.
  (C-94.)

- **A COPY REPRODUCES THE WHOLE CLASSIFICATION, AND THE RECORD GREW
  UNDER IT.** (2026-08-19, ledger rows 21 and 22.)
  `_copy_classification` built its record from breaks and pin flags and
  never read `floor` or `ceiling`, then wrote that record WHOLESALE --
  so a copy left the source's range behind AND destroyed the target's.
  (C-95.)

- **A GITHUB RELEASE BODY PRESERVES SINGLE NEWLINES, so NEVER hard-wrap
  one.** Release notes written at the usual 72 columns arrive as literal
  line breaks, and on a phone that means a sentence broken mid-clause --
  "nothing is promoted," ending a line, `main` starting the next --
  because the renderer never gets to wrap to the viewport. (C-96.)

- **A CHECK THAT CAN ONLY CONFIRM IS NOT A CHECK.** Unwrapping the rc9
  release notes, the script reported "unwrapped: 14 blocks" and I read
  that as success -- but the number needed was how many were still
  WRONG, and nine of eleven paragraphs had been skipped because they
  open with bold and my list-item guard matched `*`. (C-97.)

- **A LIST ITEM NEEDS THE SPACE.** `- `, `* `, `+ ` and `1. ` are
  bullets; `**bold` is a paragraph. Guarding on the bare character
  silently skipped most of a document.

- **A GLOB IS HOW A LOG'S DATE GETS SKIPPED.** (2026-08-19, and the
  THIRD time this project has read a stale log as current.) The rule
  already written is that every excerpt from a log must be dated before
  it is read. (C-98.)

- **WHEN TWO THINGS SHOULD DRAW THE SAME MAP, COMPARE WHAT THEY DREW,
  NOT WHAT THEY LOOK LIKE.** (2026-08-19, comparing the plugin against
  the library on the maintainer's own data.) The two paint with
  different colours by construction -- a two-colour matplotlib colormap
  against seeded QGIS renderers -- so pixels would report a difference
  that means nothing. (C-99.)

- **A NAME THAT CARRIES A NUMBER IS SORTED AS TEXT, AND rc10 COMES
  BEFORE rc2.** (2026-08-19, ledger row 25.) `release.py` named the
  candidate it had just built by sorting
  `dist/weavingspace_qgis-*rc*.zip` and taking the last entry. (C-100.)
- **VERIFY AGAINST WHAT SHIPPED, NOT WHAT YOU WROTE.** The second pass
  at those notes was checked by reading the LIVE page back and
  measuring every line, not by inspecting the local file. Where a
  publish step exists between the file and the reader, the reader's
  copy is the only one that counts.

- **A DEPENDENCY'S CHEAP ANSWER IS A CACHED ANSWER, AND A GUARD BUILT ON
  ONE IS HONEST ONLY AFTER SOMETHING INVALIDATES IT.** (2026-08-20,
  ledger row 32.) `compat.layer_data_is_available` asked a layer whether
  it was valid and its provider whether it was valid, and its own
  Returns block promised that caught "a layer whose file has been
  deleted ... including the case where the layer itself still claims to
  be valid". (C-101.)
- **AND ITS TEST HAD BEEN EXERCISING THE HONEST PATH ALL ALONG.** The
  sibling guard called `reload()` in its own setup before asking
  anything -- which is the one act that makes QGIS tell the truth, and
  the one act a user never performs. (C-102.)
- **A FIX APPLIED TO A TWIN THAT DOES NOT HAVE THE FAULT IS DEAD CODE
  THAT READS AS PROTECTION.** (2026-08-20, ledger row 34.) The rule that
  a colour equal to the renderer's SOURCE SYMBOL is QGIS's clone rather
  than somebody's decision is right on the graduated path, and was
  written onto the categorized path in the same edit out of the usual
  and correct suspicion about pairs. (C-103.)
- **A GUARD THAT LANDS WITHOUT A TEST OF ITS OWN LOOKS GUARDED, BECAUSE
  THE NEIGHBOUR IT RE-ANCHORED STILL PASSES.** The edge rule for pinned
  bounds went in on 2026-08-19, correctly re-anchoring the catalogue
  entry standing on the line it changed -- and that entry proves ends
  are adopted AT ALL, not that they are kept off the ladder's edge.
  (C-104.)

- **`styleChanged` FIRES ONLY ON `setRenderer`; AN EDIT MADE ON THE LIVE
  RENDERER IS SILENT, AND ITS `triggerRepaint()` IS THE ONLY TRACE.**
  (2026-08-20, ledger row 28, reported four times before it was
  measured.) The styling panel installs a whole renderer for some acts
  (adding a class, Classify, a paste) and edits the held renderer in
  place for others (a plain colour change) -- so the plugin followed the
  first kind and was structurally deaf to the second, while
  MAINTAINING.md asserted the opposite in as many words. (C-105.)
- **`ranges()` AND `categories()` HAND BACK COPIES, so editing one is a
  NO-OP on the layer -- and a probe that does it measures nothing.**
  (2026-08-20, twice in one hour: a signal probe's row and a guard's
  first draft.) `ranges[0].symbol().setColor(...)` recoloured a
  temporary; the renderer never changed; "no signal fired" was reported
  about an edit that had not happened. (C-106.)

- **ABSENT IS NOT MOVED: when a NEW guard reads an OLD record, ask which
  paths leave that record deliberately empty.** (2026-08-20, found by
  three hunts independently.) A guard added the day before skipped an
  element whose row signature differed from `_last_signatures` -- right
  in itself, since between a control change and the restyle that answers
  it the layer is merely BEHIND. It asked with `!=
  self._last_signatures.get(tile_id)`, and `_adopt_existing_group`
  leaves that record EMPTY on purpose, saying so in its own docstring:
  the dialog cannot know which assignments produced layers it has only
  just met. (C-107.)
- **A GUARD COMPUTED AS A DELTA IS ARMED FOR ONE INVOCATION.**
  (2026-08-20, ledger row 2, and it defeated a guard written the
  previous day.) `count_moved` was measured across
  `_row_follows_the_renderer` INSIDE ONE HANDLER CALL, to stop a class
  added in QGIS having its shuffled colours adopted. (C-108.)
- **A LADDER MAY HOLD SEVERAL CLASSES WITH IDENTICAL BOUNDS, so a lookup
  by bounds must not stop at the first match.** (2026-08-20, and it was
  a defect in the fix above, caught within the hour.) A constant column,
  a tied column and `{1, 5, 9}` at k=5 all produce degenerate ranges,
  and `addClass` then inserts another `(0.0, 0.0)` class -- which
  collides with any fixture whose first real class is also degenerate.
  (C-109.)
- **WHEN CI TIMINGS MOVE, COMPARE THE SUSPECT ON A MACHINE YOU CONTROL
  BEFORE BELIEVING THE ORDERING.** (2026-08-20.) Windows ran 89 minutes
  against a 53-59 minute history; the largest grower was 2.6x; and it
  was the one test that most exercises the path a fix landed the same
  day had opened. (C-110.)
- **WHEN A GUARD STARTS ANSWERING DIFFERENTLY, FOLLOW ITS RETURN VALUE
  INTO EVERY TUPLE IT IS A MEMBER OF, not only into its callers.**
  (2026-08-20, a regression from the previous day's own fix.)
  `compat.layer_data_is_available` was corrected to answer False for a
  moved file. (C-111.)
- **A REPAIR AIMED AT AN ACT MUST BE RE-AIMED AT THE ACT'S ABSENCE.**
  (2026-08-27, two hunts from different directions in one afternoon.) On
  2026-08-26 the stale-table drop was taught to take a saved STYLE with
  the table it removes, which mends every case where something is
  deleted. (C-112.)

- **A GUARD WHOSE CONDITION IS RIGHT CAN STILL BE AIMED AT NOTHING.**
  (2026-08-27.) The queued restamp's new guard reads `_fieldless_build`,
  and that flag was measured TRUE at exactly the moment the defect
  fires. (C-113.)

- **AN INSTRUMENT THAT HOLDS A FILE CHANGES WHAT IT MEASURES, AND BYTES
  REMEMBER PAGES NOBODY REFERENCES.** (2026-08-27, twice inside one
  test.) A guard read a GeoPackage through a `QgsVectorLayer` it left
  alive, and the open handle made the NEXT run fail at the sqlite level:
  zero tables, read as the product's fault. (C-114.)

- **RETIREMENT IS A FACT ABOUT THE OBJECT, NOT AN ABSENCE IN A
  REGISTRY.** (2026-08-27.) Every long-lived handler here is gated by
  "am I the dialog in charge", and that record was only ever cleared by
  SUCCESSION -- so a plugin the user DISABLED left it naming a dialog
  they had disposed of, which went on adopting dock edits, rewriting the
  project's group record and speaking into QGIS's message bar about
  controls in a window there was no longer any way to open, until QGIS
  restarted. (C-115.)

- **A WIDGET THAT RETAINS LAYER OBJECTS MUST BE REBUILT WHEN LAYERS ARE
  REMOVED, AND A DEAD POINTER'S ADDRESS GETS REUSED.** (2026-08-27,
  found by the saving branch's first full suite.) The region chooser
  keeps the plugin's own output out of its list through
  `setExceptedLayerList`, which stores the layer OBJECTS. That list was
  rebuilt at construction, at a project read, at a resume and after a
  landing -- and never when layers were REMOVED. So after File > New the
  combo went on excluding a set of destroyed pointers, and a layer
  allocated where a dead one had been was excluded for being somebody
  else: the chooser offers NOTHING while the project plainly holds a
  polygon layer, and Generate refuses for want of a region with nothing
  on screen to explain it. (C-116.)

- **A LAYER BUILT ON ANOTHER LAYER'S SOURCE IS THAT LAYER TO ANYTHING
  THAT LOOKS UP BY SOURCE.** (2026-08-27.) The map-unit outlines layer
  is built on the REGION'S OWN SOURCE, deliberately, since nothing is
  copied; and it carries `weavingspace_output`, which is what keeps it
  out of the region chooser. (C-117.)

- **ENUMERATE THE PRODUCERS OF A SECOND CLAIMANT, NOT JUST THE ONE YOU
  BUILT.** (2026-08-27.) The paired-layer rule of 2026-08-16 says a
  paired artefact inherits the identity property of the thing it is
  paired with, so every lookup keyed on that property gains a second
  answer. (C-118.)

- **A DANGLING REFERENCE IS NOT A DISAGREEMENT, WHICH IS WHY NOTHING
  COMPLAINS.** (2026-08-27.) An element may take its classes from
  another element's LAYER, and the choice is stored as `layer:<layer
  id>` -- while a re-tile gives every element a new layer with a new id.
  (C-119.)

- **BREAK EVERY ROUTE AT ONCE, OR THE CATALOGUE MEASURES THE OTHER
  ONE.** (2026-08-27, three times in a day.) A fix written as two guards
  -- skip our own output AND check the chooser took -- survives having
  either one mutated, because the other still sends the walk to its
  fallbacks. (C-120.)

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
  AND THEY NEED OPPOSITE REPAIRS.** (Same day.) An entry excluding modes
  from the no-data split was mutated by adding a literal to a list read
  from `mode` -- while deferral lives in `mode_raw`, so the mutation
  matched nothing and changed nothing. (C-121.)

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
  read as evidence. (C-122.)

- **A UNIFORM VERDICT IS ALMOST ALWAYS THE INSTRUMENT.** Three of this
  project's own tools were found wrong in one day by that tell alone:
  thirty-four "not in the record", then "0 of 8" everywhere, then
  DIFFERS everywhere because a comparison counted `region_7c23c`
  against `region_bb6b7` as a changed decision. Before believing a
  result that came back the same for every input, run the instrument
  against a case whose answer you already know.

- **`mutation_check` APPLIES EXACTLY ONE REPLACEMENT, BY DESIGN**, so a
  fact held at two DISTANT sites cannot be guarded by any single entry.
  The run signature's identity and fingerprint terms are 47 lines apart,
  and an anchor spanning both breaks on any edit between them. (C-123.)

- **A REPAIR'S OWN REPAIR NEEDS THE SAME SUSPICION, AND THE FIRST ONE
  CAN BE WORSE THAN THE DEFECT.** (2026-08-28, the moved-data notice,
  wrong three ways in one evening and every one of them mine.) It kept
  ONE reading in a session-wide slot and compared it against whichever
  dataset the region chooser held, so returning to an earlier map
  through the group chooser told somebody their file disagreed with
  itself when nothing had been touched. (C-124.)
- **A GUARD WHOSE PRECONDITION IS A LOSSY DIGEST IS ONLY AS GOOD AS WHAT
  THE DIGEST OMITS.** (Same day.) The same notice read
  `_layer_fingerprint` -- the feature count, the extent, the field
  names, the CRS -- none of which an ordinary VALUE EDIT moves. (C-125.)
- **OWNERSHIP IS NOT A NAME PREFIX, AND AN ELEMENT ID IS A LETTER EVERY
  MAP SHARES.** (Same day.) The stale-table drop scoped itself to "this
  map's own elements" and decided that by `tiles_<id>`, so saving into a
  GeoPackage holding a colleague's map DELETED their `tiles_a_*` and
  `tiles_b_*` while leaving their `tiles_zz_*` and their own tables --
  one line after a question promising to "leave the rest of the file
  alone", and against the method's own Returns block. (C-126.)
- **A GATE THAT READS RAW SOURCE TEXT CAN BE MOVED BY A COMMENT.** (Same
  day.) `test_pypi_provisioning_is_reached_only_through_consent` holds a
  hard rule by indexing three markers in `plugin.py` and requiring their
  ORDER. A note added above the consent call, mentioning
  `provision_from_pypi` to explain what it fetches, put the download's
  index before the dialogue's and failed the gate with the code
  perfectly correct. (C-127.)
- **A CONSENT DIALOGUE THAT ENUMERATES MUST BE DIFFED AGAINST WHAT THE
  CODE ASKS FOR.** (Same day, and it is a HARD RULE breached since the
  initial commit.) The box named the missing scientific packages;
  `provision_from_pypi` also fetches the pure-python support
  distributions the main ones import at runtime -- its own docstring
  says so -- so somebody who read "Missing or too old: geopandas" and
  approved had SEVEN distributions fetched from pypi.org, against
  metadata.txt's promise that the plugin "shows exactly what it would
  fetch and asks first". (C-128.)
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
  (C-129.)

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
  lives on the layer, never in `source()`. (C-130.)
- **A COUNT QUOTED TO A PERSON MUST BE ASKED OF THE GEOMETRY, NOT OF TWO
  TOTALS.** (2026-08-28.) The icon-mode sentence subtracted a TILE count
  from an AREA count to say which elements were short. (C-131.)
- **A PER-FILE FACT MUST NOT LIVE ON A SESSION-WIDE CONTROL.**
  (2026-08-28, round ten, and it was a repair of mine that put it
  there.) "Include the source data" is one checkbox and the answer it
  stands for belongs to a FILE: whether THAT GeoPackage carries a copy
  of the region. (C-132.)
- **A DISPLAY RULE IS ONLY DISPLAY-ONLY IF NOTHING RE-READS THE
  DISPLAY.** (2026-08-28.) `MarkableSpinBox.textFromValue` abbreviates a
  large number to "1.02M" and its docstring says it touches neither the
  stored value nor the validator. (C-133.)
- **A SUITE CAN HOLD A CONTROL AT A VALUE NO USER HOLDS.** (2026-08-28.)
  Every resume test in this suite unticks live update, which is ON by
  default -- so the whole family was driven at a setting nobody has, and
  pressing Load with the default re-tiled the opened map into memory a
  second later and emptied the saved file. (C-134.)
- **A RECORD SEEDED BY ADOPTION IS A RECORD THAT ASSUMES A PROJECT.**
  (2026-08-28.) The stale-table drop took its candidates from the
  session's own record of what it had written, plus the tables of
  elements the map still has -- and a DROPPED element is in neither.
  (C-135.)
- **AN INTERMITTENT FAILURE UNDER LOAD CAN BE THE SUITE INTERMITTENTLY
  REACHING A REAL DEFECT.** (2026-08-28.) A per-test coverage re-record
  failed one test of 645, in a shard running beside two others on a
  loaded machine. (C-136.)

- **A REPORT ABOUT A VERSION OR A BEHAVIOUR IS FIRST A QUESTION ABOUT
  WHICH BUILD IS INSTALLED.** (2026-08-29.) The maintainer reported that
  the title bar "no longer shows the rc version properly". (C-137.)
- **A CLAIM'S MECHANISM IS USUALLY RIGHT AND ITS HARM USUALLY IS NOT,
  AND THE DOOR IT NAMES IS WHEREVER THE HUNT WAS STANDING.**
  (2026-08-29, taking sixteen owed claims to the end.) This file already
  says a harm named by reading is a hypothesis. (C-138.)

- **A CALLABLE THAT OUTLIVES ITS DIALOG MUST ASK BEFORE IT TOUCHES IT,
  AND A LAMBDA IS NOT A BOUND METHOD.** (2026-08-29, a reproducible
  SEGMENTATION FAULT.) Qt drops a connection to a bound METHOD when the
  receiving QObject dies. (C-139.)

- **A WIDTH IN PIXELS IS A CLAIM ABOUT A FONT, AND SETTING A FONT IS NOT
  SWITCHING A PLATFORM.** (2026-08-29, and the second half is the part
  that will catch somebody again.) The assignment table's nine column
  widths were constants measured against the 9pt Sans Serif that
  `QT_QPA_PLATFORM=offscreen` supplies -- which every runner and every
  CI job sets. (C-140.)

- **A RESTORE IS A LANDING, FOR EVERYTHING THAT ASKS WHETHER THE
  CONTROLS DESCRIBE THE MAP.** (2026-08-28.) `_last_geometry_sig` is how
  `_restyle_only` knows the tiles on screen are the tiles these controls
  ask for, and only `_add_output_layers` ever set it -- so on a map this
  dialog did not DRAW the restyle path was unreachable at its first
  line. (C-141.)

- **A RECOVERY MUST REPORT WHICH OF ITS ROUTES ANSWERED, AND WHAT IS
  STAMPED IS WHAT IT LANDED ON.** (2026-08-29, ledger row 23, and the
  two halves of that claim turned out to be one mechanism.) A
  self-contained GeoPackage records the region its SENDER drew from,
  which on their machine is an ordinary layer and on the recipient's is
  a path that does not exist -- so the data comes back from the copy
  inside the file, and the record and the layer in force stop describing
  the same thing. (C-142.)

- **"ALREADY THERE" IS A QUESTION FOR THE FILE, NOT FOR A STRING THAT
  NAMES IT.** (2026-08-29, ledger row 35.) A save treats a layer whose
  source already names a table in this file as saved already --
  correctly, since the second press on any map meets it -- and it asked
  the SOURCE STRING, which nobody rewriting the file can change.
  (C-143.)

- **A SAVE THAT PUMPS THE EVENT LOOP MUST TAKE ITS BUTTONS DOWN, AND THE
  TWO ARE ONE DECISION.** (Maintainer's decision 3, 2026-08-29.) Every
  call the save's write loop makes is one of QGIS's or OGR's own
  per-layer APIs, and each opens the GeoPackage, so the seconds grow
  with the layers already in the file: 134 of them at the 256-element
  ceiling, with a 50 ms heartbeat recording ZERO beats. (C-144.)

- **`isVisible` IS FALSE IN A WINDOW NOBODY HAS SHOWN, SO IT CANNOT ASK
  WHETHER SOMETHING IS HIDDEN.** (2026-08-29.) A guard for the save's
  progress bar asserted `not progress.isVisible()` before and after, and
  BOTH halves passed with the repair mutated away -- the entry SURVIVED
  and said so. (C-145.)

- **A TEST LEG THAT RUNS AFTER THE STATE IT IS ABOUT MEASURES NOTHING.**
  (2026-08-29, paying back the catalogue triage's second bad trade.) A
  re-tile leg asserting that a taken-back element is re-seeded ran on
  the element the arm ABOVE had just reclaimed -- whose layer wore the
  plugin's own renderer, so the landing found nothing to carry and the
  assertion held whatever the gate said. (C-146.)

- **A BACKSLASH-NEWLINE INSIDE A NON-RAW ANCHOR IS A LINE
  CONTINUATION.** (2026-08-29.) A catalogue entry anchored on a source
  line ending in `\\` stored it as ONE collapsed line and matched
  nothing. `r"""..."""` keeps it. (C-147.)

- **THE EIGHTEENTH WATCHER FAULT: A WORK LINE THAT CANNOT SHOW A DEAD
  WORKER.** (2026-08-29.) The five-minute beat reported running work
  through `ps | ... | head -2`, so with a release parent and THREE test
  shards it showed the parent and ONE shard. (C-148.)

- **AND THE FIFTEENTH, COPIED FORWARD WITHOUT ITS REASON.** The same
  beat carried `owed=$(grep -c ... || echo "?")`, which is the exact
  fault this file has recorded since 2026-08-20: `grep -c` PRINTS `0`
  and EXITS 1 when nothing matches, so the fallback APPENDS to a
  perfectly good answer instead of replacing it. (C-149.)

- **WHEN THREE REPAIRS TO A MECHANISM FAIL, SUSPECT THE PROMISE.**
  (2026-08-29, and it cost most of an afternoon.) The assignment table's
  columns were taught to grow to their content, and the same commit
  asserted that no column ever elides. (C-150.)

- **PROVE THE QUANTITY THE FAILURE MEASURES, NOT ONE THAT SOUNDS
  EQUIVALENT.** (Same day, and it is why the four repairs above each
  looked finished.) The guard for the ceiling measured
  `minimumSizeHint()`; the tests that were failing measure `dlg.width()`
  after `show()`. (C-151.)

- **A GUARD ON A PyQGIS CALL THAT RETURNS A TUPLE CAN NEVER FIRE.**
  (2026-08-30, and it cost this project categorical colour on every text
  column.) `if not provider.addFeatures(features):` reads as careful
  code. (C-152.)
- **A TEST THAT SUPPLIES ITS OWN INPUT MEASURES THE FUNCTION, NOT THE
  PRODUCT, AND CAN HIDE A SHIPPED DEFECT FOR MONTHS.** (Same day, and it
  is the transferable half of the entry above.)
  `test_one_colour_means_one_value_across_elements` -- the guard for a
  settled ruling -- passes `classify_from=layer`, the region layer,
  which is A SOURCE THE DIALOG NEVER SUPPLIES. The ruling was therefore
  verified against a FUNCTION while the product handed over something
  else entirely, and no differential crossed the gap: file-against-map
  agrees, because both sides carry the same wrong colours. (C-153.)
- **AND A FIX THAT WIDENS A SCOPE RE-AIMS EVERY TRIAL THAT COMPARED
  AGAINST THE OLD ONE.** (Same day, and the fix exposed it within the
  hour.) With maps painted map-wide, the reopen path's adoption trial
  was still computed from each ELEMENT's own values, so it reproduced
  nothing and the walk "recovered" every ramp colour as somebody's
  HAND-PICKS. After a reopen those rows read Custom, picks outrank the
  ramp, and one later edit left one colour meaning two things. (C-154.)
- **THE DROP HAS BEEN WRONG FOUR TIMES: THE MISSING FACT IS WHAT THE
  ARTEFACT DESCRIBES, NOT WHETHER WE MAY REMOVE IT.** (2026-08-30.)
  `_write_or_drop_the_topology` decides whether a saved unit and dual
  belong in the file. v1 dropped whenever the experimental box was
  unticked -- and the box is unticked on EVERY new dialog, so opening a
  saved map and pressing Save DELETED its motif. v2 guarded with a
  per-file memory plus a count of box touches, and ticking the box to
  LOOK at the tab counted as speaking about the file. v3 drops only
  where a build has ASSESSED this design and found no topology -- but
  with the box off no build runs, so ignorance is the PERMANENT state of
  the common journey and v3 makes ignorance mean "spare": save laves,
  switch to a design with no topology at all, Save, and the file keeps
  the laves motif while its record says `topology_written: True`.
  (C-155.)
- **A QTabWidget LAYS OUT ONLY ITS CURRENT PAGE, so measuring the others
  measures the container.** (2026-08-30, and I reported the result to
  the maintainer before re-measuring it.) Sweeping every tab for
  controls stretched to the window returned 640px for a Save button, a
  Load button, a Clear button, two combos and a spin box across three
  tabs -- and 640px was the PAGE WIDTH. Those pages had never been
  current, so nothing in them had been through a layout pass and every
  child reported its parent's size, which reads exactly like a control
  with no width of its own. (C-156.)
- **A `processEvents()` LOOP LETS NO WALL TIME PASS, so a QgsTask never
  finishes.** (Same day.) A probe pumped four hundred iterations waiting
  for the topology build and concluded no topology could be built -- on
  a design whose own `can_build` answered True. (C-157.)
- **A TEST'S POSITIVE CONTROL CAN BE THE DEFECT YOU ARE ABOUT TO FIX.**
  (Same day.) `test_no_design_control_is_stretched_to_the_ window`
  proved its own measurement was live by asserting the region chooser
  DOES take the width, "meant to take the width going". (C-158.)
- **A LAYOUT PASS THAT WIDENS WHAT IT MEASURES IS A FEEDBACK LOOP; A
  MARGIN IS NOT.** (Same day, and it is the fourth failed repair to this
  one layout.) Two form blocks stacked in a QVBoxLayout end their label
  columns a few pixels apart, because a group box frames its own form
  and that inset is unknowable before a layout pass. (C-159.)
- **A STACKED WIDGET'S MINIMUM IS THE LARGEST OF ITS PAGES, AND THAT IS
  WHY ONE TAB CAN SET THE WHOLE WINDOW'S SIZE.** (Same day, maintainer's
  ask that the first tab open narrower.) The Design tab needs 550px and
  Data & colours 1004 because of the assignment table, so the window
  opened at 1296 whichever tab was in front, and a floor of 1180px in
  `_fit_to_design` made sure of it. (C-160.)
- **WHEN A CONTROL'S PARAMETER COMES FROM A GESTURE, THE HANDLE SHOULD
  BE A POSITION AND NOT A DELTA.** (Same day, recorded before it is
  built.) A drag that reports how far it has travelled has to pass that
  through a LEVER to become a parameter, and the lever is a gain factor
  nobody can see: half the edge's length was too twitchy, the full
  length still turned a 35px drag into a scale factor of 0.28. Every
  such number is tuned by somebody guessing. (C-161.)
- **A COMPARATOR THAT IS SENSITIVE TO REPRESENTATION CANNOT ANSWER A
  QUESTION ABOUT APPEARANCE.** (2026-08-31, and it is the third wrong
  instrument in one function.) `_same_shape` exists to say whether a
  manipulation moved anything a person could see, and it asked
  `shapely.equals_exact`, which compares COORDINATE SEQUENCES: two rings
  covering identical ground read as different the moment one of them
  begins at another vertex. (C-162.)

- **AND AN EXACT QUESTION MUST NOT BE ASKED WITH A TOLERANCE.** (Same
  day, the other half of the same defect.) Whether a design holds the
  class an edit names is answerable EXACTLY, from the topology, by name,
  before any geometry exists. (C-163.)

- **A FINISHED JOB'S LOG IS READABLE WHILE ITS RUN GOES ON.**
  `gh run view --log-failed` refuses until the whole RUN completes,
  which on this project means waiting for hour-long siblings; `gh api
  repos/<owner>/<repo>/actions/jobs/<id>/logs` returns a completed
  job's output immediately. That is the difference between a
  fifteen-minute diagnosis and an hour of waiting, and it is what the
  platform probe's speed is worth in practice. Pass
  `--allow-escape-sequences` and strip them.

- **A GUARD THAT COMPARES THREE OF TWENTY-SIX FIELDS IS A SECOND
  DEFINITION OF THE THING IT GUARDS, AND IT GOES STALE.** (2026-08-31,
  and TWO hunts found it independently by different routes -- the most
  this method has converged here.) The save's staleness guard asked
  whether "the design on screen is the one the map was drawn at" by
  comparing family, element count and the topology edit list, while the
  KEY it writes beside the motif hashes `_topology_stamp()` -- the
  spacing and every modifier included. (C-164.)

- **A SINGLE-SHOT TIMER THAT IS "DROPPED" IS LOST, NOT LATE -- AND THE
  COMMENT SAYING OTHERWISE IS THE WORSE HALF.** (Same day, in a repair
  written hours earlier by the same hand.) A gate refusing a live tick
  while a save writes returned without re-arming `_live_timer`, which is
  `setSingleShot(True)` and had just FIRED to reach the gate; its only
  two `start()` sites are a fresh control change and `_finish_run`.
  (C-165.)

- **A `ResizeToContents` COLUMN RE-MEASURES ON EVERY `setItem`.** (Same
  day, and it was a regression introduced by that morning's own fix.)
  The Messages tab's answer column was pushed off the viewport, so three
  columns were given resize MODES -- which cured the layout and cost ten
  to eighteen SECONDS per message once the log reached its 500-row
  ceiling, on the main thread, with live update making the plugin speak
  on every tweak. (C-166.)

- **AN ENTRY MUST BREAK THE ROUTE THE GUARD WALKS, NOT A ROUTE.** (Same
  day, twice, and it cost four attempts on one entry.) A gate was given
  three callers -- the shelf writer, the family handler and the
  element-count handler -- and an entry mutating any ONE of them
  survived, because changing the element count REPOPULATES the family
  list and the family handler re-asks anyway. (C-167.)

- **`mutation_check` MUST RUN ITS CHILD OFFSCREEN, AND THE DOCUMENTED
  INVOCATION DID NOT.** (Same day, three diagnostic rounds.) The command
  this file gives -- `env -u PYTHONHOME -u PYTHONPATH python3
  tools/mutation_check.py` -- passes no `QT_QPA_PLATFORM`, while the
  suite always sets `offscreen`. (C-168.)

- **WHEN YOU ADD A STEP TO A SEQUENCE, ASK WHAT IT RESETS.** (Same day,
  found by a hunt auditing a harness rather than a product.) The
  topology matrix grew a baseline Generate, placed between choosing a
  manipulation and clicking Apply. (C-169.)

- **A DEDUPE WRITTEN FOR AN UNREACHABLE HARM IS DELETED, NOT KEPT.**
  (Same day.) `_report_quietly` does not deduplicate, so a new notice on
  a gate reachable from every live tick looked certain to repeat -- a
  warning that fires constantly being one people learn to ignore.
  (C-170.)

- **RE-WRAPPING A PARAGRAPH DISARMED A PROSE GATE.** (Same day.) A guard
  finds a sentence in the user guide with a regular expression whose
  gaps were mostly literal spaces. Correcting a number made the word
  shorter, the paragraph was re-wrapped to tidy the ragged line, and the
  newline landed between "fifty-six" and "for a tiling" -- where a
  literal space cannot match. (C-171.)

- **A DOWNLOADED ARTEFACT HAS A FRESH MTIME AND AN OLD RESULT.** (Same
  day, the nineteenth watcher fault here and a new road.) The night's
  beat picks the newest failing log with `find -mmin -240`, which is the
  right guard against a glob sweeping up every run there has ever been
  -- and it assumes mtime is when the WORK happened. (C-172.)

- **A TRIPLE-BACKTICK FENCE SHIFTS EVERY INLINE SPAN BELOW IT, AND A
  PROSE GOES BLIND FROM THERE DOWN.** (2026-08-31, found by re-reading
  the procedural documents at the maintainer's asking, which is a
  direction docs/process/HUNT-RECORD.md carries a row for.) A fence line
  carries THREE backticks; a span pattern needs a non-backtick between a
  pair, so the first two cannot pair and the THIRD opens a span running
  to the next backtick. (C-173.)

- **WHEN ONE FUNCTION IS MADE THE OWNER OF "WHAT IS X", CHECK EVERY
  OTHER KEY FOR TERMS THAT WERE NEVER X TERMS.** (2026-08-31, found by
  TWO hunts independently -- one from the boundaries, one backwards from
  harm.) `_capture_design` was extracted that morning as the one answer
  to "what is the design", and the save's staleness guard was moved onto
  it. (C-174.)

- **AN ARMED TIMER IS NOT A RUN THAT WILL START.** (2026-08-31.)
  `_queue_live` arms the live timer on every output-affecting change
  WHATEVER the checkbox says, and `_maybe_live_generate` then declines
  at its second gate. (C-175.)

- **A GATE THAT OPENS A DOOR MUST ASK FOR WHAT IS BEHIND IT.**
  (2026-08-31, found by two hunts independently.) `opt_experimental`
  reached `_gate_experimental_tabs` and a touch counter; the topology
  build runs only from `_rebuild_unit`. (C-176.)

- **A HAND-KEPT LIST DRIFTS EVEN WHERE A COMMENT SAYS TO KEEP IT IN
  STEP.** (2026-08-31, twice in one day.) `check_standards.USER_FACING`
  decides which files the hard rules are enforced over, and its own
  comment asks that it match `text_review`'s SOURCES and DOCUMENTS.
  `metadata.txt` joined the review queue on 2026-08-12 and never joined
  this one -- so the `changelog=` and `about=` entries, which QGIS's
  plugin manager displays and which `release_notes.py` puts at the top
  of the GitHub release body, were unchecked for a HARD RULE and for
  Canadian spelling. (C-177.)

- **A WANTED WRITE THAT FAILS STILL CLEARS, SO ENABLING THE WRITE IS
  HALF A REPAIR.** (2026-08-31, and it is the third failed repair to one
  method in one day.) `_write_or_drop_the_topology` refused to write a
  motif while the experimental box was unticked, and stopping it asking
  the box changed nothing observable: on the commonest journey nothing
  has BUILT a topology, so `wanted` stayed false. (C-178.)

- **A TEST THAT MATCHES A PHRASE COPIED OUT OF THE PRODUCT IS BROKEN BY
  THE MAINTAINER'S OWN EDIT.** (2026-08-31, and the route is new.) An
  arm counted messages containing `"cannot carry"`. The maintainer
  reworded that notice, `tools/text_review.py --apply` wrote the new
  sentence into the source, and the filter matched nothing -- so the arm
  counted zero and its "at most once" assertion held whatever the code
  did. (C-179.)

- **UPSTREAM MOVED TWELVE COMMITS WITHOUT BUMPING ITS VERSION, AND FIXED
  ONE OF OUR FINDINGS.** (2026-08-31.) The vendored stamp reads
  `0.0.7.89 (bf1bbbf)`; upstream's head is `6190917` with `topology.py`
  at +179/-207 and `_tiling_geometries.py` at +44/-67 -- and the version
  string is `0.0.7.89` at BOTH ends. (C-180.)


- **A CONTROL'S SHAPE SHOULD SAY WHAT IT DOES, AND A HOVER STATE IS NOT
  A SUBSTITUTE.** (Maintainer's rulings, 2026-08-31, on finding the
  Topology tab unusable: it "should be easy to use and easy to learn",
  it "has to be perceivable", and "hover states aren't as good as shapes
  that make sense ... like visually make sense for what they do".) The
  tab's handles were a square, a circle and a diamond whose meanings
  existed only in the source. (C-181.)

- **PROFILE THE THING A PERSON WAITS FOR, BECAUSE THE COST IS OFTEN NOT
  WHERE THE SUBJECT IS.** (2026-08-31, asked whether the symmetry work
  could speed up tiling the plane.) It cannot -- covering the plane is
  TRANSLATION, and that half is already vectorised: 191,184 tiles are
  built in 2.7s of numpy and STRtree, which is upstream having taken
  this project's own optimisation. (C-182.)

- **THE VENDOR-CLAIM GATE READS "commit <sha>" ANYWHERE IN THREE FILES,
  SO WRITING ABOUT SOMEBODY ELSE'S COMMIT TRIPS IT.** (2026-08-31, met
  while mending the claims the re-vendor had made stale.)
  `check_vendor_claims` compares every `commit <hex>` in README.md,
  MAINTAINING.md and CLAUDE.md against the stamp -- which is what makes
  it catch a document naming the vendor's old commit, and what makes it
  complain about a sentence that merely MENTIONS another one. (C-183.)

- **A RE-VENDOR'S REAL QUESTION IS ONE NO GATE HERE ASKS.** (2026-08-31,
  upstream bf1bbbf to 6190917.) The colourspace comparison scores the
  plugin against `TiledMap.render` from THE SAME vendored library, so a
  change upstream moves both sides together and they go on agreeing --
  "a differential cannot see a fault its expected side shares", arriving
  at the dependency. (C-184.)

- **THE TWENTIETH AND TWENTY-FIRST WATCHER FAULTS ARE ONE RULE: KEY ON
  THE THING, NOT A SNAPSHOT OF IT.** (2026-08-31, both mine, both within
  ten minutes of arming a watcher, and both while the candidate was
  building.) This file already carries that rule from 2026-08-12, where
  a poller pinned to one commit sha sat silent while two more pushes
  superseded it. (C-185.)

- **THREE MORE FROM THE SAME MORNING, ALL CAUGHT BY HAND-RUNNING THE
  WATCHER ONCE BEFORE ARMING IT.** That is the practice this file has
  been recommending since the tenth fault, and it is the first time it
  has been done here before rather than after. (C-186.)

- **A DOCUMENTATION MERGE IS NOT A NO-OP FOR THE SUITE.** (Same day.)
  `test_every_documented_command_still_exists` opens CLAUDE.md,
  MAINTAINING.md, README.md and ROADMAP.md, which is exactly why those
  four are in `STAGE_DEPENDS` -- a documentation edit really can break a
  test, and it is the kind of change that feels as though it cannot.
  (C-187.)

- **THE ENTRY DESCRIBING THE FENCE FAULT IS WHAT BLINDED THE GATE
  NEXT.** (2026-08-31, hours after the fence repair, and found by
  planting a control rather than by reading.) This morning's lesson was
  written as a bullet opening `- **A ` followed by three literal
  backticks and the word FENCE. `_prose_outside_fences` toggles only on
  a line that STARTS with the fence, and that line starts with a dash --
  so the three backticks stayed in the prose, and three is ODD. The span
  pattern pairs positionally over the whole document, so from that line
  to the end of the file every backtick pairs with the wrong neighbour.
  (C-188.)

- **`lines[-1]` ON A FILE ENDING IN A NEWLINE REPLACES THE EMPTY STRING,
  SO THE EDIT APPENDS INSTEAD OF REPLACING.** (2026-08-31, and it
  reached the point of publication.) A paragraph of a candidate's
  release notes was rewritten by assigning to `lines[-1]` after
  `read().split("\n")`. (C-189.)

- **A WATCHER'S HEADLINE MUST CARRY WHAT IS LIVE, NOT WHAT MATTERS IN
  GENERAL.** (2026-08-31, the truncation fault three times in one day
  and the third is the interesting one.) A notification is TRUNCATED, so
  a line below the cut is a line nobody reads. (C-190.)

- **A WIDGET INSIDE A LAYOUT DOES NOT KEEP A SIZE YOU HAND IT, SO THE
  WINDOW IS THE LEVER.** (2026-08-31, and THREE of four failed attempts
  at one guard turned on this alone.) A test that resizes a child to its
  own floor measures nothing: the layout hands that child whatever is
  left over on the next pass, and the resize is gone before anything can
  read it. (C-191.)
- **A FLOOR ON ONE PANE IS TAKEN OUT OF THE PANE BESIDE IT.** (Same
  day.) The Topology tab's drawing had a 180px floor and got exactly
  180px of an 825px window, because the column of controls beside it
  claims its own preferred width first -- so the floor was not a floor
  but the whole allowance. (C-192.)
- **TWO SUFFICIENT FIXES TO ONE OUTCOME MAKE EVERY SINGLE-SITE ENTRY
  SURVIVE, AND THAT IS INFORMATION.** (Same day, four attempts before
  the question was put the right way round.) Two independent repairs
  kept a pair of handles outside the hit test's reach, and the test
  asserts the OUTCOME, so mutating either one left the assertion true.
  (C-193.)
- **A SETTLE RETURNS BEFORE THE RESULT IS ADOPTED, SO A PREMISE ASKED IN
  THE SAME BREATH READS THE OLD STATE.** (Same day.) A guard asserted,
  immediately after waiting for the topology build to go quiet, that the
  design no longer carried a topology -- and the assertion failed while
  a direct measurement of the very same dialog said it should pass.
  (C-194.)

- **A FIX APPLIED WHERE THE FAULT CANNOT BE REACHED IS DEAD CODE THAT
  READS AS PROTECTION, AND I WROTE ONE WITHIN AN HOUR OF WRITING THE
  RULE'S OTHER HALF.** (2026-09-01.) A margin pass returned early for
  want of a layout pass, under a comment promising to try again later
  while nothing scheduled a later, so it was taught to re-arm a timer.
  (C-195.)

- **AN OWNERSHIP QUESTION THAT OUR OWN ACT MAKES TRUE IS NOT AN
  OWNERSHIP QUESTION.** (2026-09-01, found by the stochastic hunt and
  widened by a second.) `_this_map_owns_the_file` answers True as soon
  as the file is in `_gpkg_tables_written`, which OUR FIRST PRESS puts
  there -- so a colleague's GeoPackage is theirs on press one and ours
  on press two, and every remover gated on that answer was handed a
  licence on the second press. (C-196.)

- **AND THE FIRST REPAIR FOR IT SPARED EVERYTHING, BECAUSE THE RECORD
  DOES NOT SPELL IT `variable`.** The drop was taught to name candidates
  from the file's own record rather than match them by prefix, composing
  table names through `bridge.element_table_name` from
  `element.get("variable")` -- a key `WORKING_STATE_ELEMENT` does not
  have, since it is `var`. (C-197.)

- **A WIDGET THAT RE-DERIVES ITS VIEW TRANSFORM FROM WHAT IT DRAWS HAS
  MADE THE TRANSFORM AN OUTPUT OF THE GESTURE.** (2026-09-01, reported
  by a hunt from the pixels and verified here from the numbers.) The
  Topology view fits to what it is drawing, and during a drag that is
  the PREVIEW; a drag freezes its origin and the unit's span at the
  press and reads later positions as fractions of that frame. (C-198.)

- **THE DESIGN A CLAIM IS DRIVEN ON CAN REFUTE A REAL DEFECT.**
  (2026-09-01, twice in one afternoon, both mine.) A vertex drag past
  its control's range records an out-of-range value on `archimedean
  4.8.8` and cannot on `laves 3.3.4.3.4`, where the library refuses the
  oversized nudge before anything is recorded; and a drag's frame drifts
  when a VERTEX is held and not when an EDGE is scaled, since only the
  first grows the extent the fit re-measures. (C-199.)

- **AND I COMMITTED PAST A RED GATE, HAVING READ IT.** (2026-09-01.)
  `check_standards` printed exit 1 and the commit ran anyway, because
  the chain was `check; echo; git commit` and the commit branched off
  the ECHO. That is this file's own entry about a gate whose exit nobody
  branches on, made by somebody who had quoted it the same day. (C-200.)

- **A LANDING THAT ARRIVES MID-GESTURE MUST WAIT FOR THE POINTER TO COME
  UP.** (2026-09-01, found FROM A RUNNER.) `show_topology` clears the
  drag preview and the chosen thing, which is right for a rebuild and
  wrong while somebody is dragging: a topology build finishing under
  their hand put the un-edited design back, dropped the highlight saying
  what they were aiming at, and left the drop to commit an edit out of a
  record they could no longer see. (C-201.)

- **THE SIX DECISIONS OF 2026-09-01, SETTLED BY GRILLING.** All four
  approved features go into 0.24.4 on the maintainer's decision, and
  each was put with a measurement rather than an opinion; the
  measurements are recorded because they are what a later session will
  not have.
  MULTI-CLASS SELECTORS: CLICK TO SELECT, A LIST TO CONFIRM, each
  following the other with the blocked-signal discipline the pin
  controls already carry. What decided the shape was how much there is
  to select: across a 48-design spread most designs carry ONE OR TWO
  transitivity classes of each kind, and where there are two the
  chooser's per-class entries plus "every vertex" and "every edge"
  already cover all three subsets, so the feature only bites on the
  eight of 48 with three or more -- `hex-slice 5` at 5 vertex and 7
  edge classes being the richest. The record needs nothing: an edit's
  `classes` is already a STRING selector and the library matches
  `label in selector`.
  CAIRO IS A RENAME, NOT A FAMILY. Measured through `catalog.make_unit`,
  `tiling_type="cairo"` and the catalogue's own `laves 3.3.4.3.4` draw
  the SAME GROUND -- four tiles, ids a-d, identical areas and bounds,
  symmetric difference 0.000 -- so one entry reads `laves 3.3.4.3.4
  (cairo)` and the well-known Archimedean and Laves names come with
  it, through `text_review` like any other prose.
  **AND THE MECHANISM IS THE LABEL/KEY SEPARATION THIS FILE ALREADY
  PREACHES.** `family_combo` is built with `addItems(names)`, so the
  catalogue name does duty as label AND identity, and
  `WORKING_STATE_DESIGN` stores `family` as the combo's TEXT -- which
  is why renaming an entry looked as though it would orphan every
  saved GeoPackage. Items carry the catalogue KEY as item data and
  show a LABEL; the record goes on storing the key; every saved file
  restores unchanged and the next rename costs nothing. This is "a
  name you show is not a name you look up by" arriving at the
  catalogue, where it had never been applied.
  THE DUAL IS BUILT HERE AND OFFERED UPSTREAM. `Tileable.__init__`
  delegates to `_setup_tiles()`, which dispatches on `tiling_type` and
  has NO path for supplied geometry, so assembling a Tileable from
  `Topology.get_dual_tiles()` means setting the fields upstream's own
  setup would set -- the vendoring boundary. It goes in behind one
  function with the measurement and the removal criteria at the site
  and a canary that fails the day the library grows a real
  constructor, AND goes up as a patch, which is the route the STRtree
  optimisation took and came back merged.
  THE SYMMETRIES: DRAWN, GATING, AND REPORTED. `Topology` already
  holds `tile_matching_transforms` and `Symmetries(polygon)` gives a
  tile's group code, but `plot_tiling_symmetries` draws through
  matplotlib, which cannot run inside the signed QGIS process on
  macOS -- so the drawing is OURS, in the view's painter, from
  upstream's data. The gating is the symmetry note's own finding: a
  vertex whose stabiliser contains a rotation has only the zero
  displacement available, so a control that cannot move the selection
  is greyed WITH ITS REASON rather than offering a rail of zero
  length. Necessary and not sufficient -- laves class B has a
  one-dimensional fixed space and still yields nothing -- so the gate
  says what it measured.
  THE ELEMENT SLIDER KEEPS ITS RANGE AND THE FLIP SPEAKS. Weave
  families run n=2 to 12 and tilings to 256, so from 13 up only
  tilings exist and `test_design_cascade` requires the toggle to flip.
  Capping the track would have to cap the spin box with it, since the
  count is one control in two widgets, and would retire that contract
  along with the route by which somebody on weaves meets the tilings
  above. Crossing 12 on a weave SAYS what it did, in the sentence
  family the switch door was given on 2026-08-26.

- **A RECORDED "DECISION" IS A HYPOTHESIS TOO: CHECK IT IS STILL ONE
  BEFORE PUTTING IT TO ANYBODY.** (2026-09-01, and it is this file's
  own rule about inventing questions, met from the other side.) The
  roadmap carried an open question -- does `publish_candidate` require
  every workflow, or every workflow whose red would stop a release --
  whose stated worry was that a genuine sampling survivor would one
  day block a candidate and start the `--despite-ci` habit. It cannot.
  Every measuring step in `mutation.yml` is `continue-on-error`: the
  catalogue sweep, `mutate_auto` on changed lines, the census and the
  gallery render. What CAN redden that workflow is provisioning, the
  baseline check, an artefact upload, or the coverage leg, which
  checks each shard's exit and refuses a partial record -- and the two
  reds of 2026-08-31 were both that leg. So the gate already means
  what the 2026-08-11 decision says. ASK OF ANY RECORDED QUESTION
  WHETHER ITS PREMISE STILL HOLDS before spending somebody's attention
  on it; a question written months ago describes the software of that
  day.

- **A FIGURE WITH NO INSTRUMENT BESIDE IT IS FOLKLORE, AND A READER WILL
  SAY SO.** (2026-09-01, from a colleague reading the symmetry note.)
  Their two comments were "I have no idea what code it's running to find
  that the hex 7-colouring is especially egregious" and "what did it do
  with the rough implementations it claims to have written". (C-202.)

- **THE TWENTY-SECOND WATCHER FAULT WAS CAUGHT BEFORE ARMING, WHICH IS
  THE FIRST TIME.** (2026-09-01.) `gh` reads the repository from the
  WORKING DIRECTORY, so a watcher launched from a scratch folder asks
  about nothing, gets an empty answer, and reports nothing -- which is
  indistinguishable from a quiet branch. (C-203.)

- **AND ALL FOUR WERE BUILT THE SAME DAY, with what each turned out to
  cost.** (2026-09-01, after the grilling above.) THE LABEL/KEY
  SEPARATION WAS THE ONE THE OTHERS SAT ON, and it touched more than the
  catalogue: `family_combo` was built with `addItems(names)`, so 13
  product sites and 121 suite sites treated the chooser's TEXT as the
  design's identity. (C-204.)

- **OPENING A GEOPACKAGE COSTS TIME PROPORTIONAL TO ITS LAYERS, AND A
  HELD HANDLE DOES NOT ANSWER IT.** (2026-09-01, measured against GDAL
  directly for the first time.) That sentence had stood in four
  documents since 2026-08-29, INFERRED from the shape of the save's own
  growth rather than asked of the dependency -- a cause named by
  reading, which reads exactly like one somebody proved. (C-205.)

- **A COMPARISON ACROSS TWO RUNS ON A BUSY MACHINE IS NOT A
  MEASUREMENT.** (Same day, and it nearly put a wrong number in a commit
  message.) A 32-element save read 1.1s in one run and 2.9s in the next
  ON IDENTICAL CODE, with the machine's load average between 18 and 37
  all session. (C-206.)

- **OGR HANDS BACK A DATETIME IN ITS OWN FORMAT, SO A VALUE COPIED OUT
  OF A ROW IS A DISPLAY RATHER THAN WHAT WAS STORED.** (Same day.)
  Writing this project's own `layer_styles` rows meant reproducing what
  QGIS puts there, so the columns were read off a file QGIS had written
  -- and the update_time copied from that reading was OGR's rendering,
  not the stored text. (C-207.)

- **NOTHING ENDS WHILE A SAVE IS OUTSTANDING.** (Maintainer's ruling,
  2026-09-01.) A quit or a window close met a save that had been
  promised and not yet written, and dropped it: `closeEvent` cleared
  `_save_pending` with nothing said. So a waiting window now holds
  both doors, says what it is waiting for, and offers Cancel; a quit
  is DELAYED rather than vetoed, because refusing outright leaves
  somebody unable to leave QGIS if a save ever wedges. TWO THINGS
  WERE PUT AS QUESTIONS AND ANSWERED, and both would have cost a map
  if guessed: Cancel abandons the save and lets the quit through, and
  "save it" at a close means WAIT FOR THE REDRAW rather than write
  what is on screen -- the press was deferred precisely because the
  map on screen is the one they had changed away from. Account in
  MAINTAINING.md under "Nothing ends while a save is outstanding".
  AND CANCEL IS CERTAIN ONLY BEFORE THE WRITING STARTS, which is said
  at the line rather than implied: a cancel mid-write needs
  `write_gpkg_layers` to take a stop callback, and until it does, a
  button offered there would be a button that lies.

- **ONE STORE, ONE MEANING -- AND A QLabel IS A STORE.** (2026-09-01.)
  The Topology tab was given a sentence saying a build was coming, and
  it went into `note`, which already means "the answer, or the reason
  there is none". (C-208.)

- **A HARNESS THAT MATCHES A SENTENCE THE PRODUCT SAYS IS RETUNED BY THE
  NEXT SENTENCE.** (Same day, and it had been true of every save test in
  the suite.) `press_save` waited out a deferred press by matching "will
  be saved afterwards" in what the plugin said. (C-209.)

- **A GUARD OVER THE WHOLE TREE CANNOT TELL YOUR OWN EDIT FROM WHAT IT
  IS WATCHING FOR.** (Same day, twice in one hour.) A chain proving
  catalogue entries asserted the tree was restored by asking `git diff
  --quiet` over everything, and stopped on a document I had regenerated
  myself twenty minutes earlier. (C-210.)

- **A WATCHER'S OWN SHELL IS PART OF THE WATCHER, AND `/bin/bash` HERE
  IS 3.2.** (2026-09-01, the twenty-third watcher fault.) A standing
  beat tracked "failures I have already reported" in an associative
  array. (C-211.)

- **A WATCHER KEYED TO ONE RUN ENDS WITH THAT RUN.** (Same evening.)
  The beat armed over a sharded suite was correct and useful, and when
  the suite was stopped it stopped too -- leaving nothing watching the
  work that followed, at the exact moment the maintainer asked where
  the watcher was. A watcher over a JOB and a watcher over the SESSION
  are different instruments: the second reports what is running, says
  "nothing running" in those words rather than going quiet, and
  outlives any single measurement.

- **A FLAG READ BY ONE CONSUMER OUTLIVES THE JOURNEYS THAT CONSUMER
  NEVER RUNS ON.** (2026-09-01, found by writing the guard for a button
  added the same day.) The waiting window's Cancel sets
  `_save_cancelled`, which `write_gpkg_layers` reads BETWEEN TABLES and
  answers with a rollback. (C-212.)

- **WHEN A NAME GAINS A LABEL, SWEEP EVERY READER OF THE QUESTION, AND
  THE SILENT ONES FIRST.** (Same day.) The label/key separation of the
  morning gave `laves 3.3.4.3.4` the displayed name `laves 3.3.4.3.4
  (cairo)`, and the product moved cleanly: items carry the key as data,
  records store the key, one owner answers "which design is this".
  (C-213.)

- **AN ENVIRONMENT SCRIPT THAT PRINTS BARE ASSIGNMENTS NEEDS `set -a`,
  OR THE CHILD NEVER SEES THEM.** (Same day, caught before it cost
  anything.) `tools/macos_qgis_env.sh` prints KEY=value lines, so a
  plain eval sets SHELL variables and exports nothing -- and the run
  then dies with "No module named 'encodings'" while the shell believes
  PYTHONHOME is set, which reads as a broken interpreter rather than a
  missing export. (C-214.)

- **A CANDIDATE'S OWN SUITE IS READ SHARD BY SHARD, AND THE PARTITION IS
  THE PROOF.** (2026-09-01, the rc10 candidate.) The stage line says one
  number and the log carries three: 250, 249 and 249 tests, each shard
  naming the SAME total of 748. That agreement is what makes a slice a
  partition rather than three overlapping runs -- the first sharded run
  this project ever made read 285, 285 and 286, and slices that disagree
  about the size of the whole mean something ran twice or not at all.
  (C-215.)

- **A DOCUMENTATION EDIT CANNOT INVALIDATE A CANDIDATE, AND KNOWING THAT
  IS WHAT MAKES THE HOUR AFTER ONE USABLE.** The receipt digests exactly
  the files that SHIP, taken with `build.py`'s own `shipped_files()`,
  and it deliberately ignores tests, tooling and documentation --
  because those cannot change what a reviewer installed, and a gate that
  fired on a comment in the suite is a gate people learn to route
  around. (C-216.)

- **A WORKFLOW'S NAME IS NOT ITS CONTRACT, AND THIS ONE HAS BEEN MISREAD
  TWICE.** (2026-09-01, on the maintainer asking whether the mutation
  gate had been tightened.) It had not, and nothing about it had moved
  since 2026-08-19. Read off `.github/workflows/mutation.yml` rather
  than off the prose about it: both measuring steps carry
  `continue-on-error`, so no survivor can redden that workflow and the
  decision of 2026-08-11 holds exactly as written. (C-217.)

- **CHECK YOUR OWN ARITHMETIC BEFORE REPORTING A PARTITION AS
  BROKEN.** (Same day.) I read a summary log and made the shards sum
  to 749 against a local 748, and said so -- which under this
  project's own rule means something ran twice or not at all. Asked of
  the shard logs themselves, all three say "of 748" and 250 plus 249
  plus 249 is 748. The partition was exact and the discrepancy was
  mine. A suspected instrument fault is still a claim, and it wants
  the same measurement as any other before it is written down.

- **AND I EDITED A DOCUMENT THE RUNNING SUITE READS.** (Same day, and it
  is the tree-lock rule with the roles reversed.) That rule is usually
  stated about SOURCE -- do not edit what a gate is measuring -- and
  `STAGE_DEPENDS` names CLAUDE.md, MAINTAINING.md, README.md and
  ROADMAP.md for exactly this reason: `test_every_documented_
  command_still_exists` opens them, so a documentation edit really can
  turn a running candidate red, and it is the kind of change that feels
  as though it cannot. (C-218.)
- **AN INSTRUMENT THAT DIES AFTER REPORTING LOOKS EXACTLY LIKE THE THING
  IT MEASURES DYING.** (2026-09-01.) A two-arm probe printed both its
  readings and then took a SEGMENTATION FAULT at interpreter teardown,
  holding dialogs alive past `exitQgis`. (C-219.)
- **A DEPENDENCY THAT ANSWERS BY RETURN VALUE CANNOT BE CAUGHT BY
  `except`.** (2026-09-02, and it was the sharpest defect of the
  campaign's first day.) `write_gpkg_layers` wrapped its commit in a
  `try`, with a comment explaining that a commit which will not go
  through leaves the file as it was. (C-220.)
- **A WAIT ONLY AN OUTER FRAME CAN END IS NOT A WAIT.** (Same day.)
  `_save_the_map` turns the event loop once per element behind its
  progress bar, so a close or a quit arriving during a write is
  delivered by THAT WRITE'S OWN PUMP -- and the hold it reaches then
  runs NESTED INSIDE the write, spinning until `_saving_now` clears,
  which only the suspended frame beneath it can do. (C-221.)
- **AN "EMPTY" FILE IS A QUESTION ABOUT CONTENT, NOT ABOUT BYTES.**
  (Same day.) The ownership question decided whether a GeoPackage was
  somebody else's with `os.path.getsize(path) > 0`, and a data source
  OGR has created and nothing has written to is 65,536 bytes of header
  holding no layer. (C-222.)
- **A TABLE KEYED BY A FAMILY DOES NOT GROW WITH THE FAMILY.** (Same
  day.) `_drag_moved` answers "did this gesture ask for anything" per
  manipulation, because each has its own idea of nothing -- zero travel
  for a nudge, half a degree for a rotation, one per cent for a scale.
  (C-223.)
- **A PREDICATE THAT MERGES TWO FACTS IS RIGHT FOR A WAIT AND WRONG FOR
  A QUESTION.** (2026-09-02, found by two hunts independently and from
  opposite directions, which is the strongest confirmation this method
  produces.) `_a_save_is_outstanding` answers "is there a save that has
  been asked for and not finished", deliberately merging a PROMISE made
  with the KEEPING of it, because to the person who pressed the button
  they are one act. (C-224.)
- **A FRAME MUST NOT REPORT THE OUTCOME OF AN ACT IT CANNOT SEE.** (Same
  day, the other end of the same mechanism.) `write_gpkg_layers` asks
  `should_stop` BETWEEN TABLES, so a Cancel landing during the styling
  or the repointing -- 13.0s of a 256-element save -- cannot be served
  and the write finishes. (C-225.)
- **A FILTER IS A VIEW, AND `getFeatures()` HONOURS ONE.** (Same day,
  found by the specification hunt.) A person who sets a filter on an
  element layer in QGIS -- the Query Builder in Layer Properties -- had
  every tile it hides written OUT of their saved GeoPackage at the next
  Save, permanently, under the word "Saved". (C-226.)
- **A RECORD FILLED BY A LANDING AND CLEARED BY NOTHING ANSWERS FOR A
  MAP IT HAS NEVER SEEN.** (Same day, found by backwards-from-harm at
  the end of a list that had ranked it fifteenth.) `_element_tables` is
  written when a map LANDS and cleared by neither the Load door nor a
  group switch, so a session that has drawn any map carries THAT map's
  table names -- and an opened map's elements share their ids with it.
  (C-227.)
- **AND WHEN A RESUME STAMPS ONE STORE, IT STAMPS THE OTHER.** (Same
  day, found by the hunt aimed at the same morning's repairs, which is
  that direction's eleventh outing for eleven.) A resume stamps the
  GROUP's record with the region the recovery LANDED ON, and it must: a
  self-contained file records the SENDER'S own path and nothing on the
  recipient's machine answers to it. (C-228.)
- **AND A DEPENDENCY'S REFUSAL CAN STOP BEING TRUE WHILE THE RULE IT
  JUSTIFIED STANDS.** Measured 2026-09-02 with the plugin out of the
  way: a `QgsVectorLayer` on `path|layername=tiles_b_v1`, copied into
  `tiles_b_v1` through an open OGR update transaction the way
  `bridge._write_one_layer` does, wrote 40 of 40 features, raised
  nothing, and committed `OGRERR_NONE`. (C-229.)
- **THE TWENTY-FOURTH WATCHER FAULT: A JOB NAME HAS A SPACE IN IT.**
  (2026-09-02, mine, in a watcher armed at the maintainer's asking to
  reach a green candidate.) The reading was `for job in $JOBS` over
  lines like `suite (4.0.3)=success`, which the shell splits at the
  space -- so every line arrived as `tests (4.0.3)=success` and there
  was no telling the SUITE from the INSTALL. Both are green far more
  often than not, so the log read plausibly and said nothing. (C-230.)

- **A LAUNCH STATE BEATS THE CARRY, SO HANDING A KEY OVER IS NOT THE
  SAME ACT AS LETTING IT FALL THROUGH.** (2026-09-02, ledger rows 22 and
  23, and the second is my own repair's defect found within the hour by
  the hunt replenished onto it.) `_stamp_working_state` merges a launch
  state OVER the record already on the group, so a resume that hands
  `region_crs` across unconditionally stamps the FILE's answer onto a
  group whose own record a LANDING wrote. (C-231.)

- **A KEY THAT ENUMERATES TWO OF A DESIGN'S TERMS IS A SECOND DEFINITION
  OF THE DESIGN.** (2026-09-02, ledger row 24, and THREE hunts of one
  round reached it from three directions -- backwards from harm, the
  specification itself, and the stochastic sessions, which is the
  strongest confirmation this method produces.)
  `topology_edits.shelf_key` was the family and the element count, and
  "Map the dual instead" moves neither -- so a design and its dual
  shared one shelf, and an edit made on the dual was replayed onto the
  design's own like-named edge the moment the box came off. (C-232.)

- **A QUESTION BUILT ON A MERGED PREDICATE MERGES THE SAME TWO STATES.**
  (Maintainer's ruling, 2026-09-02: "a panel's close button shouldn't
  stop a save, it should prompt whether to interrupt save".) Ledger row
  5 mended `_a_save_is_outstanding` for merging a promise with the
  keeping of it -- right for a WAIT, wrong for a QUESTION -- and the
  repair taught the Close arm to stop a write. (C-233.)

- **A CONTROL ONE ACT MOVES AS A SIDE EFFECT IS READ BY ANOTHER ACT AS A
  DECISION.** (Maintainer's ruling, 2026-09-02: "the save should happen
  first. then the load".) A Save kept while a re-tile is coming is a
  promise, and `_honour_a_queued_save` re-reads the output chooser at
  the moment of the write so that somebody who changes their mind about
  where the map goes is obeyed. (C-234.)

- **THE TWENTY-FIFTH WATCHER FAULT: ARMED THROUGH A PIPE, AND THE LESSON
  WAS MINE FROM THAT MORNING.** (2026-09-02.) A watcher was launched as
  its script piped into `tail`, which buffers to EOF -- so a watcher
  running perfectly well printed NOTHING, and the maintainer said so
  before any beat arrived. (C-235.)

- **A PROBE'S CONTROL CAN MOVE THE THING BOTH ARMS ARE ABOUT.**
  (2026-09-02, verifying row 24.) The control for "an ordinary design
  change moves the shelf key" changed the ELEMENT COUNT -- which
  repopulates the family list and lands on whatever that count offers,
  so `hex-slice 4#4` became `square-colouring 5#5` and every later
  reading was about a design nobody had chosen. (C-236.)

- **AN ASSERTION THAT NAMES A MOMENT IS A CLAIM ABOUT WHEN ITS OWN
  READING WAS TAKEN.** (2026-09-02, CI's coverage leg on rc13's own
  commit, and it spent that candidate.) `a build that lands mid drag
  does not wipe the gesture` failed on its main assertion rather than on
  a premise -- "the panel adopted a new topology mid-gesture" -- on one
  shard of three, each naming the same total of 772, while the same test
  passed in the candidate's own local suite. (C-237.)

- **A WAIT HELPER THAT DOES NOT WIDEN IS A CEILING SIZED ON THE FASTEST
  MACHINE THE SUITE WILL EVER RUN ON.** (2026-09-02, rc14, and it spent
  a second candidate in two days.) Every allowance in this suite is
  `CONTENTION` times something -- 2.5 for a sharded run times each
  platform's declared slowness, so a three-shard Linux job gets seven
  and a half times this Mac's patience. (C-238.)

- **`findData` COMPARES THROUGH QVariant, SO A TUPLE NEVER MATCHES AN
  EQUAL TUPLE.** (2026-09-02, and the first repair built on it changed
  nothing whatever.) The topology class chooser carries `(target,
  label)` as its item data; `combo.findData(wanted)` answers -1 for a
  pair that is plainly in the list, while the verb chooser's own
  `findData` beside it works perfectly -- because its data is a STRING.
  The repair looked right, ran, and the probe reported the identical
  before-and-after, which is the shape this file already names: a
  verdict that will not budge is almost always the instrument. (C-239.)

- **A LANDING IS HELD FOR A GESTURE, AND THE CLICK BEFORE THE PRESS IS
  NOT A GESTURE.** (2026-09-02, macOS CI at `743e73b`.) The ruling of
  2026-09-01 holds a build that lands mid-drag until the pointer comes
  up, and `gesture_in_progress()` is true from the press to the release
  -- so the window between the CLICK that chooses a class and the PRESS
  that grabs its handle is uncovered, and a landing there applies at
  once. (C-240.)

- **A PATCH THAT REWRITES ANOTHER PATCH'S OUTPUT TAKES ITS MARKER WITH
  IT.** (2026-09-04, found by the suite rather than by reading.)
  `vendor_weavingspace.py` decides whether a patch is already in a file
  by looking for its own `new` text, which doubles as the marker.
  (C-241.)

- **A RATE QUOTED FROM TOO FEW DRAWS IS NOT A MEASUREMENT, AND I
  PUBLISHED TWO.** (2026-09-04, chasing the topology matrix's one
  failing cell.) The cell reproduced on the second of two attempts, and
  I reported it as DETERMINISTIC; the next run of the same probe
  answered in 1.43s both times. (C-242.)

- **A GUARD CAN BE AIMED AT A STATE WITHOUT KNOWING WHAT PRODUCES IT.**
  (Same day, and it is the other half of the entry above.) The stall's
  CAUSE is undiagnosed -- QGIS accepts a topology build, leaves it
  `Queued`, and never starts it -- and the state it leaves was measured
  exactly: a task the dialog believes is in flight, reading Queued, with
  `active=0` on the pool. (C-243.)

- **CLEARING A PREVIEW AT THE DROP PUTS THE OLD PICTURE BACK FOR THE
  WHOLE OF AN ASYNCHRONOUS REBUILD.** (2026-09-04, a field report
  against 0.24.4rc15 confirmed and repaired.) `_commit_the_drag` opened
  by clearing the drag preview, which reads as tidy -- the gesture is
  over, so put the transient thing away -- and the answer that replaces
  it arrives SECONDS LATER off another thread. (C-244.)
