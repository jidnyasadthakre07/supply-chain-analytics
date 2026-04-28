import pandas as pd
import numpy as np
import sqlite3
import os
from pathlib import Path

DB_PATH = 'data/supply_chain.db'


# ── Helper ────────────────────────────────────────────────────────────────────
def get_connection():
    return sqlite3.connect(DB_PATH)


# ── STEP 1: Load raw data ─────────────────────────────────────────────────────
def load_raw_orders():
    """Read raw orders from CSV and do basic cleaning."""
    df = pd.read_csv('data/raw/orders.csv', parse_dates=['order_date'])

    # 1a. Drop duplicates
    df = df.drop_duplicates(subset='order_id')

    # 1b. Drop rows with null order_id or product_name
    df = df.dropna(subset=['order_id', 'product_name'])

    # 1c. Fix data types
    df['quantity_ordered'] = df['quantity_ordered'].astype(int)
    df['unit_cost']        = df['unit_cost'].astype(float).round(2)
    df['total_cost']       = (df['quantity_ordered'] * df['unit_cost']).round(2)
    df['is_delayed']       = df['is_delayed'].astype(int)

    # 1d. Standardise text columns (strip spaces, title case)
    df['product_name']  = df['product_name'].str.strip().str.title()
    df['supplier_name'] = df['supplier_name'].str.strip().str.title()
    df['region']        = df['region'].str.strip().str.title()

    print(f'Raw orders loaded: {len(df)} rows')
    return df


# ── STEP 2: Build dim_date ────────────────────────────────────────────────────
def build_dim_date(df):
    """Extract unique dates and build calendar dimension."""
    dates = df['order_date'].dt.normalize().unique()
    date_rows = []

    for d in sorted(dates):
        date_rows.append({
            'date_id'    : int(d.strftime('%Y%m%d')),   # e.g. 20220315
            'full_date'  : d.strftime('%Y-%m-%d'),
            'year'       : d.year,
            'quarter'    : (d.month - 1) // 3 + 1,
            'month'      : d.month,
            'month_name' : d.strftime('%B'),
            'week'       : int(d.strftime('%W')),
            'day_of_week': d.strftime('%A'),
        })

    dim_date = pd.DataFrame(date_rows)
    print(f'dim_date built: {len(dim_date)} unique dates')
    return dim_date


# ── STEP 3: Build dim_product ─────────────────────────────────────────────────
def build_dim_product(df):
    """Unique products with average unit cost and category."""
    category_map = {
        'Laptop'    : 'Computing', 'Monitor'  : 'Computing',
        'Phone'     : 'Mobile',    'Tablet'   : 'Mobile',
        'Keyboard'  : 'Accessories', 'Mouse'  : 'Accessories',
        'Headphones': 'Audio',     'Speaker'  : 'Audio',
        'Camera'    : 'Imaging',   'Printer'  : 'Imaging',
    }

    dim_product = (
        df.groupby('product_name')['unit_cost']
        .mean().round(2)
        .reset_index()
        .rename(columns={'unit_cost': 'unit_cost'})
    )
    dim_product.insert(0, 'product_id', range(1, len(dim_product) + 1))
    dim_product['category'] = dim_product['product_name'].map(category_map).fillna('Other')

    print(f'dim_product built: {len(dim_product)} products')
    return dim_product


# ── STEP 4: Build dim_supplier ────────────────────────────────────────────────
def build_dim_supplier(df):
    """Unique suppliers with reliability score based on delay rate."""
    supplier_stats = df.groupby('supplier_name')['is_delayed'].mean().reset_index()
    supplier_stats.columns = ['supplier_name', 'delay_rate']

    supplier_stats['reliability'] = pd.cut(
        supplier_stats['delay_rate'],
        bins   = [-0.01, 0.15, 0.30, 1.0],
        labels = ['High', 'Medium', 'Low']
    )

    dim_supplier = supplier_stats[['supplier_name', 'reliability']].copy()
    dim_supplier.insert(0, 'supplier_id', range(1, len(dim_supplier) + 1))
    dim_supplier['country'] = 'India'

    print(f'dim_supplier built: {len(dim_supplier)} suppliers')
    return dim_supplier


