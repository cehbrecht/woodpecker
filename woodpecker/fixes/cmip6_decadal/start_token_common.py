from __future__ import annotations

import re

import xarray as xr


_START_YEAR_PATTERN = re.compile(r"s(\d{4})(?:[^\d]|$)")

_METADATA_SOURCES = (
    "sub_experiment_id",
    "startdate",
    "source_name",
    "further_info_url",
)


def extract_start_year(dataset: xr.Dataset) -> int | None:
    """Return the hindcast start year extracted from CMIP6-decadal metadata tokens.

    Scans ``sub_experiment_id``, ``startdate``, ``source_name``, and
    ``further_info_url`` in that order and returns the four-digit year from the
    first matching ``sYYYY`` token, or *None* if none is found.
    """
    for key in _METADATA_SOURCES:
        source = dataset.attrs.get(key)
        if not isinstance(source, str) or not source:
            continue
        match = _START_YEAR_PATTERN.search(source)
        if match:
            return int(match.group(1))
    return None


def normalized_start_token(dataset: xr.Dataset) -> str | None:
    """Return the canonical ``sYYYY11`` start token for the dataset, or *None*."""
    year = extract_start_year(dataset)
    if year is None:
        return None
    return f"s{year:04d}11"
