from __future__ import annotations

from pathlib import Path
from typing import Callable, Iterator, Tuple

import pytest
from click.testing import CliRunner

from woodpecker.fixes.identifiers import IdentifierResolver
from woodpecker.fixes.registry import FixRegistry
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
    """Keep per-test identity resolver registrations from leaking globally."""
    resolvers = identity_registry.snapshot_registry()
    try:
        yield
    finally:
        identity_registry.restore_registry(resolvers)


@pytest.fixture(autouse=True)
def isolate_fix_registry() -> Iterator[None]:
    """Keep per-test fix registrations from leaking globally."""
    registry = dict(FixRegistry._registry)
    identifier_index = dict(FixRegistry._resolver._identifier_index)
    ambiguous_identifiers = set(FixRegistry._resolver._ambiguous_identifiers)
    try:
        yield
    finally:
        FixRegistry._registry = registry
        FixRegistry._resolver = IdentifierResolver(
            index=identifier_index,
            ambiguous_identifiers=ambiguous_identifiers,
        )


@pytest.fixture
def cli_runner() -> CliRunner:
    """Return a Click CLI runner for command tests."""
    return CliRunner()


@pytest.fixture
def make_placeholder_netcdf_path(tmp_path: Path) -> Callable[[str], Path]:
    """Create tiny placeholder `.nc` paths for filename-based tests."""

    def _make(filename: str) -> Path:
        path = tmp_path / filename
        path.write_text(PLACEHOLDER_NETCDF_CONTENT, encoding="utf-8")
        return path

    return _make


@pytest.fixture
def cmip6_member_file(make_placeholder_netcdf_path: Callable[[str], Path]) -> Path:
    """Return a placeholder CMIP6-like NetCDF path."""
    return make_placeholder_netcdf_path("cmip6_member.nc")


@pytest.fixture
def atlas_spaced_file(make_placeholder_netcdf_path: Callable[[str], Path]) -> Path:
    """Return a placeholder Atlas-like path with a space in the filename."""
    return make_placeholder_netcdf_path("atlas sample.nc")


@pytest.fixture
def isolated_cli_workspace(
    cli_runner: CliRunner,
) -> Iterator[Tuple[CliRunner, Callable[[str], Path]]]:
    """Run CLI tests in an isolated cwd with a helper for placeholder files."""
    with cli_runner.isolated_filesystem():

        def _make(filename: str) -> Path:
            path = Path(filename)
            path.write_text(PLACEHOLDER_NETCDF_CONTENT, encoding="utf-8")
            return path

        yield cli_runner, _make
