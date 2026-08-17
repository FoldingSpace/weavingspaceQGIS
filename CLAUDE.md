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
  list, so the two cannot drift apart quietly. It runs in a second,
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
  secrets take seconds, and the FUNCTIONAL SUITE IS THE THIRD STAGE,
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
  a twenty-four-minute macOS suite (the Linux legs take 52-54, and
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
  `dialog._add_output_layers`). "Create as new group" is the comparison
  escape hatch.
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
  it. (User instruction, 2026-08-09.)
  **THE GENERAL FORM WAS WITHDRAWN ON 2026-08-16 AND REPLACED BY A
  NUDGE. Read this before the history below it.** Reducing k re-samples
  the ramp: class i takes `ramp.color(i/(k-1))`, so a shorter ladder
  spreads its survivors across the whole ramp and every colour moves
  with nobody choosing to move it. Measured that day, five asked over
  four distinct values on Reds: the map drew the FOUR-class ladder
  exactly, and neither middle colour was one the five-class ladder
  would have used. It is also unstable -- a column that gains a value
  later re-colours every class -- which is the thing
  one-colour-one-meaning exists to forbid. The maintainer's rule is
  that an empty class is INVISIBLE, NOT DELETED.
  What cures the original symptom instead is
  `bridge._nudge_off_shared_bounds`: where the classifier has returned
  DEGENERATE ranges, every finite-width range's upper bound moves down
  by one unit in the last place. A value sitting on a shared boundary
  then falls past the interval swallowing it into the degenerate range
  that means exactly that value. On {1, 5, 9} at k=5 the values land
  in classes 1, 3 and 5, the highest wears the darkest colour, and the
  two empty classes are REAL numeric ranges -- so a value arriving
  later from someone editing in QGIS lands in one and draws in its
  colour. That last property is why an empty class was never given a
  hatched SYMBOL: a hatch baked into a renderer is a snapshot of
  emptiness that nothing refreshes, and it would go on hatching
  features added later. The plugin's SWATCH marked them instead until
  2026-08-17, when that mark went too (see below); the argument
  against putting it in the renderer stands whatever the swatch does,
  and is the one to reach for if anybody proposes it again.
  IT IS SCOPED, and the scope is the whole safety of it: on ordinary
  data every range has width, nothing is degenerate, and no bound
  moves. Shrinking bounds generally would push any value sitting
  exactly on a break up into the next class, reversing QGIS's
  convention across every classed map for no benefit.
  The ONE-VALUE COLLAPSE survives as a deliberate carve-out
  (maintainer's ruling the same day): five ranges all reading "7 - 7"
  in five colours is a legend claiming variation the data lacks, and
  marking four of them would not cure that.
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
  `pin_problem` refuses every pin on a constant column, a copy is not
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
  surviving field (losing a column costs an element its variable, not
  its place on the map — unassigned draws as flat fill, so a deletion
  in QGIS would quietly cost the map two of its four variables), a
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
separate column exists. CONDITION TO WATCH, re-checked 2026-08-09 (twice):
the vendor is now 0.0.7.61 at upstream commit c0f109c while the app
still pins 0.0.7.59. Relative to .59 the vendored code differs by
MIT licence headers, comment blocks, the STRtree tileable filter
(the optimisation this project offered upstream, output-identical
over twenty configurations when offered), and a one-word bugfix in
get_regularised_prototiles_background (prototile ids on the
regularised-prototile frame — a path the plugin does not draw
through). None of that changes what TiledMap.render paints for the
gallery's cases, and the release gates re-measure the claim every
run, so the single reference column still speaks for both. Repeat
this comparison at the next bump; if a release ever changes rendered
behaviour while the app lags, a live browser capture becomes a
genuinely independent third column and should be added then.
