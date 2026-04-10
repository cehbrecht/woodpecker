import json
from pathlib import Path
from typing import Callable

from click.testing import CliRunner

from woodpecker.cli import cli


def test_list_fixes_contains_known_codes():
    runner = CliRunner()
    result = runner.invoke(cli, ["list-fixes", "--format", "text"])

    assert result.exit_code == 0
    assert "CMIP6D01" in result.output
    assert "ATLAS01" in result.output


def test_io_status_text_output_contains_expected_keys():
    runner = CliRunner()
    result = runner.invoke(cli, ["io-status"])

    assert result.exit_code == 0
    assert "xarray_input:" in result.output
    assert "netcdf_input:" in result.output
    assert "zarr_output:" in result.output


def test_io_status_json_output_structure():
    runner = CliRunner()
    result = runner.invoke(cli, ["io-status", "--format", "json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    expected_keys = {
        "xarray_input",
        "netcdf_input",
        "zarr_input",
        "netcdf_output",
        "zarr_output",
    }
    assert set(payload.keys()) == expected_keys
    assert all(isinstance(payload[key], bool) for key in expected_keys)


def test_check_returns_zero_when_no_findings(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
):
    runner, make_dummy_netcdf = isolated_cli_workspace
    make_dummy_netcdf("cmip6_decadal_ok.nc")
    result = runner.invoke(cli, ["check", ".", "--select", "CMIP6D01"])

    assert result.exit_code == 0
    assert "No issues found" in result.output


def test_check_returns_nonzero_when_findings_exist(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
):
    runner, make_dummy_netcdf = isolated_cli_workspace
    make_dummy_netcdf("cmip6_bad.nc")
    result = runner.invoke(cli, ["check", ".", "--select", "CMIP601"])

    assert result.exit_code == 1
    assert "CMIP601" in result.output


def test_check_json_output_structure(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
):
    runner, make_dummy_netcdf = isolated_cli_workspace
    make_dummy_netcdf("cmip6_bad.nc")
    result = runner.invoke(
        cli,
        ["check", ".", "--select", "CMIP601", "--format", "json"],
    )

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert isinstance(payload, list)
    assert payload
    assert {"path", "code", "name", "message"}.issubset(payload[0].keys())
    assert payload[0]["code"] == "CMIP601"


def test_fix_write_cmip6d01_reports_no_change_for_empty_fallback_dataset(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
):
    runner, make_dummy_netcdf = isolated_cli_workspace
    make_dummy_netcdf("c3s-cmip6-decadal.case.nc")

    result = runner.invoke(
        cli,
        ["fix", ".", "--select", "CMIP6D01", "--write", "--output-format", "netcdf"],
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

    monkeypatch.setattr("woodpecker.cli.run_fix", _fake_run_fix)

    result = runner.invoke(
        cli,
        [
            "fix",
            ".",
            "--select",
            "CMIP6D01",
            "--write",
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

    monkeypatch.setattr("woodpecker.cli.run_fix", _fake_run_fix)

    result = runner.invoke(
        cli,
        [
            "fix",
            ".",
            "--select",
            "CMIP6D01",
            "--write",
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
    assert "Unknown fix code(s): DOESNOTEXIST" in result.output


def test_check_uses_workflow_defaults(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
):
    runner, make_dummy_netcdf = isolated_cli_workspace
    make_dummy_netcdf("cmip6_bad.nc")
    Path("workflow.json").write_text(
        json.dumps({"inputs": ["."], "codes": ["CMIP601"]}),
        encoding="utf-8",
    )

    result = runner.invoke(cli, ["check", "--workflow", "workflow.json"])

    assert result.exit_code == 1
    assert "CMIP601" in result.output


def test_fix_uses_workflow_output_format_when_auto(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
    monkeypatch,
):
    runner, make_dummy_netcdf = isolated_cli_workspace
    make_dummy_netcdf("cmip6_case.nc")
    Path("workflow.json").write_text(
        json.dumps({"inputs": ["."], "codes": ["CMIP6D01"], "output_format": "zarr"}),
        encoding="utf-8",
    )

    def _fake_run_fix(inputs, fixes, dry_run, output_format):
        _ = (inputs, fixes, dry_run)
        assert output_format == "zarr"
        return {
            "attempted": 1,
            "changed": 1,
            "persist_attempted": 1,
            "persisted": 1,
            "persist_failed": 0,
        }

    monkeypatch.setattr("woodpecker.cli.run_fix", _fake_run_fix)

    result = runner.invoke(
        cli,
        ["fix", "--workflow", "workflow.json", "--write", "--format", "json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["output_format"] == "zarr"


def test_check_workflow_applies_fix_options_to_message(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
):
    runner, make_dummy_netcdf = isolated_cli_workspace
    make_dummy_netcdf("c3s-cmip6.member.nc")
    Path("workflow.json").write_text(
        json.dumps(
            {
                "inputs": ["."],
                "codes": ["CMIP601"],
                "fixes": {"CMIP601": {"message": "configured check message"}},
            }
        ),
        encoding="utf-8",
    )

    result = runner.invoke(cli, ["check", "--workflow", "workflow.json"])

    assert result.exit_code == 1
    assert "configured check message" in result.output


def test_fix_writes_provenance_file_by_default(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
):
    runner, make_dummy_netcdf = isolated_cli_workspace
    make_dummy_netcdf("cmip6_case.nc")

    result = runner.invoke(cli, ["fix", ".", "--select", "CMIP601"])

    assert result.exit_code == 0
    prov_path = Path("woodpecker.prov.json")
    assert prov_path.exists()
    payload = json.loads(prov_path.read_text(encoding="utf-8"))
    assert "activity" in payload
    assert "entity" in payload
