from __future__ import annotations

from importlib import metadata
import warnings
from typing import Any, Iterable

ENTRYPOINT_GROUP = "woodpecker.plugins"
_PLUGINS_LOADED = False


def _iter_plugin_entry_points() -> Iterable[Any]:
    """Return entry points for external woodpecker plugins."""
    entries = metadata.entry_points()
    if hasattr(entries, "select"):
        return entries.select(group=ENTRYPOINT_GROUP)
    return entries.get(ENTRYPOINT_GROUP, [])


def load_plugins() -> None:
    """Load external plugins once.

    Each entry point may reference either:
    - a module (import side effects register fixes), or
    - a callable loader function (called after load).
    """
    global _PLUGINS_LOADED
    if _PLUGINS_LOADED:
        return

    _PLUGINS_LOADED = True
    for entry in _iter_plugin_entry_points():
        try:
            loaded = entry.load()
            if callable(loaded):
                loaded()
        except Exception as exc:
            warnings.warn(
                f"Failed to load woodpecker plugin '{getattr(entry, 'name', '<unknown>')}': {exc}",
                RuntimeWarning,
                stacklevel=2,
            )
