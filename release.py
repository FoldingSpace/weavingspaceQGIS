#!/usr/bin/env python3
"""Cut a release: run every check, write the report, then build the zip.

Usage:
    python3 release.py            # find QGIS automatically (macOS)
    QGIS_PYTHON=... QGIS_PREFIX_PATH=... python3 release.py   # explicit

This is THE way to put out a version (see MAINTAINING.md). It will not
produce a zip unless everything passes. Steps, in order:

1. functional suite (tests/run_tests.py) under QGIS's bundled Python —
   the regression record of everything this project has fixed: the
   pyproj/threading rule, the tile-count guard, auto-render, per-row
   symbology behaviour, GeoPackage output, spacing persistence, QML
   round-trips;
2. visual gallery (tests/visual_tests.py), rendering canonical
   weavingspace outputs to PNGs with image assertions (including
   CIELAB distance-to-ramp checks) and writing
   reports/v<version>/index.html;
3. reference comparison (tools/visual_reference_report.py) in a
   separate Python environment with geopandas and matplotlib: each
   gallery render is scored in Lab colourspace against weavingspace's
   own TiledMap.render on identical inputs (the web app's rendering
   path), with the Quant: Unclassed render as fallback where quantile
   classing alone explains a mismatch; writes visual-comparison.pdf.
   The environment is found via $REFERENCE_PYTHON, else
   .venv-reference/ (created automatically on first use — this cannot
   run under QGIS's Python because macOS code-signing refuses PyPI C
   extensions in the signed QGIS process);
4. build.py, producing dist/weavingspace_qgis.zip.

Environment discovery: on macOS the newest /Applications/QGIS*.app is
used, deriving the interpreter and the env vars its Python needs
(PYTHONHOME because the app's python is relocated; PROJ_LIB so PROJ
finds its coordinate database; QT_QPA_PLATFORM=offscreen so no windows
open). On other platforms set QGIS_PYTHON and QGIS_PREFIX_PATH
yourself — see "Running the tests" in MAINTAINING.md for per-platform
commands.
"""

import argparse
import glob
import os
import shutil
import re
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))


def plugin_version():
  """The version this release will carry, read from metadata.txt.

  Returns:
    The value of the ``version=`` line in the plugin's metadata.txt,
    e.g. "1.4.2", or "unknown" when the field is missing. Nothing is
    written.

  metadata.txt is the single place a version is declared -- it is what
  QGIS's plugin manager reads out of the installed package -- so
  everything downstream is named from here: the report directory, the
  zip, the git tag, the changelog entry used as the commit message,
  and the version the citation file is mended to.
  """
  with open(os.path.join(ROOT, "weavingspace_qgis", "metadata.txt"),
            encoding="utf-8") as f:
    for line in f:
      if line.startswith("version="):
        return line.split("=", 1)[1].strip()
  return "unknown"


def qgis_environment():
  """(python_executable, env) for running scripts under QGIS's Python."""
  env = dict(os.environ)
  env.setdefault("QT_QPA_PLATFORM", "offscreen")
  explicit = os.environ.get("QGIS_PYTHON")
  if explicit:
    return explicit, env
  apps = sorted(glob.glob("/Applications/QGIS*.app"))
  if not apps:
    sys.exit("No QGIS app found; set QGIS_PYTHON and QGIS_PREFIX_PATH "
             "(see MAINTAINING.md).")
  contents = os.path.join(apps[-1], "Contents")
  pythons = sorted(glob.glob(os.path.join(contents, "MacOS", "python3.*")))
  if not pythons:
    sys.exit(f"No bundled python3 in {contents}/MacOS")
  env["PYTHONHOME"] = os.path.join(contents, "Frameworks")
  env["PROJ_LIB"] = os.path.join(contents, "Resources", "qgis", "proj")
  env["QGIS_PREFIX_PATH"] = os.path.join(contents, "MacOS")
  return pythons[0], env


