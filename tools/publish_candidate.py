"""Publish a release candidate to GitHub as a PRE-RELEASE.

Ten candidates of 0.24.3 went out this way before anything wrote the
procedure down: a tag `v<version>rc<N>` on the candidate's own commit,
a release titled "<version>rc<N> — release candidate", marked
pre-release so it never becomes Latest and never displaces a real
version, carrying three assets a tester needs -- the zip they install,
the per-test report, and the colourspace comparison PDF. The
maintainer made that the standard on 2026-08-21, so it lives in a
program rather than in somebody's memory of last time.

WHY A TOOL AND NOT A COMMAND SOMEBODY TYPES. Every one of the checks
below was performed by hand for ten candidates, which is ten chances
to skip one at two in the morning: that a receipt matches the tree, so
only a GATED candidate can be published; that the tag is free, because
a candidate number is spent by anything bearing it; that CI on that
exact commit is green, because the body says so and a body that claims
a verdict nobody read is worse than one that says nothing; and that a
person has written what changed, because a candidate nobody described
is a candidate nobody knows what to test.

WHAT IT WILL NOT DO. It never touches `main`, never makes a Latest
release, and never tags anything but the commit it verified. Promoting
a candidate to a release remains `release.py`, and remains the
maintainer's explicit call.
"""
import argparse
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

REPO = "FoldingSpace/weavingspaceQGIS"

# What a tester is asked to report back on, kept here rather than
# retyped per candidate: the questions do not change much, and a
# candidate that forgets to ask gets feedback about whatever the
# tester happened to notice.
#
# ONE LONG LINE PER PARAGRAPH, and it is not a style preference. A
# GitHub release body preserves single newlines, so a paragraph
# wrapped at the usual 72 columns arrives with those breaks in it and
# a phone shows a sentence snapped mid-clause. The rule is written up
# in docs/PUBLISHING.md, learned on rc9 -- and this constant was
# hard-wrapped anyway, so every candidate this tool has published
# carried it in the one paragraph nobody rereads because nobody wrote
# it that day. Found 2026-08-27 by measuring the LIVE page rather than
# the local file. metadata.txt is the opposite and stays wrapped,
# because the plugin manager shows it as it stands.
CLOSING = """## What would be most useful to hear

Whether the thing this candidate changed behaves as the notes above say, on your own data rather than on a fixture. Whether anything you had set up survived the upgrade. And whether a crash of any kind turns up, with what you were doing immediately before it."""


def run(*args, **kwargs):
  """Run a command and hand back the completed process.

  Args:
    *args: the argv list, as separate arguments.
    **kwargs: passed through to subprocess.run; `check` defaults to
      False so a caller can read a failure rather than be raised at.

  Returns:
    The CompletedProcess, with stdout and stderr captured as text.
  """
  kwargs.setdefault("check", False)
  return subprocess.run(list(args), cwd=ROOT, capture_output=True,
                        text=True, **kwargs)


def tree_digest():
  """The digest of exactly the files that ship.

  Returns:
    Whatever `release.tree_digest()` returns -- IMPORTED rather than
    reimplemented. A first draft of this file computed its own sha256
    over `build.shipped_files()` and got a different answer, because
    that function hands back (path, archive name) PAIRS and the copy
    hashed the pair. Two implementations of one rule have two
    behaviours the day one of them is wrong, which is the fault that
    put rc10's zip beside rc9's receipt; the receipt is written by
    release.py, so release.py is asked what it means.
  """
  import release
  return release.tree_digest()


def gate_numbers(report):
  """What the local gates measured, read off the testing report.

  Args:
    report: path to reports/v<version>/testing-report.md.

  Returns:
    (suite_passed, suite_failed, visual_passed, visual_failed), each an
    int. Read rather than retyped: a number in a release body that
    somebody typed from memory is a claim with no measurement behind
    it, and this project has published one of those before.
  """
  text = open(report, encoding="utf-8").read()
  parts = re.split(r"^## ", text, flags=re.M)
  counts = {}
  for part in parts:
    name = "suite" if part.startswith("Functional suite") else (
      "visual" if part.startswith("Visual gallery") else None)
    if name is None:
      continue
    counts[name] = (len(re.findall(r"^- \*\*PASS\*\*", part, re.M)),
                    len(re.findall(r"^- \*\*FAIL\*\*", part, re.M)))
  suite = counts.get("suite", (0, 0))
  visual = counts.get("visual", (0, 0))
  return suite[0], suite[1], visual[0], visual[1]


