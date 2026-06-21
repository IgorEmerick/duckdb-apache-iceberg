"""Migration discovery and execution (PyIceberg).

Migration files are Python modules named ``{timestamp}-{name}.py`` exposing an
``up(catalog)`` function. A plain lexical sort on the filename yields
chronological order. Applied migrations are recorded in the ``migrations``
Iceberg table (created by the first migration).
"""

import importlib.util
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path

from pyiceberg.catalog import Catalog

from db import store
from db.catalog import namespace

# Repository-level directory holding the ``{timestamp}-{name}.py`` files.
MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "migrations"


def pending_migrations(available: Iterable[str], applied: Iterable[str]) -> list[str]:
  """Return migration filenames not yet applied, in chronological order."""
  applied_set = set(applied)
  return sorted(name for name in available if name not in applied_set)


def applied_migrations(catalog: Catalog) -> set[str]:
  """Return the set of migration names recorded in the ``migrations`` table.

  Returns an empty set when the table does not exist yet (fresh catalog).
  """
  if not store.table_exists(catalog, "migrations"):
    return set()
  return {row["name"] for row in store.rows(catalog, "migrations")}


def _load_up(path: Path):
  spec = importlib.util.spec_from_file_location(f"migration_{path.stem}", path)
  module = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(module)
  return module.up


def run_migrations(catalog: Catalog, migrations_dir: str | Path) -> list[str]:
  """Apply every pending migration module in chronological order.

  Ensures the namespace exists, then for each migration not yet recorded runs
  its ``up(catalog)`` and records its name. Returns the names applied this call.
  """
  catalog.create_namespace_if_not_exists(namespace())

  directory = Path(migrations_dir)
  available = [p.name for p in directory.glob("*.py") if not p.name.startswith("_")]
  pending = pending_migrations(available, applied_migrations(catalog))

  for name in pending:
    up = _load_up(directory / name)
    up(catalog)
    store.append(catalog, "migrations", {"name": name, "applied_at": datetime.now()})

  return pending
