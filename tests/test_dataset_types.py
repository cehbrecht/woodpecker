import xarray as xr

# Import side effects to ensure atlas detector registration.
import woodpecker.fixes  # noqa: F401
from woodpecker.fixes.dataset_types import identify_dataset_type


def test_identify_dataset_type_detects_atlas_from_source_name():
    ds = xr.Dataset(attrs={"source_name": "c3s-ipcc-atlas.dataset.tas.nc"})

    detected = identify_dataset_type(ds)

    assert detected == "atlas"


def test_identify_dataset_type_returns_none_when_unknown():
    ds = xr.Dataset(attrs={"source_name": "some-random-dataset.nc"})

    detected = identify_dataset_type(ds)

    assert detected is None


def test_identify_dataset_type_detects_cmip6_decadal_from_source_name():
    ds = xr.Dataset(attrs={"source_name": "c3s-cmip6-decadal.member.tas.nc"})

    detected = identify_dataset_type(ds)

    assert detected == "cmip6-decadal"
