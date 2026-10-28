CREATE TABLE IF NOT EXISTS etl_run_log (
    run_id BIGSERIAL PRIMARY KEY,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'running',
    customers_inserted INTEGER NOT NULL DEFAULT 0,
    customers_updated INTEGER NOT NULL DEFAULT 0,
    customers_unchanged INTEGER NOT NULL DEFAULT 0,
    products_inserted INTEGER NOT NULL DEFAULT 0,
    products_updated INTEGER NOT NULL DEFAULT 0,
    products_unchanged INTEGER NOT NULL DEFAULT 0,
    orders_inserted INTEGER NOT NULL DEFAULT 0,
    orders_updated INTEGER NOT NULL DEFAULT 0,
    orders_unchanged INTEGER NOT NULL DEFAULT 0,
    error_message TEXT
);