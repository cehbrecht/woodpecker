from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Mapping

import yaml

from .models import DatasetMatcher, FixPlan, FixPlanDocument, FixRef, Link


def _write_optional(path: str | Path | None, text: str) -> str:
    if path is not None:
        Path(path).write_text(text, encoding="utf-8")
    return text


def _model_payload(model: Any) -> dict[str, Any]:
    return model.model_dump(exclude_defaults=True, exclude_none=True, mode="json")


def _coerce_links(links: tuple[Link | Mapping[str, Any], ...]) -> tuple[Link, ...]:
    return tuple(
        link if isinstance(link, Link) else Link.model_validate(dict(link)) for link in links
    )


@dataclass(frozen=True)
class FixStepBuilder:
    """Python builder for a configured fix step."""

    id: str
    options: Mapping[str, Any] = field(default_factory=dict)
    links: tuple[Link | Mapping[str, Any], ...] = ()

    def to_model(self) -> FixRef:
        return FixRef(id=self.id, options=dict(self.options), links=list(_coerce_links(self.links)))

    def to_payload(self) -> dict[str, Any]:
        return _model_payload(self.to_model())


@dataclass(frozen=True)
class DatasetMatcherBuilder:
    """Python builder for fix-plan dataset matching rules."""

    attrs: Mapping[str, Any] = field(default_factory=dict)
    dataset_id_patterns: tuple[str, ...] = ()
    path_patterns: tuple[str, ...] = ()

    def to_model(self) -> DatasetMatcher:
        return DatasetMatcher(
            attrs=dict(self.attrs),
            dataset_id_patterns=list(self.dataset_id_patterns),
            path_patterns=list(self.path_patterns),
        )

    def to_payload(self) -> dict[str, Any]:
        return _model_payload(self.to_model())


@dataclass(frozen=True)
class FixPlanBuilder:
    """Python builder for a fix plan document entry."""

    id: str
    description: str = ""
    aliases: tuple[str, ...] = ()
    _match: DatasetMatcherBuilder | DatasetMatcher | Mapping[str, Any] | None = None
    _steps: tuple[FixStepBuilder | FixRef | str | Mapping[str, Any], ...] = ()
    links: tuple[Link | Mapping[str, Any], ...] = ()

    def match(
        self,
        *,
        attrs: Mapping[str, Any] | None = None,
        dataset_id_patterns: tuple[str, ...] | list[str] = (),
        path_patterns: tuple[str, ...] | list[str] = (),
    ) -> FixPlanBuilder:
        return replace(
            self,
            _match=DatasetMatcherBuilder(
                attrs=dict(attrs or {}),
                dataset_id_patterns=tuple(str(item) for item in dataset_id_patterns),
                path_patterns=tuple(str(item) for item in path_patterns),
            ),
        )

    def steps(self, *items: FixStepBuilder | FixRef | str | Mapping[str, Any]) -> FixPlanBuilder:
        return replace(self, _steps=self._steps + tuple(items))

    def link(self, rel: str, href: str, title: str | None = None) -> FixPlanBuilder:
        return replace(self, links=self.links + (Link(rel=rel, href=href, title=title),))

    def to_model(self) -> FixPlan:
        payload: dict[str, Any] = {
            "id": self.id,
            "aliases": list(self.aliases),
            "description": self.description,
            "steps": [self._step_model(step) for step in self._steps],
            "links": list(_coerce_links(self.links)),
        }
        if self._match is not None:
            payload["match"] = self._match_model(self._match)
        return FixPlan.model_validate(payload)

    def to_document(self, *, schema_version: int = 1) -> FixPlanDocument:
        return FixPlanDocument(schema_version=schema_version, plans=[self.to_model()])

    def to_payload(self) -> dict[str, Any]:
        return _model_payload(self.to_model())

    def to_document_payload(self, *, schema_version: int = 1) -> dict[str, Any]:
        return _model_payload(self.to_document(schema_version=schema_version))

    def to_json(self, path: str | Path | None = None, *, schema_version: int = 1) -> str:
        text = json.dumps(self.to_document_payload(schema_version=schema_version), indent=2)
        return _write_optional(path, text)

    def to_yaml(self, path: str | Path | None = None, *, schema_version: int = 1) -> str:
        text = yaml.safe_dump(
            self.to_document_payload(schema_version=schema_version),
            sort_keys=False,
        )
        return _write_optional(path, text)

    @staticmethod
    def _step_model(step: FixStepBuilder | FixRef | str | Mapping[str, Any]) -> FixRef:
        if isinstance(step, FixStepBuilder):
            return step.to_model()
        if isinstance(step, FixRef):
            return step
        if isinstance(step, str):
            return FixRef(id=step)
        return FixRef.model_validate(dict(step))

    @staticmethod
    def _match_model(
        matcher: DatasetMatcherBuilder | DatasetMatcher | Mapping[str, Any],
    ) -> DatasetMatcher:
        if isinstance(matcher, DatasetMatcherBuilder):
            return matcher.to_model()
        if isinstance(matcher, DatasetMatcher):
            return matcher
        return DatasetMatcher.model_validate(dict(matcher))


