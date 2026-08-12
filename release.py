#!/usr/bin/env python3
"""Cut a release: run every check, write the report, then build the zip.

Usage:
    python3 release.py            # find QGIS automatically (macOS)
    QGIS_PYTHON=... QGIS_PREFIX_PATH=... python3 release.py   # explicit

This is THE way to put out a version (see MAINTAINING.md). It will not
produce a zip unless everything passes. Steps, in order:

1. functional suite (tests/run_tests.py) under QGIS's bundled Python —
   the regression record of everything this project has fixed: the
   pyproj/threading rule, the tile-count guard, auto-render, per-row
   symbology behaviour, GeoPackage output, spacing persistence, QML
   round-trips;
2. visual gallery (tests/visual_tests.py), rendering canonical
   weavingspace outputs to PNGs with image assertions (including
   CIELAB distance-to-ramp checks) and writing
   reports/v<version>/index.html;
3. reference comparison (tools/visual_reference_report.py) in a
   separate Python environment with geopandas and matplotlib: each
   gallery render is scored in Lab colourspace against weavingspace's
   own TiledMap.render on identical inputs (the web app's rendering
   path), with the Quant: Unclassed render as fallback where quantile
   classing alone explains a mismatch; writes visual-comparison.pdf.
   The environment is found via $REFERENCE_PYTHON, else
   .venv-reference/ (created automatically on first use — this cannot
   run under QGIS's Python because macOS code-signing refuses PyPI C
   extensions in the signed QGIS process);
4. build.py, producing dist/weavingspace_qgis.zip.

Environment discovery: on macOS the newest /Applications/QGIS*.app is
used, deriving the interpreter and the env vars its Python needs
(PYTHONHOME because the app's python is relocated; PROJ_LIB so PROJ
finds its coordinate database; QT_QPA_PLATFORM=offscreen so no windows
open). On other platforms set QGIS_PYTHON and QGIS_PREFIX_PATH
yourself — see "Running the tests" in MAINTAINING.md for per-platform
commands.
"""

import argparse
import datetime
import glob
import json
import os
import shutil
import re
import subprocess
import sys
import threading
import time

ROOT = os.path.dirname(os.path.abspath(__file__))


def plugin_version():
  """The version this release will carry, read from metadata.txt.

  Returns:
    The value of the ``version=`` line in the plugin's metadata.txt,
    e.g. "1.4.2", or "unknown" when the field is missing. Nothing is
    written.

  metadata.txt is the single place a version is declared -- it is what
  QGIS's plugin manager reads out of the installed package -- so
  everything downstream is named from here: the report directory, the
  zip, the git tag, the changelog entry used as the commit message,
  and the version the citation file is mended to.
  """
  with open(os.path.join(ROOT, "weavingspace_qgis", "metadata.txt"),
            encoding="utf-8") as f:
    for line in f:
      if line.startswith("version="):
        return line.split("=", 1)[1].strip()
  return "unknown"


def qgis_environment():
  """(python_executable, env) for running scripts under QGIS's Python."""
  env = dict(os.environ)
  env.setdefault("QT_QPA_PLATFORM", "offscreen")
  explicit = os.environ.get("QGIS_PYTHON")
  if explicit:
    return explicit, env
  apps = sorted(glob.glob("/Applications/QGIS*.app"))
  if not apps:
    sys.exit("No QGIS app found; set QGIS_PYTHON and QGIS_PREFIX_PATH "
             "(see MAINTAINING.md).")
  contents = os.path.join(apps[-1], "Contents")
  pythons = sorted(glob.glob(os.path.join(contents, "MacOS", "python3.*")))
  if not pythons:
    sys.exit(f"No bundled python3 in {contents}/MacOS")
  env["PYTHONHOME"] = os.path.join(contents, "Frameworks")
  env["PROJ_LIB"] = os.path.join(contents, "Resources", "qgis", "proj")
  env["QGIS_PREFIX_PATH"] = os.path.join(contents, "MacOS")
  return pythons[0], env


# The stages a release goes through, in order, so the progress chart
# can show what is still to come rather than only what has happened.
# Names must match the `step` passed to run(); anything run() sees that
# is not here is appended when it starts, so the chart stays honest if
# a stage is added and this list is forgotten.
EXPECTED_STAGES = [
  "roadmap and branches", "standards check", "secrets audit",
  "functional suite",
  "coverage report", "visual gallery", "create reference venv",
  "install reference packages", "reference comparison",
  "testing report", "per-test coverage record", "merge the coverage shards",
  "refresh published images",
  "test map", "bug register", "published content audit",
  "build release candidate", "candidate dossier", "build zip",
]

# name -> [status, seconds]. status is "done", "running" or "failed".
STAGE_STATE = {}
STAGE_ORDER = []
# stage -> seconds it has currently gone without using any cpu.
STAGE_IDLE = {}

# Where the last run's stage durations are kept, so this run can
# estimate. In dist/ because that is local, persistent and never
# committed: timings belong to a machine, not to the repository, and
# quoting somebody else's hardware back at a user would be worse than
# saying nothing.
TIMINGS_PATH = os.path.join(ROOT, "dist", "stage-timings.json")


def load_timings():
  """Stage durations recorded by previous runs.

  Returns:
    {stage name: seconds}, empty when nothing has been recorded or
    the file cannot be read. Unreadable is treated as absent
    deliberately: a corrupt timing file must cost an estimate, never
    a release.
  """
  try:
    with open(TIMINGS_PATH, encoding="utf-8") as handle:
      recorded = json.load(handle)
    return {str(k): float(v) for k, v in recorded.items()}
  except (OSError, ValueError, TypeError, AttributeError):
    return {}


def remember_timing(step, seconds):
  """Record how long a stage took, for the next run to quote.

  Args:
    step: the stage name.
    seconds: how long it took.

  Returns:
    None. Failures to write are swallowed: this is a convenience for
    the next run and must never be the thing that stops this one.

  Only SUCCESSFUL stages are recorded, by the caller. A stage that
  failed or was killed says nothing about how long the work takes.
  """
  try:
    known = load_timings()
    known[step] = round(seconds, 1)
    os.makedirs(os.path.dirname(TIMINGS_PATH), exist_ok=True)
    with open(TIMINGS_PATH, "w", encoding="utf-8") as handle:
      json.dump(known, handle, indent=2, sort_keys=True)
  except OSError:
    pass


def _spell(seconds):
  """Seconds as a short human duration: 8s, 3m, 1h04m."""
  seconds = int(seconds)
  if seconds < 90:
    return f"{seconds}s"
  if seconds < 3600:
    return f"{seconds // 60}m"
  return f"{seconds // 3600}h{(seconds % 3600) // 60:02d}m"

# When this release began. Module level because the abort path inside
# run() prints the chart too, and a failure should say what had
# already passed rather than only what broke.
RELEASE_STARTED = time.time()

# How long a stage may accumulate NO cpu time before it is considered
# stuck rather than slow. Ten minutes for ordinary stages: everything
# here is compute, so ten minutes of a completely idle process tree
# means it is waiting for something that is never coming -- most
# likely a modal dialog offscreen, which is this project's classic
# hang.
STALL_SECONDS = 600

# How often the watcher looks. Thirty seconds is frequent enough to
# notice a hang promptly and rare enough that the sampling costs
# nothing; it is a named constant so tests can turn it down and
# exercise the watchdog in seconds rather than minutes.
SAMPLE_SECONDS = 30

# Stages that are SUPPOSED to be idle, because they are waiting on a
# network rather than computing. Calling these stuck would be the
# false alarm that teaches people to switch watchdogs off.
NETWORK_STAGES = {"create reference venv", "install reference packages"}
NETWORK_STALL_SECONDS = 2700

