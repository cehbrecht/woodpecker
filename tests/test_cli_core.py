import json

from click.testing import CliRunner

from woodpecker.cli import cli


def test_list_fixes_contains_known_codes():
    runner = CliRunner()
    result = runner.invoke(cli, ["list-fixes", "--format", "text"])

    assert result.exit_code == 0
    assert "woodpecker.normalize_tas_units_to_kelvin" in result.output
    assert "woodpecker.ensure_latitude_is_increasing" in result.output


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
