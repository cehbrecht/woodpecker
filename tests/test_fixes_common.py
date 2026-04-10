import numpy as np
import xarray as xr

from woodpecker.fixes.common import COMMON01, COMMON03


def test_common01_apply_write_converts_temperature_units_to_kelvin():
    dataset = xr.Dataset(
        data_vars={"temp": ("time", np.array([0.0, 1.0], dtype=np.float32))},
        coords={"time": [0, 1]},
    )
    dataset["temp"].attrs["units"] = "degC"

    changed = COMMON01().apply(dataset, dry_run=False)

    assert changed is True
    assert dataset["temp"].attrs["units"] == "K"
    np.testing.assert_allclose(dataset["temp"].values, [273.15, 274.15])


def test_common03_apply_write_renames_temp_to_tas():
    dataset = xr.Dataset(
        data_vars={"temp": ("time", np.array([10.0, 11.0], dtype=np.float32))},
        coords={"time": [0, 1]},
    )

    changed = COMMON03().apply(dataset, dry_run=False)

    assert changed is True
    assert "tas" in dataset.data_vars
    assert "temp" not in dataset.data_vars
