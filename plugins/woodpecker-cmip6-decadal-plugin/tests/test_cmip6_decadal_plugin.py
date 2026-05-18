from pathlib import Path

import numpy as np
import pytest
import woodpecker_cmip6_decadal_plugin  # noqa: F401
import xarray as xr
from _cmip6_decadal_helpers import assert_check_fix_cycle, assert_plan_check_fix_cycle

from woodpecker.fixes.registry import FixRegistry
from woodpecker.testing import make_cmip6_decadal

EXPECTED_FIX_IDS = {
    "cmip6_decadal.calendar_normalization",
    "cmip6_decadal.coordinates_encoding_cleanup",
    "cmip6_decadal.fillvalue_encoding_cleanup",
    "cmip6_decadal.further_info_url_normalization",
    "cmip6_decadal.leadtime_coordinate",
    "cmip6_decadal.leadtime_metadata_normalization",
    "cmip6_decadal.model_global_attributes",
    "cmip6_decadal.realization_comment_normalization",
    "cmip6_decadal.realization_dtype_normalization",
    "cmip6_decadal.realization_index_normalization",
    "cmip6_decadal.realization_long_name_normalization",
    "cmip6_decadal.realization_variable",
    "cmip6_decadal.reftime_coordinate",
    "cmip6_decadal.start_token_normalization",
    "cmip6_decadal.time_metadata",
}
DECADAL_SOURCE_NAME = "c3s-cmip6-decadal.member.tas.nc"
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
PLAN_PATH = Path(__file__).parent / "plans" / "cmip6_decadal_full_plan.json"


def _decadal_dataset(**overrides):
    return make_cmip6_decadal(overrides={"source_name": DECADAL_SOURCE_NAME, **overrides})


def _ec_earth_decadal_dataset(**overrides):
    return make_cmip6_decadal(overrides={"source_name": EC_EARTH_DECADAL_SOURCE_NAME, **overrides})


def _set_realization(dataset, **attrs):
    dataset["realization"] = xr.DataArray(2, attrs=attrs)


def _with_bounds(dataset):
    _set_realization(dataset)
    dataset["lon_bnds"] = (("x", "bnds"), [[0.0, 1.0]])
    dataset["lat_bnds"] = (("x", "bnds"), [[10.0, 11.0]])
    dataset["time_bnds"] = (("time", "bnds"), [[0.0, 1.0]] * dataset.sizes["time"])
    dataset = dataset.assign_coords(x=[0], bnds=[0, 1])
    return dataset


def _with_forecast_times(dataset):
    dataset = dataset.isel(time=slice(0, 2))
    return dataset.assign_coords(time=np.array(["1960-11-16", "1960-12-16"], dtype="datetime64[D]"))


def _decadal_time_metadata_case():
    dataset = _decadal_dataset()

    def assert_fixed(ds):
        assert ds["time"].attrs["long_name"] == "valid_time"

    return dataset, assert_fixed


def _decadal_calendar_case():
    dataset = _decadal_dataset()
    dataset["time"].encoding["calendar"] = "proleptic_gregorian"

    def assert_fixed(ds):
        assert ds["time"].encoding["calendar"] == "standard"

    return dataset, assert_fixed


def _decadal_realization_variable_case():
    dataset = _decadal_dataset(realization_index="2")

    def assert_fixed(ds):
        assert int(ds["realization"].values) == 2

    return dataset, assert_fixed


def _decadal_coordinates_encoding_case():
    dataset = _with_bounds(_decadal_dataset())
    dataset["realization"].encoding["coordinates"] = "time"

    def assert_fixed(ds):
        assert "coordinates" not in ds["realization"].encoding

    return dataset, assert_fixed


def _decadal_realization_comment_case():
    dataset = _decadal_dataset()
    _set_realization(dataset, comment="short")

    def assert_fixed(ds):
        assert "initialization_description" in ds["realization"].attrs["comment"]

    return dataset, assert_fixed


def _decadal_realization_dtype_case():
    dataset = _decadal_dataset()
    _set_realization(dataset)

    def assert_fixed(ds):
        assert ds["realization"].dtype == np.int32

    return dataset, assert_fixed


def _decadal_fillvalue_encoding_case():
    dataset = _with_bounds(_decadal_dataset())
    dataset["realization"].encoding["_FillValue"] = -9999

    def assert_fixed(ds):
        assert "_FillValue" not in ds["realization"].encoding

    return dataset, assert_fixed


def _decadal_further_info_url_case():
    dataset = _decadal_dataset(
        further_info_url=(
            "https://furtherinfo.es-doc.org/CMIP6.EC-Earth-Consortium.EC-Earth3."
            "dcppA-hindcast.s1960-r2i1p1f1"
        )
    )

    def assert_fixed(ds):
        assert "s1960.r2i1p1f1" in ds.attrs["further_info_url"]

    return dataset, assert_fixed


def _decadal_start_token_case():
    dataset = _ec_earth_decadal_dataset(startdate="s1960", sub_experiment_id="s1960")

    def assert_fixed(ds):
        assert ds.attrs["startdate"] == "s196011"
        assert ds.attrs["sub_experiment_id"] == "s196011"

    return dataset, assert_fixed


