import json
from pathlib import Path

import pytest
import xarray as xr

from woodpecker.fixes.registry import Fix, FixRegistry, register_fix
from woodpecker.plans.io import load_fix_plan, load_fix_plan_document
from woodpecker.plans.matcher import plan_matches_dataset
from woodpecker.plans.models import (
    FixPlan,
    FixPlanDocument,
    FixPlanRuntimeMetadata,
    FixRef,
    ProviderMetadata,
)
from woodpecker.plans.runner import apply_fix_plan


class _FixMethodFix(Fix):
    namespace_prefix = "plan_test"
    local_id = "fix_method"
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


class _ApplyMethodFix(Fix):
    namespace_prefix = "plan_test"
    local_id = "apply_method"
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


class _TypeErrorInsideMethodFix(Fix):
    namespace_prefix = "plan_test"
    local_id = "type_error_inside_method"
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
        '{"fixes": [{"id": "plan_test.fix_method", "options": {"mode": "fast"}}, "plan_test.apply_method"]}',
        encoding="utf-8",
    )

    plan = load_fix_plan(plan_path)

    assert isinstance(plan, FixPlan)
    assert [f.id for f in plan.fixes] == ["plan_test.fix_method", "plan_test.apply_method"]
    assert plan.fixes[0].options == {"mode": "fast"}
    assert plan.fixes[1].options == {}


def test_load_fix_plan_from_yaml(tmp_path: Path):
    plan_path = tmp_path / "plan.yaml"
    plan_path.write_text(
        "fixes:\n  - id: plan_test.fix_method\n    options:\n      level: strict\n",
        encoding="utf-8",
    )

    plan = load_fix_plan(plan_path)

    assert [f.id for f in plan.fixes] == ["plan_test.fix_method"]
    assert plan.fixes[0].options == {"level": "strict"}


def test_apply_plan_calls_check_then_fix_and_passes_options():
    register_fix(_FixMethodFix)
    ds = xr.Dataset()
    plan = FixPlan.from_mapping(
        {"fixes": [{"id": "plan_test.fix_method", "options": {"alpha": 1}}]}
    )

    try:
        apply_fix_plan(ds, plan, FixRegistry)
    finally:
        FixRegistry._registry.pop("plan_test.fix_method", None)

    assert ds.attrs["trace"] == [("check", {"alpha": 1}), ("fix", {"alpha": 1})]


def test_apply_plan_falls_back_to_apply_when_fix_method_missing():
    register_fix(_ApplyMethodFix)
    ds = xr.Dataset()
    plan = FixPlan.from_mapping(
        {"fixes": [{"id": "plan_test.apply_method", "options": {"beta": 2}}]}
    )

    try:
        apply_fix_plan(ds, plan, FixRegistry)
    finally:
        FixRegistry._registry.pop("plan_test.apply_method", None)

    assert ds.attrs["trace"] == [("check", {"beta": 2}), ("apply", {"beta": 2}, False)]


def test_apply_plan_does_not_mask_type_error_from_fix_method():
    register_fix(_TypeErrorInsideMethodFix)
    ds = xr.Dataset()
    plan = FixPlan.from_mapping(
        {"fixes": [{"id": "plan_test.type_error_inside_method", "options": {"gamma": 3}}]}
    )

    try:
        with pytest.raises(TypeError, match="internal check bug"):
            apply_fix_plan(ds, plan, FixRegistry)
    finally:
        FixRegistry._registry.pop("plan_test.type_error_inside_method", None)


