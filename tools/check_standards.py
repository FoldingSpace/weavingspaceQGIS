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
  # absence.py holds the legend labels for the three kinds of
  # unplaceable value, which are read straight off a map's legend.
  os.path.join(PLUGIN, "absence.py"),
  os.path.join(PLUGIN, "compat.py"),
  os.path.join(PLUGIN, "deps.py"),
  os.path.join(PLUGIN, "plugin.py"),
  os.path.join(ROOT, "docs", "USER-GUIDE.md"),
  os.path.join(ROOT, "README.md"),
  os.path.join(ROOT, "docs", "index.html"),
  # metadata.txt IS THE MOST-READ PROSE THIS PROJECT SHIPS, and it was
  # missing from this list until 2026-08-31. Its `changelog=` and
  # `about=` are what QGIS's plugin manager displays, and
  # `release_notes.py` puts the same changelog entry at the top of the
  # GitHub release body -- two renderers, one text, neither of them
  # checked here. MEASURED by planting one sentence in both places:
  # "The tile color is chosen for you, reproducing what the web app
  # does." in README.md fails this check twice over, on the web-app
  # rule and on the spelling; the identical sentence in the changelog
  # passed clean. So a HARD RULE -- never explain the plugin in terms
  # of something the reader cannot see -- was unenforced in the one
  # file most users read, and so was Canadian spelling.
  # THE COMMENT ABOVE THIS LIST ALREADY SAID SO: it asks that this
  # stay in step with `text_review.py`'s SOURCES and DOCUMENTS, and
  # DOCUMENTS has carried metadata.txt since 2026-08-12, when a stale
  # changelog shipped and the queue was widened to catch it. The two
  # drifted anyway, which is what a hand-kept list does.
  os.path.join(PLUGIN, "metadata.txt"),
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
    # EVERY SPELLING THE RULE NAMES, which until 2026-08-28 meant one
    # of them. The loop carried three tuples and acted on a single
    # `if wrong == "color":`, so `colors` and `symbolize` were dead
    # code reading as protection -- and `colormap` and `behavior`,
    # both named in CLAUDE.md's hard rule, were never looked for at
    # all: `colormap` fails the word boundary in `\bcolor(s|ed|ing)?\b`.
    # Found by the instruments audit of that day, with a plant the
    # gate had to catch as its control.
    # AND CANADIAN SPELLING KEEPS -ize, which is why the wrong half of
    # that pair is `symbolise` rather than `symbolize`. The retired
    # tuple had it the other way round with a question mark in the
    # replacement, so nobody had decided it; CLAUDE.md had.
    misspellings = (
      (r"\bcolor(s|ed|ing)?\b", "colour"),
      (r"\bcolor ?map(s)?\b", "colourmap"),
      (r"\bbehavior(s|al)?\b", "behaviour"),
      (r"\b(symbolis|categoris|organis)(e|es|ed|ing|ation)\b", "-ize"),
    )
    for pattern, right in misspellings:
      for m in re.finditer(pattern, spell_text):
        # QGIS AND MATPLOTLIB API NAMES ARE ALLOWED; prose is not.
        # An identifier that mirrors somebody else's API keeps their
        # spelling, which is the other half of the same rule.
        context = spell_text[max(0, m.start() - 30):m.end() + 30]
        if "Qgs" in context or "setColor" in context or \
            "color_part" in context or "_r" in context or \
            "matplotlib" in context or "cmap" in context:
          continue
        problems.append(f"{rel}: American spelling \"{m.group(0)}\" "
                        f"in user-facing text (this project writes "
                        f"{right})")
        break


def check_regression_shapes():
  """Every Regression: line says HOW the defect was found.

  Returns:
    None; anything untagged is appended to `problems`.

  WHY IT IS ENFORCED. The tag is what makes docs/BUG-REGISTER.md
  answer the only question it is consulted for -- which shape of test
  is actually catching defects, and therefore whether the next
  afternoon goes on another differential sweep or on another hunt. It
  was optional, and on 2026-08-15 a HUNDRED of the 162 lines had no
  tag at all, which made the register's own summary read "unrecorded:
  100" and the rest of it decoration.

  Absent is now an error. A defect whose provenance genuinely was not
  written down carries `[unrecorded]` EXPLICITLY: that keeps the
  history honest -- inventing a shape would be worse than admitting
  none -- while making silence impossible for anything written from
  now on. (Maintainer's instruction: "this should never go
  unrecorded. fix the rules".)
  """
  import ast as _ast
  known = set()
  register = os.path.join(ROOT, "tools", "bug_register.py")
  if os.path.exists(register):
    with open(register, encoding="utf-8") as handle:
      tree = _ast.parse(handle.read())
    for node in _ast.walk(tree):
      if isinstance(node, _ast.Assign) and len(node.targets) == 1 \
          and getattr(node.targets[0], "id", None) == "HOW" \
          and isinstance(node.value, _ast.Dict):
        for key in node.value.keys:
          try:
            known.add(_ast.literal_eval(key))
          except (ValueError, TypeError):
            continue
  if not known:
    problems.append(
      "tools/bug_register.py's HOW map could not be read, so the "
      "shapes a Regression line may name are unknown")
    return
  for name in ("run_tests.py", "visual_tests.py"):
    path = os.path.join(ROOT, "tests", name)
    if not os.path.exists(path):
      continue
    with open(path, encoding="utf-8") as handle:
      tree = _ast.parse(handle.read())
    for node in _ast.walk(tree):
      if not isinstance(node, _ast.FunctionDef) \
          or not node.name.startswith("test_"):
        continue
      doc = _ast.get_docstring(node) or ""
      # The SAME anchored pattern tools/bug_register.py uses, and it
      # must stay the same: this check decides which docstrings owe a
      # [shape] tag, and the register decides which become entries, so
      # a difference between the two makes one of them demand a tag
      # the other will never read. Unanchored, both matched a sentence
      # that merely NAMED the marker, and the tag went on a docstring
      # saying it deliberately had no line. (2026-08-16.)
      found = re.search(r"^[ \t]*Regression:\s*(.+?)(?:\n\s*\n|\Z)",
                        doc, re.S | re.M)
      if not found:
        continue
      text = " ".join(found.group(1).split())
      tag = re.search(r"\[([a-z-]+)\]\s*$", text)
      if tag is None:
        problems.append(
          f"tests/{name}: {node.name} records a defect without saying "
          f"how it was found; end its Regression line with a shape in "
          f"brackets, or [unrecorded] if it genuinely was not written "
          f"down")
      elif tag.group(1) not in known:
        problems.append(
          f"tests/{name}: {node.name} names the shape "
          f"[{tag.group(1)}], which tools/bug_register.py does not "
          f"know; add it to HOW or use one that exists")


