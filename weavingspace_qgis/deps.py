"""Dependency provisioning for the WeavingSpace plugin.

Most QGIS 4+ installations bundle everything weavingspace needs
(geopandas, pandas, shapely, pyproj, networkx); the notable gap is
Linux, where QGIS uses the distribution's Python and these packages may
not be installed. This module makes missing packages available with
zero user tooling:

1. wheels bundled in the plugin's ``wheels/`` folder that match the running
   interpreter are extracted into ``<plugin>/libs`` (a wheel is just a zip);
2. anything still missing can be fetched from PyPI (with user consent,
   handled by the caller) by picking the correct wheel for this interpreter
   from the PyPI JSON API and extracting it the same way.

No pip, no package manager, nothing touches the QGIS Python installation
itself: everything lands in the plugin's own ``libs`` folder, which is
*prepended* to ``sys.path`` — deliberately, so that a package we
provisioned (only ever done when the QGIS-shipped one is absent or
below the version floor) beats the stale copy; libs never contains a
package whose shipped version was adequate, so nothing healthy is
shadowed. See add_paths for the same rationale at the code.
"""

from __future__ import annotations

import importlib
import importlib.util
import json
import os
import re
import sys
import tempfile
import urllib.request
import zipfile

PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
LIBS_DIR = os.path.join(PLUGIN_DIR, "libs")
WHEELS_DIR = os.path.join(PLUGIN_DIR, "wheels")
VENDOR_DIR = os.path.join(PLUGIN_DIR, "vendor")

# import name -> PyPI distribution name.
REQUIRED = {
  "numpy": "numpy",
  "shapely": "shapely",
  "pandas": "pandas",
  "pyproj": "pyproj",
  "geopandas": "geopandas",
  "networkx": "networkx",
}

# Minimum versions weavingspace actually needs at runtime. A system
# package manager can supply geopandas/shapely too old to carry e.g.
# GeoSeries.union_all or shapely 2's vectorised API while importing
# fine, so versions are checked, not just importability. numpy's floor is what the
# pandas wheels we may provision require; we only ever provision numpy
# 1.26.x (never 2.x), which stays ABI-compatible with modules QGIS built
# against older numpy 1.x.
MIN_VERSIONS = {
  "numpy": (1, 22, 4),
  "shapely": (2, 0, 0),
  "pandas": (2, 0, 0),
  "pyproj": (3, 3, 0),
  "geopandas": (1, 0, 0),
  "networkx": (2, 4, 0),
}

# pure-python runtime deps of the packages above (import name -> PyPI name).
# Provisioned automatically when absent; all tiny py3-none-any wheels.
SUPPORT = {
  "packaging": "packaging",       # geopandas
  "dateutil": "python-dateutil",  # pandas
  "pytz": "pytz",                 # pandas
  "tzdata": "tzdata",             # pandas
  "six": "six",                   # python-dateutil
  "certifi": "certifi",           # pyproj
}

SUPPORT_CANDIDATES = {
  "packaging": ["25.0", "24.2"],
  "python-dateutil": ["2.9.0.post0"],
  "pytz": ["2025.2"],
  "tzdata": ["2025.2"],
  "six": ["1.17.0"],
  "certifi": ["2025.7.14", "2024.8.30"],
}

# candidate versions, newest first; the first with a wheel matching
# this interpreter wins (QGIS 4+ bundles Python 3.12 or newer).
PYPI_CANDIDATES = {
  "numpy": ["1.26.4"],
  "shapely": ["2.1.2", "2.0.7"],
  "pandas": ["2.3.3", "2.2.3"],
  "pyproj": ["3.7.2", "3.7.1"],
  "geopandas": ["1.1.2"],
  "networkx": ["3.4.2"],
}


def add_paths() -> None:
  """Put vendor (weavingspace itself) and libs on sys.path.

  Both are *prepended*: vendor so our patched weavingspace beats any
  pip-installed copy, libs so packages we provisioned (which we only do
  when the QGIS-shipped version is absent or too old) beat the stale
  bundled ones. libs never contains a package whose shipped version was
  adequate, so nothing healthy gets shadowed.
  """
  for path in (LIBS_DIR, VENDOR_DIR):
    if os.path.isdir(path):
      if path in sys.path:
        sys.path.remove(path)
      sys.path.insert(0, path)


def _parse_version(text: str) -> tuple:
  """Version string to a comparable tuple.

  Args:
    text: a version as PyPI or a package reports it, e.g. "2.3.3",
      "1.26" or "3.0.0rc1".

  Returns:
    A (major, minor, patch) tuple of ints, padded and with any
    suffix dropped, so versions can be compared with < and >.
  """
  parts = []
  for chunk in re.split(r"[.\-+]", text)[:3]:
    m = re.match(r"\d+", chunk)
    parts.append(int(m.group()) if m else 0)
  return tuple(parts + [0] * (3 - len(parts)))


