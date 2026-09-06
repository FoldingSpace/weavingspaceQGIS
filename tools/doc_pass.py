"""An archiving pass, one verbatim move at a time.

A pass is a list of operations against one live document and its
archive. Each operation names a block of the live document by its
first line and (exclusively) the first line of what follows it, moves
that block VERBATIM into the archive under the next free id with a
note saying where it came from, and puts a replacement in its place
which must quote the id. Nothing is deleted: every non-blank line of
the block is in the archive afterwards, and `doc_archive.py` keeps the
pointer and the account paired.

    from doc_pass import Pass
    p = Pass("CLAUDE.md", "CLAUDE-archived.md", "C", "Lessons learned here, in full")
    p.move(start="- **SEED a watcher", end="- **Two watchers must never",
           title="The watcher that announced history as news",
           replacement="- **SEED a watcher with what is already true.** ... ({id}.)  -- {id} fills the WHOLE id, prefix included")
    p.apply()

`{id}` in a replacement is filled with the id assigned. `merge` takes
several blocks and archives them under ONE id, in order, for a family
consolidated into one live entry.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REVISION = "2026-09-05"


class Pass:
  """One archiving pass over a live document and its archive: a list of
  verbatim moves applied together, each under the next free id."""
  def __init__(self, live, archive, prefix, section):
    """Open both documents and find the next free id.

    Args:
      live: the live document, relative to the repository root.
      archive: its `-archived.md` twin, likewise.
      prefix: the id prefix the archive uses (`C`, `T`, ...).
      section: the index label written beside each new entry.
    """
    self.live = os.path.join(ROOT, live)
    self.archive = os.path.join(ROOT, archive)
    self.prefix = prefix
    self.section = section
    self.live_name = live
    self.ops = []
    with open(self.live, encoding="utf-8") as handle:
      self.text = handle.read()
    with open(self.archive, encoding="utf-8") as handle:
      self.archive_text = handle.read()
    defined = re.findall(rf"^### {prefix}-(\d+) ", self.archive_text, re.M)
    self.next_id = max(int(n) for n in defined) + 1

  # ------------------------------------------------------------ blocks

  def _find(self, start, end, text=None):
    """The character span of a block, from its unique start anchor to the
    start of its end anchor (or the end of the text where `end` is None).

    Args:
      start: the block's first line, which must occur exactly once.
      end: the first line of what follows the block, or None.
      text: the text searched; the live document by default.

    Returns:
      (i, j) with the block being text[i:j].
    """
    text = self.text if text is None else text
    i = text.find(start)
    assert i >= 0, f"start anchor not found: {start[:60]!r}"
    assert text.find(start, i + 1) < 0, f"start anchor ambiguous: {start[:60]!r}"
    if end is None:
      j = len(text)
    else:
      j = text.find(end, i + len(start))
      assert j >= 0, f"end anchor not found after start: {end[:60]!r}"
    # the block ends at the start of the end anchor's line
    return i, j

  def _line_span(self, i, j):
    """The 1-based line numbers a character span covers.

    Args:
      i: the span's first character.
      j: the character after its last.
    """
    before = self.text[:i].count("\n") + 1
    after = self.text[:j].count("\n")
    return before, after

  def move(self, start, end, title, replacement, note=""):
    """Queue one block to move to the archive under its own id.

    Args:
      start: the block's first line.
      end: the first line of what follows it, or None for the file's end.
      title: the archive heading.
      replacement: what stands in the live document instead; `{id}` in
        it is filled with the WHOLE id, prefix included.
      note: an optional clause added to the archive's provenance line.
    """
    self.ops.append(("move", [(start, end)], title, replacement, note))

  def merge(self, blocks, title, replacement, note=""):
    """Queue several blocks to move to the archive under ONE id, in order.

    Args:
      blocks: a list of (start, end) anchor pairs.
      title: the archive heading.
      replacement: what stands where the FIRST block stood; the others
        are removed.
      note: an optional clause added to the archive's provenance line.
    """
    self.ops.append(("merge", blocks, title, replacement, note))

  # ------------------------------------------------------------- apply

  def apply(self, dry=False):
    """Perform every queued operation and write both documents.

    Args:
      dry: report what would move and write nothing.
    """
    index_lines = []
    entries = []
    moved_lines = 0
    for _kind, blocks, title, replacement, note in self.ops:
      ident = f"{self.prefix}-{self.next_id}"
      self.next_id += 1
      bodies = []
      spans = []
      for start, end in blocks:
        i, j = self._find(start, end)
        body = self.text[i:j]
        assert body.strip(), "empty block"
        spans.append(self._line_span(i, j))
        bodies.append(body.rstrip("\n"))
        moved_lines += body.count("\n")
      # replace, last block first so earlier offsets stay valid
      located = sorted(((self._find(s, e), k) for k, (s, e) in enumerate(blocks)),
                       key=lambda pair: pair[0][0], reverse=True)
      filled = replacement.replace("{id}", ident)
      first = min(located, key=lambda pair: pair[0][0])[0][0]
      for (i, j), k in located:
        if i == first:
          self.text = self.text[:i] + filled + ("\n" if not filled.endswith("\n") else "") + self.text[j:]
        else:
          self.text = self.text[:i] + self.text[j:]
      where = ", ".join(f"lines {a}–{b}" for a, b in spans)
      head = (f"### {ident} — {title}\n\n"
              f"<sub>Cut from `{self.live_name}`, {where} of the {REVISION} "
              f"revision{(', ' + note) if note else ''}.</sub>\n\n")
      entries.append(head + "\n\n".join(bodies) + "\n")
      short = title if len(title) <= 90 else title[:87] + "..."
      index_lines.append(f"- **{ident}** — {short}  <sub>{self.section}</sub>")
    # the index: append after the last index line
    lines = self.archive_text.split("\n")
    last = max(k for k, line in enumerate(lines) if line.startswith(f"- **{self.prefix}-"))
    lines[last + 1:last + 1] = index_lines
    archive_text = "\n".join(lines).rstrip("\n") + "\n\n" + "\n\n".join(entries)
    if dry:
      print(f"would move {moved_lines} lines in {len(self.ops)} operation(s)")
      return
    with open(self.live, "w", encoding="utf-8") as handle:
      handle.write(self.text)
    with open(self.archive, "w", encoding="utf-8") as handle:
      handle.write(archive_text)
    self.archive_text = archive_text
    print(f"moved {moved_lines} lines in {len(self.ops)} operation(s); "
          f"next id {self.prefix}-{self.next_id}")
    self.ops = []


def block(live, start, end):
  """Print a block, for reading before deciding what to do with it.

  Args:
    live: the live document, relative to the repository root.
    start: the block's first line.
    end: the first line of what follows it, or None for the file's end.
  """
  with open(os.path.join(ROOT, live), encoding="utf-8") as handle:
    text = handle.read()
  i = text.find(start)
  j = text.find(end, i + 1) if end else len(text)
  print(text[i:j])


if __name__ == "__main__":
  block(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
