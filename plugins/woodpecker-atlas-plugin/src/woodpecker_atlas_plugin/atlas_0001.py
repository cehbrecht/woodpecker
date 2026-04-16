from __future__ import annotations

import xarray as xr

from woodpecker.fixes.common.helpers import (
    lower_source_name,
    normalize_compression_settings,
    vars_with_compression_above_level,
    vars_with_encoding_key,
)
from woodpecker.fixes.registry import Fix, FixRegistry


def _atlas_vars_to_check(dataset: xr.Dataset) -> list[str]:
    return list(dataset.coords) + list(dataset.data_vars)


def _needs_fillvalue_cleanup(dataset: xr.Dataset) -> bool:
    for var in _atlas_vars_to_check(dataset):
        if dataset[var].encoding.get("_FillValue", "__missing__") is not None:
            return True
    return False


def _needs_string_coord_encoding_cleanup(dataset: xr.Dataset) -> bool:
    coord_vars = (
        "member_id",
        "gcm_variant",
        "gcm_model",
        "gcm_institution",
        "rcm_variant",
        "rcm_model",
        "rcm_institution",
    )
    for var in coord_vars:
        if var not in dataset:
            continue
        enc = dataset[var].encoding
        if any(opt in enc for opt in ("zlib", "shuffle", "complevel")):
            return True
    return False


def _needs_compression_level_cleanup(dataset: xr.Dataset) -> bool:
    return bool(vars_with_compression_above_level(dataset, list(dataset.data_vars), max_level=1))


def _apply_atlas_encoding_cleanup(dataset: xr.Dataset) -> bool:
    changed = False

    for var in _atlas_vars_to_check(dataset):
        if dataset[var].encoding.get("_FillValue", "__missing__") is not None:
            dataset[var].encoding["_FillValue"] = None
            changed = True

    coord_candidates = (
        "member_id",
        "gcm_variant",
        "gcm_model",
        "gcm_institution",
        "rcm_variant",
        "rcm_model",
        "rcm_institution",
    )

    for en in ("zlib", "shuffle", "complevel"):
        cvars_to_fix = vars_with_encoding_key(dataset, coord_candidates, en)
        for cvar in cvars_to_fix:
            del dataset[cvar].encoding[en]
            changed = True

    vars_to_fix = vars_with_compression_above_level(dataset, list(dataset.data_vars), max_level=1)
    if normalize_compression_settings(dataset, vars_to_fix, level=1, zlib=True, shuffle=True):
        changed = True

    return changed


@FixRegistry.register
class ATLAS_0001(Fix):
    code = "ATLAS_0001"
    name = "ATLAS encoding cleanup"
    description = "Applies rook-equivalent ATLAS deflation/encoding cleanup."
    categories = ["encoding"]
    priority = 20
    dataset = "ATLAS"

    def matches(self, dataset: xr.Dataset) -> bool:
        source = lower_source_name(dataset)
        return source.endswith(".nc") and "atlas" in source

    def check(self, dataset: xr.Dataset) -> list[str]:
        findings = []
        if _needs_fillvalue_cleanup(dataset):
            findings.append(
                "encoding _FillValue cleanup is required for ATLAS coordinates/data vars"
            )
        if _needs_string_coord_encoding_cleanup(dataset):
            findings.append("ATLAS string coordinates still contain compression encoding options")
        if _needs_compression_level_cleanup(dataset):
            findings.append("ATLAS data variable compression level should be normalized to 1")
        return findings

    def apply(self, dataset: xr.Dataset, dry_run: bool = True) -> bool:
        needs_change = any(
            (
                _needs_fillvalue_cleanup(dataset),
                _needs_string_coord_encoding_cleanup(dataset),
                _needs_compression_level_cleanup(dataset),
            )
        )
        if not needs_change:
            return False

        if dry_run:
            return True

        return _apply_atlas_encoding_cleanup(dataset)
