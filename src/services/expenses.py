"""Expense service: create, read, update (partial), and delete expenses.

Operates over a DuckDB connection whose default database is the Iceberg catalog
(a plain in-memory database in tests), so all SQL uses unqualified table names.
"""

import duckdb

from services import _clock
from services._repository import insert_with_generated_id
from services.errors import ExpenseNotFound, UnknownCategory

_TABLE = "expenses"
_CATEGORY_TABLE = "expense_categories"
_COLUMNS = (
  "id",
  "category_id",
  "description",
  "payment_method",
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


def get_expense(conn: duckdb.DuckDBPyConnection, expense_id: int) -> dict:
  """Return the expense, or raise ``ExpenseNotFound``."""
  columns = ", ".join(_COLUMNS)
  row = conn.execute(
    f"SELECT {columns} FROM {_TABLE} WHERE id = ?", [expense_id]
  ).fetchone()
  if row is None:
    raise ExpenseNotFound(expense_id)
  return _row_to_dict(row)


def create_expense(
  conn: duckdb.DuckDBPyConnection,
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
  if not _category_exists(conn, category_id):
    raise UnknownCategory(category_id)

  timestamp = _clock.now()
  new_id = insert_with_generated_id(
    conn,
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
  return get_expense(conn, new_id)


def update_expense(
  conn: duckdb.DuckDBPyConnection, expense_id: int, changes: dict
) -> dict:
  """Apply a partial update to an expense (only the provided fields).

  Raises ``ExpenseNotFound`` if it does not exist and ``UnknownCategory`` if a
  provided ``category_id`` does not exist.
  """
  get_expense(conn, expense_id)  # raises ExpenseNotFound

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
    [*updates.values(), expense_id],
  )
  return get_expense(conn, expense_id)


def delete_expense(conn: duckdb.DuckDBPyConnection, expense_id: int) -> None:
  """Delete an expense, or raise ``ExpenseNotFound``."""
  get_expense(conn, expense_id)  # raises ExpenseNotFound
  conn.execute(f"DELETE FROM {_TABLE} WHERE id = ?", [expense_id])
