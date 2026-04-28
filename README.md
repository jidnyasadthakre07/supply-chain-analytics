# 🏭 Supply Chain & Demand Forecasting Intelligence Platform

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![SQL](https://img.shields.io/badge/SQL-SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![Power BI](https://img.shields.io/badge/Power%20BI-Dashboard-F2C811?style=for-the-badge&logo=powerbi&logoColor=black)
![Pandas](https://img.shields.io/badge/Pandas-Data%20Engineering-150458?style=for-the-badge&logo=pandas&logoColor=white)
![Prophet](https://img.shields.io/badge/Prophet-Forecasting-FF6F00?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Complete-1D9E75?style=for-the-badge)

**An end-to-end data analytics platform covering the full data lifecycle —**
**from raw ingestion to executive-level BI dashboard — built for Data Engineer, Data Analyst, and Business Analyst roles.**

[Overview](#-project-overview) • [Architecture](#-architecture) • [Project Structure](#-project-structure) • [Pipeline](#-data-pipeline) • [Analytics](#-analytics--kpis) • [Dashboard](#-power-bi-dashboard) • [Setup](#-quick-start) • [Results](#-key-business-insights) • [Skills](#-skills-demonstrated)

</div>

---

## 📌 Project Overview

This project simulates a **real-world supply chain analytics platform** for a multi-region retail company operating across 5 regions, 10 product categories, and 5 suppliers. It processes **2,000+ orders spanning 2 years** of transactional data.

The platform answers critical business questions:

| Business Question | Analytics Module |
|---|---|
| How much demand will we see in the next 90 days? | Demand Forecasting (Prophet) |
| Which products are at risk of stocking out? | Inventory KPI Engine |
| Which supplier is causing the most delays? | Supplier Risk Scoring |
| Are we meeting our SLA targets? | Cost & Delivery Variance |
| What is our overall supply chain health? | Executive KPI Dashboard |

> **Why this project?** Supply chain analytics is one of the highest-demand skill sets in the data industry. Companies like Amazon, Flipkart, Walmart, and Maersk hire thousands of data professionals specifically for supply chain intelligence. This project demonstrates the exact skills those roles require.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                                 │
│   ERP Orders  │  Inventory Data  │  Supplier Info  │  Region Data   │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   DATA ENGINEERING LAYER                            │
│                                                                     │
│   ingestion.py          transformation.py                           │
│   ┌─────────────┐       ┌──────────────────────────────────────┐    │
│   │ Generate    │──────▶│ Clean → Star Schema → SQLite         |    |
│   │ 2000 orders │       │ fact_orders + 4 dimension tables     │    │
│   └─────────────┘       └──────────────────────────────────────┘    │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     ANALYTICS LAYER                                 │
│                                                                     │
│  forecasting.py                    kpi.py                           │
│  ┌─────────────────────┐          ┌──────────────────────────┐      │
│  │ Demand Forecast     │          │ Inventory KPIs           │      │
│  │ Supplier Risk Score │          │ Cost Variance Analysis   │      │
│  │ 90-day Prediction   │          │ Executive KPI Summary    │      │
│  └─────────────────────┘          └──────────────────────────┘      │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  BUSINESS INTELLIGENCE LAYER                        │
│                                                                     │
│   Power BI Dashboard                                                │
│   ┌──────────┐ ┌──────────┐ ┌───────────────┐ ┌─────────────────┐   │
│   │ 4 KPI    │ │ Revenue  │ │ Supplier Risk │ │ Stock Alert     │   │
│   │ Cards    │ │ Trends   │ │ Scorecard     │ │ Table           │   │
│   └──────────┘ └──────────┘ └───────────────┘ └─────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
supply_chain_project/
│
├── 📂 data/
│   ├── raw/                        ← source CSV files (generated)
│   │   ├── orders.csv              ← 2000 order records
│   │   └── inventory.csv           ← product inventory snapshot
│   ├── processed/                  ← cleaned, transformed data
│   ├── powerbi/                    ← CSV exports for Power BI
│   │   ├── fact_orders.csv
│   │   ├── dim_product.csv
│   │   ├── dim_supplier.csv
│   │   ├── dim_region.csv
│   │   ├── dim_date.csv
│   │   └── kpi_summary.csv
│   └── outputs/                    ← charts, forecasts, KPI reports
│       ├── forecast.csv
│       ├── kpi_inventory.csv
│       ├── supplier_risk.csv
│       ├── cost_variance.csv
│       ├── kpi_summary.csv
│       ├── chart_forecast.png
│       ├── chart_inventory.png
│       ├── chart_supplier_risk.png
│       └── chart_cost_variance.png
│
├── 📂 notebooks/
│   ├── 01_data_ingestion.ipynb     ← Phase 2: data generation & loading
│   ├── 02_transformation.ipynb     ← Phase 3: star schema build
│   ├── 03_forecasting.ipynb        ← Phase 4: forecasting & analytics
│   └── 04_kpi_analysis.ipynb       ← Phase 4b: KPI deep dive
│
├── 📂 src/
│   ├── ingestion.py                ← data generation and SQLite loading
│   ├── transformation.py           ← star schema builder (8 functions)
│   ├── forecasting.py              ← 5 analytics modules
│   ├── kpi.py                      ← KPI calculation engine
│   └── export_for_powerbi.py       ← exports CSVs for Power BI
│
├── 📂 sql/
│   ├── create_tables.sql           ← DDL: star schema table definitions
│   ├── staging_orders.sql          ← 6 business KPI queries
│   ├── kpi_queries.sql             ← executive KPI SQL queries
│   └── test_query.py               ← validation script
│
├── 📂 dashboard/
│   └── supply_chain_dashboard.pbix ← Power BI dashboard file
│
├── requirements.txt
└── README.md
```

---

## 🔄 Data Pipeline

The pipeline runs in 4 sequential steps. Each step is independent and modular.

### Phase 1 — Data Ingestion (`src/ingestion.py`)

Generates **2,000 realistic supply chain orders** using NumPy and Pandas, simulating:
- 10 products across 5 categories (Computing, Mobile, Audio, Imaging, Accessories)
- 5 suppliers with varying reliability profiles
- 5 geographic regions (North, South, East, West, Central)
- 730 days of order history (2022–2023)
- Realistic delay simulation (approx. 25% of orders delayed)

```python
# Key function signatures
generate_orders(n=2000)      → DataFrame   # creates raw order records
generate_inventory(df)       → DataFrame   # computes inventory snapshot
save_to_csv(df, filename)    → path        # saves to data/raw/
load_to_sqlite(df, table)    → None        # loads to SQLite warehouse
```

### Phase 2 — Data Transformation (`src/transformation.py`)

Cleans raw data and builds a **Kimball-style star schema**:

```
                    ┌──────────────┐
                    │   dim_date   │
                    │  date_id PK  │
                    └──────┬───────┘
                           │
┌──────────────┐    ┌──────┴────────┐    ┌───────────────┐
│ dim_product  │    │  fact_orders  │    │ dim_supplier  │
│ product_id PK│◀───│  order_id PK  │───▶│ supplier_id PK│
└──────────────┘    │  product_id FK│    └───────────────┘
                    │  supplier_id  │
┌──────────────┐    │  region_id    │
│  dim_region  │◀───│  date_id FK   │
│  region_id PK│    │  quantity     │
└──────────────┘    │  total_cost   │
                    │  lead_time    │
                    │  is_delayed   │
                    └───────────────┘
```

**Data quality steps applied:**
- Duplicate removal on `order_id`
- Null handling on critical fields
- Data type enforcement (int, float, datetime)
- Text standardisation (strip, title case)
- FK validation — zero null foreign keys in final fact table

### Phase 3 — Analytics & Forecasting (`src/forecasting.py`)

Five analytics modules run sequentially:

#### Module 1: Demand Forecasting
- Uses **Meta Prophet** with yearly + weekly seasonality
- Trained on 730 days of daily order quantities
- Outputs 90-day forward forecast with confidence intervals
- Falls back to 30-day rolling average if Prophet unavailable

#### Module 2: Inventory KPIs
```
Reorder Point   = Avg Daily Demand × Avg Lead Time
Safety Stock    = Avg Daily Demand × Avg Lead Time × 1.5
Turnover Ratio  = Total Units Sold ÷ Avg Stock on Hand
Days of Stock   = Avg Stock ÷ Avg Daily Demand
```

#### Module 3: Supplier Risk Scoring
Composite weighted risk index (0–100):
```
Risk Score = (Delay Rate × 0.40)
           + (Lead Time vs Benchmark × 0.35)
           + (Lead Time Variance × 0.25)

Risk Labels:  0–30 → Low Risk
             31–60 → Medium Risk
             61–100 → High Risk
```

#### Module 4: Cost Variance Analysis
```
Day Variance = Actual Delivery Days − Planned Lead Time
Delay Cost   = Order Value × Delay Days × 0.5%
On-Time Rate = (1 − Delayed Orders ÷ Total Orders) × 100
```

#### Module 5: Executive KPI Summary
Single-table summary of 8 top-level business metrics for stakeholder reporting.

---

## 📊 Analytics & KPIs

### KPI Framework

| KPI | Formula | Target | Status |
|-----|---------|--------|--------|
| On-Time Delivery Rate | (1 − avg delayed) × 100 | ≥ 80% | ⚠️ 75.1% |
| Avg Lead Time | avg(lead_time_days) | ≤ 20 days | ⚠️ 24.0 days |
| Inventory Turnover | units_sold ÷ avg_stock | ≥ 6× | ✅ varies |
| Supplier Risk Score | weighted composite | ≤ 30 | ⚠️ 1 high-risk |
| Critical Stock Items | stock < reorder_point | 0 | ❌ 2 items |

### SQL KPI Queries (`sql/kpi_queries.sql`)

All KPIs are available as production-ready SQL queries that join the star schema:

```sql
-- Example: Supplier performance leaderboard
SELECT
    s.supplier_name,
    s.reliability,
    ROUND(AVG(f.is_delayed)*100, 1)   AS delay_rate_pct,
    ROUND(AVG(f.lead_time_days), 1)   AS avg_lead_time,
    COUNT(f.order_id)                 AS total_orders
FROM fact_orders f
JOIN dim_supplier s ON f.supplier_id = s.supplier_id
GROUP BY s.supplier_name
ORDER BY delay_rate_pct DESC;
```

---

## 📈 Power BI Dashboard

The executive dashboard (`dashboard/supply_chain_dashboard.pbix`) contains:

| Visual | Type | Business Purpose |
|--------|------|-----------------|
| Total Revenue | KPI Card | Headline financial performance |
| On-Time Rate | KPI Card | SLA compliance at a glance |
| Total Orders | KPI Card | Volume indicator |
| Avg Lead Time | KPI Card | Operational efficiency |
| Revenue by Product | Horizontal Bar | Product profitability ranking |
| Monthly Revenue Trend | Line Chart | Growth and seasonality patterns |
| Supplier Delay Rate | Column Chart | Supplier risk comparison |
| Stock Alert Table | Conditional Table | CRITICAL / LOW / OK alerts |
| Orders by Region | Donut Chart | Geographic distribution |
| Year Slicer | Filter | Time-based filtering |
| Category Slicer | Filter | Product category filtering |

**Dashboard is fully interactive** — slicers filter all visuals simultaneously.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Windows OS (for Power BI Desktop)
- Git

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/jidnyasadthakre07/supply-chain-analytics.git
cd supply-chain-analytics

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
venv\Scripts\activate          # Windows
source venv/bin/activate       # Mac/Linux

# 4. Install all dependencies
pip install -r requirements.txt
```

### Run the Full Pipeline

```bash
# Step 1 — Generate and load raw data
python src/ingestion.py

# Step 2 — Build star schema and load to SQLite
python src/transformation.py

# Step 3 — Run all analytics modules + generate charts
python src/forecasting.py

# Step 4 — Calculate KPIs
python src/kpi.py

# Step 5 — Export CSVs for Power BI
python src/export_for_powerbi.py
```

### Expected Output After Running

```
data/
├── supply_chain.db          ← SQLite warehouse (5 tables, 2000+ rows)
├── raw/
│   ├── orders.csv           ← 2000 order records
│   └── inventory.csv        ← 10 product snapshots
├── powerbi/
│   └── *.csv                ← 6 CSV files ready for Power BI
└── outputs/
    ├── forecast.csv         ← 90-day demand prediction
    ├── kpi_inventory.csv    ← per-product KPI metrics
    ├── supplier_risk.csv    ← weighted risk scores
    ├── cost_variance.csv    ← planned vs actual delivery
    ├── kpi_summary.csv      ← executive summary
    └── chart_*.png          ← 4 analysis charts
```

---

## 📦 Dependencies

```
pandas==2.1.0          # data manipulation
numpy==1.24.0          # numerical operations
matplotlib==3.7.0      # chart generation
seaborn==0.12.0        # statistical visualisation
scikit-learn==1.3.0    # ML utilities
prophet==1.1.4         # time-series forecasting
sqlalchemy==2.0.0      # database interface
jupyter==1.0.0         # notebook environment
openpyxl==3.1.0        # Excel export support
plotly==5.15.0         # interactive charts
```

Install all with:
```bash
pip install -r requirements.txt
```

---

## 💡 Key Business Insights

These are the actual insights this platform surfaces from the data:

**1. SLA Breach Detected**
> On-time delivery rate is **75.1%** — 4.9 points below the industry-standard 80% SLA target. This translates to approximately **498 delayed orders** out of 2,000, with an average delay of 3.7 days per affected order.

**2. Critical Stock Alert**
> **2 products** (Camera and Printer) are in CRITICAL stock status — current warehouse stock is below their calculated reorder points. Without immediate procurement action, these products will stock out before the next shipment arrives.

**3. High-Risk Supplier Identified**
> One supplier has a **delay rate exceeding 30%** — more than double the network average of ~12%. The composite risk score places this supplier in the HIGH RISK category (score > 60), driven primarily by lead time unpredictability.

**4. Revenue Concentration**
> The top 3 products (Laptop, Phone, Monitor) account for approximately **58% of total revenue**. A disruption in any of these product lines would have an outsized impact on overall business performance.

**5. 90-Day Demand Forecast**
> The Prophet model forecasts a **moderate upward trend** in demand over the next 90 days, with clear weekly seasonality patterns. This gives procurement teams a data-backed basis for purchase order planning.

---

## 🛠️ Tech Stack

| Category | Technology | Purpose |
|----------|-----------|---------|
| Language | Python 3.10+ | Core pipeline and analytics |
| Data manipulation | Pandas, NumPy | Ingestion, cleaning, transformation |
| Database | SQLite + SQLAlchemy | Local data warehouse |
| Data modelling | Star schema (Kimball) | Analytical query optimisation |
| Forecasting | Meta Prophet | Time-series demand prediction |
| Visualisation | Matplotlib, Seaborn | Chart generation |
| BI Dashboard | Power BI Desktop | Executive reporting |
| Query language | SQL | KPI calculations and data access |
| Environment | Jupyter Notebooks | Exploratory analysis |
| Version control | Git + GitHub | Code management |

---

## 🎯 Skills Demonstrated

### Data Engineer
- Built modular ETL pipeline: Extract → Transform → Load in separate, reusable Python modules
- Designed Kimball star schema with `fact_orders` central table and 4 dimension tables
- Wrote DDL SQL (`CREATE TABLE` with `PRIMARY KEY`, `FOREIGN KEY`, data types)
- Implemented data quality checks: deduplication, null handling, type casting, FK validation
- Loaded structured data into SQLite — a lightweight production-equivalent data warehouse
- Created parameterised, reusable functions across all pipeline stages

### Data Analyst
- Built 90-day demand forecasting model using Meta Prophet with seasonality configuration
- Designed inventory KPI framework: reorder point, safety stock, turnover ratio, days of stock
- Developed composite supplier risk scoring model with weighted index methodology
- Performed cost variance analysis: planned vs actual lead time, SLA breach detection
- Generated 4 professional analytical charts using Matplotlib and Seaborn
- Wrote 10+ complex SQL queries joining multiple tables with aggregation and filtering

### Business Analyst
- Translated raw operational data into executive-level KPI narrative
- Built conditional stock alert system with CRITICAL / LOW / OK status classification
- Designed stakeholder-ready Power BI dashboard with 9 interactive visuals and 2 slicers
- Created scenario-ready CSV outputs for what-if planning and procurement decisions
- Identified 5 actionable business insights with quantified impact from the data
- Structured output reports that non-technical stakeholders can act on directly

---

## 📂 Notebooks Guide

| Notebook | What it covers | Run time |
|----------|---------------|---------|
| `01_data_ingestion.ipynb` | Data generation, loading, first-look stats | ~1 min |
| `02_transformation.ipynb` | Star schema build, validation checks | ~1 min |
| `03_forecasting.ipynb` | Prophet forecasting, all 5 analytics modules | ~3 mins |
| `04_kpi_analysis.ipynb` | KPI deep dive, region/product/trend charts | ~2 mins |

Open notebooks in order. Each notebook imports from `src/` — make sure pipeline scripts have been run first.

---

## 🔮 Future Improvements

These are the natural next steps if this were a production system:

- **Cloud warehouse** — migrate from SQLite to Google BigQuery or Snowflake free tier
- **Airflow orchestration** — schedule pipeline runs with Apache Airflow DAGs
- **dbt transformation layer** — replace raw SQL with version-controlled dbt models
- **Streamlit dashboard** — add a Python-based interactive web dashboard
- **Real-time data** — integrate Kafka for streaming order data ingestion
- **ML enhancement** — add XGBoost for multi-feature demand forecasting
- **Alerting system** — automated email/Slack alerts when KPIs breach thresholds
- **Unit tests** — pytest test suite for all pipeline functions

---

## 👤 About This Project

This project was built as part of a portfolio demonstrating end-to-end data skills across three roles: **Data Engineer**, **Data Analyst**, and **Business Analyst**. It is one of three portfolio projects:

| Project | Core Skills | Domain |
|---------|------------|--------|
| Customer Churn Analysis | ML, classification, feature engineering | Telecom / Retail |
| Audit & Risk Anomaly Detection | Anomaly detection, statistical analysis | Finance / Risk |
| **Supply Chain Forecasting Platform** | **ETL, forecasting, BI dashboard** | **Operations** |

---
## Author
 **Jidnyasa Thakre**