# The backstop. CPU-idleness cannot catch a stage SPINNING, since an
# infinite loop accumulates cpu happily forever, so an absolute
# ceiling stays -- set high enough that only a runaway reaches it.
ABSOLUTE_CEILING = 4 * 3600


def tree_cpu_seconds(pid):
  """Total cpu time used by a process and everything it started.

  Args:
    pid: the process to measure.

  Returns:
    Seconds of cpu time across the whole tree, or None when it cannot
    be read -- the process finishing between listing and measuring is
    ordinary, not an error.

  The whole TREE, because release.py's stages are subprocesses that
  themselves spawn: the suite runs QGIS, which forks for the
  hostile-data cases. Measuring only the direct child would report a
  busy release as idle.
  """
  try:
    listing = subprocess.run(
      ["ps", "-eo", "pid=,ppid=,time="], capture_output=True, text=True,
      timeout=30)
  except (subprocess.SubprocessError, OSError):
    return None
  if listing.returncode != 0:
    return None
  children, times = {}, {}
  for line in listing.stdout.splitlines():
    parts = line.split()
    if len(parts) < 3:
      continue
    try:
      this, parent = int(parts[0]), int(parts[1])
    except ValueError:
      continue
    children.setdefault(parent, []).append(this)
    # ps prints cpu time as [DD-]HH:MM:SS
    clock = parts[2]
    days = 0
    if "-" in clock:
      day_part, clock = clock.split("-", 1)
      days = int(day_part)
    bits = [float(b) for b in clock.split(":")]
    while len(bits) < 3:
      bits.insert(0, 0.0)
    times[this] = days * 86400 + bits[0] * 3600 + bits[1] * 60 + bits[2]
  total, stack = 0.0, [pid]
  seen = set()
  while stack:
    current = stack.pop()
    if current in seen:
      continue
    seen.add(current)
    total += times.get(current, 0.0)
    stack.extend(children.get(current, []))
  return total


def stage_chart(started, final=False):
  """The progress chart, as a block of text.

  Args:
    started: time.time() when the release began. Kept for the wall
      clock a reader compares against their watch; every DURATION in
      the chart is monotonic, so a machine that slept does not report
      hours of work it did not do.
    final: the run is OVER. Expected stages that never ran are then
      dropped instead of listed as pending -- a finished chart
      showing ".." rows (a cached venv, a skipped guard) reads as an
      unfinished run, which is exactly what it is not. (User
      instruction, 2026-08-09.)

  Returns:
    A multi-line string listing every stage with its state and, for
    those that have finished, how long they took. Mid-run, stages not
    yet reached are listed too, because "what is left" is most of
    what somebody watching wants to know.
  """
  now = time.time()
  expected = load_timings()
  remaining = 0.0
  # WORKING time, not wall clock. A laptop closed for two hours
  # reported "running 148m" beside stages summing to thirty, because
  # the header read time.time() while the durations are monotonic
  # (2026-08-11, a real run carried to a meeting). The two are not
  # comparable and printing them side by side invites exactly the
  # wrong conclusion -- that something has hung. Sleep is excluded
  # here, so the header and the stage list finally agree.
  working = sum(state[1] for state in STAGE_STATE.values()
                if state[0] in ("done", "failed"))
  working += sum(time.monotonic() - state[1]
                 for state in STAGE_STATE.values()
                 if state[0] == "running")
  working = int(working)
  # BOTH, labelled, whenever they differ by more than a minute. Only
  # the working figure is comparable with the stage list below it, and
  # only the elapsed figure is comparable with the reader's watch;
  # printing one alone invites the wrong question in one direction or
  # the other. They diverge when the machine sleeps -- two hours of a
  # closed laptop against thirty minutes of work, 2026-08-11 -- and
  # that gap is worth seeing rather than hiding, because it explains
  # an estimate that would otherwise look wrong.
  elapsed = int(now - started)
  spell = f"working {working // 60}m"
  if abs(elapsed - working) > 60:
    spell += f", {elapsed // 60}m elapsed including time asleep"
  lines = [f"\n=== progress at {time.strftime('%H:%M')} ({spell}) ==="]
  seen = list(STAGE_ORDER)
  if not final:
    for name in EXPECTED_STAGES:
      if name not in seen:
        seen.append(name)
  for name in seen:
    state = STAGE_STATE.get(name)
    if state is None:
      guess = expected.get(name)
      lines.append(f"  ..  {name}"
                   + (f"  ~{_spell(guess)}" if guess else ""))
      if guess:
        remaining += guess
    elif state[0] == "running":
      ran = time.monotonic() - state[1]
      idle = STAGE_IDLE.get(name, 0)
      allowance = (NETWORK_STALL_SECONDS if name in NETWORK_STAGES
                   else STALL_SECONDS)
      mark, note = ">>", ""
      if idle > allowance / 2:
        mark = "!!"
        note = (f"  NO CPU FOR {int(idle // 60)}m -- stopping at "
                f"{int(allowance // 60)}m idle")
      guess = expected.get(name)
      if guess and not note:
        left = guess - ran
        note = (f"  ~{_spell(left)} left" if left > 0
                else f"  over its usual {_spell(guess)}")
        remaining += max(left, 0)
      lines.append(f"  {mark}  {name}  (running "
                   f"{int(ran // 60)}m{int(ran % 60):02d}s){note}")
    elif state[0] == "failed":
      lines.append(f"  XX  {name}  FAILED")
    else:
      lines.append(f"  ok  {name}  {_spell(state[1])}")
  if remaining > 0:
    finish = time.strftime("%H:%M", time.localtime(now + remaining))
    lines.append(f"  -- about {_spell(remaining)} left, finishing "
                 f"around {finish}")
  elif not expected:
    lines.append("  -- no previous run to estimate from; this one is "
                 "measuring itself")
  return "\n".join(lines)


def start_progress(started):
  """Print the chart every ten minutes until the release finishes.

  Args:
    started: time.time() when the release began.

  Returns:
    The threading.Event that stops it. Set it when the release ends.

  A daemon thread, so it can never keep the process alive, and it
  waits before its first report so a run that finishes quickly says
  nothing at all. Ten minutes is chosen against the stages: the suite
  and the gallery are the long ones, and a chart every ten minutes
  distinguishes "still going" from "stuck" without becoming noise.
  """
  stop = threading.Event()

  def tick():
    while not stop.wait(600):
      print(stage_chart(started), flush=True)

  threading.Thread(target=tick, daemon=True).start()
  return stop


