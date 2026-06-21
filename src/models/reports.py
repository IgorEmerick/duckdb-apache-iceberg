"""Pydantic models for the monthly report response."""

from pydantic import BaseModel


class ReportIncome(BaseModel):
  id: int
  category: str
  description: str | None
  amount_cents: int


class ReportExpense(BaseModel):
  id: int
  category: str
  description: str
  payment_method: str
  amount_cents: int


class CategoryTotal(BaseModel):
  category: str
  total_cents: int


class MonthlyReport(BaseModel):
  month: str
  incomes: list[ReportIncome]
  expenses: list[ReportExpense]
  totals_per_category: list[CategoryTotal]
  total_income_cents: int
  total_expense_cents: int
  balance_cents: int