def _installed_version(import_name: str) -> str | None:
  """Version of the package as it would import right now, or None."""
  try:
    import importlib.metadata as md
  except ImportError:  # pragma: no cover - py3.7 only
    return None
  try:
    module = importlib.import_module(import_name)
    version = getattr(module, "__version__", None)
    if version is None:
      version = md.version(REQUIRED[import_name])
    return version
  except Exception:
    return None


def missing_packages() -> list[str]:
  """Import names of required packages that are absent *or too old*."""
  add_paths()
  needed = []
  for import_name in REQUIRED:
    try:
      if importlib.util.find_spec(import_name) is None:
        needed.append(import_name)
        continue
    except (ImportError, ValueError):
      needed.append(import_name)
      continue
    version = _installed_version(import_name)
    if version is None or \
        _parse_version(version) < MIN_VERSIONS[import_name]:
      # unimportable/unidentifiable counts as needing provision too
      needed.append(import_name)
  return needed


def _forget_modules(import_names: list[str]) -> None:
  """Drop provisioned packages from sys.modules so the fresh copies in
  libs are picked up (the version check may have imported stale ones)."""
  for name in import_names:
    for mod in [m for m in sys.modules if m == name
                or m.startswith(name + ".")]:
      del sys.modules[mod]
  add_paths()  # libs may only exist since the first extraction
  importlib.invalidate_caches()


def _python_ok(requires_python) -> bool:
  """Check a PyPI requires_python specifier against this interpreter."""
  if not requires_python:
    return True
  current = sys.version_info[:3]
  try:
    for clause in str(requires_python).split(","):
      clause = clause.strip()
      m = re.match(r"(>=|<=|==|!=|>|<|~=)\s*([\d.*]+)$", clause)
      if not m:
        continue  # unknown clause: don't let it block us
      op, ver = m.groups()
      ver = ver.replace(".*", "")
      target = _parse_version(ver)
      ok = {">=": current >= target, ">": current > target,
            "<=": current <= target, "<": current < target,
            "==": current[:len(ver.split('.'))] ==
                  target[:len(ver.split('.'))],
            "!=": current[:len(ver.split('.'))] !=
                  target[:len(ver.split('.'))],
            "~=": current >= target}[op]
      if not ok:
        return False
  except Exception:
    return True
  return True


def _manual_tags() -> list[str]:
  """Minimal wheel-tag list for interpreters without packaging or pip.

  Rare QGIS builds have shipped without either. This covers the
  realistic cases: CPython binary wheels for this exact version, abi3
  wheels, and pure-python wheels.
  """
  import sysconfig
  major, minor = sys.version_info[:2]
  cp = f"cp{major}{minor}"
  plat = sysconfig.get_platform().replace("-", "_").replace(".", "_")
  plats = [plat]
  if sys.platform == "darwin":
    # accept a range of macOS deployment targets and fat binaries
    import platform as _platform
    arch = _platform.machine()
    for ver in ("15_0", "14_0", "13_0", "12_0", "11_0", "10_15", "10_13",
                "10_9"):
      plats += [f"macosx_{ver}_{arch}", f"macosx_{ver}_universal2"]
  elif sys.platform.startswith("linux"):
    import platform as _platform
    arch = _platform.machine()
    for glibc_minor in range(40, 16, -1):
      plats.append(f"manylinux_2_{glibc_minor}_{arch}")
    plats += [f"manylinux2014_{arch}", f"manylinux2010_{arch}",
              f"manylinux1_{arch}"]
  tags = []
  for p in plats:
    tags.append(f"{cp}-{cp}-{p}")
  for m in range(minor, 1, -1):
    for p in plats:
      tags.append(f"cp{major}{m}-abi3-{p}")
  tags.append(f"{cp}-none-any")
  tags.append("py3-none-any")
  return tags


def _sys_tags() -> list[str]:
  """Compatible wheel tags for this interpreter, most preferred first.

  Uses the ``packaging`` library, or pip's vendored copy, or a manual
  fallback for QGIS builds that ship neither.
  """
  try:
    from packaging.tags import sys_tags
  except ImportError:
    try:
      from pip._vendor.packaging.tags import sys_tags
    except ImportError:
      return _manual_tags()
  return [str(t) for t in sys_tags()]


def _wheel_tags(wheel_name: str) -> list[str]:
  """Expand a wheel filename's compressed tag set to individual tags."""
  stem = wheel_name[:-4] if wheel_name.endswith(".whl") else wheel_name
  parts = stem.split("-")
  # name-version[-build]-python-abi-platform
  pythons, abis, platforms = parts[-3], parts[-2], parts[-1]
  return [f"{py}-{abi}-{plat}"
          for py in pythons.split(".")
          for abi in abis.split(".")
          for plat in platforms.split(".")]


def _best_wheel(filenames: list[str]) -> str | None:
  """Pick the wheel that best fits this interpreter.

  Args:
    filenames: candidate wheel filenames, as PyPI lists them.

  Returns:
    The best-matching filename, or None when none of them can run
    here. "Best" means highest-ranked in ``_sys_tags()``, which
    orders this interpreter's acceptable tags from most specific
    (built for this Python and this CPU) to least (pure Python, any
    platform); a wheel whose tags do not appear there at all would
    fail to import and is never chosen.
  """
  ranks = {tag: i for i, tag in enumerate(_sys_tags())}
  best, best_rank = None, None
  for fn in filenames:
    if not fn.endswith(".whl"):
      continue
    try:
      rank = min(ranks[t] for t in _wheel_tags(fn) if t in ranks)
    except ValueError:
      continue  # no compatible tag
    if best_rank is None or rank < best_rank:
      best, best_rank = fn, rank
  return best


