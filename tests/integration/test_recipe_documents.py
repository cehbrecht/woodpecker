"""Integration guards for shared recipe documents."""

from pathlib import Path

import pytest

from woodpecker.fixes.registry import FixFunctionRegistry
from woodpecker.recipes import SUPPORTED_EXTENSIONS, load_recipe_document
from woodpecker.testing import integration_root_dir

pytest.importorskip("woodpecker_atlas_plugin")
pytest.importorskip("woodpecker_cmip6_decadal_plugin")
pytest.importorskip("woodpecker_cmip6_plugin")
pytest.importorskip("woodpecker_cmip7_plugin")


def _plan_document_paths() -> list[Path]:
    recipe_dir = integration_root_dir() / "recipes"
    return sorted(
        path for path in recipe_dir.iterdir() if path.suffix.lower() in SUPPORTED_EXTENSIONS
    )


def test_integration_plan_steps_resolve_registered_core_and_plugin_fixes():
    recipe_paths = _plan_document_paths()

    assert recipe_paths

    step_ids: set[str] = set()
    for path in recipe_paths:
        document = load_recipe_document(path)
        for recipe in document.recipes:
            for step in recipe.steps:
                step_ids.add(step.id)
                assert FixFunctionRegistry.resolve_identifier(step.id) == step.id

    registered_ids = set(FixFunctionRegistry.registered_ids())

    assert any(identifier.startswith("woodpecker.") for identifier in step_ids)
    assert any(identifier.startswith("atlas.") for identifier in step_ids)
    assert any(identifier.startswith("cmip6_decadal.") for identifier in step_ids)
    assert any(identifier.startswith("cmip7.") for identifier in step_ids)
    assert any(identifier.startswith("cmip6.") for identifier in registered_ids)
