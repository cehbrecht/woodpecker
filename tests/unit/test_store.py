from __future__ import annotations

from pathlib import Path

import pytest
import xarray as xr

from woodpecker.plans.matcher import plan_matches_dataset
from woodpecker.plans.models import DatasetMatcher, FixPlan, FixRef
from woodpecker.stores import DuckDBFixPlanStore, JsonFixPlanStore
from woodpecker.testing import make_atlas, make_cmip6

UNKNOWN_PLAN_ID_ERROR = "Unknown plan identifier"


def _sample_plan() -> FixPlan:
    return FixPlan(
        id="tests.plan_1",
        description="sample plan",
        match=DatasetMatcher(
            attrs={"project_id": "CMIP6", "table_id": "Amon"},
            path_patterns=["*cmip6*.nc"],
        ),
        steps=[
            FixRef(id="woodpecker.normalize_tas_units_to_kelvin", options={"mode": "fast"}),
            FixRef(id="woodpecker.ensure_latitude_is_increasing"),
        ],
    )


def _single_step_plan(
    plan_id: str,
    fix_id: str = "woodpecker.remove_coordinate_fill_value_encodings",
    *,
    match: DatasetMatcher | None = None,
    description: str | None = None,
) -> FixPlan:
    kwargs = {"id": plan_id, "steps": [FixRef(id=fix_id)]}
    if match is not None:
        kwargs["match"] = match
    if description is not None:
        kwargs["description"] = description
    return FixPlan(**kwargs)


def _json_store(tmp_path: Path) -> JsonFixPlanStore:
    return JsonFixPlanStore(tmp_path / "fix-plans.json")


def _duckdb_store(tmp_path: Path) -> DuckDBFixPlanStore:
    pytest.importorskip("duckdb")
    return DuckDBFixPlanStore(tmp_path / "fix-plans.duckdb")


STORE_FACTORIES = [
    pytest.param(_json_store, id="json-store"),
    pytest.param(_duckdb_store, id="duckdb-store"),
]


def _assert_lookup_ids(store, dataset: xr.Dataset, *, path: str, expected_ids: list[str]) -> None:
    matched = store.lookup(dataset, path=path)
    assert [item.id for item in matched] == expected_ids


# Serialization and matcher behavior


def test_fix_plan_serialization_roundtrip():
    plan = _sample_plan()

    payload = plan.model_dump_json()
    restored = FixPlan.model_validate_json(payload)

    assert restored == plan
    assert restored.steps[0].id == "woodpecker.normalize_tas_units_to_kelvin"
    assert restored.steps[0].options == {"mode": "fast"}


def test_plan_matcher_requires_both_attrs_and_path_when_both_defined():
    plan = _sample_plan()
    ds = make_cmip6()

    assert plan_matches_dataset(plan, ds, path="/tmp/data/cmip6_case.nc") is True
    assert plan_matches_dataset(plan, ds, path="/tmp/data/other_case.nc") is False


def test_plan_matcher_general_applicability_without_matcher():
    plan = FixPlan(
        id="tests.plan_any", steps=[FixRef(id="woodpecker.normalize_tas_units_to_kelvin")]
    )
    ds = xr.Dataset(attrs={"anything": "value"})

    assert plan_matches_dataset(plan, ds) is True


def test_plan_matcher_attrs_only():
    plan = FixPlan(
        id="tests.plan_attrs",
        match=DatasetMatcher(attrs={"project_id": "CMIP7"}),
        steps=[FixRef(id="cmip7.ensure_project_id_present")],
    )

    assert plan_matches_dataset(plan, xr.Dataset(attrs={"project_id": "CMIP7"})) is True
    assert plan_matches_dataset(plan, make_cmip6()) is False


def test_plan_matcher_path_only():
    plan = FixPlan(
        id="tests.plan_path",
        match=DatasetMatcher(path_patterns=["*.zarr", "*decadal*.nc"]),
        steps=[FixRef(id="woodpecker.ensure_latitude_is_increasing")],
    )
    ds = xr.Dataset()

    assert plan_matches_dataset(plan, ds, path="/tmp/case.zarr") is True
    assert plan_matches_dataset(plan, ds, path="/tmp/c3s-decadal.nc") is True
    assert plan_matches_dataset(plan, ds, path="/tmp/case.nc") is False
    assert plan_matches_dataset(plan, ds, path=None) is False


