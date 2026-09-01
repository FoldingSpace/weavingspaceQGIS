#!/usr/bin/env python3
"""Gather every sentence a user reads, so none ships unreviewed.

    python3 tools/text_review.py              # write docs/TEXT-REVIEW.md
    python3 tools/text_review.py --approve    # mark what is there as read
    python3 tools/text_review.py --check      # fail if anything is new

The problem this solves. User-facing prose is scattered: tooltips in
dialog.py, warnings built in bridge.py and perception.py, sections of
help_content.py, plus the README, the project page and the user guide.
Reviewing "the text" therefore means hunting through Python, which is
why text ships unread.

The problem it solves SECOND, which matters more. Reviewing everything
before every release is a job nobody keeps doing. So approval is
remembered: each string is recorded by content hash, and a string you
have already read never comes back. What you see is the DELTA — new
sentences and changed ones. On a quiet release that list is empty.

The workflow:

  1. `text_review.py` writes docs/TEXT-REVIEW.md with everything not
     yet approved, each with where it lives and what surrounds it.
  2. You read it and edit the wording IN THAT FILE, which is the point
     of it: the alternative is hunting the sentence through Python to
     change a comma, which is why text ships unread.
  3. `text_review.py --apply` writes those edits back into the source
     they came from and records the new wording as reviewed. Sentences
     you were happy with need no edit; `--approve` alone does the same
     job when you changed nothing.
  4. `--check` runs at release and fails while anything is unapproved.

Approval covers EVERYTHING listed, not only what you edited, because
"no edit" is how this file says "that reads correctly". So run --apply
when you have been through the whole list; it is recorded in
docs/text-approved.json and a git checkout of that file undoes it.

What counts as user-facing: string literals in the plugin package that
read like prose — several words, not identifiers, not docstrings — and
whole documents for the README, project page and user guide, which are
reviewed a PARAGRAPH at a time, hashed per block. This said they
were reviewed as wholes because per-paragraph hashes would be noise;
that was the original design and document_blocks replaced it, so a
comma no longer re-opens a whole page. (Corrected 2026-08-12.)
"""
import argparse
import ast
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PACKAGE = os.path.join(ROOT, "weavingspace_qgis")
APPROVED = os.path.join(ROOT, "docs", "text-approved.json")
REVIEW = os.path.join(ROOT, "docs", "TEXT-REVIEW.md")

# Documents are split into paragraphs and hashed per block. The
# trade-off is real and worth stating: a block small enough to review
# is a block a moved comma re-opens, and a document whole enough to
# survive a comma is one nobody reads twice. Paragraphs are the
# compromise, and this comment described the other side of it until
# 2026-08-12, long after document_blocks made the choice.
# metadata.txt is here for the changelog and the `about` text, which
# are the MOST read user-facing prose this project ships: QGIS's
# plugin manager shows them to everybody who installs or updates,
# and tools/release_notes.py puts the changelog paragraph at the top
# of the GitHub release page. It was outside this queue until
# 2026-08-12, which is how 0.24.1 shipped a changelog ending "Nothing
# else about the plugin has changed" four hours after something else
# about the plugin changed. Approved once, then quietly falsified by
# later work, with nothing to notice.
DOCUMENTS = ["README.md", os.path.join("docs", "index.html"),
             os.path.join("docs", "USER-GUIDE.md"),
             os.path.join("weavingspace_qgis", "metadata.txt")]

# Files whose strings are read by users. Deliberately not tools/ or
# tests/, whose messages are read by us.
SOURCES = ["dialog.py", "bridge.py", "perception.py", "compat.py",
           "help_content.py", "deps.py", "plugin.py",
           "category_editor.py", "absence.py",
           # catalog.py joined on 2026-09-01 with the design labels:
           # its COMMON_NAMES are the shortest user-facing text here
           # and are collected by name in `collect`, since the prose
           # filter's twenty-five character floor cannot see them.
           "catalog.py"]