def _decadal_realization_long_name_case():
    dataset = _decadal_dataset()
    _set_realization(dataset, long_name="member")

    def assert_fixed(ds):
        assert ds["realization"].attrs["long_name"] == "realization"

    return dataset, assert_fixed


def _decadal_realization_index_case():
    dataset = _decadal_dataset(realization_index="2")

    def assert_fixed(ds):
        assert ds.attrs["realization_index"] == 2

    return dataset, assert_fixed


def _decadal_leadtime_metadata_case():
    dataset = _decadal_dataset()
    dataset = dataset.assign_coords(leadtime=("time", np.arange(dataset.sizes["time"])))
    dataset["leadtime"].attrs["units"] = "hours"

    def assert_fixed(ds):
        assert ds["leadtime"].attrs["units"] == "days"
        assert ds["leadtime"].attrs["standard_name"] == "forecast_period"

    return dataset, assert_fixed


def _decadal_model_global_attrs_case():
    dataset = _ec_earth_decadal_dataset(forcing_description="wrong")

    def assert_fixed(ds):
        assert ds.attrs["forcing_description"] == "f1, CMIP6 historical forcings"
        assert ds.attrs["physics_description"].startswith("physics from the standard model")

    return dataset, assert_fixed


def _decadal_reftime_coordinate_case():
    dataset = _with_forecast_times(_ec_earth_decadal_dataset(startdate="s196011"))
    dataset["time"].encoding["calendar"] = "standard"

    def assert_fixed(ds):
        assert "reftime" in ds.coords
        assert ds["reftime"].attrs["standard_name"] == "forecast_reference_time"

    return dataset, assert_fixed


def _decadal_leadtime_coordinate_case():
    dataset = _with_forecast_times(_decadal_dataset())
    dataset.coords["reftime"] = xr.DataArray(np.datetime64("1960-11-01"))

    def assert_fixed(ds):
        assert "leadtime" in ds.coords
        np.testing.assert_allclose(ds["leadtime"].values, np.array([15.0, 45.0]))

    return dataset, assert_fixed


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


def test_plugin_registers_expected_fixes():
    fix_ids = {fix.id for fix in FixRegistry.discover()}

    assert EXPECTED_FIX_IDS.issubset(fix_ids)


def test_plugin_fixes_work_with_public_api():
    import woodpecker

    dataset = make_cmip6_decadal(overrides={"source_name": "c3s-cmip6-decadal.member.tos.nc"})
    dataset["time"].attrs.pop("long_name", None)
    findings = woodpecker.check(dataset, fixes=sorted(EXPECTED_FIX_IDS))

    assert findings
    assert set(findings.fix_ids).issubset(EXPECTED_FIX_IDS)


@pytest.mark.parametrize(
    ("fix_id", "case_factory"),
    [
        ("cmip6_decadal.time_metadata", _decadal_time_metadata_case),
        ("cmip6_decadal.calendar_normalization", _decadal_calendar_case),
        ("cmip6_decadal.realization_variable", _decadal_realization_variable_case),
        ("cmip6_decadal.coordinates_encoding_cleanup", _decadal_coordinates_encoding_case),
        ("cmip6_decadal.realization_comment_normalization", _decadal_realization_comment_case),
        ("cmip6_decadal.realization_dtype_normalization", _decadal_realization_dtype_case),
        ("cmip6_decadal.fillvalue_encoding_cleanup", _decadal_fillvalue_encoding_case),
        ("cmip6_decadal.further_info_url_normalization", _decadal_further_info_url_case),
        ("cmip6_decadal.start_token_normalization", _decadal_start_token_case),
        ("cmip6_decadal.realization_long_name_normalization", _decadal_realization_long_name_case),
        ("cmip6_decadal.realization_index_normalization", _decadal_realization_index_case),
        ("cmip6_decadal.leadtime_metadata_normalization", _decadal_leadtime_metadata_case),
        ("cmip6_decadal.model_global_attributes", _decadal_model_global_attrs_case),
        ("cmip6_decadal.reftime_coordinate", _decadal_reftime_coordinate_case),
        ("cmip6_decadal.leadtime_coordinate", _decadal_leadtime_coordinate_case),
    ],
)
def test_cmip6_decadal_fix_is_detected_and_applied(fix_id, case_factory):
    dataset, assert_fixed = case_factory()

    assert_check_fix_cycle(
        dataset,
        fix_id,
        assert_fixed=assert_fixed,
    )


def test_cmip6_decadal_full_plan_checks_and_fixes_synthetic_dataset():
    dataset = _cmip6_decadal_full_suite_dataset()

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

    assert_plan_check_fix_cycle(
        PLAN_PATH,
        dataset,
        expected_fix_ids=DECADAL_FULL_FIX_IDS,
        expected_changed=len(DECADAL_FULL_FIX_IDS),
        expected_write_changed=len(DECADAL_FULL_FIX_IDS) + 1,
        assert_unchanged=assert_unchanged,
        assert_fixed=assert_fixed,
    )
