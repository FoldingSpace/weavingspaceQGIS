"""Run a bug hunt's probes against a frozen copy of the tree.

WHY THIS EXISTS, measured rather than assumed. One session's hunts
left 373 one-shot probe scripts and ELEVEN hand-written shell wrappers
in the scratchpad, every wrapper re-deriving how to start QGIS's
Python -- and every one of them copied the same recipe, including a
`QGIS_PREFIX_PATH` that was WRONG. That prefix leaves QGIS unable to
find its own style database, so those hunts probed a QGIS with no
stock colour ramps and none of them knew. A shared harness fixes that
once instead of eleven times, and fixes it for the hunts that have not
been written yet.

It also closes the most expensive failure of that round. Two hunts of
three spent their whole run -- about 350,000 tokens -- confirming
defects that had been fixed while they ran, because a hunt reads a
commit and the tree does not stop for it. Naming the commit makes a
claim reproducible without making it CURRENT, and no amount of prose
in the brief prevents that. So this refuses.

USAGE, and it is meant to be the whole of a hunt's setup:

    python3 tools/hunt_probe.py --prepare --name <this-hunt>
        Archive HEAD into a scratch directory of this hunt's OWN and
        print the commit. Pass --name (or set $WEAVINGSPACE_HUNT)
        whenever more than one hunt runs at a time, which is the
        usual case here; without it the copy is called "solo".
        Everything after this runs against that frozen copy, never
        against the working tree, so a sibling's uncommitted fix
        cannot read as a race.

    python3 tools/hunt_probe.py --run probe.py [args...]
        Run one probe under QGIS's own Python inside the frozen copy.
        Prints the commit it is testing. REFUSES if HEAD has moved
        since --prepare, unless --anyway is given, in which case it
        says loudly that the claim being produced is about an old
        tree.

    python3 tools/hunt_probe.py --status
        What commit is frozen, whether HEAD has moved, and where the
        copy is.

A probe is therefore the twenty lines that state a hypothesis rather
than seventy-nine, of which forty were the same boilerplate every
time.
"""
import argparse
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ONE PLACE PER HUNT, not one per checkout. It used to be shared, on
# the reasoning that two hunts in a session should not each pay to
# build a copy -- and that was wrong in a way that only shows when
# several hunts run at once, which is how they are actually run here.
# Six hunts probing one directory write their probe scripts into it,
# read each other's files, and one calling --prepare wipes the tree
# the other five are working in. A sibling's probe output is
# indistinguishable from your own results, which is the single thing
# a hunt must never get wrong.
#
# Measured 2026-08-16: eleven hunts across three rounds, every one of
# them told by hand to copy the shared tree somewhere private first,
# because the harness would not do it. That instruction is what this
# replaces.
#
# The name comes from --name, or $WEAVINGSPACE_HUNT, or the string
# "solo". A hunt that names nothing still gets a directory of its
# own name rather than a shared one, so the default is safe and the
# flag is only needed to run two at once.
def _hunt_name() -> str:
  """Which hunt this invocation belongs to.

  Returns:
    The name from --name, else $WEAVINGSPACE_HUNT, else "solo".
    Reduced to characters that are safe in a path, since it becomes a
    directory: anything else is replaced with a dash.
  """
  wanted = None
  argv = sys.argv
  for i, arg in enumerate(argv):
    if arg == "--name" and i + 1 < len(argv):
      wanted = argv[i + 1]
      break
    if arg.startswith("--name="):
      wanted = arg.split("=", 1)[1]
      break
  wanted = wanted or os.environ.get("WEAVINGSPACE_HUNT") or "solo"
  return "".join(c if c.isalnum() or c in "-_" else "-" for c in wanted)


BASE = os.path.join(os.environ.get("TMPDIR", "/tmp"), "weavingspace-hunt")
HOME = os.path.join(BASE, _hunt_name())
TREE = os.path.join(HOME, "tree")
STAMP = os.path.join(HOME, "commit.txt")


def git(*args):
  """Run git in the real checkout and return its stripped output.

  Args:
    *args: the git arguments, e.g. ("rev-parse", "HEAD").

  Returns:
    The command's stdout with surrounding whitespace removed, or None
    when git could not answer -- absence is reported by the caller
    rather than raised, since a hunt may run where git does not.
  """
  try:
    done = subprocess.run(("git",) + args, cwd=ROOT, capture_output=True,
                          text=True, timeout=60)
  except (subprocess.SubprocessError, OSError):
    return None
  return done.stdout.strip() if done.returncode == 0 else None


def qgis_environment():
  """The environment QGIS's own Python needs, discovered not guessed.

  Returns:
    A dict of environment variables to add, or an empty dict when the
    discovery script could not answer -- in which case the caller runs
    with whatever is already set and says so.

  It delegates to tools/macos_qgis_env.sh, which is the same script
  tests/run_tests_macos.sh and the macOS CI job use. That is the whole
  point: a hunt's probes and the suite must agree about which QGIS
  they are talking to, and about its prefix, which is where eleven
  hand-written wrappers went wrong.
  """
  script = os.path.join(ROOT, "tools", "macos_qgis_env.sh")
  if not os.path.exists(script):
    return {}
  try:
    done = subprocess.run(["bash", script], capture_output=True,
                          text=True, timeout=300)
  except (subprocess.SubprocessError, OSError):
    return {}
  if done.returncode != 0:
    return {}
  found = {}
  for line in done.stdout.splitlines():
    if "=" in line:
      key, value = line.split("=", 1)
      found[key.strip()] = value.strip()
  return found


