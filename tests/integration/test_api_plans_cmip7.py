"""End-to-end public API examples for CMIP7 fix plans."""

from pathlib import Path

import numpy as np
import pytest

import woodpecker
from woodpecker.testing import make_cmip7

from .helpers import write_plan_document

pytest.importorskip("woodpecker_cmip7_plugin")

ESA_CCI_SOURCE_NAME = "ESACCI-WATERVAPOUR-L3C-TCWV-meris-005deg-2002-2017-fv3.2.zarr"


def _esa_cci_water_vapour_dataset():
    dataset = make_cmip7(
        variable="prw",
        overrides={"source_name": ESA_CCI_SOURCE_NAME},
        seed=7,
    )
    dataset = dataset.isel(lat=slice(None, None, -1))
    dataset = dataset.assign_coords(bnds=[0, 1])
    dataset["lat_bnds"] = (
        ("lat", "bnds"),
        np.column_stack([dataset["lat"].values - 0.5, dataset["lat"].values + 0.5]),
    )
    return dataset


def test_esa_cci_zarr_plan_checks_and_fixes_synthetic_cmip7_dataset(tmp_path: Path):
    dataset = _esa_cci_water_vapour_dataset()
    plan_path = write_plan_document(
        tmp_path / "plans.json",
        [
            {
                "id": "cmip7.esa_cci_water_vapour_zarr",
                "description": "CMIP7/ESA CCI zarr-style inputs",
                "match": {"path_patterns": ["*ESACCI-WATERVAPOUR-*.zarr"]},
                "steps": [
                    {
                        "id": "cmip7.configurable_reformat_bridge",
                        "options": {
                            "realm": "atmos",
                            "branded_variable": "prw_tavg-u-hxy-u",
                            "dim_map": {"bnds": "nv"},
                            "variable_map": {"prw": "tcwv"},
                            "keep_global_attrs": True,
                        },
                    },
                    {"id": "woodpecker.ensure_latitude_is_increasing"},
                ],
            }
        ],
    )

    findings = woodpecker.check_plan(plan_path, inputs=dataset)

    assert findings.fix_ids == (
        "cmip7.configurable_reformat_bridge",
        "woodpecker.ensure_latitude_is_increasing",
    )

    dry_run = woodpecker.fix_plan(plan_path, inputs=dataset, write=False)

    assert dry_run.changed == 2
    assert "prw" in dataset.data_vars
    assert "bnds" in dataset.dims
    assert float(dataset["lat"].values[0]) > float(dataset["lat"].values[-1])

    write = woodpecker.fix_plan(plan_path, inputs=dataset, write=True)

    assert write.changed == 2
    assert "tcwv" in dataset.data_vars
    assert "prw" not in dataset.data_vars
    assert "nv" in dataset.dims
    assert "bnds" not in dataset.dims
    assert dataset.attrs["realm"] == "atmos"
    assert dataset.attrs["branded_variable"] == "prw_tavg-u-hxy-u"
    assert float(dataset["lat"].values[0]) < float(dataset["lat"].values[-1])
    assert not woodpecker.check_plan(plan_path, inputs=dataset).has_findings
