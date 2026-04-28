-- ─────────────────────────────────────────────
--  DIMENSION TABLES  (lookup/descriptive data)
-- ─────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS dim_date (
    date_id     INTEGER PRIMARY KEY,
    full_date   TEXT NOT NULL,
    year        INTEGER,
    quarter     INTEGER,
    month       INTEGER,
    month_name  TEXT,
    week        INTEGER,
    day_of_week TEXT
);

CREATE TABLE IF NOT EXISTS dim_product (
    product_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name TEXT NOT NULL UNIQUE,
    category     TEXT,
    unit_cost    REAL
);

CREATE TABLE IF NOT EXISTS dim_supplier (
    supplier_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_name TEXT NOT NULL UNIQUE,
    country       TEXT DEFAULT 'India',
    reliability   TEXT   -- 'High' / 'Medium' / 'Low'
);

CREATE TABLE IF NOT EXISTS dim_region (
    region_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    region_name TEXT NOT NULL UNIQUE,
    zone        TEXT
);

-- ─────────────────────────────────────────────
--  FACT TABLE  (all measurable numbers)
-- ─────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS fact_orders (
    order_id         TEXT PRIMARY KEY,
    date_id          INTEGER,
    product_id       INTEGER,
    supplier_id      INTEGER,
    region_id        INTEGER,
    quantity_ordered INTEGER,
    unit_cost        REAL,
    total_cost       REAL,
    lead_time_days   INTEGER,
    actual_delivery_days INTEGER,
    delay_days       INTEGER,
    is_delayed       INTEGER,   -- 0 or 1 (boolean)
    warehouse_stock  INTEGER,

    FOREIGN KEY (date_id)     REFERENCES dim_date(date_id),
    FOREIGN KEY (product_id)  REFERENCES dim_product(product_id),
    FOREIGN KEY (supplier_id) REFERENCES dim_supplier(supplier_id),
    FOREIGN KEY (region_id)   REFERENCES dim_region(region_id)
);