def looks_like_prose(text):
  """Is this string something a user would read as a sentence?

  Args:
    text: a string literal from the source.

  Returns:
    True when it reads like prose rather than like an identifier, a
    format key, a colour, or a path. The test is deliberately loose --
    several words, some length, a lowercase letter, no obvious code
    punctuation at the start -- because a false positive costs one
    line in a review file, while a false negative ships unread text.
  """
  if len(text) < 25 or text.count(" ") < 3:
    return False
  if text.strip().startswith(("#", "/", "<?", "http")):
    return False
  # A LEADING placeholder is not a reason to skip a sentence. This
  # rule used to reject anything starting with "{", to skip format
  # keys -- and it thereby dropped every user-facing sentence that
  # opens with an interpolated value ("{} of {} areas have no value
  # for '{}' ..."), which shipped unread as a result. The length and
  # word-count tests above already exclude bare format keys, so what
  # is rejected here is a string that is placeholders and punctuation
  # and nothing else.
  without_placeholders = re.sub(r"\{[^}]*\}", " ", text)
  if not any(c.isalpha() for c in without_placeholders):
    return False
  if not any(c.islower() for c in text):
    return False
  # format templates and SQL-ish fragments are not prose
  if text.count("%") > 2 or text.strip().startswith("SELECT "):
    return False
  return True


def strings_in(path):
  """Every prose-looking string literal in a Python file.

  Args:
    path: absolute path to a module.

  Returns:
    A list of (line number, text, enclosing function). Docstrings are
    skipped: they are
    for maintainers, and this project's standard already makes them
    dense, so including them would bury the sentences users see.
  """
  with open(path, encoding="utf-8") as handle:
    source = handle.read()
  try:
    tree = ast.parse(source, path)
  except SyntaxError as exc:
    print(f"  cannot parse {path}: {exc}")
    return []

  docstrings = set()
  for node in ast.walk(tree):
    if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                         ast.AsyncFunctionDef)):
      first = node.body[0] if node.body else None
      if isinstance(first, ast.Expr) and \
              isinstance(first.value, ast.Constant) and \
              isinstance(first.value.value, str):
        docstrings.add(id(first.value))

  # f-strings arrive as JoinedStr: a list of literal chunks with the
  # interpolations between them. Walking for plain Constants would
  # split one sentence into fragments -- "categories where it had" on
  # its own line -- which is unreadable as a review item. So handle
  # them whole, rendering each interpolation as {} so the shape of the
  # sentence survives, and skip the chunks so they are not counted
  # twice.
  inside_fstring = set()
  found = []
  for node in ast.walk(tree):
    if isinstance(node, ast.JoinedStr):
      rendered = []
      for part in node.values:
        if isinstance(part, ast.Constant) and isinstance(part.value, str):
          inside_fstring.add(id(part))
          rendered.append(part.value)
        else:
          rendered.append("{}")
      text = " ".join("".join(rendered).split())
      if looks_like_prose(text):
        found.append((node.lineno, text, _span(node)))

  for node in ast.walk(tree):
    if isinstance(node, ast.Constant) and isinstance(node.value, str) \
            and id(node) not in docstrings \
            and id(node) not in inside_fstring \
            and looks_like_prose(node.value):
      found.append((node.lineno, " ".join(node.value.split()), _span(node)))

  # Attach the enclosing function to each item. A sentence reads
  # differently depending on where it appears -- the same words are
  # reassuring in a tooltip and alarming in a message bar -- so the
  # reviewer needs to know which is which without opening the source.
  spans = []
  for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
      spans.append((node.lineno, getattr(node, "end_lineno", node.lineno),
                    node.name))
  spans.sort(key=lambda s: s[1] - s[0])          # innermost wins
  placed = []
  for line, text, where in sorted(found, key=lambda f: f[0]):
    context = next((name for start, end, name in spans
                    if start <= line <= end), "module level")
    placed.append((line, text, context, where))
  return placed


def _span(node):
  """Where a literal sits in the file, as (line, col, endline, endcol).

  Kept so an edit can be written back by REPLACING THE WHOLE NODE
  rather than by searching for the sentence as text. Searching fails
  the moment a string is written across several lines -- which this
  project's line length forces on most of its longer tooltips, so the
  failure was not an edge case but the common one. Columns from the
  parser are byte offsets into the utf-8 line, which matters here
  because this prose contains en-dashes and accented place names.
  """
  return (node.lineno, node.col_offset,
          getattr(node, "end_lineno", node.lineno),
          getattr(node, "end_col_offset", node.col_offset))


