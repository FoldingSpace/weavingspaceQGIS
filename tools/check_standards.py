#!/usr/bin/env python3
"""Refuse a release that breaks the project's own rules.

Run by release.py before anything else, and standalone at any time:

    python3 tools/check_standards.py

The rules enforced here are the ones the project has decided it lives
by (see CLAUDE.md). They are checked mechanically because every one of
them was, at some point, kept faithfully right up until the moment it
was forgotten.

What is checked, and why each one earns its place:

* DOCUMENTATION. Every public function and class in the plugin's own
  modules carries a docstring, and functions taking arguments beyond
  ``self`` document them. A docstring that says only what a function
  is called is not documentation; the standard here is inputs,
  outputs and the reason for anything surprising.
* NO STALE MUTATION MARKERS. A mutation left in the source is a
  deliberately broken line shipped to users. This happened once, when
  a killed audit skipped its cleanup.
* NO WEB-APP TALK IN USER-FACING TEXT. Plugin users have never seen
  MapWeaver; explaining a control in terms of it explains nothing.
  The help and guide may LINK it under further reading, which is the
  one sanctioned exception.
* CANADIAN SPELLING in user-facing text: colour, not color.
* THE AUDIT TOOLS EXIST AND ARE WIRED UP: the mutation catalogue
  covers the behaviours the tests claim to guard, and every mutation
  names a test that exists.
"""

import ast
import importlib.util
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = os.path.join(ROOT, "weavingspace_qgis")
SKIP_DIRS = ("vendor", "libs", "__pycache__")
USER_FACING = [
  os.path.join(PLUGIN, "help_content.py"),
  os.path.join(ROOT, "docs", "USER-GUIDE.md"),
]

problems = []


def plugin_sources():
  for dirpath, dirnames, filenames in os.walk(PLUGIN):
    dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
    for name in sorted(filenames):
      if name.endswith(".py"):
        yield os.path.join(dirpath, name)


def check_documentation():
  """Docstrings on public definitions, with arguments documented."""
  for path in plugin_sources():
    with open(path, encoding="utf-8") as f:
      source = f.read()
    tree = ast.parse(source, path)
    rel = os.path.relpath(path, ROOT)
    # Only definitions a caller can reach: module level and class
    # level. A closure defined inside a function is implementation
    # detail of that function, documented by the prose around it, and
    # demanding an Args block for `to_screen(x, y)` inside a paint
    # method would be noise rather than documentation.
    reachable = []
    for node in tree.body:
      if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        reachable.append(node)
      elif isinstance(node, ast.ClassDef):
        reachable.append(node)
        reachable += [c for c in node.body
                      if isinstance(c, (ast.FunctionDef,
                                        ast.AsyncFunctionDef))]
    for node in reachable:
      if False:
        continue
      name = node.name
      if name.startswith("__") and name.endswith("__"):
        continue
      doc = ast.get_docstring(node)
      if not doc:
        problems.append(f"{rel}:{node.lineno} {name} has no docstring")
        continue
      if isinstance(node, ast.ClassDef):
        continue
      args = [a.arg for a in node.args.args
              if a.arg not in ("self", "cls")]
      args += [a.arg for a in node.args.kwonlyargs]
      if len(args) >= 2 and "Args:" not in doc and "Arg:" not in doc:
        # two or more arguments and no Args block: the caller is being
        # asked to guess what they mean
        problems.append(
          f"{rel}:{node.lineno} {name}({', '.join(args)}) documents no "
          "arguments")


def check_no_mutation_markers():
  """Nothing from the mutation tool left behind in shipped code."""
  for path in plugin_sources():
    with open(path, encoding="utf-8") as f:
      for i, line in enumerate(f, 1):
        if "# mutation" in line or "TEMP probe" in line:
          problems.append(
            f"{os.path.relpath(path, ROOT)}:{i} carries a mutation marker")


