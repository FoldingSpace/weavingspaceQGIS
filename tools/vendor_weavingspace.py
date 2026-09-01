#!/usr/bin/env python3
"""Vendor (or re-vendor) the weavingspace library into the plugin.

Usage:
    python3 tools/vendor_weavingspace.py /path/to/weavingspace/weavingspace

The argument is the *package directory* of an upstream checkout or
release (the folder containing tileable.py, tile_map.py, ...). The
script copies it into weavingspace_qgis/vendor/weavingspace and
re-applies every plugin patch, so upgrading the core library is:

    1. get the new upstream,
    2. run this script,
    3. read its report,
    4. run release.py (tests + visual gallery + zip).

The plugin targets QGIS 4+ (Python 3.12+), so upstream's modern
Python (match statements, dataclass slots, and so on) is vendored
untouched. WHY PATCHES EXIST (each is a numbered PATCH below):
  1. Optional plotting dependencies. QGIS installs lack matplotlib and
     the plugin never plots with it, so its imports are wrapped to fall
     back to a proxy (_optional.MissingModule) that only errors if
     actually *called*. Scipy was in this family until 2026-08-31, when
     upstream dropped its one use; patches 1e and 1f are retired below
     with the measurement that closed them.
  2. Performance (RETIRED -- see below; upstream adopted the same
   optimisation and the patch went with it): _TileGrid buffers the
   region to find its tiling
     rectangle; buffering the *convex hull* instead of the full
     detailed union is equivalent for that purpose (hull ⊇ union, and
     the rectangle only needs to contain the region generously) and
     turns minutes into milliseconds on coastline-heavy data.

FAILURE MODE, BY DESIGN: every patch asserts on an exact anchor string
from upstream. When a new upstream changes that code, the script
REPORTS the patch as needing attention instead of writing a silently
broken vendor — read the report, adapt the patch (the intent is
documented at each one), rerun.

The script needs only the standard library; run it with any Python 3.
"""

import pathlib
import re
import subprocess
import shutil
import sys

PLUGIN_DIR = pathlib.Path(__file__).resolve().parent.parent / "weavingspace_qgis"
VENDOR_DIR = PLUGIN_DIR / "vendor" / "weavingspace"

OK, FAILED = [], []


def report(name, applied, detail=""):
  """Record and announce the outcome of one patch.

  Args:
    name: the patch's label, the same one used in the numbered PATCH
      comments in main(), e.g. "1c tile_map matplotlib". It is what a
      maintainer reads in the summary line and then goes looking for
      in this file.
    applied: True when the vendored file now carries the patch,
      including the case where it was already present; False when the
      upstream anchor no longer matches and a person has to adapt the
      patch by hand.
    detail: optional clause printed after the name, used to say why
      nothing was written ("anchor not found in tileable.py") or that
      there was nothing to do ("already present"). Omitted when the
      patch simply applied.

  Returns:
    Nothing. Appends name to the module-level OK or FAILED list, which
    is what the closing summary counts and what decides the exit
    status; the immediate feedback goes to stdout.
  """
  (OK if applied else FAILED).append(name)
  mark = "applied" if applied else "NEEDS ATTENTION"
  print(f"  [{mark}] {name}" + (f" — {detail}" if detail else ""))


def targeted(path, name, old, new):
  """Apply one exact-anchor patch; report instead of raising when the
  anchor no longer exists in the new upstream.

  Args:
    path: the file to rewrite, always one already copied into
      VENDOR_DIR. The upstream checkout is never touched.
    name: the patch's label, passed straight to report().
    old: the upstream text to find, character for character. The
      exactness is the point: a fuzzy match would let a changed
      upstream be patched in a way nobody had read.
    new: the text that replaces it. It doubles as the "already
      patched" marker, so it must be the complete patched form and
      must not appear in unpatched upstream, or a re-vendor would
      either skip a needed patch or apply it twice.

  Returns:
    Nothing. Rewrites path in place when the anchor is present and the
    patch is not, replacing only the FIRST occurrence so that a patch
    written against one site cannot silently spread to a second one
    that happens to match. Any other outcome leaves the file exactly
    as copied. Every path reports, so the patch lands in OK or FAILED
    and never passes unnoticed.
  """
  text = path.read_text()
  if new in text:
    report(name, True, "already present")
    return
  if old not in text:
    report(name, False, f"anchor not found in {path.name}")
    return
  path.write_text(text.replace(old, new, 1))
  report(name, True)


OPTIONAL_PY = '''"""Placeholders for optional plotting dependencies.

The QGIS plugin build of weavingspace does not require matplotlib: it
is used only by the notebook-oriented plotting helpers. When absent we
substitute a proxy that supports attribute access (so type annotations
such as ``plt.Axes`` still evaluate) but raises ImportError as soon as
anything is actually called.

Scipy was named here too until 2026-08-31. Upstream's only use of it
was one interpolating spline in ``Topology.zigzag_between_points``,
which their commit 2dbea80 replaced by sampling ``np.sin`` directly, so
the vendored library no longer imports scipy anywhere. The proxy stays
general rather than being renamed for matplotlib, since the next
optional dependency will want the same treatment.
"""

from __future__ import annotations


class MissingModule:
  """Stand-in for an uninstalled optional module."""

  def __init__(self, name: str) -> None:
    self._missing_name = name

  def __getattr__(self, attr: str) -> "MissingModule":
    if attr.startswith("__") and attr.endswith("__"):
      raise AttributeError(attr)
    return MissingModule(f"{self._missing_name}.{attr}")

  def __call__(self, *args, **kwargs):
    raise ImportError(
      f"'{self._missing_name}' requires an optional dependency that is "
      "not installed in this Python environment. Plotting helpers need "
      "matplotlib; the QGIS plugin does not use them.")
'''