def ci_verdict(sha):
  """Ask GitHub what every workflow on this commit concluded.

  Args:
    sha: the full or short commit the candidate was built from.

  Returns:
    (green, sentence, runs) -- green is True only when every workflow
    on that commit COMPLETED and SUCCEEDED; sentence is what the
    release body should say about CI; runs is the list of
    (workflow, status, conclusion, id) actually seen.

    An empty list is NOT green: no run on a commit means nothing
    checked it, which reads exactly like a pass if you only look for
    failures.
  """
  out = run("gh", "run", "list", "--limit", "20", "--json",
            "headSha,status,conclusion,databaseId,workflowName")
  if out.returncode != 0:
    return False, "CI could not be reached to ask.", []
  runs = [(r["workflowName"], r["status"], r["conclusion"],
           r["databaseId"])
          for r in json.loads(out.stdout)
          if r["headSha"].startswith(sha)]
  if not runs:
    return False, "No CI run exists for this commit.", []
  unfinished = [r for r in runs if r[1] != "completed"]
  failed = [r for r in runs if r[2] not in (None, "success")]
  if unfinished:
    return False, (f"{len(unfinished)} CI workflow(s) still running: "
                   + ", ".join(r[0] for r in unfinished)), runs
  if failed:
    return False, ("CI is not green: "
                   + ", ".join(f"{r[0]} {r[2]}" for r in failed)), runs
  links = ", ".join(
    f"[{r[0]}](https://github.com/{REPO}/actions/runs/{r[3]})"
    for r in runs)
  return True, (f"Every CI workflow on that commit is green: {links}."), runs