def _offsets(raw, span):
  """Absolute byte offsets in a file for one parser span.

  Args:
    raw: the file's bytes.
    span: what ``_span`` returned.

  Returns:
    (start, end) suitable for slicing ``raw``.
  """
  starts, position = [0], 0
  for line in raw.splitlines(keepends=True):
    position += len(line)
    starts.append(position)
  line, col, end_line, end_col = span
  return starts[line - 1] + col, starts[end_line - 1] + end_col


def digest(text):
  """A stable id for one piece of text."""
  return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def document_blocks(path):
  """A document split into the paragraphs a reader would review.

  Args:
    path: absolute path to README.md, the project page or the guide.

  Returns:
    A list of (line number, block text) for blocks carrying prose.
    Blocks are separated by blank lines, which in all three documents
    corresponds to a paragraph, a heading, a caption or a list.

  These were once listed as whole files with a line count and nothing
  to edit, on the reasoning that a README is already a file you can
  open. That reasoning was wrong in practice: the sentences a reader
  actually meets on the project page never got reviewed, because
  nothing ever put them in front of anyone. A paragraph is the right
  unit -- small enough that an approved one stays approved when its
  neighbour changes, large enough that the id list does not become
  noise.

  Style sheets, scripts and fenced code are skipped: they are not
  prose, and a reviewer scrolling past a screenful of CSS to reach the
  next sentence stops reviewing.
  """
  with open(path, encoding="utf-8") as handle:
    body = handle.read()
  blocks, line = [], 1
  for chunk in body.split("\n\n"):
    start = line
    line += chunk.count("\n") + 2
    stripped = chunk.strip()
    if not stripped:
      continue
    lowered = stripped.lower()
    if lowered.startswith(("<style", "<script", "```", "<!--")):
      continue
    words = re.findall(r"[A-Za-z']{2,}", re.sub(r"<[^>]+>", " ", stripped))
    # a heading is three words and worth reviewing; a lone image tag or
    # a row of punctuation is not
    if len(words) < 3:
      continue
    blocks.append((start, chunk))
  return blocks


def collect():
  """Everything a user might read, with where it came from.

  Returns:
    A list of dicts: kind ("string" or "document"), where, line, text,
    and hash. Documents carry a hash of the whole file and a short
    excerpt rather than their contents.
  """
  items = []
  for name in SOURCES:
    path = os.path.join(PACKAGE, name)
    if not os.path.exists(path):
      continue
    for line, text, context, span in strings_in(path):
      items.append({"kind": "string",
                    "where": f"weavingspace_qgis/{name}",
                    "line": line, "text": text, "context": context,
                    "span": span, "hash": digest(text)})
  # THE CATALOGUE'S COMMON NAMES, collected by NAME rather than by the
  # prose filter. (2026-09-01, with the labels themselves.) They are
  # the shortest user-facing text this plugin has -- "trihexagonal" is
  # thirteen characters against `looks_like_prose`'s floor of
  # twenty-five -- so the ordinary sweep cannot see them, and they are
  # read by anybody choosing a design. A label that is WRONG is a
  # claim about mathematics made in the software's own voice, which is
  # exactly the kind of sentence this queue exists to put in front of
  # a person.
  catalogue = os.path.join(PACKAGE, "catalog.py")
  if os.path.exists(catalogue):
    names = {}
    source = open(catalogue, encoding="utf-8").read()
    tree = ast.parse(source)
    for node in ast.walk(tree):
      if not isinstance(node, ast.Assign):
        continue
      target = node.targets[0] if node.targets else None
      if getattr(target, "id", None) != "COMMON_NAMES":
        continue
      if isinstance(node.value, ast.Dict):
        for key, value in zip(node.value.keys, node.value.values):
          if isinstance(key, ast.Constant) and isinstance(value, ast.Constant):
            names[str(key.value)] = (str(value.value), value.lineno)
    for key, (label, line) in sorted(names.items()):
      shown = f"{key} ({label})"
      items.append({"kind": "string",
                    "where": "weavingspace_qgis/catalog.py",
                    "line": line, "text": shown,
                    "context": "the design chooser's own label",
                    "span": None, "hash": digest(shown)})
  for name in DOCUMENTS:
    path = os.path.join(ROOT, name)
    if not os.path.exists(path):
      continue
    for line, block in document_blocks(path):
      items.append({"kind": "block", "where": name, "line": line,
                    "text": block, "context": "document",
                    "hash": digest(block)})
  return items


