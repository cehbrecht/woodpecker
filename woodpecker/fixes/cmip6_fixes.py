from __future__ import annotations

import xarray as xr

from .registry import Fix, FixRegistry


def _lower_source_name(dataset: xr.Dataset) -> str:
    return str(dataset.attrs.get("source_name", "")).lower()


@FixRegistry.register
class CMIP6D01(Fix):
    code = "CMIP6D01"
    name = "Decadal metadata baseline"
    description = "Fixes known CMIP6 decadal (CDS) metadata issues (baseline scaffolding)."
    categories = ["metadata"]
    priority = 10
    dataset = "CMIP6-decadal"

    def matches(self, dataset: xr.Dataset) -> bool:
        source = _lower_source_name(dataset)
        return source.endswith(".nc") and "cmip6" in source

    def check(self, dataset: xr.Dataset) -> list[str]:
        findings = []
        if "decadal" not in _lower_source_name(dataset):
            findings.append("expected CMIP6 decadal filename hint ('decadal') is missing")
        return findings

    def apply(self, dataset: xr.Dataset, dry_run: bool = True) -> bool:
        if "decadal" in _lower_source_name(dataset):
            return False

        if dry_run:
            return True
        dataset.attrs["woodpecker_fix_CMIP6D01"] = "applied"
        return True


@FixRegistry.register
class ATLAS01(Fix):
    code = "ATLAS01"
    name = "ATLAS encoding cleanup"
    description = "Fixes common ATLAS encoding/deflation issues (baseline scaffolding)."
    categories = ["encoding", "metadata"]
    priority = 20
    dataset = "ATLAS"

    def matches(self, dataset: xr.Dataset) -> bool:
        source = _lower_source_name(dataset)
        return source.endswith(".nc") and "atlas" in source

    def check(self, dataset: xr.Dataset) -> list[str]:
        findings = []
        source_name = str(dataset.attrs.get("source_name", ""))
        if source_name.lower().endswith(".nc") and " " in source_name:
            findings.append(
                "filename contains spaces; use underscores for stable downstream tooling"
            )
        return findings

    def apply(self, dataset: xr.Dataset, dry_run: bool = True) -> bool:
        source_name = str(dataset.attrs.get("source_name", ""))
        if " " not in source_name:
            return False

        if dry_run:
            return True
        dataset.attrs["woodpecker_fix_ATLAS01"] = "applied"
        return True