# an optional import wrapped in a fallback to the proxy above
OPTIONAL_TEMPLATE = """try:
{imports}
except ImportError:
  from weavingspace._optional import MissingModule
{fallbacks}"""


def wrap_optional(path, name, import_lines, fallback_lines):
  """PATCH 1 for one file: wrap the given import statement(s).

  Args:
    path: the vendored module whose plotting imports must become
      optional.
    name: the patch's label for the report, e.g. "1e topology scipy".
    import_lines: upstream's import statement(s) exactly as written,
      unindented and in upstream's own order. They are joined with
      newlines to form the anchor, so they must be CONSECUTIVE lines
      upstream; a blank line or a reordering between them makes the
      patch report as needing attention, which is the intended
      failure.
    fallback_lines: the assignments to run when the import raises
      ImportError, one per name the import would have bound, each
      binding a MissingModule proxy (see OPTIONAL_PY). Every name the
      module later uses must appear here, or the fallback path fails
      with NameError at import time instead of the proxy's much more
      informative ImportError at call time.

  Returns:
    Nothing. Builds the try/except form and hands it to targeted(), so
    the file is rewritten in place and the outcome recorded in OK or
    FAILED.
  """
  anchor = "\n".join(import_lines)
  replacement = OPTIONAL_TEMPLATE.format(
    imports="\n".join("  " + ln for ln in import_lines),
    fallbacks="\n".join("  " + ln for ln in fallback_lines))
  targeted(path, name, anchor, replacement)


def record_upstream_version(upstream):
  """Write down which upstream release this vendor copy came from.

  Args:
    upstream: the weavingspace PACKAGE directory that was copied.

  Returns:
    The version string recorded, or "unknown" when the upstream tree
    carries no pyproject.toml to read it from.

  Why a file rather than prose: the vendored version is claimed in
  README.md, MAINTAINING.md and CLAUDE.md, and prose does not update
  itself. With a stamp on disk the release-time content audit can
  check those claims against something that was written by the tool
  that actually did the copying.
  """
  version = "unknown"
  commit = ""
  project = upstream.parent / "pyproject.toml"
  if project.exists():
    for line in project.read_text(encoding="utf-8").splitlines():
      match = re.match(r"""\s*version\s*=\s*["']([^"']+)["']""", line)
      if match:
        version = match.group(1)
        break
  try:
    result = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                            cwd=upstream.parent, capture_output=True,
                            text=True, check=True)
    commit = result.stdout.strip()
  except (subprocess.CalledProcessError, FileNotFoundError, OSError):
    pass
  # A MISSING COMMIT IS SAID OUT LOUD rather than quietly dropped.
  # The stamp carries the commit precisely BECAUSE upstream does not
  # always bump the version when the code moves, so a stamp reduced to
  # its version half has lost the part that was the reason for having
  # it -- and it looks exactly like a stamp that never had one. Met on
  # 2026-08-30, vendoring from a `git archive` extraction with no
  # repository in it, which turned "0.0.7.89 (bf1bbbf)" into
  # "0.0.7.89" with nothing said.
  if not commit:
    print("  WARNING: no git repository above the upstream package, so "
          "the stamp records the VERSION ONLY.\n"
          "  Upstream does not always bump the version when the code "
          "changes, which is why the commit is recorded at all.\n"
          "  Vendor from a checkout rather than an export, or write "
          "the commit into VENDOR-VERSION.txt by hand.")
  stamp = version if not commit else f"{version} ({commit})"
  (VENDOR_DIR.parent / "VENDOR-VERSION.txt").write_text(
    f"{stamp}\n", encoding="utf-8")
  print(f"recorded upstream version: {stamp}")
  return version


