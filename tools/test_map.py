#!/usr/bin/env python3
"""What the test suite covers, on one page.

    python3 tools/test_map.py            # write docs/TEST-MAP.md
    python3 tools/test_map.py --check    # fail if it is out of date

The suite is one file of tens of thousands of lines and some hundreds
of tests -- deliberately not counted here, because a count in prose is
true until somebody adds one, and the current figures are at the top
of the document this tool generates. That is navigable by search and
not by reading, so
the question a maintainer actually has — "what does this cover, and
what does it not?" — cannot be answered by opening it. Splitting the
file into modules would not answer it either: coverage of intent is
not the same shape as file boundaries.

So this reads the suite instead and writes the index. Everything here
is derived, never maintained by hand: the display names come from the
``check(...)`` calls in main(), the one-line purposes from the first
sentence of each test's docstring, and the marks from what each test
actually does.

Four marks, and the useful one is the last:

  visual   the test renders a map or a widget and measures the image
  race     it drives something while a run or a debounce is in flight
  family   it asserts over a TABLE of cases rather than one example
  guards   its docstring carries a ``Regression:`` line, meaning it
           was written because that defect actually happened here

That last column is the one worth scanning. A test with a Regression
line guards ground we have already fallen through; a test without one
guards ground we merely imagined. An area with many tests and no
Regression lines is not necessarily well tested — it may only be
well imagined.
"""

import argparse
import ast
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SUITES = [os.path.join(ROOT, "tests", "run_tests.py"),
          os.path.join(ROOT, "tests", "visual_tests.py")]
MAP = os.path.join(ROOT, "docs", "TEST-MAP.md")

# Areas, matched against a test's name and its first docstring line.
# Ordered: the first area whose words match wins, so put the specific
# before the general. "Other" catching a lot is itself a finding —
# it means the suite has grown a topic nobody has named.
AREAS = [
  ("The categorical colour editor",
   ("colour editor", "hand-pick", "hand pick", "no-data row",
    "edit colours", "picked colour", "custom")),
  ("Runs, races and concurrency",
   ("race", "cancel", "live update", "debounce", "task", "progress",
    "stress", "fuzz", "adversarial", "sequence", "during a run",
    "overlap", "zombie", "lifecycle of a run")),
  ("What the user reads",
   ("tooltip", "explains itself", "help tab", "user guide", "notice",
    "warn", "message", "says which", "legib", "text")),
  ("The preview widget",
   ("preview", "design view", "swatch", "glyph", "shells")),
  ("Colour and symbology",
   ("colour", "color", "ramp", "palette", "class", "categor",
    "opacity", "separate", "renderer", "symbol")),
  ("Agreement with the library",
   ("ui vs library", "library", "metamorphic", "differential",
    "random designs", "inset percentage")),
  # Robustness comes BEFORE the output rule, and that order is the
  # whole point. Matching is first-rule-wins on the test's display
  # name, and the output rule's "layer" keyword is greedy: it claimed
  # "hostile numbers", "a reprojected layer", "the layer changes
  # without being edited" and two more, so the map reported five
  # tests in the robustness area while a dozen sat elsewhere. A map
  # that misplaces its own coverage is worse than no map, because it
  # is consulted when deciding where to write tests next.
  ("Robustness and the world outside",
   ("hostile", "awkward", "locale", "data underneath", "data changed",
    "qgis changes", "deps", "missing", "plugin lifecycle", "recover",
    "nonsense", "extremes", "reprojected", "without being edited",
    "will not say", "no crs", "refreshes itself", "uncommitted")),
  ("Output: layers, groups, GeoPackage",
   ("layer", "group", "gpkg", "geopackage", "output", "outline",
    "export", "region chooser")),
  ("Design: units, families, modifiers",
   ("famil", "modifier", "rotate", "skew", "inset", "spacing",
    "catalogue", "catalog", "offset", "grid", "weave", "strand",
    "tiling", "design", "element count", "control")),
]


def registered_names(source):
  """Display name for each test function, from the check() calls.

  Args:
    source: the text of a suite file.

  Returns:
    {function name: display name} for every test registered in
    main(). Read from the source rather than by importing, because
    importing a suite requires QGIS and this tool must run anywhere.
  """
  found = {}
  for match in re.finditer(r'check\(\s*"([^"]+)",\s*\n?\s*(\w+)\)',
                           source):
    found[match.group(2)] = match.group(1)
  return found


def first_sentence(doc):
  """The opening sentence of a docstring, as one line.

  Args:
    doc: a docstring, or None.

  Returns:
    A single line with newlines collapsed, ending in a full stop, or
    an empty string. Only the first sentence: the rest of these
    docstrings explains WHY, which belongs in the file rather than in
    an index.
  """
  if not doc:
    return ""
  text = " ".join(doc.strip().split())
  cut = text.split(". ")[0].strip()
  return cut if cut.endswith(".") else cut + "."


def area_of(name, purpose):
  """Which part of the plugin a test belongs to.

  Args:
    name: the test's function name.
    purpose: its first docstring sentence.

  Returns:
    An area title from AREAS, or "Other" when nothing matches. The
    match is on words, in order, so a test about categorical colours
    lands in colour rather than in the editor unless it names the
    editor.
  """
  hay = f"{name} {purpose}".lower().replace("_", " ")
  for title, words in AREAS:
    if any(word in hay for word in words):
      return title
  return "Other"


