"""Seed the immutable OUTROS fallback category (id 1) in both category tables."""

from pyiceberg.catalog import Catalog
from pyiceberg.expressions import EqualTo

from db import store


def _seed_outros(catalog: Catalog, table: str) -> None:
  existing = store.rows(catalog, table, EqualTo("name", "OUTROS"))
  if not existing:
    store.append(catalog, table, {"id": 1, "name": "OUTROS"})


def up(catalog: Catalog) -> None:
  _seed_outros(catalog, "expense_categories")
  _seed_outros(catalog, "income_categories")
