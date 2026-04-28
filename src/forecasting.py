import pandas as pd
import numpy as np
import sqlite3
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import os
import warnings
warnings.filterwarnings('ignore')

DB_PATH  = 'data/supply_chain.db'
OUT_PATH = 'data/outputs'
os.makedirs(OUT_PATH, exist_ok=True)

# ── Chart style ───────────────────────────────────────────────────────────────
plt.rcParams.update({
    'figure.facecolor' : '#FAFAFA',
    'axes.facecolor'   : '#FAFAFA',
    'axes.spines.top'  : False,
    'axes.spines.right': False,
    'axes.grid'        : True,
    'grid.alpha'       : 0.3,
    'font.size'        : 11,
})

def get_conn():
    return sqlite3.connect(DB_PATH)


# ════════════════════════════════════════════════════════════════════════════
#  MODULE 1 — DEMAND FORECASTING  (Prophet)
# ════════════════════════════════════════════════════════════════════════════

def run_demand_forecast():
    """
    Aggregate daily order quantity, train Prophet, forecast 90 days ahead.
    Saves forecast CSV and chart.
    """
    conn = get_conn()

    # Pull daily total quantity from star schema
    df = pd.read_sql_query("""
        SELECT
            d.full_date          AS ds,
            SUM(f.quantity_ordered) AS y
        FROM fact_orders f
        JOIN dim_date d ON f.date_id = d.date_id
        GROUP BY d.full_date
        ORDER BY d.full_date
    """, conn)
    conn.close()

    df['ds'] = pd.to_datetime(df['ds'])
    df['y']  = df['y'].astype(float)

    print(f'Forecasting on {len(df)} daily observations...')

    # ── Try Prophet, fall back to simple moving average ───────────────────
    try:
        from prophet import Prophet

        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            seasonality_mode='multiplicative',
            changepoint_prior_scale=0.05,
        )
        model.fit(df)

        future = model.make_future_dataframe(periods=90)
        forecast = model.predict(future)

        result = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].copy()
        result.columns = ['date', 'forecast_qty', 'lower_bound', 'upper_bound']
        result['forecast_qty'] = result['forecast_qty'].clip(lower=0).round(0)
        result['lower_bound'] = result['lower_bound'].clip(lower=0).round(0)
        result['upper_bound'] = result['upper_bound'].round(0)
        method = 'Prophet'

    except Exception as e:
        print(f'Prophet failed ({e}) — using rolling average fallback.')

        last_date = df['ds'].max()
        future_dates = pd.date_range(last_date + pd.Timedelta(days=1), periods=90)
        rolling_mean = df['y'].rolling(30).mean().iloc[-1]

        hist = df.rename(columns={'ds': 'date', 'y': 'forecast_qty'})
        hist['lower_bound'] = hist['forecast_qty'] * 0.85
        hist['upper_bound'] = hist['forecast_qty'] * 1.15

        fut = pd.DataFrame({
            'date': future_dates,
            'forecast_qty': rolling_mean,
            'lower_bound': rolling_mean * 0.85,
            'upper_bound': rolling_mean * 1.15,
        })

        result = pd.concat([hist, fut], ignore_index=True)
        method = 'Rolling Mean'

    # ── Save CSV ──────────────────────────────────────────────────────────
    result.to_csv(f'{OUT_PATH}/forecast.csv', index=False)
    print(f'Forecast saved ({method}): {OUT_PATH}/forecast.csv')


    
    # ── Chart ─────────────────────────────────────────────────────────────
    
    # Ensure correct types
    result['date'] = pd.to_datetime(result['date'])
    result['forecast_qty'] = pd.to_numeric(result['forecast_qty'], errors='coerce')
    result['lower_bound']  = pd.to_numeric(result['lower_bound'], errors='coerce')
    result['upper_bound']  = pd.to_numeric(result['upper_bound'], errors='coerce')

    result = result.dropna()

    fig, ax = plt.subplots(figsize=(12, 5))
    cutoff = df['ds'].max()

    actual   = result[result['date'] <= cutoff]
    future_r = result[result['date'] > cutoff]

    ax.plot(actual['date'], actual['forecast_qty'],
            color='#534AB7', linewidth=1.5, label='Historical / fitted')

    ax.plot(future_r['date'], future_r['forecast_qty'],
            color='#D85A30', linewidth=2, linestyle='--', label='90-day forecast')

    ax.fill_between(
        future_r['date'],
        future_r['lower_bound'].values,
        future_r['upper_bound'].values,
        color='#D85A30',
        alpha=0.12,
        label='Confidence band'
    )

    ax.axvline(cutoff, color='gray', linewidth=1, linestyle=':')
    ax.set_title('Daily Demand Forecast — 90 Days Ahead', fontsize=14, fontweight='bold')
    ax.set_xlabel('Date')
    ax.set_ylabel('Units Ordered')
    ax.legend()
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{int(x):,}'))
    plt.tight_layout()
    plt.savefig(f'{OUT_PATH}/chart_forecast.png', dpi=150)
    plt.close()
    print(f'Chart saved: {OUT_PATH}/chart_forecast.png')

    return result


