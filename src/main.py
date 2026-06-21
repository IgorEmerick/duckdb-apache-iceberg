"""FastAPI application entry point.

Run with: ``uvicorn main:app --app-dir src``
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from pyiceberg.catalog import Catalog

from db.migrations import MIGRATIONS_DIR, run_migrations
from routers import expenses, incomes, reports
from routers.categories import build_categories_router


def create_app(
  catalog: Catalog | None = None,
  migrations_dir: str | Path = MIGRATIONS_DIR,
) -> FastAPI:
  """Build and configure the FastAPI application.

  ``catalog`` lets callers (e.g. tests) inject a PyIceberg catalog. When
  omitted, the real REST catalog is built lazily on startup. Pending migrations
  are applied during the startup lifespan event.
  """

  @asynccontextmanager
  async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    active = catalog
    if active is None:
      from db.catalog import get_catalog

      active = get_catalog()
    app.state.catalog = active
    run_migrations(active, migrations_dir)
    yield

  app = FastAPI(title="Financial Management Back-End", lifespan=lifespan)

  @app.get("/health")
  def health() -> dict[str, str]:
    return {"status": "ok"}

  app.include_router(build_categories_router("expense", "/expense-categories"))
  app.include_router(build_categories_router("income", "/income-categories"))
  app.include_router(expenses.router)
  app.include_router(incomes.router)
  app.include_router(reports.router)

  return app


app = create_app()
