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

# Spans that are somebody TALKING ABOUT the phrase rather than saying
# it: "..." straight or curly, and `...` for code.
QUOTED = re.compile(r'"[^"]*"|“[^”]*”|`[^`]*`', re.S)


def says_it_is_clear(section: str) -> bool:
  """Does this section DECLARE itself clear, rather than mention the phrase?

  Args:
    section: the version's own slice of ROADMAP.md.

  Returns:
    True when the clearance phrase appears outside every quotation.

  A BARE SUBSTRING SEARCH LET A SECTION PASS BY SAYING THE OPPOSITE.
  0.24.3's own section carried the sentence "WHAT IS STILL OWED, and
  it is the reason this section does not yet say 'nothing
  outstanding'" -- written honestly, and read by this gate as the
  declaration it was denying. So a tree with a page of outstanding
  work was cleared for a candidate, which is the fault this check
  exists to prevent arriving through the check itself.

  A QUOTED PHRASE IS A MENTION, NOT A STATEMENT, and that distinction
  is the whole of the repair: the roadmap explains its own convention
  in prose, so quoting the words is something it does legitimately and
  often. Stripping quoted spans before looking keeps the phrase
  prose-first, which is why it was chosen over a marker, while making
  it impossible to satisfy by discussing it.
  """
  return CLEAR in QUOTED.sub(" ", section).lower()


def outstanding_entries(section: str):
  """The bold entries a version still owes, and whether they are named.

  Args:
    section: the version's own slice of ROADMAP.md.

  Returns:
    A pair (named, entries). `named` is True when the section carries
    a heading that says what is OWED, in which case `entries` holds
    only the bold lines beneath it. Otherwise `named` is False and
    `entries` is every bold line in the section, which the caller must
    describe honestly rather than present as a list of debts.

  A LIST THAT NAMES THE WRONG THINGS TEACHES PEOPLE TO SILENCE THE
  GATE. This used to take every bold line in the section, and a
  version's section opens with what it GIVES YOU and what it PUTS
  RIGHT -- so a refusal listed five delivered features as work still
  owed. That is the shape this project already names about a checker
  whose failures are mostly false: the true ones go with them.

  THE FILE'S OWN CONVENTION IS THE HEADING, so that is what is read
  rather than a guess about wording. Where a section does not use one,
  saying so beats pretending the list means something it does not.
  """
  chunks = re.split(r"^###\s+(.*)$", section, flags=re.M)
  # chunks alternates: preamble, heading, body, heading, body...
  owed = []
  for index in range(1, len(chunks) - 1, 2):
    if re.search(r"outstanding|still owed|owes", chunks[index], re.I):
      owed.append(chunks[index + 1])
  bold = lambda text: [line.strip() for line in text.splitlines()
                       if line.strip().startswith("**")]
  if owed:
    return True, [item for body in owed for item in bold(body)]
  return False, bold(section)


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
    # NEVER merge into a dirty tree. A merge with uncommitted changes
    # either refuses halfway or entangles them, and an automated step
    # must not be the thing that decides what happens to work
    # somebody had in progress. (Written after doing exactly that to
    # my own uncommitted work with a reset, minutes after arguing for
    # this guard: knowing the rule and following it are separate.)
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT,
                           capture_output=True, text=True).stdout.strip()
    if dirty:
      print(f"NOT merging: the working tree has uncommitted changes "
            f"in {len(dirty.splitlines())} file(s). Commit or stash "
            f"them first; a merge should not decide what happens to "
            f"work in progress.")
      return 1
    # Printed BEFORE the merges, so the undo is in the log even if
    # something later goes wrong. A release that aborts after this
    # point leaves the merge in place, which is not damage but is a
    # surprise, and a surprise with no undo written down is worse.
    before = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                            capture_output=True, text=True).stdout.strip()
    print(f"merging {len(pending)} branch(es) due for {version}. "
          f"To undo all of it: git reset --hard {before[:12]}")
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
    landed = subprocess.run(["git", "log", "--oneline", f"{before}..HEAD"],
                            cwd=ROOT, capture_output=True,
                            text=True).stdout.strip()
    if landed:
      # say what arrived: a merge nobody announced is one nobody
      # knows to look for when something later behaves oddly
      print("merged:\n" + "\n".join(f"    {line}"
                                     for line in landed.splitlines()))
  for name in pending:
    problems.append(
      f"{name} was written for {version} and is not merged. Merge it, "
      f"or rename it for the version it is really for.")

  # Every parked branch must be DESCRIBED, whatever version it is
  # for. A branch nobody wrote an entry for is work whose purpose
  # survives only in whoever made it -- which is the failure this
  # file exists to prevent, arriving by the other door.
  # refs/heads/for-* does NOT match for-0.24.1/slug: the glob stops
  # at the slash, so the pattern found nothing and the check passed
  # vacuously when first written. List every branch and filter here.
  all_parked = subprocess.run(
    ["git", "for-each-ref", "--format=%(refname:short)", "refs/heads/"],
    cwd=ROOT, capture_output=True, text=True)
  for name in all_parked.stdout.split():
    if not name.startswith("for-") or "/" not in name:
      continue
    parked_version = name.split("/")[0][len("for-"):]
    if roadmap_section(parked_version) is None:
      problems.append(
        f"{name} is parked for {parked_version}, which ROADMAP.md "
        f"does not describe. Add a section for it saying what the "
        f"branch is and what must be true before it merges; a branch "
        f"alone cannot tell you it is unfinished.")

  section = roadmap_section(version)
  if section is None:
    problems.append(
      f"ROADMAP.md has no section for {version}. Every release says "
      f"what it owed, even when the answer is nothing.")
  elif not says_it_is_clear(section):
    named, whole = outstanding_entries(section)
    problems.append(
      (f"ROADMAP.md still lists work under {version}"
       + (":" if named else ", though its section has no heading "
                           "naming what is owed. Every bold entry in "
                           "it, which may include what the version "
                           "DELIVERS rather than what it owes:") + "\n")
      + "\n".join(f"    {item}" for item in whole[:6])
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
