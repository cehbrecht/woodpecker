from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Label:
    """User-facing informational metadata label."""

    id: str
    title: str
    description: str = ""
    category: str = "info"

    def to_dict(self) -> dict[str, str]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
        }


class LabelCategories:
    """Predefined label categories."""

    INFO = "info"
    RISK_LOW = "risk-low"
    RISK_MEDIUM = "risk-medium"
    RISK_HIGH = "risk-high"

    RISK = (RISK_LOW, RISK_MEDIUM, RISK_HIGH)


class Labels:
    """Predefined label ids."""

    REVIEW_BEFORE_APPLYING = "label.review_before_applying"
    METADATA_ONLY = "label.metadata_only"
    ENCODING_METADATA = "label.encoding_metadata"
    REVERSIBLE_RENAME = "label.reversible_rename"
    SAFE_COORDINATE_CREATION = "label.coordinate_marker_creation"
    VALUE_TRANSFORMATION = "label.value_transformation"
    COORDINATE_REORDERING = "label.coordinate_reordering"
    DIMENSION_REMAPPING = "label.dimension_remapping"
    COORDINATE_TRANSFORMATION = "label.coordinate_transformation"
    VARIABLE_REMOVAL = "label.variable_removal"
    VARIABLE_CREATION = "label.variable_creation"
    DTYPE_TRANSFORMATION = "label.dtype_transformation"
    COORDINATE_CREATION = "label.derived_coordinate_creation"
    WORKFLOW_TRANSFORMATION = "label.workflow_transformation"


class LabelRegistry:
    """Extensible registry for user-facing labels.

    Labels are informational metadata. They are not used for selection,
    priority, recipe matching, or automation decisions.
    """

    _labels: dict[str, Label] = {}

    @classmethod
    def register(
        cls,
        label_id: str,
        title: str,
        *,
        description: str = "",
        category: str = "info",
        override: bool = False,
    ) -> Label:
        label = Label(
            id=str(label_id).strip(),
            title=str(title).strip(),
            description=str(description or "").strip(),
            category=str(category or LabelCategories.INFO).strip(),
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
    def get(cls, label_id: str) -> Label | None:
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
            return Label(id=key, title=key, category=LabelCategories.INFO).to_dict()
        return label.to_dict()

    @classmethod
    def list_labels(cls, *, category: str | None = None) -> list[Label]:
        labels = cls._labels.values()
        if category is not None:
            labels = [label for label in labels if label.category == category]
        return sorted(labels, key=lambda label: label.id)

    @classmethod
    def labels_with_category(cls, label_ids: list[str], category: str) -> list[Label]:
        return [
            label
            for label_id in label_ids
            if (label := cls.get(label_id)) is not None and label.category == category
        ]


def register_label(
    label_id: str,
    title: str,
    *,
    description: str = "",
    category: str = "info",
    override: bool = False,
) -> Label:
    """Register a custom informational label."""

    return LabelRegistry.register(
        label_id,
        title,
        description=description,
        category=category,
        override=override,
    )


def _register_builtin_labels() -> None:
    builtins = [
        (
            Labels.REVIEW_BEFORE_APPLYING,
            "careful: review before applying",
            "Default label for fixes that should be reviewed before applying.",
            LabelCategories.RISK_MEDIUM,
        ),
        (
            Labels.METADATA_ONLY,
            "safe: metadata only",
            "Changes metadata without changing data values.",
            LabelCategories.RISK_LOW,
        ),
        (
            Labels.ENCODING_METADATA,
            "safe: encoding metadata",
            "Changes encoding or persistence metadata without changing data values.",
            LabelCategories.RISK_LOW,
        ),
        (
            Labels.REVERSIBLE_RENAME,
            "safe: reversible rename",
            "Renames variables, coordinates, or dimensions without changing values.",
            LabelCategories.RISK_LOW,
        ),
        (
            Labels.SAFE_COORDINATE_CREATION,
            "safe: coordinate creation",
            "Creates coordinate markers from existing dimensions or values.",
            LabelCategories.RISK_LOW,
        ),
        (
            Labels.VALUE_TRANSFORMATION,
            "careful: value transformation",
            "Transforms data or coordinate values.",
            LabelCategories.RISK_MEDIUM,
        ),
        (
            Labels.COORDINATE_REORDERING,
            "careful: coordinate reordering",
            "Reorders coordinate-dependent data.",
            LabelCategories.RISK_MEDIUM,
        ),
        (
            Labels.DIMENSION_REMAPPING,
            "careful: dimension remapping",
            "Remaps dimensions or dimension relationships.",
            LabelCategories.RISK_MEDIUM,
        ),
        (
            Labels.COORDINATE_TRANSFORMATION,
            "careful: coordinate transformation",
            "Transforms coordinate values, bounds, or geometry.",
            LabelCategories.RISK_MEDIUM,
        ),
        (
            Labels.VARIABLE_REMOVAL,
            "careful: variable removal",
            "Removes variables or coordinates.",
            LabelCategories.RISK_MEDIUM,
        ),
        (
            Labels.VARIABLE_CREATION,
            "careful: variable creation",
            "Creates variables from existing metadata or values.",
            LabelCategories.RISK_MEDIUM,
        ),
        (
            Labels.DTYPE_TRANSFORMATION,
            "careful: dtype transformation",
            "Changes variable or coordinate data types.",
            LabelCategories.RISK_MEDIUM,
        ),
        (
            Labels.COORDINATE_CREATION,
            "careful: coordinate creation",
            "Creates derived coordinates or coordinate values.",
            LabelCategories.RISK_MEDIUM,
        ),
        (
            Labels.WORKFLOW_TRANSFORMATION,
            "careful: workflow transformation",
            "Applies a composed workflow with structural and metadata changes.",
            LabelCategories.RISK_HIGH,
        ),
    ]
    for label_id, title, description, category in builtins:
        LabelRegistry.register(label_id, title, description=description, category=category)


_register_builtin_labels()