@dataclass(frozen=True)
class FixPlanDocumentBuilder:
    """Python builder for a fix plan document."""

    plans: tuple[FixPlanBuilder | FixPlan | Mapping[str, Any], ...]
    schema_version: int = 1

    def to_model(self) -> FixPlanDocument:
        return FixPlanDocument(
            schema_version=self.schema_version,
            plans=[self._plan_model(plan) for plan in self.plans],
        )

    def to_payload(self) -> dict[str, Any]:
        return _model_payload(self.to_model())

    def to_json(self, path: str | Path | None = None) -> str:
        text = json.dumps(self.to_payload(), indent=2)
        return _write_optional(path, text)

    def to_yaml(self, path: str | Path | None = None) -> str:
        text = yaml.safe_dump(self.to_payload(), sort_keys=False)
        return _write_optional(path, text)

    @staticmethod
    def _plan_model(plan: FixPlanBuilder | FixPlan | Mapping[str, Any]) -> FixPlan:
        if isinstance(plan, FixPlanBuilder):
            return plan.to_model()
        if isinstance(plan, FixPlan):
            return plan
        return FixPlan.model_validate(dict(plan))


def fix(
    id: str,
    options: Mapping[str, Any] | None = None,
    *,
    links: tuple[Link | Mapping[str, Any], ...] | list[Link | Mapping[str, Any]] = (),
    **kwargs: Any,
) -> FixStepBuilder:
    """Create a configured fix step for a Python-authored plan."""

    merged_options = dict(options or {})
    merged_options.update(kwargs)
    return FixStepBuilder(id=id, options=merged_options, links=tuple(links))


def match(
    *,
    attrs: Mapping[str, Any] | None = None,
    dataset_id_patterns: tuple[str, ...] | list[str] = (),
    path_patterns: tuple[str, ...] | list[str] = (),
) -> DatasetMatcherBuilder:
    """Create dataset matching rules for a Python-authored plan."""

    return DatasetMatcherBuilder(
        attrs=dict(attrs or {}),
        dataset_id_patterns=tuple(str(item) for item in dataset_id_patterns),
        path_patterns=tuple(str(item) for item in path_patterns),
    )


def plan(
    id: str,
    *steps: FixStepBuilder | FixRef | str | Mapping[str, Any],
    description: str = "",
    aliases: tuple[str, ...] | list[str] = (),
    match: DatasetMatcherBuilder | DatasetMatcher | Mapping[str, Any] | None = None,
    links: tuple[Link | Mapping[str, Any], ...] | list[Link | Mapping[str, Any]] = (),
) -> FixPlanBuilder:
    """Create a Python-authored fix plan."""

    return FixPlanBuilder(
        id=id,
        description=description,
        aliases=tuple(str(alias) for alias in aliases),
        _match=match,
        _steps=tuple(steps),
        links=tuple(links),
    )


def document(
    *plans: FixPlanBuilder | FixPlan | Mapping[str, Any],
    schema_version: int = 1,
) -> FixPlanDocumentBuilder:
    """Create a Python-authored fix plan document."""

    return FixPlanDocumentBuilder(plans=tuple(plans), schema_version=schema_version)
