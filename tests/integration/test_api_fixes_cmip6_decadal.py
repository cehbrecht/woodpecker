"""End-to-end public API examples for CMIP6-decadal synthetic datasets."""

import numpy as np

from woodpecker.testing import make_cmip6_decadal

from .helpers import assert_check_fix_cycle


def test_cmip6_decadal_equivalent_dimensions_are_detected_and_fixed():
    dataset = make_cmip6_decadal()
    dataset = dataset.assign_coords(member=np.arange(dataset.sizes["lat"]))
    dataset["member_weight"] = ("member", np.ones(dataset.sizes["lat"], dtype="float32"))
    fix_options = {
        "woodpecker.merge_equivalent_dimensions": {"dims": ["lat", "member"]},
    }

    def assert_unchanged(ds):
        assert "member" in ds["member_weight"].dims
        assert "member" in ds.dims

    def assert_fixed(ds):
        assert "member" not in ds["member_weight"].dims
        assert ds["member_weight"].dims == ("lat",)

    assert_check_fix_cycle(
        dataset,
        "woodpecker.merge_equivalent_dimensions",
        fix_options=fix_options,
        assert_unchanged=assert_unchanged,
        assert_fixed=assert_fixed,
    )
