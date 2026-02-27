import json
from pathlib import Path

from click.testing import CliRunner

from woodpecker.cli import cli


def test_list_fixes_contains_known_codes():
    runner = CliRunner()
    result = runner.invoke(cli, ["list-fixes", "--format", "text"])

    assert result.exit_code == 0
    assert "CMIP6D01" in result.output
    assert "ATLAS01" in result.output


def test_check_returns_zero_when_no_findings():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("cmip6_decadal_ok.nc").write_text("", encoding="utf-8")
        result = runner.invoke(cli, ["check", ".", "--select", "CMIP6D01"])

    assert result.exit_code == 0
    assert "No issues found" in result.output


def test_check_returns_nonzero_when_findings_exist():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("cmip6_bad.nc").write_text("", encoding="utf-8")
        result = runner.invoke(cli, ["check", ".", "--select", "CMIP6D01"])

    assert result.exit_code == 1
    assert "CMIP6D01" in result.output


def test_check_json_output_structure():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("cmip6_bad.nc").write_text("", encoding="utf-8")
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


def test_fix_write_applies_rename_for_cmip6_rule():
    runner = CliRunner()
    with runner.isolated_filesystem():
        source = Path("cmip6_case.nc")
        source.write_text("", encoding="utf-8")

        result = runner.invoke(cli, ["fix", ".", "--select", "CMIP6D01", "--write"])

        assert result.exit_code == 0
        assert "1 files changed" in result.output
        assert not source.exists()
        assert Path("cmip6_case_decadal.nc").exists()
