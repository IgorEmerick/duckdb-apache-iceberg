-- Income categories. Names are unique (enforced in the service layer). The
-- OUTROS row is the fallback used when a category is deleted.
CREATE TABLE IF NOT EXISTS income_categories (
  id BIGINT,
  name VARCHAR
);
