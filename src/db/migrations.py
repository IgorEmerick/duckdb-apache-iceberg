"""Migration discovery and ordering.

Migration files are named ``{timestamp}-{name}`` so a plain lexical sort on the
filename yields chronological order.
"""

from collections.abc import Iterable


def pending_migrations(available: Iterable[str], applied: Iterable[str]) -> list[str]:
  """Return migration filenames not yet applied, in chronological order.

  ``available`` is the set of migration files found on disk; ``applied`` is the
  set of migration names already recorded in the migrations table.
  """
  applied_set = set(applied)
  return sorted(name for name in available if name not in applied_set)