def load_approved():
  """Hashes already read and accepted, with when."""
  if not os.path.exists(APPROVED):
    return {}
  with open(APPROVED, encoding="utf-8") as handle:
    return json.load(handle)


def write_review(pending, total):
  """The review file: only what has not been approved.

  Args:
    pending: items not yet approved at their current wording.
    total: how many pieces of text exist altogether, for context.

  Wording already edited IN the review file is carried forward rather
  than replaced by the source it came from. Without that, any
  regeneration -- and `--check` regenerates on every failing run, which
  means every release attempt -- would silently overwrite unsaved
  editing with the very sentences the reviewer had just rejected. The
  file is a working copy that survives being rebuilt, or it is not a
  working copy at all.
  """
  in_progress = edits_from_review()
  lines = [
    "# Text awaiting review",
    "",
    "Generated by `tools/text_review.py` — and **you can edit the "
    "quoted sentences here directly**. When the wording is right, "
    "`--apply` writes your edits back into the source and records "
    "them as reviewed. Leave the `<!-- id -->` comments alone; they "
    "are how each sentence finds its way home.",
    "",
    f"{len(pending)} of {total} pieces of user-facing text are new or "
    f"changed since they were last approved.",
    "",
  ]
  if not pending:
    lines += ["Nothing is waiting. Every sentence a user reads has "
              "been reviewed at its current wording.", ""]
  else:
    lines += ["Edit any sentence below, then:", "",
              "```bash",
              "python3 tools/text_review.py --apply    # edits -> source",
              "```", "",
              "Sentences you are happy with as they stand need no edit; "
              "`--apply` records everything here as reviewed either "
              "way. To accept the lot untouched, use `--approve`.", ""]
    documents = [i for i in pending if i["kind"] == "block"]
    strings = [i for i in pending if i["kind"] == "string"]
    if documents:
      lines += ["## Documents", "",
                "The README, the project page and the user guide, one "
                "paragraph at a time. Edit inside the fences and "
                "leave the fence lines themselves alone. Markup is "
                "shown as it is written, so change the words and "
                "leave the tags where they are.", ""]
      for item in sorted(documents, key=lambda i: (i["where"], i["line"])):
        wording = in_progress.get(item["hash"], item["text"])
        edited = " *(your edit, not yet applied)*" \
            if wording != item["text"] else ""
        lines += [f"**`{item['where']}:{item['line']}`**{edited}", "",
                  f"<!-- id:{item['hash']} -->",
                  "````", wording, "````", ""]
    if strings:
      lines += ["## Sentences", ""]
      for item in sorted(strings, key=lambda i: (i["where"], i["line"])):
        wording = in_progress.get(item["hash"], item["text"])
        edited = " *(your edit, not yet applied)*" \
            if wording != item["text"] else ""
        lines += [f"**`{item['where']}:{item['line']}`** "
                  f"— in `{item.get('context', '?')}`{edited}", "",
                  f"<!-- id:{item['hash']} -->",
                  f"> {wording}", ""]
  with open(REVIEW, "w", encoding="utf-8") as handle:
    handle.write("\n".join(lines))


