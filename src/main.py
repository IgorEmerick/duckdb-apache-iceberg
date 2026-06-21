"""FastAPI application entry point.

Run with: ``uvicorn main:app --app-dir src``
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import duckdb
from fastapi import FastAPI

from db.migrations import MIGRATIONS_DIR, run_migrations
from routers import expenses, incomes, reports
from routers.categories import build_categories_router


def create_app(
  connection: duckdb.DuckDBPyConnection | None = None,
  migrations_dir: str | Path = MIGRATIONS_DIR,
) -> FastAPI:
  """Build and configure the FastAPI application.

  ``connection`` lets callers (e.g. tests) inject a DuckDB connection. When
  omitted, the real Iceberg-backed connection is built lazily on startup.
  Pending migrations are applied during the startup lifespan event.
  """

  @asynccontextmanager
  async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    conn = connection
    if conn is None:
      from db.connection import get_connection

      conn = get_connection()
    app.state.connection = conn
    run_migrations(conn, migrations_dir)
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
