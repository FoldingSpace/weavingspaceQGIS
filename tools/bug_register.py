#!/usr/bin/env python3
"""Build the register of defects this suite guards, from the suite.

    python3 tools/bug_register.py            # writes docs/BUG-REGISTER.md
    python3 tools/bug_register.py --check    # fails if the file is stale

CLAUDE.md says every fixed bug gets a regression test and that a bug
without one is not fixed. That is a strong claim and it was
unauditable: the tests existed, but nothing could count them or say
which defect each one pinned, so the claim rested on memory.

The convention is one line in a test's docstring:

    Regression: Generate pressed inside the 350 ms preview debounce
      tiled the PREVIOUS design. [ui-vs-library]

Everything after "Regression:" up to the next blank line is the
description; a bracketed tag at the end records HOW it was found. That
last part earns its keep over time: it says which shape of test is
actually catching defects, which is the difference between spending
the next afternoon on more unit tests or on another differential
sweep.

Tests without such a line are not delinquent. Most tests describe how
the software should behave rather than a specific past failure, and
inventing a defect for each would make the register useless.
"""
import argparse
import ast
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SUITES = [os.path.join("tests", "run_tests.py"),
          os.path.join("tests", "visual_tests.py")]
OUT = os.path.join("docs", "BUG-REGISTER.md")

# How a defect came to light. Kept short so the register stays
# readable, and open-ended so a new shape of testing can be recorded
# the first time it finds something.
HOW = {
  "ui-vs-library": "driving the UI and rebuilding the same map from the "
                   "library directly",
  "colourspace": "comparing rendered output against the reference in "
                 "Lab space",
  "race": "race and stress testing",
  "integration": "a multi-step session test",
  # Added 2026-08-19, the first time a defect was recorded as found
  # this way rather than by an instrument aimed at it. The whole suite
  # is not the same shape as any one test in it: what it catches is a
  # change that moved something under a test written about something
  # else, and three of those in one day were caught by PREMISE
  # assertions refusing to report a vacuous pass. The vocabulary is
  # open-ended for exactly this.
  "suite": "the functional suite, run whole",
  "mutation": "the mutation campaign",
  "hostile-data": "the hostile data corpus",
  "family-audit": "a family audit of the claims the software makes",
  "second-machine": "running the suite somewhere other than the "
                    "machine it was written on",
  "user": "reported by a user",
  "review": "reading the code",
  # Reading the DOCUMENTS is its own direction and has its own row in
  # docs/process/HUNT-RECORD.md: it found a method defined twice in one
  # class, an uncached swatch redrawn 306,558 times, and on 2026-08-31 a
  # release gate blind to everything quoted after a fenced block. None
  # of those came from a question about the code, so filing them under
  # "reading the code" would blur the one signal this register exists
  # to give -- which shape of work is actually catching defects.
  "docs-reading": "re-reading the procedural documents",
  "hunt": "a bug hunt pointed in a named direction",
  "differential": "a randomised differential sweep",
  # Not a shape of test at all: a defect whose provenance was not
  # written down at the time. It is spelled out rather than left
  # blank so that nothing is EVER silently unrecorded -- a reader
  # sees a deliberate mark, and tools/check_standards.py refuses a
  # Regression line with no tag, so a new one cannot join these.
  # (Maintainer's instruction, 2026-08-15, on finding 100 of them.)
  "unrecorded": "not written down at the time",
}


