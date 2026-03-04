# Changelog

## Unreleased

- Added `uv`-based developer workflow support in `Makefile` (`install-uv`, `dev-uv`).
- Added Ruff lint/format tooling and Make targets (`lint`, `lint-fix`, `format`).
- Added CI workflow for lint and tests (`.github/workflows/ci.yml`).
- Updated CI/docs workflows to install dependencies via `uv`.
- Updated README and conda environment docs/deps for the new workflow.
