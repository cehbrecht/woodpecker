from pathlib import Path

import xarray as xr

from woodpecker.testing import (
    integration_plan_path,
    integration_root_dir,
    make_atlas,
    make_cmip6,
    make_cmip6_decadal,
    make_cmip7,
    make_cordex,
)
from woodpecker.testing import testing_root_dir as _testing_root_dir


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


def test_make_cmip6_supports_compact_grid_sizes():
    ds = make_cmip6(periods=1, nlat=2, nlon=3)

    assert ds.sizes == {"time": 1, "lat": 2, "lon": 3}
    assert ds["tas"].shape == (1, 2, 3)


def test_make_cmip6_decadal_returns_realistic_dataset():
    ds = make_cmip6_decadal()

    assert ds.sizes == {"time": 12, "lat": 18, "lon": 36}
    assert set(ds.data_vars) == {"tos"}
    assert ds.attrs["project_id"] == "CMIP6"
    assert ds.attrs["activity_id"] == "DCPP"
    assert ds.attrs["experiment_id"] == "dcppA-hindcast"
    assert ds.attrs["sub_experiment_id"] == "s1960"
    assert ds.attrs["table_id"] == "Omon"


def test_make_cmip7_returns_realistic_dataset():
    ds = make_cmip7()

    assert ds.sizes == {"time": 12, "lat": 18, "lon": 36}
    assert set(ds.data_vars) == {"tas"}
    assert ds.attrs["project_id"] == "CMIP7"
    assert ds.attrs["mip_era"] == "CMIP7"
    assert ds.attrs["source_id"] == "UKESM2-1"
    assert ds.attrs["activity_id"] == "CMIP"
    assert ds.attrs["experiment_id"] == "historical"
    assert ds.attrs["variable_id"] == "tas"
    assert ds.attrs["table_id"] == "Amon"


def test_make_atlas_returns_realistic_dataset():
    ds = make_atlas()

    assert ds.sizes == {"time": 12, "lat": 18, "lon": 36}
    assert set(ds.data_vars) == {"pr"}
    assert ds["pr"].attrs["units"] == "kg m-2 s-1"
    assert ds.attrs["project_id"] == "C3S-Atlas"
    assert "atlas" in ds.attrs["dataset_id"]
    assert ds.attrs["experiment_id"] == "ssp245"
    assert ds.attrs["frequency"] == "mon"


def test_make_cordex_returns_realistic_dataset():
    ds = make_cordex()

    assert ds.sizes == {"time": 12, "lat": 18, "lon": 36}
    assert set(ds.data_vars) == {"tasmax"}
    assert ds.attrs["project_id"] == "CORDEX"
    assert ds.attrs["domain_id"] == "EUR-11"
    assert ds.attrs["driving_model_id"] == "MOHC-HadGEM2-ES"
    assert ds.attrs["driving_experiment_id"] == "rcp85"
    assert ds.attrs["scenario_id"] == "rcp85"
    assert ds.attrs["rcm_model_id"] == "RCA4"
    assert ds.attrs["frequency"] == "day"


def test_new_factories_are_deterministic():
    factories = (make_cmip6_decadal, make_cmip7, make_atlas, make_cordex)

    for make_dataset in factories:
        xr.testing.assert_identical(make_dataset(), make_dataset())
        xr.testing.assert_identical(make_dataset(seed=10), make_dataset(seed=10))


def test_new_factories_share_corruption_api():
    factories = (make_cmip6_decadal, make_cmip7, make_atlas, make_cordex)

    for make_dataset in factories:
        variable = next(iter(make_dataset().data_vars))
        renamed = f"{variable}_broken"
        ds = make_dataset(
            missing=["units"],
            overrides={"experiment_id": "synthetic-test"},
            rename_vars={variable: renamed},
        )

        assert "units" not in ds.attrs
        assert "units" not in ds[renamed].attrs
        assert ds.attrs["experiment_id"] == "synthetic-test"
        assert set(ds.data_vars) == {renamed}


def test_testing_paths_point_to_integration_assets():
    integration_root = integration_root_dir(start=Path(__file__))

    assert _testing_root_dir(start=Path(__file__)).name == "tests"
    assert integration_root.name == "integration"
    assert integration_plan_path("cmip6_core_plan.yaml", start=Path(__file__)).is_file()
