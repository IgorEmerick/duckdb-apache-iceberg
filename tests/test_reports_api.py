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


def test_report_returns_200_with_shape(client):
  category = client.post("/expense-categories", json={"name": "Food"}).json()
  client.post(
    "/expenses",
    json={
      "category_id": category["id"],
      "description": "Lunch",
      "payment_method": "PIX",
      "amount_cents": 20000,
      "month": "2026-06",
    },
  )
  client.post("/incomes", json={"amount_cents": 50000, "month": "2026-06"})

  response = client.get("/reports?month=2026-06")

  assert response.status_code == 200
  data = response.json()
  assert data["month"] == "2026-06"
  assert len(data["incomes"]) == 1
  assert len(data["expenses"]) == 1
  assert data["totals_per_category"] == [{"category": "Food", "total_cents": 20000}]
  assert data["total_income_cents"] == 50000
  assert data["total_expense_cents"] == 20000
  assert data["balance_cents"] == 30000


def test_report_defaults_to_current_month(client):
  client.post("/incomes", json={"amount_cents": 1000})  # defaults to current month

  response = client.get("/reports")

  assert response.status_code == 200
  data = response.json()
  assert data["month"] == date.today().strftime("%Y-%m")
  assert data["total_income_cents"] == 1000


def test_report_invalid_month_returns_422(client):
  assert client.get("/reports?month=2026-13").status_code == 422
