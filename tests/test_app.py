from fastapi.testclient import TestClient

from db.migrations import applied_migrations
from main import create_app


def test_health_endpoint_returns_ok():
  client = TestClient(create_app())

  response = client.get("/health")

  assert response.status_code == 200
  assert response.json() == {"status": "ok"}


def test_startup_runs_migrations_against_injected_catalog(fresh_catalog):
  app = create_app(catalog=fresh_catalog)

  with TestClient(app):  # entering the context triggers lifespan startup
    pass

  names = applied_migrations(fresh_catalog)
  assert any("create_migrations_table" in name for name in names)
