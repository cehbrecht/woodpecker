from pathlib import Path

import pytest
import xarray as xr

from woodpecker.api import check, check_workflow, fix, fix_workflow
from woodpecker.inout import (
    PathInput,
    ZarrInput,
    ZarrOutputAdapter,
    get_io_availability,
    get_output_adapter,
)


def test_check_supports_xarray_dataset_input():
    ds = xr.Dataset(coords={"time": [0, 1]}, attrs={"source_name": "c3s-cmip6-decadal.bad.nc"})
    ds["time"].encoding["calendar"] = "proleptic_gregorian"

    findings = check(ds, codes=["CMIP6D_0001", "CMIP6D_0002"])

    assert findings
    assert {entry["code"] for entry in findings}.issuperset({"CMIP6D_0001", "CMIP6D_0002"})


def test_fix_supports_xarray_dataset_input_write_mode():
    ds = xr.Dataset(
        data_vars={"tas": ("time", [273.1, 274.2])},
        coords={"time": [0, 1]},
        attrs={"source_name": "c3s-ipcc-atlas.dataset.tas.nc"},
    )
    ds["tas"].encoding["complevel"] = 4

    stats = fix(ds, codes=["ATLAS_0001"], write=True)

    assert stats["attempted"] == 1
    assert stats["changed"] == 1
    assert ds["tas"].encoding["complevel"] == 1
    assert ds["tas"].encoding["zlib"] is True


def test_check_supports_path_input(make_dummy_netcdf):
    source = make_dummy_netcdf("cmip6_bad.nc")

    findings = check([source], codes=["CMIP6_0001"])

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
    ds = xr.Dataset(
        data_vars={"tas": ("time", [273.1, 274.2])},
        coords={"time": [0, 1]},
        attrs={"source_name": "c3s-ipcc-atlas.dataset.tas.nc"},
    )
    ds["tas"].encoding["complevel"] = 4

    stats = fix(ds, codes=["ATLAS_0001"], write=True, output_format="netcdf")

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


def test_api_check_raises_on_unknown_fix_code(make_dummy_netcdf):
    source = make_dummy_netcdf("cmip6_bad.nc")

    with pytest.raises(ValueError, match=r"Unknown fix code\(s\): DOESNOTEXIST"):
        check([source], codes=["DOESNOTEXIST"])


def test_api_check_workflow_uses_codes_from_workflow(tmp_path: Path, make_dummy_netcdf):
    source = make_dummy_netcdf("cmip6_bad.nc")
    workflow_path = tmp_path / "workflow.json"
    workflow_path.write_text(
        '{"codes": ["CMIP6_0001"]}',
        encoding="utf-8",
    )

    findings = check_workflow(workflow_path, inputs=[source])

    assert findings
    assert findings[0]["code"] == "CMIP6_0001"


def test_api_fix_workflow_uses_output_format_from_workflow(tmp_path: Path, monkeypatch):
    ds = xr.Dataset(
        data_vars={"tas": ("time", [273.1, 274.2])},
        coords={"time": [0, 1]},
        attrs={"source_name": "c3s-ipcc-atlas.dataset.tas.nc"},
    )
    workflow_path = tmp_path / "workflow.json"
    workflow_path.write_text(
        '{"codes": ["ATLAS_0001"], "output_format": "netcdf"}',
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

    fix_workflow(workflow_path, inputs=ds, write=True)

    assert observed["output_format"] == "netcdf"


def test_api_fix_workflow_applies_fix_options_to_dataset_attrs(tmp_path: Path):
    ds = xr.Dataset(attrs={"source_name": "c3s-cmip6.member.tas.nc"})
    workflow_path = tmp_path / "workflow.json"
    workflow_path.write_text(
        '{"codes": ["CMIP6_0001"], "fixes": {"CMIP6_0001": {"marker_attr": "custom_marker", "marker_value": "ok"}}}',
        encoding="utf-8",
    )

    stats = fix_workflow(workflow_path, inputs=ds, write=True)

    assert stats["attempted"] == 1
    assert stats["changed"] == 1
    assert ds.attrs["custom_marker"] == "ok"
