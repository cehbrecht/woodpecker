"""End-to-end public API examples for CMIP6-decadal fix plans."""

import numpy as np
import pytest
import xarray as xr

import woodpecker
from woodpecker.testing import integration_plan_path, make_cmip6_decadal

pytest.importorskip("woodpecker_cmip6_decadal_plugin")

EC_EARTH_DECADAL_SOURCE_NAME = (
    "c3s-cmip6-decadal.DCPP.EC-Earth-Consortium.EC-Earth3."
    "dcppA-hindcast.s1960-r2i1p1f1.Amon.tas.gr.v20201215.nc"
)

DECADAL_FULL_FIX_IDS = (
    "cmip6_decadal.time_metadata",
    "cmip6_decadal.calendar_normalization",
    "cmip6_decadal.realization_comment_normalization",
    "cmip6_decadal.realization_dtype_normalization",
    "cmip6_decadal.fillvalue_encoding_cleanup",
    "cmip6_decadal.start_token_normalization",
    "cmip6_decadal.realization_long_name_normalization",
    "cmip6_decadal.realization_index_normalization",
    "cmip6_decadal.model_global_attributes",
    "cmip6_decadal.reftime_coordinate",
)


def _cmip6_decadal_full_suite_dataset():
    dataset = make_cmip6_decadal(
        overrides={
            "source_name": EC_EARTH_DECADAL_SOURCE_NAME,
            "startdate": "s1960",
            "sub_experiment_id": "s1960",
            "realization_index": "2",
            "forcing_description": "wrong",
        }
    )
    dataset = dataset.isel(time=slice(0, 2))
    dataset = dataset.assign_coords(
        time=np.array(["1960-11-16", "1960-12-16"], dtype="datetime64[D]")
    )
    dataset["time"].attrs["long_name"] = "time"
    dataset["time"].encoding["calendar"] = "proleptic_gregorian"
    dataset["realization"] = xr.DataArray(2, attrs={"comment": "short", "long_name": "member"})
    dataset["realization"].encoding["_FillValue"] = -9999
    return dataset


def test_cmip6_decadal_full_plan_checks_and_fixes_synthetic_dataset():
    dataset = _cmip6_decadal_full_suite_dataset()
    plan_path = integration_plan_path("cmip6_decadal_full_plan.json")

    def assert_unchanged(ds):
        assert ds.attrs["startdate"] == "s1960"
        assert "reftime" not in ds.coords
        assert "leadtime" not in ds.coords

    def assert_fixed(ds):
        assert ds.attrs["startdate"] == "s196011"
        assert ds.attrs["sub_experiment_id"] == "s196011"
        assert ds.attrs["forcing_description"] == "f1, CMIP6 historical forcings"
        assert ds.attrs["realization_index"] == 2
        assert ds["time"].attrs["long_name"] == "valid_time"
        assert ds["time"].encoding["calendar"] == "standard"
        assert ds["realization"].dtype == np.int32
        assert ds["realization"].attrs["long_name"] == "realization"
        assert "_FillValue" not in ds["realization"].encoding
        assert "reftime" in ds.coords
        assert "leadtime" in ds.coords

    findings = woodpecker.plan.check(dataset, plan_path)
    assert findings.fix_ids == DECADAL_FULL_FIX_IDS

    preview = woodpecker.plan.fix(dataset, plan_path, dry_run=True)
    assert preview.changed == len(DECADAL_FULL_FIX_IDS)
    assert preview.persisted == 0
    assert_unchanged(dataset)

    write = woodpecker.plan.fix(dataset, plan_path, dry_run=False)
    assert write.changed == len(DECADAL_FULL_FIX_IDS) + 1
    assert write.persisted == 1
    assert_fixed(dataset)

    assert not woodpecker.plan.check(dataset, plan_path)
