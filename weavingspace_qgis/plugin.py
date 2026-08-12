"""QGIS plugin hooks for WeavingSpace.

QGIS drives a plugin through two calls: ``initGui`` when the plugin is
enabled (add menu entries/toolbar buttons here) and ``unload`` when it
is disabled (remove them again; forgetting leaves dead buttons behind).
Everything between those is up to the plugin. This class also owns the
one-time dependency check: the heavy imports (geopandas and friends)
happen only when the user first opens the dialog, so a machine missing
them still starts QGIS cleanly and gets a helpful offer instead of an
ImportError.
"""

from __future__ import annotations

import os

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMessageBox, QProgressDialog

from . import deps

PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))


def dependency_consent_box(parent, missing):
  """Build the dialogue that asks to download the missing packages.

  Args:
    parent: the window to centre on; None is accepted, which is what
      a test passes.
    missing: import names of the packages that are absent or too old,
      in the order deps.py found them.

  Returns:
    (box, approve_button). The caller shows the box and compares
    ``box.clickedButton()`` with the button returned; anything else,
    including closing the window, means no.

  Built here rather than inline in the caller so it can be read
  without owning a QGIS that happens to be missing a package: a test
  asserts what it says, and the release screenshots it.

  On the wording. This asks permission to download and unpack code,
  which is the most intrusive thing this plugin ever does and the one
  a reviewer of the QGIS plugin repository will look at hardest. So
  it states what can be checked rather than asking to be trusted:
  what arrives, from where, exactly where it lands, what is left
  alone, how to undo it, and what declining costs. The shape serves
  two readers at once -- a plain first paragraph for somebody who
  wants the gist and a button, then short specific lines for somebody
  who wants to verify. Neither has to read the other's half.

  The buttons say what they do. "Yes" and "No" do not tell a reader
  that No closes the plugin, and the safe answer is the default so
  that a stray Return cannot start a download nobody read about.
  """
  from qgis.PyQt.QtWidgets import QMessageBox as _Box
  names = ", ".join(missing)
  box = _Box(parent)
  box.setWindowTitle("WeavingSpace needs a few Python components")
  box.setIcon(_Box.Icon.Question)
  box.setText(
    "WeavingSpace draws its maps with three well-known Python libraries. This "
    "QGIS installation either does not have them or has versions too old to "
    "use, so they have to be fetched before the plugin can open.")
  box.setInformativeText(
    f"Missing or too old:  {names}\n"
    "\n"
    "If you approve, WeavingSpace will:\n"
    "  \u2022 download those packages from PyPI, the standard Python "
    "package archive at pypi.org, about 20 to 60 MB;\n"
    "  \u2022 unpack them into a folder belonging to this plugin:\n"
    f"      {deps.LIBS_DIR}\n"
    "  \u2022 use them from there, and only when QGIS's own copy is "
    "missing or too old.\n"
    "\n"
    "It will NOT: install anything into QGIS or your operating "
    "system, run an installer or package manager, change any other "
    "plugin, or send anything about you anywhere.\n"
    "\n"
    "This happens once. To undo it later, delete that folder, or "
    "uninstall the plugin in the usual way.\n"
    "\n"
    "If you cancel, nothing is downloaded and WeavingSpace closes: "
    "it cannot draw maps without these packages.")
  approve = box.addButton("Download and open WeavingSpace",
                          _Box.ButtonRole.AcceptRole)
  box.addButton("Cancel and close", _Box.ButtonRole.RejectRole)
  box.setDefaultButton(box.buttons()[-1])
  return box, approve


