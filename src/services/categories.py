"""Category service: expense and income categories (PyIceberg writes).

Uniqueness and id generation are enforced here because Iceberg tables do not
enforce constraints.
"""

from pyiceberg.catalog import Catalog
from pyiceberg.expressions import EqualTo

from db import store
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


def _by_id(catalog: Catalog, table: str, id_: int) -> dict | None:
  rows = store.rows(catalog, table, EqualTo("id", id_))
  return rows[0] if rows else None


def _by_name(catalog: Catalog, table: str, name: str) -> dict | None:
  rows = store.rows(catalog, table, EqualTo("name", name))
  return rows[0] if rows else None


def _name_taken(
  catalog: Catalog, table: str, name: str, exclude_id: int | None = None
) -> bool:
  rows = store.rows(catalog, table, EqualTo("name", name))
  return any(row["id"] != exclude_id for row in rows)


def list_categories(catalog: Catalog, kind: str) -> list[dict]:
  """Return all categories of ``kind`` ordered by id."""
  table, _ = _tables(kind)
  rows = store.rows(catalog, table)
  return sorted(
    ({"id": row["id"], "name": row["name"]} for row in rows),
    key=lambda category: category["id"],
  )


def create_category(catalog: Catalog, kind: str, name: str) -> dict:
  """Create a category. Raises ``DuplicateCategoryName`` if the name is taken."""
  table, _ = _tables(kind)
  if _name_taken(catalog, table, name):
    raise DuplicateCategoryName(name)
  new_id = insert_with_generated_id(catalog, table, {"name": name})
  return {"id": new_id, "name": name}


def update_category(catalog: Catalog, kind: str, id_: int, name: str) -> dict:
  """Rename a category.

  Raises ``CategoryNotFound`` if missing, ``ProtectedCategory`` for OUTROS, and
  ``DuplicateCategoryName`` if another category owns ``name``.
  """
  table, _ = _tables(kind)
  current = _by_id(catalog, table, id_)
  if current is None:
    raise CategoryNotFound(id_)
  if current["name"] == OUTROS_NAME:
    raise ProtectedCategory(OUTROS_NAME)
  if _name_taken(catalog, table, name, exclude_id=id_):
    raise DuplicateCategoryName(name)

  store.replace(catalog, table, EqualTo("id", id_), [{"id": id_, "name": name}])
  return {"id": id_, "name": name}


def delete_category(catalog: Catalog, kind: str, id_: int) -> None:
  """Delete a category, reassigning its linked transactions to OUTROS.

  Raises ``CategoryNotFound`` if missing and ``ProtectedCategory`` for OUTROS.
  """
  table, txn_table = _tables(kind)
  current = _by_id(catalog, table, id_)
  if current is None:
    raise CategoryNotFound(id_)
  if current["name"] == OUTROS_NAME:
    raise ProtectedCategory(OUTROS_NAME)

  outros = _by_name(catalog, table, OUTROS_NAME)
  if outros is None:
    raise OutrosCategoryMissing(kind)

  linked = store.rows(catalog, txn_table, EqualTo("category_id", id_))
  if linked:
    reassigned = [{**row, "category_id": outros["id"]} for row in linked]
    store.replace(catalog, txn_table, EqualTo("category_id", id_), reassigned)

  store.delete(catalog, table, EqualTo("id", id_))