def test_load_fix_plan_document_json(tmp_path: Path):
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(
        json.dumps(
            {
                "plans": [
                    {
                        "id": "cmip6-basic",
                        "description": "simple plan",
                        "match": {"path_patterns": ["*cmip6*.nc"]},
                        "fixes": [{"id": "CMIP6_0001", "options": {"message": "ok"}}],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    document = load_fix_plan_document(plan_path)

    assert isinstance(document, FixPlanDocument)
    assert document.schema_version == 1
    assert len(document.plans) == 1
    assert document.plans[0].id == "cmip6-basic"
    assert document.plans[0].fixes[0].id == "cmip6_0001"


def test_load_fix_plan_document_single_plan_shorthand(tmp_path: Path):
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(
        json.dumps(
            {
                "id": "single",
                "fixes": [{"id": "CMIP6_0001"}],
            }
        ),
        encoding="utf-8",
    )

    document = load_fix_plan_document(plan_path)

    assert document.schema_version == 1
    assert len(document.plans) == 1
    assert document.plans[0].id == "single"
    assert document.plans[0].fixes[0].id == "cmip6_0001"


def test_load_fix_plan_document_plan_entries_normalize_fix_ids(tmp_path: Path):
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(
        json.dumps(
            {
                "plans": [
                    {
                        "id": "mixed-case",
                        "fixes": [
                            {
                                "id": "cmip6.dummy_placeholder",
                                "options": {"marker_attr": "my_marker"},
                            },
                            {"id": "atlas.encoding_cleanup", "options": {}},
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    document = load_fix_plan_document(plan_path)

    fixes = document.plans[0].fixes
    assert [item.id for item in fixes] == ["cmip6.dummy_placeholder", "atlas.encoding_cleanup"]
    assert fixes[0].options["marker_attr"] == "my_marker"


def test_fix_plan_to_dict_persists_canonical_ids_from_local_fix_refs():
    plan = FixPlan.from_mapping(
        {
            "id": "atlas.atlas_basic",
            "namespace_prefix": "atlas",
            "fixes": [
                {"id": "encoding_cleanup", "options": {"mode": "strict"}},
                {"id": "atlas.project_id_normalization", "options": {}},
            ],
        }
    )

    payload = plan.to_dict()

    assert [item.id for item in plan.fixes] == [
        "atlas.encoding_cleanup",
        "atlas.project_id_normalization",
    ]
    assert [item["id"] for item in payload["fixes"]] == [
        "atlas.encoding_cleanup",
        "atlas.project_id_normalization",
    ]
    assert payload["fixes"][0]["options"] == {"mode": "strict"}
    assert payload["id"] == "atlas.atlas_basic"
    assert "namespace" not in payload
    assert "local_id" not in payload


def test_fix_plan_identity_uses_identifier_set_when_prefix_and_local_available():
    plan = FixPlan(id="atlas.atlas_basic", fixes=[FixRef(id="atlas.encoding_cleanup")])

    assert plan.identifier_set is not None
    assert plan.identifier_set.namespace_prefix == "atlas"
    assert plan.identifier_set.local_id == "atlas_basic"
    assert plan.identifier_set.canonical_id == "atlas.atlas_basic"
    assert plan.namespace_prefix == "atlas"


def test_fix_plan_namespace_scopes_unqualified_fix_refs():
    plan = FixPlan.from_mapping(
        {
            "id": "atlas_plan",
            "namespace_prefix": "atlas",
            "fixes": [{"id": "encoding_cleanup"}],
        }
    )

    assert plan.namespace_prefix == "atlas"
    assert [item.id for item in plan.fixes] == ["atlas.encoding_cleanup"]


def test_fix_plan_runtime_metadata_provider_is_available_but_not_persisted():
    plan = FixPlan(
        id="cmip7.esa_cci_water_vapour_zarr",
        fixes=[FixRef(id="cmip7.configurable_reformat_bridge")],
        runtime_metadata=FixPlanRuntimeMetadata(
            provider=ProviderMetadata(name="woodpecker-cmip7-plugin", version="0.4.2")
        ),
    )

    runtime_payload = plan.runtime_metadata_dict()
    assert runtime_payload == {"provider": {"name": "woodpecker-cmip7-plugin", "version": "0.4.2"}}

    persisted = plan.to_dict()
    assert "runtime_metadata" not in persisted


def test_fix_plan_document_description_fields_are_parsed(tmp_path: Path):
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(
        json.dumps(
            {
                "plans": [
                    {
                        "id": "with-description",
                        "description": "Dataset selector note",
                        "fixes": [{"id": "CMIP6_0001", "options": {"message": "selector message"}}],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    document = load_fix_plan_document(plan_path)

    assert document.plans[0].description == "Dataset selector note"


def test_fix_plan_document_uses_explicit_schema_version_when_present(tmp_path: Path):
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "plans": [
                    {
                        "id": "atlas.basic",
                        "fixes": [{"id": "atlas.encoding_cleanup"}],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    document = load_fix_plan_document(plan_path)

    assert document.schema_version == 1
    assert document.plans[0].id == "atlas.basic"


def test_fix_plan_document_to_dict_includes_schema_version():
    document = FixPlanDocument(
        plans=[FixPlan(id="atlas.basic", fixes=[FixRef(id="atlas.encoding_cleanup")])]
    )

    payload = document.to_dict()

    assert payload["schema_version"] == 1
    assert payload["plans"][0]["id"] == "atlas.basic"


def test_esa_cci_example_fix_plan_uses_plugin_cmip7_fix_codes_in_order():
    plan_path = Path("examples/fix-plans/esa_cci.json")

    document = load_fix_plan_document(plan_path)
    assert len(document.plans) == 2

    ds = xr.Dataset()
    target = "/tmp/ESACCI-WATERVAPOUR-L3C-TCWV-meris-005deg-2002-2017-fv3.2.zarr"
    matched = [plan for plan in document.plans if plan_matches_dataset(plan, ds, path=target)]

    assert matched
    plan = matched[0]
    assert [plan.resolve_fix_identifier(item) for item in plan.fixes] == [
        "cmip7.configurable_reformat_bridge",
        "woodpecker.ensure_latitude_is_increasing",
    ]