@pytest.mark.parametrize(
    ("filename", "schema_marker"),
    [
        ("fix-plans.json", '"schema_version": 1'),
        ("fix-plans.yaml", "schema_version: 1"),
    ],
)
def test_json_store_save_list_lookup(tmp_path, filename, schema_marker):
    store = JsonFixPlanStore(tmp_path / filename)
    plan_1 = _sample_plan()
    plan_2 = _single_step_plan("tests.plan_2")

    store.save_plan(plan_1)
    store.save_plan(plan_2)

    raw = store.path.read_text(encoding="utf-8")
    assert schema_marker in raw

    listed = store.list_plans()
    assert [item.id for item in listed] == ["tests.plan_1", "tests.plan_2"]

    ds = make_cmip6()
    _assert_lookup_ids(
        store,
        ds,
        path="/tmp/cmip6_case.nc",
        expected_ids=["tests.plan_1", "tests.plan_2"],
    )
    _assert_lookup_ids(store, ds, path="/tmp/no-match.txt", expected_ids=["tests.plan_2"])


# JSON store behavior


def test_json_store_lookup_matches_atlas_fixture(tmp_path):
    store = JsonFixPlanStore(tmp_path / "fix-plans.json")
    atlas_plan = _single_step_plan(
        "atlas.lookup",
        "atlas.encoding_cleanup",
        match=DatasetMatcher(
            attrs={"project_id": "C3S-Atlas"},
            path_patterns=["*atlas*.nc"],
        ),
    )
    catchall_plan = _single_step_plan("tests.catchall")

    store.save_plan(atlas_plan)
    store.save_plan(catchall_plan)

    matched = store.lookup(make_atlas(), path="/tmp/atlas_case.nc")

    assert [item.id for item in matched] == ["atlas.lookup", "tests.catchall"]


def test_json_store_save_replaces_existing_plan_id(tmp_path):
    store = JsonFixPlanStore(tmp_path / "fix-plans.json")

    store.save_plan(
        _single_step_plan(
            "tests.plan_1",
            "woodpecker.normalize_tas_units_to_kelvin",
            description="old",
        )
    )
    store.save_plan(
        _single_step_plan(
            "tests.plan_1",
            "woodpecker.ensure_latitude_is_increasing",
            description="new",
        )
    )

    listed = store.list_plans()
    assert len(listed) == 1
    assert listed[0].description == "new"
    assert listed[0].steps[0].id == "woodpecker.ensure_latitude_is_increasing"


def test_json_store_save_upserts_by_plan_id(tmp_path):
    store = JsonFixPlanStore(tmp_path / "fix-plans.json")

    store.save_plan(
        FixPlan(
            id="atlas.cleanup_plan",
            description="old",
            steps=[FixRef(id="atlas.encoding_cleanup")],
        )
    )
    store.save_plan(
        FixPlan(
            id="atlas.cleanup_plan",
            description="new",
            steps=[FixRef(id="atlas.project_id_normalization")],
        )
    )

    listed = store.list_plans()
    assert len(listed) == 1
    assert listed[0].id == "atlas.cleanup_plan"
    assert listed[0].description == "new"


def test_json_store_save_normalizes_prefix_and_suffix_plan_id(tmp_path):
    store = JsonFixPlanStore(tmp_path / "fix-plans.json")
    store.save_plan(
        FixPlan.model_validate(
            {
                "prefix": "atlas",
                "suffix": "cleanup_plan",
                "steps": [{"id": "encoding_cleanup"}],
            }
        )
    )

    listed = store.list_plans()
    raw = store.path.read_text(encoding="utf-8")

    assert listed[0].id == "atlas.cleanup_plan"
    assert listed[0].steps[0].id == "atlas.encoding_cleanup"
    assert '"id": "atlas.cleanup_plan"' in raw
    assert "suffix" not in raw


