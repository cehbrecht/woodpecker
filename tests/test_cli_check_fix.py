import json
from pathlib import Path
from typing import Callable

import pytest
from click.testing import CliRunner

from woodpecker.cli import cli

pytestmark = pytest.mark.filterwarnings("ignore:.*Failed to read NetCDF input.*")


def test_check_returns_zero_when_no_findings(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
):
    runner, make_dummy_netcdf = isolated_cli_workspace
    make_dummy_netcdf("cmip6_decadal_ok.nc")
    result = runner.invoke(
        cli, ["check", ".", "--select", "woodpecker.normalize_tas_units_to_kelvin"]
    )

    assert result.exit_code == 0
    assert "No issues found" in result.output


def test_check_returns_nonzero_when_findings_exist(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
    monkeypatch,
):
    runner, make_dummy_netcdf = isolated_cli_workspace
    make_dummy_netcdf("cmip6_bad.nc")

    def _fake_run_check(*args, **kwargs):
        _ = (args, kwargs)
        return [
            {
                "path": "cmip6_bad.nc",
                "fix_id": "woodpecker.normalize_tas_units_to_kelvin",
                "name": "Common check",
                "message": "synthetic finding",
            }
        ]

    monkeypatch.setattr("woodpecker.cli.execute_check_context", _fake_run_check)

    result = runner.invoke(
        cli, ["check", ".", "--select", "woodpecker.normalize_tas_units_to_kelvin"]
    )

    assert result.exit_code == 1
    assert "woodpecker.normalize_tas_units_to_kelvin" in result.output


def test_check_json_output_structure(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
    monkeypatch,
):
    runner, make_dummy_netcdf = isolated_cli_workspace
    make_dummy_netcdf("cmip6_bad.nc")

    def _fake_run_check(*args, **kwargs):
        _ = (args, kwargs)
        return [
            {
                "path": "cmip6_bad.nc",
                "fix_id": "woodpecker.normalize_tas_units_to_kelvin",
                "name": "Common check",
                "message": "synthetic finding",
            }
        ]

    monkeypatch.setattr("woodpecker.cli.execute_check_context", _fake_run_check)

    result = runner.invoke(
        cli,
        ["check", ".", "--select", "woodpecker.normalize_tas_units_to_kelvin", "--format", "json"],
    )

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert isinstance(payload, list)
    assert payload
    assert {"path", "fix_id", "name", "message"}.issubset(payload[0].keys())
    assert payload[0]["fix_id"] == "woodpecker.normalize_tas_units_to_kelvin"


def test_fix_write_cmip6d01_reports_no_change_for_empty_fallback_dataset(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
):
    runner, make_dummy_netcdf = isolated_cli_workspace
    make_dummy_netcdf("c3s-cmip6-decadal.case.nc")

    result = runner.invoke(
        cli,
        [
            "fix",
            ".",
            "--select",
            "woodpecker.normalize_tas_units_to_kelvin",
            "--force-apply",
            "--output-format",
            "netcdf",
        ],
    )

    assert result.exit_code == 0
    assert "1 fix applications attempted" in result.output
    assert "0 files changed" in result.output


