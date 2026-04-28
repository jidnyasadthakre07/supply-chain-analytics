import pandas as pd
import sqlite3
import os

DB_PATH  = 'data/supply_chain.db'
OUT_PATH = 'data/powerbi'
os.makedirs(OUT_PATH, exist_ok=True)

conn = sqlite3.connect(DB_PATH)

exports = {
    'fact_orders'   : 'SELECT * FROM fact_orders',
    'dim_product'   : 'SELECT * FROM dim_product',
    'dim_supplier'  : 'SELECT * FROM dim_supplier',
    'dim_region'    : 'SELECT * FROM dim_region',
    'dim_date'      : 'SELECT * FROM dim_date',
    'kpi_summary'   : '''
        SELECT
            p.product_name,
            p.category,
            r.region_name,
            s.supplier_name,
            s.reliability,
            d.year,
            d.month,
            d.month_name,
            d.quarter,
            f.quantity_ordered,
            f.total_cost,
            f.lead_time_days,
            f.actual_delivery_days,
            f.delay_days,
            f.is_delayed,
            f.warehouse_stock
        FROM fact_orders f
        JOIN dim_product  p ON f.product_id  = p.product_id
        JOIN dim_supplier s ON f.supplier_id = s.supplier_id
        JOIN dim_region   r ON f.region_id   = r.region_id
        JOIN dim_date     d ON f.date_id     = d.date_id
    '''
}

for name, query in exports.items():
    df = pd.read_sql_query(query, conn)
    path = f'{OUT_PATH}/{name}.csv'
    df.to_csv(path, index=False)
    print(f'Exported {name}: {len(df)} rows → {path}')

conn.close()
print('\nAll files ready in data/powerbi/')