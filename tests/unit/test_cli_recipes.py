import json
from pathlib import Path
from typing import Callable

import pytest
from click.testing import CliRunner

from woodpecker.cli import cli
from woodpecker.testing import write_json, write_recipe_document

pytestmark = pytest.mark.filterwarnings("ignore:.*Failed to read NetCDF input.*")
CliWorkspace = tuple[CliRunner, Callable[[str], Path]]

PLAN_COMMAND_CASES = [
    pytest.param("recipes.json", True, ["check", "."], id="store-list-payload"),
    pytest.param("recipe.json", False, ["check"], id="recipe-document-payload"),
]


def _finding(message: str, *, path: str = "cmip6_bad.nc") -> dict[str, str]:
    return {
        "path": path,
        "fix_id": "woodpecker.normalize_tas_units_to_kelvin",
        "name": "Common check",
        "message": message,
    }


def _write_multiple_matching_plans(path: str, *, with_path_filters: bool) -> None:
    recipes = [
        {
            "id": "test.first",
            "aliases": ["selected_first"],
            "steps": [{"id": "woodpecker.ensure_latitude_is_increasing"}],
        },
        {
            "id": "test.second",
            "aliases": ["selected_second"],
            "steps": [{"id": "woodpecker.normalize_tas_units_to_kelvin"}],
        },
    ]
    if with_path_filters:
        for recipe in recipes:
            recipe["match"] = {"path_patterns": ["*cmip6_bad.nc"]}
        write_json(path, recipes)
    else:
        write_recipe_document(path, recipes)


@pytest.mark.parametrize(
    ("recipe_path", "with_path_filters", "command_prefix"),
    PLAN_COMMAND_CASES,
)
def test_check_recipe_store_requires_recipe_id_when_multiple_match(
    isolated_cli_workspace: CliWorkspace,
    recipe_path,
    with_path_filters,
    command_prefix,
):
    runner, make_placeholder_netcdf_path = isolated_cli_workspace
    make_placeholder_netcdf_path("cmip6_bad.nc")
    _write_multiple_matching_plans(recipe_path, with_path_filters=with_path_filters)

    result = runner.invoke(
        cli,
        [*command_prefix, "--recipe", recipe_path],
    )

    assert result.exit_code != 0
    assert "Multiple matching recipes found" in result.output


@pytest.mark.parametrize(
    ("recipe_path", "with_path_filters", "command_prefix"),
    PLAN_COMMAND_CASES,
)
def test_check_recipe_store_recipe_id_selects_specific_plan(
    isolated_cli_workspace: CliWorkspace,
    monkeypatch,
    recipe_path,
    with_path_filters,
    command_prefix,
):
    runner, make_placeholder_netcdf_path = isolated_cli_workspace
    make_placeholder_netcdf_path("cmip6_bad.nc")
    _write_multiple_matching_plans(recipe_path, with_path_filters=with_path_filters)

    def _fake_run_check(*args, **kwargs):
        _ = (args, kwargs)
        return [_finding("selected recipe")]

    monkeypatch.setattr(
        "woodpecker.recipes.resolver._iter_store_matches",
        lambda inputs, store: store.list_recipes(),
    )
    monkeypatch.setattr("woodpecker.cli.execute_check_context", _fake_run_check)

    result = runner.invoke(
        cli,
        [
            "check",
            *command_prefix[1:],
            "--recipe",
            recipe_path,
            "--recipe-id",
            "test.selected_second",
        ],
    )

    assert result.exit_code == 1
    assert "woodpecker.normalize_tas_units_to_kelvin" in result.output


def test_check_recipe_id_without_plan_uses_discovered_catalog(
    isolated_cli_workspace: CliWorkspace,
):
    runner, _ = isolated_cli_workspace

    result = runner.invoke(cli, ["check", ".", "--recipe-id", "test.alpha"])

    assert result.exit_code != 0
    assert "Unknown recipe identifier: test.alpha" in result.output


def test_list_recipes_text_output(
    isolated_cli_workspace: CliWorkspace,
):
    runner, _ = isolated_cli_workspace
    write_json(
        "recipes.json",
        [
            {
                "id": "test.alpha",
                "steps": [{"id": "woodpecker.normalize_tas_units_to_kelvin"}],
            },
            {
                "id": "test.beta",
                "steps": [
                    {"id": "woodpecker.ensure_latitude_is_increasing"},
                    {"id": "woodpecker.remove_coordinate_fill_value_encodings"},
                ],
            },
        ],
    )

    result = runner.invoke(
        cli,
        ["list-recipes", "--recipe", "recipes.json"],
    )

    assert result.exit_code == 0
    assert "test.alpha: 1 step" in result.output
    assert "test.beta: 2 steps" in result.output


