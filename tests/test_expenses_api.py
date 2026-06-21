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


def _valid_body(**overrides):
  body = {
    "category_id": 1,  # seeded OUTROS expense category
    "description": "Lunch",
    "payment_method": "PIX",
    "amount_cents": 1500,
    "month": "2026-03",
  }
  body.update(overrides)
  return body


def test_create_returns_201(client):
  response = client.post("/expenses", json=_valid_body())

  assert response.status_code == 201
  data = response.json()
  assert data["id"] == 1
  assert data["amount_cents"] == 1500
  assert data["payment_method"] == "PIX"


def test_create_defaults_month_to_current(client):
  body = _valid_body()
  del body["month"]

  response = client.post("/expenses", json=body)

  assert response.status_code == 201
  assert response.json()["month"] == date.today().strftime("%Y-%m")


def test_create_unknown_category_returns_422(client):
  response = client.post("/expenses", json=_valid_body(category_id=999))

  assert response.status_code == 422


def test_create_invalid_payment_method_returns_422(client):
  response = client.post("/expenses", json=_valid_body(payment_method="BITCOIN"))

  assert response.status_code == 422


def test_create_invalid_month_returns_422(client):
  response = client.post("/expenses", json=_valid_body(month="2026-13"))

  assert response.status_code == 422


def test_create_nonpositive_amount_returns_422(client):
  response = client.post("/expenses", json=_valid_body(amount_cents=0))

  assert response.status_code == 422


def test_get_returns_200_and_404(client):
  created = client.post("/expenses", json=_valid_body()).json()

  assert client.get(f"/expenses/{created['id']}").status_code == 200
  assert client.get("/expenses/999").status_code == 404


def test_patch_updates_only_provided_fields(client):
  created = client.post("/expenses", json=_valid_body()).json()

  response = client.patch(f"/expenses/{created['id']}", json={"amount_cents": 2000})

  assert response.status_code == 200
  data = response.json()
  assert data["amount_cents"] == 2000
  assert data["description"] == "Lunch"  # untouched


def test_patch_missing_returns_404(client):
  response = client.patch("/expenses/999", json={"amount_cents": 2000})

  assert response.status_code == 404


def test_patch_unknown_category_returns_422(client):
  created = client.post("/expenses", json=_valid_body()).json()

  response = client.patch(f"/expenses/{created['id']}", json={"category_id": 999})

  assert response.status_code == 422


def test_delete_returns_204_then_404(client):
  created = client.post("/expenses", json=_valid_body()).json()

  assert client.delete(f"/expenses/{created['id']}").status_code == 204
  assert client.get(f"/expenses/{created['id']}").status_code == 404


def test_delete_missing_returns_404(client):
  assert client.delete("/expenses/999").status_code == 404
