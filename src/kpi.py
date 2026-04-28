import pandas as pd
import sqlite3

DB_PATH = 'data/supply_chain.db'

def get_conn():
    return sqlite3.connect(DB_PATH)


def kpi_executive_summary():
    """Return a dict of top-level executive KPIs."""
    conn = get_conn()
    kpis = {}

    queries = {
        'total_orders'        : 'SELECT COUNT(*) FROM fact_orders',
        'total_revenue'       : 'SELECT ROUND(SUM(total_cost), 0) FROM fact_orders',
        'avg_order_value'     : 'SELECT ROUND(AVG(total_cost), 0) FROM fact_orders',
        'on_time_rate_pct'    : 'SELECT ROUND((1 - AVG(is_delayed)) * 100, 1) FROM fact_orders',
        'avg_lead_time_days'  : 'SELECT ROUND(AVG(lead_time_days), 1) FROM fact_orders',
        'avg_delay_days'      : 'SELECT ROUND(AVG(delay_days), 2) FROM fact_orders',
        'total_delayed_orders': 'SELECT SUM(is_delayed) FROM fact_orders',
        'high_risk_suppliers' : "SELECT COUNT(*) FROM dim_supplier WHERE reliability = 'Low'",
        'critical_stock_items': """
            SELECT COUNT(*) FROM (
                SELECT product_id FROM fact_orders
                GROUP BY product_id
                HAVING AVG(warehouse_stock) < 100
            )
        """,
    }

    for key, q in queries.items():
        kpis[key] = conn.execute(q).fetchone()[0]

    conn.close()
    return kpis


def kpi_by_region():
    """Revenue and delay rate broken down by region."""
    conn = get_conn()
    df = pd.read_sql_query("""
        SELECT
            r.region_name,
            COUNT(f.order_id)               AS total_orders,
            ROUND(SUM(f.total_cost), 0)     AS total_revenue,
            ROUND(AVG(f.is_delayed)*100, 1) AS delay_rate_pct
        FROM fact_orders f
        JOIN dim_region r ON f.region_id = r.region_id
        GROUP BY r.region_name
        ORDER BY total_revenue DESC
    """, conn)
    conn.close()
    return df


def kpi_by_product():
    """Revenue, quantity and stock status per product."""
    conn = get_conn()
    df = pd.read_sql_query("""
        SELECT
            p.product_name,
            p.category,
            SUM(f.quantity_ordered)          AS total_qty,
            ROUND(SUM(f.total_cost), 0)      AS total_revenue,
            ROUND(AVG(f.warehouse_stock), 0) AS avg_stock,
            ROUND(AVG(f.lead_time_days), 1)  AS avg_lead_time
        FROM fact_orders f
        JOIN dim_product p ON f.product_id = p.product_id
        GROUP BY p.product_name
        ORDER BY total_revenue DESC
    """, conn)
    conn.close()
    return df


def kpi_monthly_trend():
    """Monthly order volume and revenue for trend analysis."""
    conn = get_conn()
    df = pd.read_sql_query("""
        SELECT
            d.year,
            d.month,
            d.month_name,
            COUNT(f.order_id)           AS total_orders,
            ROUND(SUM(f.total_cost), 0) AS total_revenue,
            ROUND(AVG(f.is_delayed)*100,1) AS delay_rate_pct
        FROM fact_orders f
        JOIN dim_date d ON f.date_id = d.date_id
        GROUP BY d.year, d.month
        ORDER BY d.year, d.month
    """, conn)
    conn.close()
    return df


if __name__ == '__main__':
    print('── Executive KPIs ──────────────────────')
    summary = kpi_executive_summary()
    for k, v in summary.items():
        print(f'  {k:<28}: {v}')

    print('\n── Revenue by Region ───────────────────')
    print(kpi_by_region().to_string(index=False))

    print('\n── Revenue by Product ──────────────────')
    print(kpi_by_product().to_string(index=False))