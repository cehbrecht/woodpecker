import json
from pathlib import Path

import pytest
import xarray as xr

from woodpecker.fixes.registry import FixRegistry, register_fix
from woodpecker.plans.io import load_fix_plan, load_fix_plan_spec
from woodpecker.plans.models import FixPlan
from woodpecker.plans.runner import apply_fix_plan


class _FixMethodFix:
    code = "PLAN_0001"
    name = "Plan fix method"
    description = ""
    categories = ["metadata"]
    priority = 10
    dataset = None

    def configure(self, config=None):
        self.config = dict(config or {})
        return self

    def check(self, dataset):
        dataset.attrs.setdefault("trace", []).append(("check", dict(getattr(self, "config", {}))))
        return []

    def fix(self, dataset):
        dataset.attrs.setdefault("trace", []).append(("fix", dict(getattr(self, "config", {}))))
        return dataset


class _ApplyMethodFix:
    code = "PLAN_0002"
    name = "Plan apply method"
    description = ""
    categories = ["metadata"]
    priority = 10
    dataset = None

    def configure(self, config=None):
        self.config = dict(config or {})
        return self

    def check(self, dataset):
        dataset.attrs.setdefault("trace", []).append(("check", dict(getattr(self, "config", {}))))
        return []

    def apply(self, dataset, dry_run=True):
        dataset.attrs.setdefault("trace", []).append(
            ("apply", dict(getattr(self, "config", {})), dry_run)
        )
        return True


class _TypeErrorInsideMethodFix:
    code = "PLAN_0003"
    name = "Plan type error fix"
    description = ""
    categories = ["metadata"]
    priority = 10
    dataset = None

    def check(self, dataset, options=None):
        raise TypeError("internal check bug")

    def fix(self, dataset, options=None):
        return dataset


def test_load_fix_plan_from_json(tmp_path: Path):
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(
        '{"fixes": [{"id": "PLAN_0001", "options": {"mode": "fast"}}, "PLAN_0002"]}',
        encoding="utf-8",
    )

    plan = load_fix_plan(plan_path)

    assert isinstance(plan, FixPlan)
    assert [f.id for f in plan.fixes] == ["PLAN_0001", "PLAN_0002"]
    assert plan.fixes[0].options == {"mode": "fast"}
    assert plan.fixes[1].options == {}


def test_load_fix_plan_from_yaml(tmp_path: Path):
    plan_path = tmp_path / "plan.yaml"
    plan_path.write_text(
        "fixes:\n  - id: PLAN_0001\n    options:\n      level: strict\n",
        encoding="utf-8",
    )

    plan = load_fix_plan(plan_path)

    assert [f.id for f in plan.fixes] == ["PLAN_0001"]
    assert plan.fixes[0].options == {"level": "strict"}


def test_apply_plan_calls_check_then_fix_and_passes_options():
    register_fix(_FixMethodFix)
    ds = xr.Dataset()
    plan = FixPlan.from_mapping({"fixes": [{"id": "PLAN_0001", "options": {"alpha": 1}}]})

    try:
        apply_fix_plan(ds, plan, FixRegistry)
    finally:
        FixRegistry._registry.pop("PLAN_0001", None)

    assert ds.attrs["trace"] == [("check", {"alpha": 1}), ("fix", {"alpha": 1})]


def test_apply_plan_falls_back_to_apply_when_fix_method_missing():
    register_fix(_ApplyMethodFix)
    ds = xr.Dataset()
    plan = FixPlan.from_mapping({"fixes": [{"id": "PLAN_0002", "options": {"beta": 2}}]})

    try:
        apply_fix_plan(ds, plan, FixRegistry)
    finally:
        FixRegistry._registry.pop("PLAN_0002", None)

    assert ds.attrs["trace"] == [("check", {"beta": 2}), ("apply", {"beta": 2}, False)]


def test_apply_plan_does_not_mask_type_error_from_fix_method():
    register_fix(_TypeErrorInsideMethodFix)
    ds = xr.Dataset()
    plan = FixPlan.from_mapping({"fixes": [{"id": "PLAN_0003", "options": {"gamma": 3}}]})

    try:
        with pytest.raises(TypeError, match="internal check bug"):
            apply_fix_plan(ds, plan, FixRegistry)
    finally:
        FixRegistry._registry.pop("PLAN_0003", None)


def test_load_fix_plan_spec_json(tmp_path: Path):
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(
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

    plan = load_fix_plan_spec(plan_path)

    assert plan.version == 1
    assert plan.inputs == ["./data"]
    assert plan.codes == ["CMIP6_0001"]
    assert plan.output_format == "netcdf"


def test_load_fix_plan_spec_invalid_output_format(tmp_path: Path):
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(
        json.dumps({"codes": ["CMIP6_0001"], "output_format": "parquet"}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Invalid fix plan file"):
        load_fix_plan_spec(plan_path)


def test_load_fix_plan_spec_fixes_normalized_to_uppercase(tmp_path: Path):
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(
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

    plan = load_fix_plan_spec(plan_path)

    assert set(plan.fixes.keys()) == {"CMIP6_0001", "ATLAS_0001"}
    assert plan.fixes["CMIP6_0001"]["marker_attr"] == "my_marker"


def test_fix_plan_resolve_matches_dataset_selector_and_steps(tmp_path: Path):
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(
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

    plan = load_fix_plan_spec(plan_path)
    resolution = plan.resolve(["/tmp/c3s-cmip6.member.nc"])

    assert resolution.codes == ["CMIP6_0001"]
    assert resolution.ordered_ids == ["CMIP6_0001"]
    assert resolution.fixes["CMIP6_0001"]["message"] == "selector message"


def test_fix_plan_comment_fields_are_parsed(tmp_path: Path):
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(
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

    plan = load_fix_plan_spec(plan_path)

    assert plan.comment == "Top-level note"
    block = plan.datasets["*cmip6*.nc"]
    assert block.comment == "Dataset selector note"
    assert block.steps[0].comment == "Fix note with docs link"


def test_esa_cci_example_fix_plan_uses_plugin_cmip7_fix_codes_in_order():
    plan_path = Path("examples/fix-plans/esa_cci.json")

    plan = load_fix_plan_spec(plan_path)
    resolution = plan.resolve(
        ["/tmp/ESACCI-WATERVAPOUR-L3C-TCWV-meris-005deg-2002-2017-fv3.2.zarr"]
    )

    assert resolution.dataset == "cmip7"
    assert resolution.codes == ["CMIP7_0003", "COMMON_0002"]
    assert resolution.ordered_ids == ["CMIP7_0003", "COMMON_0002"]
