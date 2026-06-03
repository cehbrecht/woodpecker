import json
from pathlib import Path

from woodpecker import check, fix, recipe

CORE_FIX_IDS = {
    "woodpecker.normalize_tas_units_to_kelvin",
    "woodpecker.ensure_latitude_is_increasing",
    "woodpecker.remove_coordinate_fill_value_encodings",
    "woodpecker.merge_equivalent_dimensions",
}


def write_recipe_document(path: Path, recipes: list[dict]) -> Path:
    path.write_text(json.dumps({"recipes": recipes}), encoding="utf-8")
    return path


def unique_in_order(values) -> tuple[str, ...]:
    out = []
    for value in values:
        if value not in out:
            out.append(value)
    return tuple(out)


def check_finding_ids(dataset, fix_id: str, *, fix_options=None) -> set[str]:
    result = check(
        dataset,
        fixes=fix_id,
        options=fix_options,
    )
    return set(result.fix_ids)


def assert_no_core_fixes_reported(dataset) -> None:
    assert not check(dataset, fixes=sorted(CORE_FIX_IDS))


def assert_fix_dry_run_reports_change(dataset, fix_id: str, *, fix_options=None) -> None:
    result = fix(dataset, fixes=fix_id, options=fix_options, dry_run=True)

    assert result.attempted == 1
    assert result.changed == 1
    assert result.persist_attempted == 0
    assert result.persisted == 0
    assert result.failed == 0
    assert len(result.preview) == 1
    assert result.preview[0]["fix_id"] == fix_id
    assert result.preview[0]["changed"] is True


def assert_fix_write_reports_change(dataset, fix_id: str, *, fix_options=None) -> None:
    result = fix(dataset, fixes=fix_id, options=fix_options, dry_run=False)

    assert result.attempted == 1
    assert result.changed == 1
    assert result.persist_attempted == 1
    assert result.persisted == 1
    assert result.failed == 0


def assert_check_fix_cycle(
    dataset,
    fix_id: str,
    *,
    assert_fixed,
    assert_unchanged=None,
    fix_options=None,
) -> None:
    """Exercise the public API from finding through dry-run, write, and re-check."""
    assert check_finding_ids(dataset, fix_id, fix_options=fix_options) == {fix_id}

    assert_fix_dry_run_reports_change(dataset, fix_id, fix_options=fix_options)
    if assert_unchanged is not None:
        assert_unchanged(dataset)

    assert_fix_write_reports_change(dataset, fix_id, fix_options=fix_options)
    assert_fixed(dataset)

    assert check_finding_ids(dataset, fix_id, fix_options=fix_options) == set()


def assert_plan_check_fix_cycle(
    recipe_source,
    dataset,
    *,
    expected_fix_ids: tuple[str, ...],
    expected_changed: int,
    assert_fixed,
    assert_unchanged=None,
    recipe_id: str | None = None,
) -> None:
    """Exercise the recipe API from finding through dry-run, write, and re-check."""
    findings = recipe.check(dataset, recipe_source, recipe_id=recipe_id)

    assert unique_in_order(findings.fix_ids) == expected_fix_ids

    preview = recipe.fix(dataset, recipe_source, dry_run=True, recipe_id=recipe_id)
    assert preview.changed == expected_changed
    assert preview.persisted == 0
    if assert_unchanged is not None:
        assert_unchanged(dataset)

    write = recipe.fix(dataset, recipe_source, dry_run=False, recipe_id=recipe_id)
    assert write.changed == expected_changed
    assert write.persisted == 1
    assert_fixed(dataset)

    assert not recipe.check(dataset, recipe_source, recipe_id=recipe_id)
