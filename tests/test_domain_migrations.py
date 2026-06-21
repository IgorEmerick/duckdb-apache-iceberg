from db import store
from db.catalog import namespace


def test_domain_tables_created(catalog):
  for table in (
    "migrations",
    "expense_categories",
    "income_categories",
    "expenses",
    "incomes",
  ):
    assert catalog.table_exists(f"{namespace()}.{table}")


def test_outros_category_seeded_in_both_tables(catalog):
  for table in ("expense_categories", "income_categories"):
    rows = store.rows(catalog, table)
    outros = [r for r in rows if r["name"] == "OUTROS"]
    assert outros == [{"id": 1, "name": "OUTROS"}]
