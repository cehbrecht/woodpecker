from __future__ import annotations

import xarray as xr

from ..registry import Fix, FixRegistry
from .common import (
    apply_atlas_encoding_cleanup,
    lower_source_name,
    needs_compression_level_cleanup,
    needs_fillvalue_cleanup,
    needs_string_coord_encoding_cleanup,
)


@FixRegistry.register
class ATLAS01(Fix):
    code = "ATLAS01"
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
        if needs_fillvalue_cleanup(dataset):
            findings.append("encoding _FillValue cleanup is required for ATLAS coordinates/data vars")
        if needs_string_coord_encoding_cleanup(dataset):
            findings.append("ATLAS string coordinates still contain compression encoding options")
        if needs_compression_level_cleanup(dataset):
            findings.append("ATLAS data variable compression level should be normalized to 1")
        return findings

    def apply(self, dataset: xr.Dataset, dry_run: bool = True) -> bool:
        needs_change = any(
            (
                needs_fillvalue_cleanup(dataset),
                needs_string_coord_encoding_cleanup(dataset),
                needs_compression_level_cleanup(dataset),
            )
        )
        if not needs_change:
            return False

        if dry_run:
            return True

        return apply_atlas_encoding_cleanup(dataset)
