from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FixLabel:
    """User-facing informational label for fix metadata."""

    id: str
    title: str
    description: str = ""
    group: str = "tag"

    def to_dict(self) -> dict[str, str]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "group": self.group,
        }


class RiskLabels:
    """Predefined risk labels used by core fixes and bundled plugins."""

    REVIEW_BEFORE_APPLYING = "risk.careful.review"
    METADATA_ONLY = "risk.safe.metadata_only"
    ENCODING_METADATA = "risk.safe.encoding_metadata"
    REVERSIBLE_RENAME = "risk.safe.reversible_rename"
    SAFE_COORDINATE_CREATION = "risk.safe.coordinate_creation"
    VALUE_TRANSFORMATION = "risk.careful.value_transformation"
    COORDINATE_REORDERING = "risk.careful.coordinate_reordering"
    DIMENSION_REMAPPING = "risk.careful.dimension_remapping"
    COORDINATE_TRANSFORMATION = "risk.careful.coordinate_transformation"
    VARIABLE_REMOVAL = "risk.careful.variable_removal"
    VARIABLE_CREATION = "risk.careful.variable_creation"
    DTYPE_TRANSFORMATION = "risk.careful.dtype_transformation"
    COORDINATE_CREATION = "risk.careful.coordinate_creation"
    WORKFLOW_TRANSFORMATION = "risk.careful.workflow_transformation"


class FixLabelRegistry:
    """Extensible registry for user-facing fix labels.

    Labels are informational metadata. They are not used for selection,
    priority, recipe matching, or automation decisions.
    """

    _labels: dict[str, FixLabel] = {}

    @classmethod
    def register(
        cls,
        label_id: str,
        title: str,
        *,
        description: str = "",
        group: str = "tag",
        override: bool = False,
    ) -> FixLabel:
        label = FixLabel(
            id=str(label_id).strip(),
            title=str(title).strip(),
            description=str(description or "").strip(),
            group=str(group or "tag").strip(),
        )
        if not label.id:
            raise ValueError("Label id must be non-empty")
        if not label.title:
            raise ValueError("Label title must be non-empty")
        if label.id in cls._labels and not override:
            raise ValueError(f"Duplicate label id: {label.id}")
        cls._labels[label.id] = label
        return label

    @classmethod
    def get(cls, label_id: str) -> FixLabel | None:
        return cls._labels.get(str(label_id).strip())

    @classmethod
    def title(cls, label_id: str) -> str:
        key = str(label_id).strip()
        label = cls.get(key)
        if label is None:
            return key
        return label.title

    @classmethod
    def metadata(cls, label_id: str) -> dict[str, str]:
        key = str(label_id).strip()
        label = cls.get(key)
        if label is None:
            return FixLabel(id=key, title=key, group="custom").to_dict()
        return label.to_dict()

    @classmethod
    def list_labels(cls, *, group: str | None = None) -> list[FixLabel]:
        labels = cls._labels.values()
        if group is not None:
            labels = [label for label in labels if label.group == group]
        return sorted(labels, key=lambda label: label.id)


def register_fix_label(
    label_id: str,
    title: str,
    *,
    description: str = "",
    group: str = "tag",
    override: bool = False,
) -> FixLabel:
    """Register a custom informational label for fixes or plugins."""

    return FixLabelRegistry.register(
        label_id,
        title,
        description=description,
        group=group,
        override=override,
    )


def _register_builtin_labels() -> None:
    builtins = [
        (
            RiskLabels.REVIEW_BEFORE_APPLYING,
            "careful: review before applying",
            "Default risk label for fixes that have not declared a more specific risk.",
        ),
        (RiskLabels.METADATA_ONLY, "safe: metadata only", "Changes metadata without changing data values."),
        (
            RiskLabels.ENCODING_METADATA,
            "safe: encoding metadata",
            "Changes encoding or persistence metadata without changing data values.",
        ),
        (
            RiskLabels.REVERSIBLE_RENAME,
            "safe: reversible rename",
            "Renames variables, coordinates, or dimensions without changing values.",
        ),
        (
            RiskLabels.SAFE_COORDINATE_CREATION,
            "safe: coordinate creation",
            "Creates coordinate markers from existing dimensions or values.",
        ),
        (
            RiskLabels.VALUE_TRANSFORMATION,
            "careful: value transformation",
            "Transforms data or coordinate values.",
        ),
        (
            RiskLabels.COORDINATE_REORDERING,
            "careful: coordinate reordering",
            "Reorders coordinate-dependent data.",
        ),
        (
            RiskLabels.DIMENSION_REMAPPING,
            "careful: dimension remapping",
            "Remaps dimensions or dimension relationships.",
        ),
        (
            RiskLabels.COORDINATE_TRANSFORMATION,
            "careful: coordinate transformation",
            "Transforms coordinate values, bounds, or geometry.",
        ),
        (
            RiskLabels.VARIABLE_REMOVAL,
            "careful: variable removal",
            "Removes variables or coordinates.",
        ),
        (
            RiskLabels.VARIABLE_CREATION,
            "careful: variable creation",
            "Creates variables from existing metadata or values.",
        ),
        (
            RiskLabels.DTYPE_TRANSFORMATION,
            "careful: dtype transformation",
            "Changes variable or coordinate data types.",
        ),
        (
            RiskLabels.COORDINATE_CREATION,
            "careful: coordinate creation",
            "Creates derived coordinates or coordinate values.",
        ),
        (
            RiskLabels.WORKFLOW_TRANSFORMATION,
            "careful: workflow transformation",
            "Applies a composed workflow with structural and metadata changes.",
        ),
    ]
    for label_id, title, description in builtins:
        FixLabelRegistry.register(label_id, title, description=description, group="risk")


_register_builtin_labels()
