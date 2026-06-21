"""FastAPI application entry point.

Run with: ``uvicorn main:app --app-dir src``
"""

from fastapi import FastAPI


def create_app() -> FastAPI:
  """Build and configure the FastAPI application."""
  app = FastAPI(title="Financial Management Back-End")

  @app.get("/health")
  def health() -> dict[str, str]:
    return {"status": "ok"}

  return app


app = create_app()
