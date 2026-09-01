"""Placeholders for optional plotting dependencies.

The QGIS plugin build of weavingspace does not require matplotlib: it
is used only by the notebook-oriented plotting helpers. When absent we
substitute a proxy that supports attribute access (so type annotations
such as ``plt.Axes`` still evaluate) but raises ImportError as soon as
anything is actually called.

Scipy was named here too until 2026-08-31. Upstream's only use of it
was one interpolating spline in ``Topology.zigzag_between_points``,
which their commit 2dbea80 replaced by sampling ``np.sin`` directly, so
the vendored library no longer imports scipy anywhere. The proxy stays
general rather than being renamed for matplotlib, since the next
optional dependency will want the same treatment.
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
      "matplotlib; the QGIS plugin does not use them.")
