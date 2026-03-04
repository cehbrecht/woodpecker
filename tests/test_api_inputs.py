from pathlib import Path

import xarray as xr

from woodpecker.api import check, fix


def test_check_supports_xarray_dataset_input():
    ds = xr.Dataset(attrs={"source_name": "cmip6_bad.nc"})

    findings = check(ds, codes=["CMIP6D01"])

    assert findings
    assert findings[0]["code"] == "CMIP6D01"


def test_fix_supports_xarray_dataset_input_write_mode():
    ds = xr.Dataset(attrs={"source_name": "atlas sample.nc"})

    stats = fix(ds, codes=["ATLAS01"], write=True)

    assert stats["attempted"] == 1
    assert stats["changed"] == 1
    assert ds.attrs["woodpecker_fix_ATLAS01"] == "applied"


def test_check_supports_path_input(make_dummy_netcdf):
    source = make_dummy_netcdf("cmip6_bad.nc")

    findings = check([source], codes=["CMIP6D01"])

    assert findings
    assert findings[0]["path"] == str(Path(source))
