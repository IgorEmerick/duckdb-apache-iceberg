from datetime import date

import duckdb
import pytest
from fastapi.testclient import TestClient

from main import create_app


@pytest.fixture
def client():
  conn = duckdb.connect(":memory:")
  app = create_app(connection=conn)
  with TestClient(app) as test_client:  # lifespan runs the migrations
    yield test_client


def test_create_defaults_category_to_outros_and_month(client):
  response = client.post("/incomes", json={"amount_cents": 5000})

  assert response.status_code == 201
  data = response.json()
  assert data["category_id"] == 1  # OUTROS
  assert data["description"] is None
  assert data["month"] == date.today().strftime("%Y-%m")


def test_create_with_category_and_description(client):
  response = client.post(
    "/incomes",
    json={
      "amount_cents": 5000,
      "month": "2026-03",
      "description": "Salário",
      "category_id": 1,
    },
  )

  assert response.status_code == 201
  assert response.json()["description"] == "Salário"


def test_create_unknown_category_returns_422(client):
  response = client.post("/incomes", json={"amount_cents": 100, "category_id": 999})

  assert response.status_code == 422


def test_create_invalid_month_returns_422(client):
  response = client.post("/incomes", json={"amount_cents": 100, "month": "2026-00"})

  assert response.status_code == 422


def test_create_nonpositive_amount_returns_422(client):
  response = client.post("/incomes", json={"amount_cents": -5})

  assert response.status_code == 422


def test_get_returns_200_and_404(client):
  created = client.post("/incomes", json={"amount_cents": 100}).json()

  assert client.get(f"/incomes/{created['id']}").status_code == 200
  assert client.get("/incomes/999").status_code == 404


def test_patch_updates_only_provided_fields(client):
  created = client.post(
    "/incomes", json={"amount_cents": 100, "description": "Old"}
  ).json()

  response = client.patch(f"/incomes/{created['id']}", json={"amount_cents": 250})

  assert response.status_code == 200
  data = response.json()
  assert data["amount_cents"] == 250
  assert data["description"] == "Old"  # untouched


def test_patch_missing_returns_404(client):
  assert client.patch("/incomes/999", json={"amount_cents": 1}).status_code == 404


def test_delete_returns_204_then_404(client):
  created = client.post("/incomes", json={"amount_cents": 100}).json()

  assert client.delete(f"/incomes/{created['id']}").status_code == 204
  assert client.get(f"/incomes/{created['id']}").status_code == 404


def test_delete_missing_returns_404(client):
  assert client.delete("/incomes/999").status_code == 404
