from __future__ import annotations

from pathlib import Path
from typing import Callable, Iterator, Tuple

import pytest
from click.testing import CliRunner

from woodpecker.identity import registry as identity_registry

# Shared test-data fixtures for lightweight NetCDF-style tests.
#
# We intentionally use tiny placeholder `.nc` files (plain text) to keep tests
# fast and deterministic while still exercising filename-based matching/check/fix
# logic. Use:
# - path fixtures (e.g. `cmip6_member_file`) for simple unit tests
# - `make_placeholder_netcdf_path` for custom filenames
# - `isolated_cli_workspace` for CLI tests that need a clean cwd


PLACEHOLDER_NETCDF_CONTENT = "placeholder-netcdf-path\n"


@pytest.fixture(autouse=True)
def isolate_identity_resolver_registry() -> Iterator[None]:
    """Restore built-in dataset identity resolvers after each test."""
    resolvers = dict(identity_registry._RESOLVERS)
    try:
        yield
    finally:
        identity_registry._RESOLVERS.clear()
        identity_registry._RESOLVERS.update(resolvers)


@pytest.fixture
def cli_runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def make_placeholder_netcdf_path(tmp_path: Path) -> Callable[[str], Path]:
    def _make(filename: str) -> Path:
        path = tmp_path / filename
        path.write_text(PLACEHOLDER_NETCDF_CONTENT, encoding="utf-8")
        return path

    return _make


@pytest.fixture
def cmip6_member_file(make_placeholder_netcdf_path: Callable[[str], Path]) -> Path:
    return make_placeholder_netcdf_path("cmip6_member.nc")


@pytest.fixture
def atlas_spaced_file(make_placeholder_netcdf_path: Callable[[str], Path]) -> Path:
    return make_placeholder_netcdf_path("atlas sample.nc")


@pytest.fixture
def isolated_cli_workspace(
    cli_runner: CliRunner,
) -> Iterator[Tuple[CliRunner, Callable[[str], Path]]]:
    with cli_runner.isolated_filesystem():

        def _make(filename: str) -> Path:
            path = Path(filename)
            path.write_text(PLACEHOLDER_NETCDF_CONTENT, encoding="utf-8")
            return path

        yield cli_runner, _make
