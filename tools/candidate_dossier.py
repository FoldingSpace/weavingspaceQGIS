#!/usr/bin/env python3
"""Everything about a release candidate, on one page, for review.

    python3 tools/candidate_dossier.py 0.24.0rc3

Written by ``release.py --rc`` beside the candidate zip. It exists
because "review the release" is otherwise an instruction to read a
repository: the reviewer has to know what changed, what was measured,
what is being claimed, what is knowingly wrong, and what to actually
try in QGIS. Those live in six different places, and nobody assembles
them by hand more than once.

Everything here is derived from the repository as it stands. Nothing
is written by hand and nothing is remembered from a previous run, so
a dossier cannot describe a candidate other than the one just built.

What it deliberately includes, and why each earns its place:

* WHAT CHANGED since the previous candidate, not only since the last
  release. Reviewing rc3 means reviewing what rc2's feedback
  produced.
* THE NUMBERS WITH THEIR SCOPE. A mutation rate without its stratum,
  or a coverage figure without its date, is the kind of claim this
  project has already had to correct four times.
* WHAT IS KNOWINGLY WRONG: accepted survivors, open defects, the
  limitations already recorded. A review that only sees the good news
  is not a review.
* WHAT TO TRY. The reviewer cannot know which parts of the plugin
  this candidate is most likely to have broken. The changed files
  say, and that list is far more useful than "please test it".
"""

import argparse
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# Which parts of the plugin a changed file puts at risk, so the
# dossier can say what to exercise rather than asking for a general
# look. Keyed by file, since that is what git reports.
AT_RISK = {
  "dialog.py": "the dialog: controls, the table, the preview, live "
               "update, and anything that runs a generation",
  "category_editor.py": "the Categorical colour editor: open it from "
                        "a categorized element and change colours",
  "bridge.py": "symbology and output: renderers, ramps, the "
               "GeoPackage, the outlines layer",
  "catalog.py": "the design catalogue: element counts and families",
  "worker.py": "generation and cancelling, especially mid-run",
  "compat.py": "anything QGIS-version-specific; try the oldest QGIS "
               "you support",
  "deps.py": "a profile WITHOUT the dependencies, to see the "
             "provisioner run",
  "help_content.py": "the Help tab",
  "plugin.py": "the menu item, the toolbar button, enabling and "
               "disabling the plugin",
  "perception.py": "the colour-legibility warning (Map options)",
}


def shell(command, default=""):
  """Run a command and return its output, or a default if it fails.

  Args:
    command: argument list.
    default: what to return when the command fails or is missing.

  Returns:
    Stripped stdout, or default. Nothing here is important enough to
    stop a dossier being written: a missing git history or an absent
    report should leave a gap in the page, not an exception.
  """
  try:
    done = subprocess.run(command, cwd=ROOT, capture_output=True,
                          text=True, timeout=60)
    return done.stdout.strip() if done.returncode == 0 else default
  except Exception:
    return default


def previous_candidate(label):
  """The candidate before this one, if there is one.

  Args:
    label: this candidate's label, e.g. "0.24.0rc3".

  Returns:
    The previous label ("0.24.0rc2") or None for rc1. Used to scope
    "what changed" to the last review round rather than to the last
    release, since that is what a reviewer is being asked about.
  """
  match = re.match(r"(.+)rc(\d+)$", label)
  if not match or int(match.group(2)) <= 1:
    return None
  return f"{match.group(1)}rc{int(match.group(2)) - 1}"


def changed_files(since_ref):
  """Repository files changed since a git ref.

  Args:
    since_ref: a tag or commit, or None for "everything uncommitted
      plus the last release".

  Returns:
    A sorted list of repo-relative paths, empty when git cannot say.
  """
  if since_ref:
    out = shell(["git", "diff", "--name-only", since_ref])
  else:
    out = shell(["git", "diff", "--name-only", "HEAD"])
  return sorted(p for p in out.split("\n") if p)


def suite_numbers():
  """Test counts from the most recent testing report, if present.

  Returns:
    A one-line summary, or a note that no report was found. Read from
    the report rather than by running the suite: this tool assembles
    evidence, it does not produce it.
  """
  reports = os.path.join(ROOT, "reports")
  if not os.path.isdir(reports):
    return "no reports directory; run a release stage first"
  versions = sorted(os.listdir(reports))
  for version in reversed(versions):
    path = os.path.join(reports, version, "testing-report.md")
    if os.path.exists(path):
      text = open(path, encoding="utf-8").read()
      passed = len(re.findall(r"^\|\s*PASS", text, re.M)) or \
          text.count("PASS")
      failed = len(re.findall(r"^\|\s*FAIL", text, re.M))
      return (f"{passed} passing, {failed} failing "
              f"(from reports/{version}/testing-report.md)")
  return "no testing report found"


def test_map_summary():
  """The suite's shape, from docs/TEST-MAP.md.

  Returns:
    The area table if the map exists, else a note. Included whole
    because it is short and because the ratio of tests to tests
    GUARDING A REAL DEFECT is the most honest single view of a suite.
  """
  path = os.path.join(ROOT, "docs", "TEST-MAP.md")
  if not os.path.exists(path):
    return "no test map; run tools/test_map.py"
  text = open(path, encoding="utf-8").read()
  table = re.search(r"\| area \|.*?(?=\n\n)", text, re.S)
  head = re.search(r"^(\d+) tests across (\d+) areas", text, re.M)
  lines = []
  if head:
    lines.append(f"{head.group(1)} tests across {head.group(2)} areas.")
  if table:
    lines.append(table.group(0))
  return "\n\n".join(lines) if lines else "test map unreadable"


