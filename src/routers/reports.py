"""HTTP route for the monthly report."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from pyiceberg.catalog import Catalog

from models.reports import MonthlyReport
from services import reports


def get_catalog(request: Request) -> Catalog:
  return request.app.state.catalog


router = APIRouter(prefix="/reports", tags=["reports"])

MonthQuery = Annotated[str | None, Query(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")]


@router.get("", response_model=MonthlyReport)
def get_report(
  month: MonthQuery = None,
  catalog: Catalog = Depends(get_catalog),
):
  return reports.build_report(catalog, month)
