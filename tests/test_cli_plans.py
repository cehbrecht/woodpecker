import json
from pathlib import Path
from typing import Callable

import pytest
from click.testing import CliRunner

from woodpecker.cli import cli

pytestmark = pytest.mark.filterwarnings("ignore:.*Failed to read NetCDF input.*")


def test_check_uses_json_plan_store_lookup(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
    monkeypatch,
):
    runner, make_dummy_netcdf = isolated_cli_workspace
    make_dummy_netcdf("cmip6_bad.nc")
    Path("plans.json").write_text(
        json.dumps(
            [
                {
                    "id": "cmip6.default",
                    "match": {"path_patterns": ["*cmip6_bad.nc"]},
                    "steps": [{"id": "woodpecker.normalize_tas_units_to_kelvin"}],
                }
            ]
        ),
        encoding="utf-8",
    )

    def _fake_run_check(*args, **kwargs):
        _ = (args, kwargs)
        return [
            {
                "path": "cmip6_bad.nc",
                "fix_id": "woodpecker.normalize_tas_units_to_kelvin",
                "name": "Common check",
                "message": "from json store",
            }
        ]

    monkeypatch.setattr("woodpecker.cli.execute_check_context", _fake_run_check)

    result = runner.invoke(
        cli,
        ["check", ".", "--plan", "plans.json"],
    )

    assert result.exit_code == 1
    assert "woodpecker.normalize_tas_units_to_kelvin" in result.output


def test_check_plan_store_requires_plan_id_when_multiple_match_without_path_filters(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
):
    runner, make_dummy_netcdf = isolated_cli_workspace
    make_dummy_netcdf("cmip6_bad.nc")
    Path("plans.json").write_text(
        json.dumps(
            [
                {
                    "id": "test.first",
                    "match": {"path_patterns": ["*cmip6_bad.nc"]},
                    "steps": [{"id": "woodpecker.normalize_tas_units_to_kelvin"}],
                },
                {
                    "id": "test.second",
                    "match": {"path_patterns": ["*cmip6_bad.nc"]},
                    "steps": [{"id": "woodpecker.ensure_latitude_is_increasing"}],
                },
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        cli,
        ["check", ".", "--plan", "plans.json"],
    )

    assert result.exit_code != 0
    assert "Multiple matching fix plans found" in result.output


def test_check_plan_store_plan_id_selects_specific_plan_without_path_filters(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
    monkeypatch,
):
    runner, make_dummy_netcdf = isolated_cli_workspace
    make_dummy_netcdf("cmip6_bad.nc")
    Path("plans.json").write_text(
        json.dumps(
            [
                {
                    "id": "test.first",
                    "match": {"path_patterns": ["*cmip6_bad.nc"]},
                    "steps": [{"id": "woodpecker.ensure_latitude_is_increasing"}],
                },
                {
                    "id": "test.second",
                    "match": {"path_patterns": ["*cmip6_bad.nc"]},
                    "steps": [{"id": "woodpecker.normalize_tas_units_to_kelvin"}],
                },
            ]
        ),
        encoding="utf-8",
    )

    def _fake_run_check(*args, **kwargs):
        _ = (args, kwargs)
        return [
            {
                "path": "cmip6_bad.nc",
                "fix_id": "woodpecker.normalize_tas_units_to_kelvin",
                "name": "Common check",
                "message": "selected plan",
            }
        ]

    monkeypatch.setattr("woodpecker.cli.execute_check_context", _fake_run_check)

    result = runner.invoke(
        cli,
        [
            "check",
            ".",
            "--plan",
            "plans.json",
            "--plan-id",
            "test.second",
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


def test_check_plan_store_requires_plan_id_when_multiple_match(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
):
    runner, make_dummy_netcdf = isolated_cli_workspace
    make_dummy_netcdf("cmip6_bad.nc")

    Path("plan.json").write_text(
        json.dumps(
            {
                "plans": [
                    {
                        "id": "test.first",
                        "steps": [{"id": "woodpecker.normalize_tas_units_to_kelvin"}],
                    },
                    {
                        "id": "test.second",
                        "steps": [{"id": "woodpecker.ensure_latitude_is_increasing"}],
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    result = runner.invoke(cli, ["check", "--plan", "plan.json"])

    assert result.exit_code != 0
    assert "Multiple matching fix plans found" in result.output


def test_check_plan_store_plan_id_selects_specific_plan(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
    monkeypatch,
):
    runner, make_dummy_netcdf = isolated_cli_workspace
    make_dummy_netcdf("cmip6_bad.nc")

    Path("plan.json").write_text(
        json.dumps(
            {
                "plans": [
                    {
                        "id": "test.first",
                        "steps": [{"id": "woodpecker.ensure_latitude_is_increasing"}],
                    },
                    {
                        "id": "test.second",
                        "steps": [{"id": "woodpecker.normalize_tas_units_to_kelvin"}],
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    def _fake_run_check(*args, **kwargs):
        _ = (args, kwargs)
        return [
            {
                "path": "cmip6_bad.nc",
                "fix_id": "woodpecker.normalize_tas_units_to_kelvin",
                "name": "Common check",
                "message": "selected plan",
            }
        ]

    monkeypatch.setattr("woodpecker.cli.execute_check_context", _fake_run_check)

    result = runner.invoke(cli, ["check", "--plan", "plan.json", "--plan-id", "test.second"])

    assert result.exit_code == 1
    assert "woodpecker.normalize_tas_units_to_kelvin" in result.output


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
    assert "test.alpha: 1 fixes" in result.output
    assert "test.beta: 2 fixes" in result.output


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
                {"id": "test.beta", "steps": [{"id": "woodpecker.ensure_latitude_is_increasing"}]},
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
            "test.beta",
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
