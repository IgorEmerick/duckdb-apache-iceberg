"""Migration discovery and ordering.

Migration files are named ``{timestamp}-{name}`` so a plain lexical sort on the
filename yields chronological order.
"""

from collections.abc import Iterable
from pathlib import Path

import duckdb

MIGRATIONS_TABLE_DDL = (
  "CREATE TABLE IF NOT EXISTS migrations (name VARCHAR, applied_at TIMESTAMP)"
)

# Repository-level directory holding the ``{timestamp}-{name}.sql`` files.
MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "migrations"


def pending_migrations(available: Iterable[str], applied: Iterable[str]) -> list[str]:
  """Return migration filenames not yet applied, in chronological order.

  ``available`` is the set of migration files found on disk; ``applied`` is the
  set of migration names already recorded in the migrations table.
  """
  applied_set = set(applied)
  return sorted(name for name in available if name not in applied_set)


def applied_migrations(conn: duckdb.DuckDBPyConnection) -> set[str]:
  """Return the set of migration names recorded in the ``migrations`` table.

  Returns an empty set when the table does not exist yet (fresh database),
  so the very first migration can bootstrap it.
  """
  try:
    rows = conn.execute("SELECT name FROM migrations").fetchall()
  except duckdb.CatalogException:
    return set()
  return {row[0] for row in rows}


def run_migrations(
  conn: duckdb.DuckDBPyConnection, migrations_dir: str | Path
) -> list[str]:
  """Apply every pending ``.sql`` migration in chronological order.

  Ensures the ``migrations`` bookkeeping table exists, then for each migration
  not yet recorded (ordered by filename) executes its SQL and records its name.
  Returns the list of migration names applied during this call.
  """
  conn.execute(MIGRATIONS_TABLE_DDL)

  directory = Path(migrations_dir)
  available = [path.name for path in directory.glob("*.sql")]
  pending = pending_migrations(available, applied_migrations(conn))

  for name in pending:
    sql = (directory / name).read_text()
    conn.execute(sql)
    conn.execute("INSERT INTO migrations VALUES (?, now())", [name])

  return pending
