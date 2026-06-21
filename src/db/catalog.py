"""PyIceberg catalog factory.

PyIceberg owns the write side (table management + inserts/updates/deletes);
DuckDB is used only to aggregate Arrow data on the read side. In production the
catalog is a REST catalog configured from environment variables; tests build a
local SQLite-backed catalog (see ``tests/conftest.py``).

Environment variables (see ``README.md``):

- ``ICEBERG_REST_URI``     — Iceberg REST catalog endpoint (required).
- ``ICEBERG_WAREHOUSE``    — warehouse root, local folder or ``s3://…`` (required).
- ``ICEBERG_CATALOG_NAME`` — catalog name (default ``finance``).
- ``ICEBERG_NAMESPACE``    — namespace tables live in (default ``finance``).
- ``AWS_ACCESS_KEY_ID`` / ``AWS_SECRET_ACCESS_KEY`` / ``AWS_REGION``
- ``S3_ENDPOINT`` — custom endpoint host[:port] (e.g. ``minio:9000``).
- ``S3_URL_STYLE`` — ``path`` (default) or ``vhost``.
- ``S3_USE_SSL`` — ``true`` or ``false``.
"""

import os

from pyiceberg.catalog import Catalog, load_catalog


def namespace() -> str:
  """Return the namespace that all tables live in."""
  return os.environ.get("ICEBERG_NAMESPACE", "finance")


def _s3_properties() -> dict[str, str]:
  props: dict[str, str] = {}
  key_id = os.environ.get("AWS_ACCESS_KEY_ID")
  secret = os.environ.get("AWS_SECRET_ACCESS_KEY")
  endpoint = os.environ.get("S3_ENDPOINT")
  if key_id:
    props["s3.access-key-id"] = key_id
  if secret:
    props["s3.secret-access-key"] = secret
  if os.environ.get("AWS_REGION"):
    props["s3.region"] = os.environ["AWS_REGION"]
  if endpoint:
    scheme = (
      "https"
      if os.environ.get("S3_USE_SSL", "false").lower()
      in (
        "1",
        "true",
        "yes",
      )
      else "http"
    )
    props["s3.endpoint"] = f"{scheme}://{endpoint}"
  if os.environ.get("S3_URL_STYLE", "path") == "path":
    props["s3.path-style-access"] = "true"
  return props


def get_catalog() -> Catalog:
  """Build the REST catalog from environment variables.

  Raises ``RuntimeError`` when required configuration is missing.
  """
  rest_uri = os.environ.get("ICEBERG_REST_URI")
  warehouse = os.environ.get("ICEBERG_WAREHOUSE")
  if not rest_uri or not warehouse:
    raise RuntimeError(
      "ICEBERG_REST_URI and ICEBERG_WAREHOUSE environment variables are required"
    )

  name = os.environ.get("ICEBERG_CATALOG_NAME", "finance")
  properties = {
    "type": "rest",
    "uri": rest_uri,
    "warehouse": warehouse,
    **_s3_properties(),
  }
  return load_catalog(name, **properties)
