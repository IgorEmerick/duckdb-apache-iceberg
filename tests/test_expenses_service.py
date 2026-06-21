import datetime as dt

import pytest

from db import store
from services import expenses
from services.errors import ExpenseNotFound, UnknownCategory


@pytest.fixture
def category_id(catalog):
  store.append(catalog, "expense_categories", {"id": 2, "name": "Food"})
  return 2


def test_create_persists_and_returns(catalog, category_id):
  created = expenses.create_expense(
    catalog,
    category_id=category_id,
    description="Lunch",
    payment_method="PIX",
    amount_cents=1500,
    month="2026-03",
  )

  assert created["id"] == 1
  assert created["category_id"] == category_id
  assert created["description"] == "Lunch"
  assert created["payment_method"] == "PIX"
  assert created["amount_cents"] == 1500
  assert created["month"] == "2026-03"
  assert created["created_at"] == created["updated_at"]


def test_create_defaults_month_to_current(catalog, category_id, monkeypatch):
  monkeypatch.setattr(expenses._clock, "current_month", lambda: "2026-06")

  created = expenses.create_expense(
    catalog,
    category_id=category_id,
    description="x",
    payment_method="CASH",
    amount_cents=100,
    month=None,
  )

  assert created["month"] == "2026-06"


def test_create_unknown_category_raises(catalog):
  with pytest.raises(UnknownCategory):
    expenses.create_expense(
      catalog,
      category_id=999,
      description="x",
      payment_method="CASH",
      amount_cents=100,
      month="2026-01",
    )


def test_get_missing_raises(catalog):
  with pytest.raises(ExpenseNotFound):
    expenses.get_expense(catalog, 999)


def test_update_patches_only_provided_fields(catalog, category_id, monkeypatch):
  created = expenses.create_expense(
    catalog,
    category_id=category_id,
    description="Old",
    payment_method="CASH",
    amount_cents=100,
    month="2026-01",
  )
  monkeypatch.setattr(expenses._clock, "now", lambda: dt.datetime(2030, 1, 1))

  updated = expenses.update_expense(catalog, created["id"], {"description": "New"})

  assert updated["description"] == "New"
  assert updated["amount_cents"] == 100  # untouched
  assert updated["month"] == "2026-01"  # untouched
  assert updated["updated_at"] == dt.datetime(2030, 1, 1)


def test_update_missing_raises(catalog):
  with pytest.raises(ExpenseNotFound):
    expenses.update_expense(catalog, 999, {"description": "x"})


def test_update_unknown_category_raises(catalog, category_id):
  created = expenses.create_expense(
    catalog,
    category_id=category_id,
    description="x",
    payment_method="CASH",
    amount_cents=100,
    month="2026-01",
  )

  with pytest.raises(UnknownCategory):
    expenses.update_expense(catalog, created["id"], {"category_id": 999})


def test_delete_removes(catalog, category_id):
  created = expenses.create_expense(
    catalog,
    category_id=category_id,
    description="x",
    payment_method="CASH",
    amount_cents=100,
    month="2026-01",
  )

  expenses.delete_expense(catalog, created["id"])

  with pytest.raises(ExpenseNotFound):
    expenses.get_expense(catalog, created["id"])


def test_delete_missing_raises(catalog):
  with pytest.raises(ExpenseNotFound):
    expenses.delete_expense(catalog, 999)
