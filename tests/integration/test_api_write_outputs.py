"""End-to-end public API examples for write-mode output behavior."""

from woodpecker import fix
from woodpecker.testing import make_cmip6


def test_public_api_write_mode_reports_in_memory_persistence_stats():
    dataset = make_cmip6(overrides={"units": "degC"})

    stats = fix(
        dataset,
        identifiers=["woodpecker.normalize_tas_units_to_kelvin"],
        write=True,
        output_format="auto",
    )

    assert stats == {
        "attempted": 1,
        "changed": 1,
        "persist_attempted": 1,
        "persisted": 1,
        "persist_failed": 0,
    }
    assert dataset["tas"].attrs["units"] == "K"