def run(step, cmd, env, capture=False):
  """Run one release step, and abandon the release if it fails.

  Args:
    step: the human name of this stage ("visual gallery", "secrets
      audit"), printed as a banner and quoted in the abort message so
      a failure says which gate stopped the release.
    cmd: the command as a list of words, run with the repository root
      as its working directory.
    env: the environment to run it in. The stages that need QGIS get
      the interpreter environment from qgis_environment(); the plain
      ones (standards, secrets, the zip) get a copy of os.environ,
      because loading QGIS's Python into them buys nothing.
    capture: collect stdout and stderr and hand them back instead of
      letting them stream. Set for the stages whose output the
      testing report quotes test by test; the tail is still printed,
      so a long capture is not a silent one.

  Returns:
    The combined output when capture is set, otherwise the empty
    string. Nothing else is mutated -- but a non-zero exit status
    calls sys.exit here rather than returning, so no later step, and
    above all no zip, can be produced from a state that has already
    failed a gate.
  """
  print(f"\n=== {step} ===")
  result = subprocess.run(cmd, env=env, cwd=ROOT,
                          capture_output=capture, text=True)
  output = (result.stdout or "") + (result.stderr or "") if capture else ""
  if capture:
    print(output[-2000:])
  if result.returncode != 0:
    sys.exit(f"RELEASE ABORTED: {step} failed "
             f"(exit {result.returncode}); no zip was built.")
  return output


def test_docstrings():
  """{display name: first docstring sentence} for every functional
  test, read from tests/run_tests.py itself (the AST, so nothing needs
  importing under QGIS here). The display names come from the check()
  calls in its main(); the sentences from each test function's
  docstring. Used to annotate the testing report."""
  import ast
  import re
  path = os.path.join(ROOT, "tests", "run_tests.py")
  with open(path, encoding="utf-8") as f:
    source = f.read()
  tree = ast.parse(source)
  docs = {}
  for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
      doc = ast.get_docstring(node) or ""
      first = doc.replace("\n", " ").split(". ")[0].strip()
      docs[node.name] = (first + "." if first and not first.endswith(".")
                         else first)
  names = {}
  for m in re.finditer(r'check\("([^"]+)",\s*\n?\s*(test_\w+)\)',
                       source):
    names[m.group(1)] = docs.get(m.group(2), "")
  return names


