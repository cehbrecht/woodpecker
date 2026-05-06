import json
from pathlib import Path
from typing import Callable

import pytest
from click.testing import CliRunner

from woodpecker.cli import cli

pytestmark = pytest.mark.filterwarnings("ignore:.*Failed to read NetCDF input.*")


def _finding(message: str, *, path: str = "cmip6_bad.nc") -> dict[str, str]:
    return {
        "path": path,
        "fix_id": "woodpecker.normalize_tas_units_to_kelvin",
        "name": "Common check",
        "message": message,
    }


def _successful_fix_stats() -> dict[str, int]:
    return {
        "attempted": 1,
        "changed": 1,
        "persist_attempted": 1,
        "persisted": 1,
        "persist_failed": 0,
    }


def _write_json(path: str, payload) -> None:
    Path(path).write_text(json.dumps(payload), encoding="utf-8")


def _write_plan_document(path: str, plans: list[dict]) -> None:
    _write_json(path, {"plans": plans})


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
        _write_json(path, plans)
    else:
        _write_plan_document(path, plans)


@pytest.mark.parametrize(
    ("plan_path", "with_path_filters", "command_prefix"),
    [
        ("plans.json", True, ["check", "."]),
        ("plan.json", False, ["check"]),
    ],
)
def test_check_plan_store_requires_plan_id_when_multiple_match(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
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
    [
        ("plans.json", True, ["check", "."]),
        ("plan.json", False, ["check"]),
    ],
)
def test_check_plan_store_plan_id_selects_specific_plan(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
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
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
):
    runner, _ = isolated_cli_workspace

    result = runner.invoke(cli, ["check", ".", "--plan-id", "test.alpha"])

    assert result.exit_code != 0
    assert "--plan-id requires --plan" in result.output


def test_list_plans_text_output(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
):
    runner, _ = isolated_cli_workspace
    Path("plans.json").write_text(
        json.dumps(
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
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        cli,
        ["list-plans", "--plan", "plans.json"],
    )

    assert result.exit_code == 0
    assert "test.alpha: 1 step" in result.output
    assert "test.beta: 2 steps" in result.output


def test_list_plans_json_output(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
):
    runner, _ = isolated_cli_workspace
    Path("plans.json").write_text(
        json.dumps(
            [
                {
                    "id": "test.alpha",
                    "steps": [{"id": "woodpecker.normalize_tas_units_to_kelvin"}],
                }
            ]
        ),
        encoding="utf-8",
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
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
):
    runner, _ = isolated_cli_workspace

    result = runner.invoke(cli, ["list-plans"])

    assert result.exit_code != 0
    assert "Missing option '--plan'" in result.output


def test_load_plans_from_plan_document_into_json_store(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
):
    runner, _ = isolated_cli_workspace

    Path("plan-doc.json").write_text(
        json.dumps(
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
            }
        ),
        encoding="utf-8",
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
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
):
    runner, _ = isolated_cli_workspace

    Path("source.json").write_text(
        json.dumps(
            [
                {"id": "test.alpha", "steps": [{"id": "woodpecker.normalize_tas_units_to_kelvin"}]},
                {
                    "id": "test.beta",
                    "aliases": ["beta_alias"],
                    "steps": [{"id": "woodpecker.ensure_latitude_is_increasing"}],
                },
            ]
        ),
        encoding="utf-8",
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


def test_load_plans_requires_source_plan_location(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
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
    assert "Missing option '--from-plan'" in result.output