def edits_from_review():
  """What the user changed in the review file.

  Returns:
    {hash: new text} for every sentence whose wording in
    docs/TEXT-REVIEW.md differs from the source it came from.

  The review file is a WORKING COPY, not a report. Hunting through
  Python to fix a tooltip is the thing this tool exists to abolish, so
  the sentences are editable where they are read, and each carries an
  invisible id marking where it belongs.
  """
  if not os.path.exists(REVIEW):
    return {}
  edits = {}
  current = None
  collecting = None      # lines of a fenced block, once inside one
  with open(REVIEW, encoding="utf-8") as handle:
    for line in handle:
      if collecting is not None:
        # a document paragraph runs to its closing fence; its own
        # content may contain anything except that fence
        if line.rstrip("\n") == "````":
          edits[current] = "\n".join(collecting)
          current, collecting = None, None
        else:
          collecting.append(line.rstrip("\n"))
        continue
      marker = re.match(r"<!-- id:([0-9a-f]+) -->", line.strip())
      if marker:
        current = marker.group(1)
      elif current and line.rstrip("\n") == "````":
        collecting = []
      elif current and line.startswith("> "):
        edits[current] = line[2:].strip()
        current = None
  return edits


def apply_edit(item, new_text):
  """Write one edited sentence back into the source.

  Args:
    item: the collected item, carrying where the string lives.
    new_text: the wording from the review file.

  Returns:
    A problem string, or None on success.

  Plain literals are replaced directly. An f-string was shown as a
  template with {} where its interpolations were, so putting it back
  means splitting the new wording on {} and re-joining it around the
  ORIGINAL expressions -- which only works if the placeholder count
  still matches. If it does not, the edit is refused with an
  explanation rather than guessed at: a mangled f-string would be a
  crash in front of a user.
  """
  if item["kind"] == "block":
    return apply_block_edit(item, new_text)

  path = os.path.join(PACKAGE, os.path.basename(item["where"]))
  with open(path, "rb") as handle:
    raw = handle.read()

  old_text = item["text"]
  if "{}" in old_text and new_text.count("{}") != old_text.count("{}"):
    return (f"{item['where']}:{item['line']} has "
            f"{old_text.count('{}')} value(s) filled in and the new "
            f"wording has {new_text.count('{}')}. The braces mark "
            f"where a number or a name is dropped in, so removing one "
            f"would leave a sentence with nothing to say there; put it "
            f"back, or edit this one in the source")

  start, end = _offsets(raw, item["span"])
  if "{}" in old_text:
    replacement = _fstring_literal(raw[start:end].decode("utf-8"), new_text)
    if replacement is None:
      return (f"{item['where']}:{item['line']} builds its sentence "
              f"around quoted values, which cannot be re-assembled "
              f"safely; edit that one in the source")
  else:
    replacement = _plain_literal(new_text)

  # Continuation lines align under the opening quote, which is where
  # this project already puts them. Three forms are tried in turn,
  # because implicit concatenation is only legal inside brackets: as
  # it stands (right for a call argument), wrapped in parentheses of
  # its own (right for a bare assignment), and finally one long line,
  # which always parses but would be an unusually long line in
  # the package, so it is the last resort rather than the default.
  column = item["span"][1]
  candidates = (_wrapped(replacement, column, " " * column),
                "(" + _wrapped(replacement, column + 1,
                               " " * (column + 1)) + ")",
                replacement)
  for candidate in candidates:
    rewritten = raw[:start] + candidate.encode("utf-8") + raw[end:]
    try:
      ast.parse(rewritten.decode("utf-8"), path)
    except SyntaxError:
      continue          # the wrapped form needs brackets it lacks
    with open(path, "wb") as handle:
      handle.write(rewritten)
    return None
  return (f"{item['where']}:{item['line']} could not be rewritten "
          f"without breaking the file, so it was left alone; edit it "
          f"in the source")


def apply_block_edit(item, new_text):
  """Write one edited paragraph back into its document.

  Args:
    item: the collected block, carrying the document and the original
      paragraph exactly as it appears there.
    new_text: the paragraph as edited in the review file.

  Returns:
    A problem string, or None on success.

  Matched on the ORIGINAL text rather than on a line range, because
  earlier edits to the same document move every line after them, and
  a line-based rewrite would then land in the wrong place. The
  paragraph is required to appear exactly once: a document with two
  identical paragraphs is not something to guess at.
  """
  path = os.path.join(ROOT, item["where"])
  with open(path, encoding="utf-8") as handle:
    body = handle.read()
  old_text = item["text"]
  found = body.count(old_text)
  if found == 0:
    return (f"{item['where']}:{item['line']} no longer contains that "
            f"paragraph, so it was left alone")
  if found > 1:
    return (f"{item['where']}:{item['line']} appears {found} times in "
            f"the document, so which one to change is ambiguous; edit "
            f"it in the file")
  with open(path, "w", encoding="utf-8") as handle:
    handle.write(body.replace(old_text, new_text, 1))
  return None


