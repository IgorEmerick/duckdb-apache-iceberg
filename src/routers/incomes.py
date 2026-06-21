"""HTTP routes for incomes."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pyiceberg.catalog import Catalog

from models.incomes import IncomeCreate, IncomeOut, IncomeUpdate
from services import incomes
from services.errors import IncomeNotFound, UnknownCategory


def get_catalog(request: Request) -> Catalog:
  return request.app.state.catalog


router = APIRouter(prefix="/incomes", tags=["incomes"])


@router.post("", response_model=IncomeOut, status_code=status.HTTP_201_CREATED)
def create_income(
  payload: IncomeCreate,
  catalog: Catalog = Depends(get_catalog),
):
  try:
    return incomes.create_income(
      catalog,
      amount_cents=payload.amount_cents,
      month=payload.month,
      description=payload.description,
      category_id=payload.category_id,
    )
  except UnknownCategory as exc:
    raise HTTPException(
      status.HTTP_422_UNPROCESSABLE_CONTENT, "unknown category"
    ) from exc


@router.get("/{income_id}", response_model=IncomeOut)
def get_income(
  income_id: int,
  catalog: Catalog = Depends(get_catalog),
):
  try:
    return incomes.get_income(catalog, income_id)
  except IncomeNotFound as exc:
    raise HTTPException(status.HTTP_404_NOT_FOUND, "income not found") from exc


@router.patch("/{income_id}", response_model=IncomeOut)
def update_income(
  income_id: int,
  payload: IncomeUpdate,
  catalog: Catalog = Depends(get_catalog),
):
  changes = payload.model_dump(exclude_unset=True, mode="json")
  try:
    return incomes.update_income(catalog, income_id, changes)
  except IncomeNotFound as exc:
    raise HTTPException(status.HTTP_404_NOT_FOUND, "income not found") from exc
  except UnknownCategory as exc:
    raise HTTPException(
      status.HTTP_422_UNPROCESSABLE_CONTENT, "unknown category"
    ) from exc


@router.delete("/{income_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_income(
  income_id: int,
  catalog: Catalog = Depends(get_catalog),
):
  try:
    incomes.delete_income(catalog, income_id)
  except IncomeNotFound as exc:
    raise HTTPException(status.HTTP_404_NOT_FOUND, "income not found") from exc
