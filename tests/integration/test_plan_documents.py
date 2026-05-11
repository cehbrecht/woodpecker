"""Integration guards for shared fix-plan documents."""

from pathlib import Path

import pytest

from woodpecker.fixes.registry import FixRegistry
from woodpecker.plans import SUPPORTED_EXTENSIONS, load_fix_plan_document
from woodpecker.testing import integration_root_dir

pytest.importorskip("woodpecker_atlas_plugin")
pytest.importorskip("woodpecker_cmip6_decadal_plugin")
pytest.importorskip("woodpecker_cmip6_plugin")
pytest.importorskip("woodpecker_cmip7_plugin")


def _plan_document_paths() -> list[Path]:
    plan_dir = integration_root_dir() / "plans"
    return sorted(
        path for path in plan_dir.iterdir() if path.suffix.lower() in SUPPORTED_EXTENSIONS
    )


def test_integration_plan_steps_resolve_registered_core_and_plugin_fixes():
    plan_paths = _plan_document_paths()

    assert plan_paths

    step_ids: set[str] = set()
    for path in plan_paths:
        document = load_fix_plan_document(path)
        for plan in document.plans:
            for step in plan.steps:
                step_ids.add(step.id)
                assert FixRegistry.resolve_identifier(step.id) == step.id

    registered_ids = set(FixRegistry.registered_ids())

    assert any(identifier.startswith("woodpecker.") for identifier in step_ids)
    assert any(identifier.startswith("atlas.") for identifier in step_ids)
    assert any(identifier.startswith("cmip6_decadal.") for identifier in step_ids)
    assert any(identifier.startswith("cmip7.") for identifier in step_ids)
    assert any(identifier.startswith("cmip6.") for identifier in registered_ids)
