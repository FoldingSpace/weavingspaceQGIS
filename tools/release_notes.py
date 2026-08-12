#!/usr/bin/env python3
"""Assemble the release notes: the reviewed prose, plus the facts.

    python3 tools/release_notes.py                 # to stdout
    python3 tools/release_notes.py reports/v0.24.0 # and write notes.md there

Release notes have two jobs and one document usually does neither
well. A user wants to know what changed and whether it affects them,
in a paragraph. Anyone evaluating the release wants to know what was
measured, and to be able to check. Writing one text for both produces
either a changelog nobody reads or a summary nobody trusts.

So this composes rather than writes:

  the CONCISE half is the ``changelog=`` entry in metadata.txt for
    this version. It is written by a person, reviewed through
    tools/text_review.py like every other sentence a user meets, and
    is already what QGIS's plugin manager shows -- so the release
    page and the plugin manager cannot drift apart, because they are
    the same words;

  the COMPREHENSIVE half is generated from what the release actually
    measured: how many tests ran, how many guard a defect that
    really happened, the mutation bound, and what is attached.

Nothing here invents prose. If the changelog entry for this version
is missing, this refuses -- a release whose notes were written by a
script is a release nobody described.

Before this existed the GitHub release body was the testing report,
a per-test listing which is admirable evidence and unreadable as an
announcement.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = "https://github.com/FoldingSpace/weavingspaceQGIS"


def metadata_field(name):
  """One field from metadata.txt, continuation lines included.

  Args:
    name: the field, e.g. "version" or "changelog".

  Returns:
    The value as a string, with indented continuation lines joined,
    or "" when the field is absent. metadata.txt is the single place
    the version and the user-facing changelog are declared, so
    everything here reads from it rather than keeping a second copy.
  """
  path = os.path.join(ROOT, "weavingspace_qgis", "metadata.txt")
  lines, collecting = [], False
  with open(path, encoding="utf-8") as handle:
    for line in handle:
      if line.startswith(f"{name}="):
        lines.append(line.split("=", 1)[1].rstrip())
        collecting = True
      elif collecting and line[:1] in (" ", "\t"):
        lines.append(line.strip())
      elif collecting:
        break
  return "\n".join(lines).strip()


def entry_for(changelog, version):
  """The changelog paragraph for one version.

  Args:
    changelog: the whole changelog field.
    version: the version whose entry is wanted.

  Returns:
    The text of that version's entry with the version number
    stripped from the front, or None when there is none -- which is
    a refusal rather than an empty section, because notes nobody
    wrote are worse than notes nobody has.
  """
  match = re.search(rf"{re.escape(version)}\s+(.*?)(?=\n\s*\d+\.\d+\.\d+\s|\Z)",
                    changelog, re.S)
  if not match:
    return None
  return " ".join(match.group(1).split())


def measured(version):
  """What this release's own gates recorded, if they have run.

  Args:
    version: the version whose reports directory to read.

  Returns:
    A list of already-formatted lines. Each is omitted rather than
    guessed when its source is absent, so notes built before the
    gates have run are shorter rather than wrong.
  """
  facts = []
  test_map = os.path.join(ROOT, "docs", "TEST-MAP.md")
  if os.path.exists(test_map):
    text = open(test_map, encoding="utf-8").read()
    counted = re.search(r"(\d+)\s+tests?\s+across\s+(\d+)\s+areas", text)
    guarding = sum(int(n) for n in re.findall(r"\|\s*\d+\s*\|\s*(\d+)\s*\|",
                                              text))
    if counted:
      facts.append(
        f"- {counted.group(1)} tests across {counted.group(2)} areas"
        + (f", {guarding} of them guarding a defect that actually "
           f"happened here" if guarding else ""))
  register = os.path.join(ROOT, "docs", "BUG-REGISTER.md")
  if os.path.exists(register):
    text = open(register, encoding="utf-8").read()
    found = re.search(r"(\d+)\s+defects?", text)
    if found:
      facts.append(f"- {found.group(1)} defects on the register, each "
                   f"with the test that would catch it again")
  return facts


def main():
  """Compose the notes and print them; write them too if asked.

  Returns:
    None. Exits non-zero when this version has no changelog entry,
    because that is the half a person has to write and no tool
    should paper over it.
  """
  version = metadata_field("version")
  entry = entry_for(metadata_field("changelog"), version)
  if not entry:
    sys.exit(
      f"metadata.txt has no changelog entry for {version}. That "
      f"paragraph is the release notes -- the part a user reads and "
      f"the part the plugin manager shows -- and it is written by a "
      f"person, not generated. Add it, then run "
      f"tools/text_review.py so it is reviewed like every other "
      f"sentence a user meets.")

  lines = [f"# WeavingSpace {version}", "", entry, ""]
  facts = measured(version)
  if facts:
    lines += ["## What was measured", ""] + facts + [""]
  lines += [
    "## In this release", "",
    "- `weavingspace_qgis.zip` — install through Plugins > Manage and "
    "Install Plugins... > Install from ZIP",
    "- `testing-report.md` — every test with its result and measured "
    "values",
    "- `visual-comparison.pdf` — each rendered map scored against the "
    "weavingspace library's own renderer, in a perceptual colourspace",
    "",
    f"How this is built and tested: [docs/PUBLISHING.md]"
    f"({REPO}/blob/main/docs/PUBLISHING.md) and "
    f"[docs/TESTING.md]({REPO}/blob/main/docs/TESTING.md). The "
    f"campaigns behind it are in [docs/process/]({REPO}/tree/main/"
    f"docs/process).",
  ]
  # The line a reader of a GitHub release looks for, in the place and
  # the wording they look for it. Omitted rather than guessed when
  # there is no previous tag to compare against -- the first release
  # of anything has nothing to diff.
  import subprocess
  previous = subprocess.run(
    ["git", "describe", "--tags", "--abbrev=0", "HEAD^"],
    cwd=ROOT, capture_output=True, text=True)
  if previous.returncode == 0 and previous.stdout.strip():
    lines += ["", f"**Full changelog**: {REPO}/compare/"
                  f"{previous.stdout.strip()}...v{version}"]
  notes = "\n".join(lines).rstrip() + "\n"
  print(notes)
  if len(sys.argv) > 1:
    out = os.path.join(sys.argv[1], "release-notes.md")
    os.makedirs(sys.argv[1], exist_ok=True)
    with open(out, "w", encoding="utf-8") as handle:
      handle.write(notes)
    print(f"(written to {os.path.relpath(out, ROOT)})", file=sys.stderr)


if __name__ == "__main__":
  main()
