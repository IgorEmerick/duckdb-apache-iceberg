import shutil

import duckdb

from db.migrations import MIGRATIONS_DIR, applied_migrations, run_migrations


def _initial_migration():
  return next(MIGRATIONS_DIR.glob("*-create_migrations_table.sql"))


def _write(dir_path, name, sql):
  (dir_path / name).write_text(sql)


def _table_exists(conn, table):
  rows = conn.execute(
    "SELECT 1 FROM information_schema.tables WHERE table_name = ?", [table]
  ).fetchall()
  return len(rows) == 1


def test_applied_is_empty_when_table_missing():
  conn = duckdb.connect(":memory:")

  assert applied_migrations(conn) == set()


def test_applied_returns_recorded_names():
  conn = duckdb.connect(":memory:")
  conn.execute("CREATE TABLE migrations (name VARCHAR, applied_at TIMESTAMP)")
  conn.execute("INSERT INTO migrations VALUES ('a.sql', now()), ('b.sql', now())")

  assert applied_migrations(conn) == {"a.sql", "b.sql"}


def test_run_executes_pending_in_order_and_records(tmp_path):
  _write(tmp_path, "20260101000000-create_a.sql", "CREATE TABLE a (id INTEGER);")
  _write(tmp_path, "20260103000000-create_c.sql", "CREATE TABLE c (id INTEGER);")
  _write(tmp_path, "20260102000000-create_b.sql", "CREATE TABLE b (id INTEGER);")
  conn = duckdb.connect(":memory:")

  run_migrations(conn, tmp_path)

  assert _table_exists(conn, "a")
  assert _table_exists(conn, "b")
  assert _table_exists(conn, "c")
  recorded = [row[0] for row in conn.execute("SELECT name FROM migrations").fetchall()]
  assert recorded == [
    "20260101000000-create_a.sql",
    "20260102000000-create_b.sql",
    "20260103000000-create_c.sql",
  ]


def test_run_skips_already_applied(tmp_path):
  _write(tmp_path, "20260101000000-create_a.sql", "CREATE TABLE a (id INTEGER);")
  _write(tmp_path, "20260102000000-create_b.sql", "CREATE TABLE b (id INTEGER);")
  conn = duckdb.connect(":memory:")
  conn.execute("CREATE TABLE migrations (name VARCHAR, applied_at TIMESTAMP)")
  conn.execute("INSERT INTO migrations VALUES ('20260101000000-create_a.sql', now())")

  run_migrations(conn, tmp_path)

  assert not _table_exists(conn, "a")  # was marked applied, must not re-run
  assert _table_exists(conn, "b")


def test_run_is_idempotent(tmp_path):
  _write(tmp_path, "20260101000000-create_a.sql", "CREATE TABLE a (id INTEGER);")
  conn = duckdb.connect(":memory:")

  run_migrations(conn, tmp_path)
  run_migrations(conn, tmp_path)

  rows = conn.execute("SELECT name FROM migrations").fetchall()
  assert len(rows) == 1


def test_initial_migration_sql_creates_migrations_table():
  conn = duckdb.connect(":memory:")

  conn.execute(_initial_migration().read_text())

  assert _table_exists(conn, "migrations")


def test_initial_migration_registers_its_own_name(tmp_path):
  initial = _initial_migration()
  shutil.copy(initial, tmp_path / initial.name)
  conn = duckdb.connect(":memory:")

  applied = run_migrations(conn, tmp_path)

  assert applied == [initial.name]
  assert applied_migrations(conn) == {initial.name}
