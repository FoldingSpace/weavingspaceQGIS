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

import argparse
import os
import re
import shutil
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "weavingspace_qgis")
DIST = os.path.join(ROOT, "dist")
EXCLUDE_DIRS = {"__pycache__", "libs", ".DS_Store"}
METADATA = os.path.join(SRC, "metadata.txt")


def declared_version():
    """The version in metadata.txt, which is the one QGIS believes."""
    with open(METADATA, encoding="utf-8") as handle:
        match = re.search(r"^version=(.+)$", handle.read(), re.MULTILINE)
    return match.group(1).strip() if match else "0.0.0"


def next_candidate(version):
    """The next unused release-candidate number for this version.

    Args:
      version: the declared version, e.g. "0.24.0".

    Returns:
      An integer, 1 the first time and one more than the highest any
      artefact in dist/ has already claimed.

    Every artefact that BEARS a number counts, not just the zip: the
    dossier and the receipt claim it too. Counting only zips meant a
    deleted zip released its number for reuse, and the next candidate
    would take the label of one somebody had already read about --
    which happened here, with a dossier for rc3 sitting beside no zip
    at all, so the next build would have been a second, different rc3.

    A number is spent the moment anything bearing it exists, and it
    stays spent. Reusing one is worse than skipping one: nobody is
    confused by a gap in the sequence, and everybody is confused by
    two candidates with the same name.
    """
    if not os.path.isdir(DIST):
        return 1
    version_pattern = re.escape(version)
    patterns = (
        rf"weavingspace_qgis-{version_pattern}rc(\d+)\.zip$",
        rf"CANDIDATE-{version_pattern}rc(\d+)\.md$",
        rf"CANDIDATE-{version_pattern}rc(\d+)\.receipt\.json$",
    )
    used = []
    for name in os.listdir(DIST):
        for pattern in patterns:
            found = re.search(pattern, name)
            if found:
                used.append(int(found.group(1)))
                break
    return max(used, default=0) + 1


def shipped_files():
    """Every file that goes into the plugin zip.

    Returns:
      A sorted list of (absolute path, name inside the archive). Sorted
      so the order is the same on every machine, which matters because
      release.py digests this list to prove a release is being cut
      from the same tree a candidate was reviewed on.

    One rule with two callers: write_zip packs exactly these, and the
    release's promotion check hashes exactly these. Two lists would
    drift, and a proof built on a drifting list proves nothing.

    LICENSE.md is included from the repository root and written INSIDE
    the plugin folder, because QGIS unpacks only that folder into a
    profile: without it the installed plugin carries MIT-licensed
    vendored code with no notice anywhere in it, and the MIT terms
    require the notice to travel with the software.
    """
    found = []
    for dirpath, dirnames, filenames in os.walk(SRC):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for fn in filenames:
            if fn == ".DS_Store" or fn.endswith(".pyc"):
                continue
            full = os.path.join(dirpath, fn)
            found.append((full, os.path.relpath(full, ROOT)))
    licence = os.path.join(ROOT, "LICENSE.md")
    if os.path.exists(licence):
        found.append(
            (licence, os.path.join(os.path.basename(SRC), "LICENSE.md")))
    return sorted(found, key=lambda pair: pair[1])