# ════════════════════════════════════════════════════════════════════════════
#  MODULE 2 — INVENTORY KPIs
# ════════════════════════════════════════════════════════════════════════════

def run_inventory_kpis():
    """
    Calculate per-product inventory KPIs:
    - Reorder point = avg daily demand × avg lead time
    - Inventory turnover = total units sold / avg stock
    - Stock status = Critical / Low / Adequate
    """
    conn = get_conn()

    df = pd.read_sql_query("""
        SELECT
            p.product_name,
            p.category,
            COUNT(f.order_id)               AS total_orders,
            SUM(f.quantity_ordered)         AS total_units_sold,
            ROUND(AVG(f.warehouse_stock),0) AS avg_stock,
            ROUND(AVG(f.lead_time_days),1)  AS avg_lead_time,
            ROUND(SUM(f.total_cost),0)      AS total_revenue
        FROM fact_orders f
        JOIN dim_product p ON f.product_id = p.product_id
        GROUP BY p.product_name, p.category
        ORDER BY total_revenue DESC
    """, conn)
    conn.close()

    # ── KPI calculations ──────────────────────────────────────────────────
    # Avg daily demand (over 730 days)
    df['avg_daily_demand'] = (df['total_units_sold'] / 730).round(2)

    # Reorder point: order new stock when stock reaches this level
    df['reorder_point'] = (
        df['avg_daily_demand'] * df['avg_lead_time']
    ).round(0).astype(int)

    # Safety stock (1.5× lead time demand as buffer)
    df['safety_stock'] = (
        df['avg_daily_demand'] * df['avg_lead_time'] * 1.5
    ).round(0).astype(int)

    # Inventory turnover (higher = faster moving product)
    df['inventory_turnover'] = (
        df['total_units_sold'] / df['avg_stock'].replace(0, np.nan)
    ).round(2)

    # Days of stock remaining
    df['days_of_stock'] = (
        df['avg_stock'] / df['avg_daily_demand'].replace(0, np.nan)
    ).round(1)

    # Stock status
    df['stock_status'] = pd.cut(
        df['avg_stock'],
        bins   = [-1, 100, 300, 99999],
        labels = ['CRITICAL', 'LOW', 'ADEQUATE']
    )

    # ── Save CSV ──────────────────────────────────────────────────────────
    df.to_csv(f'{OUT_PATH}/kpi_inventory.csv', index=False)
    print(f'Inventory KPIs saved: {OUT_PATH}/kpi_inventory.csv')

    # ── Chart: Inventory turnover by product ──────────────────────────────
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Left: turnover bar chart
    colors = ['#D85A30' if s == 'CRITICAL' else
              '#EF9F27' if s == 'LOW' else '#1D9E75'
              for s in df['stock_status']]

    axes[0].barh(df['product_name'], df['inventory_turnover'], color=colors)
    axes[0].set_title('Inventory Turnover by Product', fontweight='bold')
    axes[0].set_xlabel('Turnover Ratio')
    axes[0].invert_yaxis()

    # Right: days of stock remaining
    axes[1].barh(df['product_name'], df['days_of_stock'], color='#534AB7')
    axes[1].axvline(30, color='#D85A30', linestyle='--', linewidth=1.5,
                    label='30-day threshold')
    axes[1].set_title('Days of Stock Remaining', fontweight='bold')
    axes[1].set_xlabel('Days')
    axes[1].invert_yaxis()
    axes[1].legend()

    plt.suptitle('Inventory Health Dashboard', fontsize=13, fontweight='bold', y=1.01)
    plt.tight_layout()
    plt.savefig(f'{OUT_PATH}/chart_inventory.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f'Chart saved: {OUT_PATH}/chart_inventory.png')

    return df


# ════════════════════════════════════════════════════════════════════════════
#  MODULE 3 — SUPPLIER RISK SCORING
# ════════════════════════════════════════════════════════════════════════════

def run_supplier_risk():
    """
    Score each supplier on a 0–100 risk index using:
      - Delay rate (40% weight)
      - Avg lead time vs benchmark (35% weight)
      - Lead time variance (25% weight)
    Higher score = higher risk.
    """
    conn = get_conn()

    df = pd.read_sql_query("""
        SELECT
            s.supplier_name,
            s.reliability,
            COUNT(f.order_id)                       AS total_orders,
            ROUND(AVG(f.is_delayed)*100, 2)         AS delay_rate_pct,
            ROUND(AVG(f.lead_time_days), 1)         AS avg_lead_time,
            ROUND(MIN(f.lead_time_days), 0)         AS min_lead_time,
            ROUND(MAX(f.lead_time_days), 0)         AS max_lead_time,
            ROUND(SUM(f.total_cost), 0)             AS total_spend
        FROM fact_orders f
        JOIN dim_supplier s ON f.supplier_id = s.supplier_id
        GROUP BY s.supplier_name
        ORDER BY delay_rate_pct DESC
    """, conn)
    conn.close()

    # ── Risk score calculation ────────────────────────────────────────────
    benchmark_lead_time = 15   # days — industry benchmark

    # Normalise each component to 0–100
    df['delay_score'] = (df['delay_rate_pct'] / 100 * 100).clip(0, 100)

    df['lead_time_score'] = (
        (df['avg_lead_time'] - benchmark_lead_time) /
        benchmark_lead_time * 100
    ).clip(0, 100)

    df['variance_score'] = (
        (df['max_lead_time'] - df['min_lead_time']) / df['avg_lead_time'] * 100
    ).clip(0, 100)

    # Weighted composite risk index
    df['risk_score'] = (
        df['delay_score']    * 0.40 +
        df['lead_time_score']* 0.35 +
        df['variance_score'] * 0.25
    ).round(1)

    df['risk_label'] = pd.cut(
        df['risk_score'],
        bins   = [-1, 30, 60, 101],
        labels = ['Low Risk', 'Medium Risk', 'High Risk']
    )

    # ── Save CSV ──────────────────────────────────────────────────────────
    df.to_csv(f'{OUT_PATH}/supplier_risk.csv', index=False)
    print(f'Supplier risk saved: {OUT_PATH}/supplier_risk.csv')

    # ── Chart: risk scorecard ─────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(10, 5))

    bar_colors = ['#D85A30' if r == 'High Risk' else
                  '#EF9F27' if r == 'Medium Risk' else '#1D9E75'
                  for r in df['risk_label']]

    bars = ax.bar(df['supplier_name'], df['risk_score'],
                  color=bar_colors, width=0.55, edgecolor='none')

    # Annotate each bar
    for bar, score in zip(bars, df['risk_score']):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 1,
                f'{score}', ha='center', va='bottom',
                fontsize=11, fontweight='bold')

    ax.axhline(60, color='#D85A30', linestyle='--', linewidth=1,
               label='High risk threshold (60)')
    ax.axhline(30, color='#EF9F27', linestyle='--', linewidth=1,
               label='Medium risk threshold (30)')
    ax.set_title('Supplier Risk Score Index (0 = safe, 100 = critical)',
                 fontsize=13, fontweight='bold')
    ax.set_ylabel('Risk Score')
    ax.set_ylim(0, 105)
    ax.legend()
    plt.tight_layout()
    plt.savefig(f'{OUT_PATH}/chart_supplier_risk.png', dpi=150)
    plt.close()
    print(f'Chart saved: {OUT_PATH}/chart_supplier_risk.png')

    return df


