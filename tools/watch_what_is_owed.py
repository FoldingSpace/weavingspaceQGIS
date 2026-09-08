#!/usr/bin/env python3
"""One watcher over EVERYTHING A SESSION OWES, asking the tree and the remote.

    python3 tools/watch_what_is_owed.py --once        # report and stop
    python3 tools/watch_what_is_owed.py 300           # watch, 300s apart

It exists because the two ad-hoc watchers written for this in one week
both failed, in different ways, and both failures are already written
down in CLAUDE.md as things not to do again:

  ONE GREPPED FOR A TOKEN rather than asking a behaviour. It reported
  two CLOSED items as owed, having searched for `override=True` (which
  the repair legitimately keeps inside a conditional) and for a function
  name nobody had written -- and it was silent about eleven unpushed
  commits, because it watched one thread of several.

  THE OTHER RAN ONCE AND EXITED, so its completion notification read
  exactly like a report. A watcher that has exited is not a watcher.

So every check here is a QUESTION PUT TO GIT, TO THE REMOTE, OR TO A
CHECKER THAT ALREADY EXISTS -- never a search for a string that ought to
be somewhere. Nothing is remembered between passes except the previous
answer, and the whole picture is re-derived each time, so a watcher
pinned to a stale subject cannot go quiet at the next push.

AND IT EXITS WHEN THE ANSWER CHANGES, which is what turns a log into a
prompt: the harness notifies when a background command ends, so a
watcher that keeps running keeps its finding to itself. That is
`tools/hunt_campaign_watch.sh`'s contract, borrowed deliberately.

HAND-RUN IT ONCE BEFORE ARMING IT, from the repository, and read the
whole output. `gh` reads the repository from the working directory, so
a watcher started anywhere else asks about nothing -- which is the
twenty-first watcher fault this project has paid for.

Exit codes: 0 where nothing is owed, 1 where something is (or where the
owed set has changed since the last pass, in watch mode), 2 where the
watcher could not answer at all, which is not the same as "nothing".
"""

import argparse
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# The INSTRUMENT is committed; its state is not, for the same reason the
# hunt campaign's is not -- a watcher's memory is about one session.
STATE = os.path.join(ROOT, "dev", "what-is-owed.json")


def run(command, timeout=120):
  """Run a command in the repository and hand back what it said.

  Args:
    command: argv, run without a shell so nothing is word-split.
    timeout: seconds before the call is abandoned; a checker that hangs
      is a finding rather than a reason to wait.

  Returns:
    (returncode, output). The code is 127 where the command does not
    exist and 124 where it timed out, both distinct from any check's own
    verdict, because a gate that could not START is not a gate that
    answered.
  """
  try:
    done = subprocess.run(command, cwd=ROOT, timeout=timeout,
                          capture_output=True, text=True)
  except FileNotFoundError:
    return 127, f"{command[0]} is not on the path"
  except subprocess.TimeoutExpired:
    return 124, f"{command[0]} did not answer within {timeout}s"
  return done.returncode, (done.stdout + done.stderr).strip()


def git(*args, timeout=60):
  """Ask git something, with the same distinction between kinds of failure.

  Args:
    *args: the git arguments, without the leading `git`.
    timeout: passed through to `run`.

  Returns:
    (returncode, output).
  """
  return run(["git", *args], timeout=timeout)


def clean_python():
  """The interpreter the project's own tools must run under.

  Returns:
    argv prefix that strips `PYTHONHOME` and `PYTHONPATH`. The two
    interpreters here are not interchangeable: a tool launched under
    QGIS's python dies at `import` having done nothing, which reads
    exactly like a check that passed.
  """
  return ["env", "-u", "PYTHONHOME", "-u", "PYTHONPATH", sys.executable]


def subject():
  """What this pass is about, named on every line it prints.

  Returns:
    (branch, head) as short strings, or ("?", "?") where git cannot say
    -- which is itself worth printing rather than crashing on.
  """
  _c, branch = git("rev-parse", "--abbrev-ref", "HEAD")
  _c, head = git("rev-parse", "--short", "HEAD")
  return branch or "?", head or "?"