def entries():
  """Every Regression: line in the suites, with its test.

  Returns:
    A list of dicts with test, defect, how, and file. Docstrings are
    taken from the AST rather than matched with a pattern: the first
    version of this tool used a regex spanning "def ... docstring",
    which crosses a function boundary as soon as a signature wraps
    over two lines, and it duly credited one test with another
    test's defect.
  """
  found = []
  for relative in SUITES:
    path = os.path.join(ROOT, relative)
    if not os.path.exists(path):
      continue
    with open(path, encoding="utf-8") as handle:
      source = handle.read()
    # Ask Python which docstring belongs to which function rather than
    # pattern-matching for it. A regex over "def ... docstring" spans
    # function boundaries the moment a signature wraps across lines,
    # and it did: the first run of this tool credited one test's
    # defect to another test entirely.
    try:
      tree = ast.parse(source, path)
    except SyntaxError as exc:
      print(f"  cannot parse {relative}: {exc}")
      continue
    for node in ast.walk(tree):
      if not isinstance(node, ast.FunctionDef) \
              or not node.name.startswith("test_"):
        continue
      doc = ast.get_docstring(node) or ""
      name = node.name
      # ANCHORED TO THE START OF A LINE, and that is the whole point.
      # An unanchored search matches the marker wherever it appears,
      # including inside a sentence ABOUT it -- and a docstring saying
      # "No ``Regression:`` line, deliberately" duly published the rest
      # of that sentence as a defect this suite guards, inflating the
      # count by one and putting a claim into docs/BUG-REGISTER.md that
      # no test supported. Worse, check_standards then demanded a
      # [shape] tag on the phantom, and somebody supplied one, so the
      # file ended up carrying a tag on a paragraph declaring it had no
      # line to tag. Real lines always begin one: ast.get_docstring
      # cleans the indentation, so `^[ \t]*` is all the leeway needed.
      # (Found 2026-08-16 by reading the generated register.)
      note = re.search(r"^[ \t]*Regression:\s*(.+?)(?:\n\s*\n|\Z)",
                       doc, re.S | re.M)
      if not note:
        continue
      text = " ".join(note.group(1).split())
      tag = re.search(r"\[([a-z-]+)\]\s*$", text)
      how = tag.group(1) if tag else "unrecorded"
      if tag:
        text = text[:tag.start()].strip()
      found.append({"test": name, "defect": text, "how": how,
                    "file": relative})
  return sorted(found, key=lambda e: (e["how"], e["test"]))


def render(found):
  """The register as markdown."""
  lines = [
    "# Defects this suite guards",
    "",
    "Generated by `tools/bug_register.py` from `Regression:` lines in",
    "the tests themselves, so it cannot drift from what is actually",
    "guarded. To add an entry, write the line in the test's docstring;",
    "there is no separate list to remember.",
    "",
    f"{len(found)} defect(s) with a regression test.",
    "",
  ]
  by_how = {}
  for entry in found:
    by_how.setdefault(entry["how"], []).append(entry)
  for how in sorted(by_how):
    lines.append(f"## Found by {HOW.get(how, how)}")
    lines.append("")
    for entry in by_how[how]:
      lines.append(f"- **{entry['defect']}**  \n  guarded by "
                   f"`{entry['test']}`")
    lines.append("")

  # The count per shape is the useful part over time: it says where
  # the next afternoon of testing effort is best spent.
  lines.append("## Which shape of test found them")
  lines.append("")
  for how in sorted(by_how, key=lambda k: -len(by_how[k])):
    lines.append(f"- {HOW.get(how, how)}: {len(by_how[how])}")
  lines.append("")
  return "\n".join(lines)


def main():
  """Regenerate docs/BUG-REGISTER.md, or report that it has gone stale.

  Returns:
    0 when the register was written, or when --check finds the file
    on disk already identical to what the suites say it should be; 1
    when --check finds it stale. Without --check, docs/BUG-REGISTER.md
    is overwritten -- the only thing this tool mutates.

  --check exists because the register is generated rather than
  maintained. A Regression: line added without regenerating leaves a
  file that reads as the list of defects this suite guards while
  being short by one, and a register that lags the tests is worse
  than no register, since nothing about it looks wrong.
  """
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--check", action="store_true",
                      help="do not write; fail if the register on disk "
                           "is not what the tests would produce")
  args = parser.parse_args()

  found = entries()
  text = render(found)
  path = os.path.join(ROOT, OUT)
  current = ""
  if os.path.exists(path):
    with open(path, encoding="utf-8") as handle:
      current = handle.read()

  if args.check:
    if current != text:
      print("docs/BUG-REGISTER.md is out of date; run "
            "tools/bug_register.py")
      return 1
    print(f"bug register current: {len(found)} defect(s) guarded")
    return 0

  with open(path, "w", encoding="utf-8") as handle:
    handle.write(text)
  print(f"wrote {OUT}: {len(found)} defect(s) guarded")
  return 0


if __name__ == "__main__":
  sys.exit(main())
