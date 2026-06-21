"""Time helpers, isolated so tests can monkeypatch them deterministically."""

from datetime import date, datetime


def current_month() -> str:
  """Return the current month as a ``YYYY-MM`` string."""
  return date.today().strftime("%Y-%m")


def now() -> datetime:
  """Return the current timestamp."""
  return datetime.now()
