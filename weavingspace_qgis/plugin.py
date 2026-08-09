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

    names = ", ".join(missing)
    answer = QMessageBox.question(
      self.iface.mainWindow(), "WeavingSpace – one-time setup",
      "This QGIS installation is missing (or has outdated versions of) "
      f"Python components the plugin needs:\n\n    {names}\n\n"
      "WeavingSpace can download them from PyPI (python.org's package "
      "archive) into the plugin's own folder; nothing else in your QGIS "
      "installation is touched, and this happens only once.\n\n"
      "Download them now (about 20 to 60 MB)?",
      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    if answer != QMessageBox.StandardButton.Yes:
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
      QMessageBox.critical(
        self.iface.mainWindow(), "WeavingSpace",
        "Could not set up: " + ", ".join(still_missing) +
        "\n\nCheck your internet connection and try again, or install "
        "these packages into QGIS's Python yourself.")
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
