"""Integration test against a live Iceberg REST catalog.

Skipped unless ICEBERG_REST_URI and ICEBERG_WAREHOUSE are set (e.g. when the
docker-compose stack is running). Run with:

  ICEBERG_REST_URI=http://localhost:8181 ICEBERG_WAREHOUSE=s3://warehouse/ \
  AWS_ACCESS_KEY_ID=admin AWS_SECRET_ACCESS_KEY=password AWS_REGION=us-east-1 \
  S3_ENDPOINT=localhost:9000 S3_URL_STYLE=path S3_USE_SSL=false \
  .venv/bin/pytest tests/test_catalog_integration.py
"""

import os
import uuid

import pytest

_CONFIGURED = bool(
  os.environ.get("ICEBERG_REST_URI") and os.environ.get("ICEBERG_WAREHOUSE")
)

pytestmark = pytest.mark.skipif(
  not _CONFIGURED,
  reason="requires a running Iceberg REST catalog (ICEBERG_REST_URI/WAREHOUSE)",
)


def test_migrations_and_write_roundtrip_against_real_catalog():
  from db.catalog import get_catalog, namespace
  from db.migrations import MIGRATIONS_DIR, run_migrations
  from services import categories, reports

  catalog = get_catalog()
  run_migrations(catalog, MIGRATIONS_DIR)  # idempotent

  for table in ("migrations", "expense_categories", "expenses", "incomes"):
    assert catalog.table_exists(f"{namespace()}.{table}")

  name = f"it-{uuid.uuid4().hex[:8]}"
  created = categories.create_category(catalog, "expense", name)
  listed = [c["name"] for c in categories.list_categories(catalog, "expense")]
  assert name in listed

  categories.delete_category(catalog, "expense", created["id"])

  # The read/aggregation path works too.
  report = reports.build_report(catalog, "2026-06")
  assert set(report) == {
    "month",
    "incomes",
    "expenses",
    "totals_per_category",
    "total_income_cents",
    "total_expense_cents",
    "balance_cents",
  }
