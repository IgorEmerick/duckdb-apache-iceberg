"""DuckDB connection wired to the Iceberg REST catalog.

Configuration comes from environment variables (see ``README.md``):

- ``ICEBERG_REST_URI``   — Iceberg REST catalog endpoint (required).
- ``ICEBERG_WAREHOUSE``  — warehouse root, local folder or ``s3://…`` (required).
- ``ICEBERG_CATALOG_NAME`` — attached catalog name (default ``finance``).
"""

import os

import duckdb


def get_connection() -> duckdb.DuckDBPyConnection:
  """Build a DuckDB connection with the Iceberg REST catalog attached.

  Loads the ``iceberg`` and ``httpfs`` extensions and ``ATTACH``es the REST
  catalog whose warehouse is ``ICEBERG_WAREHOUSE``. Raises ``RuntimeError`` when
  required configuration is missing.
  """
  rest_uri = os.environ.get("ICEBERG_REST_URI")
  warehouse = os.environ.get("ICEBERG_WAREHOUSE")
  if not rest_uri or not warehouse:
    raise RuntimeError(
      "ICEBERG_REST_URI and ICEBERG_WAREHOUSE environment variables are required"
    )
  catalog = os.environ.get("ICEBERG_CATALOG_NAME", "finance")

  conn = duckdb.connect()
  conn.execute("INSTALL iceberg")
  conn.execute("LOAD iceberg")
  conn.execute("INSTALL httpfs")
  conn.execute("LOAD httpfs")
  conn.execute(
    f"ATTACH '{warehouse}' AS {catalog} (TYPE iceberg, ENDPOINT '{rest_uri}')"
  )
  # Make the catalog the default database so application SQL can use
  # unqualified table names (identical to the in-memory test connection).
  conn.execute(f"USE {catalog}")
  return conn
