from db.migrations import pending_migrations


def test_returns_unapplied_in_chronological_order():
  available = [
    "20260102000000-add_expenses.sql",
    "20260101000000-create_migrations_table.sql",
    "20260103000000-add_incomes.sql",
  ]
  applied = {"20260101000000-create_migrations_table.sql"}

  result = pending_migrations(available, applied)

  assert result == [
    "20260102000000-add_expenses.sql",
    "20260103000000-add_incomes.sql",
  ]


def test_returns_empty_when_all_applied():
  available = ["20260101000000-create_migrations_table.sql"]
  applied = {"20260101000000-create_migrations_table.sql"}

  assert pending_migrations(available, applied) == []


def test_orders_by_timestamp_prefix_not_insertion_order():
  available = [
    "20260103000000-c.sql",
    "20260101000000-a.sql",
    "20260102000000-b.sql",
  ]

  assert pending_migrations(available, set()) == [
    "20260101000000-a.sql",
    "20260102000000-b.sql",
    "20260103000000-c.sql",
  ]
