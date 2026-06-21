"""HTTP routes for expense and income categories.

A single factory builds an equivalent router for each category kind, mapping
domain errors to HTTP status codes.
"""

import duckdb
from fastapi import APIRouter, Depends, HTTPException, Request, status

from models.categories import CategoryCreate, CategoryOut, CategoryUpdate
from services import categories
from services.errors import (
  CategoryNotFound,
  DuplicateCategoryName,
  ProtectedCategory,
)


def get_connection(request: Request) -> duckdb.DuckDBPyConnection:
  return request.app.state.connection


def build_categories_router(kind: str, prefix: str) -> APIRouter:
  router = APIRouter(prefix=prefix, tags=[prefix.strip("/")])

  @router.get("", response_model=list[CategoryOut])
  def list_categories(conn: duckdb.DuckDBPyConnection = Depends(get_connection)):
    return categories.list_categories(conn, kind)

  @router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
  def create_category(
    payload: CategoryCreate,
    conn: duckdb.DuckDBPyConnection = Depends(get_connection),
  ):
    try:
      return categories.create_category(conn, kind, payload.name)
    except DuplicateCategoryName as exc:
      raise HTTPException(
        status.HTTP_409_CONFLICT, "category name already exists"
      ) from exc

  @router.put("/{category_id}", response_model=CategoryOut)
  def update_category(
    category_id: int,
    payload: CategoryUpdate,
    conn: duckdb.DuckDBPyConnection = Depends(get_connection),
  ):
    try:
      return categories.update_category(conn, kind, category_id, payload.name)
    except CategoryNotFound as exc:
      raise HTTPException(status.HTTP_404_NOT_FOUND, "category not found") from exc
    except ProtectedCategory as exc:
      raise HTTPException(
        status.HTTP_409_CONFLICT, "OUTROS category cannot be modified"
      ) from exc
    except DuplicateCategoryName as exc:
      raise HTTPException(
        status.HTTP_409_CONFLICT, "category name already exists"
      ) from exc

  @router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
  def delete_category(
    category_id: int,
    conn: duckdb.DuckDBPyConnection = Depends(get_connection),
  ):
    try:
      categories.delete_category(conn, kind, category_id)
    except CategoryNotFound as exc:
      raise HTTPException(status.HTTP_404_NOT_FOUND, "category not found") from exc
    except ProtectedCategory as exc:
      raise HTTPException(
        status.HTTP_409_CONFLICT, "OUTROS category cannot be deleted"
      ) from exc

  return router