def bug_register_count():
  """How many defects the suite guards, from the register."""
  path = os.path.join(ROOT, "docs", "BUG-REGISTER.md")
  if not os.path.exists(path):
    return "no bug register"
  text = open(path, encoding="utf-8").read()
  found = re.search(r"(\d+)\s+defect", text)
  return (f"{found.group(1)} defects guarded by a regression test"
          if found else "bug register present")


def text_state():
  """Whether any user-facing text is unreviewed."""
  approved = os.path.join(ROOT, "docs", "text-approved.json")
  if not os.path.exists(approved):
    return "no approval record; run tools/text_review.py"
  count = len(json.load(open(approved, encoding="utf-8")))
  pending = shell([sys.executable,
                   os.path.join("tools", "text_review.py"), "--check"],
                  default="")
  clear = "none pending" in pending
  return (f"{count} pieces approved, "
          f"{'nothing pending' if clear else 'SOMETHING PENDING'}")


def what_to_try(files):
  """What a reviewer should exercise, given what changed.

  Args:
    files: repo-relative paths changed since the previous candidate.

  Returns:
    A list of prompts. Derived from the changed files, because the
    reviewer cannot be expected to guess which part of the plugin
    this candidate put at risk, and "please have a look" wastes the
    one thing a human reviewer offers that no test does.
  """
  hits = []
  for path in files:
    name = os.path.basename(path)
    if name in AT_RISK and AT_RISK[name] not in hits:
      hits.append(AT_RISK[name])
  if not hits:
    hits.append("nothing in the plugin package changed; this "
                "candidate differs only in tooling, tests or "
                "documentation")
  return hits


def commit_of(label):
  """The commit a previous dossier recorded, if there is one.

  Args:
    label: a candidate label, e.g. "0.24.0rc2".

  Returns:
    The git sha that candidate was built from, or None. Each dossier
    records its own commit for exactly this purpose: "what changed
    since the last candidate" cannot be answered from tags, because a
    candidate is never tagged — that is the point of a candidate.
  """
  if not label:
    return None
  path = os.path.join(ROOT, "dist", f"CANDIDATE-{label}.md")
  if not os.path.exists(path):
    return None
  found = re.search(r"^built from commit `([0-9a-f]+)`",
                    open(path, encoding="utf-8").read(), re.M)
  return found.group(1) if found else None


def render(label, previous):
  """Assemble the dossier.

  Args:
    label: this candidate's label, e.g. "0.24.0rc3".
    previous: the previous candidate's label, or None.

  Returns:
    The document text.
  """
  # Diff against the commit the PREVIOUS candidate recorded. Tags do
  # not help here: a candidate is deliberately never tagged, so there
  # is nothing in git to diff against except what a dossier wrote
  # down. With no previous candidate, fall back to the last release
  # tag, and failing that report the working tree.
  here = shell(["git", "rev-parse", "--short", "HEAD"], "unknown")
  earlier = commit_of(previous)
  if not earlier:
    earlier = shell(["git", "describe", "--tags", "--abbrev=0"], "")
  files = changed_files(earlier or None)
  plugin_files = [f for f in files if f.startswith("weavingspace_qgis/")]
  commits = shell(["git", "log", "--oneline", "-12"])

  out = [
    f"# Release candidate {label}",
    "",
    f"built from commit `{here}`",
    "",
    "Built locally. Nothing has been committed, tagged or published.",
    "Read this, try the plugin, and say what should change; the next",
    "candidate answers the feedback.",
    "",
    "## What to try in QGIS",
    "",
    f"Installed as version `{label}` in every QGIS profile on this",
    "machine that already had the plugin. Restart QGIS first — Python",
    "modules already imported stay imported.",
    "",
  ]
  out += [f"- {item}" for item in what_to_try(files)]
  out += [
    "",
    "## What changed",
    "",
    (f"{len(files)} file(s) changed since "
     f"{('candidate ' + previous) if commit_of(previous) else (earlier or 'the working tree')}"
     f", {len(plugin_files)} of them in the plugin itself."),
    "",
    "Recent commits:",
    "",
    "```",
    commits or "(no git history)",
    "```",
    "",
    "## What was measured",
    "",
    f"- Tests: {suite_numbers()}",
    f"- {bug_register_count()}",
    f"- User-facing text: {text_state()}",
    "",
    "Mutation score is NOT re-measured for a candidate: it takes",
    "hours and a candidate is meant to be cheap. The standing figure",
    "and its scope are in docs/MUTATION-TESTING.md, which states the",
    "batch, the bound and what it does not cover.",
    "",
    "## The shape of the suite",
    "",
    test_map_summary(),
    "",
    "## What is knowingly wrong",
    "",
    "Accepted mutation survivors, open defects and limitations are in",
    "docs/MUTATION-TESTING.md and dev/state-of-play.md. A review that",
    "only sees the good news is not a review; if anything in those",
    "lists should block the release, say so now rather than after.",
    "",
  ]
  return "\n".join(out) + "\n"


def main():
  """Write the dossier for a candidate.

  Returns:
    0 always. A dossier that cannot be assembled still gets written,
    with the gaps visible, because a missing section is information
    and a missing page is not.
  """
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("label", help="candidate label, e.g. 0.24.0rc3")
  args = parser.parse_args()

  target = os.path.join(ROOT, "dist", f"CANDIDATE-{args.label}.md")
  os.makedirs(os.path.dirname(target), exist_ok=True)
  with open(target, "w", encoding="utf-8") as handle:
    handle.write(render(args.label, previous_candidate(args.label)))
  print(f"wrote {os.path.relpath(target, ROOT)}")
  return 0


if __name__ == "__main__":
  sys.exit(main())
