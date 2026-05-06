"""Synthetic climate datasets for tests and examples."""

from .atlas import make_atlas
from .cmip6 import make_cmip6
from .cmip7 import make_cmip7
from .cordex import make_cordex
from .decadal import make_cmip6_decadal

__all__ = ["make_atlas", "make_cmip6", "make_cmip6_decadal", "make_cmip7", "make_cordex"]
