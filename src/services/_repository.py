"""Shared persistence helpers for the service layer.

Iceberg-backed tables do not auto-generate ids, so ids are allocated as
``max(id) + 1``. The insert is retried on a constraint violation so a race
between computing the id and inserting is resolved by the database rather than
a check-then-insert.
"""

import duckdb

_MAX_ID_RETRIES = 5


def next_id(conn: duckdb.DuckDBPyConnection, table: str) -> int:
  """Return the next id for ``table`` as ``max(id) + 1`` (1 when empty)."""
  row = conn.execute(f"SELECT coalesce(max(id), 0) + 1 FROM {table}").fetchone()
  return int(row[0]) if row is not None else 1


def insert_with_generated_id(
  conn: duckdb.DuckDBPyConnection, table: str, values: dict
) -> int:
  """Insert ``values`` with a generated ``id``; return the id.

  ``values`` holds the non-id columns. Retries on
  ``duckdb.ConstraintException`` (a concurrent insert that grabbed the id).
  """
  columns = list(values.keys())
  column_sql = ", ".join(["id", *columns])
  placeholders = ", ".join(["?"] * (len(columns) + 1))
  tail = [values[column] for column in columns]

  last_error: duckdb.ConstraintException | None = None
  for _ in range(_MAX_ID_RETRIES):
    new_id = next_id(conn, table)
    try:
      conn.execute(
        f"INSERT INTO {table} ({column_sql}) VALUES ({placeholders})",
        [new_id, *tail],
      )
    except duckdb.ConstraintException as exc:
      last_error = exc
      continue
    return new_id

  raise RuntimeError(f"could not allocate a unique id for {table}") from last_error
