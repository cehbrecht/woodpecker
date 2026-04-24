from pathlib import Path

import pytest
import xarray as xr

from woodpecker.api import check, check_plan, fix, fix_plan
from woodpecker.inout import (
    NetCDFInput,
    ZarrInput,
    ZarrOutputAdapter,
    get_io_availability,
    get_output_adapter,
)


def test_check_supports_xarray_dataset_input():
    ds = xr.Dataset(
        coords={"lat": [10.0, -10.0], "lon": [0.0]},
        data_vars={"tas": (("lat", "lon"), [[280.0], [281.0]])},
        attrs={"source_name": "example.nc"},
    )

    findings = check(ds, identifiers=["woodpecker.ensure_latitude_is_increasing"])

    assert findings
    assert {entry["fix_id"] for entry in findings}.issuperset(
        {"woodpecker.ensure_latitude_is_increasing"}
    )


def test_fix_supports_xarray_dataset_input_write_mode():
    ds = xr.Dataset(
        data_vars={"tas": ("time", [0.0, 1.0], {"units": "degC"})},
        coords={"time": [0, 1]},
        attrs={"source_name": "example.nc"},
    )

    stats = fix(ds, identifiers=["woodpecker.normalize_tas_units_to_kelvin"], write=True)

    assert stats["attempted"] == 1
    assert stats["changed"] == 1
    assert ds["tas"].attrs["units"] == "K"


def test_check_supports_path_input(make_dummy_netcdf, monkeypatch):
    source = make_dummy_netcdf("cmip6_bad.nc")

    def _fake_run_check(*args, **kwargs):
        _ = (args, kwargs)
        return [
            {
                "path": str(Path(source)),
                "fix_id": "woodpecker.normalize_tas_units_to_kelvin",
                "name": "Common check",
                "message": "synthetic finding",
            }
        ]

    monkeypatch.setattr("woodpecker.api.run_check", _fake_run_check)

    findings = check([source], identifiers=["woodpecker.normalize_tas_units_to_kelvin"])

    assert findings
    assert findings[0]["path"] == str(Path(source))


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


def test_fix_accepts_explicit_output_format():
    ds = xr.Dataset(
        data_vars={"tas": ("time", [0.0, 1.0], {"units": "degC"})},
        coords={"time": [0, 1]},
        attrs={"source_name": "example.nc"},
    )

    stats = fix(
        ds,
        identifiers=["woodpecker.normalize_tas_units_to_kelvin"],
        write=True,
        output_format="netcdf",
    )

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
    monkeypatch.setattr("woodpecker.inout.backends.zarr.zarr_backend_available", lambda: False)
    monkeypatch.setattr("woodpecker.inout.runtime._WARNED_MESSAGES", set())
    adapter = ZarrOutputAdapter()
    ds = xr.Dataset(attrs={"source_name": "case.nc"})
    data_input = NetCDFInput(source_path=Path("case.nc"), name="case.nc")

    with pytest.warns(UserWarning, match="Zarr output backend unavailable"):
        ok = adapter.save(ds, data_input, dry_run=False)

    assert ok is False


def test_api_check_raises_on_unknown_fix_code(make_dummy_netcdf):
    source = make_dummy_netcdf("cmip6_bad.nc")

    with pytest.raises(ValueError, match=r"Unknown fix identifier\(s\): DOESNOTEXIST"):
        check([source], identifiers=["DOESNOTEXIST"])


def test_api_check_plan_uses_codes_from_plan(tmp_path: Path, make_dummy_netcdf, monkeypatch):
    source = make_dummy_netcdf("cmip6_bad.nc")
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(
        '{"plans": [{"id": "core.basic", "steps": [{"id": "woodpecker.normalize_tas_units_to_kelvin"}]}]}',
        encoding="utf-8",
    )

    def _fake_run_check(*args, **kwargs):
        _ = (args, kwargs)
        return [
            {
                "path": str(Path(source)),
                "fix_id": "woodpecker.normalize_tas_units_to_kelvin",
                "name": "Common check",
                "message": "synthetic finding",
            }
        ]

    monkeypatch.setattr("woodpecker.api.run_check", _fake_run_check)

    findings = check_plan(plan_path, inputs=[source])

    assert findings
    assert findings[0]["fix_id"] == "woodpecker.normalize_tas_units_to_kelvin"


def test_api_fix_plan_uses_explicit_output_format_argument(tmp_path: Path, monkeypatch):
    ds = xr.Dataset(
        data_vars={"tas": ("time", [0.0, 1.0], {"units": "degC"})},
        coords={"time": [0, 1]},
        attrs={"source_name": "example.nc"},
    )
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(
        '{"plans": [{"id": "core.basic", "steps": [{"id": "woodpecker.normalize_tas_units_to_kelvin"}]}]}',
        encoding="utf-8",
    )

    observed: dict[str, str] = {}

    def _fake_run_fix(inputs, fixes, dry_run, output_format):
        _ = (inputs, fixes, dry_run)
        observed["output_format"] = output_format
        return {
            "attempted": 1,
            "changed": 1,
            "persist_attempted": 0,
            "persisted": 0,
            "persist_failed": 0,
        }

    monkeypatch.setattr("woodpecker.api.run_fix", _fake_run_fix)

    fix_plan(plan_path, inputs=ds, write=True, output_format="netcdf")

    assert observed["output_format"] == "netcdf"


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

    stats = fix_plan(plan_path, inputs=ds, write=True)

    assert stats["attempted"] == 1
    assert stats["changed"] == 1
    assert "y" not in ds["b"].dims
    assert "x" in ds["b"].dims