def mutation_sample_size(changed_lines):
  """How many mutants the changed-lines guard samples.

  Args:
    changed_lines: lines added to shipped plugin code since the last
      release tag, as ``git diff --numstat`` counts them.

  Returns:
    max(12, min(80, changed_lines // 20)). A FIXED sample was sized
    for routine releases and became decorative the night a round
    changed seventeen hundred lines -- twelve mutants over a diff
    that size certifies nearly nothing, while over a ten-line fix
    they are dense coverage. One mutant per twenty changed lines
    keeps the density roughly constant; the floor keeps small
    releases honestly sampled and the cap keeps the stage's cost
    proportionate (about two hours at worst) rather than open-ended.
    (User instruction, 2026-08-09.)
  """
  return max(12, min(80, changed_lines // 20))


# What each stage's result DEPENDS ON, so --resume can tell a stage
# whose answer still holds from one whose answer is stale. Paths are
# relative to the repository root; a directory means everything under
# it. Anything not listed here is never skipped.
#
# This is deliberately narrower than "the whole tree" and wider than
# tree_digest(), which covers only files that SHIP. A gate's result
# turns on the code it exercised AND the harness that exercised it: a
# change to tests/run_tests.py invalidates the suite even though no
# shipped byte moved, and a change to tools/coverage_per_test.py
# invalidates the coverage record and NOTHING ELSE -- which is the
# case that prompted this, four full re-runs into one afternoon.
STAGE_DEPENDS = {
  "functional suite": ["weavingspace_qgis", "tests/run_tests.py"],
  "coverage report": ["weavingspace_qgis", "tests/run_tests.py",
                      "tools/coverage_report.py"],
  "visual gallery": ["weavingspace_qgis", "tests/visual_tests.py"],
  "reference comparison": ["weavingspace_qgis",
                           "tools/visual_reference_report.py"],
  "per-test coverage record": ["weavingspace_qgis", "tests/run_tests.py",
                               "tools/coverage_per_test.py"],
}
STAGE_STATE_PATH = os.path.join(ROOT, "reports", "stage-state.json")

# Set from --resume in main(). A module global rather than an argument
# threaded through run() and run_sharded() because every caller would
# pass the same value, and a parameter that is never varied is one
# more thing to get wrong at one of twenty call sites.
RESUMING = False


def stage_fingerprint(step):
  """A hash of everything that could change this stage's answer.

  Args:
    step: the stage name, as passed to run().

  Returns:
    A hex digest over the declared dependencies' contents, or None
    when the stage has none declared -- which means it is never
    skipped, the safe default for anything nobody has thought about.
  """
  import hashlib
  paths = STAGE_DEPENDS.get(step)
  if not paths:
    return None
  digest = hashlib.sha256()
  for entry in sorted(paths):
    full = os.path.join(ROOT, entry)
    files = []
    if os.path.isdir(full):
      for base, dirs, names in os.walk(full):
        dirs[:] = [d for d in dirs if d not in ("__pycache__", "libs")]
        files += [os.path.join(base, n) for n in names
                  if not n.endswith(".pyc")]
    elif os.path.exists(full):
      files = [full]
    for path in sorted(files):
      digest.update(os.path.relpath(path, ROOT).encode("utf-8"))
      with open(path, "rb") as handle:
        digest.update(hashlib.sha256(handle.read()).digest())
  return digest.hexdigest()


def load_stage_state():
  """What previous runs recorded about each stage, or {} if nothing."""
  try:
    with open(STAGE_STATE_PATH, encoding="utf-8") as handle:
      return json.load(handle)
  except (OSError, ValueError):
    return {}


def remember_stage(step):
  """Record that this stage passed, against what it depended on.

  Args:
    step: the stage that just succeeded.

  Returns:
    None. Failures to write are swallowed: this exists to save time
    on a later run and must never be the thing that stops this one.
  """
  fingerprint = stage_fingerprint(step)
  if fingerprint is None:
    return
  try:
    state = load_stage_state()
    state[step] = {"fingerprint": fingerprint, "at": time.time()}
    os.makedirs(os.path.dirname(STAGE_STATE_PATH), exist_ok=True)
    with open(STAGE_STATE_PATH, "w", encoding="utf-8") as handle:
      json.dump(state, handle, indent=1, sort_keys=True)
  except OSError:
    pass


def may_skip(step, resuming):
  """Whether this stage's previous answer still holds.

  Args:
    step: the stage about to run.
    resuming: whether --resume was asked for. Without it nothing is
      ever skipped, because a full run is what a release means and
      the saving is only ever worth asking for deliberately.

  Returns:
    True when the stage passed before against exactly the inputs it
    has now. Says so out loud when it skips, because a gate that did
    not run is a thing a reader must be told rather than left to
    infer from a suspiciously short log.
  """
  if not resuming:
    return False
  recorded = load_stage_state().get(step)
  if not recorded:
    return False
  if recorded.get("fingerprint") != stage_fingerprint(step):
    return False
  when = time.strftime("%H:%M", time.localtime(recorded.get("at", 0)))
  print(f"\n=== {step} — SKIPPED, passed at {when} and nothing it "
        f"depends on has changed since ===", flush=True)
  STAGE_STATE[step] = ("done", 0.0)
  if step not in STAGE_ORDER:
    STAGE_ORDER.append(step)
  return True


def skip_if_already_done(step, capture):
  """Whether to skip this stage, and what it said when it last ran.

  Args:
    step: the stage about to run.
    capture: whether the caller USES this stage's output. Four do --
      the testing report quotes the suite test by test, and the
      gallery and comparison summaries are read for their numbers.

  Returns:
    (True, output) when the stage may be skipped, where output is the
    text the caller would have received; (False, "") otherwise.

  The output comes from reports/stage-logs/, which run() and
  run_sharded() already write in full for exactly this kind of
  reason. That file is what makes a skip HONEST rather than merely
  fast: a skip that returned "" would hand the testing report an
  empty string and produce a report describing nothing, which is
  worse than the hour it saved. So a captured stage whose log is
  missing is NOT skipped, however well its fingerprint matches.

  Written after three aborts in one night, all in machinery rather
  than in the plugin, each costing a full re-run of gates that had
  already passed. may_skip and remember_stage were written weeks
  earlier and remember_stage was already recording; only the flag and
  this call site were missing, so the evidence to skip was on disk
  and unread. (2026-08-11.)
  """
  if not RESUMING:
    return False, ""
  saved = stage_log_path(step)
  if capture and not os.path.exists(saved):
    return False, ""
  if not may_skip(step, RESUMING):
    return False, ""
  if not capture:
    return True, ""
  with open(saved, encoding="utf-8") as handle:
    return True, handle.read()


def stage_log_path(step):
  """Where this stage's full output is kept.

  Args:
    step: the human stage name, e.g. "functional suite".

  Returns:
    An absolute path under reports/stage-logs/, with everything but
    letters and digits turned into hyphens. ONE rule with two
    callers -- the in-progress stamp and the finished output -- so
    the two can never write to different files and leave a reader
    holding whichever is older.
  """
  log_dir = os.path.join(ROOT, "reports", "stage-logs")
  os.makedirs(log_dir, exist_ok=True)
  return os.path.join(
    log_dir, "".join(c if c.isalnum() else "-" for c in step) + ".log")


def stamp_stage_log(step, began):
  """Replace a stage's log with a note saying this stage is running.

  Args:
    step: the human stage name.
    began: the time.time() at which the stage started.

  Returns:
    None; the file is overwritten. The old contents are deliberately
    DISCARDED rather than kept above the note: a reader who scrolls
    finds the previous run's results and no longer knows which run
    they belong to, which is the whole failure this prevents.
  """
  with open(stage_log_path(step), "w", encoding="utf-8") as handle:
    handle.write(
      f"IN PROGRESS: {step}\n"
      f"started {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(began))}"
      f", part of the release begun "
      f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(RELEASE_STARTED))}"
      f"\n\nThis stage has not finished, so it has no result yet. The "
      f"previous run's output was cleared when this one started, "
      f"because an old log with nothing to say it is old reads "
      f"exactly like a current one.\n")


