#!/usr/bin/env python3
"""Install the built zip into a QGIS profile and load the plugin from it.

    <qgis python> tools/install_and_load.py
    <qgis python> tools/install_and_load.py <path to a zip>

WHY THIS EXISTS, and why it is not covered by anything else. The suite
imports the plugin from the CHECKOUT. The release builds a zip and
never opens it. So the first thing every user does -- unpack the zip
into a QGIS profile and let QGIS call classFactory -- was the one
thing neither machine tested, and it is exactly the path a plugin
repository reviewer looks at: an archive whose shape is wrong, a file
that the packing rule forgot, or an import that only worked because
the repository happened to be on sys.path would all reach a user
before they reached us.

What it does, in the order QGIS does it:

  unpack the archive into a profile's python/plugins directory,
    which is where QGIS's plugin manager puts it, and assert the
    shape the repository requires -- ONE top-level folder carrying
    __init__.py and metadata.txt;
  put that directory on sys.path and import the plugin package BY
    NAME, as QGIS does, rather than by path;
  read metadata.txt the way the plugin manager reads it, and check
    the fields it refuses to install without;
  call classFactory with a stub iface, which is what QGIS calls, and
    require a plugin object with initGui and unload;
  call initGui and unload, because a plugin that cannot be removed
    cleanly leaves a QGIS session broken.

It does NOT open the dialog: that is the suite's work, and doing it
here would duplicate the whole functional suite to no purpose. The
question here is narrower and nobody else asks it -- does the
ARTEFACT load?

Exit status: 0 when the plugin installed, imported, built and
unloaded; non-zero with an explanation otherwise.
"""
import os
import sys
import tempfile
import zipfile


def unpack(archive, profile):
  """Unpack the zip where QGIS's plugin manager would put it.

  Args:
    archive: path to the built zip.
    profile: a directory standing in for a QGIS profile.

  Returns:
    The plugins directory the package now sits in, so the caller can
    put it on sys.path exactly as QGIS does.

  Raises:
    SystemExit: when the archive has a shape QGIS would refuse --
      more than one top-level entry, or a folder missing __init__.py
      or metadata.txt. Those are the plugin repository's own rules,
      and an archive that breaks them installs into nothing.
  """
  plugins = os.path.join(profile, "python", "plugins")
  os.makedirs(plugins, exist_ok=True)
  with zipfile.ZipFile(archive) as bundle:
    tops = {name.split("/")[0] for name in bundle.namelist()}
    if len(tops) != 1:
      sys.exit(f"the archive has {len(tops)} top-level entries "
               f"({sorted(tops)}); QGIS requires exactly one folder")
    bundle.extractall(plugins)
  folder = os.path.join(plugins, tops.pop())
  for required in ("__init__.py", "metadata.txt"):
    if not os.path.exists(os.path.join(folder, required)):
      sys.exit(f"the installed folder has no {required}; QGIS's "
               f"plugin manager would refuse it")
  return plugins, os.path.basename(folder)


def read_metadata(folder):
  """metadata.txt as the plugin manager reads it: a flat key=value map.

  Args:
    folder: the installed plugin folder.

  Returns:
    A dict of the fields. Continuation lines (the changelog) are
    ignored, which is what a reader of single fields does.
  """
  fields = {}
  with open(os.path.join(folder, "metadata.txt"), encoding="utf-8") as f:
    for line in f:
      if "=" in line and not line.startswith(" "):
        key, _, value = line.partition("=")
        fields[key.strip()] = value.strip()
  return fields


class _Iface:
  """The smallest QGIS interface classFactory and initGui can accept.

  QGIS hands the plugin a QgisInterface; the plugin only asks it for
  a main window, menus and a toolbar during construction and
  initGui. Standing in for it here keeps this a test of the ARTEFACT
  rather than a second QGIS session.
  """

  def __init__(self):
    """Build the widgets initGui will attach things to."""
    from qgis.PyQt.QtWidgets import QMainWindow
    self._window = QMainWindow()
    self._toolbar = self._window.addToolBar("WeavingSpace")
    self._menu = []
    self._icons = []

  def mainWindow(self):
    """The window a dialog would be parented to."""
    return self._window

  def addToolBarIcon(self, action):
    """Record the toolbar action the way QGIS would."""
    self._toolbar.addAction(action)
    self._icons.append(action)

  def removeToolBarIcon(self, action):
    """Remove it again, which unload must do."""
    self._toolbar.removeAction(action)
    if action in self._icons:
      self._icons.remove(action)

  def addPluginToMenu(self, menu, action):
    """Record a menu entry the way QGIS's Plugins menu would.

    Args:
      menu: the submenu name the plugin asks for, e.g. "&WeavingSpace".
      action: the QAction it wants placed there.

    Returns:
      None; the pair is kept so unload can be checked for having
      taken it away again.
    """
    self._menu.append((menu, action))

  def removePluginMenu(self, menu, action):
    """Take a menu entry away again, which is half of what unload is.

    Args:
      menu: the submenu name given to addPluginToMenu.
      action: the QAction to remove.

    Returns:
      None. A pair that was never added is ignored rather than
      raising: QGIS tolerates that, and a stub that is stricter than
      the thing it stands in for invents failures.
    """
    if (menu, action) in self._menu:
      self._menu.remove((menu, action))

  def messageBar(self):
    """The plugin reports through this; a stub is enough."""
    return self

  def pushMessage(self, *args, **kwargs):
    """Swallow a message rather than needing a real bar."""


