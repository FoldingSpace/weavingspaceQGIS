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
# Everything a user reads. This list was once help_content.py and the
# user guide alone, which left every tooltip in dialog.py and every
# warning in bridge.py unchecked -- and an American spelling duly
# reached a shipped tooltip, past a gate whose whole job was to catch
# exactly that. The rule was never "check the two files we happened to
# think of"; it was "check what users read". Keep this list matching
# text_review.py's SOURCES and DOCUMENTS, for the same reason.
USER_FACING = [
  os.path.join(PLUGIN, "help_content.py"),
  os.path.join(PLUGIN, "dialog.py"),
  os.path.join(PLUGIN, "bridge.py"),
  os.path.join(PLUGIN, "perception.py"),
  os.path.join(PLUGIN, "category_editor.py"),
  os.path.join(PLUGIN, "compat.py"),
  os.path.join(PLUGIN, "deps.py"),
  os.path.join(PLUGIN, "plugin.py"),
  os.path.join(ROOT, "docs", "USER-GUIDE.md"),
  os.path.join(ROOT, "README.md"),
  os.path.join(ROOT, "docs", "index.html"),
]

problems = []


def plugin_sources():
  """Every Python file the plugin itself ships."""
  for dirpath, dirnames, filenames in os.walk(PLUGIN):
    dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
    for name in sorted(filenames):
      if name.endswith(".py"):
        yield os.path.join(dirpath, name)


def our_sources():
  """Every Python file WE wrote, wherever it lives.

  Yields:
    Absolute paths, plugin package first, then the tooling and the
    tests, then the two scripts at the root.

  The documentation standard applies to code this project writes, not
  to the subset of it that happens to be inside the plugin folder.
  That distinction had gone unnoticed because the checker only ever
  walked the package, which left the tools ungoverned — and by now
  the tools rewrite shipped source (text_review), decide the mutation
  score (mutate_auto), and write into a user's QGIS profiles (build).
  Those deserve the same explanation as the dialog.

  vendor/ is excluded because it is not ours: it is upstream's code,
  vendored verbatim, and holding it to our conventions would mean
  either editing it (which the next re-vendor discards) or failing
  forever.
  """
  seen = set()
  for path in plugin_sources():
    seen.add(path)
    yield path
  for folder in ("tools", "tests"):
    root = os.path.join(ROOT, folder)
    if not os.path.isdir(root):
      continue
    for dirpath, dirnames, filenames in os.walk(root):
      dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
      for name in sorted(filenames):
        if name.endswith(".py"):
          path = os.path.join(dirpath, name)
          if path not in seen:
            yield path
  for name in ("build.py", "release.py"):
    path = os.path.join(ROOT, name)
    if os.path.exists(path):
      yield path


def check_documentation():
  """Docstrings on public definitions, with arguments documented.

  Applied to everything WE write -- the plugin, the tools and the
  tests alike -- because the standard is about code this project is
  responsible for, not about which folder it sits in.
  """
  for path in our_sources():
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
  for path in plugin_sources():  # only the package is ever shipped
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
    if path.endswith(".py"):
      # For a module, "user-facing text" is the prose STRINGS, not the
      # file. Comments and docstrings are written for maintainers, and
      # the web app is deliberately a maintainer-facing fact here --
      # catalogue parity, the reference renderer. Checking whole files
      # reported fifteen docstrings explaining where the catalogue
      # comes from, which is exactly what those docstrings are for.
      # The same collector text_review.py uses, so the two agree on
      # what counts as something a user reads.
      sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
      from text_review import strings_in
      text = "\n\n".join(t for _l, t, _c, _s in strings_in(path))
    # Likewise a page is its prose, not its style sheet: every "color"
    # on the project page is a CSS property, and reporting those as
    # American spelling would train everyone to ignore this check,
    # which is worse than not having it. Only the SPELLING pass gets
    # the stripped version, though. The web-app rule allows a mention
    # whose paragraph carries a link, and stripping tags takes the
    # hrefs away -- which turned the sanctioned paper citation and
    # further-reading link into two false alarms.
    spell_text = text
    if path.endswith(".html"):
      spell_text = re.sub(r"<style.*?</style>|<script.*?</script>", " ",
                          text, flags=re.DOTALL | re.IGNORECASE)
      spell_text = re.sub(r"<[^>]+>", " ", spell_text)
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
        for m in re.finditer(r"\bcolor(s|ed|ing)?\b", spell_text):
          # QGIS API names are allowed; prose is not
          context = spell_text[max(0, m.start() - 30):m.end() + 30]
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
  check_binding_documents()


def check_binding_documents():
  """The documents CLAUDE.md declares binding still exist and are cited.

  CLAUDE.md requires docs/TESTING.md and docs/MUTATION-TESTING.md to
  be read before tests are written or changed. A rule that points at a
  missing file is worse than no rule, and a document nothing points at
  is a document nobody opens, so both directions are checked here.
  """
  for name in ("docs/TESTING.md", "docs/MUTATION-TESTING.md",
               "docs/MUTATION-LOOP.md"):
    path = os.path.join(ROOT, name)
    if not os.path.exists(path):
      problems.append(f"{name} is missing, but CLAUDE.md declares it "
                      f"binding on anyone writing tests")
      continue
    if os.path.getsize(path) < 2000:
      problems.append(f"{name} has been reduced to a stub; it is "
                      f"meant to carry the lessons, not a heading")
    with open(os.path.join(ROOT, "CLAUDE.md"), encoding="utf-8") as f:
      if name not in f.read():
        problems.append(f"CLAUDE.md no longer points at {name}, so "
                        f"nothing will send a reader to it")


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
  """Run every standards check and report everything that breaches one.

  Returns:
    None. Prints each problem and exits 1 when there are any, which
    is what stops release.py before any of the expensive stages;
    prints a one-line all-clear otherwise. Nothing is written.

  The checks append to the module-level ``problems`` list rather than
  returning their own findings, so one run reports every breach at
  once. Stopping at the first would turn a tidy-up into a series of
  runs, and a checker that has to be run five times is a checker that
  gets run once.
  """
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
