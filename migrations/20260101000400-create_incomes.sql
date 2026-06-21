-- Incomes. category_id references income_categories (defaults to OUTROS at the
-- service layer); description is optional. Monetary values are integer cents
-- (BRL). month is a 'YYYY-MM' string.
CREATE TABLE IF NOT EXISTS incomes (
  id BIGINT,
  category_id BIGINT,
  description VARCHAR,
  amount_cents BIGINT,
  month VARCHAR,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
