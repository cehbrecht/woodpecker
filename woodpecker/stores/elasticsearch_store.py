"""Placeholder Elasticsearch-backed FixPlanStore.

This module is intentionally documentation-by-code only.

Why this exists:
- It captures the intended interface and design direction for an
  Elasticsearch-backed `FixPlanStore`.
- It keeps future work discoverable without changing current runtime behavior.

Current status:
- The class is a non-operational stub.
- It is not wired into factory helpers, CLI options, or package exports.
- All operational methods raise `NotImplementedError`.

Future implementation outline:
- Connect to Elasticsearch using the official Python client.
- Store each `FixPlan` as one document in a dedicated index.
- Use `plan.id` as the document id when available.
- Implement `list_plans()` via a search/scan query over the plan index.
- Implement `save_plan()` via indexing/upsert.
- Implement `lookup(dataset, path=...)` by translating dataset metadata and
  optional path hints into Elasticsearch queries.
- Optionally validate candidate results locally with existing plan matching
  logic (`plan_matches_dataset`) as a safety layer.

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

from ..plans.models import FixPlan
from .base import FixPlanStore


class ElasticsearchFixPlanStore(FixPlanStore):
    """Design stub for a future Elasticsearch-backed plan store.

    The shape of this class mirrors other store implementations (for example,
    the DuckDB-backed store) so future wiring can be straightforward.

    Parameters
    ----------
    index
        Elasticsearch index name intended for fix plan documents.
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
        index: str = "woodpecker-fix-plans",
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
                "ElasticsearchFixPlanStore requires optional dependency "
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
            "ElasticsearchFixPlanStore is a placeholder. Client creation is not implemented yet."
        )

    def list_plans(self) -> list[FixPlan]:
        """List all stored `FixPlan` documents.

        Future behavior may execute a search/scan query and decode each hit
        into a `FixPlan` instance.
        """

        raise NotImplementedError(
            "ElasticsearchFixPlanStore is a placeholder. list_plans() is not implemented yet."
        )

    def save_plan(self, plan: FixPlan) -> None:
        """Persist a `FixPlan` document.

        Future behavior may index or upsert the plan document, using `plan.id`
        as the Elasticsearch document id when present.
        """

        _ = plan
        raise NotImplementedError(
            "ElasticsearchFixPlanStore is a placeholder. save_plan() is not implemented yet."
        )

    def lookup(self, dataset: Any, path: str | None = None) -> list[FixPlan]:
        """Return plans likely matching a dataset and optional file path.

        Future behavior may:
        - build Elasticsearch queries from dataset attrs/path signals,
        - fetch candidate plans,
        - optionally run local `plan_matches_dataset` validation for safety.
        """

        _ = (dataset, path)
        raise NotImplementedError(
            "ElasticsearchFixPlanStore is a placeholder. lookup() is not implemented yet."
        )
