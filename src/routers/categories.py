"""HTTP routes for expense and income categories.

A single factory builds an equivalent router for each category kind, mapping
domain errors to HTTP status codes.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pyiceberg.catalog import Catalog

from models.categories import CategoryCreate, CategoryOut, CategoryUpdate
from services import categories
from services.errors import (
  CategoryNotFound,
  DuplicateCategoryName,
  ProtectedCategory,
)


def get_catalog(request: Request) -> Catalog:
  return request.app.state.catalog


def build_categories_router(kind: str, prefix: str) -> APIRouter:
  router = APIRouter(prefix=prefix, tags=[prefix.strip("/")])

  @router.get("", response_model=list[CategoryOut])
  def list_categories(catalog: Catalog = Depends(get_catalog)):
    return categories.list_categories(catalog, kind)

  @router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
  def create_category(
    payload: CategoryCreate,
    catalog: Catalog = Depends(get_catalog),
  ):
    try:
      return categories.create_category(catalog, kind, payload.name)
    except DuplicateCategoryName as exc:
      raise HTTPException(
        status.HTTP_409_CONFLICT, "category name already exists"
      ) from exc

  @router.put("/{category_id}", response_model=CategoryOut)
  def update_category(
    category_id: int,
    payload: CategoryUpdate,
    catalog: Catalog = Depends(get_catalog),
  ):
    try:
      return categories.update_category(catalog, kind, category_id, payload.name)
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
    catalog: Catalog = Depends(get_catalog),
  ):
    try:
      categories.delete_category(catalog, kind, category_id)
    except CategoryNotFound as exc:
      raise HTTPException(status.HTTP_404_NOT_FOUND, "category not found") from exc
    except ProtectedCategory as exc:
      raise HTTPException(
        status.HTTP_409_CONFLICT, "OUTROS category cannot be deleted"
      ) from exc

  return router
