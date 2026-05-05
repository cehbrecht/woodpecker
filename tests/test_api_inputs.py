from pathlib import Path

import pytest
import xarray as xr

from woodpecker.api import check, check_plan, fix, fix_plan
from woodpecker.io import (
    NetCDFInput,
    ZarrInput,
    ZarrOutputAdapter,
    get_io_availability,
    get_output_adapter,
)
from woodpecker.testing import make_cmip6


def test_check_supports_xarray_dataset_input():
    ds = xr.Dataset(
        coords={"lat": [10.0, -10.0], "lon": [0.0]},
        data_vars={"tas": (("lat", "lon"), [[280.0], [281.0]])},
        attrs={"source_name": "example.nc"},
    )

    result = check(ds, identifiers=["woodpecker.ensure_latitude_is_increasing"])

    assert result.has_findings
    assert set(result.fix_ids).issuperset({"woodpecker.ensure_latitude_is_increasing"})


@pytest.mark.parametrize("output_format", ["auto", "netcdf"])
def test_fix_supports_xarray_dataset_input_write_mode(output_format):
    ds = make_cmip6(overrides={"units": "degC"})

    result = fix(
        ds,
        identifiers=["woodpecker.normalize_tas_units_to_kelvin"],
        write=True,
        output_format=output_format,
    )

    assert result.attempted == 1
    assert result.changed == 1
    assert ds["tas"].attrs["units"] == "K"


def test_check_exposes_findings_as_properties():
    ds = make_cmip6(overrides={"units": "degC"})

    result = check(ds, identifiers=["woodpecker.normalize_tas_units_to_kelvin"])

    assert result.has_findings is True
    assert result.fix_ids == ("woodpecker.normalize_tas_units_to_kelvin",)
    assert result.findings[0]["message"]


def test_fix_exposes_stats_as_properties():
    ds = make_cmip6(overrides={"units": "degC"})

    result = fix(
        ds,
        identifiers=["woodpecker.normalize_tas_units_to_kelvin"],
        write=True,
    )

    assert result.attempted == 1
    assert result.changed == 1
    assert result.has_changes is True
    assert result.persist_attempted == 1
    assert result.persisted == 1
    assert result.persist_failed == 0
    assert ds["tas"].attrs["units"] == "K"


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
        check([source], identifiers=["DOESNOTEXIST"])


def test_api_check_plan_returns_result_object(tmp_path: Path):
    ds = make_cmip6(overrides={"units": "degC"})
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(
        '{"plans": [{"id": "core.check", "steps": [{"id": "woodpecker.normalize_tas_units_to_kelvin"}]}]}',
        encoding="utf-8",
    )

    result = check_plan(plan_path, inputs=ds)

    assert result.has_findings is True
    assert result.fix_ids == ("woodpecker.normalize_tas_units_to_kelvin",)


def test_api_fix_plan_applies_fix_options_to_dataset_attrs(tmp_path: Path):
    ds = xr.Dataset(
        data_vars={
            "a": ("x", [1.0, 2.0]),
            "b": ("y", [3.0, 4.0]),
        },
        coords={"x": [0, 1], "y": [0, 1]},
        attrs={"source_name": "example.nc"},
    )
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(
        '{"plans": [{"id": "core.options", "steps": [{"id": "woodpecker.merge_equivalent_dimensions", "options": {"dims": ["x", "y"]}}]}]}',
        encoding="utf-8",
    )

    result = fix_plan(plan_path, inputs=ds, write=True)

    assert result.attempted == 1
    assert result.changed == 1
    assert "y" not in ds["b"].dims
    assert "x" in ds["b"].dims
