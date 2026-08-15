"""Run exactly what CI's fast job runs, before pushing rather than after.

The gap this closes was measured, not imagined. On 2026-08-12 this
branch went red at 07:52 and stayed red for EIGHTEEN pushes across six
hours, while work continued on top of it. The local habit was
`check_standards` and `check_no_secrets`, both of which passed the
whole time; what was failing was `text_review.py --check`, because
five sentences awaited a person's approval and approving prose is the
maintainer's act that no local gate may perform. A gate only a person
can satisfy is precisely the one that goes unsatisfied for six hours.

So the fix is not a watcher per push -- twenty pushes would mean
twenty pollers, and this project already has "one watcher, not a fresh
script each time" near the top of its list after seven watcher faults
in one night. The fix is to ask the question a second BEFORE the push
instead of twenty minutes after it, and to ask ALL of it.

The commands are READ OUT OF THE WORKFLOW rather than written here
again, for the same reason `check_standards` reads `release.py`'s own
stage list: a hand-kept copy of somebody else's list is a copy that
drifts, and it drifts silently, and the drift is discovered by the
thing it was supposed to prevent. Add a step to the standards job and
it runs here from the next invocation with nobody editing this file.

What this deliberately does NOT do is run the QGIS jobs -- the suite,
the install check, the gallery, and the Windows install check. Those
need containers and tens of minutes, they are what CI is FOR, and
duplicating them locally is the habit docs/PUBLISHING.md spent eighty
minutes a candidate unlearning. The Windows one could not be run here
at any price: this project has one machine and it is a Mac. This is
the twenty-second job only.

    python3 tools/check_before_push.py
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKFLOW = os.path.join(ROOT, ".github", "workflows", "ci.yml")

# The job whose steps are cheap enough to run on a laptop before every
# push. Named rather than inferred: "cheap" is a judgement, and the
# other four jobs are deliberately excluded above.
FAST_JOB = "standards"


def commands_in(job):
  """The shell commands a workflow job runs, in order.

  Args:
    job: the job's key in ci.yml, e.g. "standards".

  Returns:
    A list of (name, command) pairs, where name is the step's `name:`
    when it has one and the command itself otherwise. Only single-line
    `run:` steps are returned; a step with a block scalar is a script
    rather than a check and is reported by the caller as skipped, so
    it cannot be silently dropped.

  Raises:
    SystemExit: when the workflow or the job cannot be found. An empty
      list would read exactly like "nothing to check", which is the
      failure this whole file exists to prevent.

  Parsed with regular expressions rather than a YAML library on
  purpose: this must run on a plain Python with nothing installed,
  which is the same reason build.py is stdlib-only. The shapes it
  accepts are the shapes this workflow uses, and it REFUSES rather
  than guesses on anything else.
  """
  if not os.path.exists(WORKFLOW):
    raise SystemExit(f"no workflow at {WORKFLOW}; nothing to mirror")
  with open(WORKFLOW, encoding="utf-8") as handle:
    text = handle.read()

  # the job's block: from its key at two spaces of indent, up to the
  # next key at that same indent
  block = re.search(
    rf"^  {re.escape(job)}:\n(.*?)(?=^  \S|\Z)", text, re.M | re.S)
  if block is None:
    raise SystemExit(
      f"ci.yml has no job called {job!r}. Either it was renamed -- in "
      f"which case rename FAST_JOB here in the same commit -- or the "
      f"fast checks have gone, which is a bigger question.")
  body = block.group(1)

  found, pending_name, skipped = [], None, []
  for line in body.splitlines():
    named = re.match(r"\s*- name: (.+?)\s*$", line)
    if named:
      pending_name = named.group(1)
      continue
    inline = re.match(r"\s*run: (?!\|)(.+?)\s*$", line)
    if inline:
      found.append((pending_name or inline.group(1), inline.group(1)))
      pending_name = None
      continue
    if re.match(r"\s*run: \|", line):
      skipped.append(pending_name or "(unnamed multi-line step)")
      pending_name = None
  if not found:
    raise SystemExit(
      f"parsed the {job!r} job and found no runnable steps, which "
      f"cannot be right. Rather than report success over nothing, "
      f"this refuses: check the workflow's shape against the parser.")
  return found, skipped


def main():
  """Run every fast CI check against the working tree.

  Returns:
    None. Exits 0 when all of them pass and 1 otherwise, so it can sit
    in front of a push in a shell chain. Each check's own output is
    left alone -- they already say what is wrong, and rewording a
    checker's message in a wrapper is how a diagnosis gets lost.
  """
  checks, skipped = commands_in(FAST_JOB)
  # flush every heading: the child processes write straight to the
  # terminal while these prints sit in a buffer, so without it the
  # headings arrive AFTER the output they label and a reader
  # attributes each result to the wrong check
  print(f"running the {len(checks)} check(s) CI's '{FAST_JOB}' job "
        f"runs, read from ci.yml:\n", flush=True)
  failed = []
  for name, command in checks:
    print(f"--- {name}", flush=True)
    result = subprocess.run(command, shell=True, cwd=ROOT)
    if result.returncode != 0:
      failed.append(name)
    print(flush=True)

  # Said out loud rather than passed over: a step this cannot run is a
  # hole in the mirror, and a hole nobody mentions is how the mirror
  # stops being one.
  for name in skipped:
    print(f"NOT RUN HERE (multi-line script step): {name}")

  if failed:
    print(f"{len(failed)} check(s) failed: {', '.join(failed)}")
    print("CI will fail on this tree. Fix it, or -- if the failure is "
          "the text-review queue -- take the wording to the "
          "maintainer, because approving it is their act and not "
          "this program's.")
    sys.exit(1)
  print("all clear: CI's fast job would pass on this tree")


if __name__ == "__main__":
  main()
