import datetime as dt

import pytest

from db import store
from services import incomes
from services.errors import IncomeNotFound, UnknownCategory


@pytest.fixture
def category_id(catalog):
  store.append(catalog, "income_categories", {"id": 2, "name": "Salary"})
  return 2


def test_create_persists_and_returns(catalog, category_id):
  created = incomes.create_income(
    catalog,
    amount_cents=5000,
    month="2026-03",
    description="Salário",
    category_id=category_id,
  )

  assert created["id"] == 1
  assert created["category_id"] == category_id
  assert created["description"] == "Salário"
  assert created["amount_cents"] == 5000
  assert created["month"] == "2026-03"
  assert created["created_at"] == created["updated_at"]


def test_create_defaults_category_to_outros(catalog):
  created = incomes.create_income(catalog, amount_cents=100, month="2026-01")

  assert created["category_id"] == 1  # OUTROS


def test_create_allows_optional_description(catalog):
  created = incomes.create_income(catalog, amount_cents=100, month="2026-01")

  assert created["description"] is None


def test_create_defaults_month_to_current(catalog, monkeypatch):
  monkeypatch.setattr(incomes._clock, "current_month", lambda: "2026-06")

  created = incomes.create_income(catalog, amount_cents=100)

  assert created["month"] == "2026-06"


def test_create_unknown_category_raises(catalog):
  with pytest.raises(UnknownCategory):
    incomes.create_income(catalog, amount_cents=100, month="2026-01", category_id=999)


def test_get_missing_raises(catalog):
  with pytest.raises(IncomeNotFound):
    incomes.get_income(catalog, 999)


def test_update_patches_only_provided_fields(catalog, category_id, monkeypatch):
  created = incomes.create_income(
    catalog,
    amount_cents=100,
    month="2026-01",
    description="Old",
    category_id=category_id,
  )
  monkeypatch.setattr(incomes._clock, "now", lambda: dt.datetime(2030, 1, 1))

  updated = incomes.update_income(catalog, created["id"], {"amount_cents": 250})

  assert updated["amount_cents"] == 250
  assert updated["description"] == "Old"  # untouched
  assert updated["month"] == "2026-01"  # untouched
  assert updated["updated_at"] == dt.datetime(2030, 1, 1)


def test_update_missing_raises(catalog):
  with pytest.raises(IncomeNotFound):
    incomes.update_income(catalog, 999, {"amount_cents": 1})


def test_update_unknown_category_raises(catalog):
  created = incomes.create_income(catalog, amount_cents=100, month="2026-01")

  with pytest.raises(UnknownCategory):
    incomes.update_income(catalog, created["id"], {"category_id": 999})


def test_delete_removes(catalog):
  created = incomes.create_income(catalog, amount_cents=100, month="2026-01")

  incomes.delete_income(catalog, created["id"])

  with pytest.raises(IncomeNotFound):
    incomes.get_income(catalog, created["id"])


def test_delete_missing_raises(catalog):
  with pytest.raises(IncomeNotFound):
    incomes.delete_income(catalog, 999)
