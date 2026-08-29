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
    return max(candidate_numbers(version), default=0) + 1


def candidate_numbers(version):
    """Every candidate number of one version present in dist/.

    Args:
      version: the declared version, e.g. "0.24.3".

    Returns:
      A list of integers, unsorted and possibly empty. One owner for
      what counts as an artefact and which version it belongs to, so
      the two callers below cannot drift apart about either.
    """
    if not os.path.isdir(DIST):
        return []
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
    return used + published_candidate_numbers(version)


def published_candidate_numbers(version):
    """Every candidate number of one version that a TAG already bears.

    Args:
      version: the declared version, e.g. "0.24.4".

    Returns:
      A list of integers from local git tags named `v<version>rc<N>`,
      or an empty list where git cannot be asked. Never raises: this
      is consulted in order to avoid reusing a name, and a check that
      explodes is worse than one that declines.

    WHY IT EXISTS. `dist/` is PER WORKTREE and a candidate's name is
    GLOBAL. On 2026-08-29 a candidate was built in a fresh worktree
    whose `dist/` held nothing, and was duly named `0.24.4rc1` --
    while `v0.24.4rc1` had been a published pre-release since the day
    before. One name, two trees, which is the exact harm the sibling
    above says it exists to prevent: "a number is spent the moment
    anything bearing it exists, and it stays spent." A tag is the most
    durable thing that can bear one, and it was the one store nobody
    asked.

    LOCAL TAGS ONLY, and the limit is stated rather than hidden: a tag
    that has never been fetched cannot be counted here, and this will
    not reach the network to find out. `release.py` fetches before it
    names a candidate and says so when it cannot, and
    `publish_candidate.py` refuses a tag that is already taken --
    which is the backstop that held while this was wrong.
    """
    try:
        import subprocess
        done = subprocess.run(
            ["git", "tag", "--list", f"v{version}rc*"],
            capture_output=True, text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)))
        if done.returncode != 0:
            return []
        pattern = rf"^v{re.escape(version)}rc(\d+)$"
        return [int(m.group(1)) for m in
                (re.match(pattern, line.strip())
                 for line in done.stdout.splitlines()) if m]
    except Exception:
        return []


def latest_candidate(version):
    """The highest candidate number this version has on disk.

    Args:
      version: the declared version, e.g. "0.24.3".

    Returns:
      An integer, or None when this version has no candidate at all.

    WHY IT EXISTS, and the bug belongs at the line. release.py named
    the candidate it had just built by sorting dist/ and taking the
    last entry -- TEXT order, in which `rc10` sits between `rc1` and
    `rc2`, so `rc9` came last. On 2026-08-19, the first two-digit
    candidate this project has ever built, the zip was written as
    0.24.3rc10 while its dossier and receipt were written as rc9,
    OVERWRITING the genuine rc9 artefacts and putting one name over
    two trees -- which is precisely what `next_candidate` above exists
    to prevent, arriving from the other end. That glob was not scoped
    to the version either, so a 0.25.0rc1 would have been named from a
    leftover 0.24.3 candidate.
    Numbers are numbers: compare them as numbers, and derive them
    once.
    """
    used = candidate_numbers(version)
    return max(used) if used else None


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
    parser.add_argument(
        "--candidate", type=int, metavar="N",
        help="build this candidate NUMBER rather than the next unused "
             "one. For a number spent by something this tree cannot "
             "see -- a candidate built in another worktree and never "
             "tagged, whose zip is gone. It only ever SKIPS: a number "
             "at or below one already spent is refused, because a gap "
             "confuses nobody and a reused name confuses everybody.")
    args = parser.parse_args()

    if args.rc:
        version = declared_version()
        # THE MAINTAINER MAY SKIP AHEAD AND MAY NOT GO BACK. What this
        # tree can see is `dist/` and the tags it has fetched; a
        # candidate built elsewhere and never tagged is invisible to
        # both, and on 2026-08-29 exactly that produced a second
        # `0.24.4rc1` beside a published one. So the number can be
        # said out loud -- and is still checked against everything
        # that IS visible, since the failure this guards against is
        # reuse rather than arithmetic.
        automatic = next_candidate(version)
        if args.candidate is None:
            number = automatic
        elif args.candidate < automatic:
            raise SystemExit(
                f"refusing to build {version}rc{args.candidate}: "
                f"{sorted(set(candidate_numbers(version)))} are already "
                f"spent by an artefact or a tag here, so the next free "
                f"number is {automatic}. A candidate number is spent by "
                f"anything bearing it, and it stays spent.")
        else:
            number = args.candidate
            if number > automatic:
                print(f"skipping to rc{number}: rc{automatic} would be "
                      f"next from what this tree can see, and you have "
                      f"said something else bears it")
        label = f"{version}rc{number}"
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