def check_catalogue_anchors(catalogue):
  """Every catalogue entry's `old` text is still in the file it names.

  Args:
    catalogue: the path to tools/mutation_check.py.

  Returns:
    None; anything wrong is appended to `problems`, like every other
    check here.

  WHY THIS EXISTS, and it is the catalogue's own failure mode rather
  than a hypothetical. An entry whose `old` string no longer appears
  in its file matches nothing, so the tool applies no mutation, finds
  no survivor and exits clean: the entry REPORTS NOTHING instead of
  failing, and the behaviour it was written to guard is unguarded
  while the catalogue still lists it. Found 2026-08-15 an hour after
  the entry was written, when the line it anchored on was reshaped by
  the very next fix -- which is the ordinary way it will happen.

  This is the same rule as the one about generated documents: a
  guard nobody re-checks keeps its authority while losing its
  accuracy. The entries are read with ast rather than by regular
  expression, because the `old` values are multi-line strings with
  escapes in them and a pattern that got that wrong would fail in
  exactly the silent direction this check exists to close.
  """
  with open(catalogue, encoding="utf-8") as handle:
    tree = ast.parse(handle.read())
  # The entries name their file through module constants (BRIDGE,
  # DIALOG and the rest), so those are resolved first: reading them
  # as literals alone found nothing at all, which this check's own
  # count caught on its first run.
  constants = {}
  for node in tree.body:
    if isinstance(node, ast.Assign) and len(node.targets) == 1 \
        and isinstance(node.targets[0], ast.Name) \
        and isinstance(node.value, ast.Constant) \
        and isinstance(node.value.value, str):
      constants[node.targets[0].id] = node.value.value
  seen = 0
  for node in ast.walk(tree):
    if not (isinstance(node, ast.Call)
            and getattr(node.func, "id", None) == "dict"):
      continue
    fields = {kw.arg: kw.value for kw in node.keywords}
    if not {"name", "file", "old"} <= set(fields):
      continue
    holder = fields["file"]
    try:
      name = ast.literal_eval(fields["name"])
      old_text = ast.literal_eval(fields["old"])
      target = (constants.get(holder.id) if isinstance(holder, ast.Name)
                else ast.literal_eval(holder))
    except (ValueError, TypeError):
      continue                      # a computed entry: not ours to judge
    if not target:
      continue
    # A PLACEHOLDER IS NOT AN ANCHOR. A few entries are COMPUTED at
    # run time -- `crs-reattach` finds the line it wants by walking
    # the source -- and carry a literal only so the dict has the
    # shape the rest of the file expects, marked as a placeholder at
    # the site. Mutating text to itself changes nothing, so `old ==
    # new` is the reliable tell, and judging one of those anchors
    # asks a question about a string the tool never uses: the
    # uniqueness check's first draft duly reported `crs-reattach` as
    # ambiguous, on a placeholder that happens to be an ordinary call
    # appearing twice, while the entry it names had been judged
    # `caught` in the sweep an hour earlier. (2026-08-27.)
    try:
      new_text = ast.literal_eval(fields["new"]) if "new" in fields else None
    except (ValueError, TypeError):
      new_text = None
    if new_text is not None and new_text == old_text:
      continue
    seen += 1
    path = os.path.join(ROOT, target)
    if not os.path.exists(path):
      problems.append(
        f"the mutation catalogue's {name!r} names {target}, "
        f"which does not exist")
      continue
    with open(path, encoding="utf-8") as handle:
      body = handle.read()
    hits = body.count(old_text)
    if hits == 0:
      problems.append(
        f"the mutation catalogue's {name!r} anchors on text that is "
        f"no longer in {target}, so it mutates nothing and reports "
        f"nothing; re-anchor it on the line as it stands now")
    elif hits > 1:
      # PRESENT IS NOT ENOUGH, AND AMBIGUOUS FAILS THE SAME WAY. The
      # tool refuses at run time rather than mutating the first of
      # several sites, which is right -- but a refusal only reaches
      # somebody who runs the whole catalogue, and a sweep is a thing
      # that happens before a substantial release. Until 2026-08-27
      # this check asked only whether the anchor was PRESENT, so nine
      # entries sat reporting nothing at all while every gate was
      # green, and the sweep that found them was the first in weeks.
      # An entry that cannot be judged is not guarding anything,
      # whichever way it fails.
      # AND TWO OF THE NINE WERE AMBIGUOUS BY INDENTATION ALONE: a
      # match is a SUBSTRING, so a statement anchored at one nesting
      # level also matches its more deeply nested twin. Count matches
      # rather than looking for duplicated lines.
      problems.append(
        f"the mutation catalogue's {name!r} anchors on text that "
        f"appears {hits} times in {target}, so the tool would mutate "
        f"the first site while its siblings go on doing the work and "
        f"the entry reports nothing; narrow the anchor with a "
        f"neighbouring line, or anchor at the shared helper if there "
        f"is one")
  if seen < 30:
    problems.append(
      f"only {seen} catalogue entries could be read for their "
      f"anchors, which is fewer than this catalogue holds")


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
  check_catalogue_anchors(catalogue)
  count = cat.count("dict(name=")
  if count < 30:
    problems.append(
      f"the mutation catalogue has shrunk to {count} entries; it is "
      "meant to grow with the behaviours worth guarding")
  check_regression_shapes()
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


