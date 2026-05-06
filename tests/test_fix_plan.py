import json
from pathlib import Path

import pytest
import xarray as xr

from woodpecker.fixes.registry import Fix, FixRegistry, register_fix
from woodpecker.plans.matcher import plan_matches_dataset
from woodpecker.plans.models import (
    FixPlan,
    FixPlanDocument,
    FixPlanRuntimeMetadata,
    FixRef,
    ProviderMetadata,
)
from woodpecker.runner import apply_fix_plan
from woodpecker.stores.json_store import JsonFixPlanStore
from woodpecker.testing import make_cmip6


class _FixMethodFix(Fix):
    prefix = "plan_test"
    suffix = "fix_method"
    name = "Plan fix method"
    description = ""
    categories = ["metadata"]
    priority = 10
    dataset = None

    def configure(self, config=None):
        self.config = dict(config or {})
        return self

    def matches(self, dataset):
        dataset.attrs.setdefault("trace", []).append(("matches", dict(getattr(self, "config", {}))))
        return True

    def apply(self, dataset, dry_run=True):
        dataset.attrs.setdefault("trace", []).append(
            ("apply", dict(getattr(self, "config", {})), dry_run)
        )
        return True


class _ApplyMethodFix(Fix):
    prefix = "plan_test"
    suffix = "apply_method"
    name = "Plan apply method"
    description = ""
    categories = ["metadata"]
    priority = 10
    dataset = None

    def configure(self, config=None):
        self.config = dict(config or {})
        return self

    def matches(self, dataset):
        dataset.attrs.setdefault("trace", []).append(("matches", dict(getattr(self, "config", {}))))
        return True

    def apply(self, dataset, dry_run=True):
        dataset.attrs.setdefault("trace", []).append(
            ("apply", dict(getattr(self, "config", {})), dry_run)
        )
        return True


class _TypeErrorInsideMethodFix(Fix):
    prefix = "plan_test"
    suffix = "type_error_inside_method"
    name = "Plan type error fix"
    description = ""
    categories = ["metadata"]
    priority = 10
    dataset = None

    def check(self, dataset):
        raise TypeError("check should not be called")

    def matches(self, dataset):
        return True

    def apply(self, dataset, dry_run=True):
        return True


def test_load_fix_plan_from_json(tmp_path: Path):
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(
        '{"id": "plan_test.default_plan", "steps": [{"id": "plan_test.fix_method", "options": {"mode": "fast"}}, "plan_test.apply_method"]}',
        encoding="utf-8",
    )

    plans = JsonFixPlanStore(plan_path).list_plans()
    plan = plans[0]

    assert isinstance(plan, FixPlan)
    assert [f.id for f in plan.steps] == ["plan_test.fix_method", "plan_test.apply_method"]
    assert plan.steps[0].options == {"mode": "fast"}
    assert plan.steps[1].options == {}


def test_load_fix_plan_from_yaml(tmp_path: Path):
    plan_path = tmp_path / "plan.yaml"
    plan_path.write_text(
        "id: plan_test.default_plan\nsteps:\n  - id: plan_test.fix_method\n    options:\n      level: strict\n",
        encoding="utf-8",
    )

    plans = JsonFixPlanStore(plan_path).list_plans()
    plan = plans[0]

    assert [f.id for f in plan.steps] == ["plan_test.fix_method"]
    assert plan.steps[0].options == {"level": "strict"}


def test_apply_plan_calls_matches_then_apply_and_passes_options():
    register_fix(_FixMethodFix)
    ds = make_cmip6()
    plan = FixPlan.model_validate(
        {
            "id": "plan_test.execution_order",
            "steps": [{"id": "plan_test.fix_method", "options": {"alpha": 1}}],
        }
    )

    apply_fix_plan(ds, plan, FixRegistry)

    assert ds.attrs["trace"] == [("matches", {"alpha": 1}), ("apply", {"alpha": 1}, False)]


def test_apply_plan_uses_apply_for_execution():
    register_fix(_ApplyMethodFix)
    ds = make_cmip6()
    plan = FixPlan.model_validate(
        {
            "id": "plan_test.apply_fallback",
            "steps": [{"id": "plan_test.apply_method", "options": {"beta": 2}}],
        }
    )

    apply_fix_plan(ds, plan, FixRegistry)

    assert ds.attrs["trace"] == [("matches", {"beta": 2}), ("apply", {"beta": 2}, False)]