class WeavingSpacePlugin:
  """The object QGIS holds for the plugin's lifetime; owns the toolbar
  action and the (single, reused) dialog."""

  def __init__(self, iface):
    self.iface = iface
    self.action = None
    self.dialog = None

  def initGui(self):  # noqa: N802 (QGIS API)
    """Called by QGIS on enable: install the menu entry and toolbar
    button (a QAction is one user command that can appear in both)."""
    icon_path = os.path.join(PLUGIN_DIR, "icon.png")
    self.action = QAction(
      QIcon(icon_path), "WeavingSpace tiled maps...",
      self.iface.mainWindow())
    self.action.setToolTip(
      "Create tiled and woven multivariate maps")
    self.action.triggered.connect(self.open_dialog)
    self.iface.addPluginToMenu("&WeavingSpace", self.action)
    self.iface.addToolBarIcon(self.action)

  def unload(self):
    """Called by QGIS on disable/uninstall: remove our UI hooks and
    close the dialog so nothing of the plugin lingers."""
    if self.action is not None:
      self.iface.removePluginMenu("&WeavingSpace", self.action)
      self.iface.removeToolBarIcon(self.action)
      self.action = None
    if self.dialog is not None:
      self.dialog.close()
      self.dialog = None

  # ------------------------------------------------------------------ deps

  def _ensure_dependencies(self) -> bool:
    """Make sure the scientific stack is importable, provisioning it if
    needed; returns False (and explains) when the plugin cannot run.

    Order of attempts mirrors deps.py: packages already adequate ->
    done; wheels bundled in the plugin -> extract silently; otherwise
    ask consent and download from PyPI with a progress dialog
    (processEvents keeps that dialog painting during the synchronous
    downloads). pyproj gets pointed at its own PROJ data afterwards
    because QGIS's environment variables would otherwise steer a
    wheel-installed pyproj at QGIS's incompatible proj.db.
    """
    deps.add_paths()
    missing = deps.missing_packages()
    if not missing:
      deps.ensure_pyproj_data()
      return True

    missing = deps.provision_from_bundled(missing)
    if not missing:
      deps.ensure_pyproj_data()
      return True

    box, approve = dependency_consent_box(
      self.iface.mainWindow(), missing)
    box.exec()
    if box.clickedButton() is not approve:
      return False

    progress = QProgressDialog(
      "Downloading components...", None, 0, 0, self.iface.mainWindow())
    progress.setWindowTitle("WeavingSpace setup")
    progress.setMinimumDuration(0)
    progress.show()

    from qgis.PyQt.QtWidgets import QApplication

    def report(msg):
      progress.setLabelText(msg)
      QApplication.processEvents()

    try:
      still_missing = deps.provision_from_pypi(missing, progress=report)
    finally:
      progress.close()

    if still_missing:
      # The REASON, not just the names. deps.LAST_FAILURES holds one
      # line per package saying which of the four things went wrong --
      # PyPI unreachable, no wheel for this Python, the download or
      # unpack failing, no candidate versions left -- and those need
      # completely different responses from the person reading this.
      # Without it the message could only say "something is missing",
      # which is the state 0.24.1 was written to end.
      #
      # It reached tools/ci_provision.py and stopped there for a
      # while: the maintainer's tool printed the reason and the
      # user's dialogue did not, so the release notes promised
      # something no user could see. Found 2026-08-12 by the
      # documentation audit, from a comment claiming this code read
      # LAST_FAILURES when it did not.
      why = [f"{name}: {deps.LAST_FAILURES[name]}"
             for name in still_missing if name in deps.LAST_FAILURES]
      detail = ("\n\n" + "\n".join(why)) if why else ""
      QMessageBox.critical(
        self.iface.mainWindow(), "WeavingSpace",
        "Could not set up: " + ", ".join(still_missing) + detail +
        "\n\nYou can try again, or install these packages into "
        "QGIS's Python yourself.")
      return False
    deps.ensure_pyproj_data()
    return True

  # ---------------------------------------------------------------- dialog

  def open_dialog(self):
    """Toolbar/menu handler: check dependencies, import the library
    (failing loudly here rather than mysteriously later), then create
    the dialog once and re-show it on subsequent clicks (show/raise_/
    activateWindow is the Qt idiom for bringing a window forward)."""
    if not self._ensure_dependencies():
      return
    try:
      import weavingspace  # noqa: F401 - fail fast with a clear message
    except Exception as e:  # noqa: BLE001
      QMessageBox.critical(
        self.iface.mainWindow(), "WeavingSpace",
        f"The weavingspace library failed to load:\n{e}")
      return
    if self.dialog is None:
      from .dialog import WeavingSpaceDialog
      self.dialog = WeavingSpaceDialog(self.iface, self.iface.mainWindow())
    self.dialog.show()
    self.dialog.raise_()
    self.dialog.activateWindow()