def marks(node, doc, body):
  """What kind of test this is.

  Args:
    node: the ast.FunctionDef.
    doc: its docstring.
    body: the source text of the function.

  Returns:
    A list of short marks: "visual" when it renders and measures,
    "race" when it acts during a run or a debounce, "family" when it
    asserts over a table of cases, and "guards" when the docstring
    carries a Regression line. Detected from what the code does, not
    from naming conventions, so a renamed test keeps its marks.
  """
  out = []
  if any(k in body for k in ("visual_pair(", "visual_gamut(",
                             "render_layers(", ".render(", "QImage(")):
    out.append("visual")
  if any(k in body for k in ("_generate()", "_settle(", "race",
                             "_tick(", "blockSignals")) and \
      any(k in body for k in ("_task", "debounce", "_settle(",
                              "during")):
    out.append("race")
  if any(k in body for k in ("CONTROL_DEFAULTS", "CONTROL_CHECKBOXES",
                             "for name in wanted", "problems = []",
                             "wrong = []", "missing = []")):
    out.append("family")
  if doc and "Regression:" in doc:
    out.append("guards")
  return out


def collect():
  """Every test in the suite, with its area, purpose and marks.

  Returns:
    A list of dicts (area, display, function, purpose, marks, file),
    sorted by area then display name. Tests that exist but are not
    registered in main() are included with a display name of
    "NOT REGISTERED" — a test nobody runs is the most important thing
    such an index can surface.
  """
  rows = []
  for path in SUITES:
    if not os.path.exists(path):
      continue
    source = open(path, encoding="utf-8").read()
    lines = source.split("\n")
    names = registered_names(source)
    tree = ast.parse(source, path)
    for node in ast.walk(tree):
      if not isinstance(node, ast.FunctionDef):
        continue
      if not node.name.startswith(("test_", "case_")):
        continue
      doc = ast.get_docstring(node)
      body = "\n".join(
        lines[node.lineno - 1:getattr(node, "end_lineno", node.lineno)])
      purpose = first_sentence(doc)
      # The visual gallery registers its cases through its own
      # runner rather than through check(), so a missing check() entry
      # there means nothing. Only run_tests.py can orphan a test.
      gallery = node.name.startswith("case_")
      default = "(visual gallery)" if gallery else "NOT REGISTERED"
      rows.append({
        "area": area_of(node.name, purpose),
        "display": names.get(node.name, default),
        "function": node.name,
        "purpose": purpose or "(no docstring)",
        "marks": marks(node, doc, body),
        "file": os.path.basename(path),
      })
  return sorted(rows, key=lambda r: (r["area"], r["display"]))


def render(rows):
  """The map itself, as markdown.

  Args:
    rows: what collect() returned.

  Returns:
    The document text. Counts per area come first, because the shape
    of the suite is the thing to see before any individual test.
  """
  by_area = {}
  for row in rows:
    by_area.setdefault(row["area"], []).append(row)

  out = [
    "# What the test suite covers",
    "",
    "Generated by `tools/test_map.py`; do not edit. Regenerated at "
    "every release, so it cannot drift from the suite it describes.",
    "",
    f"{len(rows)} tests across {len(by_area)} areas.",
    "",
    "`guards` marks a test whose docstring carries a `Regression:` "
    "line: it was written because that defect actually happened here. "
    "A test without it guards ground we imagined rather than ground "
    "we fell through, which is worth knowing when reading an area "
    "that looks well covered.",
    "",
    "| area | tests | guarding a real defect | visual | family |",
    "|---|---:|---:|---:|---:|",
  ]
  for area in sorted(by_area):
    group = by_area[area]
    out.append(
      f"| {area} | {len(group)} | "
      f"{sum('guards' in r['marks'] for r in group)} | "
      f"{sum('visual' in r['marks'] for r in group)} | "
      f"{sum('family' in r['marks'] for r in group)} |")

  orphans = [r for r in rows if r["display"] == "NOT REGISTERED"]
  if orphans:
    out += ["", "## Not registered — these never run", ""]
    out += [f"- `{r['function']}` ({r['file']})" for r in orphans]

  for area in sorted(by_area):
    out += ["", f"## {area}", ""]
    for row in by_area[area]:
      tags = f" *[{', '.join(row['marks'])}]*" if row["marks"] else ""
      name = row["display"]
      out.append(f"- **{name}**{tags}  \n  {row['purpose']}")
  return "\n".join(out) + "\n"


def main():
  """Write the map, or check that the one on disk is current.

  Returns:
    0 when the map was written or is current, 1 when --check finds it
    stale. Writing is the default because a stale index is worse than
    none: it describes a suite that no longer exists.
  """
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--check", action="store_true",
                      help="fail if docs/TEST-MAP.md is out of date")
  args = parser.parse_args()

  text = render(collect())
  if args.check:
    current = (open(MAP, encoding="utf-8").read()
               if os.path.exists(MAP) else "")
    if current != text:
      print("docs/TEST-MAP.md is out of date; run tools/test_map.py")
      return 1
    print("test map current")
    return 0
  os.makedirs(os.path.dirname(MAP), exist_ok=True)
  with open(MAP, "w", encoding="utf-8") as handle:
    handle.write(text)
  rows = collect()
  print(f"wrote docs/TEST-MAP.md: {len(rows)} tests, "
        f"{sum('guards' in r['marks'] for r in rows)} guarding a "
        f"real defect")
  return 0


if __name__ == "__main__":
  sys.exit(main())
