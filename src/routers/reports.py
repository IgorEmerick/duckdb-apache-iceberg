"""HTTP route for the monthly report."""

from typing import Annotated

import duckdb
from fastapi import APIRouter, Depends, Query, Request

from models.reports import MonthlyReport
from services import reports


def get_connection(request: Request) -> duckdb.DuckDBPyConnection:
  return request.app.state.connection


router = APIRouter(prefix="/reports", tags=["reports"])

MonthQuery = Annotated[str | None, Query(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")]


@router.get("", response_model=MonthlyReport)
def get_report(
  month: MonthQuery = None,
  conn: duckdb.DuckDBPyConnection = Depends(get_connection),
):
  return reports.build_report(conn, month)