def unpushed():
  """Commits sitting on this branch that no runner has seen.

  Returns:
    (owed, sentence). Asks the branch's own upstream, falling back to
    `origin/<branch>`; where neither exists the honest answer is that
    the branch is unpublished rather than that nothing is owed.
  """
  code, _ = git("rev-parse", "--abbrev-ref", "@{upstream}")
  if code != 0:
    branch, _head = subject()
    code, _ = git("rev-parse", "--verify", f"origin/{branch}")
    if code != 0:
      return True, "the branch has no upstream at all, so nothing has been pushed"
    ref = f"origin/{branch}..HEAD"
  else:
    ref = "@{upstream}..HEAD"
  code, out = git("rev-list", "--count", ref)
  if code != 0:
    return True, f"git could not count unpushed commits: {out[:60]}"
  count = int(out or 0)
  if count == 0:
    return False, "nothing unpushed"
  code, shipped = git("rev-list", "--count", ref, "--",
                      "weavingspace_qgis")
  return True, (f"{count} commit(s) unpushed, {shipped or '?'} of them "
                f"touching shipped code")


def working_tree():
  """Whether anything is uncommitted.

  Returns:
    (owed, sentence). Asks git rather than remembering what was edited.
  """
  code, out = git("status", "--porcelain")
  if code != 0:
    return True, f"git status failed: {out[:60]}"
  if not out:
    return False, "working tree clean"
  return True, f"{len(out.splitlines())} uncommitted path(s)"


def changelog():
  """Whether the changelog has moved since the last tag that shipped code.

  Returns:
    (owed, sentence). The question is not whether an entry EXISTS -- the
    published-content audit already asks that -- but whether shipped code
    has landed since `metadata.txt` was last touched. An approved
    changelog goes stale under you, which this project has already
    shipped once.
  """
  code, out = git("log", "-1", "--format=%H", "--",
                  "weavingspace_qgis/metadata.txt")
  if code != 0 or not out:
    return True, "no commit has ever touched metadata.txt, which cannot be right"
  code, since = git("rev-list", "--count", f"{out}..HEAD", "--",
                    "weavingspace_qgis")
  if code != 0:
    return True, f"git could not count commits since the changelog: {since[:50]}"
  count = int(since or 0)
  if count == 0:
    return False, "the changelog is level with the shipped code"
  return True, (f"{count} shipped-code commit(s) since metadata.txt last "
                f"moved; the changelog entry is a person's to write")


def checker(name, args, good, bad):
  """Turn one of the project's own gates into a watched thread.

  Args:
    name: the script under `tools/`.
    args: extra arguments for it.
    good: what to say when it passes.
    bad: what to say when it fails, with the gate's own first line added.

  Returns:
    (owed, sentence). A gate that could not START is reported as owed
    and SAID to be unstartable, because silence plus a non-zero code is
    not a verdict.
  """
  code, out = run(clean_python() + [os.path.join("tools", name), *args])
  if code in (124, 127):
    return True, f"{name} could not answer: {out[:70]}"
  if code == 0:
    return False, good
  first = next((line for line in out.splitlines() if line.strip()), "")
  return True, f"{bad}: {first[:70]}"


def continuous_integration():
  """The colour of the newest run on this branch, asked of the remote.

  Returns:
    (owed, sentence). `gh` reads the repository from the working
    directory, so this must run from the checkout. A branch that has
    never been pushed has no runs, which is reported as such rather than
    as green.

  AND A COLOUR IS ABOUT A COMMIT, NEVER ABOUT A BRANCH. Hand-run before
  it was armed, this said "CI green" while the newest run was on the
  candidate's commit twelve behind HEAD -- a true sentence that reads as
  though the work in hand had been tested. The distance from HEAD is
  therefore part of every answer, and the word green is used only where
  the run is ON HEAD.
  """
  branch, head = subject()
  code, out = run(["gh", "run", "list", "--branch", branch, "--limit", "1",
                   "--json", "status,conclusion,headSha,workflowName"],
                  timeout=60)
  if code in (124, 127):
    return False, f"CI not asked ({out[:50]})"
  try:
    runs = json.loads(out or "[]")
  except json.JSONDecodeError:
    return False, f"CI answered something that is not JSON: {out[:50]}"
  if not runs:
    return False, "no CI run on this branch yet"
  newest = runs[0]
  sha = (newest.get("headSha") or "")[:7]
  where = f"{newest.get('workflowName', '?')} on {sha}"
  code, behind = git("rev-list", "--count", f"{sha}..HEAD") if sha else (1, "")
  if code == 0 and behind and int(behind) > 0:
    where += f", {behind} behind {head}"
  on_head = code == 0 and behind == "0"
  if newest.get("status") != "completed":
    return False, f"CI {newest.get('status')} ({where})"
  if newest.get("conclusion") == "success":
    return (False, f"CI green ({where})") if on_head else (
      True, f"CI passed on an OLDER commit ({where}); nothing has seen {head}")
  return True, f"CI {newest.get('conclusion')} ({where})"