def prepare():
  """Freeze HEAD into a scratch copy and record which commit it is.

  Returns:
    0 on success, 1 when git could not name HEAD -- a hunt without a
    commit cannot make a reproducible claim, so that is a refusal
    rather than a warning.
  """
  commit = git("rev-parse", "HEAD")
  if not commit:
    print("REFUSED: git cannot name HEAD here, so a probe run now "
          "could not say which tree it tested.")
    return 1
  shutil.rmtree(HOME, ignore_errors=True)
  os.makedirs(TREE, exist_ok=True)
  archive = subprocess.run(["git", "archive", commit], cwd=ROOT,
                           capture_output=True)
  if archive.returncode != 0:
    print("REFUSED: git archive failed; nothing was frozen.")
    return 1
  extract = subprocess.run(["tar", "-x", "-C", TREE], input=archive.stdout,
                           capture_output=True)
  if extract.returncode != 0:
    print("REFUSED: the archive would not extract; nothing was frozen.")
    return 1
  with open(STAMP, "w", encoding="utf-8") as handle:
    handle.write(commit + "\n")
  print(f"frozen at {commit[:7]}  ->  {TREE}")
  print(f"this hunt is '{_hunt_name()}'; siblings get their own copies, "
        f"so nothing here is anybody else's.")
  print("Probe THIS copy, never the working tree: on a shared tree a "
        "sibling's uncommitted fix reads exactly like a race.")
  return 0


def status():
  """Say what is frozen and whether the world has moved since.

  Returns:
    0 always. This reports; deciding what to do about a moved HEAD is
    the caller's business and --run's refusal.
  """
  if not os.path.exists(STAMP):
    print("nothing frozen; run --prepare first")
    return 0
  frozen = open(STAMP, encoding="utf-8").read().strip()
  head = git("rev-parse", "HEAD")
  print(f"hunt:   {_hunt_name()}")
  print(f"frozen: {frozen[:7]}   copy: {TREE}")
  print(f"HEAD:   {(head or 'unknown')[:7]}")
  if head and head != frozen:
    print("HEAD HAS MOVED since this copy was frozen. Anything you "
          "find here is a claim about the older tree, and may have "
          "been fixed since -- re-prepare before reporting.")
  return 0


def run(argv):
  """Run one probe under QGIS's Python inside the frozen copy.

  Args:
    argv: the probe script and its arguments, as given on the command
      line. The script path is taken as-is, so a hunt may keep its
      probes anywhere.

  Returns:
    The probe's own exit status, or 1 when the run was refused.

  REFUSES when HEAD has moved, because that is the failure this whole
  file exists for. `--anyway` proceeds and prints what the resulting
  claim is about, which is the honest version of doing it regardless.
  """
  if not os.path.exists(STAMP):
    print("REFUSED: nothing is frozen; run --prepare first.")
    return 1
  frozen = open(STAMP, encoding="utf-8").read().strip()
  head = git("rev-parse", "HEAD")
  moved = bool(head) and head != frozen
  if moved and "--anyway" not in sys.argv:
    print(f"REFUSED: frozen at {frozen[:7]} but HEAD is now "
          f"{head[:7]}.\n"
          f"  Two hunts in one round reported defects that had been "
          f"fixed while they ran, which cost an evening of "
          f"verification. Re-run --prepare, or pass --anyway and say "
          f"in your report that the claim is about {frozen[:7]}.")
    return 1

  environment = dict(os.environ)
  found = qgis_environment()
  environment.update(found)
  environment.setdefault("QT_QPA_PLATFORM", "offscreen")
  interpreter = found.get("QGIS_PY") or sys.executable
  if not found:
    print("NOTE: QGIS could not be discovered, so this runs on "
          f"{interpreter} with the environment as it stands.")

  print(f"[hunt_probe] commit {frozen[:7]}"
        f"{'  (HEAD HAS MOVED)' if moved else ''}  "
        f"python {os.path.basename(interpreter)}")
  probe = [a for a in argv if a != "--anyway"]
  try:
    done = subprocess.run([interpreter, "-u"] + probe, cwd=TREE,
                          env=environment)
  except (subprocess.SubprocessError, OSError) as exc:
    print(f"the probe could not be started: {type(exc).__name__}: {exc}")
    return 1
  return done.returncode


def main():
  """Parse the arguments and do the one thing asked.

  Returns:
    A process exit status.
  """
  parser = argparse.ArgumentParser(
    description="Run a bug hunt's probes against a frozen tree.")
  parser.add_argument("--prepare", action="store_true",
                      help="freeze HEAD into a scratch copy")
  parser.add_argument("--status", action="store_true",
                      help="what is frozen, and has HEAD moved since")
  parser.add_argument("--run", nargs=argparse.REMAINDER, default=None,
                      help="probe script and arguments, run in the copy")
  parser.add_argument("--anyway", action="store_true",
                      help="run even though HEAD has moved, and say so")
  parser.add_argument("--name", default=None,
                      help="this hunt's name; it gets a frozen copy of "
                           "its own, so siblings running at the same "
                           "time cannot read each other's probes")
  args = parser.parse_args()
  if args.prepare:
    return prepare()
  if args.status:
    return status()
  if args.run:
    return run(args.run)
  parser.print_help()
  return 0


if __name__ == "__main__":
  sys.exit(main())
