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
  2. You read it, and edit the source where the wording is wrong.
     (Edit the SOURCE, never this file: it is generated, and anything
     written here is overwritten on the next run.)
  3. `text_review.py --approve` records the hashes you have accepted.
  4. `--check` runs at release and fails while anything is unapproved.

What counts as user-facing: string literals in the plugin package that
read like prose — several words, not identifiers, not docstrings — and
whole documents for the README, project page and user guide, which are
reviewed as wholes because a hash per paragraph would just be noise.
"""
import argparse
import ast
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PACKAGE = os.path.join(ROOT, "weavingspace_qgis")
APPROVED = os.path.join(ROOT, "docs", "text-approved.json")
REVIEW = os.path.join(ROOT, "docs", "TEXT-REVIEW.md")

# Whole documents, reviewed as documents. Splitting them into hashed
# paragraphs would mean re-approving a page because a comma moved.
DOCUMENTS = ["README.md", os.path.join("docs", "index.html"),
             os.path.join("docs", "USER-GUIDE.md")]

# Files whose strings are read by users. Deliberately not tools/ or
# tests/, whose messages are read by us.
SOURCES = ["dialog.py", "bridge.py", "perception.py", "compat.py",
           "help_content.py", "deps.py", "plugin.py"]


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
  if text.strip().startswith(("#", "/", "{", "<?", "http")):
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
        found.append((node.lineno, text))

  for node in ast.walk(tree):
    if isinstance(node, ast.Constant) and isinstance(node.value, str) \
            and id(node) not in docstrings \
            and id(node) not in inside_fstring \
            and looks_like_prose(node.value):
      found.append((node.lineno, " ".join(node.value.split())))

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
  for line, text in sorted(found):
    context = next((name for start, end, name in spans
                    if start <= line <= end), "module level")
    placed.append((line, text, context))
  return placed


def digest(text):
  """A stable id for one piece of text."""
  return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


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
    for line, text, context in strings_in(path):
      items.append({"kind": "string",
                    "where": f"weavingspace_qgis/{name}",
                    "line": line, "text": text, "context": context,
                    "hash": digest(text)})
  for name in DOCUMENTS:
    path = os.path.join(ROOT, name)
    if not os.path.exists(path):
      continue
    with open(path, encoding="utf-8") as handle:
      body = handle.read()
    items.append({"kind": "document", "where": name, "line": 0,
                  "text": f"({len(body.splitlines())} lines)",
                  "hash": digest(body)})
  return items


def load_approved():
  """Hashes already read and accepted, with when."""
  if not os.path.exists(APPROVED):
    return {}
  with open(APPROVED, encoding="utf-8") as handle:
    return json.load(handle)


def write_review(pending, total):
  """The review file: only what has not been approved."""
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
    documents = [i for i in pending if i["kind"] == "document"]
    strings = [i for i in pending if i["kind"] == "string"]
    if documents:
      lines += ["## Documents changed", ""]
      for item in documents:
        lines.append(f"- `{item['where']}` {item['text']}")
      lines.append("")
    if strings:
      lines += ["## Sentences", ""]
      for item in sorted(strings, key=lambda i: (i["where"], i["line"])):
        lines += [f"**`{item['where']}:{item['line']}`** "
                  f"— in `{item.get('context', '?')}`", "",
                  f"<!-- id:{item['hash']} -->",
                  f"> {item['text']}", ""]
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
  with open(REVIEW, encoding="utf-8") as handle:
    for line in handle:
      marker = re.match(r"<!-- id:([0-9a-f]+) -->", line.strip())
      if marker:
        current = marker.group(1)
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
  path = os.path.join(PACKAGE, os.path.basename(item["where"]))
  with open(path, encoding="utf-8") as handle:
    source = handle.read()

  old_text = item["text"]
  if "{}" in old_text:
    if new_text.count("{}") != old_text.count("{}"):
      return (f"{item['where']}:{item['line']} has "
              f"{old_text.count('{}')} value(s) filled in and the new "
              f"wording has {new_text.count('{}')}; edit it in the "
              f"source, where the values are visible")
    return (f"{item['where']}:{item['line']} is built from several "
            f"pieces (an f-string); edit that one in the source")

  # a plain literal: find it as written, allowing for the wrapping
  # this project's line length forces
  compact = " ".join(old_text.split())
  for quote in ('"', "'"):
    literal = quote + compact + quote
    if literal in source:
      source = source.replace(literal, quote + new_text + quote, 1)
      with open(path, "w", encoding="utf-8") as handle:
        handle.write(source)
      return None
  return (f"{item['where']}:{item['line']} could not be found as a "
          f"single literal (it is probably split across lines); edit "
          f"it in the source")


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--approve", action="store_true",
                      help="record everything currently present as read")
  parser.add_argument("--apply", action="store_true",
                      help="write edits made in docs/TEXT-REVIEW.md back "
                           "into the source, then record everything as "
                           "reviewed")
  parser.add_argument("--check", action="store_true",
                      help="fail if anything is unapproved; changes nothing")
  args = parser.parse_args()

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
      print("\nSee docs/TEXT-REVIEW.md, fix any wording in the SOURCE, "
            "then run tools/text_review.py --approve")
      write_review(pending, len(items))
      return 1
    print(f"text reviewed: {len(items)} piece(s), none pending")
    return 0

  if args.apply:
    edits = edits_from_review()
    by_hash = {i["hash"]: i for i in items}
    changed, problems = 0, []
    for digest_id, new_text in edits.items():
      item = by_hash.get(digest_id)
      if item is None or item["kind"] != "string":
        continue
      if new_text == item["text"]:
        continue
      problem = apply_edit(item, new_text)
      if problem:
        problems.append(problem)
      else:
        changed += 1
    print(f"applied {changed} edit(s)")
    for problem in problems:
      print(f"  could not apply: {problem}")
    # re-collect, so the hashes recorded are of the NEW wording
    items = collect()
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
    write_review([], len(items))
    print(f"approved {len(pending)} new piece(s); {len(items)} total")
    return 0

  write_review(pending, len(items))
  print(f"{len(pending)} of {len(items)} piece(s) awaiting review "
        f"-> docs/TEXT-REVIEW.md")
  return 0


if __name__ == "__main__":
  sys.exit(main())
