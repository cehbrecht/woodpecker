import json
from pathlib import Path
from typing import Callable

import pytest
from click.testing import CliRunner

from woodpecker.cli import cli
from woodpecker.testing import write_json, write_plan_document

pytestmark = pytest.mark.filterwarnings("ignore:.*Failed to read NetCDF input.*")
CliWorkspace = tuple[CliRunner, Callable[[str], Path]]

PLAN_COMMAND_CASES = [
    pytest.param("plans.json", True, ["check", "."], id="store-list-payload"),
    pytest.param("plan.json", False, ["check"], id="plan-document-payload"),
]


def _finding(message: str, *, path: str = "cmip6_bad.nc") -> dict[str, str]:
    return {
        "path": path,
        "fix_id": "woodpecker.normalize_tas_units_to_kelvin",
        "name": "Common check",
        "message": message,
    }


def _write_multiple_matching_plans(path: str, *, with_path_filters: bool) -> None:
    plans = [
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
        for plan in plans:
            plan["match"] = {"path_patterns": ["*cmip6_bad.nc"]}
        write_json(path, plans)
    else:
        write_plan_document(path, plans)


@pytest.mark.parametrize(
    ("plan_path", "with_path_filters", "command_prefix"),
    PLAN_COMMAND_CASES,
)
def test_check_plan_store_requires_plan_id_when_multiple_match(
    isolated_cli_workspace: CliWorkspace,
    plan_path,
    with_path_filters,
    command_prefix,
):
    runner, make_placeholder_netcdf_path = isolated_cli_workspace
    make_placeholder_netcdf_path("cmip6_bad.nc")
    _write_multiple_matching_plans(plan_path, with_path_filters=with_path_filters)

    result = runner.invoke(
        cli,
        [*command_prefix, "--plan", plan_path],
    )

    assert result.exit_code != 0
    assert "Multiple matching fix plans found" in result.output


@pytest.mark.parametrize(
    ("plan_path", "with_path_filters", "command_prefix"),
    PLAN_COMMAND_CASES,
)
def test_check_plan_store_plan_id_selects_specific_plan(
    isolated_cli_workspace: CliWorkspace,
    monkeypatch,
    plan_path,
    with_path_filters,
    command_prefix,
):
    runner, make_placeholder_netcdf_path = isolated_cli_workspace
    make_placeholder_netcdf_path("cmip6_bad.nc")
    _write_multiple_matching_plans(plan_path, with_path_filters=with_path_filters)

    def _fake_run_check(*args, **kwargs):
        _ = (args, kwargs)
        return [_finding("selected plan")]

    monkeypatch.setattr(
        "woodpecker.fix_plans.resolver._iter_store_matches",
        lambda inputs, store: store.list_plans(),
    )
    monkeypatch.setattr("woodpecker.cli.execute_check_context", _fake_run_check)

    result = runner.invoke(
        cli,
        [
            "check",
            *command_prefix[1:],
            "--plan",
            plan_path,
            "--plan-id",
            "test.selected_second",
        ],
    )

    assert result.exit_code == 1
    assert "woodpecker.normalize_tas_units_to_kelvin" in result.output


def test_check_plan_id_without_plan_errors(
    isolated_cli_workspace: CliWorkspace,
):
    runner, _ = isolated_cli_workspace

    result = runner.invoke(cli, ["check", ".", "--plan-id", "test.alpha"])

    assert result.exit_code != 0
    assert "--plan-id requires --plan" in result.output


def test_list_plans_text_output(
    isolated_cli_workspace: CliWorkspace,
):
    runner, _ = isolated_cli_workspace
    write_json(
        "plans.json",
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
        ["list-plans", "--plan", "plans.json"],
    )

    assert result.exit_code == 0
    assert "test.alpha: 1 step" in result.output
    assert "test.beta: 2 steps" in result.output


def test_list_plans_json_output(
    isolated_cli_workspace: CliWorkspace,
):
    runner, _ = isolated_cli_workspace
    write_json(
        "plans.json",
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
            "list-plans",
            "--plan",
            "plans.json",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert isinstance(payload, list)
    assert payload[0]["id"] == "test.alpha"


def test_list_plans_requires_store_options(
    isolated_cli_workspace: CliWorkspace,
):
    runner, _ = isolated_cli_workspace

    result = runner.invoke(cli, ["list-plans"])

    assert result.exit_code != 0
    assert "--plan is required" in result.output


def test_list_plans_auto_store_does_not_require_plan_location(
    isolated_cli_workspace: CliWorkspace,
):
    runner, _ = isolated_cli_workspace

    result = runner.invoke(cli, ["list-plans", "--store", "auto"])

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
        assert context.selected_plans[0].id == "woodpecker.normalize_tas_units_to_kelvin"
        return [_finding("selected auto plan")]

    monkeypatch.setattr("woodpecker.cli.execute_check_context", _fake_run_check)

    result = runner.invoke(
        cli,
        [
            "check",
            ".",
            "--store",
            "auto",
            "--plan-id",
            "woodpecker.normalize_tas_units_to_kelvin",
        ],
    )

    assert result.exit_code == 1
    assert "selected auto plan" in result.output


def test_load_plans_from_plan_document_into_json_store(
    isolated_cli_workspace: CliWorkspace,
):
    runner, _ = isolated_cli_workspace

    write_json(
        "plan-doc.json",
        {
            "plans": [
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
            "load-plans",
            "--plan",
            "target.json",
            "--from-plan",
            "plan-doc.json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(Path("target.json").read_text(encoding="utf-8"))
    assert [item["id"] for item in payload["plans"]] == ["test.alpha", "test.beta"]


def test_load_plans_from_store_with_plan_id_filter(
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
            "load-plans",
            "--plan",
            "target.json",
            "--from-plan",
            "source.json",
            "--from-store",
            "json",
            "--plan-id",
            "test.beta_alias",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    output = json.loads(result.output)
    assert output["loaded"] == 1
    assert output["plan_ids"] == ["test.beta"]
    payload = json.loads(Path("target.json").read_text(encoding="utf-8"))
    assert [item["id"] for item in payload["plans"]] == ["test.beta"]


def test_load_plans_from_auto_store_without_source_plan(
    isolated_cli_workspace: CliWorkspace,
):
    runner, _ = isolated_cli_workspace

    result = runner.invoke(
        cli,
        [
            "load-plans",
            "--plan",
            "target.json",
            "--from-store",
            "auto",
            "--plan-id",
            "woodpecker.tas_units_to_kelvin",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(Path("target.json").read_text(encoding="utf-8"))
    assert [item["id"] for item in payload["plans"]] == ["woodpecker.normalize_tas_units_to_kelvin"]


def test_load_plans_requires_source_plan_location(
    isolated_cli_workspace: CliWorkspace,
):
    runner, _ = isolated_cli_workspace

    result = runner.invoke(
        cli,
        [
            "load-plans",
            "--plan",
            "target.json",
        ],
    )

    assert result.exit_code != 0
    assert "Provide --from-plan as the source store location" in result.output
