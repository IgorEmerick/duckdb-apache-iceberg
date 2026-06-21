"""Create the expenses table. Values are integer cents (BRL); month is a
'YYYY-MM' string; category_id references expense_categories."""

from pyiceberg.catalog import Catalog
from pyiceberg.schema import Schema
from pyiceberg.types import (
  LongType,
  NestedField,
  StringType,
  TimestampType,
)

from db import store


def up(catalog: Catalog) -> None:
  schema = Schema(
    NestedField(1, "id", LongType(), required=False),
    NestedField(2, "category_id", LongType(), required=False),
    NestedField(3, "description", StringType(), required=False),
    NestedField(4, "payment_method", StringType(), required=False),
    NestedField(5, "amount_cents", LongType(), required=False),
    NestedField(6, "month", StringType(), required=False),
    NestedField(7, "created_at", TimestampType(), required=False),
    NestedField(8, "updated_at", TimestampType(), required=False),
  )
  store.create_table(catalog, "expenses", schema)
