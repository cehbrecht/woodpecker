"""Placeholder Elasticsearch-backed RecipeStore.

This module is intentionally documentation-by-code only.

Why this exists:
- It captures the intended interface and design direction for an
  Elasticsearch-backed `RecipeStore`.
- It keeps future work discoverable without changing current runtime behavior.

Current status:
- The class is a non-operational stub.
- It is not wired into factory helpers, CLI options, or package exports.
- All operational methods raise `NotImplementedError`.

Future implementation outline:
- Connect to Elasticsearch using the official Python client.
- Store each `Recipe` as one document in a dedicated index.
- Use `recipe.id` as the document id when available.
- Implement `list_recipes()` via a search/scan query over the recipe index.
- Implement `save_recipe()` via indexing/upsert.
- Implement `lookup(dataset, path=...)` by translating dataset metadata and
  optional path hints into Elasticsearch queries.
- Optionally validate candidate results locally with existing recipe matching
  logic (`recipe_matches_dataset`) as a safety layer.

Suggested stored document shape:
- id
- description
- match
- fixes

Suggested indexed fields:
- id
- description
- match.attrs.*
- match.path_patterns
- fixes.id
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..recipes.models import Recipe
from .base import RecipeStore


class ElasticsearchRecipeStore(RecipeStore):
    """Design stub for a future Elasticsearch-backed recipe store.

    The shape of this class mirrors other store implementations (for example,
    the DuckDB-backed store) so future wiring can be straightforward.

    Parameters
    ----------
    index
        Elasticsearch index name intended for recipe documents.
    hosts
        Optional Elasticsearch host(s) configuration to use when constructing
        a client in a future implementation.
    api_key
        Optional API key placeholder for authenticated deployments.
    ca_certs
        Optional CA bundle path placeholder for TLS-enabled deployments.
    """

    def __init__(
        self,
        index: str = "woodpecker-recipes",
        hosts: list[str] | None = None,
        api_key: str | None = None,
        ca_certs: str | Path | None = None,
    ):
        self.index = str(index)
        self.hosts = list(hosts) if hosts is not None else ["http://localhost:9200"]
        self.api_key = api_key
        self.ca_certs = Path(ca_certs) if ca_certs is not None else None

    @staticmethod
    def _import_elasticsearch() -> Any:
        """Import the optional Elasticsearch dependency lazily.

        The import is deferred so this module remains safe to import in
        environments where `elasticsearch` is not installed, as long as the
        class is not used.
        """

        try:
            import elasticsearch
        except ImportError as exc:  # pragma: no cover - env-dependent
            raise RuntimeError(
                "ElasticsearchRecipeStore requires optional dependency "
                "'elasticsearch'. Install with: pip install elasticsearch"
            ) from exc
        return elasticsearch

    def _client(self) -> Any:
        """Return an Elasticsearch client object (future behavior).

        Future behavior may:
        - call `_import_elasticsearch()`
        - construct `elasticsearch.Elasticsearch(...)`
        - verify connectivity and index existence as needed.
        """

        self._import_elasticsearch()
        raise NotImplementedError(
            "ElasticsearchRecipeStore is a placeholder. Client creation is not implemented yet."
        )

    def list_recipes(self) -> list[Recipe]:
        """List all stored `Recipe` documents.

        Future behavior may execute a search/scan query and decode each hit
        into a `Recipe` instance.
        """

        raise NotImplementedError(
            "ElasticsearchRecipeStore is a placeholder. list_recipes() is not implemented yet."
        )

    def save_recipe(self, recipe: Recipe) -> None:
        """Persist a `Recipe` document.

        Future behavior may index or upsert the recipe document, using `recipe.id`
        as the Elasticsearch document id when present.
        """

        _ = recipe
        raise NotImplementedError(
            "ElasticsearchRecipeStore is a placeholder. save_recipe() is not implemented yet."
        )

    def lookup(self, dataset: Any, path: str | None = None) -> list[Recipe]:
        """Return recipes likely matching a dataset and optional file path.

        Future behavior may:
        - build Elasticsearch queries from dataset attrs/path signals,
        - fetch candidate recipes,
        - optionally run local `recipe_matches_dataset` validation for safety.
        """

        _ = (dataset, path)
        raise NotImplementedError(
            "ElasticsearchRecipeStore is a placeholder. lookup() is not implemented yet."
        )
