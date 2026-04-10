import json
from pathlib import Path

import pytest

from woodpecker.workflow import load_workflow


def test_load_workflow_json(tmp_path: Path):
    workflow_path = tmp_path / "workflow.json"
    workflow_path.write_text(
        json.dumps(
            {
                "version": 1,
                "inputs": ["./data"],
                "codes": ["CMIP601"],
                "categories": ["metadata"],
                "output_format": "netcdf",
            }
        ),
        encoding="utf-8",
    )

    workflow = load_workflow(workflow_path)

    assert workflow.version == 1
    assert workflow.inputs == ["./data"]
    assert workflow.codes == ["CMIP601"]
    assert workflow.output_format == "netcdf"


def test_load_workflow_invalid_output_format(tmp_path: Path):
    workflow_path = tmp_path / "workflow.json"
    workflow_path.write_text(
        json.dumps({"codes": ["CMIP601"], "output_format": "parquet"}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Invalid workflow file"):
        load_workflow(workflow_path)


def test_load_workflow_fixes_normalized_to_uppercase(tmp_path: Path):
    workflow_path = tmp_path / "workflow.json"
    workflow_path.write_text(
        json.dumps(
            {
                "fixes": {
                    "cmip601": {"marker_attr": "my_marker"},
                    "ATLAS01": {},
                }
            }
        ),
        encoding="utf-8",
    )

    workflow = load_workflow(workflow_path)

    assert set(workflow.fixes.keys()) == {"CMIP601", "ATLAS01"}
    assert workflow.fixes["CMIP601"]["marker_attr"] == "my_marker"