def test_list_recipes_json_output(
    isolated_cli_workspace: CliWorkspace,
):
    runner, _ = isolated_cli_workspace
    write_json(
        "recipes.json",
        [
            {
                "id": "test.alpha",
                "steps": [{"id": "woodpecker.normalize_tas_units_to_kelvin"}],
            }
        ],
    )

    result = runner.invoke(
        cli,
        [
            "list-recipes",
            "--recipe",
            "recipes.json",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert isinstance(payload, list)
    assert payload[0]["id"] == "test.alpha"


def test_list_recipes_defaults_to_discovered_catalog(
    isolated_cli_workspace: CliWorkspace,
):
    runner, _ = isolated_cli_workspace

    result = runner.invoke(cli, ["list-recipes"])

    assert result.exit_code == 0
    assert "cmip6.core_units: 1 step" in result.output
    assert "xmip.cmip6_preprocessing:" in result.output


def test_list_recipes_auto_store_does_not_require_recipe_location(
    isolated_cli_workspace: CliWorkspace,
):
    runner, _ = isolated_cli_workspace

    result = runner.invoke(cli, ["list-recipes", "--store", "auto"])

    assert result.exit_code == 0
    assert "woodpecker.normalize_tas_units_to_kelvin: 1 step" in result.output


def test_check_auto_store_uses_matching_registered_fix(
    isolated_cli_workspace: CliWorkspace,
    monkeypatch,
):
    runner, make_placeholder_netcdf_path = isolated_cli_workspace
    make_placeholder_netcdf_path("cmip6_bad.nc")

    def _fake_run_check(context, **kwargs):
        _ = kwargs
        assert context.selected_recipes[0].id == "woodpecker.normalize_tas_units_to_kelvin"
        return [_finding("selected auto recipe")]

    monkeypatch.setattr("woodpecker.cli.execute_check_context", _fake_run_check)

    result = runner.invoke(
        cli,
        [
            "check",
            ".",
            "--store",
            "auto",
            "--recipe-id",
            "woodpecker.normalize_tas_units_to_kelvin",
        ],
    )

    assert result.exit_code == 1
    assert "selected auto recipe" in result.output


def test_load_recipes_from_recipe_document_into_json_store(
    isolated_cli_workspace: CliWorkspace,
):
    runner, _ = isolated_cli_workspace

    write_json(
        "recipe-doc.json",
        {
            "recipes": [
                {
                    "id": "test.alpha",
                    "steps": [{"id": "woodpecker.normalize_tas_units_to_kelvin"}],
                },
                {
                    "id": "test.beta",
                    "steps": [{"id": "woodpecker.ensure_latitude_is_increasing"}],
                },
            ]
        },
    )

    result = runner.invoke(
        cli,
        [
            "load-recipes",
            "--recipe",
            "target.json",
            "--from-recipe",
            "recipe-doc.json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(Path("target.json").read_text(encoding="utf-8"))
    assert [item["id"] for item in payload["recipes"]] == ["test.alpha", "test.beta"]


def test_load_recipes_from_store_with_recipe_id_filter(
    isolated_cli_workspace: CliWorkspace,
):
    runner, _ = isolated_cli_workspace

    write_json(
        "source.json",
        [
            {"id": "test.alpha", "steps": [{"id": "woodpecker.normalize_tas_units_to_kelvin"}]},
            {
                "id": "test.beta",
                "aliases": ["beta_alias"],
                "steps": [{"id": "woodpecker.ensure_latitude_is_increasing"}],
            },
        ],
    )

    result = runner.invoke(
        cli,
        [
            "load-recipes",
            "--recipe",
            "target.json",
            "--from-recipe",
            "source.json",
            "--from-store",
            "json",
            "--recipe-id",
            "test.beta_alias",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    output = json.loads(result.output)
    assert output["loaded"] == 1
    assert output["recipe_ids"] == ["test.beta"]
    payload = json.loads(Path("target.json").read_text(encoding="utf-8"))
    assert [item["id"] for item in payload["recipes"]] == ["test.beta"]


def test_load_recipes_from_auto_store_without_source_plan(
    isolated_cli_workspace: CliWorkspace,
):
    runner, _ = isolated_cli_workspace

    result = runner.invoke(
        cli,
        [
            "load-recipes",
            "--recipe",
            "target.json",
            "--from-store",
            "auto",
            "--recipe-id",
            "woodpecker.tas_units_to_kelvin",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(Path("target.json").read_text(encoding="utf-8"))
    assert [item["id"] for item in payload["recipes"]] == ["woodpecker.normalize_tas_units_to_kelvin"]


def test_load_recipes_requires_source_recipe_location(
    isolated_cli_workspace: CliWorkspace,
):
    runner, _ = isolated_cli_workspace

    result = runner.invoke(
        cli,
        [
            "load-recipes",
            "--recipe",
            "target.json",
        ],
    )

    assert result.exit_code != 0
    assert "Provide --from-recipe as the source store location" in result.output