def write_zip(out, version_override=None):
    """Archive the plugin folder into `out`.

    Args:
      out: path of the zip to write.
      version_override: when given, the version written into
        metadata.txt INSIDE the archive. The file on disk is not
        touched: a candidate should announce itself as a candidate in
        QGIS's plugin manager, but the repository's declared version
        is a separate fact and editing it here would leave the working
        tree dirty in a way the release audit would rightly complain
        about.

    Returns:
      The path written.
    """
    os.makedirs(DIST, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for full, rel in shipped_files():
                if version_override and full == METADATA:
                    with open(full, encoding="utf-8") as handle:
                        text = handle.read()
                    text = re.sub(r"^version=.+$",
                                  f"version={version_override}",
                                  text, count=1, flags=re.MULTILINE)
                    zf.writestr(rel, text)
                    continue
                zf.write(full, rel)
    return out


def installed_copies():
    """Every QGIS profile that already has this plugin installed.

    Returns:
      A list of paths to weavingspace_qgis folders inside QGIS profile
      plugin directories, on this machine.

    Profiles that already carry the plugin are UPDATED; profiles that
    do not are left alone. Installing into a profile nobody asked
    about would put a plugin somewhere a user has to discover and
    remove, and a testing profile exists precisely so that what is in
    it is deliberate.
    """
    home = os.path.expanduser("~")
    roots = [
        os.path.join(home, "Library", "Application Support", "QGIS"),
        os.path.join(home, ".local", "share", "QGIS"),            # Linux
        os.path.join(os.environ.get("APPDATA", ""), "QGIS"),      # Windows
    ]
    found = []
    for root in roots:
        if not os.path.isdir(root):
            continue
        for dirpath, dirnames, _files in os.walk(root):
            if os.path.basename(dirpath) == "plugins":
                target = os.path.join(dirpath, "weavingspace_qgis")
                if os.path.isdir(target):
                    found.append(target)
                dirnames[:] = []          # no need to descend further
    return sorted(found)


def install_into(target, source_zip):
    """Replace one installed copy with the contents of a built zip.

    Args:
      target: an existing weavingspace_qgis folder in a QGIS profile.
      source_zip: the zip to install from.

    Returns:
      None.

    ``libs/`` is preserved. That folder holds wheels the dependency
    provisioner downloaded for THIS machine; it is deliberately absent
    from the zip, and deleting it would make the plugin re-download
    everything on next launch for no reason. Everything else is
    removed first, so a file dropped from the plugin does not linger
    in an installed copy and go on being imported.
    """
    for name in os.listdir(target):
        if name == "libs":
            continue
        path = os.path.join(target, name)
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
    with zipfile.ZipFile(source_zip) as zf:
        for member in zf.namelist():
            rel = os.path.relpath(member, "weavingspace_qgis")
            if rel.startswith(".."):
                continue
            destination = os.path.join(target, rel)
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            with zf.open(member) as src, open(destination, "wb") as dst:
                shutil.copyfileobj(src, dst)


def main():
    """Build the release zip, or a numbered release candidate.

    Returns:
      None. Writes into dist/ and, for a candidate, updates the
      copies already installed in QGIS profiles on this machine
      unless --no-install says otherwise.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--rc", action="store_true",
        help="build a numbered release candidate instead of the "
             "release zip, for hands-on testing before publishing")
    parser.add_argument(
        "--no-install", action="store_true",
        help="with --rc, do not update the copies already installed "
             "in QGIS profiles on this machine")
    args = parser.parse_args()

    if args.rc:
        version = declared_version()
        label = f"{version}rc{next_candidate(version)}"
        out = write_zip(
            os.path.join(DIST, f"weavingspace_qgis-{label}.zip"), label)
        size = os.path.getsize(out) / 1e6
        print(f"wrote {out} ({size:.1f} MB)")
        print(f"installs in QGIS as version {label}, so a tester can "
              f"tell it from the release")
        if not args.no_install:
            targets = installed_copies()
            for target in targets:
                install_into(target, out)
                print(f"  updated {target}")
            if targets:
                print("\nRestart QGIS, or use Plugin Reloader, before "
                      "trying it: Python modules already imported stay "
                      "imported.")
            else:
                print("\nNo existing installation found, so nothing was "
                      "updated. Install the zip once through Plugins > "
                      "Manage and Install Plugins... and later "
                      "candidates will land in place automatically.")
        return

    out = write_zip(os.path.join(DIST, "weavingspace_qgis.zip"))
    size = os.path.getsize(out) / 1e6
    print(f"wrote {out} ({size:.1f} MB)")


if __name__ == "__main__":
    main()
