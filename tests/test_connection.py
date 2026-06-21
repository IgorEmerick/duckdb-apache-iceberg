import os

import pytest

from db.connection import get_connection

_CATALOG_CONFIGURED = bool(
  os.environ.get("ICEBERG_REST_URI") and os.environ.get("ICEBERG_WAREHOUSE")
)


def test_get_connection_requires_catalog_env(monkeypatch):
  monkeypatch.delenv("ICEBERG_REST_URI", raising=False)
  monkeypatch.delenv("ICEBERG_WAREHOUSE", raising=False)

  with pytest.raises(RuntimeError, match="ICEBERG_REST_URI"):
    get_connection()


@pytest.mark.skipif(
  not _CATALOG_CONFIGURED,
  reason="requires a running Iceberg REST catalog (ICEBERG_REST_URI/WAREHOUSE)",
)
def test_get_connection_attaches_catalog():
  conn = get_connection()
  catalog = os.environ.get("ICEBERG_CATALOG_NAME", "finance")

  databases = [
    row[0]
    for row in conn.execute("SELECT database_name FROM duckdb_databases()").fetchall()
  ]

  assert catalog in databases