# ── STEP 5: Build dim_region ──────────────────────────────────────────────────
def build_dim_region(df):
    """Unique regions with zone mapping."""
    zone_map = {
        'North'  : 'North Zone',
        'South'  : 'South Zone',
        'East'   : 'East Zone',
        'West'   : 'West Zone',
        'Central': 'Central Zone',
    }

    dim_region = pd.DataFrame({
        'region_id'  : range(1, df['region'].nunique() + 1),
        'region_name': sorted(df['region'].unique()),
    })
    dim_region['zone'] = dim_region['region_name'].map(zone_map)

    print(f'dim_region built: {len(dim_region)} regions')
    return dim_region


# ── STEP 6: Build fact_orders ─────────────────────────────────────────────────
def build_fact_orders(df, dim_date, dim_product, dim_supplier, dim_region):
    """Join all dimensions to create the final fact table."""
    fact = df.copy()

    # Map date → date_id
    fact['date_id'] = fact['order_date'].dt.strftime('%Y%m%d').astype(int)

    # Map product name → product_id
    fact = fact.merge(
        dim_product[['product_id', 'product_name']],
        on='product_name', how='left'
    )

    # Map supplier name → supplier_id
    fact = fact.merge(
        dim_supplier[['supplier_id', 'supplier_name']],
        on='supplier_name', how='left'
    )

    # Map region name → region_id
    fact = fact.merge(
        dim_region[['region_id', 'region_name']],
        left_on='region', right_on='region_name', how='left'
    )

    # Select only the columns we need in the fact table
    fact_orders = fact[[
        'order_id', 'date_id', 'product_id', 'supplier_id', 'region_id',
        'quantity_ordered', 'unit_cost', 'total_cost',
        'lead_time_days', 'actual_delivery_days',
        'delay_days', 'is_delayed', 'warehouse_stock'
    ]].copy()

    print(f'fact_orders built: {len(fact_orders)} rows')
    print(f'  Nulls check: {fact_orders.isnull().sum().sum()} nulls found')
    return fact_orders


# ── STEP 7: Load all tables to SQLite ─────────────────────────────────────────
def load_star_schema(dim_date, dim_product, dim_supplier, dim_region, fact_orders):
    """Write all 5 tables to SQLite database."""
    conn = get_connection()

    # Read SQL DDL and create tables first
    from pathlib import Path  # add this at the TOP of the file (once)

def load_star_schema(dim_date, dim_product, dim_supplier, dim_region, fact_orders):
    conn = get_connection()

    BASE_DIR = Path(__file__).resolve().parent.parent
    sql_path = BASE_DIR / 'sql' / 'create_tables.sql'

    with open(sql_path, 'r') as f:
        conn.executescript(f.read())

    tables = {
        'dim_date'    : dim_date,
        'dim_product' : dim_product,
        'dim_supplier': dim_supplier,
        'dim_region'  : dim_region,
        'fact_orders' : fact_orders,
    }

    for name, df in tables.items():
        df.to_sql(name, conn, if_exists='replace', index=False)
        print(f'  Loaded {name}: {len(df)} rows')

    conn.close()
    print('\nStar schema loaded successfully.')


# ── STEP 8: Validation queries ────────────────────────────────────────────────
def validate_schema():
    """Run quick checks to confirm data quality."""
    conn = get_connection()

    checks = {
        'Total orders'        : 'SELECT COUNT(*) FROM fact_orders',
        'Unique products'     : 'SELECT COUNT(*) FROM dim_product',
        'Unique suppliers'    : 'SELECT COUNT(*) FROM dim_supplier',
        'Delayed order %'     : 'SELECT ROUND(AVG(is_delayed)*100,1) FROM fact_orders',
        'Avg lead time (days)': 'SELECT ROUND(AVG(lead_time_days),1) FROM fact_orders',
        'Total revenue'       : 'SELECT ROUND(SUM(total_cost),0) FROM fact_orders',
        'Null product_ids'    : 'SELECT COUNT(*) FROM fact_orders WHERE product_id IS NULL',
    }

    print('\n── Validation Results ───────────────────')
    for label, query in checks.items():
        result = conn.execute(query).fetchone()[0]
        print(f'  {label:<25}: {result}')

    conn.close()


# ── MAIN ──────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print('Starting transformation pipeline...\n')

    df           = load_raw_orders()
    dim_date     = build_dim_date(df)
    dim_product  = build_dim_product(df)
    dim_supplier = build_dim_supplier(df)
    dim_region   = build_dim_region(df)
    fact_orders  = build_fact_orders(df, dim_date, dim_product, dim_supplier, dim_region)

    load_star_schema(dim_date, dim_product, dim_supplier, dim_region, fact_orders)
    validate_schema()