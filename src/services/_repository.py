"""Shared persistence helpers for the service layer.

Iceberg tables do not auto-generate ids, so ids are allocated as
``max(id) + 1`` over the current rows. Single-user usage makes this safe.
"""

from pyiceberg.catalog import Catalog

from db import store


def next_id(catalog: Catalog, table: str) -> int:
  """Return the next id for ``table`` as ``max(id) + 1`` (1 when empty)."""
  rows = store.rows(catalog, table)
  return max((row["id"] for row in rows), default=0) + 1


def insert_with_generated_id(catalog: Catalog, table: str, values: dict) -> int:
  """Append ``values`` with a generated ``id``; return the id."""
  new_id = next_id(catalog, table)
  store.append(catalog, table, {"id": new_id, **values})
  return new_id