def _plain_literal(text):
  """One ordinary string literal holding this wording."""
  return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _fstring_literal(original, new_text):
  """An f-string carrying new wording around the SAME values.

  Args:
    original: the f-string exactly as it appears in the source.
    new_text: the reviewed wording, with {} where values belong.

  Returns:
    Source for the replacement, or None when it cannot be done safely.

  The interpolations are lifted verbatim from the original rather than
  re-derived, because they are code: `len(found) - 1` means something
  the review file cannot see. Only the words around them change. An
  interpolation containing a double quote is refused outright -- older
  Python cannot nest the same quote inside an f-string, and a file
  that will not parse on a user's QGIS is a far worse outcome than a
  sentence left unedited.
  """
  try:
    node = ast.parse("(" + original + ")", mode="eval").body
  except SyntaxError:
    return None
  if not isinstance(node, ast.JoinedStr):
    return None
  values = []
  for part in node.values:
    if not (isinstance(part, ast.Constant) and isinstance(part.value, str)):
      rendered = ast.unparse(part)
      if '"' in rendered:
        return None
      values.append(rendered)
  words = new_text.split("{}")
  if len(words) != len(values) + 1:
    return None
  out = ['f"']
  for index, word in enumerate(words):
    out.append(word.replace("\\", "\\\\").replace('"', '\\"'))
    if index < len(values):
      out.append(values[index])
  out.append('"')
  return "".join(out)


def _wrapped(literal, column, indent):
  """The same literal, broken across lines to respect line length.

  Args:
    literal: a single string or f-string literal.
    column: the column the literal starts at.
    indent: leading whitespace for continuation lines.

  Returns:
    Implicitly-concatenated pieces, or the literal unchanged when it
    already fits. Implicit concatenation only works inside brackets,
    so the caller tries this form first and falls back to one long
    line when the parser rejects it.
  """
  if column + len(literal) <= 79:
    return literal
  prefix = "f" if literal.startswith('f"') else ""
  body = literal[len(prefix) + 1:-1]
  # room for the words themselves: the line also carries the indent,
  # any f prefix, two quotes, and the trailing space that joins this
  # piece to the next one -- that last one is easy to forget, and
  # forgetting it puts every wrapped line one column over the limit
  room = max(20, 79 - len(indent) - len(prefix) - 3)
  pieces, current = [], ""
  for word in body.split(" "):
    if current and len(current) + 1 + len(word) > room:
      pieces.append(current + " ")
      current = word
    else:
      current = f"{current} {word}".strip() if current else word
  pieces.append(current)
  return f"\n{indent}".join(f'{prefix}"{piece}"' for piece in pieces)


SELF_TEST_SOURCE = '''\
def _build_ui(self):
  box.setToolTip("The polygon layer whose attributes will be mapped. "
                 "A projected CRS is best; geographic layers are "
                 "reprojected to Web Mercator (fine for exploring, "
                 "rarely for publishing).")
  short.setToolTip("A coarse value from the layer extent")
  note = f"At {spacing:,.0f} {units} spacing, {dropped} of {total} areas received no tiles and appear nowhere on the map."
  wide = "A sentence on one line, long enough that it has to be wrapped."
  return note, wide
'''

SELF_TEST_CASES = [
  # a sentence written across several lines, which is what this
  # project's line length forces on any tooltip worth reading
  ("The polygon layer whose attributes will be mapped. A projected CRS "
   "is best; geographic layers are reprojected to Web Mercator (fine "
   "for exploring, rarely for publishing).",
   "The polygon layer whose attributes will be mapped. A projected CRS "
   "is best; geographic layers are reprojected to Web Mercator (fine "
   "for exploring, not necessarily for publishing)."),
  # a short literal that grows
  ("A coarse value from the layer extent",
   "A coarse value from the layer extent, good for iterating"),
  # an f-string: the words change and the VALUES must survive untouched
  ("At {} {} spacing, {} of {} areas received no tiles and appear "
   "nowhere on the map.",
   "At {} {} spacing, {} of {} areas received no tiles and so appear "
   "nowhere on this map."),
  # a bare assignment, where implicit concatenation needs brackets
  ("A sentence on one line, long enough that it has to be wrapped.",
   "A sentence on one line, now long enough that it certainly has to "
   "be wrapped across more than one line of source."),
]


