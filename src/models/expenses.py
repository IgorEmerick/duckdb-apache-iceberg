"""Pydantic models for expense requests and responses."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel

from models.common import MonthStr, NonEmptyStr, PositiveCents


class PaymentMethod(StrEnum):
  CASH = "CASH"
  CREDIT_CARD = "CREDIT_CARD"
  DEBIT_CARD = "DEBIT_CARD"
  PIX = "PIX"
  BANK_TRANSFER = "BANK_TRANSFER"


class ExpenseCreate(BaseModel):
  category_id: int
  description: NonEmptyStr
  payment_method: PaymentMethod
  amount_cents: PositiveCents
  month: MonthStr | None = None


class ExpenseUpdate(BaseModel):
  category_id: int | None = None
  description: NonEmptyStr | None = None
  payment_method: PaymentMethod | None = None
  amount_cents: PositiveCents | None = None
  month: MonthStr | None = None


class ExpenseOut(BaseModel):
  id: int
  category_id: int
  description: str
  payment_method: PaymentMethod
  amount_cents: int
  month: str
  created_at: datetime
  updated_at: datetime
