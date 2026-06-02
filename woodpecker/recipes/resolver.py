from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Literal, Sequence

from woodpecker.io import DataInput, normalize_inputs
from woodpecker.recipes.models import Recipe
from woodpecker.selection import select_fixes
from woodpecker.stores.base import RecipeStore
from woodpecker.stores.helpers import create_recipe_store


@dataclass(frozen=True)
class RunContext:
    """Resolved execution context shared by `check` and `fix`.

    Precedence rules:
    - explicit CLI arguments override recipe/store-derived values
    - when `--recipe` is set, recipes are loaded through selected `--store`
    - with no recipe/store source, direct registry selection is used
    """

    inputs: list[DataInput]
    fixes: list[Any]
    selected_recipes: list[Recipe]
    resolved_dataset: str | None
    resolved_categories: tuple[str, ...]
    resolved_identifiers: tuple[str, ...]
    resolved_fix_options: dict[str, dict[str, Any]]
    resolved_output_format: str
    source: Literal["direct", "store"]


def normalize_ordered_identifiers(identifiers: Sequence[str]) -> tuple[str, ...]:
    """Normalize and deduplicate fix identifiers while preserving order."""

    out: list[str] = []
    seen: set[str] = set()
    for raw in identifiers:
        identifier = str(raw).strip()
        if not identifier or identifier in seen:
            continue
        out.append(identifier)
        seen.add(identifier)
    return tuple(out)


def _recipe_key(recipe: Recipe) -> str:
    return recipe.id or json.dumps(recipe.model_dump(), sort_keys=True)


def _finalize_matching_recipes(
    recipes: Iterable[Recipe],
    *,
    store: RecipeStore | None = None,
    recipe_id: str | None,
    not_found_message: str,
    multiple_message_prefix: str,
) -> list[Recipe]:
    """Deduplicate matched recipes, apply optional id filter, and enforce uniqueness."""

    unique: dict[str, Recipe] = {}
    for recipe in recipes:
        unique[_recipe_key(recipe)] = recipe

    matches = list(unique.values())
    if recipe_id:
        requested = recipe_id.strip()
        if store is not None:
            selected = store.get_recipe(requested)
            matches = [recipe for recipe in matches if recipe.id == selected.id]
        else:
            matches = [recipe for recipe in matches if recipe.id == requested]
        if not matches:
            raise ValueError(not_found_message.format(recipe_id=requested))

    if not matches:
        return []
    if len(matches) > 1:
        recipe_ids = [recipe.id for recipe in matches if recipe.id]
        label = ", ".join(recipe_ids) if recipe_ids else f"{len(matches)} unnamed recipes"
        raise ValueError(multiple_message_prefix + label)
    return matches


def _iter_store_matches(inputs: Sequence[DataInput], store: RecipeStore) -> list[Recipe]:
    """Collect recipes returned by store lookup across all normalized inputs."""

    out: list[Recipe] = []
    for data_input in inputs:
        dataset = data_input.load()
        try:
            out.extend(store.lookup(dataset, path=data_input.reference))
        finally:
            close = getattr(dataset, "close", None)
            if callable(close):
                close()
    return out


def select_matching_store_recipes(
    *,
    store: RecipeStore,
    inputs: Sequence[DataInput],
    recipe_id: str | None,
) -> list[Recipe]:
    """Select one matching recipe from store lookups with clear ambiguity handling."""

    return _finalize_matching_recipes(
        _iter_store_matches(inputs, store),
        store=store,
        recipe_id=recipe_id,
        not_found_message="No matching recipe found for --recipe-id '{recipe_id}'.",
        multiple_message_prefix="Multiple matching recipes found; specify --recipe-id to choose one: ",
    )


