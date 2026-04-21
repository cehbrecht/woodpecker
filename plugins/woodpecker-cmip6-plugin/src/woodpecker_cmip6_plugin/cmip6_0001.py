from __future__ import annotations

import xarray as xr

from woodpecker.fixes.registry import Fix, FixRegistry


def _is_cmip6_non_decadal(dataset: xr.Dataset) -> bool:
    source = str(dataset.attrs.get("source_name", "")).lower()
    return source.endswith(".nc") and "cmip6" in source and "decadal" not in source


@FixRegistry.register
class Cmip6DummyPlaceholderFix(Fix):
    local_id = "0001"
    name = "CMIP6 dummy placeholder"
    description = "Dummy placeholder for future non-decadal CMIP6 fixes."
    categories = ["metadata"]
    priority = 40
    dataset = "cmip6"

    def matches(self, dataset: xr.Dataset) -> bool:
        return _is_cmip6_non_decadal(dataset)

    def check(self, dataset: xr.Dataset) -> list[str]:
        if _is_cmip6_non_decadal(dataset):
            config = getattr(self, "config", {}) or {}
            message = config.get("message", "dummy CMIP6 placeholder fix candidate")
            return [str(message)]
        return []

    def apply(self, dataset: xr.Dataset, dry_run: bool = True) -> bool:
        if not _is_cmip6_non_decadal(dataset):
            return False
        if dry_run:
            return True
        config = getattr(self, "config", {}) or {}
        marker_attr = str(config.get("marker_attr", "woodpecker_fix_cmip6_0001"))
        marker_value = str(config.get("marker_value", "applied"))
        dataset.attrs[marker_attr] = marker_value
        return True
