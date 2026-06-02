from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ..recipes.models import Recipe
from .index import RecipeIndex


class RecipeStore(ABC):
    """Abstract base for recipe storage backends.

    Backends must implement ``lookup``, ``list_recipes``, and ``save_recipe``.
    ``get_recipe`` is provided for free via ``RecipeIndex`` and does not need
    to be overridden unless the backend wants to optimize the hot path.
    """

    @abstractmethod
    def lookup(self, dataset: Any, path: str | None = None) -> list[Recipe]:
        raise NotImplementedError

    @abstractmethod
    def list_recipes(self) -> list[Recipe]:
        raise NotImplementedError

    @abstractmethod
    def save_recipe(self, recipe: Recipe) -> None:
        raise NotImplementedError

    def get_recipe(self, identifier: str) -> Recipe:
        # If this becomes a hot path, concrete stores can cache RecipeIndex and
        # invalidate on save_recipe(); keep base class behavior stateless and minimal.
        return RecipeIndex(self.list_recipes()).get(identifier)
