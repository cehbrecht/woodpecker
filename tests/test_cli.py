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
    result = runner.invoke(cli, ["check", ".", "--select", "CMIP6D01"])

    assert result.exit_code == 1
    assert "CMIP6D01" in result.output


def test_check_json_output_structure(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
):
    runner, make_dummy_netcdf = isolated_cli_workspace
    make_dummy_netcdf("cmip6_bad.nc")
    result = runner.invoke(
        cli,
        ["check", ".", "--select", "CMIP6D01", "--format", "json"],
    )

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert isinstance(payload, list)
    assert payload
    assert {"path", "code", "name", "message"}.issubset(payload[0].keys())
    assert payload[0]["code"] == "CMIP6D01"


def test_fix_write_applies_rename_for_cmip6_rule(
    isolated_cli_workspace: tuple[CliRunner, Callable[[str], Path]],
):
    runner, make_dummy_netcdf = isolated_cli_workspace
    source = make_dummy_netcdf("cmip6_case.nc")

    result = runner.invoke(cli, ["fix", ".", "--select", "CMIP6D01", "--write"])

    assert result.exit_code == 0
    assert "1 files changed" in result.output
    assert not source.exists()
    assert Path("cmip6_case_decadal.nc").exists()
