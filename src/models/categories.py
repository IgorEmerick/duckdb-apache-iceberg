"""Pydantic models for category requests and responses."""

from typing import Annotated

from pydantic import BaseModel, StringConstraints

NonEmptyName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class CategoryCreate(BaseModel):
  name: NonEmptyName


class CategoryUpdate(BaseModel):
  name: NonEmptyName


class CategoryOut(BaseModel):
  id: int
  name: str
