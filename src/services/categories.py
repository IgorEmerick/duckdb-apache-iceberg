"""Category service: expense and income categories.

Operates over a DuckDB connection whose default database is the Iceberg catalog
(in tests, a plain in-memory database) so all SQL uses unqualified table names.
Uniqueness and id generation are enforced here because Iceberg-backed tables do
not enforce constraints.
"""

import duckdb

from services._repository import insert_with_generated_id
from services.errors import (
  CategoryNotFound,
  DuplicateCategoryName,
  OutrosCategoryMissing,
  ProtectedCategory,
)

OUTROS_NAME = "OUTROS"

# kind -> (category table, linked transactions table)
_TABLES = {
  "expense": ("expense_categories", "expenses"),
  "income": ("income_categories", "incomes"),
}


def _tables(kind: str) -> tuple[str, str]:
  try:
    return _TABLES[kind]
  except KeyError:
    raise ValueError(f"unknown category kind: {kind!r}") from None


def _name_exists(
  conn: duckdb.DuckDBPyConnection,
  table: str,
  name: str,
  exclude_id: int | None = None,
) -> bool:
  if exclude_id is None:
    rows = conn.execute(f"SELECT 1 FROM {table} WHERE name = ?", [name]).fetchall()
  else:
    rows = conn.execute(
      f"SELECT 1 FROM {table} WHERE name = ? AND id <> ?", [name, exclude_id]
    ).fetchall()
  return len(rows) > 0


def list_categories(conn: duckdb.DuckDBPyConnection, kind: str) -> list[dict]:
  """Return all categories of ``kind`` ordered by id."""
  table, _ = _tables(kind)
  rows = conn.execute(f"SELECT id, name FROM {table} ORDER BY id").fetchall()
  return [{"id": row[0], "name": row[1]} for row in rows]


def create_category(conn: duckdb.DuckDBPyConnection, kind: str, name: str) -> dict:
  """Create a category, generating its id as ``max(id) + 1``.

  Raises ``DuplicateCategoryName`` if the name is taken. Id generation and the
  retry-on-constraint behaviour live in ``services._repository``.
  """
  table, _ = _tables(kind)
  if _name_exists(conn, table, name):
    raise DuplicateCategoryName(name)

  new_id = insert_with_generated_id(conn, table, {"name": name})
  return {"id": new_id, "name": name}


def _get_name(conn: duckdb.DuckDBPyConnection, table: str, id_: int) -> str | None:
  row = conn.execute(f"SELECT name FROM {table} WHERE id = ?", [id_]).fetchone()
  return None if row is None else row[0]


def update_category(
  conn: duckdb.DuckDBPyConnection, kind: str, id_: int, name: str
) -> dict:
  """Rename a category.

  Raises ``CategoryNotFound`` if it does not exist, ``ProtectedCategory`` for
  OUTROS, and ``DuplicateCategoryName`` if another category owns ``name``.
  """
  table, _ = _tables(kind)
  current = _get_name(conn, table, id_)
  if current is None:
    raise CategoryNotFound(id_)
  if current == OUTROS_NAME:
    raise ProtectedCategory(OUTROS_NAME)
  if _name_exists(conn, table, name, exclude_id=id_):
    raise DuplicateCategoryName(name)

  conn.execute(f"UPDATE {table} SET name = ? WHERE id = ?", [name, id_])
  return {"id": id_, "name": name}


def delete_category(conn: duckdb.DuckDBPyConnection, kind: str, id_: int) -> None:
  """Delete a category, reassigning its linked transactions to OUTROS.

  Raises ``CategoryNotFound`` if it does not exist and ``ProtectedCategory``
  for OUTROS.
  """
  table, txn_table = _tables(kind)
  current = _get_name(conn, table, id_)
  if current is None:
    raise CategoryNotFound(id_)
  if current == OUTROS_NAME:
    raise ProtectedCategory(OUTROS_NAME)

  outros = conn.execute(
    f"SELECT id FROM {table} WHERE name = ?", [OUTROS_NAME]
  ).fetchone()
  if outros is None:
    raise OutrosCategoryMissing(kind)
  outros_id = outros[0]
  conn.execute(
    f"UPDATE {txn_table} SET category_id = ? WHERE category_id = ?",
    [outros_id, id_],
  )
  conn.execute(f"DELETE FROM {table} WHERE id = ?", [id_])
