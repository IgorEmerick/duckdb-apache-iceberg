from db import store
from db.migrations import MIGRATIONS_DIR, applied_migrations, run_migrations


def test_applied_is_empty_on_fresh_catalog(fresh_catalog):
  assert applied_migrations(fresh_catalog) == set()


def test_run_applies_all_migrations_and_records_them(fresh_catalog):
  applied = run_migrations(fresh_catalog, MIGRATIONS_DIR)

  assert "20260101000000-create_migrations_table.py" in applied
  recorded = applied_migrations(fresh_catalog)
  assert set(applied) == recorded
  assert len(recorded) == len(applied)


def test_run_is_idempotent(fresh_catalog):
  run_migrations(fresh_catalog, MIGRATIONS_DIR)
  second = run_migrations(fresh_catalog, MIGRATIONS_DIR)

  assert second == []  # nothing pending on the second run
  names = [row["name"] for row in store.rows(fresh_catalog, "migrations")]
  assert len(names) == len(set(names))  # no duplicate records