def check_skill_provenance():
  """Do the skills still match the documents they were derived from?

  Returns:
    None; appends to the module-level ``problems``.

  A skill in .claude/skills/ records the documents it was written
  from, with a sha256 of each. That provenance exists so a skill
  cannot quietly outlive its source -- and until this check, nothing
  verified it: docs/MUTATION-TESTING.md changed and the
  mutation-campaign skill went on claiming to derive from a version
  that no longer existed.

  A skill teaching the wrong procedure is worse than an absent one,
  because it is followed with confidence. When this fires, REREAD the
  source and update the skill's guidance, then refresh the hash. Do
  not refresh the hash alone: that silences the check without doing
  the work it exists to prompt.
  """
  import hashlib
  skills = os.path.join(ROOT, ".claude", "skills")
  if not os.path.isdir(skills):
    return
  for name in sorted(os.listdir(skills)):
    manifest = os.path.join(skills, name, "SKILL.md")
    if not os.path.exists(manifest):
      continue
    text = open(manifest, encoding="utf-8").read()
    for source, claimed in re.findall(
        r"path: (\S+)\n\s+sha256: (\w+)", text):
      full = os.path.join(ROOT, source)
      if not os.path.exists(full):
        problems.append(
          f"skill {name!r} derives from {source}, which no longer "
          f"exists")
        continue
      with open(full, "rb") as handle:
        actual = hashlib.sha256(handle.read()).hexdigest()
      if actual != claimed:
        problems.append(
          f"skill {name!r} was derived from {source}, which has "
          f"changed since. Reread it, update the skill's guidance if "
          f"the procedure moved, then refresh the sha256 -- refreshing "
          f"the hash alone silences the check without doing the work.")


