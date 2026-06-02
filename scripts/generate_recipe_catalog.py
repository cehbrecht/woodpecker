from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from woodpecker.recipes import RecipeLoader
from woodpecker.recipes.models import Recipe
from woodpecker.stores.json_store import JsonRecipeStore

DEFAULT_RECIPE_DIR = Path("tests/integration/recipes")
GITHUB_BLOB_BASE_URL = "https://github.com/cehbrecht/woodpecker/blob/main"
DOCS_RECIPE_ENV = "_WOODPECKER_DOCS_RECIPE_PATH"


def _markdown_cell(value: object) -> str:
    text = str(value or "")
    return text.replace("\n", "<br>").replace("|", "\\|")


def _format_match(recipe: Recipe) -> str:
    if recipe.match is None:
        return ""

    parts: list[str] = []
    if recipe.match.dataset_id_patterns:
        parts.append(f"dataset ids: {', '.join(recipe.match.dataset_id_patterns)}")
    if recipe.match.attrs:
        attrs = ", ".join(f"{key}={value}" for key, value in sorted(recipe.match.attrs.items()))
        parts.append(f"attrs: {attrs}")
    if recipe.match.path_patterns:
        parts.append(f"paths: {', '.join(recipe.match.path_patterns)}")
    return "; ".join(parts)


def _format_steps(recipe: Recipe) -> str:
    return "<br>".join(step.id for step in recipe.steps)


def _github_source_links(source_files: list[str]) -> str:
    return "<br>".join(
        f"[{source_file}]({GITHUB_BLOB_BASE_URL}/{source_file})" for source_file in source_files
    )


def _recipe_payload(recipe: Recipe, source_files: list[str], source: str) -> dict[str, Any]:
    payload = recipe.model_dump()
    payload["prefix"] = recipe.prefix
    payload["suffix"] = recipe.suffix
    payload["source"] = source
    payload["source_files"] = source_files
    payload["step_ids"] = [step.id for step in recipe.steps]
    return payload


def _add_recipe(
    recipe: Recipe,
    source_files: list[str],
    source: str,
    recipes_by_id: dict[str, Recipe],
    source_files_by_id: dict[str, list[str]],
    source_by_id: dict[str, str],
) -> None:
    existing = recipes_by_id.get(recipe.id)
    if existing is not None:
        raise ValueError(f"Duplicate definition for recipe id '{recipe.id}'")
    recipes_by_id[recipe.id] = recipe
    source_files_by_id[recipe.id] = source_files
    source_by_id[recipe.id] = source


def load_integration_recipes(
    recipe_dir: Path = DEFAULT_RECIPE_DIR,
) -> list[tuple[Recipe, list[str], str]]:
    """Load integration-test recipes, raising on duplicate recipe ids."""

    recipes_by_id: dict[str, Recipe] = {}
    source_files_by_id: dict[str, list[str]] = {}
    source_by_id: dict[str, str] = {}

    for path in sorted(recipe_dir.glob("*")):
        if path.suffix.lower() not in {".json", ".yaml", ".yml"}:
            continue

        source_label = path.as_posix()
        for recipe in JsonRecipeStore(path).list_recipes():
            _add_recipe(
                recipe,
                [source_label],
                "integration-tests",
                recipes_by_id,
                source_files_by_id,
                source_by_id,
            )

    return [
        (recipes_by_id[recipe_id], source_files_by_id[recipe_id], source_by_id[recipe_id])
        for recipe_id in sorted(recipes_by_id)
    ]


def load_plugin_recipes() -> list[tuple[Recipe, list[str], str]]:
    """Load recipe documents bundled as package resources by local plugins."""

    return load_discovered_recipes(include_core=False)


def _package_source_file(label: str) -> tuple[str, str]:
    package_resource = label.removeprefix("package:")
    package, resource_path = package_resource.split("/", 1)
    if package == "woodpecker.recipes":
        return "core", f"woodpecker/recipes/{resource_path}"
    if package.startswith("woodpecker_") and package.endswith("_plugin"):
        distribution = package.replace("_", "-")
        return "plugin:" + package, f"plugins/{distribution}/src/{package}/{resource_path}"
    return "package:" + package, package.replace(".", "/") + "/" + resource_path


def load_discovered_recipes(include_core: bool = True) -> list[tuple[Recipe, list[str], str]]:
    """Load package-bundled recipes through the same loader used at runtime."""

    loader = RecipeLoader(
        env_var=DOCS_RECIPE_ENV,
        user_dirs=(),
        system_dirs=(),
        core_packages=("woodpecker.recipes",) if include_core else (),
    )
    recipes_by_id: dict[str, Recipe] = {}
    source_files_by_id: dict[str, list[str]] = {}
    source_by_id: dict[str, str] = {}

    for document in loader.load_documents():
        source, source_file = _package_source_file(document.label)
        for recipe in document.recipes:
            _add_recipe(
                recipe,
                [source_file],
                source,
                recipes_by_id,
                source_files_by_id,
                source_by_id,
            )

    return [
        (recipes_by_id[recipe_id], source_files_by_id[recipe_id], source_by_id[recipe_id])
        for recipe_id in sorted(recipes_by_id)
    ]


def generate_recipe_catalog(
    md_path: str = "docs/recipe-reference.md",
    json_path: str = "docs/recipe-reference.json",
    recipe_dir: str = str(DEFAULT_RECIPE_DIR),
    include_plugin_recipes: bool = True,
) -> None:
    recipes = (
        load_integration_recipes(Path(recipe_dir))
        if not include_plugin_recipes
        else load_discovered_recipes(include_core=True)
    )

    md_lines = [
        "# Generated Recipes Reference",
        "",
        "This page is generated from recipe documents discovered by `RecipeLoader`.",
        "",
        "Recipes are curated workflows for selecting and applying fixes to matching datasets.",
        "",
        "Source values point to core or package-bundled plugin recipes discovered by RecipeLoader.",
        "",
        "| ID | Description | Match | Steps | Source | Source Files |",
        "|----|-------------|-------|-------|--------|--------------|",
    ]
    json_list = []

    for recipe, source_files, source in recipes:
        md_lines.append(
            f"| {_markdown_cell(recipe.id)}"
            f" | {_markdown_cell(recipe.description)}"
            f" | {_markdown_cell(_format_match(recipe))}"
            f" | {_markdown_cell(_format_steps(recipe))}"
            f" | {_markdown_cell(source)}"
            f" | {_github_source_links(source_files)} |"
        )
        json_list.append(_recipe_payload(recipe, source_files, source))

    Path(md_path).write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    Path(json_path).write_text(json.dumps(json_list, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {md_path} and {json_path} with {len(recipes)} recipes")


if __name__ == "__main__":
    generate_recipe_catalog()
