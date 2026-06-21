import datetime as dt

import duckdb
import pytest

from db.migrations import MIGRATIONS_DIR, run_migrations
from services import incomes
from services.errors import IncomeNotFound, UnknownCategory


@pytest.fixture
def conn():
  connection = duckdb.connect(":memory:")
  run_migrations(connection, MIGRATIONS_DIR)
  connection.execute("INSERT INTO income_categories (id, name) VALUES (2, 'Salary')")
  return connection


def test_create_persists_and_returns(conn):
  created = incomes.create_income(
    conn, amount_cents=5000, month="2026-03", description="Salário", category_id=2
  )

  assert created["id"] == 1
  assert created["category_id"] == 2
  assert created["description"] == "Salário"
  assert created["amount_cents"] == 5000
  assert created["month"] == "2026-03"
  assert created["created_at"] == created["updated_at"]


def test_create_defaults_category_to_outros(conn):
  created = incomes.create_income(conn, amount_cents=100, month="2026-01")

  assert created["category_id"] == 1  # OUTROS


def test_create_allows_optional_description(conn):
  created = incomes.create_income(conn, amount_cents=100, month="2026-01")

  assert created["description"] is None


def test_create_defaults_month_to_current(conn, monkeypatch):
  monkeypatch.setattr(incomes._clock, "current_month", lambda: "2026-06")

  created = incomes.create_income(conn, amount_cents=100)

  assert created["month"] == "2026-06"


def test_create_unknown_category_raises(conn):
  with pytest.raises(UnknownCategory):
    incomes.create_income(conn, amount_cents=100, month="2026-01", category_id=999)


def test_get_missing_raises(conn):
  with pytest.raises(IncomeNotFound):
    incomes.get_income(conn, 999)


def test_update_patches_only_provided_fields(conn, monkeypatch):
  created = incomes.create_income(
    conn, amount_cents=100, month="2026-01", description="Old", category_id=2
  )
  monkeypatch.setattr(incomes._clock, "now", lambda: dt.datetime(2030, 1, 1))

  updated = incomes.update_income(conn, created["id"], {"amount_cents": 250})

  assert updated["amount_cents"] == 250
  assert updated["description"] == "Old"  # untouched
  assert updated["month"] == "2026-01"  # untouched
  assert updated["updated_at"] == dt.datetime(2030, 1, 1)


def test_update_missing_raises(conn):
  with pytest.raises(IncomeNotFound):
    incomes.update_income(conn, 999, {"amount_cents": 1})


def test_update_unknown_category_raises(conn):
  created = incomes.create_income(conn, amount_cents=100, month="2026-01")

  with pytest.raises(UnknownCategory):
    incomes.update_income(conn, created["id"], {"category_id": 999})


def test_delete_removes(conn):
  created = incomes.create_income(conn, amount_cents=100, month="2026-01")

  incomes.delete_income(conn, created["id"])

  with pytest.raises(IncomeNotFound):
    incomes.get_income(conn, created["id"])


def test_delete_missing_raises(conn):
  with pytest.raises(IncomeNotFound):
    incomes.delete_income(conn, 999)
