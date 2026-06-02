from __future__ import annotations

from woodpecker.fixes.identifiers import IdentifierResolver

from ..recipes.models import Recipe


class RecipeIndex:
    """Index a collection of ``Recipe`` objects for fast identifier-based retrieval.

    On construction, recipes are keyed by their id and an ``IdentifierResolver``
    is built so recipes can be looked up by id or declared alias.
    Duplicate ids raise immediately.
    """

    def __init__(self, recipes: list[Recipe]):
        self._plans = list(recipes)
        self._recipes_by_id = self._index_recipes_by_id(self._plans)
        self._resolver = self._build_recipe_identifier_resolver(self._recipes_by_id)

    @staticmethod
    def recipe_id(recipe: Recipe) -> str:
        """Return normalized id for *recipe*."""
        if recipe.identifier_set is not None:
            return recipe.identifier_set.id
        return str(recipe.id).strip().lower()

    @classmethod
    def _index_recipes_by_id(cls, recipes: list[Recipe]) -> dict[str, Recipe]:
        """Build an id-keyed dict, raising on duplicate ids."""
        indexed: dict[str, Recipe] = {}
        for recipe in recipes:
            recipe_id = cls.recipe_id(recipe)
            if not recipe_id:
                raise ValueError("Encountered recipe with empty identifier.")
            if recipe_id in indexed:
                raise ValueError(f"Duplicate recipe id detected: {recipe_id}")
            indexed[recipe_id] = recipe
        return indexed

    @staticmethod
    def _build_recipe_identifier_resolver(
        recipes_by_id: dict[str, Recipe],
    ) -> IdentifierResolver:
        """Build a resolver seeded with every recipe id and alias in the index."""
        resolver = IdentifierResolver(index={recipe_id: recipe_id for recipe_id in recipes_by_id})
        for recipe in recipes_by_id.values():
            if recipe.identifier_set is not None:
                resolver.register(recipe.identifier_set)
        return resolver

    def get(self, identifier: str) -> Recipe:
        """Return the recipe matching *identifier* (id or alias).

        Raises ``ValueError`` for unknown or ambiguous identifiers.
        """
        try:
            resolved_id = self._resolver.resolve(identifier)
        except KeyError as exc:
            raise ValueError(f"Unknown recipe identifier: {identifier}") from exc

        return self._recipes_by_id[resolved_id]

    def list(self) -> list[Recipe]:
        """Return all recipes in insertion order."""
        return list(self._plans)