def main():
  """Publish the newest candidate, or the one named, as a pre-release.

  Returns:
    An exit status: 0 when the pre-release exists at the end, 1 when
    anything was refused. Every refusal names what to do about it.
  """
  import build
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--label", help="e.g. 0.24.3rc16; defaults to "
                                      "the newest candidate on disk")
  parser.add_argument("--notes", help="a markdown file saying what "
                                      "changed since the last candidate")
  parser.add_argument("--despite-ci", metavar="REASON",
                      help="publish though CI is not green, with the "
                           "reason printed IN the release body")
  parser.add_argument("--dry-run", action="store_true",
                      help="say what would be published and stop")
  args = parser.parse_args()

  # THE VERSION AND THE NUMBER COME FROM THE SAME TWO FUNCTIONS
  # release.py uses. A third derivation of "which candidate is this"
  # is how rc10's zip came to sit beside rc9's receipt: build.py owns
  # both answers now, and this asks build.py.
  version = build.declared_version()
  if args.label:
    label = args.label
    version = label.split("rc")[0]
  else:
    number = build.latest_candidate(version)
    if number is None:
      print(f"{version} has no candidate on disk; run release.py --rc "
            f"first")
      return 1
    label = f"{version}rc{number}"
  tag = f"v{label}"
  dist = os.path.join(ROOT, "dist")
  reports = os.path.join(ROOT, "reports", f"v{version}")
  zip_path = os.path.join(dist, f"weavingspace_qgis-{label}.zip")
  receipt_path = os.path.join(dist, f"CANDIDATE-{label}.receipt.json")
  assets = [zip_path,
            os.path.join(reports, "testing-report.md"),
            os.path.join(reports, "visual-comparison.pdf")]

  # ---- only a GATED candidate may be published.
  if not os.path.exists(receipt_path):
    print(f"{label} has no receipt, so no gate ever passed on it; "
          f"build it with release.py --rc")
    return 1
  receipt = json.load(open(receipt_path, encoding="utf-8"))
  if receipt.get("tree") != tree_digest():
    print(f"the shipped files have changed since {label} was built, so "
          f"the zip is not this tree; run release.py --rc again")
    return 1
  missing = [a for a in assets if not os.path.exists(a)]
  if missing:
    print("these assets are missing:\n  "
          + "\n  ".join(os.path.relpath(m, ROOT) for m in missing))
    return 1

  # ---- a candidate number is spent by anything bearing it.
  if run("git", "rev-parse", "-q", "--verify",
         f"refs/tags/{tag}").returncode == 0:
    print(f"{tag} already exists locally; a candidate number is never "
          f"reused, so build the next one")
    return 1
  if run("gh", "release", "view", tag).returncode == 0:
    print(f"{tag} is already published; a candidate number is never "
          f"reused, so build the next one")
    return 1

  # THE COMMIT IS THE ONE THE CANDIDATE WAS BUILT FROM, read out of its
  # own dossier, and NOT `HEAD`. They are the same at the moment a
  # candidate is built and diverge at the next commit -- and a tester
  # who reads "built from abc1234" and checks out abc1234 must get the
  # tree that was measured, not whatever the branch has reached since.
  # The receipt covers only files that SHIP, so ordinary work on tests,
  # tooling and documentation leaves it matching while the branch moves
  # on; that is exactly the window in which HEAD would have lied.
  dossier = os.path.join(dist, f"CANDIDATE-{label}.md")
  sha = ""
  if os.path.exists(dossier):
    found = re.search(r"built from commit `([0-9a-f]{7,40})`",
                      open(dossier, encoding="utf-8").read())
    sha = found.group(1) if found else ""
  if not sha:
    print(f"{label}'s dossier does not say which commit it was built "
          f"from, and HEAD is not an answer to that question; rebuild "
          f"it with release.py --rc")
    return 1
  # ...EXPANDED TO ALL FORTY CHARACTERS for GitHub, which rejects a
  # short one outright: `Release.target_commitish is invalid`, HTTP
  # 422, measured 2026-08-21 on the first candidate this tool
  # published. Every hand-published candidate before it carried a full
  # sha because `gh` was handed one. The BODY still shows the short
  # form, which is what a person reads and types.
  full = run("git", "rev-parse", sha).stdout.strip()
  if len(full) != 40:
    print(f"git cannot resolve {sha} to a commit in this checkout; the "
          f"candidate names a tree that is not here")
    return 1
  dirty = run("git", "status", "--porcelain").stdout.strip()

  # ---- the body says CI is green, so ASK rather than claim.
  green, ci_sentence, _runs = ci_verdict(sha)
  if not green and not args.despite_ci:
    print(f"{ci_sentence}\nA candidate's body says what CI found, so "
          f"this refuses rather than publish a claim nobody checked. "
          f"Wait, or pass --despite-ci with a reason that will be "
          f"printed in the release body.")
    return 1
  if not green:
    ci_sentence = (f"{ci_sentence} Published anyway, deliberately: "
                   f"{args.despite_ci}")

  # ---- a candidate nobody described is a candidate nobody can test.
  if not args.notes or not os.path.exists(args.notes):
    print("--notes must name a markdown file saying what changed since "
          "the last candidate, in the words a tester needs. A "
          "candidate whose body is generated is a candidate nobody "
          "described.")
    return 1
  notes = open(args.notes, encoding="utf-8").read().strip()

  passed, failed, seen, unseen = gate_numbers(assets[1])
  body = (
    f"Release candidate for testing. **Not a release** — nothing is "
    f"promoted, `main` is untouched, and the plugin manager will show "
    f"this as `{label}`.\n\n"
    f"Built from `{sha}`"
    + ("" if not dirty else " (with uncommitted files that do not ship)")
    + f". Every local gate passed on that tree: the functional suite "
    f"in three shards, {passed} of {passed + failed} with no failures, "
    f"the visual gallery {seen} of {seen + unseen}, and the "
    f"colourspace comparison against the library's own renderer. "
    f"{ci_sentence}\n\n{notes}\n\n{CLOSING}\n")

  if args.dry_run:
    print(f"would publish {tag} as a pre-release on {sha}, with:")
    for a in assets:
      print(f"  {os.path.relpath(a, ROOT)}")
    print("\n--- body ---\n" + body)
    return 0

  made = run("gh", "release", "create", tag, *assets,
             "--repo", REPO, "--target", full, "--prerelease",
             "--title", f"{label} — release candidate",
             "--notes", body)
  if made.returncode != 0:
    print("gh refused to create the release:\n" + made.stderr.strip())
    return 1
  print(f"published {tag} as a pre-release: {made.stdout.strip()}")
  return 0


if __name__ == "__main__":
  sys.exit(main())
