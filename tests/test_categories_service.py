import duckdb
import pytest

from db.migrations import MIGRATIONS_DIR, run_migrations
from services import categories
from services.errors import (
  CategoryNotFound,
  DuplicateCategoryName,
  OutrosCategoryMissing,
  ProtectedCategory,
)

_TXN = {"expense": "expenses", "income": "incomes"}
_CAT = {"expense": "expense_categories", "income": "income_categories"}


@pytest.fixture
def conn():
  connection = duckdb.connect(":memory:")
  run_migrations(connection, MIGRATIONS_DIR)
  return connection


@pytest.mark.parametrize("kind", ["expense", "income"])
def test_list_returns_only_seeded_outros_initially(conn, kind):
  assert categories.list_categories(conn, kind) == [{"id": 1, "name": "OUTROS"}]


@pytest.mark.parametrize("kind", ["expense", "income"])
def test_create_adds_category_with_generated_id(conn, kind):
  created = categories.create_category(conn, kind, "Alimentação")

  assert created == {"id": 2, "name": "Alimentação"}
  assert {"id": 2, "name": "Alimentação"} in categories.list_categories(conn, kind)


@pytest.mark.parametrize("kind", ["expense", "income"])
def test_create_generates_sequential_ids(conn, kind):
  first = categories.create_category(conn, kind, "A")
  second = categories.create_category(conn, kind, "B")

  assert (first["id"], second["id"]) == (2, 3)


@pytest.mark.parametrize("kind", ["expense", "income"])
def test_create_rejects_duplicate_name(conn, kind):
  categories.create_category(conn, kind, "Lazer")

  with pytest.raises(DuplicateCategoryName):
    categories.create_category(conn, kind, "Lazer")


def test_create_retries_on_insert_constraint_violation(conn, monkeypatch):
  real_insert = categories._insert_category
  calls = {"n": 0}

  def flaky_insert(connection, table, id_, name):
    calls["n"] += 1
    if calls["n"] == 1:
      raise duckdb.ConstraintException("duplicate id")
    return real_insert(connection, table, id_, name)

  monkeypatch.setattr(categories, "_insert_category", flaky_insert)

  created = categories.create_category(conn, "expense", "Mercado")

  assert created == {"id": 2, "name": "Mercado"}
  assert calls["n"] >= 2  # retried after the constraint violation


@pytest.mark.parametrize("kind", ["expense", "income"])
def test_update_renames_category(conn, kind):
  created = categories.create_category(conn, kind, "Antigo")

  updated = categories.update_category(conn, kind, created["id"], "Novo")

  assert updated == {"id": created["id"], "name": "Novo"}
  names = [c["name"] for c in categories.list_categories(conn, kind)]
  assert "Novo" in names and "Antigo" not in names


@pytest.mark.parametrize("kind", ["expense", "income"])
def test_update_missing_raises_not_found(conn, kind):
  with pytest.raises(CategoryNotFound):
    categories.update_category(conn, kind, 999, "X")


@pytest.mark.parametrize("kind", ["expense", "income"])
def test_update_rejects_duplicate_name(conn, kind):
  categories.create_category(conn, kind, "A")
  b = categories.create_category(conn, kind, "B")

  with pytest.raises(DuplicateCategoryName):
    categories.update_category(conn, kind, b["id"], "A")


@pytest.mark.parametrize("kind", ["expense", "income"])
def test_update_outros_is_protected(conn, kind):
  with pytest.raises(ProtectedCategory):
    categories.update_category(conn, kind, 1, "Qualquer")


@pytest.mark.parametrize("kind", ["expense", "income"])
def test_delete_removes_category(conn, kind):
  created = categories.create_category(conn, kind, "Temp")

  categories.delete_category(conn, kind, created["id"])

  ids = [c["id"] for c in categories.list_categories(conn, kind)]
  assert created["id"] not in ids


@pytest.mark.parametrize("kind", ["expense", "income"])
def test_delete_missing_raises_not_found(conn, kind):
  with pytest.raises(CategoryNotFound):
    categories.delete_category(conn, kind, 999)


@pytest.mark.parametrize("kind", ["expense", "income"])
def test_delete_outros_is_protected(conn, kind):
  with pytest.raises(ProtectedCategory):
    categories.delete_category(conn, kind, 1)


@pytest.mark.parametrize("kind", ["expense", "income"])
def test_delete_reassigns_linked_rows_to_outros(conn, kind):
  created = categories.create_category(conn, kind, "Some")
  txn = _TXN[kind]
  conn.execute(
    f"INSERT INTO {txn} (id, category_id, description, amount_cents, month) "
    "VALUES (10, ?, 'x', 100, '2026-06')",
    [created["id"]],
  )

  categories.delete_category(conn, kind, created["id"])

  rows = conn.execute(f"SELECT category_id FROM {txn} WHERE id = 10").fetchall()
  assert rows == [(1,)]  # reassigned to OUTROS


@pytest.mark.parametrize("kind", ["expense", "income"])
def test_delete_non_outros_raises_when_fallback_missing(conn, kind):
  # Deleting a regular (non-OUTROS) category needs the OUTROS fallback to
  # reassign its linked rows. If OUTROS is gone, the delete must fail.
  victim = categories.create_category(conn, kind, "Some")  # a non-OUTROS category
  conn.execute(f"DELETE FROM {_CAT[kind]} WHERE name = 'OUTROS'")

  with pytest.raises(OutrosCategoryMissing):
    categories.delete_category(conn, kind, victim["id"])
