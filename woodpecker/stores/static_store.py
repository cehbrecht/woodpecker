from __future__ import annotations

from typing import Any, Iterable

from ..recipes.matcher import recipe_matches_dataset
from ..recipes.models import Recipe
from .base import RecipeStore


class StaticRecipeStore(RecipeStore):
    """Read-only RecipeStore backed by an in-memory recipe list."""

    def __init__(self, recipes: Iterable[Recipe]):
        self._plans = list(recipes)

    def list_recipes(self) -> list[Recipe]:
        return list(self._plans)

    def lookup(self, dataset: Any, path: str | None = None) -> list[Recipe]:
        return [
            recipe for recipe in self._plans if recipe_matches_dataset(recipe, dataset, path=path)
        ]

    def save_recipe(self, recipe: Recipe) -> None:
        _ = recipe
        raise NotImplementedError("StaticRecipeStore is read-only.")