def self_test():
  """Prove the applier still edits source correctly, in a sandbox.

  Returns:
    0 when every shape applies, 1 otherwise, with what failed printed.

  This exists because `--apply` REWRITES SHIPPED SOURCE unattended.
  The first version of it could only find a sentence written as one
  literal, so it silently declined most of the file; the second
  applied the first edit and then aimed every later one at offsets
  that edit had already moved. Neither failure was visible in the
  tool's own output, and the second could have written nonsense into
  dialog.py rather than refusing. So the shapes that broke it are
  pinned here: multi-line concatenation, a short literal, an f-string
  whose interpolations must survive verbatim, and a bare assignment
  where wrapping needs brackets it does not have.
  """
  global PACKAGE
  work = tempfile.mkdtemp()
  original = PACKAGE
  try:
    PACKAGE = os.path.join(work, "weavingspace_qgis")
    os.makedirs(PACKAGE)
    path = os.path.join(PACKAGE, "dialog.py")
    with open(path, "w", encoding="utf-8") as handle:
      handle.write(SELF_TEST_SOURCE)

    failures = []
    for old, new in SELF_TEST_CASES:
      found = {text: (line, span)
               for line, text, _, span in strings_in(path)}
      if old not in found:
        failures.append(f"never collected: {old[:60]}")
        continue
      line, span = found[old]
      problem = apply_edit({"where": "weavingspace_qgis/dialog.py",
                            "line": line, "text": old, "span": span,
                            "kind": "string"}, new)
      if problem:
        failures.append(f"refused: {problem}")
        continue
      with open(path, encoding="utf-8") as handle:
        body = handle.read()
      try:
        ast.parse(body, path)
      except SyntaxError as exc:
        failures.append(f"wrote source that will not parse: {exc}")
        break
      if new not in {t for _, t, _, _ in strings_in(path)}:
        failures.append(f"applied but not present: {new[:60]}")

    with open(path, encoding="utf-8") as handle:
      body = handle.read()
    for expression in ("{spacing:,.0f}", "{units}", "{dropped}", "{total}"):
      if expression not in body:
        failures.append(f"lost an interpolated value: {expression}")
    longest = max((len(l) for l in body.splitlines()), default=0)
    if longest > 79:
      failures.append(f"left a line {longest} columns wide")

    if failures:
      print("text_review self-test FAILED:")
      for failure in failures:
        print(f"  {failure}")
      return 1
    print(f"text_review self-test passed: {len(SELF_TEST_CASES)} shapes "
          f"applied, source parses, values intact")
    return 0
  finally:
    PACKAGE = original
    shutil.rmtree(work, ignore_errors=True)


