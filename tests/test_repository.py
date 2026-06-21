import duckdb

from services import _repository as repository


def test_insert_generates_sequential_ids():
  conn = duckdb.connect(":memory:")
  conn.execute("CREATE TABLE t (id BIGINT, name VARCHAR)")

  first = repository.insert_with_generated_id(conn, "t", {"name": "a"})
  second = repository.insert_with_generated_id(conn, "t", {"name": "b"})

  assert (first, second) == (1, 2)
  rows = conn.execute("SELECT id, name FROM t ORDER BY id").fetchall()
  assert rows == [(1, "a"), (2, "b")]


def test_insert_retries_on_constraint_violation(monkeypatch):
  conn = duckdb.connect(":memory:")
  conn.execute("CREATE TABLE t (id BIGINT PRIMARY KEY, name VARCHAR)")
  conn.execute("INSERT INTO t VALUES (1, 'existing')")
  # First generated id collides with the existing row (real PK violation),
  # then a free id is returned.
  ids = iter([1, 2])
  monkeypatch.setattr(repository, "next_id", lambda conn, table: next(ids))

  new_id = repository.insert_with_generated_id(conn, "t", {"name": "new"})

  assert new_id == 2
