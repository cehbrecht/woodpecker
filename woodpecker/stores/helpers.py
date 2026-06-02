from __future__ import annotations

from pathlib import Path

from woodpecker.recipes.loaders import RecipeLoader

from .auto_store import AutoRecipeStore
from .base import RecipeStore
from .duckdb_store import DuckDBRecipeStore
from .json_store import JsonRecipeStore


def create_recipe_store(store_type: str, recipe_location: Path | None) -> RecipeStore:
    """Create a RecipeStore backend for the selected store type and location."""

    if store_type == "catalog":
        explicit = [recipe_location] if recipe_location is not None else []
        return RecipeLoader().catalog(explicit_locations=explicit)

    if store_type == "auto":
        return AutoRecipeStore()

    if recipe_location is None:
        raise ValueError("--recipe is required when using a recipe store backend.")

    if store_type == "json":
        return JsonRecipeStore(recipe_location)
    if store_type == "duckdb":
        return DuckDBRecipeStore(recipe_location)

    raise ValueError(f"Unsupported recipe store type: {store_type}")
