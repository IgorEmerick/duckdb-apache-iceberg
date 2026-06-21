import pytest
from pyiceberg.catalog.sql import SqlCatalog

from db.migrations import MIGRATIONS_DIR, run_migrations


@pytest.fixture
def fresh_catalog(tmp_path):
  """A local PyIceberg catalog (SQLite + temp warehouse), no migrations run."""
  return SqlCatalog(
    "test",
    uri=f"sqlite:///{tmp_path}/catalog.db",
    warehouse=f"file://{tmp_path}/warehouse",
  )


@pytest.fixture
def catalog(fresh_catalog):
  """A migrated local catalog ready for service/report tests."""
  run_migrations(fresh_catalog, MIGRATIONS_DIR)
  return fresh_catalog
