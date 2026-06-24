from __future__ import annotations

import os
from dataclasses import dataclass
from importlib.metadata import entry_points
from importlib.resources import as_file, files
from pathlib import Path
from typing import Iterable

from woodpecker.recipes.models import Recipe, RecipeDocument
from woodpecker.stores.catalog import RecipeCatalog
from woodpecker.stores.json_store import JsonRecipeStore
from woodpecker.stores.static_store import StaticRecipeStore

SUPPORTED_EXTENSIONS = {".json", ".yaml", ".yml"}
RECIPE_PATH_ENV = "WOODPECKER_RECIPE_PATH"
DEFAULT_SYSTEM_DIRS = (
    Path("/etc/woodpecker/recipes"),
    Path("/etc/woodpecker"),
)
DEFAULT_USER_DIRS = (
    Path.home() / ".config" / "woodpecker" / "recipes",
    Path.home() / ".woodpecker" / "recipes",
)


@dataclass(frozen=True)
class RecipeDocumentSource:
    label: str
    recipes: tuple[Recipe, ...]


def _is_supported_recipe_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS


def _iter_recipe_files(location: str | Path) -> Iterable[Path]:
    path = Path(location).expanduser()
    if _is_supported_recipe_file(path):
        yield path
        return
    if path.is_dir():
        for candidate in sorted(path.iterdir()):
            if _is_supported_recipe_file(candidate):
                yield candidate


def _iter_recipe_files_from_many(locations: Iterable[str | Path]) -> Iterable[Path]:
    for location in locations:
        yield from _iter_recipe_files(location)


def _split_path_env(value: str | None) -> list[Path]:
    if not value:
        return []
    return [Path(item).expanduser() for item in value.split(os.pathsep) if item.strip()]


def _plugin_packages() -> tuple[str, ...]:
    packages: list[str] = []
    for entry_point in entry_points(group="woodpecker.plugins"):
        package = entry_point.value.split(":", 1)[0]
        if package and package not in packages:
            packages.append(package)
    return tuple(packages)


class RecipeLoader:
    def __init__(
        self,
        *,
        user_dirs: Iterable[str | Path] | None = None,
        system_dirs: Iterable[str | Path] | None = None,
        env_var: str = RECIPE_PATH_ENV,
        core_packages: Iterable[str] = ("woodpecker.recipes",),
        plugin_packages: Iterable[str] | None = None,
        resource_dir: str = "recipes",
    ):
        self.user_dirs = tuple(Path(path).expanduser() for path in (user_dirs or DEFAULT_USER_DIRS))
        self.system_dirs = tuple(
            Path(path).expanduser() for path in (system_dirs or DEFAULT_SYSTEM_DIRS)
        )
        self.env_var = env_var
        self.core_packages = tuple(core_packages)
        self.plugin_packages = tuple(plugin_packages) if plugin_packages is not None else None
        self.resource_dir = resource_dir

    def load_document(self, location: str | Path) -> RecipeDocument:
        return RecipeDocument(recipes=JsonRecipeStore(location).list_recipes())

    def load_documents(
        self,
        explicit_locations: Iterable[str | Path] = (),
    ) -> list[RecipeDocumentSource]:
        sources: list[RecipeDocumentSource] = []
        sources.extend(self._load_files(_iter_recipe_files_from_many(explicit_locations)))
        sources.extend(
            self._load_files(_iter_recipe_files_from_many(_split_path_env(os.getenv(self.env_var))))
        )
        sources.extend(self._load_files(_iter_recipe_files_from_many(self.user_dirs)))
        sources.extend(self._load_files(_iter_recipe_files_from_many(self.system_dirs)))
        sources.extend(self._load_package_documents(self.core_packages))
        sources.extend(self._load_package_documents(self.plugin_packages or _plugin_packages()))
        return [source for source in sources if source.recipes]

    def catalog(self, explicit_locations: Iterable[str | Path] = ()) -> RecipeCatalog:
        return RecipeCatalog(
            StaticRecipeStore(source.recipes)
            for source in self.load_documents(explicit_locations=explicit_locations)
        )

    def _load_files(self, paths: Iterable[Path]) -> list[RecipeDocumentSource]:
        sources: list[RecipeDocumentSource] = []
        for path in paths:
            recipes = tuple(JsonRecipeStore(path).list_recipes())
            sources.append(RecipeDocumentSource(label=str(path), recipes=recipes))
        return sources

    def _load_package_documents(self, packages: Iterable[str]) -> list[RecipeDocumentSource]:
        sources: list[RecipeDocumentSource] = []
        for package in packages:
            try:
                recipe_dir = files(package).joinpath(self.resource_dir)
                if not recipe_dir.is_dir():
                    continue
                recipe_refs = sorted(recipe_dir.iterdir(), key=lambda ref: ref.name)
            except (FileNotFoundError, ModuleNotFoundError):
                continue

            for recipe_ref in recipe_refs:
                if not recipe_ref.name.lower().endswith(tuple(SUPPORTED_EXTENSIONS)):
                    continue
                with as_file(recipe_ref) as recipe_path:
                    recipes = tuple(JsonRecipeStore(recipe_path).list_recipes())
                sources.append(
                    RecipeDocumentSource(
                        label=f"package:{package}/{self.resource_dir}/{recipe_ref.name}",
                        recipes=recipes,
                    )
                )
        return sources


def load_recipe(path: str | Path) -> Recipe:
    recipes = RecipeLoader().load_document(path).recipes
    if not recipes:
        raise ValueError("No recipes found in recipe file")
    return recipes[0]


def load_recipe_document(path: str | Path) -> RecipeDocument:
    return RecipeLoader().load_document(path)