def _extract_wheel(path: str) -> None:
  """Unpack a wheel into the plugin's own libs directory.

  Args:
    path: the .whl file to extract.

  Returns:
    None. A wheel is a zip, and everything lands in libs/ so nothing
    outside the plugin folder is ever touched.
  """
  os.makedirs(LIBS_DIR, exist_ok=True)
  with zipfile.ZipFile(path) as zf:
    zf.extractall(LIBS_DIR)


def provision_from_bundled(missing: list[str]) -> list[str]:
  """Extract any bundled wheels that satisfy missing packages.

  Returns the packages still missing afterwards.
  """
  if not os.path.isdir(WHEELS_DIR):
    return missing
  wheels = os.listdir(WHEELS_DIR)
  still_missing = []
  for import_name in missing:
    dist = REQUIRED[import_name]
    norm = re.sub(r"[-_.]+", "_", dist).lower()
    mine = [w for w in wheels
            if re.sub(r"[-_.]+", "_", w.split("-")[0]).lower() == norm]
    chosen = _best_wheel(mine)
    if chosen:
      try:
        _extract_wheel(os.path.join(WHEELS_DIR, chosen))
      except Exception:
        # A wheel that is not a readable zip -- truncated by a copy,
        # or not a wheel at all -- used to let zipfile.BadZipFile out
        # of here, through _ensure_dependencies and out of
        # open_dialog, so pressing the toolbar button produced a
        # traceback instead of a sentence. A bundled file we cannot
        # read means the dependency is still missing, which is a
        # state this function already knows how to report; the PyPI
        # path below declines the same way.
        still_missing.append(import_name)
    else:
      still_missing.append(import_name)
  _forget_modules([m for m in missing if m not in still_missing])
  return still_missing


def _fetch_dist(dist: str, candidates: list[str], progress=None) -> bool:
  """Download and extract the best-matching wheel for one distribution.

  Args:
    dist: the PyPI project name, e.g. "geopandas".
    candidates: versions to try, newest first; the first whose wheel
      fits this interpreter wins.
    progress: optional callable(str), so a setup dialog can say what
      is happening during a synchronous download.

  Returns:
    True when a wheel was fetched and unpacked into libs/.
  """
  for version in candidates:
    url = f"https://pypi.org/pypi/{dist}/{version}/json"
    try:
      with urllib.request.urlopen(url, timeout=30) as resp:
        info = json.load(resp)
    except Exception:
      continue
    files = {f["filename"]: f["url"] for f in info.get("urls", [])
             if _python_ok(f.get("requires_python"))}
    chosen = _best_wheel(list(files))
    if not chosen:
      continue
    if progress:
      progress(f"Downloading {chosen}...")
    try:
      with tempfile.TemporaryDirectory() as td:
        dest = os.path.join(td, chosen)
        urllib.request.urlretrieve(files[chosen], dest)
        _extract_wheel(dest)
      return True
    except Exception:
      continue
  return False


def provision_from_pypi(missing: list[str], progress=None) -> list[str]:
  """Download and extract matching wheels from PyPI for missing packages.

  Args:
    missing: import names still unavailable after bundled wheels were
      tried.
    progress: optional callable(str) for setup-dialog messages.

  Returns:
    The packages STILL missing; empty means the plugin can run. Any
    absent pure-python support packages (packaging, dateutil and the
    like) that the main packages import at runtime are fetched too,
    since a partial install fails later and less clearly.
  """
  still_missing = []
  for import_name in missing:
    dist = REQUIRED[import_name]
    if not _fetch_dist(dist, PYPI_CANDIDATES.get(dist, []), progress):
      still_missing.append(import_name)
  provisioned = [m for m in missing if m not in still_missing]
  if provisioned:
    for import_name, dist in SUPPORT.items():
      try:
        present = importlib.util.find_spec(import_name) is not None
      except (ImportError, ValueError):
        present = False
      if not present:
        _fetch_dist(dist, SUPPORT_CANDIDATES.get(dist, []), progress)
  _forget_modules(provisioned)
  return still_missing


def ensure_pyproj_data() -> None:
  """If pyproj was provisioned into libs, force it onto its own PROJ data.

  QGIS sets PROJ_LIB for its own (possibly different-versioned) PROJ; a
  wheel-installed pyproj must use the proj.db it shipped with.
  """
  pyproj_dir = os.path.join(LIBS_DIR, "pyproj")
  if not os.path.isdir(pyproj_dir):
    return
  data = os.path.join(pyproj_dir, "proj_dir", "share", "proj")
  if os.path.isdir(data):
    try:
      import pyproj.datadir
      pyproj.datadir.set_data_dir(data)
    except Exception:
      pass