def write_testing_report(report_dir, version, functional, visual,
                         comparison, coverage=""):
  """Write this release's per-test record to testing-report.md.

  Args:
    report_dir: reports/v<version>/, this release's evidence
      directory; the markdown file is written into it.
    version: the version being released, used in the heading.
    functional: captured output of tests/run_tests.py, read for its
      PASS/FAIL lines and annotated from each test's docstring.
    visual: captured output of tests/visual_tests.py, whose PASS/FAIL
      lines carry the measured values after " :: ".
    comparison: captured output of tools/visual_reference_report.py,
      the colourspace scores against the original renderer.
    coverage: captured output of tools/coverage_report.py. Only its
      "coverage:" summary line is used, and it defaults to empty so
      the report can still be written when coverage was not run --
      coverage is reported, never gating.

  Returns:
    None. Writes report_dir/testing-report.md, replacing any earlier
    one, and prints its path.

  Every test is listed individually rather than totalled, because
  this file is both the record the release notes point at (--push
  attaches it to the GitHub Release as the notes) and what the user
  is shown per test whenever something is published. A count of
  passes says nothing about which behaviours were actually checked.
  """
  lines = [f"# Testing report — v{version}", ""]
  lines += ["## Functional suite (tests/run_tests.py)", ""]
  annotations = test_docstrings()
  for ln in functional.splitlines():
    if ln.startswith(("PASS", "FAIL")):
      name = ln[4:].strip()
      note = annotations.get(name, "")
      lines.append(f"- **{ln[:4].strip()}** {name}"
                   + (f" — {note}" if note else ""))
  lines.append("")
  lines += ["## Visual gallery (tests/visual_tests.py)", ""]
  for ln in visual.splitlines():
    if ln.startswith(("PASS", "FAIL")):
      body = ln[4:].strip()
      name, _, detail = body.partition(" :: ")
      lines.append(f"- **{ln[:4].strip()}** {name}"
                   + (f" — {detail}" if detail.strip() else ""))
  lines.append("")
  lines += ["## Reference comparison "
            "(tools/visual_reference_report.py)", ""]
  for ln in comparison.splitlines():
    if ln.startswith(("PASS", "FAIL")):
      lines.append(f"- **{ln[:4].strip()}** {ln[4:].strip()}")
  summary = [ln for ln in coverage.splitlines()
             if ln.startswith("coverage:")]
  if summary:
    lines += ["## Coverage of plugin code", "",
              f"- {summary[-1]} (see coverage.md for the per-module "
              "table and the untested line runs)", ""]
  lines += ["", "Artifacts: index.html (gallery renders), "
            "visual-comparison.pdf (side-by-side against the original "
            "renderer), coverage.md, functional.txt (raw run).",
            "",
            "Not part of the gate, run before substantial releases: "
            "`tools/mutation_check.py` breaks each guarded behaviour "
            "in turn and confirms its test fails."]
  path = os.path.join(report_dir, "testing-report.md")
  with open(path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
  print(f"testing report: {path}")


def prune_old_reports(keep=3):
  """Delete all but the most recent report directories.

  Args:
    keep: how many versions to retain, newest first.

  Returns:
    None. Each release writes renders, a gallery, a comparison PDF
    and per-test output -- a few megabytes that are worth having for
    the version you just cut and the couple before it, and dead
    weight after that (they reached 136 MB across twenty versions
    before anyone looked). The zip in dist/ and the plugin installed
    in QGIS are what actually ship; these are evidence, and evidence
    for a version nobody is looking at any more is just disk.
  """
  import re
  import shutil
  reports = os.path.join(ROOT, "reports")
  if not os.path.isdir(reports):
    return

  def as_version(name):
    parts = re.findall(r"\d+", name)
    return tuple(int(p) for p in parts) if parts else (0,)

  versions = sorted((d for d in os.listdir(reports)
                     if d.startswith("v") and
                     os.path.isdir(os.path.join(reports, d))),
                    key=as_version)
  removed = 0
  for old_dir in versions[:-keep] if keep else versions:
    path = os.path.join(reports, old_dir)
    size = sum(os.path.getsize(os.path.join(dp, f))
               for dp, _dn, fn in os.walk(path) for f in fn)
    shutil.rmtree(path, ignore_errors=True)
    removed += size
  if removed:
    print(f"tidied {removed / 1e6:.0f} MB of superseded reports "
          f"(kept the newest {keep})")


def git(*arguments, check=True, quiet=False):
  """Run a git command in the project directory.

  Args:
    *arguments: the command, without the leading "git".
    check: raise if git fails. False where a non-zero status is an
      answer rather than an error (asking whether a tag exists).
    quiet: do not echo the command.

  Returns:
    The completed process, with stdout captured.
  """
  if not quiet:
    print(f"  git {' '.join(arguments)}")
  return subprocess.run(["git", *arguments], cwd=ROOT, check=check,
                        capture_output=True, text=True)


def changelog_entry(version):
  """The changelog lines for this version, as a paragraph.

  Args:
    version: the version being released.

  Returns:
    The text of the entry, or an empty string when there is none.
    Used as the commit message body, so that the history says what
    changed in the same words the plugin manager will show a user.
  """
  path = os.path.join(ROOT, "weavingspace_qgis", "metadata.txt")
  with open(path, encoding="utf-8") as handle:
    text = handle.read()
  match = re.search(rf"^changelog=(.*?)(?=^\w+=|\Z)", text,
                    re.S | re.M)
  if not match:
    return ""
  for block in match.group(1).split("\n\n"):
    if version in block:
      return " ".join(line.strip() for line in block.splitlines()).strip()
  return ""


def commit_and_tag(version, report_dir, push):
  """Record the release in version control, and optionally publish it.

  Args:
    version: the version being released.
    report_dir: this release's report directory, whose files are
      attached to the GitHub release.
    push: whether to send the result to GitHub. False leaves
      everything local and prints the commands instead.

  Returns:
    None.

  Committing and tagging are local and can be undone with one
  command, so they are unconditional: the repository should never
  disagree with the zip that was just built. Pushing and publishing
  cannot be undone once anyone has fetched, so they need the flag.
  """
  print("\n=== version control ===")
  inside = git("rev-parse", "--git-dir", check=False, quiet=True)
  if inside.returncode != 0:
    print("  not a git repository yet; skipping.\n"
          "  To start one:  git init && git add -A && "
          "git commit -m 'Initial commit'")
    return

  # asked twice, deliberately: the steps above generate files, and a
  # secret introduced by a generator is still a leaked secret
  run("secrets audit (pre-commit)",
      [sys.executable, os.path.join("tools", "check_no_secrets.py")],
      dict(os.environ))

  git("add", "-A")
  staged = git("diff", "--cached", "--quiet", check=False, quiet=True)
  if staged.returncode == 0:
    print("  nothing to commit; the tree already matches this release")
  else:
    entry = changelog_entry(version)
    message = f"Release v{version}"
    if entry:
      message += f"\n\n{entry}"
    git("commit", "-m", message)

  tag = f"v{version}"
  exists = git("rev-parse", "-q", "--verify", f"refs/tags/{tag}",
               check=False, quiet=True)
  if exists.returncode == 0:
    print(f"  tag {tag} already exists and will not be moved; bump the "
          f"version in metadata.txt for a new release")
  else:
    git("tag", "-a", tag, "-m", f"WeavingSpace plugin {tag}")

  assets = [os.path.join(ROOT, "dist", "weavingspace_qgis.zip"),
            os.path.join(report_dir, "testing-report.md"),
            os.path.join(report_dir, "visual-comparison.pdf")]
  assets = [a for a in assets if os.path.exists(a)]

  if not push:
    print("\n  Local only. To publish this release:")
    print(f"    git push origin HEAD && git push origin {tag}")
    print(f"    gh release create {tag} \\\n         "
          + " \\\n         ".join(assets)
          + f" \\\n         --title '{tag}' --notes-file "
            f"{os.path.relpath(assets[1], ROOT) if len(assets) > 1 else ''}")
    print("  or re-run with --push to do both.")
    return

  git("push", "origin", "HEAD")
  git("push", "origin", tag)
  if shutil.which("gh") is None:
    print("  gh is not installed, so the tag is pushed but no GitHub "
          "release was created. Either install it (brew install gh; "
          "gh auth login) or attach the files by hand at\n"
          "  https://github.com/FoldingSpace/weavingspaceQGIS/releases/new")
    return
  notes = os.path.join(report_dir, "testing-report.md")
  command = ["gh", "release", "create", tag, *assets, "--title", tag]
  if os.path.exists(notes):
    command += ["--notes-file", notes]
  print(f"  {' '.join(command[:4])} ...")
  subprocess.run(command, cwd=ROOT, check=True)
  print(f"  published: "
        f"https://github.com/FoldingSpace/weavingspaceQGIS/releases/tag/{tag}")
  print("  the project page updates itself from docs/ on the next "
        "GitHub Pages build, usually within a minute")


def main():
  """Cut a release from the command line, gate by gate.

  Returns:
    0 once a release candidate has been built (--rc), otherwise None
    when the full release has finished. Every failure leaves through
    run()'s sys.exit, so returning at all means the gates passed.

  What it leaves behind: reports/v<version>/ (functional output,
  gallery, coverage, comparison PDF, testing report), refreshed
  images in docs/img/, possibly a mended CITATION.cff,
  dist/weavingspace_qgis.zip, and a commit and tag. With --push, also
  a pushed branch and tag and a GitHub Release with the zip, report
  and PDF attached; --push is the single point at which anything
  leaves this machine.

  The ORDER is the substance of this function. The two cheap refusals
  come first, so a release that breaks the project's own rules or
  carries a secret fails in seconds rather than after the gallery.
  The test stages follow, then the report they feed, then the
  mutation guard over only what changed since the last tag, then the
  published images and the audit of the claims those images support.
  The zip is built last, from a tree every gate has already passed;
  committing and tagging are local and reversible, so they are
  unconditional. --rc stops before all of that, leaving a numbered
  candidate in dist/ and the tree untouched, because the gates can
  say whether the plugin is correct and only a person making a map
  can say whether it is any good to use.
  """
  parser = argparse.ArgumentParser(
    description="Build, test, document and publish a release.")
  parser.add_argument(
    "--push", action="store_true",
    help="after the gates pass, push the branch and tag and create the "
         "GitHub release. Without this the commit and tag stay local "
         "and the commands to publish them are printed.")
  parser.add_argument(
    "--rc", action="store_true",
    help="build a numbered release candidate for hands-on testing and "
         "stop. Runs the same correctness gates, skips the publication "
         "steps, and commits nothing.")
  args = parser.parse_args()

  started = time.time()
  version = plugin_version()
  print(f"Releasing WeavingSpace plugin v{version}")
  python, env = qgis_environment()
  print(f"QGIS Python: {python}")

  report_dir = os.path.join(ROOT, "reports", f"v{version}")
  os.makedirs(report_dir, exist_ok=True)
  # the functional suite writes its UI-vs-library renders here, and
  # the comparison step turns them into PDF pages
  env["WEAVINGSPACE_REPORT_DIR"] = report_dir

  # 0. the project's own rules, before anything expensive runs: a
  # release that breaks them should fail in seconds, not after the
  # visual gallery
  run("standards check",
      [sys.executable, os.path.join("tools", "check_standards.py")],
      dict(os.environ))

  # 0b. and nothing that must not be published, checked before any of
  # the expensive work and again immediately before the commit. A
  # leaked key is the one failure that cannot be undone by a later
  # release, so it is worth asking twice.
  run("secrets audit",
      [sys.executable, os.path.join("tools", "check_no_secrets.py")],
      dict(os.environ))

  # 1. functional suite; captured so the report can include it
  functional = run("functional suite",
                   [python, "-u", os.path.join("tests", "run_tests.py")],
                   env, capture=True)
  with open(os.path.join(report_dir, "functional.txt"), "w",
            encoding="utf-8") as f:
    # keep the readable tail (PASS/FAIL lines), not Qt's noise
    lines = [ln for ln in functional.splitlines()
             if ln.startswith(("PASS", "FAIL")) or "passed" in ln]
    f.write("\n".join(lines))

  # 1b. coverage of plugin code, from a second run of the same suite
  # (cheap: sys.monitoring disables each line after its first hit).
  # Reported, never gating: coverage is a map of untested ground, not
  # a target to satisfy.
  coverage = run("coverage report",
                 [python, "-u", os.path.join("tools", "coverage_report.py"),
                  report_dir], env, capture=True)

  # 2. visual gallery + HTML report (captured for the testing report)
  visual = run("visual gallery",
               [python, "-u", os.path.join("tests", "visual_tests.py")],
               env, capture=True)

  # 3. colourspace comparison against the original renderer, in a
  # plain (non-QGIS) environment that carries geopandas + matplotlib
  ref_python = os.environ.get("REFERENCE_PYTHON")
  if not ref_python:
    venv_dir = os.path.join(ROOT, ".venv-reference")
    ref_python = os.path.join(venv_dir, "bin", "python3")
    if not os.path.exists(ref_python):
      print("\n=== creating reference environment (.venv-reference) ===")
      run("create reference venv",
          [sys.executable, "-m", "venv", venv_dir], dict(os.environ))
      run("install reference packages",
          [os.path.join(venv_dir, "bin", "pip"), "install", "--quiet",
           "geopandas", "matplotlib", "networkx", "mapclassify"],
          dict(os.environ))
  comparison = run(
      "reference comparison",
      [ref_python, os.path.join("tools", "visual_reference_report.py"),
       report_dir], dict(os.environ), capture=True)

  write_testing_report(report_dir, version, functional, visual,
                       comparison, coverage)

  # 3a. Record which lines each test executes, then hold the code that
  # CHANGED since the last release to account: mutate only those lines
  # and require the tests to catch them. This is the routine guard
  # against a slow slide. The full campaign asks how good the suite is
  # over the whole plugin and takes hours; this asks whether today's
  # work is defended, costs minutes, and is the one that runs every
  # time. Skipped on the first release, when there is no previous tag
  # to compare against.
  run("per-test coverage record",
      [python, "-u", os.path.join("tools", "coverage_per_test.py")], env)
  previous = subprocess.run(["git", "describe", "--tags", "--abbrev=0"],
                            cwd=ROOT, capture_output=True, text=True)
  if previous.returncode == 0 and previous.stdout.strip():
    run(f"new-code mutation guard (since {previous.stdout.strip()})",
        [python, "-u", os.path.join("tools", "mutate_auto.py"),
         "--since", previous.stdout.strip(), "--sample", "12",
         "--workers", "2", "--require", "70"], env)
  else:
    print("\n=== new-code mutation guard ===\n  no previous release "
          "tag to compare against; skipped this once")

  # 3b. re-photograph what we publish. The README and the project page
  # show the dialog and a set of maps, and both are claims about how
  # the plugin currently looks and what it currently produces. They go
  # stale silently, so they are retaken from THIS release's gallery
  # rather than carried forward.
  run("refresh published images",
      [python, "-u", os.path.join("tools", "make_site_images.py"),
       "--gallery", report_dir], env)

  # 3c. and then check every other claim the published files make:
  # the citation version, the changelog entry, the images, the links,
  # the vendored library version, the repository URLs. Mechanical
  # corrections are applied; anything needing words stops the release.
  # The suite's own index, regenerated from the suite. Placed with
  # the published-content audit because it is the same kind of claim:
  # a document that describes something else and rots silently unless
  # it is rebuilt from the thing it describes.
  run("test map", [sys.executable, os.path.join("tools", "test_map.py")],
      dict(os.environ))

  run("published content audit",
      [sys.executable, os.path.join("tools", "sync_release_content.py"),
       "--fix", "--since", str(started)], dict(os.environ))

  # 4. build the zip only now that everything has passed
  if args.rc:
    # A candidate is the same code, packaged for people rather than
    # for publication: it goes no further than dist/, nothing is
    # committed, no tag is cut and no image or document is rewritten.
    # It exists because the checks above answer "is this correct?" and
    # cannot answer "is this any good to use?", which only comes back
    # from somebody making a map with it. Stopping here is the point:
    # a candidate that quietly did the publication steps would leave
    # the tree looking released when it is not.
    run("build release candidate",
        [sys.executable, "build.py", "--rc"], dict(os.environ))
    print(f"\nRelease candidate built from a passing tree. Nothing was "
          f"committed, tagged or published.\n"
          f"  candidates: dist/\n"
          f"  report:     {os.path.relpath(report_dir, ROOT)}\n\n"
          f"Install it in QGIS with Plugins > Manage and Install "
          f"Plugins... > Install from ZIP.\nWhen the feedback is in, "
          f"run release.py (or release.py --push) for the real thing.")
    return 0

  run("build zip", [sys.executable, "build.py"], dict(os.environ))

  prune_old_reports(keep=3)

  # 5. version control. Committing and tagging are local and
  # reversible, so they always happen; pushing is neither, so it
  # happens only when asked for on this invocation.
  commit_and_tag(version, report_dir, push=args.push)

  print(f"\nRelease v{version} complete."
        f"\n  zip:        dist/weavingspace_qgis.zip"
        f"\n  report:     reports/v{version}/index.html"
        f"\n  tests:      reports/v{version}/testing-report.md"
        f"\n  comparison: reports/v{version}/visual-comparison.pdf")


if __name__ == "__main__":
  main()
