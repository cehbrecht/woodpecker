from pathlib import Path

import pytest
import xarray as xr

from woodpecker.api import check, fix
from woodpecker.inout import (
    PathInput,
    ZarrInput,
    ZarrOutputAdapter,
    get_io_availability,
    get_output_adapter,
)


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


def test_output_adapter_target_paths_for_path_inputs():
    netcdf_adapter = get_output_adapter("netcdf")
    zarr_adapter = get_output_adapter("zarr")

    path_input = PathInput(source_path=Path("example.nc"), name="example.nc")
    zarr_input = ZarrInput(source_path=Path("example.zarr"), name="example.zarr")

    assert netcdf_adapter is not None
    assert zarr_adapter is not None
    assert netcdf_adapter.target_path(path_input) == Path("example.nc")
    assert zarr_adapter.target_path(path_input) == Path("example.zarr")
    assert netcdf_adapter.target_path(zarr_input) == Path("example.nc")


def test_fix_accepts_explicit_output_format():
    ds = xr.Dataset(attrs={"source_name": "atlas sample.nc"})

    stats = fix(ds, codes=["ATLAS01"], write=True, output_format="netcdf")

    assert stats["attempted"] == 1
    assert stats["changed"] == 1


def test_io_availability_report_has_expected_keys():
    report = get_io_availability()

    assert {
        "xarray_input",
        "netcdf_input",
        "zarr_input",
        "netcdf_output",
        "zarr_output",
    }.issubset(report.keys())


def test_zarr_output_adapter_warns_and_fails_when_backend_unavailable(monkeypatch):
    monkeypatch.setattr("woodpecker.inout.zarr._zarr_backend_available", lambda: False)
    monkeypatch.setattr("woodpecker.inout.base._WARNED_MESSAGES", set())
    adapter = ZarrOutputAdapter()
    ds = xr.Dataset(attrs={"source_name": "case.nc"})
    data_input = PathInput(source_path=Path("case.nc"), name="case.nc")

    with pytest.warns(UserWarning, match="Zarr output backend unavailable"):
        ok = adapter.save(ds, data_input, dry_run=False)

    assert ok is False