def test_apply_plan_does_not_call_check():
    register_fix(_TypeErrorInsideMethodFix)
    ds = make_cmip6()
    plan = FixPlan.model_validate(
        {
            "id": "plan_test.type_error_passthrough",
            "steps": [{"id": "plan_test.type_error_inside_method", "options": {"gamma": 3}}],
        }
    )

    apply_fix_plan(ds, plan, FixRegistry)


def test_load_fix_plan_document_json(tmp_path: Path):
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(
        json.dumps(
            {
                "plans": [
                    {
                        "id": "cmip6.basic",
                        "description": "simple plan",
                        "match": {"path_patterns": ["*cmip6*.nc"]},
                        "steps": [{"id": "CMIP6_0001", "options": {"message": "ok"}}],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    document = FixPlanDocument(plans=JsonFixPlanStore(plan_path).list_plans())

    assert isinstance(document, FixPlanDocument)
    assert document.schema_version == 1
    assert len(document.plans) == 1
    assert document.plans[0].id == "cmip6.basic"
    assert document.plans[0].steps[0].id == "cmip6.cmip6_0001"


def test_load_fix_plan_document_single_plan_shorthand(tmp_path: Path):
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(
        json.dumps(
            {
                "id": "atlas.single",
                "steps": [{"id": "CMIP6_0001"}],
            }
        ),
        encoding="utf-8",
    )

    document = FixPlanDocument(plans=JsonFixPlanStore(plan_path).list_plans())

    assert document.schema_version == 1
    assert len(document.plans) == 1
    assert document.plans[0].id == "atlas.single"
    assert document.plans[0].steps[0].id == "atlas.cmip6_0001"


def test_load_fix_plan_document_plan_entries_normalize_fix_ids(tmp_path: Path):
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(
        json.dumps(
            {
                "plans": [
                    {
                        "id": "atlas.mixed_case",
                        "steps": [
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

    document = FixPlanDocument(plans=JsonFixPlanStore(plan_path).list_plans())

    fixes = document.plans[0].steps
    assert [item.id for item in fixes] == ["cmip6.dummy_placeholder", "atlas.encoding_cleanup"]
    assert fixes[0].options["marker_attr"] == "my_marker"


def test_fix_plan_to_dict_persists_canonical_ids_from_suffix_fix_refs():
    plan = FixPlan.model_validate(
        {
            "id": "atlas.atlas_basic",
            "steps": [
                {"id": "encoding_cleanup", "options": {"mode": "strict"}},
                {"id": "atlas.project_id_normalization", "options": {}},
            ],
        }
    )

    payload = plan.model_dump()

    assert [item.id for item in plan.steps] == [
        "atlas.encoding_cleanup",
        "atlas.project_id_normalization",
    ]
    assert [item["id"] for item in payload["steps"]] == [
        "atlas.encoding_cleanup",
        "atlas.project_id_normalization",
    ]
    assert payload["steps"][0]["options"] == {"mode": "strict"}
    assert payload["id"] == "atlas.atlas_basic"
    assert "namespace" not in payload
    assert "suffix" not in payload


def test_fix_plan_identity_uses_identifier_set_when_prefix_and_suffix_available():
    plan = FixPlan(id="atlas.atlas_basic", steps=[FixRef(id="atlas.encoding_cleanup")])

    assert plan.identifier_set is not None
    assert plan.identifier_set.prefix == "atlas"
    assert plan.identifier_set.suffix == "atlas_basic"
    assert plan.identifier_set.id == "atlas.atlas_basic"
    assert plan.prefix == "atlas"


def test_fix_plan_identity_can_be_built_from_prefix_and_suffix():
    plan = FixPlan.model_validate(
        {
            "prefix": "atlas",
            "suffix": "atlas_basic",
            "steps": [{"id": "encoding_cleanup"}],
        }
    )

    assert plan.id == "atlas.atlas_basic"
    assert plan.prefix == "atlas"
    assert plan.suffix == "atlas_basic"
    assert [item.id for item in plan.steps] == ["atlas.encoding_cleanup"]


def test_fix_plan_identity_can_scope_unqualified_id_with_prefix_alias():
    plan = FixPlan.model_validate(
        {
            "prefix": "atlas",
            "id": "atlas_basic",
            "steps": [{"id": "encoding_cleanup"}],
        }
    )

    assert plan.id == "atlas.atlas_basic"
    assert [item.id for item in plan.steps] == ["atlas.encoding_cleanup"]


def test_fix_plan_identity_persists_canonical_id_only():
    plan = FixPlan.model_validate(
        {
            "prefix": "atlas",
            "suffix": "atlas_basic",
            "steps": [{"id": "encoding_cleanup"}],
        }
    )

    payload = plan.model_dump()

    assert payload["id"] == "atlas.atlas_basic"
    assert "prefix" not in payload
    assert "suffix" not in payload


def test_fix_plan_identity_rejects_conflicting_explicit_parts():
    with pytest.raises(ValueError, match="suffix does not match"):
        FixPlan.model_validate(
            {
                "id": "atlas.basic",
                "suffix": "other",
                "steps": [{"id": "encoding_cleanup"}],
            }
        )


def test_fix_plan_identity_includes_aliases():
    plan = FixPlan(
        id="atlas.atlas_basic",
        aliases=["basic", "legacy.atlas_basic"],
        steps=[FixRef(id="atlas.encoding_cleanup")],
    )

    assert plan.aliases == ["basic", "atlas.basic", "legacy.atlas_basic"]
    assert plan.identifier_set.aliases == (
        "basic",
        "atlas.basic",
        "legacy.atlas_basic",
    )


def test_fix_plan_namespace_scopes_unqualified_fix_refs():
    plan = FixPlan.model_validate(
        {
            "id": "atlas.atlas_plan",
            "steps": [{"id": "encoding_cleanup"}],
        }
    )

    assert plan.prefix == "atlas"
    assert [item.id for item in plan.steps] == ["atlas.encoding_cleanup"]


def test_fix_plan_runtime_metadata_provider_is_available_but_not_persisted():
    plan = FixPlan(
        id="cmip7.esa_cci_water_vapour_zarr",
        steps=[FixRef(id="cmip7.configurable_reformat_bridge")],
        runtime_metadata=FixPlanRuntimeMetadata(
            provider=ProviderMetadata(name="woodpecker-cmip7-plugin", version="0.4.2")
        ),
    )

    runtime_payload = plan.runtime_metadata_dump()
    assert runtime_payload == {"provider": {"name": "woodpecker-cmip7-plugin", "version": "0.4.2"}}

    persisted = plan.model_dump()
    assert "runtime_metadata" not in persisted


def test_fix_plan_document_description_fields_are_parsed(tmp_path: Path):
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(
        json.dumps(
            {
                "plans": [
                    {
                        "id": "atlas.with_description",
                        "description": "Dataset selector note",
                        "steps": [{"id": "CMIP6_0001", "options": {"message": "selector message"}}],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    document = FixPlanDocument(plans=JsonFixPlanStore(plan_path).list_plans())

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
                        "steps": [{"id": "atlas.encoding_cleanup"}],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    document = FixPlanDocument(plans=JsonFixPlanStore(plan_path).list_plans())

    assert document.schema_version == 1
    assert document.plans[0].id == "atlas.basic"


def test_fix_plan_document_to_dict_includes_schema_version():
    document = FixPlanDocument(
        plans=[FixPlan(id="atlas.basic", steps=[FixRef(id="atlas.encoding_cleanup")])]
    )

    payload = document.model_dump()

    assert payload["schema_version"] == 1
    assert payload["plans"][0]["id"] == "atlas.basic"


def test_cmip7_plan_document_uses_plugin_fix_codes_in_order(tmp_path):
    plan_path = tmp_path / "fix-plans.json"
    plan_path.write_text(
        json.dumps(
            {
                "plans": [
                    {
                        "id": "cmip7.synthetic_reformat",
                        "match": {"path_patterns": ["*.zarr"]},
                        "steps": [
                            {"id": "cmip7.configurable_reformat_bridge"},
                            {"id": "woodpecker.ensure_latitude_is_increasing"},
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    document = FixPlanDocument(plans=JsonFixPlanStore(plan_path).list_plans())
    assert len(document.plans) == 1

    ds = xr.Dataset()
    target = "/tmp/CMIP7.CMIP.synthetic.case.zarr"
    matched = [plan for plan in document.plans if plan_matches_dataset(plan, ds, path=target)]

    assert matched
    plan = matched[0]
    assert [plan.resolve_fix_identifier(item) for item in plan.steps] == [
        "cmip7.configurable_reformat_bridge",
        "woodpecker.ensure_latitude_is_increasing",
    ]
