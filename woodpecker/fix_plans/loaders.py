from __future__ import annotations

import os
from dataclasses import dataclass
from importlib.metadata import entry_points
from importlib.resources import as_file, files
from pathlib import Path
from typing import Iterable

from woodpecker.fix_plans.models import FixPlan, FixPlanDocument
from woodpecker.stores.catalog import FixPlanCatalog
from woodpecker.stores.json_store import JsonFixPlanStore
from woodpecker.stores.static_store import StaticFixPlanStore

SUPPORTED_EXTENSIONS = {".json", ".yaml", ".yml"}
FIX_PLAN_PATH_ENV = "WOODPECKER_FIX_PLAN_PATH"
DEFAULT_SYSTEM_DIRS = (
    Path("/etc/woodpecker/fix-plans"),
    Path("/etc/woodpecker/plans"),
    Path("/etc/woodpecker"),
)
DEFAULT_USER_DIRS = (
    Path.home() / ".config" / "woodpecker" / "fix-plans",
    Path.home() / ".woodpecker" / "fix-plans",
    Path.home() / ".woodpecker" / "plans",
)


@dataclass(frozen=True)
class FixPlanDocumentSource:
    """Loaded fix-plan document plus the location it came from."""

    label: str
    plans: tuple[FixPlan, ...]


def _is_supported_plan_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS


def _iter_plan_files(location: str | Path) -> Iterable[Path]:
    path = Path(location).expanduser()
    if _is_supported_plan_file(path):
        yield path
        return
    if path.is_dir():
        for candidate in sorted(path.iterdir()):
            if _is_supported_plan_file(candidate):
                yield candidate


def _iter_plan_files_from_many(locations: Iterable[str | Path]) -> Iterable[Path]:
    for location in locations:
        yield from _iter_plan_files(location)


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


class FixPlanLoader:
    """Coordinate fix-plan discovery across explicit, user, system, core, and plugin locations."""

    def __init__(
        self,
        *,
        user_dirs: Iterable[str | Path] | None = None,
        system_dirs: Iterable[str | Path] | None = None,
        env_var: str = FIX_PLAN_PATH_ENV,
        core_packages: Iterable[str] = ("woodpecker.fix_plans",),
        plugin_packages: Iterable[str] | None = None,
        resource_dir: str = "plans",
    ):
        self.user_dirs = tuple(Path(path).expanduser() for path in (user_dirs or DEFAULT_USER_DIRS))
        self.system_dirs = tuple(
            Path(path).expanduser() for path in (system_dirs or DEFAULT_SYSTEM_DIRS)
        )
        self.env_var = env_var
        self.core_packages = tuple(core_packages)
        self.plugin_packages = tuple(plugin_packages) if plugin_packages is not None else None
        self.resource_dir = resource_dir

    def load_document(self, location: str | Path) -> FixPlanDocument:
        """Load a single fix-plan document from an explicit file path."""

        return FixPlanDocument(plans=JsonFixPlanStore(location).list_plans())

    def load_documents(
        self,
        explicit_locations: Iterable[str | Path] = (),
    ) -> list[FixPlanDocumentSource]:
        """Load all discovered fix-plan documents in precedence order."""

        sources: list[FixPlanDocumentSource] = []
        sources.extend(self._load_files(_iter_plan_files_from_many(explicit_locations)))
        sources.extend(
            self._load_files(_iter_plan_files_from_many(_split_path_env(os.getenv(self.env_var))))
        )
        sources.extend(self._load_files(_iter_plan_files_from_many(self.user_dirs)))
        sources.extend(self._load_files(_iter_plan_files_from_many(self.system_dirs)))
        sources.extend(self._load_package_documents(self.core_packages))
        sources.extend(self._load_package_documents(self.plugin_packages or _plugin_packages()))
        return [source for source in sources if source.plans]

    def catalog(self, explicit_locations: Iterable[str | Path] = ()) -> FixPlanCatalog:
        """Return a read-only catalog over all discovered plans."""

        return FixPlanCatalog(
            StaticFixPlanStore(source.plans)
            for source in self.load_documents(explicit_locations=explicit_locations)
        )

    def _load_files(self, paths: Iterable[Path]) -> list[FixPlanDocumentSource]:
        sources: list[FixPlanDocumentSource] = []
        for path in paths:
            plans = tuple(JsonFixPlanStore(path).list_plans())
            sources.append(FixPlanDocumentSource(label=str(path), plans=plans))
        return sources

    def _load_package_documents(self, packages: Iterable[str]) -> list[FixPlanDocumentSource]:
        sources: list[FixPlanDocumentSource] = []
        for package in packages:
            try:
                plan_dir = files(package).joinpath(self.resource_dir)
                if not plan_dir.is_dir():
                    continue
                plan_refs = sorted(plan_dir.iterdir(), key=lambda ref: ref.name)
            except (FileNotFoundError, ModuleNotFoundError):
                continue

            for plan_ref in plan_refs:
                if not plan_ref.name.lower().endswith(tuple(SUPPORTED_EXTENSIONS)):
                    continue
                with as_file(plan_ref) as plan_path:
                    plans = tuple(JsonFixPlanStore(plan_path).list_plans())
                sources.append(
                    FixPlanDocumentSource(
                        label=f"package:{package}/{self.resource_dir}/{plan_ref.name}",
                        plans=plans,
                    )
                )
        return sources


def load_fix_plan(path: str | Path) -> FixPlan:
    plans = FixPlanLoader().load_document(path).plans
    if not plans:
        raise ValueError("No plans found in fix plan file")
    return plans[0]


def load_fix_plan_document(path: str | Path) -> FixPlanDocument:
    return FixPlanLoader().load_document(path)
