"""Built-in dataset identity resolver plugins."""

from .fallback import FallbackDatasetIdentityResolver

__all__ = [
	"FallbackDatasetIdentityResolver",
]
