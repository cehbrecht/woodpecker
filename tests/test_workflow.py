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
                "codes": ["CMIP6_0001"],
                "categories": ["metadata"],
                "output_format": "netcdf",
            }
        ),
        encoding="utf-8",
    )

    workflow = load_workflow(workflow_path)

    assert workflow.version == 1
    assert workflow.inputs == ["./data"]
    assert workflow.codes == ["CMIP6_0001"]
    assert workflow.output_format == "netcdf"


def test_load_workflow_invalid_output_format(tmp_path: Path):
    workflow_path = tmp_path / "workflow.json"
    workflow_path.write_text(
        json.dumps({"codes": ["CMIP6_0001"], "output_format": "parquet"}),
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
                    "cmip6_0001": {"marker_attr": "my_marker"},
                    "ATLAS_0001": {},
                }
            }
        ),
        encoding="utf-8",
    )

    workflow = load_workflow(workflow_path)

    assert set(workflow.fixes.keys()) == {"CMIP6_0001", "ATLAS_0001"}
    assert workflow.fixes["CMIP6_0001"]["marker_attr"] == "my_marker"


def test_workflow_resolve_matches_dataset_selector_and_steps(tmp_path: Path):
    workflow_path = tmp_path / "workflow.json"
    workflow_path.write_text(
        json.dumps(
            {
                "codes": ["ATLAS_0001"],
                "datasets": {
                    "*cmip6*.nc": {
                        "steps": [
                            {"code": "CMIP6_0001", "options": {"message": "selector message"}}
                        ]
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    workflow = load_workflow(workflow_path)
    resolution = workflow.resolve(["/tmp/c3s-cmip6.member.nc"])

    assert resolution.codes == ["CMIP6_0001"]
    assert resolution.ordered_codes == ["CMIP6_0001"]
    assert resolution.fixes["CMIP6_0001"]["message"] == "selector message"


def test_workflow_comment_fields_are_parsed(tmp_path: Path):
    workflow_path = tmp_path / "workflow.json"
    workflow_path.write_text(
        json.dumps(
            {
                "comment": "Top-level note",
                "datasets": {
                    "*cmip6*.nc": {
                        "comment": "Dataset selector note",
                        "steps": [
                            {
                                "code": "CMIP6_0001",
                                "comment": "Fix note with docs link",
                                "options": {"message": "selector message"},
                            }
                        ],
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    workflow = load_workflow(workflow_path)

    assert workflow.comment == "Top-level note"
    block = workflow.datasets["*cmip6*.nc"]
    assert block.comment == "Dataset selector note"
    assert block.steps[0].comment == "Fix note with docs link"


def test_esa_cci_example_workflow_uses_cmip7_fix_codes_in_order():
    workflow_path = Path("workflows/examples/esa_cci.json")

    workflow = load_workflow(workflow_path)
    resolution = workflow.resolve(
        ["/tmp/ESACCI-WATERVAPOUR-L3C-TCWV-meris-005deg-2002-2017-fv3.2.zarr"]
    )

    assert resolution.dataset == "CMIP7"
    assert resolution.codes == ["CMIP7_0003", "COMMON_0002"]
    assert resolution.ordered_codes == ["CMIP7_0003", "COMMON_0002"]