def resolve_recipe_source(
    *,
    inputs: Sequence[DataInput],
    store_type: str,
    recipe_location: Path | None,
    recipe_id: str | None,
) -> tuple[
    Literal["direct", "store"],
    list[Recipe],
    tuple[str, ...],
    dict[str, dict[str, Any]],
]:
    """Resolve recipe selection through RecipeStore with direct-mode fallback.

    Returns source marker, selected recipes, resolved identifiers, and resolved fix options.
    """

    if store_type == "auto":
        store = create_recipe_store(store_type, recipe_location)
        if recipe_id:
            selected = store.get_recipe(recipe_id.strip())
            identifiers, fix_options = selected.step_identifiers_and_options()
            return "store", [selected], identifiers, fix_options

        recipes = select_matching_store_recipes(store=store, inputs=inputs, recipe_id=recipe_id)
        if not recipes:
            raise ValueError("No matching auto recipes found for selected inputs.")

        selected = recipes[0]
        identifiers, fix_options = selected.step_identifiers_and_options()
        return "store", [selected], identifiers, fix_options

    use_catalog = store_type == "catalog" or (recipe_location is None and recipe_id is not None)
    if use_catalog:
        store = create_recipe_store("catalog", recipe_location)
        if recipe_id:
            selected = store.get_recipe(recipe_id.strip())
            identifiers, fix_options = selected.step_identifiers_and_options()
            return "store", [selected], identifiers, fix_options

        recipes = select_matching_store_recipes(store=store, inputs=inputs, recipe_id=recipe_id)
        if not recipes:
            raise ValueError("No matching discovered recipes found for selected inputs.")

        selected = recipes[0]
        identifiers, fix_options = selected.step_identifiers_and_options()
        return "store", [selected], identifiers, fix_options

    if recipe_location is None:
        return "direct", [], (), {}

    store = create_recipe_store(store_type, recipe_location)
    recipes = select_matching_store_recipes(store=store, inputs=inputs, recipe_id=recipe_id)
    if not recipes:
        raise ValueError("No matching recipes found in selected store for selected inputs.")

    selected = recipes[0]
    identifiers, fix_options = selected.step_identifiers_and_options()
    return "store", [selected], identifiers, fix_options


def resolve_target_paths(paths: tuple[Path, ...]) -> list[Path]:
    """Resolve CLI path arguments to execution inputs."""

    if paths:
        return list(paths)
    return [Path.cwd()]


def resolve_selection_inputs(
    *,
    cli_identifiers: Sequence[str],
    source_identifiers: tuple[str, ...],
    source_fix_options: dict[str, dict[str, Any]],
) -> tuple[tuple[str, ...], tuple[str, ...], dict[str, dict[str, Any]]]:
    """Resolve identifier/option precedence between CLI and recipe/store defaults."""

    normalized_cli_identifiers = normalize_ordered_identifiers(cli_identifiers)
    resolved_identifiers = normalized_cli_identifiers or source_identifiers
    resolved_ordered_identifiers = resolved_identifiers
    resolved_fix_options = {key: dict(value) for key, value in source_fix_options.items()}
    return resolved_identifiers, resolved_ordered_identifiers, resolved_fix_options


def resolve_run_context(
    *,
    paths: tuple[Path, ...],
    store_type: str,
    recipe_location: Path | None,
    recipe_id: str | None,
    dataset: str | None,
    categories: tuple[str, ...],
    identifiers: tuple[str, ...],
    output_format: str,
) -> RunContext:
    """Resolve inputs and fix selection for check/fix commands.

    Precedence:
        - store lookup when `--recipe` is provided
        - direct selection otherwise

    - explicit CLI filters (`--dataset`, `--category`, `--select`) override
      store-derived defaults
    """

    target_paths = resolve_target_paths(paths)
    inputs = normalize_inputs(target_paths)

    source, selected_recipes, source_identifiers, source_fix_options = resolve_recipe_source(
        inputs=inputs,
        store_type=store_type,
        recipe_location=recipe_location,
        recipe_id=recipe_id,
    )

    resolved_identifiers, resolved_ordered_identifiers, resolved_fix_options = (
        resolve_selection_inputs(
            cli_identifiers=identifiers,
            source_identifiers=source_identifiers,
            source_fix_options=source_fix_options,
        )
    )
    resolved_dataset = dataset
    resolved_categories = categories
    resolved_output_format = output_format

    fixes = select_fixes(
        dataset=resolved_dataset,
        categories=resolved_categories,
        identifiers=resolved_identifiers,
        strict_identifiers=True,
        fix_options=resolved_fix_options,
        ordered_identifiers=resolved_ordered_identifiers,
    )

    return RunContext(
        inputs=inputs,
        fixes=fixes,
        selected_recipes=selected_recipes,
        resolved_dataset=resolved_dataset,
        resolved_categories=tuple(resolved_categories),
        resolved_identifiers=tuple(resolved_identifiers),
        resolved_fix_options=resolved_fix_options,
        resolved_output_format=resolved_output_format,
        source=source,
    )


def resolve_load_source_recipes(
    *,
    from_recipe: Path | None,
    from_store_type: str | None,
    recipe_id: str | None,
) -> list[Recipe]:
    """Resolve source recipes for load-recipes command."""

    if from_recipe is None:
        if from_store_type not in {"auto", "catalog"}:
            raise ValueError("Provide --from-recipe as the source store location.")

    source_store_type = from_store_type or "json"
    source_store = create_recipe_store(source_store_type, from_recipe)
    recipes = list(source_store.list_recipes())

    if recipe_id:
        selected = source_store.get_recipe(recipe_id.strip())
        recipes = [recipe for recipe in recipes if recipe.id == selected.id]

    if not recipes:
        raise ValueError("No recipes found in selected source store.")

    return recipes
