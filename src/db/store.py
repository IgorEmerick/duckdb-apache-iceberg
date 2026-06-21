"""Thin PyIceberg data-access helpers.

All table identifiers are resolved within the configured namespace, so callers
refer to tables by their short name (``"expenses"``, ``"migrations"``, …).
"""

import pyarrow as pa
from pyiceberg.catalog import Catalog
from pyiceberg.expressions import BooleanExpression
from pyiceberg.schema import Schema
from pyiceberg.table import Table

from db.catalog import namespace


def identifier(name: str) -> str:
  """Return the fully-qualified ``namespace.table`` identifier."""
  return f"{namespace()}.{name}"


def create_table(catalog: Catalog, name: str, schema: Schema) -> None:
  """Create a table from an Iceberg schema if it does not exist."""
  catalog.create_table_if_not_exists(identifier(name), schema)


def table_exists(catalog: Catalog, name: str) -> bool:
  return catalog.table_exists(identifier(name))


def load(catalog: Catalog, name: str) -> Table:
  return catalog.load_table(identifier(name))


def rows(
  catalog: Catalog, name: str, predicate: BooleanExpression | None = None
) -> list[dict]:
  """Return all matching rows as plain dicts (column name -> value)."""
  table = load(catalog, name)
  scan = table.scan(row_filter=predicate) if predicate is not None else table.scan()
  return scan.to_arrow().to_pylist()


def append(catalog: Catalog, name: str, row: dict) -> None:
  """Append a single row (must include every column)."""
  table = load(catalog, name)
  table.append(pa.Table.from_pylist([row], schema=table.schema().as_arrow()))


def delete(catalog: Catalog, name: str, predicate: BooleanExpression) -> None:
  """Delete rows matching ``predicate``."""
  load(catalog, name).delete(predicate)


def replace(
  catalog: Catalog, name: str, predicate: BooleanExpression, new_rows: list[dict]
) -> None:
  """Atomically delete rows matching ``predicate`` and append ``new_rows``."""
  table = load(catalog, name)
  with table.transaction() as txn:
    txn.delete(predicate)
    if new_rows:
      txn.append(pa.Table.from_pylist(new_rows, schema=table.schema().as_arrow()))
