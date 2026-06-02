from __future__ import annotations

from typing import Any, Iterable

from ..recipes.models import Recipe
from .base import RecipeStore
from .index import RecipeIndex


class RecipeCatalog(RecipeStore):
    """Aggregate multiple recipe sources into one read-only query surface."""

    def __init__(self, sources: Iterable[RecipeStore]):
        self.sources = list(sources)

    @staticmethod
    def _deduplicate(recipes: Iterable[Recipe]) -> list[Recipe]:
        out: list[Recipe] = []
        positions: dict[str, int] = {}
        for recipe in recipes:
            recipe_id = RecipeIndex.recipe_id(recipe)
            if recipe_id in positions:
                idx = positions[recipe_id]
                existing = out[idx]
                aliases = list(existing.aliases)
                for alias in recipe.aliases:
                    if alias not in aliases:
                        aliases.append(alias)
                payload = existing.model_dump()
                payload["aliases"] = aliases
                out[idx] = Recipe.model_validate(payload)
                continue
            positions[recipe_id] = len(out)
            out.append(recipe)
        return out

    def list_recipes(self) -> list[Recipe]:
        recipes: list[Recipe] = []
        for source in self.sources:
            recipes.extend(source.list_recipes())
        return self._deduplicate(recipes)

    def lookup(self, dataset: Any, path: str | None = None) -> list[Recipe]:
        recipes: list[Recipe] = []
        for source in self.sources:
            recipes.extend(source.lookup(dataset, path=path))
        return self._deduplicate(recipes)

    def get_recipe(self, identifier: str) -> Recipe:
        return RecipeIndex(self.list_recipes()).get(identifier)

    def save_recipe(self, recipe: Recipe) -> None:
        _ = recipe
        raise NotImplementedError("RecipeCatalog is read-only.")
