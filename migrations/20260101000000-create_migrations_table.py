"""Initial migration: create the bookkeeping table that records which
migrations have been applied."""

from pyiceberg.catalog import Catalog
from pyiceberg.schema import Schema
from pyiceberg.types import NestedField, StringType, TimestampType

from db import store


def up(catalog: Catalog) -> None:
  schema = Schema(
    NestedField(1, "name", StringType(), required=False),
    NestedField(2, "applied_at", TimestampType(), required=False),
  )
  store.create_table(catalog, "migrations", schema)
