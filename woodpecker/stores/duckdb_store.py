from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from ..recipes.matcher import recipe_matches_dataset
from ..recipes.models import DatasetMatcher, FixRef, Recipe
from .base import RecipeStore
from .index import RecipeIndex


class DuckDBRecipeStore(RecipeStore):
    def __init__(self, path: str | Path | None = None):
        # Use an in-memory database when no path is provided.
        self._is_in_memory = path is None or str(path) == ":memory:"
        self._dsn = ":memory:" if self._is_in_memory else str(path)
        self.path = None if self._is_in_memory else Path(path)
        self._in_memory_connection: Any | None = None
        self._ensure_schema()

    @staticmethod
    def _import_duckdb() -> Any:
        try:
            import duckdb
        except ImportError as exc:  # pragma: no cover - exercised in environments without duckdb
            raise RuntimeError(
                "DuckDBRecipeStore requires optional dependency 'duckdb'. Install with: pip install duckdb (or pip install 'woodpecker[full]')"
            ) from exc
        return duckdb

    def _connect(self) -> Any:
        duckdb = self._import_duckdb()
        if self._is_in_memory:
            if self._in_memory_connection is None:
                self._in_memory_connection = duckdb.connect(self._dsn)
            return self._in_memory_connection

        assert self.path is not None
        self.path.parent.mkdir(parents=True, exist_ok=True)
        return duckdb.connect(self._dsn)

    @contextmanager
    def _connection(self):
        con = self._connect()
        try:
            yield con
        finally:
            if not self._is_in_memory:
                con.close()

    def close(self) -> None:
        if self._in_memory_connection is not None:
            self._in_memory_connection.close()
            self._in_memory_connection = None

    def _ensure_schema(self) -> None:
        with self._connection() as con:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS recipes (
                    id TEXT PRIMARY KEY,
                    aliases_json TEXT,
                    description TEXT,
                    match_json TEXT,
                    steps_json TEXT
                )
                """
            )
            con.execute("ALTER TABLE recipes ADD COLUMN IF NOT EXISTS aliases_json TEXT")

    def list_recipes(self) -> list[Recipe]:
        with self._connection() as con:
            rows = con.execute(
                "SELECT id, aliases_json, description, match_json, steps_json FROM recipes ORDER BY id"
            ).fetchall()

        recipes: list[Recipe] = []
        for recipe_id, aliases_json, description, match_json, steps_json in rows:
            aliases_payload = json.loads(aliases_json) if aliases_json else []
            match_payload = json.loads(match_json) if match_json else None
            steps_payload = json.loads(steps_json) if steps_json else []
            recipes.append(
                Recipe(
                    id=str(recipe_id),
                    aliases=list(aliases_payload) if isinstance(aliases_payload, list) else [],
                    description=str(description or ""),
                    match=DatasetMatcher.model_validate(match_payload)
                    if isinstance(match_payload, dict)
                    else None,
                    steps=[FixRef.model_validate(item) for item in steps_payload],
                )
            )
        return recipes

    def save_recipe(self, recipe: Recipe) -> None:
        aliases_json = json.dumps(list(recipe.aliases))
        match_json = json.dumps(recipe.match.model_dump()) if recipe.match is not None else None
        steps_json = json.dumps([item.model_dump() for item in recipe.steps])
        recipe_id = RecipeIndex.recipe_id(recipe)

        with self._connection() as con:
            con.execute(
                """
                INSERT OR REPLACE INTO recipes (id, aliases_json, description, match_json, steps_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                [recipe_id, aliases_json, recipe.description, match_json, steps_json],
            )

    @staticmethod
    def _parse_matcher(match_json: str | None) -> DatasetMatcher | None:
        match_payload = json.loads(match_json) if match_json else None
        return (
            DatasetMatcher.model_validate(match_payload)
            if isinstance(match_payload, dict)
            else None
        )

    @staticmethod
    def _parse_steps(steps_json: str | None) -> list[FixRef]:
        steps_payload = json.loads(steps_json) if steps_json else []
        return [FixRef.model_validate(item) for item in steps_payload]

    def _candidate_query(self, dataset: Any) -> tuple[str, list[Any]]:
        """Build a coarse SQL prefilter; exact recipe matching is done in Python."""

        sql = "SELECT id, aliases_json, description, match_json, steps_json FROM recipes"
        dataset_attrs = getattr(dataset, "attrs", None)
        if not isinstance(dataset_attrs, dict):
            dataset_attrs = dict(dataset_attrs or {})

        clauses: list[str] = []
        params: list[Any] = []
        for key, value in dataset_attrs.items():
            key_text = str(key)
            clauses.append(
                "("
                "match_json IS NULL "
                "OR json_extract_string(CAST(match_json AS JSON), '$.attrs."
                + key_text
                + "') IS NULL "
                "OR json_extract_string(CAST(match_json AS JSON), '$.attrs." + key_text + "') = ?"
                ")"
            )
            params.append(value)

        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY id"
        return sql, params

    def lookup(self, dataset: Any, path: str | None = None) -> list[Recipe]:
        sql, params = self._candidate_query(dataset)
        with self._connection() as con:
            rows = con.execute(sql, params).fetchall()

        matched: list[Recipe] = []
        for recipe_id, aliases_json, description, match_json, steps_json in rows:
            aliases_payload = json.loads(aliases_json) if aliases_json else []
            matcher = self._parse_matcher(match_json)
            candidate = Recipe(
                id=str(recipe_id),
                aliases=list(aliases_payload) if isinstance(aliases_payload, list) else [],
                description=str(description or ""),
                match=matcher,
                steps=[],
            )
            if not recipe_matches_dataset(candidate, dataset, path=path):
                continue

            matched.append(
                Recipe(
                    id=candidate.id,
                    aliases=candidate.aliases,
                    description=candidate.description,
                    match=matcher,
                    steps=self._parse_steps(steps_json),
                )
            )

        return matched
