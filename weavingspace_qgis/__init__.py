"""WeavingSpace QGIS plugin package.

QGIS discovers a plugin by importing its package and calling
``classFactory(iface)``, which must return an object with ``initGui``
and ``unload`` methods (see plugin.py). ``iface`` is the running QGIS
application's plugin interface. Path setup happens first so the
vendored weavingspace library (and any provisioned dependencies in
libs/) are importable before anything else loads.
"""


def classFactory(iface):  # noqa: N802 (QGIS API)
  """QGIS's entry point: build and return the plugin object."""
  from . import deps
  deps.add_paths()
  from .plugin import WeavingSpacePlugin
  return WeavingSpacePlugin(iface)
