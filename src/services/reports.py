"""Monthly report service.

PyIceberg scans the tables to Arrow; DuckDB aggregates the Arrow in-process
(reads only). Builds a month's incomes and expenses (with category names), the
per-category expense totals (highest spend first), the income/expense totals,
and the balance.
"""

import duckdb
from pyiceberg.catalog import Catalog

from db import store
from services import _clock


def _register(con: duckdb.DuckDBPyConnection, catalog: Catalog, name: str) -> None:
  con.register(name, store.load(catalog, name).scan().to_arrow())


def build_report(catalog: Catalog, month: str | None = None) -> dict:
  """Return the monthly report for ``month`` (defaults to the current month)."""
  resolved_month = month if month is not None else _clock.current_month()

  con = duckdb.connect()
  for table in ("incomes", "income_categories", "expenses", "expense_categories"):
    _register(con, catalog, table)

  income_rows = con.execute(
    """
    SELECT i.id, ic.name, i.description, i.amount_cents
    FROM incomes i
    JOIN income_categories ic ON i.category_id = ic.id
    WHERE i.month = ?
    ORDER BY i.id
    """,
    [resolved_month],
  ).fetchall()
  incomes = [
    {"id": row[0], "category": row[1], "description": row[2], "amount_cents": row[3]}
    for row in income_rows
  ]

  expense_rows = con.execute(
    """
    SELECT e.id, ec.name, e.description, e.payment_method, e.amount_cents
    FROM expenses e
    JOIN expense_categories ec ON e.category_id = ec.id
    WHERE e.month = ?
    ORDER BY e.id
    """,
    [resolved_month],
  ).fetchall()
  expenses = [
    {
      "id": row[0],
      "category": row[1],
      "description": row[2],
      "payment_method": row[3],
      "amount_cents": row[4],
    }
    for row in expense_rows
  ]

  total_rows = con.execute(
    """
    SELECT ec.name, SUM(e.amount_cents) AS total_cents
    FROM expenses e
    JOIN expense_categories ec ON e.category_id = ec.id
    WHERE e.month = ?
    GROUP BY ec.name
    ORDER BY total_cents DESC, ec.name ASC
    """,
    [resolved_month],
  ).fetchall()
  totals_per_category = [
    {"category": row[0], "total_cents": int(row[1])} for row in total_rows
  ]

  total_income_cents = sum(income["amount_cents"] for income in incomes)
  total_expense_cents = sum(expense["amount_cents"] for expense in expenses)

  return {
    "month": resolved_month,
    "incomes": incomes,
    "expenses": expenses,
    "totals_per_category": totals_per_category,
    "total_income_cents": total_income_cents,
    "total_expense_cents": total_expense_cents,
    "balance_cents": total_income_cents - total_expense_cents,
  }
