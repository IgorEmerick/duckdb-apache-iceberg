"""Domain errors for the service layer.

Routers map these to HTTP status codes; the services stay transport-agnostic.
"""


class CategoryError(Exception):
  """Base class for category domain errors."""


class DuplicateCategoryName(CategoryError):
  """A category with the same name already exists."""


class CategoryNotFound(CategoryError):
  """The referenced category does not exist."""


class ProtectedCategory(CategoryError):
  """The OUTROS fallback category cannot be modified or deleted."""


class OutrosCategoryMissing(CategoryError):
  """The OUTROS fallback category is missing (data-integrity violation)."""
