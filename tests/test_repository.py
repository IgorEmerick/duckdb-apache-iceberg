from db import store
from services import _repository as repository


def test_next_id_is_one_for_empty_table(catalog):
  # incomes starts empty
  assert repository.next_id(catalog, "incomes") == 1


def test_insert_generates_sequential_ids(catalog):
  # expense_categories already holds OUTROS (id 1)
  first = repository.insert_with_generated_id(
    catalog, "expense_categories", {"name": "A"}
  )
  second = repository.insert_with_generated_id(
    catalog, "expense_categories", {"name": "B"}
  )

  assert (first, second) == (2, 3)
  names = {row["name"] for row in store.rows(catalog, "expense_categories")}
  assert {"OUTROS", "A", "B"} == names
