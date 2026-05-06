import pytest
import xarray as xr

# Import side effects to ensure atlas detector registration.
import woodpecker.fixes  # noqa: F401
from woodpecker.identity import resolve_dataset_identity


@pytest.mark.parametrize(
    ("source_name", "expected_type"),
    [
        ("c3s-ipcc-atlas.dataset.tas.nc", "atlas"),
        ("c3s-cmip6-decadal.member.tas.nc", "cmip6-decadal"),
        ("c3s-cmip6.member.tas.nc", "cmip6"),
        ("some-random-dataset.nc", None),
    ],
)
def test_identify_dataset_type_from_source_name(source_name, expected_type):
    ds = xr.Dataset(attrs={"source_name": source_name})

    detected = resolve_dataset_identity(ds).dataset_type

    assert detected == expected_type


def test_identify_dataset_type_prefers_metadata_for_cmip6():
    ds = xr.Dataset(
        attrs={
            "mip_era": "CMIP6",
            "activity_id": "CMIP",
            "source_id": "EC-Earth3",
            "dataset_id": "c3s-cmip6.foo.bar",
        }
    )

    detected = resolve_dataset_identity(ds).dataset_type

    assert detected == "cmip6"


def test_identify_dataset_type_prefers_decadal_metadata_over_source_name():
    ds = xr.Dataset(
        attrs={
            "mip_era": "CMIP6",
            "activity_id": "DCPP",
            "source_name": "c3s-cmip6.member.tas.nc",
        }
    )

    detected = resolve_dataset_identity(ds).dataset_type

    assert detected == "cmip6-decadal"


def test_identify_dataset_type_does_not_classify_plain_cmip6_metadata_as_decadal():
    ds = xr.Dataset(
        attrs={
            "mip_era": "CMIP6",
            "project_id": "c3s-cmip6",
            "dataset_id": "c3s-cmip6.foo.bar",
        }
    )

    detected = resolve_dataset_identity(ds).dataset_type

    assert detected == "cmip6"
