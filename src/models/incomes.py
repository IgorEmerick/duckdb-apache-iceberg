"""Pydantic models for income requests and responses."""

from datetime import datetime

from pydantic import BaseModel

from models.common import MonthStr, NonEmptyStr, PositiveCents


class IncomeCreate(BaseModel):
  amount_cents: PositiveCents
  month: MonthStr | None = None
  description: NonEmptyStr | None = None
  category_id: int | None = None


class IncomeUpdate(BaseModel):
  amount_cents: PositiveCents | None = None
  month: MonthStr | None = None
  description: NonEmptyStr | None = None
  category_id: int | None = None


class IncomeOut(BaseModel):
  id: int
  category_id: int
  description: str | None
  amount_cents: int
  month: str
  created_at: datetime
  updated_at: datetime
