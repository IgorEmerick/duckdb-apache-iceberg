"""Expense service: create, read, update (partial), and delete (PyIceberg)."""

from pyiceberg.catalog import Catalog
from pyiceberg.expressions import EqualTo

from db import store
from services import _clock
from services._repository import insert_with_generated_id
from services.errors import ExpenseNotFound, UnknownCategory

_TABLE = "expenses"
_CATEGORY_TABLE = "expense_categories"
_FIELDS = (
  "category_id",
  "description",
  "payment_method",
  "amount_cents",
  "month",
)


def _category_exists(catalog: Catalog, category_id: int) -> bool:
  return bool(store.rows(catalog, _CATEGORY_TABLE, EqualTo("id", category_id)))


def get_expense(catalog: Catalog, expense_id: int) -> dict:
  """Return the expense, or raise ``ExpenseNotFound``."""
  rows = store.rows(catalog, _TABLE, EqualTo("id", expense_id))
  if not rows:
    raise ExpenseNotFound(expense_id)
  return rows[0]


def create_expense(
  catalog: Catalog,
  *,
  category_id: int,
  description: str,
  payment_method: str,
  amount_cents: int,
  month: str | None = None,
) -> dict:
  """Create an expense. ``month`` defaults to the current month when omitted.

  Raises ``UnknownCategory`` if ``category_id`` does not exist.
  """
  if not _category_exists(catalog, category_id):
    raise UnknownCategory(category_id)

  timestamp = _clock.now()
  new_id = insert_with_generated_id(
    catalog,
    _TABLE,
    {
      "category_id": category_id,
      "description": description,
      "payment_method": payment_method,
      "amount_cents": amount_cents,
      "month": month if month is not None else _clock.current_month(),
      "created_at": timestamp,
      "updated_at": timestamp,
    },
  )
  return get_expense(catalog, new_id)


def update_expense(catalog: Catalog, expense_id: int, changes: dict) -> dict:
  """Apply a partial update to an expense (only the provided fields).

  Raises ``ExpenseNotFound`` if missing and ``UnknownCategory`` if a provided
  ``category_id`` does not exist.
  """
  current = get_expense(catalog, expense_id)

  if "category_id" in changes and not _category_exists(catalog, changes["category_id"]):
    raise UnknownCategory(changes["category_id"])

  applied = {field: changes[field] for field in _FIELDS if field in changes}
  updated = {**current, **applied, "updated_at": _clock.now()}
  store.replace(catalog, _TABLE, EqualTo("id", expense_id), [updated])
  return updated


def delete_expense(catalog: Catalog, expense_id: int) -> None:
  """Delete an expense, or raise ``ExpenseNotFound``."""
  get_expense(catalog, expense_id)
  store.delete(catalog, _TABLE, EqualTo("id", expense_id))
