from pathlib import Path

import pytest
import xarray as xr

from woodpecker.api import check, fix
from woodpecker.io import (
    NetCDFInput,
    ZarrInput,
    ZarrOutputAdapter,
    get_io_availability,
    get_output_adapter,
)
from woodpecker.testing import make_cmip6


def test_check_exposes_findings_as_properties():
    ds = make_cmip6(overrides={"units": "degC"})

    result = check(ds, fixes="woodpecker.normalize_tas_units_to_kelvin")

    assert result
    assert len(result) == 1
    assert result.count == 1
    assert result.fix_ids == ("woodpecker.normalize_tas_units_to_kelvin",)
    assert result.findings[0]["message"]
    assert str(result) == ("1 finding from 1 fix: woodpecker.normalize_tas_units_to_kelvin")


def test_check_accepts_fix_alias():
    ds = make_cmip6(overrides={"units": "degC"})

    result = check(ds, fixes="woodpecker.tas_units_to_kelvin")

    assert result.fix_ids == ("woodpecker.normalize_tas_units_to_kelvin",)


def test_fix_exposes_stats_as_properties():
    ds = make_cmip6(overrides={"units": "degC"})

    result = fix(
        ds,
        fixes="woodpecker.normalize_tas_units_to_kelvin",
        dry_run=False,
    )

    assert result.attempted == 1
    assert result.changed == 1
    assert result
    assert len(result) == 1
    assert result.count == 1
    assert result.persist_attempted == 1
    assert result.persisted == 1
    assert result.failed == 0
    assert result.preview[0]["fix_id"] == "woodpecker.normalize_tas_units_to_kelvin"
    assert result.preview[0]["changed"] is True
    assert str(result) == "1 change, 1 attempt, 1 persisted"
    assert ds["tas"].attrs["units"] == "K"


def test_empty_results_are_falsey_and_readable():
    ds = make_cmip6(overrides={"units": "K"})

    findings = check(ds, fixes="woodpecker.normalize_tas_units_to_kelvin")
    result = fix(ds, fixes="woodpecker.normalize_tas_units_to_kelvin")

    assert not findings
    assert len(findings) == 0
    assert findings.count == 0
    assert str(findings) == "No findings."

    assert not result
    assert len(result) == 0
    assert result.count == 0
    assert str(result) == "0 changes, 0 attempts, 0 persisted"


def test_output_adapter_target_paths_for_path_inputs():
    netcdf_adapter = get_output_adapter("netcdf")
    zarr_adapter = get_output_adapter("zarr")

    path_input = NetCDFInput(source_path=Path("example.nc"), name="example.nc")
    zarr_input = ZarrInput(source_path=Path("example.zarr"), name="example.zarr")

    assert netcdf_adapter is not None
    assert zarr_adapter is not None
    assert netcdf_adapter.target_path(path_input) == Path("example.nc")
    assert zarr_adapter.target_path(path_input) == Path("example.zarr")
    assert netcdf_adapter.target_path(zarr_input) == Path("example.nc")


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
    monkeypatch.setattr("woodpecker.io.backends.zarr.zarr_backend_available", lambda: False)
    monkeypatch.setattr("woodpecker.io.runtime._WARNED_MESSAGES", set())
    adapter = ZarrOutputAdapter()
    ds = xr.Dataset(attrs={"source_name": "case.nc"})
    data_input = NetCDFInput(source_path=Path("case.nc"), name="case.nc")

    with pytest.warns(UserWarning, match="Zarr output backend unavailable"):
        ok = adapter.save(ds, data_input, dry_run=False)

    assert ok is False


def test_api_check_raises_on_unknown_fix_code(make_placeholder_netcdf_path):
    source = make_placeholder_netcdf_path("cmip6_bad.nc")

    with pytest.raises(ValueError, match=r"Unknown fix identifier\(s\): DOESNOTEXIST"):
        check([source], fixes="DOESNOTEXIST")


def test_api_check_strict_io_raises_on_load_fallback(monkeypatch, make_placeholder_netcdf_path):
    source = make_placeholder_netcdf_path("cmip6_bad.nc")
    monkeypatch.setattr("woodpecker.io.backends.nc.netcdf_backend_available", lambda: False)

    with pytest.raises(RuntimeError, match="NetCDF input backend unavailable"):
        check([source], strict_io=True)
