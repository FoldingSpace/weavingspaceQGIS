#!/usr/bin/env python3
"""Build the installable plugin zip.

Usage: python3 build.py   (any Python 3; nothing QGIS-specific here)

Produces dist/weavingspace_qgis.zip, installable in QGIS via
Plugins > Manage and Install Plugins... > Install from ZIP. The zip
must contain the plugin folder as its top-level entry (QGIS unzips it
straight into the profile's python/plugins directory), so paths are
archived relative to the repo root. Excluded: caches, and the libs/
folder that the dependency provisioner may have created inside a
locally installed copy (provisioned wheels belong to one machine, and
shipping binaries would also break the official repository's rules).
Prefer cutting releases via release.py, which runs the test suite and
refuses to build on failure.
"""

import os
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "weavingspace_qgis")
DIST = os.path.join(ROOT, "dist")
EXCLUDE_DIRS = {"__pycache__", "libs", ".DS_Store"}


def main():
    os.makedirs(DIST, exist_ok=True)
    out = os.path.join(DIST, "weavingspace_qgis.zip")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for dirpath, dirnames, filenames in os.walk(SRC):
            dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
            for fn in filenames:
                if fn == ".DS_Store" or fn.endswith(".pyc"):
                    continue
                full = os.path.join(dirpath, fn)
                rel = os.path.relpath(full, ROOT)
                zf.write(full, rel)
    size = os.path.getsize(out) / 1e6
    print(f"wrote {out} ({size:.1f} MB)")


if __name__ == "__main__":
    main()
