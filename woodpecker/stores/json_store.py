from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from ..recipes.matcher import recipe_matches_dataset
from ..recipes.models import Recipe
from .base import RecipeStore
from .index import RecipeIndex


class JsonRecipeStore(RecipeStore):
    def __init__(self, path: str | Path):
        self.path = Path(path)
        suffix = self.path.suffix.lower()
        if suffix in {".yaml", ".yml"}:
            self._format_label = "YAML"
            self._loads = lambda text: yaml.safe_load(text) if text.strip() else []
            self._dumps = lambda payload: yaml.safe_dump(
                payload,
                sort_keys=False,
                allow_unicode=True,
            )
        else:
            self._format_label = "JSON"
            self._loads = lambda text: json.loads(text or "[]")
            self._dumps = lambda payload: json.dumps(payload, ensure_ascii=False, indent=2) + "\n"

    def _read_raw(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []

        payload = self._loads(self.path.read_text(encoding="utf-8"))
        return self._coerce_recipe_payload(payload)

    def _coerce_recipe_payload(self, payload: Any) -> list[dict[str, Any]]:
        if payload is None:
            return []

        if isinstance(payload, list):
            recipes = payload
        elif isinstance(payload, dict):
            if "recipes" in payload:
                recipes = payload.get("recipes", [])
            else:
                # Single-recipe shorthand payload.
                recipes = [payload]
        else:
            raise ValueError(
                f"{self._format_label} recipe store file must contain a list or {{'recipes': [...]}} payload"
            )

        if not isinstance(recipes, list):
            raise ValueError(
                f"{self._format_label} recipe store file must contain a list or {{'recipes': [...]}} payload"
            )
        return [item for item in recipes if isinstance(item, dict)]

    def _write_raw(self, recipes: list[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"schema_version": 1, "recipes": recipes}
        self.path.write_text(self._dumps(payload), encoding="utf-8")

    def list_recipes(self) -> list[Recipe]:
        return [Recipe.model_validate(item) for item in self._read_raw()]

    def save_recipe(self, recipe: Recipe) -> None:
        recipes = self._read_raw()
        target_id = RecipeIndex.recipe_id(recipe)
        replaced = False
        for idx, existing in enumerate(recipes):
            existing_recipe = Recipe.model_validate(existing)
            if RecipeIndex.recipe_id(existing_recipe) == target_id:
                recipes[idx] = recipe.model_dump()
                replaced = True
                break
        if not replaced:
            recipes.append(recipe.model_dump())
        self._write_raw(recipes)

    def lookup(self, dataset: Any, path: str | None = None) -> list[Recipe]:
        return [
            recipe
            for recipe in self.list_recipes()
            if recipe_matches_dataset(recipe, dataset, path=path)
        ]