def run(step, cmd, env, capture=False):
  """Run one release step, and abandon the release if it fails.

  Args:
    step: the human name of this stage ("visual gallery", "secrets
      audit"), printed as a banner and quoted in the abort message so
      a failure says which gate stopped the release.
    cmd: the command as a list of words, run with the repository root
      as its working directory.
    env: the environment to run it in. The stages that need QGIS get
      the interpreter environment from qgis_environment(); the plain
      ones (standards, secrets, the zip) get a copy of os.environ,
      because loading QGIS's Python into them buys nothing.
    capture: collect stdout and stderr and hand them back instead of
      letting them stream. Set for the stages whose output the
      testing report quotes test by test; the tail is still printed,
      so a long capture is not a silent one.

  Returns:
    The combined output when capture is set, otherwise the empty
    string. Nothing else is mutated -- but a non-zero exit status
    calls sys.exit here rather than returning, so no later step, and
    above all no zip, can be produced from a state that has already
    failed a gate.
  """
  skipped, remembered = skip_if_already_done(step, capture)
  if skipped:
    return remembered
  print(f"\n=== {step} ===", flush=True)
  if step not in STAGE_ORDER:
    STAGE_ORDER.append(step)
  # monotonic, like every other duration here: the chart
  # subtracts from it, and a wall-clock start would make a
  # sleeping machine look like a stage that had run for hours
  STAGE_STATE[step] = ["running", time.monotonic()]
  began = time.time()            # for stamping: a human reads it
  # for every DURATION below. Kept apart from `began` deliberately:
  # mixing the two clocks in one subtraction is how a sleep turns
  # into a stall, and the mix would look perfectly ordinary.
  began_monotonic = time.monotonic()
  if capture:
    # Stamp the stage log as IN PROGRESS before the work starts.
    # Without this the file on disk keeps the PREVIOUS run's output
    # for as long as this stage takes, and anybody checking on
    # progress reads last night's verdict as though it were tonight's
    # -- which happened on 2026-08-11, when a stale "275 passed, 1
    # failed" from the aborted rc5 was nearly reported as the result
    # of the run then twenty minutes into its suite. A log that is
    # merely OLD is a log that lies, because nothing about it says so.
    stamp_stage_log(step, began)
  stalled = []
  process = subprocess.Popen(
    cmd, env=env, cwd=ROOT, text=True,
    stdout=subprocess.PIPE if capture else None,
    stderr=subprocess.STDOUT if capture else None)

  def watch():
    """Stop the stage if it goes long enough without using any cpu.

    Every clock reading here is time.monotonic(), NEVER time.time(),
    and the difference is a closed laptop. Wall clock advances while
    a machine sleeps; the process accumulates no cpu, because it is
    not running. Read together on wake, those two say "hours idle,
    no work done" -- which is this watchdog's definition of a hang,
    so a healthy release would be killed for having been carried to
    a meeting. On macOS time.monotonic() stops with the machine, so
    a sleep simply does not count.

    This is the same defect the mutation campaign fixed in
    mutate_auto.py after a sleeping laptop cost four verdicts in
    batch 8 (docs/MUTATION-TESTING.md, "the measurement keeps
    flattering itself"). release.py was written afterwards and
    repeated it, which is worth knowing: a lesson recorded in one
    tool does not travel to the next by itself.
    """
    allowance = (NETWORK_STALL_SECONDS if step in NETWORK_STAGES
                 else STALL_SECONDS)
    last_cpu, idle_since = None, time.monotonic()
    while process.poll() is None:
      time.sleep(SAMPLE_SECONDS)
      used = tree_cpu_seconds(process.pid)
      now = time.monotonic()
      # a hundredth of a second of movement is enough to call it
      # alive; ps reports to that resolution and a working tree
      # moves far more
      if used is None or last_cpu is None or used > last_cpu + 0.01:
        idle_since = now
      last_cpu = used if used is not None else last_cpu
      STAGE_IDLE[step] = now - idle_since
      if now - idle_since > allowance or \
          now - began_monotonic > ABSOLUTE_CEILING:
        stalled.append(
          "used no cpu at all"
          if now - began_monotonic <= ABSOLUTE_CEILING
          else "ran past the absolute ceiling while still busy")
        process.kill()
        return

  watcher = threading.Thread(target=watch, daemon=True)
  watcher.start()
  output_text = process.communicate()[0] if capture else None
  returncode = process.wait()
  STAGE_IDLE.pop(step, None)
  # monotonic: a stage carried through a sleep would otherwise be
  # remembered as having taken hours, and remember_timing feeds the
  # estimates printed in the progress chart
  spent = time.monotonic() - began_monotonic
  STAGE_STATE[step] = ("failed" if (returncode or stalled) else "done",
                       spent)
  if not returncode and not stalled:
    # only a stage that actually finished says anything about how
    # long the work takes
    remember_timing(step, spent)
    remember_stage(step)
  if stalled:
    print(stage_chart(RELEASE_STARTED), flush=True)
    sys.exit(
      f"RELEASE ABORTED: {step} {stalled[0]} and has been stopped; no "
      f"zip was built.\n"
      f"  It was killed because it had stopped doing work, not because "
      f"it was slow:\n"
      f"  the whole process tree accumulated no cpu time. That usually "
      f"means it is\n  waiting for something that will never come -- "
      f"most often a modal dialog\n  offscreen, which is this "
      f"project's classic hang.\n"
      f"  Look at reports/ for how far it got.")

  class _Finished:
    """The bits of CompletedProcess the rest of run() reads."""
    def __init__(self, code, text):
      self.returncode = code
      self.stdout = text
      self.stderr = ""

  result = _Finished(returncode, output_text)
  output = (result.stdout or "") + (result.stderr or "") if capture else ""
  stage_log = None
  if capture:
    # the WHOLE output, kept on disk: the console shows only the tail
    # below, and a failure whose casualties sat above the tail once
    # cost a full re-run just to learn their names. reports/ is
    # local-only, so a big log costs nobody a clone.
    stage_log = stage_log_path(step)
    with open(stage_log, "w", encoding="utf-8") as handle:
      handle.write(output)
    print(output[-2000:])
  if result.returncode != 0:
    print(stage_chart(RELEASE_STARTED), flush=True)
    where = (f"\n  Full stage output: {stage_log}" if stage_log
             else "\n  The stage streamed; its full output is above.")
    sys.exit(f"RELEASE ABORTED: {step} failed "
             f"(exit {result.returncode}); no zip was built.{where}")
  return output


SHARDS = int(os.environ.get("WEAVINGSPACE_RELEASE_SHARDS", "3"))


def run_sharded(step, argv, env, capture=False):
  """Run one stage as SHARDS concurrent processes over slices of the suite.

  Args:
    step: the human stage name, used for the banner and the log.
    argv: the command, WITHOUT any shard argument; each process gets
      WEAVINGSPACE_TEST_SHARD=i/n in its environment instead, which
      the suite reads at import.
    env: the base environment; each shard receives a copy.
    capture: collect and return the combined output, as run() does.

  Returns:
    The concatenated output when capture is set, otherwise "". Exits
    the release if any shard fails, naming which -- a slice that fails
    is the suite failing, and three green shards beside one red one is
    not a passing suite.

  Why this is safe here and would not be everywhere: the tests are
  order-independent by construction, since every one runs with an
  EMPTY project. A slice is therefore a legitimate subset rather than
  a different suite. What it costs is time PER TEST -- concurrent QGIS
  processes inflate per-unit times by 15-50% on this machine -- which
  is why the suite widens its stall ceilings whenever a shard is in
  force, by two and a half times against a measured worst case of
  1.5. Without that headroom sharding would turn slow tests into
  false stalls, which is the fault this project committed twice on
  2026-08-11 and does not intend to commit a third time.
  """
  skipped, remembered = skip_if_already_done(step, capture)
  if skipped:
    return remembered
  print(f"\n=== {step} ({SHARDS} shards) ===", flush=True)
  if step not in STAGE_ORDER:
    STAGE_ORDER.append(step)
  STAGE_STATE[step] = ["running", time.monotonic()]
  began = time.monotonic()
  processes = []
  for index in range(SHARDS):
    shard_env = dict(env)
    shard_env["WEAVINGSPACE_TEST_SHARD"] = f"{index}/{SHARDS}"
    processes.append(subprocess.Popen(
      argv, env=shard_env, cwd=ROOT, text=True,
      stdout=subprocess.PIPE if capture else None,
      stderr=subprocess.STDOUT if capture else None))
  output, failed = "", []
  for index, process in enumerate(processes):
    text = process.communicate()[0] if capture else None
    if capture:
      output += f"\n--- shard {index} of {SHARDS} ---\n" + (text or "")
    if process.wait() != 0:
      failed.append(index)
  spent = time.monotonic() - began
  STAGE_STATE[step] = ("failed" if failed else "done", spent)
  if not failed:
    remember_timing(step, spent)
    remember_stage(step)
  if capture:
    stage_log = stage_log_path(step)
    with open(stage_log, "w", encoding="utf-8") as handle:
      handle.write(output)
    print(output[-2000:])
  if failed:
    print(stage_chart(RELEASE_STARTED), flush=True)
    sys.exit(f"RELEASE ABORTED: {step} failed in shard(s) "
             f"{failed}; no zip was built.\n"
             f"  A slice failing IS the suite failing. Its output is "
             f"above and in {stage_log_path(step)}.")
  return output


