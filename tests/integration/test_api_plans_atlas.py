"""End-to-end public API examples for Atlas fix plans."""

from pathlib import Path

import pytest

import woodpecker
from woodpecker.testing import make_atlas

from .helpers import write_plan_document

pytest.importorskip("woodpecker_atlas_plugin")


def test_atlas_plan_checks_and_fixes_synthetic_dataset(tmp_path: Path):
    dataset = make_atlas(missing=["project_id"])
    dataset["pr"].encoding["complevel"] = 5
    plan_path = write_plan_document(
        tmp_path / "plans.json",
        [
            {
                "id": "atlas.basic",
                "description": "Concrete Atlas plan for atlas*.nc files",
                "match": {"path_patterns": ["*atlas*.nc"]},
                "steps": [
                    {"id": "atlas.encoding_cleanup"},
                    {"id": "atlas.project_id_normalization"},
                ],
            }
        ],
    )

    findings = woodpecker.check_plan(plan_path, inputs=dataset)

    assert set(findings.fix_ids) == {
        "atlas.encoding_cleanup",
        "atlas.project_id_normalization",
    }

    dry_run = woodpecker.fix_plan(plan_path, inputs=dataset, write=False)

    assert dry_run.changed == 2
    assert "project_id" not in dataset.attrs
    assert dataset["pr"].encoding["complevel"] == 5

    write = woodpecker.fix_plan(plan_path, inputs=dataset, write=True)

    assert write.changed == 2
    assert dataset.attrs["project_id"] == "c3s-ipcc-atlas"
    assert dataset["pr"].encoding["complevel"] == 1
    assert dataset["pr"].encoding["zlib"] is True
    assert dataset["pr"].encoding["shuffle"] is True
    assert not woodpecker.check_plan(plan_path, inputs=dataset).has_findings
