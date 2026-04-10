from __future__ import annotations

import re

import xarray as xr

from ..registry import Fix, FixRegistry
from .helpers import is_cmip6_decadal_netcdf

_MALFORMED_URL_VARIANT_PATTERN = re.compile(r"(\.s\d{4})-(r\d+i\d+p\d+f\d+)")


def _normalized_further_info_url(url: str) -> str:
    return _MALFORMED_URL_VARIANT_PATTERN.sub(r"\1.\2", url)


def _needs_further_info_url_fix(dataset: xr.Dataset) -> bool:
    raw_url = dataset.attrs.get("further_info_url")
    if not isinstance(raw_url, str) or not raw_url:
        return False
    return _normalized_further_info_url(raw_url) != raw_url


def _apply_further_info_url_fix(dataset: xr.Dataset) -> bool:
    if not _needs_further_info_url_fix(dataset):
        return False
    dataset.attrs["further_info_url"] = _normalized_further_info_url(
        dataset.attrs["further_info_url"]
    )
    return True


@FixRegistry.register
class CMIP6D_0008(Fix):
    code = "CMIP6D_0008"
    name = "Decadal further_info_url normalization"
    description = (
        "Normalizes malformed CMIP6-decadal further_info_url variant separators from '-' to '.'."
    )
    categories = ["metadata"]
    priority = 17
    dataset = "CMIP6-decadal"

    def matches(self, dataset: xr.Dataset) -> bool:
        return is_cmip6_decadal_netcdf(dataset)

    def check(self, dataset: xr.Dataset) -> list[str]:
        if not is_cmip6_decadal_netcdf(dataset):
            return []
        if _needs_further_info_url_fix(dataset):
            return ["further_info_url should use '.' before ripf variant token"]
        return []

    def apply(self, dataset: xr.Dataset, dry_run: bool = True) -> bool:
        if not is_cmip6_decadal_netcdf(dataset):
            return False
        if not _needs_further_info_url_fix(dataset):
            return False
        if dry_run:
            return True
        return _apply_further_info_url_fix(dataset)
