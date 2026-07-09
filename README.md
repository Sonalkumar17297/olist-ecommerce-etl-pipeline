# olist-ecommerce-etl-pipeline
Brazilian E-Commerce ETL Pipeline | Python, Pandas, PostgreSQL, SQL - Processed 110,000+ real e-commerce orders across 5 related datasets   (448,369 total rows) — handling date conversion, null treatment,   multi-table joins, and payment pre-aggregation before loading into PostgreSQL.
# 🛒 Brazilian E-Commerce ETL Pipeline
### Large-Scale Data Engineering Pipeline | Python · Pandas · PostgreSQL · SQL

> Processes **110,000+ real e-commerce orders** across 5 related datasets — demonstrating production-grade ETL with genuine data quality challenges, multi-table transformations, and actionable business insights.

---

## 📊 Project Overview

This project builds a complete, end-to-end data pipeline using the [Olist Brazilian E-Commerce Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) — a real-world dataset containing 100,000+ orders from a Brazilian marketplace between 2016 and 2018.

The pipeline mirrors what a Data Engineer does in production:
- Extract raw data from multiple source files
- Transform and clean messy, real-world data
- Load into a production-grade relational database
- Analyze using SQL to surface actionable business insights

---

## 🏗️ Pipeline Architecture

```
[5 Raw CSV Files]          [Transform Layer]           [Load Layer]        [Analyze Layer]
─────────────────          ─────────────────           ────────────        ──────────────
orders.csv        ──┐
order_items.csv   ──┤
customers.csv     ──┼──→  Python + Pandas  ──→  PostgreSQL (olist_db)  ──→  SQL Queries
products.csv      ──┤      Clean · Merge         olist_orders table          Business KPIs
order_payments.csv──┘      Validate · Transform   110,189 clean rows
```

---

## 📁 Dataset

| File | Rows | Description |
|------|------|-------------|
| `olist_orders_dataset.csv` | 99,441 | Core orders with timestamps and status |
| `olist_order_items_dataset.csv` | 112,650 | Products within each order |
| `olist_customers_dataset.csv` | 99,441 | Customer location data |
| `olist_order_payments_dataset.csv` | 103,886 | Payment method and values |
| `olist_products_dataset.csv` | 32,951 | Product catalog with categories |

**Total raw records processed: 448,369**

---

## ⚙️ Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.8 | Core scripting language |
| Pandas | Data cleaning, transformation, multi-table merging |
| SQLAlchemy | Python-to-PostgreSQL ORM bridge |
| psycopg2 | PostgreSQL database driver |
| PostgreSQL 16 | Production-grade relational database |
| SQL | Business analysis queries |

---

## 🔧 Key Data Engineering Challenges Solved

### 1. Date Type Conversion
All 5 timestamp columns were stored as raw strings (`object` type) — unusable for any date-based calculation.

```python
date_columns = [
    'order_purchase_timestamp',
    'order_approved_at',
    'order_delivered_carrier_date',
    'order_delivered_customer_date',
    'order_estimated_delivery_date'
]
for col in date_columns:
    orders_df[col] = pd.to_datetime(orders_df[col])
```

### 2. Delivery Time Calculation
Calculated actual delivery duration as a new engineered feature:

```python
orders_df['delivery_time_days'] = (
    orders_df['order_delivered_customer_date'] -
    orders_df['order_purchase_timestamp']
).dt.days
```

### 3. Multi-Table Join (5 Tables)
Merged 5 related datasets on foreign key relationships — mirroring production database join patterns:

```
customers → orders → order_items → products
                  ↘ payments
```

### 4. Payment Aggregation Before Merge
Orders with multiple payment methods (e.g., credit card + voucher) required pre-aggregation to avoid row duplication:

```python
payments_summary = payments_df.groupby('order_id').agg(
    total_payment=('payment_value', 'sum'),
    payment_type=('payment_type', 'first')
).reset_index()
```

### 5. Null Handling Strategy
Applied different strategies based on column context:

| Column | Nulls | Strategy | Reason |
|--------|-------|----------|--------|
| `delivery_time_days` | 8 | Median fill | Preserve row for analysis |
| `total_payment` | 3 | Fill with 0 | No payment = zero value |
| `payment_type` | 3 | Fill 'unknown' | Categorical placeholder |
| `order_delivered_customer_date` | 8 | Drop rows | Can't analyze without delivery date |
| `product_category_name` | 610 | Fill 'unknown' | Keep product rows intact |

### 6. SettingWithCopyWarning Fix
Used `.copy()` when creating derived DataFrames to ensure modifications apply to an independent copy, not a view:

