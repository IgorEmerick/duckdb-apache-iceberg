"""Create the expense_categories table. Names are unique (enforced in the
service layer); the OUTROS row is the delete-cascade fallback."""

from pyiceberg.catalog import Catalog
from pyiceberg.schema import Schema
from pyiceberg.types import LongType, NestedField, StringType

from db import store


def up(catalog: Catalog) -> None:
  schema = Schema(
    NestedField(1, "id", LongType(), required=False),
    NestedField(2, "name", StringType(), required=False),
  )
  store.create_table(catalog, "expense_categories", schema)
