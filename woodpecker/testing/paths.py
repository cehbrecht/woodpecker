"""Paths to repository test assets used by examples and integration tests."""

from pathlib import Path


def repository_root(start: str | Path | None = None) -> Path:
    """Return the Woodpecker repository root by walking up from ``start``."""
    current = Path.cwd() if start is None else Path(start)
    current = current.resolve()
    if current.is_file():
        current = current.parent

    for path in (current, *current.parents):
        if (path / "pyproject.toml").is_file() and (path / "woodpecker").is_dir():
            return path

    msg = f"Could not locate the Woodpecker repository root from {current}."
    raise FileNotFoundError(msg)


def testing_root_dir(start: str | Path | None = None) -> Path:
    """Return the repository ``tests`` directory."""
    return repository_root(start) / "tests"


def integration_root_dir(start: str | Path | None = None) -> Path:
    """Return the repository ``tests/integration`` directory."""
    return testing_root_dir(start) / "integration"


def integration_plan_path(filename: str, *, start: str | Path | None = None) -> Path:
    """Return a plan document from ``tests/integration/plans``."""
    return integration_root_dir(start) / "plans" / filename
