-- Expense categories. Names are unique (enforced in the service layer, since
-- Iceberg-backed tables do not enforce constraints). The OUTROS row is the
-- fallback used when a category is deleted.
CREATE TABLE IF NOT EXISTS expense_categories (
  id BIGINT,
  name VARCHAR
);
