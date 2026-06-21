import duckdb
from fastapi.testclient import TestClient

from db.migrations import applied_migrations
from main import create_app


def test_health_endpoint_returns_ok():
  client = TestClient(create_app())

  response = client.get("/health")

  assert response.status_code == 200
  assert response.json() == {"status": "ok"}


def test_startup_runs_migrations_against_injected_connection():
  conn = duckdb.connect(":memory:")
  app = create_app(connection=conn)

  with TestClient(app):  # entering the context triggers lifespan startup
    pass

  names = applied_migrations(conn)
  assert any("create_migrations_table" in name for name in names)
