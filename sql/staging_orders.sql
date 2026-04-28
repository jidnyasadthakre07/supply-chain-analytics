-- ── Query 1: Monthly order volume and revenue ─────────────────────────────
SELECT
    d.year,
    d.month_name,
    d.month,
    COUNT(f.order_id)          AS total_orders,
    SUM(f.quantity_ordered)    AS total_units,
    ROUND(SUM(f.total_cost),0) AS total_revenue
FROM fact_orders f
JOIN dim_date d ON f.date_id = d.date_id
GROUP BY d.year, d.month
ORDER BY d.year, d.month;


-- ── Query 2: Supplier performance (delay rate + avg lead time) ─────────────
SELECT
    s.supplier_name,
    s.reliability,
    COUNT(f.order_id)                        AS total_orders,
    ROUND(AVG(f.lead_time_days), 1)          AS avg_lead_time,
    ROUND(AVG(f.actual_delivery_days), 1)    AS avg_actual_days,
    ROUND(AVG(f.is_delayed) * 100, 1)        AS delay_rate_pct,
    ROUND(SUM(f.total_cost), 0)              AS total_value
FROM fact_orders f
JOIN dim_supplier s ON f.supplier_id = s.supplier_id
GROUP BY s.supplier_name
ORDER BY delay_rate_pct DESC;


-- ── Query 3: Product profitability and demand ─────────────────────────────
SELECT
    p.product_name,
    p.category,
    COUNT(f.order_id)               AS order_count,
    SUM(f.quantity_ordered)         AS total_qty,
    ROUND(AVG(f.unit_cost), 2)      AS avg_unit_cost,
    ROUND(SUM(f.total_cost), 0)     AS total_revenue,
    ROUND(AVG(f.warehouse_stock),0) AS avg_stock
FROM fact_orders f
JOIN dim_product p ON f.product_id = p.product_id
GROUP BY p.product_name
ORDER BY total_revenue DESC;


-- ── Query 4: Region-wise performance ──────────────────────────────────────
SELECT
    r.region_name,
    COUNT(f.order_id)               AS total_orders,
    ROUND(SUM(f.total_cost), 0)     AS total_revenue,
    ROUND(AVG(f.delay_days), 1)     AS avg_delay_days,
    ROUND(AVG(f.is_delayed)*100,1)  AS delay_rate_pct
FROM fact_orders f
JOIN dim_region r ON f.region_id = r.region_id
GROUP BY r.region_name
ORDER BY total_revenue DESC;


-- ── Query 5: Stock alert — products below reorder point ───────────────────
SELECT
    p.product_name,
    p.category,
    ROUND(AVG(f.warehouse_stock), 0)  AS current_stock,
    ROUND(AVG(f.lead_time_days), 0)   AS avg_lead_time,
    COUNT(f.order_id)                 AS monthly_demand,
    CASE
        WHEN AVG(f.warehouse_stock) < 100 THEN 'CRITICAL'
        WHEN AVG(f.warehouse_stock) < 250 THEN 'LOW'
        ELSE 'ADEQUATE'
    END AS stock_status
FROM fact_orders f
JOIN dim_product p ON f.product_id = p.product_id
GROUP BY p.product_name
ORDER BY current_stock ASC;


-- ── Query 6: Cost variance — planned vs actual ─────────────────────────────
SELECT
    p.product_name,
    ROUND(AVG(f.lead_time_days), 1)         AS planned_days,
    ROUND(AVG(f.actual_delivery_days), 1)   AS actual_days,
    ROUND(AVG(f.actual_delivery_days)
        - AVG(f.lead_time_days), 1)         AS avg_variance_days,
    ROUND(SUM(f.total_cost), 0)             AS total_spend
FROM fact_orders f
JOIN dim_product p ON f.product_id = p.product_id
GROUP BY p.product_name
ORDER BY avg_variance_days DESC;