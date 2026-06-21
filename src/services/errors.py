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


class TransactionError(Exception):
  """Base class for expense/income domain errors."""


class ExpenseNotFound(TransactionError):
  """The referenced expense does not exist."""


class IncomeNotFound(TransactionError):
  """The referenced income does not exist."""


class UnknownCategory(TransactionError):
  """A transaction references a category id that does not exist."""
