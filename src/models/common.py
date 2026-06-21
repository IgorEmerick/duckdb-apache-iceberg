"""Shared constrained types for request models."""

from typing import Annotated

from pydantic import Field, StringConstraints

MonthStr = Annotated[str, StringConstraints(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")]
NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
PositiveCents = Annotated[int, Field(gt=0)]