# ════════════════════════════════════════════════════════════════════════════
#  MODULE 4 — COST VARIANCE ANALYSIS
# ════════════════════════════════════════════════════════════════════════════

def run_cost_variance():
    """
    Compare planned vs actual delivery performance.
    Calculates delay cost impact assuming each extra day = 0.5% of order value.
    """
    conn = get_conn()

    df = pd.read_sql_query("""
        SELECT
            d.year,
            d.month,
            d.month_name,
            d.quarter,
            p.category,
            COUNT(f.order_id)                           AS total_orders,
            ROUND(SUM(f.total_cost), 0)                 AS planned_spend,
            ROUND(AVG(f.lead_time_days), 1)             AS planned_days,
            ROUND(AVG(f.actual_delivery_days), 1)       AS actual_days,
            ROUND(AVG(f.delay_days), 2)                 AS avg_delay,
            SUM(f.is_delayed)                           AS delayed_orders
        FROM fact_orders f
        JOIN dim_date    d ON f.date_id    = d.date_id
        JOIN dim_product p ON f.product_id = p.product_id
        GROUP BY d.year, d.month, p.category
        ORDER BY d.year, d.month
    """, conn)
    conn.close()

    # ── Variance metrics ──────────────────────────────────────────────────
    df['day_variance']    = (df['actual_days'] - df['planned_days']).round(2)
    df['delay_cost']      = (
        df['planned_spend'] * df['avg_delay'] * 0.005
    ).round(0)   # 0.5% per delayed day
    df['on_time_rate']    = (
        1 - df['delayed_orders'] / df['total_orders']
    ).round(3) * 100
    df['period']          = df['year'].astype(str) + '-Q' + df['quarter'].astype(str)

    # ── Save CSV ──────────────────────────────────────────────────────────
    df.to_csv(f'{OUT_PATH}/cost_variance.csv', index=False)
    print(f'Cost variance saved: {OUT_PATH}/cost_variance.csv')

    # ── Charts ────────────────────────────────────────────────────────────
    fig, axes = plt.subplots(2, 1, figsize=(13, 9))

    # Top: monthly spend by category (stacked bar)
    pivot = df.pivot_table(
        index='month', columns='category',
        values='planned_spend', aggfunc='sum'
    ).fillna(0)

    palette = ['#534AB7', '#1D9E75', '#D85A30', '#EF9F27', '#185FA5']
    pivot.plot(kind='bar', stacked=True, ax=axes[0],
               color=palette[:len(pivot.columns)],
               edgecolor='none', width=0.7)
    axes[0].set_title('Monthly Revenue by Product Category', fontweight='bold')
    axes[0].set_xlabel('Month')
    axes[0].set_ylabel('Revenue (₹)')
    axes[0].yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda x, _: f'₹{x/1e6:.1f}M'))
    axes[0].legend(title='Category', bbox_to_anchor=(1.01, 1), loc='upper left')
    axes[0].tick_params(axis='x', rotation=0)

    # Bottom: on-time delivery rate over time (line)
    monthly_ot = df.groupby('month')['on_time_rate'].mean().reset_index()

    # FIX: ensure numeric types
    monthly_ot['month'] = pd.to_numeric(monthly_ot['month'], errors='coerce')
    monthly_ot['on_time_rate'] = pd.to_numeric(monthly_ot['on_time_rate'], errors='coerce')

    # remove bad rows
    monthly_ot = monthly_ot.dropna()
    
    axes[1].plot(
    monthly_ot['month'].values,
    monthly_ot['on_time_rate'].values,
    color='#534AB7',
    linewidth=2.5,
    marker='o',
    markersize=5
)
    axes[1].axhline(80, color='#D85A30', linestyle='--', linewidth=1.5,
                    label='80% SLA target')
    axes[1].fill_between(
    monthly_ot['month'].values,
    monthly_ot['on_time_rate'].values,
    80,
    where=(monthly_ot['on_time_rate'].values < 80),
    color='#D85A30',
    alpha=0.15,
    label='Below SLA'
)
    axes[1].set_title('On-Time Delivery Rate by Month', fontweight='bold')
    axes[1].set_xlabel('Month')
    axes[1].set_ylabel('On-Time Rate (%)')
    axes[1].set_ylim(60, 100)
    axes[1].legend()

    plt.suptitle('Cost & Delivery Variance Analysis', fontsize=14,
                 fontweight='bold', y=1.01)
    plt.tight_layout()
    plt.savefig(f'{OUT_PATH}/chart_cost_variance.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f'Chart saved: {OUT_PATH}/chart_cost_variance.png')

    return df


# ════════════════════════════════════════════════════════════════════════════
#  MODULE 5 — EXECUTIVE KPI SUMMARY
# ════════════════════════════════════════════════════════════════════════════

def run_kpi_summary():
    """
    Build a single executive-level summary table with the most
    important KPIs across the whole dataset.
    """
    conn = get_conn()

    summary = {}

    queries = {
        'total_orders'        : 'SELECT COUNT(*) FROM fact_orders',
        'total_revenue'       : 'SELECT ROUND(SUM(total_cost),0) FROM fact_orders',
        'avg_order_value'     : 'SELECT ROUND(AVG(total_cost),0) FROM fact_orders',
        'on_time_rate_pct'    : 'SELECT ROUND((1-AVG(is_delayed))*100,1) FROM fact_orders',
        'avg_lead_time_days'  : 'SELECT ROUND(AVG(lead_time_days),1) FROM fact_orders',
        'avg_delay_days'      : 'SELECT ROUND(AVG(delay_days),2) FROM fact_orders',
        'critical_stock_items': """
            SELECT COUNT(*) FROM (
                SELECT product_id
                FROM fact_orders
                GROUP BY product_id
                HAVING AVG(warehouse_stock) < 100
            )""",
        'high_risk_suppliers' : """
            SELECT COUNT(*) FROM dim_supplier
            WHERE reliability = 'Low'""",
    }

    for key, q in queries.items():
        summary[key] = conn.execute(q).fetchone()[0]

    conn.close()

    kpi_df = pd.DataFrame([{
        'KPI'  : k.replace('_', ' ').title(),
        'Value': v
    } for k, v in summary.items()])

    kpi_df.to_csv(f'{OUT_PATH}/kpi_summary.csv', index=False)
    print(f'\nExecutive KPI Summary:')
    print(f'{"─"*40}')
    for _, row in kpi_df.iterrows():
        print(f"  {row['KPI']:<28}: {row['Value']}")

    return kpi_df


# ════════════════════════════════════════════════════════════════════════════
#  RUN ALL MODULES
# ════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print('='*55)
    print(' PHASE 4 — ANALYTICS & FORECASTING')
    print('='*55)

    print('\n[1/5] Running demand forecast...')
    forecast_df = run_demand_forecast()

    print('\n[2/5] Running inventory KPIs...')
    kpi_df = run_inventory_kpis()

    print('\n[3/5] Running supplier risk scoring...')
    risk_df = run_supplier_risk()

    print('\n[4/5] Running cost variance analysis...')
    variance_df = run_cost_variance()

    print('\n[5/5] Building executive KPI summary...')
    summary_df = run_kpi_summary()

    print('\n' + '='*55)
    print(' ALL OUTPUTS SAVED TO: data/outputs/')
    print('='*55)
    print('\n  forecast.csv         — 90-day demand prediction')
    print('  kpi_inventory.csv    — per-product KPIs')
    print('  supplier_risk.csv    — weighted risk scores')
    print('  cost_variance.csv    — planned vs actual delivery')
    print('  kpi_summary.csv      — executive summary')
    print('  chart_forecast.png')
    print('  chart_inventory.png')
    print('  chart_supplier_risk.png')
    print('  chart_cost_variance.png')