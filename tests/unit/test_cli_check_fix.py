import json
from pathlib import Path
from typing import Callable

import pytest
from click.testing import CliRunner

from woodpecker.cli import cli

pytestmark = pytest.mark.filterwarnings("ignore:.*Failed to read NetCDF input.*")


def _finding(message: str = "synthetic finding") -> dict[str, str]:
    return {
        "path": "cmip6_bad.nc",
        "fix_id": "woodpecker.normalize_tas_units_to_kelvin",
        "name": "Common check",
        "risk": "risk.careful.value_transformation",
        "risk_label": "careful: value transformation",
        "risk_metadata": {
            "id": "risk.careful.value_transformation",
            "title": "careful: value transformation",
            "description": "Transforms data or coordinate values.",
            "category": "risk",
        },
        "labels": [],
        "label_titles": [],
        "label_metadata": [],
        "message": message,
    }


def _fix_stats(*, persisted: int = 1, persist_failed: int = 0) -> dict[str, object]:
    return {
        "attempted": 1,
        "changed": 1,
        "persist_attempted": 1,
        "persisted": persisted,
        "persist_failed": persist_failed,
        "preview": [
            {
                "path": "cmip6_case.nc",
                "fix_id": "woodpecker.normalize_tas_units_to_kelvin",
                "name": "Normalize units",
                "risk": "risk.careful.value_transformation",
                "risk_label": "careful: value transformation",
                "risk_metadata": {
                    "id": "risk.careful.value_transformation",
                    "title": "careful: value transformation",
                    "description": "Transforms data or coordinate values.",
                    "category": "risk",
                },
                "labels": [],
                "label_titles": [],
                "label_metadata": [],
                "changed": True,
            }
        ],
    }


def test_check_json_output_structure(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
    monkeypatch,
):
    runner, make_placeholder_netcdf_path = isolated_cli_workspace
    make_placeholder_netcdf_path("cmip6_bad.nc")

    def _fake_run_check(*args, **kwargs):
        _ = (args, kwargs)
        return [_finding()]

    monkeypatch.setattr("woodpecker.cli.execute_check_context", _fake_run_check)

    result = runner.invoke(
        cli,
        ["check", ".", "--select", "woodpecker.normalize_tas_units_to_kelvin", "--format", "json"],
    )

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert isinstance(payload, list)
    assert payload
    assert {
        "path",
        "fix_id",
        "name",
        "risk",
        "risk_label",
        "risk_metadata",
        "labels",
        "label_titles",
        "label_metadata",
        "message",
    }.issubset(payload[0].keys())
    assert payload[0]["fix_id"] == "woodpecker.normalize_tas_units_to_kelvin"
    assert payload[0]["risk"] == "risk.careful.value_transformation"
    assert payload[0]["risk_label"] == "careful: value transformation"
    assert payload[0]["risk_metadata"]["category"] == "risk"


@pytest.mark.parametrize(
    ("stats", "expected_exit_code"),
    [
        (_fix_stats(), 0),
        (_fix_stats(persisted=0, persist_failed=1), 1),
    ],
)
def test_fix_json_output_contains_write_report(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
    monkeypatch,
    stats,
    expected_exit_code,
):
    runner, make_placeholder_netcdf_path = isolated_cli_workspace
    make_placeholder_netcdf_path("cmip6_case.nc")

    def _fake_run_fix(*args, **kwargs):
        return stats

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

    assert result.exit_code == expected_exit_code
    payload = json.loads(result.output)
    assert payload["mode"] == "write"
    assert payload["output_format"] == "netcdf"
    assert payload["attempted"] == stats["attempted"]
    assert payload["changed"] == stats["changed"]
    assert payload["persist_attempted"] == stats["persist_attempted"]
    assert payload["persisted"] == stats["persisted"]
    assert payload["persist_failed"] == stats["persist_failed"]
    assert payload["force_apply"] is False
    assert payload["preview"][0]["path"] == "cmip6_case.nc"
    assert payload["preview"][0]["risk"] == "risk.careful.value_transformation"
    assert payload["preview"][0]["risk_label"] == "careful: value transformation"
    assert payload["preview"][0]["risk_metadata"]["category"] == "risk"


def test_check_unknown_fix_code_returns_click_error(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
):
    runner, make_placeholder_netcdf_path = isolated_cli_workspace
    make_placeholder_netcdf_path("cmip6_case.nc")

    result = runner.invoke(cli, ["check", ".", "--select", "DOESNOTEXIST"])

    assert result.exit_code != 0
    assert "Unknown fix identifier(s): DOESNOTEXIST" in result.output


def test_fix_force_apply_is_forwarded_to_runner(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
    monkeypatch,
):
    runner, make_placeholder_netcdf_path = isolated_cli_workspace
    make_placeholder_netcdf_path("cmip6_case.nc")

    captured = {}

    def _fake_run_fix(*args, **kwargs):
        captured.update(kwargs)
        return _fix_stats()

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


def test_check_strict_io_flag_is_forwarded(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
    monkeypatch,
):
    runner, make_placeholder_netcdf_path = isolated_cli_workspace
    make_placeholder_netcdf_path("cmip6_case.nc")

    captured = {}

    def _fake_run_check(*args, **kwargs):
        captured.update(kwargs)
        return []

    monkeypatch.setattr("woodpecker.cli.execute_check_context", _fake_run_check)

    result = runner.invoke(
        cli,
        [
            "check",
            ".",
            "--select",
            "woodpecker.normalize_tas_units_to_kelvin",
            "--strict-io",
        ],
    )

    assert result.exit_code == 0
    assert captured.get("strict_io") is True


def test_fix_strict_io_flag_is_forwarded(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
    monkeypatch,
):
    runner, make_placeholder_netcdf_path = isolated_cli_workspace
    make_placeholder_netcdf_path("cmip6_case.nc")

    captured = {}

    def _fake_run_fix(*args, **kwargs):
        captured.update(kwargs)
        return _fix_stats()

    monkeypatch.setattr("woodpecker.cli.execute_fix_context", _fake_run_fix)

    result = runner.invoke(
        cli,
        [
            "fix",
            ".",
            "--select",
            "woodpecker.normalize_tas_units_to_kelvin",
            "--strict-io",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    assert captured.get("strict_io") is True
