#!/usr/bin/env python3
"""Refuse to publish credentials, key material, or private paths.

    python3 tools/check_no_secrets.py

Runs over exactly the files git would put in a commit -- tracked files
plus untracked ones that .gitignore does not exclude -- and exits
non-zero if any of them carries something that should not become
public. release.py runs it before it commits, and it is worth running
by hand before the first commit of all.

What it looks for, and why each one:

  credential-shaped strings   GitHub, Anthropic, OpenAI, AWS and Slack
                              tokens have recognisable shapes. Matching
                              the SHAPE rather than the word "token"
                              matters: this codebase says "token" all
                              over dialog.py in a perfectly innocent
                              sense (a QML class-source token), and a
                              checker that cried wolf there would be
                              switched off within a week.
  assignments                 api_key = "..." and friends, where a real
                              value has been pasted next to a
                              revealing name.
  private key blocks          any PEM block header.
  key and environment files   .env, .pem, id_rsa and the like, which
                              should never be tracked at all.
  the private style guide     two files that live outside this
                              repository on purpose; named here so a
                              stray copy cannot be committed by
                              accident.
  machine paths               /Users/<anyone>. Not a secret, but it
                              leaks a directory layout to no purpose,
                              and it is the tell that a file was
                              written for one machine rather than for
                              a reader.

Findings are printed REDACTED: a check that echoes the secret into
your terminal and your scrollback has helped nobody.

Exit status:
  0 when the tree is clean, 1 when anything was found (and the release
  stops there), 2 when the tree could not be read at all.
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# Each rule is (name, compiled pattern, what to say about it).
RULES = [
  ("GitHub token", re.compile(r"gh[pousr]_[A-Za-z0-9]{16,}"),
   "a GitHub personal access token"),
  ("GitHub fine-grained token",
   re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
   "a fine-grained GitHub token"),
  ("Anthropic key", re.compile(r"sk-ant-[A-Za-z0-9\-_]{20,}"),
   "an Anthropic API key"),
  ("OpenAI key", re.compile(r"\bsk-[A-Za-z0-9]{32,}"),
   "an OpenAI API key"),
  ("AWS key id", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
   "an AWS access key id"),
  ("Slack token", re.compile(r"xox[baprs]-[A-Za-z0-9\-]{10,}"),
   "a Slack token"),
  ("private key block",
   re.compile(r"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----"),
   "private key material"),
  ("credential assignment",
   re.compile(r"""(?i)\b(?:api[_-]?key|secret|passwd|password)\s*"""
              r"""[:=]\s*['"][^'"\n]{8,}['"]"""),
   "a credential assigned to a revealing name"),
  ("machine path", re.compile(r"/Users/[A-Za-z0-9._\-]+"),
   "an absolute path from one particular machine"),
]

# Filenames that must never be tracked, whatever they contain.
FORBIDDEN_NAMES = re.compile(
  r"(^\.env($|\.)|\.pem$|\.p12$|\.pfx$|(^|/)id_(rsa|dsa|ecdsa|ed25519)$"
  r"|^\.netrc$|^bergmann-osullivan-voice-dna\.md$"
  r"|^anti-ai-writing-style\.md$)")

# Deliberate exceptions. Every entry needs a REASON, in the same
# spirit as the equivalence claims in the mutation harness: an
# allowlist without reasons is just a way of turning the check off one
# line at a time.
ALLOWED = [
  # (path, rule name, reason)
]

BINARY = re.compile(rb"\x00")


def files_to_check():
  """The files a commit from here would contain.

  Returns:
    A list of repository-relative paths.

  Inside a git repository this asks git itself, so .gitignore is
  honoured exactly rather than approximated. Before `git init` there
  is nothing to ask, so the tree is walked and the directories named
  in .gitignore are skipped -- which is the case that matters most,
  since the whole point is to audit BEFORE the first commit.
  """
  try:
    out = subprocess.run(
      ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
      cwd=ROOT, capture_output=True, text=True, check=True)
    listed = [line for line in out.stdout.splitlines() if line]
    if listed:
      return listed
  except (subprocess.CalledProcessError, FileNotFoundError):
    pass

  skip = {".git", "dist", "reports", ".venv-reference", "__pycache__"}
  found = []
  for base, dirs, names in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d not in skip]
    for name in names:
      if name == ".DS_Store":
        continue
      full = os.path.join(base, name)
      found.append(os.path.relpath(full, ROOT))
  return sorted(found)


def redact(text):
  """Show enough of a finding to locate it, never enough to use it."""
  text = text.strip()
  if len(text) <= 8:
    return text
  return f"{text[:6]}...{text[-2:]} ({len(text)} chars)"


def scan(path):
  """Check one file against every rule.

  Args:
    path: repository-relative path.

  Returns:
    A list of (rule name, line number, redacted excerpt, explanation).
    Binary files are read but only searched for the patterns that can
    meaningfully occur in them; unreadable files are reported rather
    than skipped, since a file the checker cannot read is a file
    nobody has checked.
  """
  findings = []
  name = os.path.basename(path)
  if FORBIDDEN_NAMES.search(name) or FORBIDDEN_NAMES.search(path):
    findings.append(("forbidden file", 0, path,
                     "a file of this kind is never published"))
    return findings

  full = os.path.join(ROOT, path)
  try:
    with open(full, "rb") as handle:
      raw = handle.read()
  except OSError as exc:
    findings.append(("unreadable", 0, path, str(exc)))
    return findings
  if BINARY.search(raw[:4096]):
    return findings                     # images and GeoPackages
  try:
    text = raw.decode("utf-8")
  except UnicodeDecodeError:
    return findings

  for number, line in enumerate(text.splitlines(), 1):
    for rule, pattern, explanation in RULES:
      match = pattern.search(line)
      if not match:
        continue
      if any(a[0] == path and a[1] == rule for a in ALLOWED):
        continue
      findings.append((rule, number, redact(match.group(0)), explanation))
  return findings


def main():
  paths = files_to_check()
  if not paths:
    print("no files to check, which cannot be right")
    return 2
  problems = []
  for path in paths:
    for rule, number, excerpt, explanation in scan(path):
      problems.append((path, rule, number, excerpt, explanation))

  if problems:
    print(f"{len(problems)} thing(s) that must not be published:\n")
    for path, rule, number, excerpt, explanation in problems:
      where = f"{path}:{number}" if number else path
      print(f"  {where}\n      {rule}: {excerpt}\n      {explanation}")
    print("\nNothing has been committed. Remove these, or add a "
          "deliberate entry to ALLOWED in this file WITH A REASON.")
    return 1

  print(f"no secrets: {len(paths)} file(s) checked, nothing found")
  return 0


if __name__ == "__main__":
  sys.exit(main())
