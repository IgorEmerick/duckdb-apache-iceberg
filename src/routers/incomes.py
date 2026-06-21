"""HTTP routes for incomes."""

import duckdb
from fastapi import APIRouter, Depends, HTTPException, Request, status

from models.incomes import IncomeCreate, IncomeOut, IncomeUpdate
from services import incomes
from services.errors import IncomeNotFound, UnknownCategory


def get_connection(request: Request) -> duckdb.DuckDBPyConnection:
  return request.app.state.connection


router = APIRouter(prefix="/incomes", tags=["incomes"])


@router.post("", response_model=IncomeOut, status_code=status.HTTP_201_CREATED)
def create_income(
  payload: IncomeCreate,
  conn: duckdb.DuckDBPyConnection = Depends(get_connection),
):
  try:
    return incomes.create_income(
      conn,
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
  conn: duckdb.DuckDBPyConnection = Depends(get_connection),
):
  try:
    return incomes.get_income(conn, income_id)
  except IncomeNotFound as exc:
    raise HTTPException(status.HTTP_404_NOT_FOUND, "income not found") from exc


@router.patch("/{income_id}", response_model=IncomeOut)
def update_income(
  income_id: int,
  payload: IncomeUpdate,
  conn: duckdb.DuckDBPyConnection = Depends(get_connection),
):
  changes = payload.model_dump(exclude_unset=True, mode="json")
  try:
    return incomes.update_income(conn, income_id, changes)
  except IncomeNotFound as exc:
    raise HTTPException(status.HTTP_404_NOT_FOUND, "income not found") from exc
  except UnknownCategory as exc:
    raise HTTPException(
      status.HTTP_422_UNPROCESSABLE_CONTENT, "unknown category"
    ) from exc


@router.delete("/{income_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_income(
  income_id: int,
  conn: duckdb.DuckDBPyConnection = Depends(get_connection),
):
  try:
    incomes.delete_income(conn, income_id)
  except IncomeNotFound as exc:
    raise HTTPException(status.HTTP_404_NOT_FOUND, "income not found") from exc