def test_fix_json_output_contains_write_report(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
    monkeypatch,
):
    runner, make_dummy_netcdf = isolated_cli_workspace
    make_dummy_netcdf("cmip6_case.nc")

    def _fake_run_fix(*args, **kwargs):
        return {
            "attempted": 1,
            "changed": 1,
            "persist_attempted": 1,
            "persisted": 1,
            "persist_failed": 0,
        }

    monkeypatch.setattr("woodpecker.cli.execute_fix_context", _fake_run_fix)

    result = runner.invoke(
        cli,
        [
            "fix",
            ".",
            "--select",
            "woodpecker.normalize_tas_units_to_kelvin",
            "--output-format",
            "netcdf",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["mode"] == "write"
    assert payload["output_format"] == "netcdf"
    assert payload["attempted"] == 1
    assert payload["changed"] == 1
    assert payload["persist_attempted"] == 1
    assert payload["persisted"] == 1
    assert payload["persist_failed"] == 0
    assert payload["force_apply"] is False


def test_fix_json_write_exits_nonzero_on_persist_failure(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
    monkeypatch,
):
    runner, make_dummy_netcdf = isolated_cli_workspace
    make_dummy_netcdf("cmip6_case.nc")

    def _fake_run_fix(*args, **kwargs):
        return {
            "attempted": 1,
            "changed": 1,
            "persist_attempted": 1,
            "persisted": 0,
            "persist_failed": 1,
        }

    monkeypatch.setattr("woodpecker.cli.execute_fix_context", _fake_run_fix)

    result = runner.invoke(
        cli,
        [
            "fix",
            ".",
            "--select",
            "woodpecker.normalize_tas_units_to_kelvin",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["persist_failed"] == 1


def test_check_unknown_fix_code_returns_click_error(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
):
    runner, make_dummy_netcdf = isolated_cli_workspace
    make_dummy_netcdf("cmip6_case.nc")

    result = runner.invoke(cli, ["check", ".", "--select", "DOESNOTEXIST"])

    assert result.exit_code != 0
    assert "Unknown fix identifier(s): DOESNOTEXIST" in result.output


def test_check_uses_plan_defaults(
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
                        "id": "core.basic",
                        "steps": [{"id": "woodpecker.normalize_tas_units_to_kelvin"}],
                    }
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
                "message": "configured by plan",
            }
        ]

    monkeypatch.setattr("woodpecker.cli.execute_check_context", _fake_run_check)

    result = runner.invoke(cli, ["check", "--plan", "plan.json"])

    assert result.exit_code == 1
    assert "woodpecker.normalize_tas_units_to_kelvin" in result.output


def test_fix_uses_auto_output_format_when_not_set(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
    monkeypatch,
):
    runner, make_dummy_netcdf = isolated_cli_workspace
    make_dummy_netcdf("cmip6_case.nc")
    Path("plan.json").write_text(
        json.dumps(
            {
                "plans": [
                    {
                        "id": "core.basic",
                        "steps": [{"id": "woodpecker.normalize_tas_units_to_kelvin"}],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    def _fake_run_fix(context, **kwargs):
        _ = kwargs
        assert context.resolved_output_format == "auto"
        return {
            "attempted": 1,
            "changed": 1,
            "persist_attempted": 1,
            "persisted": 1,
            "persist_failed": 0,
        }

    monkeypatch.setattr("woodpecker.cli.execute_fix_context", _fake_run_fix)

    result = runner.invoke(
        cli,
        ["fix", "--plan", "plan.json", "--format", "json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["output_format"] == "auto"


def test_check_plan_applies_fix_options_to_message(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
    monkeypatch,
):
    runner, make_dummy_netcdf = isolated_cli_workspace
    make_dummy_netcdf("c3s-cmip6.member.nc")
    Path("plan.json").write_text(
        json.dumps(
            {
                "plans": [
                    {
                        "id": "cmip6.msg",
                        "steps": [
                            {
                                "id": "woodpecker.normalize_tas_units_to_kelvin",
                                "options": {"message": "configured check message"},
                            }
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    def _fake_run_check(context):
        message = "default"
        fixes = context.fixes
        if fixes and hasattr(fixes[0], "config"):
            message = fixes[0].config.get("message", message)
        return [
            {
                "path": "c3s-cmip6.member.nc",
                "fix_id": "woodpecker.normalize_tas_units_to_kelvin",
                "name": "Common check",
                "message": message,
            }
        ]

    monkeypatch.setattr("woodpecker.cli.execute_check_context", _fake_run_check)

    result = runner.invoke(cli, ["check", "--plan", "plan.json"])

    assert result.exit_code == 1
    assert "configured check message" in result.output


def test_fix_writes_provenance_file_by_default(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
):
    runner, make_dummy_netcdf = isolated_cli_workspace
    make_dummy_netcdf("cmip6_case.nc")

    result = runner.invoke(
        cli, ["fix", ".", "--select", "woodpecker.normalize_tas_units_to_kelvin"]
    )

    assert result.exit_code == 0
    prov_path = Path("woodpecker.prov.json")
    assert prov_path.exists()
    payload = json.loads(prov_path.read_text(encoding="utf-8"))
    assert "activity" in payload
    assert "entity" in payload


def test_fix_force_apply_is_forwarded_to_runner(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
    monkeypatch,
):
    runner, make_dummy_netcdf = isolated_cli_workspace
    make_dummy_netcdf("cmip6_case.nc")

    captured = {}

    def _fake_run_fix(*args, **kwargs):
        captured.update(kwargs)
        return {
            "attempted": 1,
            "changed": 1,
            "persist_attempted": 1,
            "persisted": 1,
            "persist_failed": 0,
        }

    monkeypatch.setattr("woodpecker.cli.execute_fix_context", _fake_run_fix)

    result = runner.invoke(
        cli,
        [
            "fix",
            ".",
            "--select",
            "woodpecker.normalize_tas_units_to_kelvin",
            "--force-apply",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    assert captured.get("force_apply") is True
    payload = json.loads(result.output)
    assert payload["force_apply"] is True


def test_fix_force_apply_requires_selected_codes(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
):
    runner, _ = isolated_cli_workspace

    result = runner.invoke(cli, ["fix", ".", "--force-apply"])

    assert result.exit_code != 0
    assert "--force-apply requires explicit fix selection" in result.output
