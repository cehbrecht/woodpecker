from __future__ import annotations

import pytest
import xarray as xr

from woodpecker.plans.matcher import plan_matches_dataset
from woodpecker.plans.models import DatasetMatcher, FixPlan, FixRef
from woodpecker.stores import DuckDBFixPlanStore, JsonFixPlanStore


def _sample_plan() -> FixPlan:
    return FixPlan(
        id="plan-1",
        description="sample plan",
        match=DatasetMatcher(
            attrs={"project_id": "CMIP6", "table_id": "Amon"},
            path_patterns=["*cmip6*.nc"],
        ),
        fixes=[
            FixRef(id="woodpecker.normalize_tas_units_to_kelvin", options={"mode": "fast"}),
            FixRef(id="woodpecker.ensure_latitude_is_increasing"),
        ],
    )


def test_fix_plan_serialization_roundtrip():
    plan = _sample_plan()

    payload = plan.to_json()
    restored = FixPlan.from_json(payload)

    assert restored == plan
    assert restored.fixes[0].id == "woodpecker.normalize_tas_units_to_kelvin"
    assert restored.fixes[0].options == {"mode": "fast"}


def test_plan_matcher_requires_both_attrs_and_path_when_both_defined():
    plan = _sample_plan()
    ds = xr.Dataset(attrs={"project_id": "CMIP6", "table_id": "Amon"})

    assert plan_matches_dataset(plan, ds, path="/tmp/data/cmip6_case.nc") is True
    assert plan_matches_dataset(plan, ds, path="/tmp/data/other_case.nc") is False


def test_plan_matcher_general_applicability_without_matcher():
    plan = FixPlan(id="plan-any", fixes=[FixRef(id="woodpecker.normalize_tas_units_to_kelvin")])
    ds = xr.Dataset(attrs={"anything": "value"})

    assert plan_matches_dataset(plan, ds) is True


def test_plan_matcher_attrs_only():
    plan = FixPlan(
        id="plan-attrs",
        match=DatasetMatcher(attrs={"project_id": "CMIP7"}),
        fixes=[FixRef(id="CMIP7_0001")],
    )

    assert plan_matches_dataset(plan, xr.Dataset(attrs={"project_id": "CMIP7"})) is True
    assert plan_matches_dataset(plan, xr.Dataset(attrs={"project_id": "CMIP6"})) is False


def test_plan_matcher_path_only():
    plan = FixPlan(
        id="plan-path",
        match=DatasetMatcher(path_patterns=["*.zarr", "*decadal*.nc"]),
        fixes=[FixRef(id="woodpecker.ensure_latitude_is_increasing")],
    )
    ds = xr.Dataset()

    assert plan_matches_dataset(plan, ds, path="/tmp/case.zarr") is True
    assert plan_matches_dataset(plan, ds, path="/tmp/c3s-decadal.nc") is True
    assert plan_matches_dataset(plan, ds, path="/tmp/case.nc") is False
    assert plan_matches_dataset(plan, ds, path=None) is False


def test_json_store_save_list_lookup(tmp_path):
    store = JsonFixPlanStore(tmp_path / "fix-plans.json")
    plan_1 = _sample_plan()
    plan_2 = FixPlan(id="plan-2", fixes=[FixRef(id="woodpecker.remove_coordinate_fill_value_encodings")])

    store.save_plan(plan_1)
    store.save_plan(plan_2)

    listed = store.list_plans()
    assert [item.id for item in listed] == ["plan-1", "plan-2"]

    ds = xr.Dataset(attrs={"project_id": "CMIP6", "table_id": "Amon"})
    matched = store.lookup(ds, path="/tmp/cmip6_case.nc")
    assert [item.id for item in matched] == ["plan-1", "plan-2"]

    matched = store.lookup(ds, path="/tmp/no-match.txt")
    assert [item.id for item in matched] == ["plan-2"]


def test_json_store_save_replaces_existing_plan_id(tmp_path):
    store = JsonFixPlanStore(tmp_path / "fix-plans.json")

    store.save_plan(FixPlan(id="plan-1", description="old", fixes=[FixRef(id="woodpecker.normalize_tas_units_to_kelvin")]))
    store.save_plan(FixPlan(id="plan-1", description="new", fixes=[FixRef(id="woodpecker.ensure_latitude_is_increasing")]))

    listed = store.list_plans()
    assert len(listed) == 1
    assert listed[0].description == "new"
    assert listed[0].fixes[0].id == "woodpecker.ensure_latitude_is_increasing"


def test_duckdb_store_save_list_lookup(tmp_path):
    pytest.importorskip("duckdb")

    store = DuckDBFixPlanStore(tmp_path / "fix-plans.duckdb")
    plan_1 = _sample_plan()
    plan_2 = FixPlan(id="plan-2", fixes=[FixRef(id="woodpecker.remove_coordinate_fill_value_encodings")])

    store.save_plan(plan_1)
    store.save_plan(plan_2)

    listed = store.list_plans()
    assert [item.id for item in listed] == ["plan-1", "plan-2"]

    ds = xr.Dataset(attrs={"project_id": "CMIP6", "table_id": "Amon"})
    matched = store.lookup(ds, path="/tmp/cmip6_case.nc")
    assert [item.id for item in matched] == ["plan-1", "plan-2"]

    matched = store.lookup(ds, path="/tmp/no-match.txt")
    assert [item.id for item in matched] == ["plan-2"]


def test_duckdb_candidate_query_builds_attr_prefilter(tmp_path):
    pytest.importorskip("duckdb")

    store = DuckDBFixPlanStore(tmp_path / "fix-plans.duckdb")
    ds = xr.Dataset(attrs={"project_id": "CMIP6", "table_id": "Amon"})

    sql, params = store._candidate_query(ds)

    assert sql.startswith("SELECT id, description, match_json, fixes_json FROM fix_plans")
    assert "$.attrs.project_id" in sql
    assert "$.attrs.table_id" in sql
    assert "ORDER BY id" in sql
    assert params == ["CMIP6", "Amon"]


def test_duckdb_lookup_skips_decoding_nonmatching_fixes_payload(tmp_path):
    duckdb = pytest.importorskip("duckdb")

    db_path = tmp_path / "fix-plans.duckdb"
    store = DuckDBFixPlanStore(db_path)
    store.save_plan(
        FixPlan(
            id="atlas",
            match=DatasetMatcher(path_patterns=["*atlas*.nc"]),
            fixes=[FixRef(id="ATLAS_0001")],
        )
    )
    store.save_plan(
        FixPlan(
            id="cmip6",
            match=DatasetMatcher(path_patterns=["*cmip6*.nc"]),
            fixes=[FixRef(id="CMIP6_0001")],
        )
    )

    # Corrupt a non-matching row to verify lookup does not decode its fixes payload.
    with duckdb.connect(str(db_path)) as con:
        con.execute("UPDATE fix_plans SET fixes_json = ? WHERE id = ?", ["not-json", "cmip6"])

    matched = store.lookup(xr.Dataset(), path="/tmp/atlas_case.nc")
    assert [item.id for item in matched] == ["atlas"]


def test_duckdb_store_raises_clear_error_when_dependency_missing(tmp_path, monkeypatch):
    import builtins

    real_import = builtins.__import__

    def _fake_import(name, *args, **kwargs):
        if name == "duckdb":
            raise ImportError("duckdb not installed")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _fake_import)

    with pytest.raises(RuntimeError, match="requires optional dependency 'duckdb'"):
        DuckDBFixPlanStore(tmp_path / "missing.duckdb")