```python
final_df = df_delivered[[...columns...]].copy()
```

---

## 📈 Business Insights Discovered

### 1. Delivery Time by State
```sql
SELECT customer_state,
       AVG(delivery_time_days) AS avg_delivery_time
FROM olist_orders
GROUP BY customer_state
ORDER BY avg_delivery_time DESC;
```

**Key Finding:** Remote Amazon states (RR, AP, AM) average **27+ days** delivery vs São Paulo's **8.3 days** — a 3x gap revealing a clear logistics opportunity for northern Brazil warehouse investment.

| State | Avg Delivery (days) |
|-------|---------------------|
| RR (Roraima) | 27.8 |
| AP (Amapá) | 27.8 |
| AM (Amazonas) | 26.0 |
| SP (São Paulo) | 8.3 |

---

### 2. Revenue by Product Category
```sql
SELECT product_category_name,
       SUM(total_payment) AS total_revenue
FROM olist_orders
GROUP BY product_category_name
ORDER BY total_revenue DESC;
```

**Key Finding:** Home goods (`cama_mesa_banho` — bed/bath) leads at **R$1.69M**, while physical media (`cds_dvds_musicais`) generates just **R$1.2K** — reflecting the global streaming-driven decline of physical media.

---

### 3. Monthly Order Growth (2016–2018)
```sql
SELECT DATE_TRUNC('month', order_purchase_timestamp) AS order_month,
       COUNT(*) AS total_orders
FROM olist_orders
GROUP BY order_month
ORDER BY order_month ASC;
```

**Key Finding:** Olist grew from **3 orders** (Sep 2016) to **8,474 orders** (Nov 2017 — Black Friday spike) — a **2,600x growth** in 14 months, stabilizing at ~7,500 orders/month through 2018.

---

## 🚀 How to Run This Project

### Prerequisites
```bash
pip install pandas sqlalchemy psycopg2-binary
```

### PostgreSQL Setup
1. Install PostgreSQL 16
2. Create a database called `olist_db`
3. Update connection string with your credentials

### Run the Pipeline
```bash
python olist_etl_pipeline.py
```

### Connection Configuration
```python
engine = create_engine(
    'postgresql+psycopg2://username:password@localhost:5432/olist_db'
)
```

---

## 📂 Project Structure

```
olist-ecommerce-etl-pipeline/
├── olist_etl_pipeline.py     # Main pipeline script (Extract → Transform → Load → Analyze)
├── README.md                  # Project documentation
└── data/                      # Raw CSV files (not committed — download from Kaggle)
    ├── olist_orders_dataset.csv
    ├── olist_order_items_dataset.csv
    ├── olist_customers_dataset.csv
    ├── olist_order_payments_dataset.csv
    └── olist_products_dataset.csv
```

---

## 🔍 Data Quality Summary

| Stage | Records In | Records Out | Removed | Reason |
|-------|-----------|-------------|---------|--------|
| Raw load | 448,369 | 448,369 | 0 | — |
| After merge | — | 113,425 | — | Orders × Items (expected expansion) |
| After status filter | 113,425 | 110,197 | 3,228 | Non-delivered orders removed |
| After null drop | 110,197 | 110,189 | 8 | Missing delivery dates |
| **Final clean dataset** | — | **110,189** | — | **Ready for analysis** |

---

## 🔮 Future Improvements

- Add incremental loading (only process new orders since last run)
- Migrate raw data layer to AWS S3 / Google Cloud Storage
- Schedule pipeline with Apache Airflow for daily runs
- Add data validation tests using Great Expectations
- Build interactive dashboard with Tableau/Power BI on top of PostgreSQL

---

## 💡 Key Learnings

- Real-world data is never clean — 5 different null-handling strategies were needed across just 5 tables
- Pre-aggregating before joining is critical when one-to-many relationships exist (payments to orders)
- `DATE_TRUNC()` in PostgreSQL is essential for time-series grouping — truncates timestamps to month/year boundaries for accurate period-based analysis
- Row count expansion after joining is expected and intentional when the right side of a JOIN has multiple rows per key

---

## 👤 Author

Built as a portfolio project demonstrating end-to-end data engineering skills:
multi-source extraction, production-grade transformation, PostgreSQL loading,
and SQL-based business analysis on a real 100,000+ row dataset.

**🔗 Connect:** [LinkedIn]([https://www.linkedin.com/in/sonal-kumar-datascience/]) | [GitHub](https://github.com/Sonalkumar17297/olist-ecommerce-etl-pipeline)
