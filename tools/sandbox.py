#!/usr/bin/env python3
"""A throwaway copy of the project to mutate, so the real one is never
written to.

Mutation testing works by breaking code on purpose and putting it back
afterwards. "Afterwards" is the weak point: a SIGKILL, a crash between
the write and the restore, or a power cut leaves deliberately broken
source in the tree. That happened here on 2026-08-07 -- a killed audit
skipped its cleanup and left a mutated line in dialog.py -- and no
amount of signal handling closes the gap, because SIGKILL cannot be
caught.

Copying first removes the failure mode instead of mitigating it. The
campaign mutates the copy; the real tree is never opened for writing,
so there is nothing to restore, nothing to corrupt, and no reason to
stop working in the meantime.

Cheap enough to do per campaign: on macOS the copy uses APFS clones
(``cp -c``), which share storage until written to, so a few thousand
files cost milliseconds and almost no disk. Elsewhere it falls back to
an ordinary recursive copy. Reports, wheels, the reference virtualenv
and build output are left behind; none of them are needed to run
tests, and they are the only big things here.
"""

import os
import shutil
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# what a test run actually needs
INCLUDE = ["weavingspace_qgis", "tests", "tools"]
# what it does not, and what would make the copy slow
EXCLUDE = {"reports", "dist", ".venv-reference", "__pycache__", ".git",
           "libs", "wheels"}


def make_sandbox(label="mutation"):
  """Copy the project into a temporary directory.

  Args:
    label: appears in the directory name, so a stray copy is
      identifiable in /tmp.

  Returns:
    The path to the copy's root. The caller is responsible for
    removing it (see ``discard``), and should run tests from inside
    it: the suite derives its own paths from ``__file__``, so a copy
    is self-contained.
  """
  base = tempfile.mkdtemp(prefix=f"weavingspace-{label}-")
  for name in INCLUDE:
    source = os.path.join(ROOT, name)
    if not os.path.isdir(source):
      continue
    target = os.path.join(base, name)
    cloned = False
    try:
      # -c asks for APFS clones: near-instant, copy-on-write
      subprocess.run(["cp", "-Rc", source, target], check=True,
                     capture_output=True, timeout=120)
      cloned = True
    except Exception:
      cloned = False
    if not cloned:
      shutil.copytree(source, target,
                      ignore=shutil.ignore_patterns(*EXCLUDE))
    for unwanted in EXCLUDE:
      stray = os.path.join(target, unwanted)
      if os.path.isdir(stray):
        shutil.rmtree(stray, ignore_errors=True)
  os.makedirs(os.path.join(base, "reports"), exist_ok=True)
  return base


def discard(path):
  """Remove a sandbox, tolerating a partially-made one.

  Args:
    path: what make_sandbox returned.

  Returns:
    None.
  """
  if path and os.path.isdir(path) and "weavingspace-" in path:
    shutil.rmtree(path, ignore_errors=True)


if __name__ == "__main__":
  import sys
  made = make_sandbox("smoke")
  print(f"sandbox at {made}")
  print("contains:", sorted(os.listdir(made)))
  if "--keep" not in sys.argv:
    discard(made)
    print("discarded")
