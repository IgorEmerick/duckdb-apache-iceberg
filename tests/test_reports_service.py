import duckdb
import pytest

from db.migrations import MIGRATIONS_DIR, run_migrations
from services import reports


def _income(c, id_, category_id, description, amount_cents, month):
  c.execute(
    "INSERT INTO incomes (id, category_id, description, amount_cents, month, "
    "created_at, updated_at) VALUES (?, ?, ?, ?, ?, now(), now())",
    [id_, category_id, description, amount_cents, month],
  )


def _expense(c, id_, category_id, description, payment_method, amount_cents, month):
  c.execute(
    "INSERT INTO expenses (id, category_id, description, payment_method, "
    "amount_cents, month, created_at, updated_at) "
    "VALUES (?, ?, ?, ?, ?, ?, now(), now())",
    [id_, category_id, description, payment_method, amount_cents, month],
  )


@pytest.fixture
def conn():
  c = duckdb.connect(":memory:")
  run_migrations(c, MIGRATIONS_DIR)
  c.execute(
    "INSERT INTO expense_categories (id, name) VALUES (2, 'Food'), (3, 'Transport')"
  )
  c.execute("INSERT INTO income_categories (id, name) VALUES (2, 'Salary')")

  # June incomes: 850000 (Salary) + 15000 (OUTROS) = 865000
  _income(c, 1, 2, "Salário", 850000, "2026-06")
  _income(c, 2, 1, None, 15000, "2026-06")
  # June expenses: Food 30000 (20000+10000), Transport 35000 -> total 65000
  _expense(c, 1, 2, "Lunch", "PIX", 20000, "2026-06")
  _expense(c, 2, 2, "Dinner", "CASH", 10000, "2026-06")
  _expense(c, 3, 3, "Fuel", "CREDIT_CARD", 35000, "2026-06")
  # May data that must be excluded from a June report
  _income(c, 3, 2, "May", 5000, "2026-05")
  _expense(c, 4, 2, "May", "CASH", 5000, "2026-05")
  return c


def test_includes_only_requested_month(conn):
  report = reports.build_report(conn, "2026-06")

  assert report["month"] == "2026-06"
  assert len(report["incomes"]) == 2
  assert len(report["expenses"]) == 3


def test_incomes_carry_category_name(conn):
  report = reports.build_report(conn, "2026-06")

  salary = next(i for i in report["incomes"] if i["id"] == 1)
  assert salary["category"] == "Salary"
  assert salary["description"] == "Salário"
  assert salary["amount_cents"] == 850000


def test_expenses_carry_category_and_payment_method(conn):
  report = reports.build_report(conn, "2026-06")

  lunch = next(e for e in report["expenses"] if e["id"] == 1)
  assert lunch["category"] == "Food"
  assert lunch["payment_method"] == "PIX"
  assert lunch["amount_cents"] == 20000


def test_totals_per_category_ordered_by_highest_spend(conn):
  report = reports.build_report(conn, "2026-06")

  assert report["totals_per_category"] == [
    {"category": "Transport", "total_cents": 35000},
    {"category": "Food", "total_cents": 30000},
  ]


def test_totals_and_balance(conn):
  report = reports.build_report(conn, "2026-06")

  assert report["total_income_cents"] == 865000
  assert report["total_expense_cents"] == 65000
  assert report["balance_cents"] == 800000


def test_defaults_to_current_month(conn, monkeypatch):
  monkeypatch.setattr(reports._clock, "current_month", lambda: "2026-06")

  report = reports.build_report(conn)

  assert report["month"] == "2026-06"
  assert report["balance_cents"] == 800000


def test_empty_month_is_zeroed(conn):
  report = reports.build_report(conn, "2099-01")

  assert report["incomes"] == []
  assert report["expenses"] == []
  assert report["totals_per_category"] == []
  assert report["total_income_cents"] == 0
  assert report["total_expense_cents"] == 0
  assert report["balance_cents"] == 0