CHECKS = (
  ("unpushed", unpushed),
  ("working tree", working_tree),
  ("changelog", changelog),
  ("standards", lambda: checker("check_standards.py", [],
                                "standards clean", "standards RED")),
  ("roadmap", lambda: checker("check_roadmap.py", [],
                              "the version's road is clear", "roadmap RED")),
  ("text review", lambda: checker("text_review.py", ["--check"],
                                  "text queue settled",
                                  "text awaiting the maintainer")),
  ("secrets", lambda: checker("check_no_secrets.py", [],
                              "no secrets", "SECRETS")),
  ("CI", continuous_integration),
)


def one_pass():
  """Re-derive every thread from scratch.

  Returns:
    (owed, lines) -- the set of thread names currently owed, and one
    printable line per thread. Nothing is carried over from the last
    pass, so a thread that closes goes quiet by being asked again rather
    than by anybody remembering to retire it.
  """
  branch, head = subject()
  owed, lines = set(), []
  for name, ask in CHECKS:
    try:
      is_owed, sentence = ask()
    except Exception as exc:                       # noqa: BLE001
      is_owed, sentence = True, f"the check itself raised {type(exc).__name__}"
    if is_owed:
      owed.add(name)
    lines.append(f"[{branch} {head}] {'OWED' if is_owed else '  ok'}  "
                 f"{name:13} {sentence}")
  return owed, lines


def read_state():
  """The previous pass's owed set, or None where there was none.

  Returns:
    A set of thread names, or None. A missing file means a FIRST pass,
    which must report everything rather than announcing history as news.
  """
  try:
    with open(STATE, encoding="utf-8") as handle:
      return set(json.load(handle))
  except (OSError, ValueError):
    return None


def write_state(owed):
  """Remember this pass's owed set.

  Args:
    owed: the set of thread names owed now.
  """
  os.makedirs(os.path.dirname(STATE), exist_ok=True)
  with open(STATE, "w", encoding="utf-8") as handle:
    json.dump(sorted(owed), handle)


def main():
  """Report once, or watch until the answer changes."""
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("interval", nargs="?", type=float, default=None,
                      help="seconds between passes; omit for a single pass")
  parser.add_argument("--once", action="store_true",
                      help="report and stop, whatever the interval says")
  parser.add_argument("--reset", action="store_true",
                      help="forget the previous pass, so the next reports all")
  args = parser.parse_args()

  if args.reset and os.path.exists(STATE):
    os.remove(STATE)

  if args.once or args.interval is None:
    owed, lines = one_pass()
    print("\n".join(lines))
    write_state(owed)
    print(f"\n{len(owed)} thread(s) owed: {', '.join(sorted(owed)) or 'none'}")
    return 1 if owed else 0

  before = read_state()
  while True:
    owed, lines = one_pass()
    if before is None or owed != before:
      print(f"---- {time.strftime('%H:%M:%S')} ----")
      print("\n".join(lines))
      if before is not None:
        opened = sorted(owed - before)
        closed = sorted(before - owed)
        if opened:
          print(f"NEWLY OWED: {', '.join(opened)}")
        if closed:
          print(f"CLOSED:     {', '.join(closed)}")
      write_state(owed)
      # EXIT ON CHANGE, so the harness's own end-of-command notification
      # carries the finding. A watcher that goes on running has told
      # nobody anything.
      return 1 if owed else 0
    time.sleep(args.interval)


if __name__ == "__main__":
  sys.exit(main())
