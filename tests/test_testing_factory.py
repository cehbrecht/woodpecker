import xarray as xr

from woodpecker.testing import make_cmip6


def test_make_cmip6_returns_realistic_small_dataset():
    ds = make_cmip6()

    assert isinstance(ds, xr.Dataset)
    assert set(ds.dims) == {"time", "lat", "lon"}
    assert ds.sizes == {"time": 12, "lat": 18, "lon": 36}
    assert set(ds.data_vars) == {"tas"}
    assert ds["tas"].dims == ("time", "lat", "lon")
    assert ds["tas"].attrs["units"] == "K"
    assert ds.attrs["project_id"] == "CMIP6"
    assert ds.attrs["mip_era"] == "CMIP6"
    assert ds.attrs["activity_id"] == "CMIP"
    assert ds.attrs["experiment_id"] == "historical"
    assert ds.attrs["variable_id"] == "tas"
    assert ds.attrs["table_id"] == "Amon"
    assert ds.attrs["frequency"] == "mon"
    assert ds.attrs["grid_label"] == "gn"


def test_make_cmip6_is_deterministic_without_seed():
    first = make_cmip6()
    second = make_cmip6()

    xr.testing.assert_identical(first, second)


def test_make_cmip6_seed_is_repeatable_and_changes_values():
    seeded = make_cmip6(seed=1)
    repeated = make_cmip6(seed=1)
    different_seed = make_cmip6(seed=2)

    xr.testing.assert_identical(seeded, repeated)
    assert not seeded["tas"].identical(different_seed["tas"])


def test_make_cmip6_supports_metadata_corruption():
    ds = make_cmip6(
        missing=["units"],
        overrides={"experiment_id": "ssp585"},
        rename_vars={"tas": "temperature"},
    )

    assert "units" not in ds.attrs
    assert "units" not in ds["temperature"].attrs
    assert ds.attrs["experiment_id"] == "ssp585"
    assert set(ds.data_vars) == {"temperature"}


def test_make_cmip6_supports_variable_specific_metadata():
    ds = make_cmip6(variable="pr")

    assert set(ds.data_vars) == {"pr"}
    assert ds.attrs["variable_id"] == "pr"
    assert ds.attrs["units"] == "kg m-2 s-1"
    assert ds["pr"].attrs["units"] == "kg m-2 s-1"