def check_derived_documents():
  """Are the generated documents current with the suite they describe?

  Returns:
    None. Appends to the module-level ``problems``, as every other
    check here does, so one run reports every breach at once.

  docs/TEST-MAP.md and docs/BUG-REGISTER.md are generated, and a
  generated document that nobody regenerates is worse than none: it
  keeps its authority while losing its accuracy, and it is consulted
  precisely when deciding where to write tests next.

  The recount uses each GENERATOR'S OWN rule, imported rather than
  restated, so this check cannot drift from the thing it checks.

  IT COMPARES THE WHOLE DOCUMENT, not the count it opens with, since
  2026-08-27. Counts were what this check compared for its first
  three weeks, on the reasoning that a count is the part a reader
  trusts -- and a count is blind to everything that leaves it
  unchanged: a test RENAMED, a purpose rewritten, a `Regression:`
  line reworded, an area re-assigned. Each of those makes the
  document describe a suite that no longer exists while its opening
  number stays right, which is the exact failure these two documents
  are regenerated to prevent. The generators already knew how to
  answer this properly -- both have a `--check` that renders and
  compares -- so what was missing was this check asking them rather
  than counting for itself. (ROADMAP item of 2026-08-13, closed.)
  Neither renderer reads a clock or the filesystem, so the comparison
  is stable: same suite, same bytes.

  It still does not WRITE, which is the part of the old reasoning
  that survives. A checker with side effects surprises whoever runs
  it, and a gate that quietly mends what it is meant to report is a
  gate nobody has to satisfy.
  """
  import importlib.util

  def load(name):
    spec = importlib.util.spec_from_file_location(
      name, os.path.join(ROOT, "tools", f"{name}.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

  def first_difference(current, fresh):
    """Where the file on disk and the suite's own answer diverge.

    Args:
      current: the document as committed.
      fresh: the document the generator would write now.

    Returns:
      A sentence naming the first line that differs and quoting both
      sides, or the line counts where one text merely runs longer.
      SAYING WHAT WAS FOUND rather than that something was found: a
      failure that only reports staleness sends somebody to a
      three-thousand-line diff to learn which test they renamed.
    """
    here, there = current.split("\n"), fresh.split("\n")
    for number, (mine, theirs) in enumerate(zip(here, there), start=1):
      if mine != theirs:
        return (f"first difference at line {number}: the file says "
                f"{mine.strip()[:70]!r} where the suite says "
                f"{theirs.strip()[:70]!r}")
    if len(here) != len(there):
      return (f"the file has {len(here)} lines where the suite would "
              f"write {len(there)}")
    return "they differ only in trailing whitespace"

  for label, tool, build in (
      ("docs/BUG-REGISTER.md", "bug_register",
       lambda m: m.render(m.entries())),
      ("docs/TEST-MAP.md", "test_map",
       lambda m: m.render(m.collect()))):
    path = os.path.join(ROOT, "docs", os.path.basename(label))
    if not os.path.exists(path):
      problems.append(f"{label} is missing; run tools/{tool}.py")
      continue
    try:
      fresh = build(load(tool))
    except Exception as exc:                                # noqa: BLE001
      problems.append(f"could not regenerate {label}: {exc}")
      continue
    current = open(path, encoding="utf-8").read()
    if current != fresh:
      problems.append(
        f"{label} is not what the suite would produce -- "
        f"{first_difference(current, fresh)}; run tools/{tool}.py and "
        f"commit the result")


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


def check_ci_covers_what_it_claims():
  """The workflow still runs everything we think it runs.

  Was ``check_linux_ci_covers_what_it_claims`` until a Windows job
  joined the file (2026-08-15); a name saying Linux over a check that
  reads the whole workflow is the kind of small lie that gets believed
  by whoever greps for it.

  Returns:
    None; appends to ``problems``. Reads .github/workflows/ci.yml as
    text rather than as YAML, because this project has no YAML
    dependency and the questions are all "is this named here".

  Why this is a STANDARD rather than a test. The pre-candidate branch
  is pushed BEFORE the local gates start, so anything wrong with the
  workflow is discovered on a runner fifty minutes later, or -- worse
  -- not discovered at all, because a job that was silently dropped
  fails nothing. Checking here means it is answered in the second
  before the push, by the same command that already guards it.

  Three ways the workflow rots, all seen in this project:

  a HARNESS exists that nothing in CI runs. tests/visual_tests.py sat
  outside the workflow for months on an untested belief about fonts,
  and when it was finally run it passed on every QGIS version;

  a job NAMES A SCRIPT that has moved or gone, which only a clean
  checkout finds -- the same shape as a document quoting a path no
  clone contains;

  a job GOES QUIET rather than going away: its command is rewritten
  into a form the pattern here no longer recognises, so the existence
  check sails over an empty set and reports nothing, which reads
  exactly like success. Asked per job below, and added 2026-08-15
  with the windows job, whose invocation is a batch shim behind an
  environment variable and is the first command in this file that the
  old pattern would have missed;

  the QGIS MATRIX drifts from what metadata.txt promises, so the
  plugin is tested on versions it does not claim and untested on ones
  it does. THIS ONE IS NOT CHECKED HERE and is named so the gap is
  visible: the others are, along with the five jobs and the stage
  list. Said plainly because this docstring claimed all of them for a
  while and the harness check did not exist -- a rule asserting its
  own enforcement is believed, which makes it the worst kind to leave
  unimplemented. (2026-08-12.)
  """
  path = os.path.join(ROOT, ".github", "workflows", "ci.yml")
  if not os.path.exists(path):
    problems.append("there is no .github/workflows/ci.yml, so nothing "
                    "runs on Linux at all")
    return
  workflow = open(path, encoding="utf-8").read()
  # WHAT THE WORKFLOW RUNS, WITHOUT WHAT IT MERELY MENTIONS. The
  # harness clause below asks whether `tests/<name>.py` appears in
  # this text, and until 2026-08-28 a COMMENT satisfied it: a line
  # reading `# NOT run here: tests/parity_harness.py` was enough, so
  # the sentence that satisfied the gate could deny it. That is
  # `check_roadmap`'s own defect of 2026-08-26 met again in a sibling
  # checker, and it was found the same way -- by planting the thing
  # the gate must catch and watching it pass.
  workflow_runs = "\n".join(
    line.split(" #", 1)[0] for line in workflow.splitlines()
    if not line.lstrip().startswith("#"))

  for job in ("standards", "suite", "install", "gallery", "windows",
              "macos"):
    if f"\n  {job}:" not in workflow:
      problems.append(
        f"ci.yml has no {job!r} job. Every one of these answers a "
        f"question the others cannot: standards checks the rules, "
        f"suite the behaviour, install what a USER receives, "
        f"gallery whether the map is drawn correctly, windows "
        f"whether the artefact survives a filesystem with the other "
        f"separator, a long-path ceiling and different locking rules, "
        f"and macos what happens on the package a user actually "
        f"downloads in a profile nobody has seeded -- the only leg "
        f"that can tell 'my machine' from 'the software', which is "
        f"how the ramp collision of 2026-08-15 stayed invisible.")

  # PARITY WITH THE MAC, derived from release.py rather than listed
  # here, so the two cannot drift apart quietly. Every stage a
  # release runs is either covered on Linux or exempt WITH A REASON.
  # The reasons are the interesting part: each one is a claim that a
  # second machine cannot answer this question, and each has been
  # wrong before -- the gallery sat exempt for months on a belief
  # about fonts that turned out to be false.
  covered_by = {
    "standards check": "standards",
    "secrets audit": "standards",
    # THE SECOND SECRETS RUN IS THE SAME QUESTION at a later moment --
    # `release.py` asks it twice, once before the expensive work and
    # once immediately before committing, because a leaked key is the
    # one failure a later release cannot undo. Linux answers "is this
    # tree clean" in the standards job, which is the whole of what
    # either invocation asks.
    "secrets audit (pre-commit)": "standards",
    "published content audit": "standards",
    "build zip": "standards",
    "functional suite": "suite",
    "visual gallery": "gallery",
    "build release candidate": "install",
  }
  mac_only = {
    "reference comparison":
      "needs matplotlib on a non-QGIS interpreter (.venv-reference); "
      "macOS code-signing keeps PyPI C extensions out of QGIS's Python",
    "create reference venv": "builds .venv-reference for the above",
    "install reference packages": "populates .venv-reference",
    "roadmap and branches": "reads local branches, which a runner "
                            "checkout does not have",
    "testing report": "written from this run's captured output",
    "release notes": "composes the body of a GitHub release from this "
                     "run's own artefacts and from `gh`; a runner has "
                     "neither the dist/ directory nor anything to "
                     "publish",
    "refresh published images": "rewrites files in the working tree",
    "test map": "regenerates a document the standards job then checks",
    "bug register": "regenerates a document the standards job then checks",
    "candidate dossier": "describes an artefact built here",
    "per-test coverage record": "left the release path 2026-08-12",
    "merge the coverage shards": "left the release path 2026-08-12",
  }
  try:
    release_src = open(os.path.join(ROOT, "release.py"),
                       encoding="utf-8").read()
    listed = re.search(r"EXPECTED_STAGES = \[(.*?)\]", release_src, re.S)
    stages = re.findall(r'"([^"]+)"', listed.group(1)) if listed else []
  except OSError:
    release_src = ""
    stages = []
  # AND THE LIST ITSELF IS CHECKED AGAINST THE STAGES release.py
  # ACTUALLY RUNS. CLAUDE.md says of this clause that "nothing there
  # is a hand-kept list, so the two cannot drift apart quietly", and
  # until 2026-08-28 `EXPECTED_STAGES` was exactly that: a stage added
  # to release.py and forgotten there got no CI job, no written
  # exemption and no complaint. Two were already outside it. The
  # sibling test `test_every_expected_stage_is_actually_run` compares
  # listed against called and never called against listed, so it could
  # not see this either. Found by the instruments audit of that day,
  # which planted a stage the gate had to catch.
  # EVERY LAUNCHER, EITHER QUOTE, AND NOT A COMMENT. The first draft
  # of this read `run("...")` alone, which a hunt aimed at it the same
  # evening showed is a partial gate: it missed a single-quoted name,
  # an f-string, a name passed as a variable, and -- not hypothetical
  # -- `run_sharded`, which is how release.py launches the functional
  # suite. It also DEMANDED a name written inside a comment. So the
  # sibling launcher is included, both quotes are, and commented lines
  # are dropped first.
  # WHAT IT STILL CANNOT SEE, said plainly rather than left implied: a
  # stage whose name is computed rather than written. A name built by
  # interpolation or held in a variable is invisible here, and the
  # honest reading of "this list cannot drift" is therefore "cannot
  # drift for a stage whose name is a literal at its call site".
  # Writing one any other way is the thing to avoid.
  release_lines = "\n".join(
    line for line in release_src.splitlines()
    if not line.lstrip().startswith("#"))
  run_names = sorted(set(
    re.findall(r"""\brun(?:_sharded)?\(\s*["']([^"']+)["']""",
               release_lines)))
  for name in run_names:
    if name not in stages:
      problems.append(
        f"release.py runs the stage {name!r} and EXPECTED_STAGES does "
        f"not list it, so the CI-parity question below is never asked "
        f"about it. Add it to EXPECTED_STAGES -- this list is what "
        f"CLAUDE.md promises cannot drift, and it drifted.")
  for stage in stages:
    if stage in mac_only:
      continue
    job = covered_by.get(stage)
    if job is None:
      problems.append(
        f"release.py runs the stage {stage!r} and nothing says "
        f"whether Linux does. Add it to covered_by with the job that "
        f"runs it, or to mac_only with the reason a second machine "
        f"cannot answer it -- an unexamined gap is how the gallery "
        f"stayed out of CI for months.")
    elif f"\n  {job}:" not in workflow:
      problems.append(
        f"{stage!r} is meant to be covered by ci.yml's {job!r} job, "
        f"which is not there any more")

  # The interpreter is named rather than matched loosely, so a path
  # that appears in a COMMENT is not read as a command. There are
  # three spellings because there are three interpreters: `python3` in
  # the Linux containers, `python` on the Windows runner where no
  # `python3` exists, and OSGeo4W's `python-qgis*.bat` shim, which the
  # windows job resolves at run time and carries in %QGIS_SHIM%.
  runs = sorted(set(re.findall(
    r"(?:python3?|python-qgis[\w-]*\.bat|%QGIS_SHIM%\")"
    r"(?:\s+-\w+)*\s+((?:tools|tests)[\\/][\w./\\-]+\.py)", workflow)))
  for quoted in runs:
    if not os.path.exists(os.path.join(ROOT, quoted.replace("\\", "/"))):
      problems.append(
        f"ci.yml runs {quoted}, which does not exist. Only a clean "
        f"checkout finds this, and it fails the whole job.")

  # A PATTERN THAT MATCHES NOTHING REPORTS NOTHING, which reads exactly
  # like success -- the fault found in seven mutation-catalogue entries
  # on 2026-08-15, and the reason this guard exists. The check above
  # asks whether the scripts it FOUND exist; it cannot notice a job
  # whose command it stopped recognising, and the windows job is the
  # one written in a form it would not have recognised before today (an
  # OSGeo4W batch shim behind %QGIS_SHIM%, reached through `call`).
  #
  # So the question is asked PER JOB. A global "is install_and_load.py
  # named anywhere" would be satisfied by the Linux `install` job for
  # ever, which is exactly the vacuous pass this is here to prevent --
  # written that way first, and it passed when the windows job's
  # variable was renamed, which is how it was caught.
  # The macos job was missing from this list until 2026-08-15, the day
  # it was added -- so the newest platform was the one job that could
  # go quiet without failing anything, which is the exact fault above
  # wearing a new coat. Its interpreter is discovered at run time and
  # carried in "$QGIS_PY", a third spelling beside python3 and the
  # OSGeo4W shim, so the pattern has to know all three.
  for job in ("standards", "suite", "install", "gallery", "windows",
              "macos"):
    block = re.search(rf"^  {job}:\n(.*?)(?=^  \S|\Z)",
                      workflow, re.M | re.S)
    if block and not re.search(
        r"(?:python3?|python-qgis[\w-]*\.bat|%QGIS_SHIM%\"|\"\$QGIS_PY\")"
        r"(?:\s+-\w+)*\s+(?:tools|tests)[\\/][\w./\\-]+\.py",
        block.group(1)):
      problems.append(
        f"ci.yml's {job!r} job runs no script this check can see. "
        f"Either the job stopped running one -- so it is asking "
        f"nothing -- or its command was rewritten into a form the "
        f"pattern here does not match, which would take it out of "
        f"the existence check above without failing anything.")

  # Every HARNESS under tests/ is run by the workflow, or exempt with
  # a reason. This is the check the docstring above has promised since
  # it was written and which did not exist until 2026-08-12, found by
  # the documentation audit -- a rule asserting its own enforcement is
  # the worst thing to leave unimplemented, because it is believed.
  #
  # It is also the check that would have caught the gallery. Adding a
  # harness and forgetting the workflow costs nothing locally and
  # leaves that harness measuring one machine for as long as nobody
  # looks.
  harness_exempt = {}          # name -> why a second machine cannot run it
  for harness in sorted(os.listdir(os.path.join(ROOT, "tests"))):
    if not harness.endswith(".py"):
      continue
    quoted = f"tests/{harness}"
    if quoted in workflow_runs or harness in harness_exempt:
      continue
    problems.append(
      f"{quoted} is a test harness that ci.yml never runs. Add it to "
      f"the workflow, or add it to harness_exempt here with the "
      f"reason a second machine cannot answer what it asks -- "
      f"tests/visual_tests.py sat outside CI for months on a belief "
      f"about fonts that turned out to be false.")
  stale = [h for h in harness_exempt
           if not os.path.exists(os.path.join(ROOT, "tests", h))]
  if stale:
    problems.append(
      f"harness_exempt names {stale}, which no longer exist; an "
      f"exemption for something that has gone is how the next real "
      f"one gets waved through")


def check_args_blocks_match_signatures():
  """Every documented argument is one the function actually takes.

  The documentation audit of 2026-08-12 split into four kinds of rot,
  and this is the one a machine can hold shut. The other three --
  behaviour that changed, a measurement since re-measured, a why
  naming a bug now fixed -- need somebody to read the code beside the
  prose, and were done by hand.

  What is checked, in the harmful direction first: a name DOCUMENTED
  that the signature does not take, which sends a caller to pass an
  argument that does not exist. Then a parameter the docstring omits,
  and an Args block whose order disagrees with the signature.

  Two things the first version of this got wrong, both worth keeping
  because they are how a checker cries wolf. GROUPED entries --
  "offset, offset_angle, point_angle: family-specific options" -- are
  deliberate and readable, and reading only the first name reported
  five perfectly good docstrings as broken. And *args sits BETWEEN
  the positional and keyword-only parameters, which is where a
  docstring naturally documents it; sorting it last reported
  release.py's git() as out of order when it is exactly in order.

  Returns:
    None. Appends to ``problems``. Functions with no Args block at
    all are ignored: whether one is REQUIRED is check_documentation's
    question, and this one only asks whether what is there is true.
  """
  import ast as _ast
  for path in our_sources():
    try:
      tree = _ast.parse(open(path, encoding="utf-8").read())
    except SyntaxError:
      continue
    rel = os.path.relpath(path, ROOT)
    for node in _ast.walk(tree):
      if not isinstance(node, (_ast.FunctionDef, _ast.AsyncFunctionDef)):
        continue
      claimed = _documented_arguments(_ast.get_docstring(node))
      if not claimed:
        continue
      actual = _signature_arguments(node)
      extra = [n for n in claimed if n not in actual]
      missing = [n for n in actual if n not in claimed]
      if extra:
        problems.append(
          f"{rel}:{node.lineno} {node.name}() documents {extra}, which "
          f"it does not take -- a reader will try to pass them")
      elif missing:
        problems.append(
          f"{rel}:{node.lineno} {node.name}() takes {missing} and its "
          f"Args block does not mention them")
      elif claimed != actual:
        problems.append(
          f"{rel}:{node.lineno} {node.name}() documents its arguments "
          f"as {claimed} but takes them as {actual}")


def _documented_arguments(doc):
  """The parameter names an Args block lists, in order.

  Args:
    doc: a docstring, or None.

  Returns:
    A list of names, empty when there is no Args block. Handles
    grouped entries ("a, b, c: one explanation"), which this project
    uses deliberately.
  """
  if not doc:
    return []
  lines = doc.splitlines()
  start = None
  for i, line in enumerate(lines):
    if line.strip() in ("Args:", "Arguments:"):
      start = i + 1
      break
  if start is None:
    return []
  names, indent = [], None
  for line in lines[start:]:
    if not line.strip():
      continue
    here = len(line) - len(line.lstrip())
    if indent is None:
      indent = here
    if here < indent:
      break
    if line.strip().rstrip(":") in ("Returns", "Raises", "Yields",
                                    "Attributes", "Note", "Example"):
      break
    if here == indent:
      match = re.match(r"([*\w]+(?:\s*,\s*[*\w]+)*)\s*(\(.*?\))?\s*:",
                       line.strip())
      if match:
        names += [part.strip().lstrip("*")
                  for part in match.group(1).split(",")]
  return names


def _signature_arguments(node):
  """The parameter names a function takes, in signature order."""
  a = node.args
  names = [p.arg for p in a.posonlyargs + a.args]
  if a.vararg:
    names.append(a.vararg.arg)
  names += [p.arg for p in a.kwonlyargs]
  if a.kwarg:
    names.append(a.kwarg.arg)
  return [n for n in names if n not in ("self", "cls")]


def check_nested_helpers_document_their_arguments():
  """Inner functions of two or more arguments say what they mean.

  Returns:
    None; anything undocumented is appended to `problems`.

  `check_documentation` deliberately governs only what a CALLER can
  reach, on the reasoning that a closure is implementation detail of
  the function around it. That reasoning holds for the docstring and
  NOT for the arguments. An inner helper taking three positional
  arguments is exactly where a reader has least context -- there is no
  signature in any index, no test naming it, and often no name that
  survives being read a year later -- and this project wrote one on
  2026-08-16 (`duplicates(body, where, path)`) that said nothing about
  any of them.

  So: a nested function of two or more arguments needs an Args block.
  It needs a docstring to put one in, which is the point rather than a
  side effect. One-argument helpers are left alone, because
  `to_screen(x)` inside a paint method really is noise.

  Dunders are exempt, as above, and so are lambdas, which cannot carry
  a docstring at all -- if a helper wants explaining, it wants to be a
  def.
  """
  for path in our_sources():
    with open(path, encoding="utf-8") as handle:
      tree = ast.parse(handle.read(), path)
    rel = os.path.relpath(path, ROOT)
    # Everything reachable is already covered; this walks the rest.
    outer = set()
    for node in tree.body:
      if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        outer.add(node)
      elif isinstance(node, ast.ClassDef):
        outer.update(c for c in node.body
                     if isinstance(c, (ast.FunctionDef,
                                       ast.AsyncFunctionDef)))
    for node in ast.walk(tree):
      if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        continue
      if node in outer:
        continue
      name = node.name
      if name.startswith("__") and name.endswith("__"):
        continue
      args = [a.arg for a in node.args.args
              if a.arg not in ("self", "cls")]
      args += [a.arg for a in node.args.kwonlyargs]
      # THREE, not two, and the line was chosen from a measurement
      # rather than by instinct (2026-08-16): at two-or-more this
      # names 92 helpers, 64 of them Qt slot closures like
      # `picked(index, colour)` whose arguments are Qt's and whose
      # names already say it. Blocks there would add some three
      # hundred lines of boilerplate and make the files longer
      # without making them clearer. At three-or-more it names 28,
      # including every genuinely opaque one -- `spin(lo, hi, val,
      # step)`, a `build` of six, a `setup` of nine -- and the helper
      # whose silence prompted the rule, `duplicates(body, where,
      # path)`. Raise it to two if the noise turns out to be worth
      # paying for; the number is here and nowhere else.
      if len(args) < 3:
        continue
      doc = ast.get_docstring(node) or ""
      if "Args:" not in doc and "Arg:" not in doc:
        problems.append(
          f"{rel}:{node.lineno} the inner helper "
          f"{name}({', '.join(args)}) documents no arguments; a "
          "closure is where a reader has least context, so three or "
          "more of them need saying")


def check_nothing_is_defined_twice():
  """No scope binds one name to two definitions.

  Returns:
    None; every redefinition is appended to `problems`.

  Python binds a name once per statement, so a second `def` of one
  name leaves the LAST in force and the first dead -- no warning, no
  error, and the file reading as though both are there. On 2026-08-16
  that shipped a colour editor labelling every value "no data",
  because the surviving definition's fallback was a fixed word and the
  dead one above it still described the behaviour the software no
  longer had.

  The suite carries this question too, and asking it HERE is the
  point: `check_standards` runs in a second before a push, where the
  suite answers fifty minutes into CI. The worst defect of that day
  would have been caught at the keyboard.

  Deliberately allowed: the decorated idioms where redefining a name
  is the language's own way of saying something -- a property's
  setter, getter or deleter, a `singledispatch` registration, and
  `typing.overload`. Definitions inside an `if` or a `try` are not
  counted either, being how a module offers one of two
  implementations; only DIRECT children of a scope are compared.
  """
  def deliberate(node):
    """Whether redefining this name is a language idiom.

    Args:
      node: the FunctionDef, AsyncFunctionDef or ClassDef to judge.
      (no second argument; listed for the reader rather than required)

    Returns:
      True when a decorator marks it as a deliberate second
      definition, False otherwise.
    """
    for dec in getattr(node, "decorator_list", []):
      target = dec.func if isinstance(dec, ast.Call) else dec
      if isinstance(target, ast.Attribute) and target.attr in (
          "setter", "getter", "deleter", "register", "overload"):
        return True
      if isinstance(target, ast.Name) and target.id == "overload":
        return True
    return False

  for path in our_sources():
    with open(path, encoding="utf-8") as handle:
      tree = ast.parse(handle.read(), path)
    rel = os.path.relpath(path, ROOT)
    scopes = [("the module", tree.body)]
    for node in ast.walk(tree):
      if isinstance(node, ast.ClassDef):
        scopes.append((f"class {node.name}", node.body))
    for where, body in scopes:
      seen = {}
      for item in body:
        if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef,
                                 ast.ClassDef)):
          continue
        if deliberate(item):
          continue
        seen.setdefault(item.name, []).append(item.lineno)
      for name, lines in seen.items():
        if len(lines) > 1:
          problems.append(
            f"{rel}: {where} defines {name} {len(lines)} times, at "
            f"lines {', '.join(str(n) for n in lines)}; Python keeps "
            "the last and the others are dead code describing "
            "behaviour the software no longer has")


