#!/usr/bin/env python3
"""Install the scientific stack a container's QGIS lacks, for CI only.

Run under the QGIS Python of a machine that is about to run the
suite:

    python3 tools/ci_provision.py

WHY THIS EXISTS. The official `qgis/qgis` images ship QGIS and its own
Python and nothing else: geopandas, shapely, pandas and networkx are
all absent. The suite imports them directly, so on 2026-08-11 the
first Linux CI run reported seventy failures of which sixty-nine said
`ModuleNotFoundError: No module named 'geopandas'` -- one cause
wearing seventy costumes, and enough noise to hide whatever real
platform differences were underneath it.

WHAT IT DELIBERATELY IS NOT. It is not a way for the plugin to install
things without asking. The plugin's own provisioning is gated by
`plugin.dependency_consent_box`, which names the packages, the source
and the exact destination folder and waits for a click, and that
remains the ONLY route from shipped code to PyPI -- a QGIS plugin
repository reviewer will look at precisely this, and rightly. What
makes the difference is where this file lives: `tools/` is not in
`build.shipped_files()`, so nothing here reaches a user's machine, and
the plugin gains no flag, environment variable or code path that could
skip the dialogue. A maintainer running a program that installs
packages is consent; software installing them unasked is not.
`test_pypi_provisioning_is_reached_only_through_consent` holds that
line so it cannot be crossed absent-mindedly.

It calls the plugin's own `deps` module rather than pip, which is the
second reason to run it: the wheel-tag matching, the numpy 1.x floor
and the pyproj data redirection are all plugin code that no test can
exercise on a Mac whose QGIS already carries every package. On Linux
CI it runs for real, and a fault in it fails here.

Exit status: 0 when nothing is missing afterwards, 1 when something
still is, naming it.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from weavingspace_qgis import deps      # noqa: E402


def main():
  """Provision whatever this QGIS lacks, and report what happened.

  Returns:
    None. Exits 1 if any required package is still missing after the
    attempt, so a CI step fails at the cause rather than letting the
    suite fail seventy times at the symptom.
  """
  missing = deps.missing_packages()
  if not missing:
    print("nothing to provision: this QGIS already carries "
          "everything the plugin needs")
    return
  print(f"missing from this QGIS: {', '.join(missing)}")

  # The bundled-wheel path first, exactly as plugin.py orders it, so
  # CI exercises the same sequence a user's machine would take.
  missing = deps.provision_from_bundled(missing)
  if missing:
    still = deps.provision_from_pypi(missing, progress=lambda m: print(
      f"  {m}", flush=True))
    if still:
      sys.exit(f"STILL MISSING after provisioning: {', '.join(still)}. "
               f"The suite cannot run. This is a fault in deps.py or in "
               f"the runner's network, not in the tests.")
  deps.ensure_pyproj_data()

  # Ask again rather than trusting the return value: the question that
  # matters is whether an import works now, and provisioning reports
  # only what it downloaded.
  left = deps.missing_packages()
  if left:
    sys.exit(f"provisioning claimed success but {', '.join(left)} is "
             f"still missing or below its version floor")
  print(f"provisioned into {deps.LIBS_DIR}; every requirement is now met")


if __name__ == "__main__":
  main()
