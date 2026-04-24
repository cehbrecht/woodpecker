from pathlib import Path

import pytest
import xarray as xr

from woodpecker.inout import NetCDFInput, ZarrInput, ZarrOutputAdapter
from woodpecker.inout.nc import netcdf_backend_available
from woodpecker.inout.zarr import zarr_backend_available

pytestmark = [
    pytest.mark.io_backend,
    pytest.mark.filterwarnings("ignore:.*NetCDF input backend unavailable.*"),
    pytest.mark.filterwarnings("ignore:.*Zarr input backend unavailable.*"),
]


@pytest.mark.skipif(not netcdf_backend_available(), reason="No NetCDF backend installed")
def test_netcdf_path_input_roundtrip(tmp_path: Path):
    source = tmp_path / "sample.nc"
    ds = xr.Dataset({"value": ("time", [1.0, 2.0])}, coords={"time": [0, 1]})
    ds.attrs["source_name"] = source.name
    ds.to_netcdf(source)
    ds.close()

    data_input = NetCDFInput(source_path=source, name=source.name)
    loaded = data_input.load()

    assert "value" in loaded
    loaded.attrs["woodpecker_fix_TEST"] = "applied"

    ok = data_input.save(loaded, dry_run=False)
    assert ok is True
    assert source.exists()

    loaded.close()


@pytest.mark.skipif(not zarr_backend_available(), reason="No Zarr backend installed")
def test_zarr_output_adapter_roundtrip(tmp_path: Path):
    source = tmp_path / "sample.nc"
    source.touch()

    ds = xr.Dataset({"value": ("time", [1.0, 2.0])}, coords={"time": [0, 1]})
    data_input = NetCDFInput(source_path=source, name=source.name)
    adapter = ZarrOutputAdapter()

    ok = adapter.save(ds, data_input, dry_run=False)
    assert ok is True

    zarr_path = source.with_suffix(".zarr")
    assert zarr_path.exists()

    zarr_input = ZarrInput(source_path=zarr_path, name=zarr_path.name)
    loaded = zarr_input.load()

    assert "value" in loaded
    loaded.close()
