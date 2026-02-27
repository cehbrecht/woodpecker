from __future__ import annotations

from pathlib import Path
from typing import Callable, Iterator, Tuple

import pytest
from click.testing import CliRunner

# Shared test-data fixtures for lightweight NetCDF-style tests.
#
# We intentionally use tiny placeholder `.nc` files (plain text) to keep tests
# fast and deterministic while still exercising filename-based matching/check/fix
# logic. Use:
# - `make_dummy_netcdf` for tmp_path unit tests
# - `isolated_cli_workspace` for CLI tests that need a clean cwd


DUMMY_NETCDF_CONTENT = "dummy-netcdf-placeholder\n"


@pytest.fixture
def cli_runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def make_dummy_netcdf(tmp_path: Path) -> Callable[[str], Path]:
    def _make(filename: str) -> Path:
        path = tmp_path / filename
        path.write_text(DUMMY_NETCDF_CONTENT, encoding="utf-8")
        return path

    return _make


@pytest.fixture
def isolated_cli_workspace(cli_runner: CliRunner) -> Iterator[Tuple[CliRunner, Callable[[str], Path]]]:
    with cli_runner.isolated_filesystem():
        def _make(filename: str) -> Path:
            path = Path(filename)
            path.write_text(DUMMY_NETCDF_CONTENT, encoding="utf-8")
            return path

        yield cli_runner, _make
