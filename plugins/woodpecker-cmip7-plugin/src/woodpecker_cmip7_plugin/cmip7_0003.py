from __future__ import annotations

from typing import Any

import xarray as xr

from woodpecker.fixes.registry import Fix, register_fix


def _config_map(config: dict[str, Any], key: str) -> dict[str, str]:
    raw = config.get(key, {})
    if not isinstance(raw, dict):
        return {}
    out: dict[str, str] = {}
    for src, dst in raw.items():
        src_name = str(src).strip()
        dst_name = str(dst).strip()
        if src_name and dst_name and src_name != dst_name:
            out[src_name] = dst_name
    return out


def _needs_variable_renames(dataset: xr.Dataset, variable_map: dict[str, str]) -> bool:
    for src, dst in variable_map.items():
        if src in dataset.data_vars and dst not in dataset.data_vars:
            return True
    return False


def _needs_attr_update(dataset: xr.Dataset, attr_name: str, value: str | None) -> bool:
    if not value:
        return False
    return str(dataset.attrs.get(attr_name, "")) != value


def _apply_variable_renames(dataset: xr.Dataset, variable_map: dict[str, str]) -> bool:
    changed = False
    for src, dst in variable_map.items():
        if src not in dataset.data_vars or dst in dataset.data_vars:
            continue
        dataset[dst] = dataset[src]
        del dataset[src]
        changed = True
    return changed


def _apply_dim_renames(dataset: xr.Dataset, dim_map: dict[str, str]) -> bool:
    changed = False
    for src, dst in dim_map.items():
        if src not in dataset.dims or dst in dataset.dims:
            continue

        for name in list(dataset.data_vars):
            if src in dataset[name].dims:
                dataset[name] = dataset[name].rename({src: dst})
                changed = True

        for name in list(dataset.coords):
            if src in dataset[name].dims:
                dataset.coords[name] = dataset.coords[name].rename({src: dst})
                changed = True

        if src in dataset.coords and dst not in dataset.coords:
            dataset.coords[dst] = dataset.coords[src]
            del dataset.coords[src]
            changed = True
    return changed


@register_fix
class ConfigurableCmip7ReformatBridgeFix(Fix):
    local_id = "0003"
    name = "Configurable CMIP7 reformat bridge (plugin)"
    description = (
        "Applies workflow-driven variable/dimension remapping and selected metadata updates."
    )
    categories = ["structure", "metadata"]
    priority = 43
    dataset = "CMIP7"

    def _config(self) -> dict[str, Any]:
        return getattr(self, "config", {}) or {}

    def matches(self, dataset: xr.Dataset) -> bool:
        config = self._config()
        variable_map = _config_map(config, "variable_map")
        dim_map = _config_map(config, "dim_map")
        realm = str(config.get("realm", "")).strip() or None
        branded_variable = str(config.get("branded_variable", "")).strip() or None
        keep_global_attrs = bool(config.get("keep_global_attrs", False))

        if _needs_variable_renames(dataset, variable_map):
            return True
        if _needs_attr_update(dataset, "realm", realm):
            return True
        if _needs_attr_update(dataset, "branded_variable", branded_variable):
            return True
        if not keep_global_attrs and bool(dataset.attrs):
            return True
        if any(src in dataset.dims and dst not in dataset.dims for src, dst in dim_map.items()):
            return True
        return False

    def check(self, dataset: xr.Dataset) -> list[str]:
        if not self.matches(dataset):
            return []
        return ["dataset can be reformatted using workflow parameters"]

    def apply(self, dataset: xr.Dataset, dry_run: bool = True) -> bool:
        if not self.matches(dataset):
            return False
        if dry_run:
            return True

        config = self._config()
        variable_map = _config_map(config, "variable_map")
        dim_map = _config_map(config, "dim_map")
        realm = str(config.get("realm", "")).strip() or None
        branded_variable = str(config.get("branded_variable", "")).strip() or None
        keep_global_attrs = bool(config.get("keep_global_attrs", False))

        changed = False
        if not keep_global_attrs and bool(dataset.attrs):
            dataset.attrs.clear()
            changed = True
        if _apply_variable_renames(dataset, variable_map):
            changed = True
        if _apply_dim_renames(dataset, dim_map):
            changed = True

        if realm and str(dataset.attrs.get("realm", "")) != realm:
            dataset.attrs["realm"] = realm
            changed = True
        if branded_variable and str(dataset.attrs.get("branded_variable", "")) != branded_variable:
            dataset.attrs["branded_variable"] = branded_variable
            changed = True

        return changed
