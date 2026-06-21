"""Income service: create, read, update (partial), and delete incomes.

Mirrors the expense service. Incomes carry an optional description and a
category that defaults to the OUTROS income category when omitted.
"""

import duckdb

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
_COLUMNS = (
  "id",
  "category_id",
  "description",
  "amount_cents",
  "month",
  "created_at",
  "updated_at",
)


def _row_to_dict(row: tuple) -> dict:
  return dict(zip(_COLUMNS, row, strict=True))


def _category_exists(conn: duckdb.DuckDBPyConnection, category_id: int) -> bool:
  rows = conn.execute(
    f"SELECT 1 FROM {_CATEGORY_TABLE} WHERE id = ?", [category_id]
  ).fetchall()
  return len(rows) > 0


def _outros_id(conn: duckdb.DuckDBPyConnection) -> int:
  row = conn.execute(
    f"SELECT id FROM {_CATEGORY_TABLE} WHERE name = ?", [_OUTROS_NAME]
  ).fetchone()
  if row is None:
    raise OutrosCategoryMissing("income")
  return row[0]


def get_income(conn: duckdb.DuckDBPyConnection, income_id: int) -> dict:
  """Return the income, or raise ``IncomeNotFound``."""
  columns = ", ".join(_COLUMNS)
  row = conn.execute(
    f"SELECT {columns} FROM {_TABLE} WHERE id = ?", [income_id]
  ).fetchone()
  if row is None:
    raise IncomeNotFound(income_id)
  return _row_to_dict(row)


def create_income(
  conn: duckdb.DuckDBPyConnection,
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
    category_id = _outros_id(conn)
  elif not _category_exists(conn, category_id):
    raise UnknownCategory(category_id)

  timestamp = _clock.now()
  new_id = insert_with_generated_id(
    conn,
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
  return get_income(conn, new_id)


def update_income(
  conn: duckdb.DuckDBPyConnection, income_id: int, changes: dict
) -> dict:
  """Apply a partial update to an income (only the provided fields).

  Raises ``IncomeNotFound`` if it does not exist and ``UnknownCategory`` if a
  provided ``category_id`` does not exist.
  """
  get_income(conn, income_id)  # raises IncomeNotFound

  if "category_id" in changes and not _category_exists(conn, changes["category_id"]):
    raise UnknownCategory(changes["category_id"])

  updates = {
    column: value
    for column, value in changes.items()
    if column in _COLUMNS and column != "id"
  }
  updates["updated_at"] = _clock.now()
  set_sql = ", ".join(f"{column} = ?" for column in updates)
  conn.execute(
    f"UPDATE {_TABLE} SET {set_sql} WHERE id = ?",
    [*updates.values(), income_id],
  )
  return get_income(conn, income_id)


def delete_income(conn: duckdb.DuckDBPyConnection, income_id: int) -> None:
  """Delete an income, or raise ``IncomeNotFound``."""
  get_income(conn, income_id)  # raises IncomeNotFound
  conn.execute(f"DELETE FROM {_TABLE} WHERE id = ?", [income_id])
