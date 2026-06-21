"""DuckDB connection wired to the Iceberg REST catalog.

Configuration comes from environment variables (see ``README.md``):

- ``ICEBERG_REST_URI``     — Iceberg REST catalog endpoint (required).
- ``ICEBERG_WAREHOUSE``    — warehouse root, local folder or ``s3://…`` (required).
- ``ICEBERG_CATALOG_NAME`` — attached catalog name (default ``finance``).

S3 access (for an ``s3://`` warehouse, including MinIO) is configured from the
standard AWS variables plus optional overrides:

- ``AWS_ACCESS_KEY_ID`` / ``AWS_SECRET_ACCESS_KEY`` / ``AWS_REGION``
- ``S3_ENDPOINT``  — custom endpoint host[:port] (e.g. ``minio:9000``).
- ``S3_URL_STYLE`` — ``path`` (default) or ``vhost``.
- ``S3_USE_SSL``   — ``true`` or ``false`` (default ``false`` when an endpoint
  override is set, ``true`` otherwise).
"""

import os

import duckdb


def _configure_s3(conn: duckdb.DuckDBPyConnection) -> None:
  """Create a DuckDB S3 secret when S3 credentials/endpoint are configured."""
  key_id = os.environ.get("AWS_ACCESS_KEY_ID")
  secret = os.environ.get("AWS_SECRET_ACCESS_KEY")
  endpoint = os.environ.get("S3_ENDPOINT")
  if not key_id and not endpoint:
    return

  region = os.environ.get("AWS_REGION", "us-east-1")
  url_style = os.environ.get("S3_URL_STYLE", "path")
  default_ssl = "false" if endpoint else "true"
  use_ssl = os.environ.get("S3_USE_SSL", default_ssl).lower() in ("1", "true", "yes")

  parts = [
    "TYPE s3",
    f"KEY_ID '{key_id}'",
    f"SECRET '{secret}'",
    f"REGION '{region}'",
    f"URL_STYLE '{url_style}'",
    f"USE_SSL {str(use_ssl).lower()}",
  ]
  if endpoint:
    parts.append(f"ENDPOINT '{endpoint}'")
  conn.execute(f"CREATE OR REPLACE SECRET s3_secret ({', '.join(parts)})")


def get_connection() -> duckdb.DuckDBPyConnection:
  """Build a DuckDB connection with the Iceberg REST catalog attached.

  Loads the ``iceberg`` and ``httpfs`` extensions, configures S3 access, and
  ``ATTACH``es the REST catalog whose warehouse is ``ICEBERG_WAREHOUSE``. Raises
  ``RuntimeError`` when required configuration is missing.
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

  _configure_s3(conn)

  conn.execute(
    f"ATTACH '{warehouse}' AS {catalog} "
    f"(TYPE iceberg, ENDPOINT '{rest_uri}', AUTHORIZATION_TYPE 'none')"
  )
  # Make the catalog the default database so application SQL can use
  # unqualified table names (identical to the in-memory test connection).
  conn.execute(f"USE {catalog}")
  return conn
