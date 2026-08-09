#!/usr/bin/env python3
"""Keep the reusable skills in step with the documents they abstract.

    python3 tools/restamp_skills.py            # re-stamp after review
    python3 tools/restamp_skills.py --check    # fail if any has drifted

The skills in `.claude/skills/` generalise this project's procedures so
they can be reused elsewhere: the mutation campaign, supervising long
jobs, honest testing of interactive software, releasing as
publication. Each names the project documents it was drawn from, with
a hash of each one at the moment the skill was last reviewed against
it.

The point is not tamper-detection; nobody is forging anything. The
point is that an abstraction rots the moment its source moves and
nothing says so. When `docs/MUTATION-LOOP.md` gains a rule, the
mutation-campaign skill should either gain it too or be a deliberate
decision not to. Without a stamp that question is never asked, and the
skill quietly becomes a description of how we used to work.

So: `--check` fails the release when a source document has changed
since its skill was stamped, naming which skill is behind. You read
the change, decide whether the abstraction needs it, edit the skill if
so, and re-stamp. The re-stamp is the assertion that a person looked.
"""
import argparse
import hashlib
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SKILLS = os.path.join(ROOT, ".claude", "skills")


def digest(path):
  """The SHA-256 of a source document, or None when it is missing."""
  full = os.path.join(ROOT, path)
  if not os.path.exists(full):
    return None
  with open(full, "rb") as handle:
    return hashlib.sha256(handle.read()).hexdigest()


def skill_files():
  """Every SKILL.md under .claude/skills/.

  Returns:
    A list of absolute paths, sorted so output is stable between runs.
  """
  found = []
  if not os.path.isdir(SKILLS):
    return found
  for name in sorted(os.listdir(SKILLS)):
    path = os.path.join(SKILLS, name, "SKILL.md")
    if os.path.exists(path):
      found.append(path)
  return found


def sources_of(text):
  """The derived_from entries in a skill's frontmatter.

  Args:
    text: the whole SKILL.md.

  Returns:
    A list of (path, recorded_sha) pairs. Parsing is a small regex
    rather than a YAML dependency, because the frontmatter here is a
    fixed shape this tool writes and reads, and a parser would be one
    more thing that can disagree with the file.
  """
  block = re.search(r"^derived_from:\n((?:\s+-\s+path:.*\n\s+sha256:.*\n)+)",
                    text, re.M)
  if not block:
    return []
  return re.findall(r"-\s+path:\s*(\S+)\s*\n\s+sha256:\s*(\S+)",
                    block.group(1))


def main():
  """Compare each skill against its source documents, then stamp or report.

  Returns:
    0 when every skill's recorded hashes match the documents it was
    drawn from, 1 when --check finds drift or when any mode finds a
    named source that no longer exists. Without --check, the drifted
    ``sha256:`` values in .claude/skills/*/SKILL.md are rewritten to
    the current ones; with it, nothing is written at all.

  Re-stamping is an assertion, not a repair: it says a person read
  what changed in the source document and decided whether the
  abstraction needed it. That is why --check reports drift instead of
  fixing it, and why the fixing mode is a separate deliberate run.

  A missing source document fails in BOTH modes. Re-stamping cannot
  invent a hash for a file that is gone, and leaving it silent would
  let a skill go on naming a document no reader can open.
  """
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--check", action="store_true",
                      help="report drift and fail, changing nothing")
  args = parser.parse_args()

  drifted, missing, stamped = [], [], 0
  for path in skill_files():
    with open(path, encoding="utf-8") as handle:
      text = handle.read()
    name = os.path.basename(os.path.dirname(path))
    updated = text
    for source, recorded in sources_of(text):
      current = digest(source)
      if current is None:
        missing.append(f"{name} says it is derived from {source}, "
                       f"which does not exist")
        continue
      if current == recorded:
        continue
      drifted.append(f"{name} was written against an older "
                     f"{source}; review the change and re-stamp")
      updated = updated.replace(f"sha256: {recorded}",
                                f"sha256: {current}", 1)
    if updated != text and not args.check:
      with open(path, "w", encoding="utf-8") as handle:
        handle.write(updated)
      stamped += 1

  if args.check:
    problems = drifted + missing
    if problems:
      print(f"{len(problems)} skill(s) out of step with the documents "
            f"they abstract:\n")
      for problem in problems:
        print(f"  {problem}")
      print("\nRead what changed, update the skill if the abstraction "
            "needs it, then run tools/restamp_skills.py.")
      return 1
    print(f"skills in step with their sources "
          f"({len(skill_files())} checked)")
    return 0

  if missing:
    for problem in missing:
      print(f"  {problem}")
    return 1
  print(f"re-stamped {stamped} skill(s); "
        f"{len(skill_files())} checked")
  return 0


if __name__ == "__main__":
  sys.exit(main())
