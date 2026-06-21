"""HTTP routes for expenses."""

import duckdb
from fastapi import APIRouter, Depends, HTTPException, Request, status

from models.expenses import ExpenseCreate, ExpenseOut, ExpenseUpdate
from services import expenses
from services.errors import ExpenseNotFound, UnknownCategory


def get_connection(request: Request) -> duckdb.DuckDBPyConnection:
  return request.app.state.connection


router = APIRouter(prefix="/expenses", tags=["expenses"])


@router.post("", response_model=ExpenseOut, status_code=status.HTTP_201_CREATED)
def create_expense(
  payload: ExpenseCreate,
  conn: duckdb.DuckDBPyConnection = Depends(get_connection),
):
  try:
    return expenses.create_expense(
      conn,
      category_id=payload.category_id,
      description=payload.description,
      payment_method=payload.payment_method.value,
      amount_cents=payload.amount_cents,
      month=payload.month,
    )
  except UnknownCategory as exc:
    raise HTTPException(
      status.HTTP_422_UNPROCESSABLE_CONTENT, "unknown category"
    ) from exc


@router.get("/{expense_id}", response_model=ExpenseOut)
def get_expense(
  expense_id: int,
  conn: duckdb.DuckDBPyConnection = Depends(get_connection),
):
  try:
    return expenses.get_expense(conn, expense_id)
  except ExpenseNotFound as exc:
    raise HTTPException(status.HTTP_404_NOT_FOUND, "expense not found") from exc


@router.patch("/{expense_id}", response_model=ExpenseOut)
def update_expense(
  expense_id: int,
  payload: ExpenseUpdate,
  conn: duckdb.DuckDBPyConnection = Depends(get_connection),
):
  changes = payload.model_dump(exclude_unset=True, mode="json")
  try:
    return expenses.update_expense(conn, expense_id, changes)
  except ExpenseNotFound as exc:
    raise HTTPException(status.HTTP_404_NOT_FOUND, "expense not found") from exc
  except UnknownCategory as exc:
    raise HTTPException(
      status.HTTP_422_UNPROCESSABLE_CONTENT, "unknown category"
    ) from exc


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
  expense_id: int,
  conn: duckdb.DuckDBPyConnection = Depends(get_connection),
):
  try:
    expenses.delete_expense(conn, expense_id)
  except ExpenseNotFound as exc:
    raise HTTPException(status.HTTP_404_NOT_FOUND, "expense not found") from exc
