import datetime as dt

import duckdb
import pytest

from db.migrations import MIGRATIONS_DIR, run_migrations
from services import expenses
from services.errors import ExpenseNotFound, UnknownCategory


@pytest.fixture
def conn():
  connection = duckdb.connect(":memory:")
  run_migrations(connection, MIGRATIONS_DIR)
  connection.execute("INSERT INTO expense_categories (id, name) VALUES (2, 'Food')")
  return connection


def test_create_persists_and_returns(conn):
  created = expenses.create_expense(
    conn,
    category_id=2,
    description="Lunch",
    payment_method="PIX",
    amount_cents=1500,
    month="2026-03",
  )

  assert created["id"] == 1
  assert created["category_id"] == 2
  assert created["description"] == "Lunch"
  assert created["payment_method"] == "PIX"
  assert created["amount_cents"] == 1500
  assert created["month"] == "2026-03"
  assert created["created_at"] == created["updated_at"]


def test_create_defaults_month_to_current(conn, monkeypatch):
  monkeypatch.setattr(expenses._clock, "current_month", lambda: "2026-06")

  created = expenses.create_expense(
    conn,
    category_id=2,
    description="x",
    payment_method="CASH",
    amount_cents=100,
    month=None,
  )

  assert created["month"] == "2026-06"


def test_create_unknown_category_raises(conn):
  with pytest.raises(UnknownCategory):
    expenses.create_expense(
      conn,
      category_id=999,
      description="x",
      payment_method="CASH",
      amount_cents=100,
      month="2026-01",
    )


def test_get_missing_raises(conn):
  with pytest.raises(ExpenseNotFound):
    expenses.get_expense(conn, 999)


def test_update_patches_only_provided_fields(conn, monkeypatch):
  created = expenses.create_expense(
    conn,
    category_id=2,
    description="Old",
    payment_method="CASH",
    amount_cents=100,
    month="2026-01",
  )
  monkeypatch.setattr(expenses._clock, "now", lambda: dt.datetime(2030, 1, 1))

  updated = expenses.update_expense(conn, created["id"], {"description": "New"})

  assert updated["description"] == "New"
  assert updated["amount_cents"] == 100  # untouched
  assert updated["month"] == "2026-01"  # untouched
  assert updated["updated_at"] == dt.datetime(2030, 1, 1)


def test_update_missing_raises(conn):
  with pytest.raises(ExpenseNotFound):
    expenses.update_expense(conn, 999, {"description": "x"})


def test_update_unknown_category_raises(conn):
  created = expenses.create_expense(
    conn,
    category_id=2,
    description="x",
    payment_method="CASH",
    amount_cents=100,
    month="2026-01",
  )

  with pytest.raises(UnknownCategory):
    expenses.update_expense(conn, created["id"], {"category_id": 999})


def test_delete_removes(conn):
  created = expenses.create_expense(
    conn,
    category_id=2,
    description="x",
    payment_method="CASH",
    amount_cents=100,
    month="2026-01",
  )

  expenses.delete_expense(conn, created["id"])

  with pytest.raises(ExpenseNotFound):
    expenses.get_expense(conn, created["id"])


def test_delete_missing_raises(conn):
  with pytest.raises(ExpenseNotFound):
    expenses.delete_expense(conn, 999)
