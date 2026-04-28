import sqlite3
import pandas as pd

conn = sqlite3.connect('data/supply_chain.db')

# Test: top 5 products by revenue
df = pd.read_sql_query("""
    SELECT
        p.product_name,
        p.category,
        COUNT(f.order_id)           AS orders,
        ROUND(SUM(f.total_cost), 0) AS revenue
    FROM fact_orders f
    JOIN dim_product p ON f.product_id = p.product_id
    GROUP BY p.product_name
    ORDER BY revenue DESC
    LIMIT 5
""", conn)

print(df.to_string(index=False))
conn.close()