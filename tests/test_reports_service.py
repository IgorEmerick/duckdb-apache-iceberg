import datetime as dt

import pytest

from db import store
from services import reports

_NOW = dt.datetime(2026, 6, 1)


def _income(catalog, row_id, category_id, description, amount_cents, month):
  store.append(
    catalog,
    "incomes",
    {
      "id": row_id,
      "category_id": category_id,
      "description": description,
      "amount_cents": amount_cents,
      "month": month,
      "created_at": _NOW,
      "updated_at": _NOW,
    },
  )


def _expense(catalog, row_id, category_id, description, payment_method, amount, month):
  store.append(
    catalog,
    "expenses",
    {
      "id": row_id,
      "category_id": category_id,
      "description": description,
      "payment_method": payment_method,
      "amount_cents": amount,
      "month": month,
      "created_at": _NOW,
      "updated_at": _NOW,
    },
  )


@pytest.fixture
def seeded(catalog):
  store.append(catalog, "expense_categories", {"id": 2, "name": "Food"})
  store.append(catalog, "expense_categories", {"id": 3, "name": "Transport"})
  store.append(catalog, "income_categories", {"id": 2, "name": "Salary"})

  # June incomes: 850000 (Salary) + 15000 (OUTROS) = 865000
  _income(catalog, 1, 2, "Salário", 850000, "2026-06")
  _income(catalog, 2, 1, None, 15000, "2026-06")
  # June expenses: Food 30000 (20000+10000), Transport 35000 -> total 65000
  _expense(catalog, 1, 2, "Lunch", "PIX", 20000, "2026-06")
  _expense(catalog, 2, 2, "Dinner", "CASH", 10000, "2026-06")
  _expense(catalog, 3, 3, "Fuel", "CREDIT_CARD", 35000, "2026-06")
  # May data that must be excluded from a June report
  _income(catalog, 3, 2, "May", 5000, "2026-05")
  _expense(catalog, 4, 2, "May", "CASH", 5000, "2026-05")
  return catalog


def test_includes_only_requested_month(seeded):
  report = reports.build_report(seeded, "2026-06")

  assert report["month"] == "2026-06"
  assert len(report["incomes"]) == 2
  assert len(report["expenses"]) == 3


def test_incomes_carry_category_name(seeded):
  report = reports.build_report(seeded, "2026-06")

  salary = next(i for i in report["incomes"] if i["id"] == 1)
  assert salary["category"] == "Salary"
  assert salary["description"] == "Salário"
  assert salary["amount_cents"] == 850000


def test_expenses_carry_category_and_payment_method(seeded):
  report = reports.build_report(seeded, "2026-06")

  lunch = next(e for e in report["expenses"] if e["id"] == 1)
  assert lunch["category"] == "Food"
  assert lunch["payment_method"] == "PIX"
  assert lunch["amount_cents"] == 20000


def test_totals_per_category_ordered_by_highest_spend(seeded):
  report = reports.build_report(seeded, "2026-06")

  assert report["totals_per_category"] == [
    {"category": "Transport", "total_cents": 35000},
    {"category": "Food", "total_cents": 30000},
  ]


def test_totals_and_balance(seeded):
  report = reports.build_report(seeded, "2026-06")

  assert report["total_income_cents"] == 865000
  assert report["total_expense_cents"] == 65000
  assert report["balance_cents"] == 800000


def test_defaults_to_current_month(seeded, monkeypatch):
  monkeypatch.setattr(reports._clock, "current_month", lambda: "2026-06")

  report = reports.build_report(seeded)

  assert report["month"] == "2026-06"
  assert report["balance_cents"] == 800000


def test_empty_month_is_zeroed(catalog):
  report = reports.build_report(catalog, "2099-01")

  assert report["incomes"] == []
  assert report["expenses"] == []
  assert report["totals_per_category"] == []
  assert report["total_income_cents"] == 0
  assert report["total_expense_cents"] == 0
  assert report["balance_cents"] == 0