def check_user_facing_text():
  """No web-app explanations, and Canadian spelling."""
  for path in USER_FACING:
    if not os.path.exists(path):
      continue
    rel = os.path.relpath(path, ROOT)
    with open(path, encoding="utf-8") as f:
      text = f.read()
    # Work in PARAGRAPHS, not sentences: a URL contains full stops, so
    # sentence-splitting tears the sanctioned further-reading links
    # apart and reports them as prose. A mention is allowed when its
    # paragraph also carries a link (that is the "another platform for
    # the same library" note) or the paper's title.
    blocks = re.split(r"\n\s*\n|</p>|<h2>", text)
    for block in blocks:
      if not re.search(r"\b(web app|MapWeaver)\b", block, re.IGNORECASE):
        continue
      linked = "http" in block
      cited = "Using MapWeaver to make" in block  # the paper's title
      if not (linked or cited):
        snippet = " ".join(block.split())[:70]
        problems.append(
          f"{rel}: explains something in terms of the web app: "
          f"\"{snippet}\"")
    for wrong, right in (("color", "colour"), ("colors", "colours"),
                         ("symbolize", "symbolise-or-symbolize?")):
      if wrong == "color":
        for m in re.finditer(r"\bcolor(s|ed|ing)?\b", text):
          # QGIS API names are allowed; prose is not
          context = text[max(0, m.start() - 30):m.end() + 30]
          if "Qgs" in context or "setColor" in context or \
              "color_part" in context or "_r" in context:
            continue
          problems.append(f"{rel}: American spelling \"{m.group(0)}\" "
                          f"in user-facing text")
          break


def check_audit_tools():
  """Every mutation names a test that exists, and the catalogue is
  not shrinking quietly."""
  catalogue = os.path.join(ROOT, "tools", "mutation_check.py")
  suite = os.path.join(ROOT, "tests", "run_tests.py")
  if not (os.path.exists(catalogue) and os.path.exists(suite)):
    problems.append("the audit tools are missing")
    return
  with open(catalogue, encoding="utf-8") as f:
    cat = f.read()
  with open(suite, encoding="utf-8") as f:
    tests = f.read()
  named = set(re.findall(r"test=['\"](test_\w+)['\"]", cat))
  for test in sorted(named):
    if f"def {test}(" not in tests:
      problems.append(
        f"tools/mutation_check.py names {test}, which no longer exists")
  count = cat.count("dict(name=")
  if count < 30:
    problems.append(
      f"the mutation catalogue has shrunk to {count} entries; it is "
      "meant to grow with the behaviours worth guarding")
  check_equivalence_claims()


def check_equivalence_claims():
  """Every mutant excused as "equivalent" carries evidence, and still
  refers to code that exists.

  An equivalent mutant is one that changes no observable behaviour, so
  removing it from the denominator is legitimate -- and it is also the
  easiest way to inflate a mutation score, since nobody can see the
  reasoning behind a one-word excuse. CLAUDE.md and
  docs/MUTATION-TESTING.md therefore require each entry to carry both
  an argument and a demonstration. This check enforces that, and
  catches the other failure mode too: an entry whose target line has
  since been edited away is excusing a mutation that no longer exists,
  which silently shrinks the denominator for free.
  """
  auto = os.path.join(ROOT, "tools", "mutate_auto.py")
  if not os.path.exists(auto):
    problems.append("tools/mutate_auto.py is missing")
    return
  spec = importlib.util.spec_from_file_location("mutate_auto", auto)
  module = importlib.util.module_from_spec(spec)
  try:
    spec.loader.exec_module(module)
  except Exception as exc:                      # pragma: no cover
    problems.append(f"tools/mutate_auto.py will not import: {exc}")
    return
  for entry in getattr(module, "EQUIVALENT", []):
    label = entry.get("snippet", "<unnamed>")[:50]
    for field in ("reason", "evidence"):
      if len(entry.get(field, "").strip()) < 40:
        problems.append(
          f"the equivalence claim for {label!r} has no real {field}; "
          f"an excused mutant needs an argument AND a demonstration, "
          f"not a note (see docs/MUTATION-TESTING.md)")
    target = os.path.join(ROOT, entry.get("file", ""))
    if not os.path.exists(target):
      problems.append(f"the equivalence claim for {label!r} names "
                      f"{entry.get('file')!r}, which does not exist")
      continue
    with open(target, encoding="utf-8") as f:
      if entry.get("snippet", "\0") not in f.read():
        problems.append(
          f"the equivalence claim for {label!r} no longer matches any "
          f"line in {entry.get('file')}; it is excusing a mutation "
          f"that cannot happen, which shrinks the denominator for free")


def main():
  check_documentation()
  check_no_mutation_markers()
  check_user_facing_text()
  check_audit_tools()
  if problems:
    print(f"{len(problems)} standards problem(s):\n")
    for problem in problems:
      print(f"  {problem}")
    print("\nThese are the project's own rules (CLAUDE.md). Fix them, "
          "or change the rule deliberately.")
    sys.exit(1)
  print("standards: documentation, markers, user-facing text, audit "
        "tools and equivalence claims all in order")


if __name__ == "__main__":
  main()
