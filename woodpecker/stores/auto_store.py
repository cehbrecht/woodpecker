from __future__ import annotations

from typing import Any

from woodpecker.fixes.registry import FixFunctionRegistry
from woodpecker.identity import dataset_type_matches_declared, resolve_dataset_identity

from ..recipes.models import FixRef, Recipe
from .base import RecipeStore


class AutoRecipeStore(RecipeStore):
    """Read-only store that exposes registered fixes as single-step recipes."""

    @staticmethod
    def _recipe_from_fix(fix: Any) -> Recipe:
        fix_id = str(getattr(fix, "id", "") or "")
        name = str(getattr(fix, "name", "") or "")
        description = str(getattr(fix, "description", "") or "")
        aliases = list(getattr(fix, "aliases", []) or [])

        return Recipe(
            id=fix_id,
            aliases=aliases,
            description=description or name,
            steps=[FixRef(id=fix_id)],
        )

    def list_recipes(self) -> list[Recipe]:
        return [self._recipe_from_fix(fix) for fix in FixFunctionRegistry.discover()]

    def lookup(self, dataset: Any, path: str | None = None) -> list[Recipe]:
        _ = path
        identity = resolve_dataset_identity(dataset)
        recipes: list[Recipe] = []

        for fix in FixFunctionRegistry.discover():
            if not dataset_type_matches_declared(
                getattr(fix, "dataset", None), identity.dataset_type
            ):
                continue
            if not fix.matches(dataset):
                continue
            recipes.append(self._recipe_from_fix(fix))

        return recipes

    def save_recipe(self, recipe: Recipe) -> None:
        _ = recipe
        raise NotImplementedError("AutoRecipeStore is read-only.")
