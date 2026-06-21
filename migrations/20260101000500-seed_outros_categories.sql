-- Seed the OUTROS fallback category (id 1) in both category tables. OUTROS is
-- immutable (cannot be renamed or deleted) and receives rows whose category is
-- deleted. Guarded so the seed is idempotent across restarts.
INSERT INTO expense_categories (id, name)
SELECT 1, 'OUTROS'
WHERE NOT EXISTS (SELECT 1 FROM expense_categories WHERE name = 'OUTROS');

INSERT INTO income_categories (id, name)
SELECT 1, 'OUTROS'
WHERE NOT EXISTS (SELECT 1 FROM income_categories WHERE name = 'OUTROS');
