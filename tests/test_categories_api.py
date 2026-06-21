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


@pytest.fixture(params=["/expense-categories", "/income-categories"])
def base(request):
  return request.param


def test_list_returns_seeded_outros(client, base):
  response = client.get(base)

  assert response.status_code == 200
  assert response.json() == [{"id": 1, "name": "OUTROS"}]


def test_create_returns_201_and_persists(client, base):
  response = client.post(base, json={"name": "Alimentação"})

  assert response.status_code == 201
  assert response.json() == {"id": 2, "name": "Alimentação"}
  listed = client.get(base).json()
  assert {"id": 2, "name": "Alimentação"} in listed


def test_create_duplicate_returns_409(client, base):
  client.post(base, json={"name": "Lazer"})

  response = client.post(base, json={"name": "Lazer"})

  assert response.status_code == 409


def test_create_empty_name_returns_422(client, base):
  response = client.post(base, json={"name": ""})

  assert response.status_code == 422


def test_update_renames_returns_200(client, base):
  created = client.post(base, json={"name": "Antigo"}).json()

  response = client.put(f"{base}/{created['id']}", json={"name": "Novo"})

  assert response.status_code == 200
  assert response.json() == {"id": created["id"], "name": "Novo"}


def test_update_missing_returns_404(client, base):
  response = client.put(f"{base}/999", json={"name": "X"})

  assert response.status_code == 404


def test_update_outros_returns_409(client, base):
  response = client.put(f"{base}/1", json={"name": "X"})

  assert response.status_code == 409


def test_delete_returns_204_and_removes(client, base):
  created = client.post(base, json={"name": "Temp"}).json()

  response = client.delete(f"{base}/{created['id']}")

  assert response.status_code == 204
  ids = [c["id"] for c in client.get(base).json()]
  assert created["id"] not in ids


def test_delete_missing_returns_404(client, base):
  response = client.delete(f"{base}/999")

  assert response.status_code == 404


def test_delete_outros_returns_409(client, base):
  response = client.delete(f"{base}/1")

  assert response.status_code == 409
