import duckdb

from db.migrations import MIGRATIONS_DIR, run_migrations


def _migrated_conn():
  conn = duckdb.connect(":memory:")
  run_migrations(conn, MIGRATIONS_DIR)
  return conn


def _table_names(conn):
  rows = conn.execute("SELECT table_name FROM information_schema.tables").fetchall()
  return {row[0] for row in rows}


def test_domain_tables_created():
  conn = _migrated_conn()

  tables = _table_names(conn)

  assert {
    "migrations",
    "expense_categories",
    "income_categories",
    "expenses",
    "incomes",
  } <= tables


def test_outros_category_seeded_in_both_tables():
  conn = _migrated_conn()

  for table in ("expense_categories", "income_categories"):
    rows = conn.execute(f"SELECT id FROM {table} WHERE name = 'OUTROS'").fetchall()
    assert rows == [(1,)]