def main():
  """Collect every user-facing sentence and run the mode asked for.

  Returns:
    0 in the ordinary modes; 1 when --check finds wording that has
    never been reviewed at its current form, and 1 when --self-test
    finds the applier broken.

  What is left behind depends on the mode. The default and --check
  write docs/TEXT-REVIEW.md, the delta of what still needs reading.
  --apply additionally writes the reviewer's edits back into the
  Python and the documents they came from, which is the whole point
  of the file being editable: the alternative is hunting a sentence
  through dialog.py to move a comma, which is why text used to ship
  unread. --approve, which --apply implies, records the current
  wording by content hash in docs/text-approved.json, so an approved
  sentence never appears again until somebody changes it.

  Approval covers everything listed, not only what was edited,
  because leaving a sentence alone is how this file says it reads
  correctly.

  One case is deliberately not approved: an edit that could not be
  written back. Recording it would stamp the OLD source wording as
  read and drop the reviewer's replacement from the next review file,
  losing the correction while reporting success. Those stay pending
  and come back next time, with the wording still in the review file.
  """
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--self-test", action="store_true",
                      help="check the applier against a throwaway module")
  parser.add_argument("--approve", action="store_true",
                      help="record everything currently present as read")
  parser.add_argument("--apply", action="store_true",
                      help="write edits made in docs/TEXT-REVIEW.md back "
                           "into the source, then record everything as "
                           "reviewed")
  parser.add_argument("--check", action="store_true",
                      help="fail if anything is unapproved; changes nothing")
  args = parser.parse_args()

  if args.self_test:
    return self_test()

  items = collect()
  approved = load_approved()
  pending = [i for i in items if i["hash"] not in approved]

  if args.check:
    if pending:
      print(f"{len(pending)} piece(s) of user-facing text have not been "
            f"reviewed at their current wording:\n")
      for item in pending[:8]:
        where = f"{item['where']}:{item['line']}" if item["line"] \
            else item["where"]
        print(f"  {where}\n      {item['text'][:96]}")
      if len(pending) > 8:
        print(f"  ... and {len(pending) - 8} more")
      print("\nEdit the wording in docs/TEXT-REVIEW.md itself, then run "
            "tools/text_review.py --apply\n(or --approve to accept it "
            "all as it stands). Anything you have already edited there "
            "is kept.")
      write_review(pending, len(items))
      return 1
    print(f"text reviewed: {len(items)} piece(s), none pending")
    return 0

  if args.apply:
    edits = edits_from_review()
    by_hash = {i["hash"]: i for i in items}
    changed, problems, refused = 0, [], set()
    for digest_id, new_text in edits.items():
      item = by_hash.get(digest_id)
      if item is None or item["kind"] not in ("string", "block"):
        continue
      if new_text == item["text"]:
        continue
      problem = apply_edit(item, new_text)
      if not problem:
        # Every edit moves the bytes after it, so each remaining span
        # in that file is now wrong. Re-reading the world after each
        # write is the difference between "the first edit applies" and
        # "the edits apply": the earlier version wrote one sentence
        # correctly and then aimed the rest at stale offsets, which
        # failed loudly here but is the kind of thing that corrupts a
        # source file quietly.
        by_hash = {i["hash"]: i for i in collect()}
      if problem:
        problems.append(problem)
        # The wording in the file is what the reviewer WANTED and the
        # source still holds what they rejected. Approving it here
        # would record their old text as read and delete their edit
        # from the next review file -- losing the correction and
        # claiming it had been accepted. So this one stays pending.
        refused.add(digest_id)
      else:
        changed += 1
    print(f"applied {changed} edit(s)")
    for problem in problems:
      print(f"  could not apply: {problem}")
    # re-collect, so the hashes recorded are of the NEW wording
    items = collect()
    if refused:
      items = [i for i in items if i["hash"] not in refused]
      print(f"\n{len(refused)} edit(s) could not be written and are "
            f"left UNAPPROVED, so they come back next time rather "
            f"than being lost. Your wording is still in "
            f"docs/TEXT-REVIEW.md.")
    args.approve = True

  if args.approve:
    stamp = __import__("time").strftime("%Y-%m-%d")
    for item in items:
      approved.setdefault(item["hash"],
                          {"where": item["where"],
                           "excerpt": item["text"][:60],
                           "approved": stamp})
    os.makedirs(os.path.dirname(APPROVED), exist_ok=True)
    with open(APPROVED, "w", encoding="utf-8") as handle:
      json.dump(approved, handle, indent=1, sort_keys=True)
    # Rebuild the review file from what is ACTUALLY still unapproved,
    # rather than declaring it empty. An edit that could not be
    # written is exactly the case where the two differ, and writing an
    # empty file there would erase the reviewer's wording while
    # reporting success -- the worst of both.
    everything = collect()
    remaining = [i for i in everything if i["hash"] not in approved]
    write_review(remaining, len(everything))
    print(f"approved {len(items)} piece(s); {len(remaining)} still "
          f"awaiting review")
    return 0

  write_review(pending, len(items))
  print(f"{len(pending)} of {len(items)} piece(s) awaiting review "
        f"-> docs/TEXT-REVIEW.md")
  return 0


if __name__ == "__main__":
  sys.exit(main())