def check_every_test_is_registered():
  """Every test the suite defines is run, and every run test exists.

  Returns:
    None; both directions of the mismatch are appended to `problems`.

  A test nobody registers never runs, and reports nothing forever --
  indistinguishable from a test that passes. Nineteen were found in
  that state on 2026-08-16. The converse is worse and faster: a
  `check()` naming a function that no longer exists breaks the suite
  at `main()`, which is how a span rewrite that took its neighbours
  announced itself the same day.

  The suite asks this of itself, and asking it here as well is
  deliberate: this runs in a second before a push, where the suite's
  own answer arrives after the tests it can no longer run.
  """
  path = os.path.join(ROOT, "tests", "run_tests.py")
  if not os.path.exists(path):
    problems.append("tests/run_tests.py is missing")
    return
  with open(path, encoding="utf-8") as handle:
    tree = ast.parse(handle.read(), path)
  defined = {node.name for node in tree.body
             if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
             and node.name.startswith("test_")}
  registered = set()
  for node in ast.walk(tree):
    if isinstance(node, ast.Call) and getattr(node.func, "id", None) \
        == "check" and len(node.args) > 1:
      target = node.args[1]
      if isinstance(target, ast.Name):
        registered.add(target.id)
  # Registered but undefined breaks the suite outright, so it is named
  # first and separately.
  for name in sorted(registered - defined):
    if name.startswith("test_"):
      problems.append(
        f"tests/run_tests.py registers {name}, which is not defined "
        "at module level; the suite would raise at main()")
  for name in sorted(defined - registered):
    problems.append(
      f"tests/run_tests.py defines {name} and never registers it, so "
      "it never runs and reports nothing forever")


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
  check_derived_documents()
  check_ci_covers_what_it_claims()
  check_skill_provenance()
  check_args_blocks_match_signatures()
  check_nested_helpers_document_their_arguments()
  check_nothing_is_defined_twice()
  check_every_test_is_registered()
  if problems:
    print(f"{len(problems)} standards problem(s):\n")
    for problem in problems:
      print(f"  {problem}")
    print("\nThese are the project's own rules (CLAUDE.md). Fix them, "
          "or change the rule deliberately.")
    sys.exit(1)
  print("standards: documentation, markers, user-facing text, audit "
        "tools, equivalence claims and the generated documents all in "
        "order")


if __name__ == "__main__":
  main()
