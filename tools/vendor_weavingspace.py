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
  1. Optional plotting dependencies. QGIS installs often lack
     matplotlib (and occasionally scipy); the plugin never plots with
     them, so their imports are wrapped to fall back to a proxy
     (_optional.MissingModule) that only errors if actually *called*.
  2. Performance: _TileGrid buffers the region to find its tiling
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
  (OK if applied else FAILED).append(name)
  mark = "applied" if applied else "NEEDS ATTENTION"
  print(f"  [{mark}] {name}" + (f" — {detail}" if detail else ""))


def targeted(path, name, old, new):
  """Apply one exact-anchor patch; report instead of raising when the
  anchor no longer exists in the new upstream."""
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

The QGIS plugin build of weavingspace does not require matplotlib or
scipy: they are only used by the notebook-oriented plotting helpers.
When absent we substitute a proxy that supports attribute access (so
type annotations such as ``plt.Axes`` still evaluate) but raises
ImportError as soon as anything is actually called.
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
      "matplotlib (and topology splines need scipy); the QGIS plugin "
      "does not use them.")
'''

# an optional import wrapped in a fallback to the proxy above
OPTIONAL_TEMPLATE = """try:
{imports}
except ImportError:
  from weavingspace._optional import MissingModule
{fallbacks}"""


def wrap_optional(path, name, import_lines, fallback_lines):
  """PATCH 1 for one file: wrap the given import statement(s)."""
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
  stamp = version if not commit else f"{version} ({commit})"
  (VENDOR_DIR.parent / "VENDOR-VERSION.txt").write_text(
    f"{stamp}\n", encoding="utf-8")
  print(f"recorded upstream version: {stamp}")
  return version


def main():
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
  wrap_optional(VENDOR_DIR / "topology.py", "1e topology scipy",
                ["from scipy import interpolate"],
                ['interpolate = MissingModule("scipy.interpolate")'])

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
