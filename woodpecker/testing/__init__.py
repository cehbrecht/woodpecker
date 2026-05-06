"""Synthetic climate datasets for tests and examples."""

from .files import write_json, write_plan_document
from .paths import integration_plan_path, integration_root_dir, repository_root, testing_root_dir
from .synthetic import make_atlas, make_cmip6, make_cmip6_decadal, make_cmip7, make_cordex

__all__ = [
    "integration_plan_path",
    "integration_root_dir",
    "make_atlas",
    "make_cmip6",
    "make_cmip6_decadal",
    "make_cmip7",
    "make_cordex",
    "repository_root",
    "testing_root_dir",
    "write_json",
    "write_plan_document",
]
