-- ── KPI 1: Overall business health ────────────────────────────────────────
SELECT
    COUNT(*)                            AS total_orders,
    ROUND(SUM(total_cost), 0)           AS total_revenue,
    ROUND(AVG(total_cost), 0)           AS avg_order_value,
    ROUND((1 - AVG(is_delayed))*100, 1) AS on_time_rate_pct,
    ROUND(AVG(lead_time_days), 1)       AS avg_lead_time,
    ROUND(AVG(delay_days), 2)           AS avg_delay_days
FROM fact_orders;


-- ── KPI 2: Monthly revenue trend ──────────────────────────────────────────
SELECT
    d.year,
    d.month_name,
    COUNT(f.order_id)           AS orders,
    ROUND(SUM(f.total_cost), 0) AS revenue
FROM fact_orders f
JOIN dim_date d ON f.date_id = d.date_id
GROUP BY d.year, d.month
ORDER BY d.year, d.month;


-- ── KPI 3: Top products by revenue ────────────────────────────────────────
SELECT
    p.product_name,
    p.category,
    ROUND(SUM(f.total_cost), 0)  AS revenue,
    SUM(f.quantity_ordered)      AS units_sold
FROM fact_orders f
JOIN dim_product p ON f.product_id = p.product_id
GROUP BY p.product_name
ORDER BY revenue DESC
LIMIT 5;


-- ── KPI 4: Supplier delay leaderboard ─────────────────────────────────────
SELECT
    s.supplier_name,
    s.reliability,
    ROUND(AVG(f.is_delayed)*100, 1) AS delay_rate_pct,
    ROUND(AVG(f.lead_time_days), 1) AS avg_lead_days,
    COUNT(f.order_id)               AS total_orders
FROM fact_orders f
JOIN dim_supplier s ON f.supplier_id = s.supplier_id
GROUP BY s.supplier_name
ORDER BY delay_rate_pct DESC;


-- ── KPI 5: Region SLA performance ─────────────────────────────────────────
SELECT
    r.region_name,
    ROUND(SUM(f.total_cost), 0)      AS revenue,
    ROUND(AVG(f.is_delayed)*100, 1)  AS delay_pct,
    ROUND((1-AVG(f.is_delayed))*100,1) AS on_time_pct
FROM fact_orders f
JOIN dim_region r ON f.region_id = r.region_id
GROUP BY r.region_name
ORDER BY on_time_pct DESC;