def main():
  """Install, import, construct, initialise and unload. Report each step.

  Returns:
    None. Exits non-zero on the first step that fails, naming it,
    because a later step's failure would be a consequence rather
    than a finding.
  """
  # THE PATH IS OPTIONAL, AND ASKING build.py IS THE DEFAULT. Every
  # artefact carries its version in its name (maintainer's rule,
  # 2026-08-29), so the zip is no longer at a fixed path -- and the
  # alternative to this was teaching three platforms' shells to
  # compose the same name, including a cmd `for /f` loop on Windows.
  # One owner for what a build is called, asked rather than repeated,
  # which is the rule this repository already applies to
  # `shipped_files` and to candidate numbering.
  if len(sys.argv) >= 2:
    archive = sys.argv[1]
  else:
    import importlib.util
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    spec = importlib.util.spec_from_file_location(
      "build_rules", os.path.join(root, "build.py"))
    build = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build)
    archive = build.release_zip_path()
  if not os.path.exists(archive):
    sys.exit(f"no archive at {archive}; build it with build.py first")

  from qgis.core import QgsApplication
  QgsApplication.setPrefixPath(
    os.environ.get("QGIS_PREFIX_PATH", "/usr"), True)
  app = QgsApplication([], True)
  app.initQgis()

  profile = tempfile.mkdtemp(prefix="ws-profile-")
  print(f"STEP unpacking {os.path.basename(archive)}", flush=True)
  plugins, package = unpack(archive, profile)
  print(f"  installed as {package}", flush=True)

  print("STEP reading metadata the way the plugin manager does",
        flush=True)
  fields = read_metadata(os.path.join(plugins, package))
  for required in ("name", "qgisMinimumVersion", "description",
                   "version", "author", "email"):
    if not fields.get(required):
      sys.exit(f"metadata.txt has no {required}; the plugin "
               f"repository refuses an upload without it")
  print(f"  {fields['name']} {fields['version']}, "
        f"needs QGIS >= {fields['qgisMinimumVersion']}", flush=True)

  # BY NAME and from the profile, as QGIS does. Importing by path
  # would prove only that the files exist; this proves the package
  # resolves as an installed plugin, with nothing from the checkout
  # on the path to help it.
  print("STEP importing the installed package", flush=True)
  sys.path.insert(0, plugins)
  for name in [n for n in sys.modules if n.startswith(package)]:
    del sys.modules[name]
  module = __import__(package)
  where = os.path.dirname(os.path.abspath(module.__file__))
  if not where.startswith(plugins):
    sys.exit(f"the import resolved to {where}, not the installed "
             f"copy under {plugins}: this proved nothing about the zip")

  print("STEP classFactory, as QGIS calls it", flush=True)
  plugin = module.classFactory(_Iface())
  for method in ("initGui", "unload"):
    if not callable(getattr(plugin, method, None)):
      sys.exit(f"the plugin object has no {method}(); QGIS calls it")

  print("STEP initGui", flush=True)
  plugin.initGui()
  print("STEP unload", flush=True)
  iface = plugin.iface if hasattr(plugin, "iface") else None
  plugin.unload()
  # unload must leave the session as it found it. A plugin that
  # cannot be removed cleanly leaves a menu entry pointing at code
  # QGIS has dropped, which is a crash the next time it is clicked.
  if iface is not None and (iface._menu or iface._icons):
    sys.exit(f"unload left {len(iface._menu)} menu entr(ies) and "
             f"{len(iface._icons)} toolbar icon(s) behind; QGIS would "
             f"keep showing them after the plugin was removed")

  print(f"INSTALLED AND LOADED: {fields['name']} {fields['version']} "
        f"unpacked into a profile, imported by name, built, "
        f"initialised and unloaded", flush=True)
  sys.stdout.flush()
  app.exitQgis()
  # os._exit: Qt and QGIS tear down C++ objects at interpreter exit
  # and that teardown has segfaulted in containers, which would turn
  # a passing check into a signal and lose this line.
  os._exit(0)


if __name__ == "__main__":
  main()
