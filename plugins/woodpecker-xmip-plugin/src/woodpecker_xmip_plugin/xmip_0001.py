from __future__ import annotations

import xarray as xr

from woodpecker.fixes.registry import Fix, register_fix

from .helpers import (
    dataset_changed,
    finding_messages,
    is_cmip6_dataset,
    overwrite_dataset_in_place,
    xmip_cmip6_preprocessing,
)


@register_fix
class XmipCmip6PreprocessingFix(Fix):
    suffix = "cmip6_preprocessing"
    aliases = ["xmip.combined_preprocessing"]
    links = [
        {
            "label": "xMIP combined_preprocessing",
            "url": "https://github.com/jbusecke/xMIP",
        }
    ]
    name = "xMIP CMIP6 preprocessing"
    description = (
        "Applies xMIP-derived CMIP6 structural and metadata preprocessing suitable for "
        "analysis-ready Woodpecker datasets."
    )
    categories = ["structure", "metadata"]
    priority = 42
    dataset = "CMIP6"

    def matches(self, dataset: xr.Dataset) -> bool:
        if not is_cmip6_dataset(dataset):
            return False
        processed = xmip_cmip6_preprocessing(dataset)
        return dataset_changed(dataset, processed)

    def check(self, dataset: xr.Dataset) -> list[str]:
        if not is_cmip6_dataset(dataset):
            return []
        processed = xmip_cmip6_preprocessing(dataset)
        return finding_messages(dataset, processed)

    def apply(self, dataset: xr.Dataset, dry_run: bool = True) -> bool:
        if not is_cmip6_dataset(dataset):
            return False

        processed = xmip_cmip6_preprocessing(dataset)
        if not dataset_changed(dataset, processed):
            return False

        if dry_run:
            return True

        overwrite_dataset_in_place(dataset, processed)
        return True
