import numpy as np
import xarray as xr

from woodpecker.fixes.common import MergeEquivalentDimensionsFix, NormalizeTasUnitsToKelvinFix


def test_common01_apply_write_converts_temperature_units_to_kelvin():
    dataset = xr.Dataset(
        data_vars={"temp": ("time", np.array([0.0, 1.0], dtype=np.float32))},
        coords={"time": [0, 1]},
    )
    dataset["temp"].attrs["units"] = "degC"

    changed = NormalizeTasUnitsToKelvinFix().apply(dataset, dry_run=False)

    assert changed is True
    assert dataset["temp"].attrs["units"] == "K"
    np.testing.assert_allclose(dataset["temp"].values, [273.15, 274.15])


def test_common04_apply_write_merges_equivalent_dims():
    dataset = xr.Dataset(
        data_vars={"tcwv": (("time", "bnds"), np.array([[1.0, 2.0]], dtype=np.float32))},
        coords={
            "time": [0],
            "bnds": [0, 1],
            "nv": [0, 1],
        },
    )

    changed = (
        MergeEquivalentDimensionsFix()
        .configure({"dims": ["bnds", "nv"]})
        .apply(dataset, dry_run=False)
    )

    assert changed is True
    assert "bnds" in dataset["tcwv"].dims
    assert "nv" not in dataset["tcwv"].dims