def main():
  """Replace the vendored library from an upstream tree, then patch it.

  The upstream package directory comes from the single command-line
  argument. VENDOR_DIR is deleted and copied afresh, which is exactly
  why a hand edit to a vendored file cannot survive and why every
  plugin change to upstream code lives here as a patch instead.
  _optional.py (the proxy the patches fall back to) is written after
  the copy, since it is ours rather than upstream's, and the version
  stamp is recorded before any patching so that even an aborted run
  leaves a truthful record of what was copied.

  Returns:
    Nothing; the process exits instead. Exit 2 with the usage text
    when the argument is missing, exit 1 with a message when the
    directory carries no tileable.py (the cheapest test that this is
    the PACKAGE directory and not the repository root above it),
    exit 1 when any patch needs attention, and exit 0 only when every
    patch applied. Non-zero is what stops release.py from building a
    zip around a vendor tree whose report nobody has read.
  """
  if len(sys.argv) != 2:
    print(__doc__)
    sys.exit(2)
  upstream = pathlib.Path(sys.argv[1]).resolve()
  if not (upstream / "tileable.py").exists():
    sys.exit(f"{upstream} does not look like the weavingspace package "
             "directory (no tileable.py)")

  print(f"Vendoring {upstream}\n     into {VENDOR_DIR}")
  if VENDOR_DIR.exists():
    shutil.rmtree(VENDOR_DIR)
  shutil.copytree(upstream, VENDOR_DIR,
                  ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
  (VENDOR_DIR / "_optional.py").write_text(OPTIONAL_PY)
  record_upstream_version(upstream)
  print("copied; applying patches:")

  # ---- PATCH 1: optional matplotlib / scipy -----------------------------
  wrap_optional(VENDOR_DIR / "tileable.py", "1a tileable matplotlib",
                ["from matplotlib import pyplot as plt"],
                ['plt = MissingModule("matplotlib.pyplot")'])
  wrap_optional(VENDOR_DIR / "symmetry.py", "1b symmetry matplotlib",
                ["from matplotlib import pyplot as plt"],
                ['plt = MissingModule("matplotlib.pyplot")'])
  wrap_optional(VENDOR_DIR / "tile_map.py", "1c tile_map matplotlib",
                ["import matplotlib.colors",
                 "import matplotlib.pyplot as plt"],
                ['matplotlib = MissingModule("matplotlib")',
                 'plt = MissingModule("matplotlib.pyplot")'])
  wrap_optional(VENDOR_DIR / "topology.py", "1d topology matplotlib",
                ["import matplotlib.pyplot as plt"],
                ['plt = MissingModule("matplotlib.pyplot")'])
  # PATCHES 1e (wrap `from scipy import interpolate`) and 1f (replace
  # the ONE call that needed it) were RETIRED on 2026-08-31, at the
  # re-vendor to upstream 6190917, BECAUSE UPSTREAM MERGED THE CHANGE
  # ITSELF -- commit 2dbea80, "dropping scipy spline dependency from
  # Topology.zigzag_between_points", which had been on their
  # `experimental` branch and is now on `main`.
  #
  # 1f's own comment said this was the moment to delete it: it was a
  # patch rather than a wait precisely because that branch's first
  # commit says it holds "code changes that QGIS plugin can ignore
  # until they are merged". The tool did what it is built to do -- both
  # anchors stopped matching and it NAMED them rather than writing a
  # broken vendor.
  #
  # MEASURED AT THE RE-VENDOR rather than assumed: the vendored tree
  # now contains no reference to scipy at all (the only `interpolate`
  # names left are shapely's `line_interpolate_point` and
  # `LineString.interpolate`), and `zigzag_between_points` samples
  # `np.sin` at (n + smoothness) * 2 + 1 points, which is character for
  # character what patch 1f used to write. So there is nothing left to
  # wrap and nothing left to replace.
  #
  # WHAT REMAINS OF PATCH 1 IS MATPLOTLIB ALONE, which is why 1a-1d
  # stand above and _optional.py stays: QGIS ships no matplotlib and
  # upstream's plotting helpers import it at module level.

  # PATCH 2 (hull buffer in _get_rect_to_tile) was RETIRED on
  # 2026-08-07: upstream adopted the same optimisation itself
  # (commit 8235837), in its own variant — per-geometry convex hulls,
  # a coverage union, then a hull of that. It was verified to tile
  # identically to the patch it replaces (349 tiles, same per-element
  # counts, same total area on the Auckland dataset) and is faster
  # again, so carrying our own version would be pure divergence.
  # Only the optional-imports family remains.


  # PATCH 2 (vectorised tile materialisation) was RETIRED on
  # 2026-08-07, the day after it was offered: upstream took it
  # (commit d4741e6, "optimisation of construction of
  # Tiling.make_tiling() using shapely.transform and numpy"), in a
  # tidier form than ours -- a _to_grid_points helper rather than a
  # closure inside make_tiling. Upstream also took the companion
  # change to the membership test (an STRtree over the region's own
  # polygons instead of testing every tile against region_union),
  # which we had offered but never vendored. Nothing to carry.
  #
  # Two notes kept for whoever revisits this:
  #  * upstream calls shapely.transform with include_z=False
  #    unconditionally, so a 3D tileable would lose its z. Ours
  #    handled that; weavingspace units are 2D, so it costs nothing
  #    today, but it is the one behavioural difference between the
  #    two versions.
  #  * the module still binds the name `shapely` only through
  #    `import shapely.ops`. That is a real Python rule (importing a
  #    submodule binds the package), not an accident, but it is the
  #    sort of thing an import tidy-up could break.

  print(f"\n{len(OK)} patches applied, {len(FAILED)} need attention"
        + (": " + ", ".join(FAILED) if FAILED else ""))
  print("Next: run release.py (tests, visual gallery, zip).")
  sys.exit(1 if FAILED else 0)


if __name__ == "__main__":
  main()