@pytest.mark.parametrize("store_factory", STORE_FACTORIES)
def test_store_get_plan_resolves_id(tmp_path, store_factory):
    store = store_factory(tmp_path)
    plan = FixPlan(id="atlas.cleanup_plan", steps=[FixRef(id="atlas.encoding_cleanup")])
    store.save_plan(plan)

    by_id = store.get_plan("atlas.cleanup_plan")
    assert by_id.id == "atlas.cleanup_plan"

    with pytest.raises(ValueError, match=UNKNOWN_PLAN_ID_ERROR):
        store.get_plan("cleanup_plan")


@pytest.mark.parametrize("store_factory", STORE_FACTORIES)
def test_store_get_plan_resolves_aliases(tmp_path, store_factory):
    store = store_factory(tmp_path)
    plan = FixPlan(
        id="atlas.cleanup_plan",
        aliases=["cleanup", "legacy.cleanup_plan"],
        steps=[FixRef(id="atlas.encoding_cleanup")],
    )
    store.save_plan(plan)

    by_qualified_alias = store.get_plan("atlas.cleanup")
    by_legacy_alias = store.get_plan("legacy.cleanup_plan")

    assert by_qualified_alias.id == "atlas.cleanup_plan"
    assert by_legacy_alias.id == "atlas.cleanup_plan"

    with pytest.raises(ValueError, match=UNKNOWN_PLAN_ID_ERROR):
        store.get_plan("cleanup")


def test_json_store_get_plan_rejects_unqualified_suffix(tmp_path):
    store = JsonFixPlanStore(tmp_path / "fix-plans.json")
    store.save_plan(
        FixPlan(id="alpha.shared", steps=[FixRef(id="woodpecker.ensure_latitude_is_increasing")])
    )
    store.save_plan(
        FixPlan(id="beta.shared", steps=[FixRef(id="woodpecker.normalize_tas_units_to_kelvin")])
    )

    with pytest.raises(ValueError, match=UNKNOWN_PLAN_ID_ERROR):
        store.get_plan("shared")


def test_json_store_get_plan_detects_duplicate_ids(tmp_path):
    store = JsonFixPlanStore(tmp_path / "fix-plans.json")
    store.path.write_text(
        '{"plans": [{"id": "atlas.cleanup_plan", "steps": [{"id": "atlas.encoding_cleanup"}]}, {"id": "atlas.cleanup_plan", "steps": [{"id": "atlas.project_id_normalization"}]}]}',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Duplicate plan id detected"):
        store.get_plan("atlas.cleanup_plan")


# DuckDB store behavior


def test_duckdb_store_save_list_lookup(tmp_path):
    store = _duckdb_store(tmp_path)
    plan_1 = _sample_plan()
    plan_2 = _single_step_plan("tests.plan_2")

    store.save_plan(plan_1)
    store.save_plan(plan_2)

    listed = store.list_plans()
    assert [item.id for item in listed] == ["tests.plan_1", "tests.plan_2"]

    ds = make_cmip6()
    _assert_lookup_ids(
        store,
        ds,
        path="/tmp/cmip6_case.nc",
        expected_ids=["tests.plan_1", "tests.plan_2"],
    )
    _assert_lookup_ids(store, ds, path="/tmp/no-match.txt", expected_ids=["tests.plan_2"])


def test_duckdb_lookup_skips_decoding_nonmatching_fixes_payload(tmp_path):
    duckdb = pytest.importorskip("duckdb")

    db_path = tmp_path / "fix-plans.duckdb"
    store = DuckDBFixPlanStore(db_path)
    store.save_plan(
        FixPlan(
            id="atlas.lookup_atlas",
            match=DatasetMatcher(path_patterns=["*atlas*.nc"]),
            steps=[FixRef(id="atlas.encoding_cleanup")],
        )
    )
    store.save_plan(
        FixPlan(
            id="cmip6.lookup_cmip6",
            match=DatasetMatcher(path_patterns=["*cmip6*.nc"]),
            steps=[FixRef(id="cmip6.dummy_placeholder")],
        )
    )

    # Corrupt a non-matching row to verify lookup does not decode its steps payload.
    with duckdb.connect(str(db_path)) as con:
        con.execute(
            "UPDATE fix_plans SET steps_json = ? WHERE id = ?",
            ["not-json", "cmip6.lookup_cmip6"],
        )

    matched = store.lookup(xr.Dataset(), path="/tmp/atlas_case.nc")
    assert [item.id for item in matched] == ["atlas.lookup_atlas"]


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
