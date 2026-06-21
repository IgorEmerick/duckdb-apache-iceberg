import datetime as dt

import pytest

from db import store
from services import categories
from services.errors import (
  CategoryNotFound,
  DuplicateCategoryName,
  OutrosCategoryMissing,
  ProtectedCategory,
)

_TXN = {"expense": "expenses", "income": "incomes"}
_CAT = {"expense": "expense_categories", "income": "income_categories"}


def _add_linked_row(catalog, kind, row_id, category_id):
  now = dt.datetime(2026, 6, 1)
  if kind == "expense":
    store.append(
      catalog,
      "expenses",
      {
        "id": row_id,
        "category_id": category_id,
        "description": "x",
        "payment_method": "CASH",
        "amount_cents": 100,
        "month": "2026-06",
        "created_at": now,
        "updated_at": now,
      },
    )
  else:
    store.append(
      catalog,
      "incomes",
      {
        "id": row_id,
        "category_id": category_id,
        "description": "x",
        "amount_cents": 100,
        "month": "2026-06",
        "created_at": now,
        "updated_at": now,
      },
    )


@pytest.mark.parametrize("kind", ["expense", "income"])
def test_list_returns_only_seeded_outros_initially(catalog, kind):
  assert categories.list_categories(catalog, kind) == [{"id": 1, "name": "OUTROS"}]


@pytest.mark.parametrize("kind", ["expense", "income"])
def test_create_adds_category_with_generated_id(catalog, kind):
  created = categories.create_category(catalog, kind, "Alimentação")

  assert created == {"id": 2, "name": "Alimentação"}
  assert created in categories.list_categories(catalog, kind)


@pytest.mark.parametrize("kind", ["expense", "income"])
def test_create_generates_sequential_ids(catalog, kind):
  first = categories.create_category(catalog, kind, "A")
  second = categories.create_category(catalog, kind, "B")

  assert (first["id"], second["id"]) == (2, 3)


@pytest.mark.parametrize("kind", ["expense", "income"])
def test_create_rejects_duplicate_name(catalog, kind):
  categories.create_category(catalog, kind, "Lazer")

  with pytest.raises(DuplicateCategoryName):
    categories.create_category(catalog, kind, "Lazer")


@pytest.mark.parametrize("kind", ["expense", "income"])
def test_update_renames_category(catalog, kind):
  created = categories.create_category(catalog, kind, "Antigo")

  updated = categories.update_category(catalog, kind, created["id"], "Novo")

  assert updated == {"id": created["id"], "name": "Novo"}
  names = [c["name"] for c in categories.list_categories(catalog, kind)]
  assert "Novo" in names and "Antigo" not in names


@pytest.mark.parametrize("kind", ["expense", "income"])
def test_update_missing_raises_not_found(catalog, kind):
  with pytest.raises(CategoryNotFound):
    categories.update_category(catalog, kind, 999, "X")


@pytest.mark.parametrize("kind", ["expense", "income"])
def test_update_rejects_duplicate_name(catalog, kind):
  categories.create_category(catalog, kind, "A")
  b = categories.create_category(catalog, kind, "B")

  with pytest.raises(DuplicateCategoryName):
    categories.update_category(catalog, kind, b["id"], "A")


@pytest.mark.parametrize("kind", ["expense", "income"])
def test_update_outros_is_protected(catalog, kind):
  with pytest.raises(ProtectedCategory):
    categories.update_category(catalog, kind, 1, "Qualquer")


@pytest.mark.parametrize("kind", ["expense", "income"])
def test_delete_removes_category(catalog, kind):
  created = categories.create_category(catalog, kind, "Temp")

  categories.delete_category(catalog, kind, created["id"])

  ids = [c["id"] for c in categories.list_categories(catalog, kind)]
  assert created["id"] not in ids


@pytest.mark.parametrize("kind", ["expense", "income"])
def test_delete_missing_raises_not_found(catalog, kind):
  with pytest.raises(CategoryNotFound):
    categories.delete_category(catalog, kind, 999)


@pytest.mark.parametrize("kind", ["expense", "income"])
def test_delete_outros_is_protected(catalog, kind):
  with pytest.raises(ProtectedCategory):
    categories.delete_category(catalog, kind, 1)


@pytest.mark.parametrize("kind", ["expense", "income"])
def test_delete_reassigns_linked_rows_to_outros(catalog, kind):
  created = categories.create_category(catalog, kind, "Some")
  _add_linked_row(catalog, kind, row_id=10, category_id=created["id"])

  categories.delete_category(catalog, kind, created["id"])

  from pyiceberg.expressions import EqualTo

  rows = store.rows(catalog, _TXN[kind], EqualTo("id", 10))
  assert [r["category_id"] for r in rows] == [1]  # reassigned to OUTROS


@pytest.mark.parametrize("kind", ["expense", "income"])
def test_delete_non_outros_raises_when_fallback_missing(catalog, kind):
  from pyiceberg.expressions import EqualTo

  victim = categories.create_category(catalog, kind, "Some")
  store.delete(catalog, _CAT[kind], EqualTo("name", "OUTROS"))

  with pytest.raises(OutrosCategoryMissing):
    categories.delete_category(catalog, kind, victim["id"])
