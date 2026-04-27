import xarray as xr

# Import side effects to ensure atlas detector registration.
import woodpecker.fixes  # noqa: F401
from woodpecker.identity import resolve_dataset_identity


def test_identify_dataset_type_detects_atlas_from_source_name():
    ds = xr.Dataset(attrs={"source_name": "c3s-ipcc-atlas.dataset.tas.nc"})

    detected = resolve_dataset_identity(ds).dataset_type

    assert detected == "atlas"


def test_identify_dataset_type_returns_none_when_unknown():
    ds = xr.Dataset(attrs={"source_name": "some-random-dataset.nc"})

    detected = resolve_dataset_identity(ds).dataset_type

    assert detected is None


def test_identify_dataset_type_detects_cmip6_decadal_from_source_name():
    ds = xr.Dataset(attrs={"source_name": "c3s-cmip6-decadal.member.tas.nc"})

    detected = resolve_dataset_identity(ds).dataset_type

    assert detected == "cmip6-decadal"


def test_identify_dataset_type_detects_cmip6_from_source_name():
    ds = xr.Dataset(attrs={"source_name": "c3s-cmip6.member.tas.nc"})

    detected = resolve_dataset_identity(ds).dataset_type

    assert detected == "cmip6"


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
