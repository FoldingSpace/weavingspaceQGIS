#!/usr/bin/env python3
"""Nothing written for this version may be left out of it.

    python3 tools/check_roadmap.py            # report
    python3 tools/check_roadmap.py --merge    # report, and merge what is due

Two ways work for a release goes missing, and this closes both.

A BRANCH written for a version and never merged. Branches named
`for-<version>/<slug>` are found by name, so work parked for 0.24.1
cannot land in 0.24.0 by accident and work meant for 0.24.0 cannot be
forgotten out of it. With --merge, a branch due for THIS version is
merged; a conflict stops the release rather than being resolved by a
script, because a conflict is a question about intent.

An ENTRY in ROADMAP.md that nobody did. The file lists what is owed
per version, including things with no code at all, and the section
for the version being released must be empty of outstanding work.
Deferring is legitimate and is the maintainer's decision: move the
entry to a later section, which is an edit only a person makes. This
tool never moves one.

Returns 0 when the version's road is clear, 1 with an explanation
otherwise. Run early -- it costs a second and it can save ninety
minutes of gates spent on a tree that was going to be refused.
"""
import argparse
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROADMAP = os.path.join(ROOT, "ROADMAP.md")

# A section is outstanding when it says nothing like this. Prose
# rather than a marker, because the file is written for a person
# first; the phrase is checked case-insensitively and the wording is
# quoted in the failure so nobody has to guess it.
CLEAR = "nothing outstanding"


def plugin_version():
  """The version a candidate would be built for, from metadata.txt.

  Returns:
    The value of the ``version=`` line, e.g. "0.24.0". This is the
    version whose roadmap section and branches are checked, because
    it is the one a candidate built now would carry.
  """
  path = os.path.join(ROOT, "weavingspace_qgis", "metadata.txt")
  with open(path, encoding="utf-8") as handle:
    for line in handle:
      if line.startswith("version="):
        return line.split("=", 1)[1].strip()
  sys.exit("metadata.txt names no version; nothing can be checked "
           "against it")


def branches_for(version):
  """Local branches named for this version that are not yet merged.

  Args:
    version: e.g. "0.24.0"; branches are matched as
      ``for-<version>/<anything>``.

  Returns:
    A list of branch names still holding commits the current HEAD
    does not have. A branch whose work is already merged is not
    listed, so a branch left behind after merging is untidy rather
    than an error.
  """
  listed = subprocess.run(
    ["git", "for-each-ref", "--format=%(refname:short)",
     f"refs/heads/for-{version}/*"],
    cwd=ROOT, capture_output=True, text=True)
  pending = []
  for name in listed.stdout.split():
    ahead = subprocess.run(["git", "log", "--oneline", f"HEAD..{name}"],
                           cwd=ROOT, capture_output=True, text=True)
    if ahead.stdout.strip():
      pending.append(name)
  return pending


def roadmap_section(version):
  """The ROADMAP text under this version's heading.

  Args:
    version: the version whose section to read.

  Returns:
    The section body as a string, or None when the file has no
    heading for this version -- which is itself a finding: a release
    with no roadmap section is one nobody wrote down.
  """
  if not os.path.exists(ROADMAP):
    return None
  with open(ROADMAP, encoding="utf-8") as handle:
    text = handle.read()
  match = re.search(
    rf"^##\s+{re.escape(version)}\b.*?$(.*?)(?=^##\s|\Z)",
    text, re.M | re.S)
  return match.group(1) if match else None


def main():
  """Check, and optionally merge, then explain anything outstanding.

  Returns:
    None; exits 0 when clear and 1 otherwise, having said which of
    the two kinds of work is in the way and what closing it means.
  """
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--merge", action="store_true",
                      help="merge branches due for this version")
  args = parser.parse_args()
  version = plugin_version()
  problems = []

  pending = branches_for(version)
  if pending and args.merge:
    for name in pending:
      print(f"merging {name}, which was written for {version}")
      merged = subprocess.run(["git", "merge", "--no-edit", name],
                              cwd=ROOT, capture_output=True, text=True)
      if merged.returncode != 0:
        # A conflict is a question about intent, and a release script
        # is the worst possible thing to answer it.
        subprocess.run(["git", "merge", "--abort"], cwd=ROOT,
                       capture_output=True)
        problems.append(
          f"{name} does not merge cleanly:\n"
          f"    {merged.stdout.strip().splitlines()[-1] if merged.stdout.strip() else merged.stderr.strip()}\n"
          f"    Merge it by hand and decide what the conflict means.")
    pending = branches_for(version)
  for name in pending:
    problems.append(
      f"{name} was written for {version} and is not merged. Merge it, "
      f"or rename it for the version it is really for.")

  section = roadmap_section(version)
  if section is None:
    problems.append(
      f"ROADMAP.md has no section for {version}. Every release says "
      f"what it owed, even when the answer is nothing.")
  elif CLEAR not in section.lower():
    outstanding = [line.strip() for line in section.splitlines()
                   if line.strip().startswith("**")]
    problems.append(
      f"ROADMAP.md still lists work under {version}:\n"
      + "\n".join(f"    {item}" for item in outstanding[:6])
      + f"\n    Do it, or move it to a later section -- deferring is "
        f"your decision and this tool will not make it. When the "
        f"section is genuinely clear, say so in it with the words "
        f"{CLEAR!r}.")

  if problems:
    print(f"{len(problems)} thing(s) stand between this tree and a "
          f"{version} candidate:\n")
    for problem in problems:
      print(f"  {problem}\n")
    return 1
  print(f"roadmap clear for {version}: no unmerged for-{version}/* "
        f"branches, nothing outstanding in ROADMAP.md")
  return 0


if __name__ == "__main__":
  sys.exit(main())