def test_docstrings():
  """{display name: first docstring sentence} for every functional
  test, read from tests/run_tests.py itself (the AST, so nothing needs
  importing under QGIS here). The display names come from the check()
  calls in its main(); the sentences from each test function's
  docstring. Used to annotate the testing report."""
  import ast
  import re
  path = os.path.join(ROOT, "tests", "run_tests.py")
  with open(path, encoding="utf-8") as f:
    source = f.read()
  tree = ast.parse(source)
  docs = {}
  for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
      doc = ast.get_docstring(node) or ""
      first = doc.replace("\n", " ").split(". ")[0].strip()
      docs[node.name] = (first + "." if first and not first.endswith(".")
                         else first)
  names = {}
  for m in re.finditer(r'check\("([^"]+)",\s*\n?\s*(test_\w+)\)',
                       source):
    names[m.group(1)] = docs.get(m.group(2), "")
  return names


def write_testing_report(report_dir, version, functional, visual,
                         comparison, coverage=""):
  """Write this release's per-test record to testing-report.md.

  Args:
    report_dir: reports/v<version>/, this release's evidence
      directory; the markdown file is written into it.
    version: the version being released, used in the heading.
    functional: captured output of tests/run_tests.py, read for its
      PASS/FAIL lines and annotated from each test's docstring.
    visual: captured output of tests/visual_tests.py, whose PASS/FAIL
      lines carry the measured values after " :: ".
    comparison: captured output of tools/visual_reference_report.py,
      the colourspace scores against the original renderer.
    coverage: captured output of tools/coverage_report.py. Only its
      "coverage:" summary line is used, and it defaults to empty so
      the report can still be written when coverage was not run --
      coverage is reported, never gating.

  Returns:
    None. Writes report_dir/testing-report.md, replacing any earlier
    one, and prints its path.

  Every test is listed individually rather than totalled, because
  this file is both the record the release notes point at (--push
  attaches it to the GitHub Release as the notes) and what the user
  is shown per test whenever something is published. A count of
  passes says nothing about which behaviours were actually checked.
  """
  lines = [f"# Testing report — v{version}", ""]
  lines += ["## Functional suite (tests/run_tests.py)", ""]
  annotations = test_docstrings()
  for ln in functional.splitlines():
    if ln.startswith(("PASS", "FAIL")):
      name = ln[4:].strip()
      note = annotations.get(name, "")
      lines.append(f"- **{ln[:4].strip()}** {name}"
                   + (f" — {note}" if note else ""))
  lines.append("")
  lines += ["## Visual gallery (tests/visual_tests.py)", ""]
  for ln in visual.splitlines():
    if ln.startswith(("PASS", "FAIL")):
      body = ln[4:].strip()
      name, _, detail = body.partition(" :: ")
      lines.append(f"- **{ln[:4].strip()}** {name}"
                   + (f" — {detail}" if detail.strip() else ""))
  lines.append("")
  lines += ["## Reference comparison "
            "(tools/visual_reference_report.py)", ""]
  for ln in comparison.splitlines():
    if ln.startswith(("PASS", "FAIL")):
      lines.append(f"- **{ln[:4].strip()}** {ln[4:].strip()}")
  summary = [ln for ln in coverage.splitlines()
             if ln.startswith("coverage:")]
  if summary:
    lines += ["## Coverage of plugin code", "",
              f"- {summary[-1]} (see coverage.md for the per-module "
              "table and the untested line runs)", ""]
  lines += ["", "Artifacts: index.html (gallery renders), "
            "visual-comparison.pdf (side-by-side against the original "
            "renderer), coverage.md, functional.txt (raw run).",
            "",
            "Not part of the gate, run before substantial releases: "
            "`tools/mutation_check.py` breaks each guarded behaviour "
            "in turn and confirms its test fails."]
  path = os.path.join(report_dir, "testing-report.md")
  with open(path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
  print(f"testing report: {path}")


def prune_old_reports(keep=3):
  """Delete all but the most recent report directories.

  Args:
    keep: how many versions to retain, newest first.

  Returns:
    None. Each release writes renders, a gallery, a comparison PDF
    and per-test output -- a few megabytes that are worth having for
    the version you just cut and the couple before it, and dead
    weight after that (they reached 136 MB across twenty versions
    before anyone looked). The zip in dist/ and the plugin installed
    in QGIS are what actually ship; these are evidence, and evidence
    for a version nobody is looking at any more is just disk.
  """
  import re
  import shutil
  reports = os.path.join(ROOT, "reports")
  if not os.path.isdir(reports):
    return

  def as_version(name):
    parts = re.findall(r"\d+", name)
    return tuple(int(p) for p in parts) if parts else (0,)

  versions = sorted((d for d in os.listdir(reports)
                     if d.startswith("v") and
                     os.path.isdir(os.path.join(reports, d))),
                    key=as_version)
  removed = 0
  for old_dir in versions[:-keep] if keep else versions:
    path = os.path.join(reports, old_dir)
    size = sum(os.path.getsize(os.path.join(dp, f))
               for dp, _dn, fn in os.walk(path) for f in fn)
    shutil.rmtree(path, ignore_errors=True)
    removed += size
  if removed:
    print(f"tidied {removed / 1e6:.0f} MB of superseded reports "
          f"(kept the newest {keep})")


def git(*arguments, check=True, quiet=False):
  """Run a git command in the project directory.

  Args:
    *arguments: the command, without the leading "git".
    check: raise if git fails. False where a non-zero status is an
      answer rather than an error (asking whether a tag exists).
    quiet: do not echo the command.

  Returns:
    The completed process, with stdout captured.
  """
  if not quiet:
    print(f"  git {' '.join(arguments)}")
  return subprocess.run(["git", *arguments], cwd=ROOT, check=check,
                        capture_output=True, text=True)


def changelog_entry(version):
  """The changelog lines for this version, as a paragraph.

  Args:
    version: the version being released.

  Returns:
    The text of the entry, or an empty string when there is none.
    Used as the commit message body, so that the history says what
    changed in the same words the plugin manager will show a user.
  """
  path = os.path.join(ROOT, "weavingspace_qgis", "metadata.txt")
  with open(path, encoding="utf-8") as handle:
    text = handle.read()
  match = re.search(rf"^changelog=(.*?)(?=^\w+=|\Z)", text,
                    re.S | re.M)
  if not match:
    return ""
  for block in match.group(1).split("\n\n"):
    if version in block:
      return " ".join(line.strip() for line in block.splitlines()).strip()
  return ""


def commit_and_tag(version, report_dir, push):
  """Record the release in version control, and optionally publish it.

  Args:
    version: the version being released.
    report_dir: this release's report directory, whose files are
      attached to the GitHub release.
    push: whether to send the result to GitHub. False leaves
      everything local and prints the commands instead.

  Returns:
    None.

  Committing and tagging are local and can be undone with one
  command, so they are unconditional: the repository should never
  disagree with the zip that was just built. Pushing and publishing
  cannot be undone once anyone has fetched, so they need the flag.
  """
  print("\n=== version control ===")
  inside = git("rev-parse", "--git-dir", check=False, quiet=True)
  if inside.returncode != 0:
    print("  not a git repository yet; skipping.\n"
          "  To start one:  git init && git add -A && "
          "git commit -m 'Initial commit'")
    return

  # asked twice, deliberately: the steps above generate files, and a
  # secret introduced by a generator is still a leaked secret
  run("secrets audit (pre-commit)",
      [sys.executable, os.path.join("tools", "check_no_secrets.py")],
      dict(os.environ))

  git("add", "-A")
  staged = git("diff", "--cached", "--quiet", check=False, quiet=True)
  if staged.returncode == 0:
    print("  nothing to commit; the tree already matches this release")
  else:
    entry = changelog_entry(version)
    message = f"Release v{version}"
    if entry:
      message += f"\n\n{entry}"
    git("commit", "-m", message)

  tag = f"v{version}"
  exists = git("rev-parse", "-q", "--verify", f"refs/tags/{tag}",
               check=False, quiet=True)
  if exists.returncode == 0:
    print(f"  tag {tag} already exists and will not be moved; bump the "
          f"version in metadata.txt for a new release")
  else:
    git("tag", "-a", tag, "-m", f"WeavingSpace plugin {tag}")

  assets = [os.path.join(ROOT, "dist", "weavingspace_qgis.zip"),
            os.path.join(report_dir, "testing-report.md"),
            os.path.join(report_dir, "visual-comparison.pdf")]
  assets = [a for a in assets if os.path.exists(a)]

  notes_preview = os.path.join(report_dir, "release-notes.md")
  if not push:
    run("release notes",
        [sys.executable, "-u", os.path.join("tools", "release_notes.py"),
         report_dir], dict(os.environ))
    print("\n  Local only. To publish this release:")
    print(f"    git push origin HEAD && git push origin {tag}")
    print(f"    gh release create {tag} \\\n         "
          + " \\\n         ".join(assets)
          + f" \\\n         --title '{tag}' --notes-file "
            f"{os.path.relpath(notes_preview, ROOT)}")
    print("  or re-run with --push to do both.")
    return

  git("push", "origin", "HEAD")
  git("push", "origin", tag)
  if shutil.which("gh") is None:
    print("  gh is not installed, so the tag is pushed but no GitHub "
          "release was created. Either install it (brew install gh; "
          "gh auth login) or attach the files by hand at\n"
          "  https://github.com/FoldingSpace/weavingspaceQGIS/releases/new")
    return
  # The release BODY is the notes, not the testing report. The report
  # is admirable evidence and unreadable as an announcement: a reader
  # arriving at a release page wants to know what changed, and gets
  # it in the words a person wrote and the plugin manager already
  # shows. The report stays ATTACHED, where somebody checking rather
  # than reading will look for it.
  notes = os.path.join(report_dir, "release-notes.md")
  run("release notes",
      [sys.executable, "-u", os.path.join("tools", "release_notes.py"),
       report_dir], dict(os.environ))
  command = ["gh", "release", "create", tag, *assets, "--title", tag]
  if os.path.exists(notes):
    command += ["--notes-file", notes]
  print(f"  {' '.join(command[:4])} ...")
  subprocess.run(command, cwd=ROOT, check=True)
  print(f"  published: "
        f"https://github.com/FoldingSpace/weavingspaceQGIS/releases/tag/{tag}")
  print("  the project page updates itself from docs/ on the next "
        "GitHub Pages build, usually within a minute")


def tree_digest():
  """A fingerprint of exactly the files that would be shipped.

  Returns:
    A hex digest over every shipped file's archive name and contents,
    taken with build.py's own file list so the two cannot disagree.

  This is what makes "the same tree" checkable. It deliberately
  ignores everything NOT shipped -- tests, tooling, documentation,
  the reports -- because those cannot change the artefact a reviewer
  installed, and a release should not be blocked by an edit to a
  comment in the test suite.
  """
  import hashlib
  import importlib.util
  spec = importlib.util.spec_from_file_location(
    "build_rules", os.path.join(ROOT, "build.py"))
  build_rules = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(build_rules)
  digest = hashlib.sha256()
  for full, rel in build_rules.shipped_files():
    digest.update(rel.encode("utf-8"))
    with open(full, "rb") as handle:
      digest.update(hashlib.sha256(handle.read()).digest())
  return digest.hexdigest()


def write_receipt(version, label, digest):
  """Record that this exact tree passed every gate and was packaged.

  Args:
    version: the version being built.
    label: the candidate's label, e.g. "0.24.0rc2".
    digest: tree_digest() for the tree it was built from.

  Returns:
    The path written.

  Written only after every gate has passed, because run() aborts the
  release on the first failure. Its existence is therefore the proof
  that this tree was measured and packaged, and the digest is what
  ties that proof to a tree rather than to a moment.
  """
  import json
  path = os.path.join(ROOT, "dist", f"CANDIDATE-{label}.receipt.json")
  with open(path, "w", encoding="utf-8") as handle:
    json.dump({"version": version, "label": label, "tree": digest,
               "built": datetime.date.today().isoformat()}, handle,
              indent=2, sort_keys=True)
  return path


def matching_receipt(version, digest):
  """The candidate this tree was reviewed as, if there is one.

  Args:
    version: the version being released.
    digest: tree_digest() for the tree as it stands now.

  Returns:
    The receipt dict for a candidate of this version built from an
    identical tree, or None. None is the refusal case, and refusing is
    the point: a release that has not been through a candidate is a
    release nobody has installed.
  """
  import json
  for path in sorted(glob.glob(os.path.join(
      ROOT, "dist", f"CANDIDATE-{version}rc*.receipt.json"))):
    try:
      with open(path, encoding="utf-8") as handle:
        receipt = json.load(handle)
    except (OSError, ValueError):
      continue
    if receipt.get("tree") == digest:
      return receipt
  return None


def main():
  """Cut a release from the command line, gate by gate.

  Returns:
    0 once a release candidate has been built (--rc), otherwise None
    when the full release has finished. Every failure leaves through
    run()'s sys.exit, so returning at all means the gates passed.

  What it leaves behind: reports/v<version>/ (functional output,
  gallery, coverage, comparison PDF, testing report), refreshed
  images in docs/img/, possibly a mended CITATION.cff,
  dist/weavingspace_qgis.zip, and a commit and tag. With --push, also
  a pushed branch and tag and a GitHub Release with the zip, report
  and PDF attached; --push is the single point at which anything
  leaves this machine.

  The ORDER is the substance of this function. The two cheap refusals
  come first, so a release that breaks the project's own rules or
  carries a secret fails in seconds rather than after the gallery.
  The test stages follow, then the report they feed, then the
  mutation guard over only what changed since the last tag, then the
  published images and the audit of the claims those images support.
  The zip is built last, from a tree every gate has already passed;
  committing and tagging are local and reversible, so they are
  unconditional. --rc stops before all of that, leaving a numbered
  candidate in dist/ and the tree untouched, because the gates can
  say whether the plugin is correct and only a person making a map
  can say whether it is any good to use.
  """
  parser = argparse.ArgumentParser(
    description="Build, test, document and publish a release.")
  parser.add_argument(
    "--push", action="store_true",
    help="after the gates pass, push the branch and tag and create the "
         "GitHub release. Without this the commit and tag stay local "
         "and the commands to publish them are printed.")
  parser.add_argument(
    "--resume", action="store_true",
    help="skip any stage that passed before against exactly the "
         "inputs it has now, reusing the output kept in "
         "reports/stage-logs/. Nothing is skipped without this flag, "
         "because a full run is what a release means and the saving "
         "is only ever worth asking for deliberately. What counts as "
         "'exactly the inputs' is STAGE_DEPENDS, which is narrower "
         "than the whole tree and wider than the files that ship: "
         "editing tests/run_tests.py invalidates the suite even "
         "though no shipped byte moved. Each skip is announced with "
         "the time it originally passed, since a gate that did not "
         "run is a thing a reader must be told rather than left to "
         "infer from a short log.")
  parser.add_argument(
    "--quick", action="store_true",
    help="with --rc, skip the coverage report: 31 minutes and it "
         "gates nothing, being informational by design. The visual "
         "gallery and the colourspace comparison are NOT skipped -- "
         "measured 2026-08-11 they cost 7 and 16 seconds and are the "
         "two stages that catch a map drawn wrongly, which is this "
         "software's characteristic failure. The old grouping dated "
         "from when the gallery was the slow one.")
  parser.add_argument(
    "--rc", action="store_true",
    help="build a numbered release candidate for hands-on testing and "
         "stop. Runs the same correctness gates, skips the publication "
         "steps, and commits nothing.")
  args = parser.parse_args()
  global RESUMING
  RESUMING = args.resume

  started = time.time()
  version = plugin_version()
  print(f"Releasing WeavingSpace plugin v{version}")
  python, env = qgis_environment()
  print(f"QGIS Python: {python}")

  report_dir = os.path.join(ROOT, "reports", f"v{version}")
  os.makedirs(report_dir, exist_ok=True)
  # the functional suite writes its UI-vs-library renders here, and
  # the comparison step turns them into PDF pages
  env["WEAVINGSPACE_REPORT_DIR"] = report_dir

  # 0. the project's own rules, before anything expensive runs: a
  # release that breaks them should fail in seconds, not after the
  # visual gallery
  # Say where we have got to every ten minutes. A release runs for
  # the better part of an hour and its longest stages capture their
  # output, so without this the log sits unchanged long enough to
  # look like a hang -- which cost two healthy runs, killed by
  # somebody watching a silent log.
  progress = start_progress(RELEASE_STARTED)

  # FIRST, before anything expensive. Work written for this version
  # and left on a branch, or an entry in ROADMAP.md nobody did, are
  # the two ways a release quietly ships without something it was
  # supposed to carry. Both cost a second to check and ninety minutes
  # to discover afterwards. --merge brings in branches named for THIS
  # version; a conflict stops the release instead, because a conflict
  # is a question about intent and a release script is the worst thing
  # to answer it. Deferring an entry is the maintainer's decision and
  # this never makes it.
  run("roadmap and branches",
      [sys.executable, "-u", os.path.join("tools", "check_roadmap.py"),
       "--merge"], dict(os.environ))
  run("standards check",
      [sys.executable, os.path.join("tools", "check_standards.py")],
      dict(os.environ))

  # 0b. and nothing that must not be published, checked before any of
  # the expensive work and again immediately before the commit. A
  # leaked key is the one failure that cannot be undone by a later
  # release, so it is worth asking twice.
  run("secrets audit",
      [sys.executable, os.path.join("tools", "check_no_secrets.py")],
      dict(os.environ))

  # ---- a real release PROMOTES a candidate. It does not re-derive one.
  #
  # The stages below cost the better part of an hour, and re-running
  # them at release time answers a question already answered -- worse,
  # it answers it about whatever the tree looks like NOW, which need
  # not be the tree somebody installed and reviewed. So a release
  # requires a receipt written by a candidate built from a byte-identical
  # tree, and having found one it skips straight to packaging and
  # version control.
  #
  # Refusing without one is the point of the whole candidate phase: it
  # makes "has a human actually run this?" a gate rather than a habit.
  if not args.rc:
    digest = tree_digest()
    receipt = matching_receipt(version, digest)
    if receipt is None:
      built = sorted(glob.glob(os.path.join(
        ROOT, "dist", f"CANDIDATE-{version}rc*.receipt.json")))
      if built:
        detail = (f"{len(built)} candidate(s) of v{version} were built, "
                  f"but from a different tree than this one. Something "
                  f"that ships has changed since the last candidate.")
      else:
        detail = f"No candidate of v{version} has been built at all."
      sys.exit(
        f"\nRefusing to release v{version}.\n\n  {detail}\n\n"
        f"  A release publishes an artefact somebody has installed and\n"
        f"  reviewed. Build a candidate, try it in QGIS, and release\n"
        f"  that:\n\n"
        f"      python3 release.py --rc\n\n"
        f"  then re-run this command without changing anything that\n"
        f"  ships.")
    print(f"\n=== promoting candidate {receipt['label']} ===\n"
          f"  built {receipt.get('built', 'earlier')} from this exact "
          f"tree, and it passed every gate then.\n"
          f"  The suite, gallery, coverage and reference comparison are "
          f"NOT re-run:\n"
          f"  the artefact is identical, file for file, to the one "
          f"already measured.")
    run("build zip", [sys.executable, "build.py"], dict(os.environ))
    prune_old_reports(keep=3)
    commit_and_tag(version, report_dir, push=args.push)
    progress.set()
    print(stage_chart(RELEASE_STARTED))
    print(f"\nRelease v{version} complete (promoted from "
          f"{receipt['label']})."
          f"\n  zip:        dist/weavingspace_qgis.zip"
          f"\n  report:     reports/v{version}/index.html")
    return 0

  # 1. functional suite; captured so the report can include it
  functional = run_sharded(
    "functional suite",
    [python, "-u", os.path.join("tests", "run_tests.py")],
    env, capture=True)
  with open(os.path.join(report_dir, "functional.txt"), "w",
            encoding="utf-8") as f:
    # keep the readable tail (PASS/FAIL lines), not Qt's noise
    lines = [ln for ln in functional.splitlines()
             if ln.startswith(("PASS", "FAIL")) or "passed" in ln]
    f.write("\n".join(lines))

  # 1b. coverage of plugin code, from a second run of the same suite
  # (cheap: sys.monitoring disables each line after its first hit).
  # Reported, never gating: coverage is a map of untested ground, not
  # a target to satisfy.
  # MEASURED 2026-08-11, and it inverts what --quick used to mean.
  # The gallery costs 7 seconds and the reference comparison 16, and
  # both catch a WRONG MAP -- the failure this software has that most
  # software does not. This report costs 31 minutes and gates
  # nothing: it is informational by its own docstring. So --quick now
  # skips the expensive non-gating stages and keeps the cheap gating
  # ones, which is what it was always for; the old grouping dated
  # from when the gallery was the slow one.
  coverage = ""
  if args.quick:
    print("\n=== coverage report — SKIPPED (--quick): 31 minutes and "
          "it gates nothing ===", flush=True)
  else:
    coverage = run("coverage report",
                   [python, "-u", os.path.join("tools",
                                              "coverage_report.py"),
                    report_dir], env, capture=True)

  # 2. visual gallery + HTML report (captured for the testing report).
  # These three stages — gallery, reference comparison, per-test
  # coverage — are most of the wall clock and all speak to RENDERING.
  # --quick skips them so a candidate can be rebuilt in a couple of
  # minutes while the changes under review are elsewhere. The
  # candidate you actually release from is built without it.
  # ALWAYS, even under --quick. Seven seconds, and it is one of the
  # two stages that can catch a map drawn wrongly -- which is this
  # software's characteristic failure, since a wrong map looks
  # exactly like a right one. It sat under --quick from when it was
  # the slow stage; measured 2026-08-11 it is not.
  visual = comparison = ""
  visual = run("visual gallery",
               [python, "-u", os.path.join("tests", "visual_tests.py")],
               env, capture=True)

  # 3. colourspace comparison against the original renderer, in a
  # plain (non-QGIS) environment that carries geopandas + matplotlib
  ref_python = os.environ.get("REFERENCE_PYTHON")
  if not ref_python:
    venv_dir = os.path.join(ROOT, ".venv-reference")
    ref_python = os.path.join(venv_dir, "bin", "python3")
    if not os.path.exists(ref_python):
      print("\n=== creating reference environment (.venv-reference) ===")
      run("create reference venv",
          [sys.executable, "-m", "venv", venv_dir], dict(os.environ))
      run("install reference packages",
          [os.path.join(venv_dir, "bin", "pip"), "install", "--quiet",
           "geopandas", "matplotlib", "networkx", "mapclassify"],
          dict(os.environ))
  # ALSO always: sixteen seconds, and it is the one check that scores
  # what the plugin drew against what the library itself draws.
  comparison = run(
      "reference comparison",
      [ref_python, os.path.join("tools", "visual_reference_report.py"),
       report_dir], dict(os.environ), capture=True)

  write_testing_report(report_dir, version, functional, visual,
                       comparison, coverage)

  # 3a. Record which lines each test executes, then hold the code that
  # CHANGED since the last release to account: mutate only those lines
  # and require the tests to catch them. This is the routine guard
  # against a slow slide. The full campaign asks how good the suite is
  # over the whole plugin and takes hours; this asks whether today's
  # work is defended, costs minutes, and is the one that runs every
  # time. Skipped on the first release, when there is no previous tag
  # to compare against.
  run_sharded("per-test coverage record",
              [python, "-u", os.path.join("tools", "coverage_per_test.py")],
              env)
  # the shards wrote one file each; the mutation tools want one map,
  # and the merge REFUSES a partial set rather than quietly producing
  # a record that overstates survivors
  run("merge the coverage shards",
      [python, "-u", os.path.join("tools", "merge_coverage_shards.py")],
      env)
  previous = subprocess.run(["git", "describe", "--tags", "--abbrev=0"],
                            cwd=ROOT, capture_output=True, text=True)
  if previous.returncode == 0 and previous.stdout.strip():
    tag = previous.stdout.strip()
    # the sample SCALES with the diff (see mutation_sample_size):
    # count the lines added to shipped plugin code since the tag,
    # vendor excluded because upstream's code is not this suite's to
    # defend
    numstat = subprocess.run(
      ["git", "diff", "--numstat", tag, "--",
       "weavingspace_qgis", ":!weavingspace_qgis/vendor"],
      cwd=ROOT, capture_output=True, text=True)
    changed = sum(
      int(line.split()[0])
      for line in numstat.stdout.splitlines()
      if line.split() and line.split()[0].isdigit())
    sample = mutation_sample_size(changed)
    run(f"new-code mutation guard (since {tag}: {changed} changed "
        f"lines, {sample} mutants)",
        [python, "-u", os.path.join("tools", "mutate_auto.py"),
         "--since", tag, "--sample", str(sample),
         "--workers", "3", "--require", "70"], env)
  else:
    # LOUD, because a skip that whispers becomes permanent: this
    # exact message printed on every candidate for two days before
    # anyone noticed the repository had never been tagged at all
    print("\n=== new-code mutation guard: SKIPPED ===\n"
          "  NO RELEASE TAG EXISTS to diff against, so the new-code\n"
          "  guard has nothing to measure and DID NOT RUN. If this\n"
          "  keeps appearing, the guard has never run: create a\n"
          "  baseline tag (git tag -a <name> <commit>) and it fires\n"
          "  from the next release onward.", flush=True)

  # 3b. re-photograph what we publish. The README and the project page
  # show the dialog and a set of maps, and both are claims about how
  # the plugin currently looks and what it currently produces. They go
  # stale silently, so they are retaken from THIS release's gallery
  # rather than carried forward.
  run("refresh published images",
      [python, "-u", os.path.join("tools", "make_site_images.py"),
       "--gallery", report_dir], env)

  # 3c. and then check every other claim the published files make:
  # the citation version, the changelog entry, the images, the links,
  # the vendored library version, the repository URLs. Mechanical
  # corrections are applied; anything needing words stops the release.
  # The suite's own index, regenerated from the suite. Placed with
  # the published-content audit because it is the same kind of claim:
  # a document that describes something else and rots silently unless
  # it is rebuilt from the thing it describes.
  run("test map", [sys.executable, os.path.join("tools", "test_map.py")],
      dict(os.environ))

  # The register is generated from the suite's own Regression: lines,
  # exactly as the map is generated from its registrations. It used to
  # be left out of this list, so it drifted between releases until a
  # reader noticed -- which is the failure the standards check now
  # catches and this line prevents.
  run("bug register",
      [sys.executable, os.path.join("tools", "bug_register.py")],
      dict(os.environ))

  run("published content audit",
      [sys.executable, os.path.join("tools", "sync_release_content.py"),
       "--fix", "--since", str(started)], dict(os.environ))

  # 4. build the zip only now that everything has passed
  if args.rc:
    # A candidate is the same code, packaged for people rather than
    # for publication: it goes no further than dist/, nothing is
    # committed, no tag is cut and no image or document is rewritten.
    # It exists because the checks above answer "is this correct?" and
    # cannot answer "is this any good to use?", which only comes back
    # from somebody making a map with it. Stopping here is the point:
    # a candidate that quietly did the publication steps would leave
    # the tree looking released when it is not.
    run("build release candidate",
        [sys.executable, "build.py", "--rc"], dict(os.environ))
    # Name the candidate that was just built, then write its dossier:
    # the page the reviewer actually reads. Derived from the tree, so
    # it cannot describe a different candidate than the one on disk.
    built = sorted(glob.glob(os.path.join(ROOT, "dist",
                                          "weavingspace_qgis-*rc*.zip")))
    if built:
      label = os.path.basename(built[-1])[len("weavingspace_qgis-"):-4]
      run("candidate dossier",
          [sys.executable, os.path.join("tools", "candidate_dossier.py"),
           label], dict(os.environ))
      # The receipt: proof that THIS tree passed every gate and was
      # packaged for review. Written last, because everything above it
      # aborts on failure, so reaching this line is the proof.
      receipt = write_receipt(version, label, tree_digest())
      print(f"  receipt: {os.path.relpath(receipt, ROOT)}")
    progress.set()
    print(stage_chart(RELEASE_STARTED, final=True))
    print(f"\nRelease candidate built from a passing tree. Nothing was "
          f"committed, tagged or published.\n"
          f"  candidates: dist/\n"
          f"  report:     {os.path.relpath(report_dir, ROOT)}\n\n"
          f"Install it in QGIS with Plugins > Manage and Install "
          f"Plugins... > Install from ZIP.\nWhen the feedback is in, "
          f"run release.py (or release.py --push) for the real thing.")
    return 0

  run("build zip", [sys.executable, "build.py"], dict(os.environ))

  prune_old_reports(keep=3)

  # 5. version control. Committing and tagging are local and
  # reversible, so they always happen; pushing is neither, so it
  # happens only when asked for on this invocation.
  commit_and_tag(version, report_dir, push=args.push)

  progress.set()
  print(stage_chart(RELEASE_STARTED, final=True))
  print(f"\nRelease v{version} complete."
        f"\n  zip:        dist/weavingspace_qgis.zip"
        f"\n  report:     reports/v{version}/index.html"
        f"\n  tests:      reports/v{version}/testing-report.md"
        f"\n  comparison: reports/v{version}/visual-comparison.pdf")


if __name__ == "__main__":
  main()
