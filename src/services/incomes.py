"""Income service: create, read, update (partial), and delete (PyIceberg).

Incomes carry an optional description and a category that defaults to the
OUTROS income category when omitted.
"""

from pyiceberg.catalog import Catalog
from pyiceberg.expressions import EqualTo

from db import store
from services import _clock
from services._repository import insert_with_generated_id
from services.errors import (
  IncomeNotFound,
  OutrosCategoryMissing,
  UnknownCategory,
)

_TABLE = "incomes"
_CATEGORY_TABLE = "income_categories"
_OUTROS_NAME = "OUTROS"
_FIELDS = ("category_id", "description", "amount_cents", "month")


def _category_exists(catalog: Catalog, category_id: int) -> bool:
  return bool(store.rows(catalog, _CATEGORY_TABLE, EqualTo("id", category_id)))


def _outros_id(catalog: Catalog) -> int:
  rows = store.rows(catalog, _CATEGORY_TABLE, EqualTo("name", _OUTROS_NAME))
  if not rows:
    raise OutrosCategoryMissing("income")
  return rows[0]["id"]


def get_income(catalog: Catalog, income_id: int) -> dict:
  """Return the income, or raise ``IncomeNotFound``."""
  rows = store.rows(catalog, _TABLE, EqualTo("id", income_id))
  if not rows:
    raise IncomeNotFound(income_id)
  return rows[0]


def create_income(
  catalog: Catalog,
  *,
  amount_cents: int,
  month: str | None = None,
  description: str | None = None,
  category_id: int | None = None,
) -> dict:
  """Create an income.

  ``month`` defaults to the current month and ``category_id`` to the OUTROS
  income category when omitted. Raises ``UnknownCategory`` if a supplied
  ``category_id`` does not exist.
  """
  if category_id is None:
    category_id = _outros_id(catalog)
  elif not _category_exists(catalog, category_id):
    raise UnknownCategory(category_id)

  timestamp = _clock.now()
  new_id = insert_with_generated_id(
    catalog,
    _TABLE,
    {
      "category_id": category_id,
      "description": description,
      "amount_cents": amount_cents,
      "month": month if month is not None else _clock.current_month(),
      "created_at": timestamp,
      "updated_at": timestamp,
    },
  )
  return get_income(catalog, new_id)


def update_income(catalog: Catalog, income_id: int, changes: dict) -> dict:
  """Apply a partial update to an income (only the provided fields).

  Raises ``IncomeNotFound`` if missing and ``UnknownCategory`` if a provided
  ``category_id`` does not exist.
  """
  current = get_income(catalog, income_id)

  if "category_id" in changes and not _category_exists(catalog, changes["category_id"]):
    raise UnknownCategory(changes["category_id"])

  applied = {field: changes[field] for field in _FIELDS if field in changes}
  updated = {**current, **applied, "updated_at": _clock.now()}
  store.replace(catalog, _TABLE, EqualTo("id", income_id), [updated])
  return updated


def delete_income(catalog: Catalog, income_id: int) -> None:
  """Delete an income, or raise ``IncomeNotFound``."""
  get_income(catalog, income_id)
  store.delete(catalog, _TABLE, EqualTo("id", income_id))
