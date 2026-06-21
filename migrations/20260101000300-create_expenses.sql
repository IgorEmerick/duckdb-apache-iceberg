-- Expenses. category_id references expense_categories; description is required.
-- Monetary values are integer cents (BRL). month is a 'YYYY-MM' string.
CREATE TABLE IF NOT EXISTS expenses (
  id BIGINT,
  category_id BIGINT,
  description VARCHAR,
  payment_method VARCHAR,
  amount_cents BIGINT,
  month VARCHAR,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
