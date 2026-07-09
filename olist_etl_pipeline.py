#!/usr/bin/env python
# coding: utf-8


import sys
get_ipython().system('{sys.executable} -m pip install psycopg2-binary --only-binary :all:')

import pandas as pd
import psycopg2
from sqlalchemy import create_engine

# File path
path = "data/"

# EXTRACT — Load all 5 CSV files
orders_df = pd.read_csv(path + 'olist_orders_dataset.csv')
order_items_df = pd.read_csv(path + 'olist_order_items_dataset.csv')
customers_df = pd.read_csv(path + 'olist_customers_dataset.csv')
payments_df = pd.read_csv(path + 'olist_order_payments_dataset.csv')
products_df = pd.read_csv(path + 'olist_products_dataset.csv')

print("Files loaded successfully!")
print(f"Orders: {orders_df.shape}")
print(f"Order Items: {order_items_df.shape}")
print(f"Customers: {customers_df.shape}")
print(f"Payments: {payments_df.shape}")
print(f"Products: {products_df.shape}")


# Quick exploration of each DataFrame
print("=== ORDERS ===")
print(orders_df.head(3))
print(orders_df.dtypes)
print(orders_df.isnull().sum())



print("=== ORDER ITEMS ===")
print(order_items_df.head(3))
print(order_items_df.dtypes)
print(order_items_df.isnull().sum())
print("\n=== CUSTOMERS ===")
print(customers_df.head(3))
print(customers_df.dtypes)
print(customers_df.isnull().sum())
print("\n=== PAYMENTS ===")
print(payments_df.head(3))
print(payments_df.dtypes)
print(payments_df.isnull().sum())
print("\n=== PRODUCTS ===")
print(products_df.head(3))
print(products_df.dtypes)
print(products_df.isnull().sum())



# TRANSFORM — Step 1: Fix Orders table

# Convert date columns from string to datetime
date_columns = [
    'order_purchase_timestamp',
    'order_approved_at',
    'order_delivered_carrier_date',
    'order_delivered_customer_date',
    'order_estimated_delivery_date'
]

for col in date_columns:
    orders_df[col] = pd.to_datetime(orders_df[col])

# Calculate delivery time in days
orders_df['delivery_time_days'] = (
    orders_df['order_delivered_customer_date'] -
    orders_df['order_purchase_timestamp']
).dt.days

# Check results
print("Date types fixed:")
print(orders_df[date_columns].dtypes)
print(f"\nDelivery time sample:")
print(orders_df[['order_id', 'order_status', 'delivery_time_days']].head())
print(f"\nNull delivery times: {orders_df['delivery_time_days'].isnull().sum()}")



# TRANSFORM — Step 2: Fix Order Items
order_items_df['shipping_limit_date'] = pd.to_datetime(
    order_items_df['shipping_limit_date']
)

# Add total item value column
order_items_df['total_item_value'] = (
    order_items_df['price'] + order_items_df['freight_value']
)

print("Order Items fixed:")
print(order_items_df[['order_id', 'price', 'freight_value', 'total_item_value']].head(3))

# TRANSFORM — Step 3: Fix Products
# Fill missing category with 'unknown'
products_df['product_category_name'] = products_df[
    'product_category_name'
].fillna('unknown')

# Fill missing dimensions with median
for col in ['product_weight_g', 'product_length_cm',
            'product_height_cm', 'product_width_cm']:
    products_df[col] = products_df[col].fillna(products_df[col].median())

# Keep only columns needed for analysis
products_clean = products_df[['product_id', 'product_category_name']]

print("\nProducts fixed:")
print(products_clean.head(3))
print(f"Null categories remaining: {products_clean['product_category_name'].isnull().sum()}")

# TRANSFORM — Step 4: Customers and Payments are already clean
print("\nCustomers shape:", customers_df.shape)
print("Payments shape:", payments_df.shape)
print("\nAll tables cleaned successfully!")



# TRANSFORM — Step 5: Merge all 5 tables

# Step 1: orders + customers (on customer_id)
df = orders_df.merge(
    customers_df[['customer_id', 'customer_state', 'customer_city']],
    on='customer_id',
    how='left'
)
print(f"After orders + customers: {df.shape}")

# Step 2: + order_items (on order_id)
df = df.merge(
    order_items_df[['order_id', 'product_id', 'price',
                    'freight_value', 'total_item_value']],
    on='order_id',
    how='left'
)
print(f"After + order_items: {df.shape}")

# Step 3: + products (on product_id)
df = df.merge(
    products_clean,
    on='product_id',
    how='left'
)
print(f"After + products: {df.shape}")

# Step 4: + payments (on order_id)
payments_summary = payments_df.groupby('order_id').agg(
    total_payment=('payment_value', 'sum'),
    payment_type=('payment_type', 'first')
).reset_index()

df = df.merge(
    payments_summary,
    on='order_id',
    how='left'
)
print(f"After + payments: {df.shape}")
print(f"\nFinal merged DataFrame columns:")
print(df.columns.tolist())



df_delivered = df[df['order_status'] == 'delivered']


print(f"Total rows: {df.shape[0]}")
print(f"Delivered rows: {df_delivered.shape[0]}")
print(f"Filtered out: {df.shape[0] - df_delivered.shape[0]} rows")
print(f"\nOrder status values remaining:")
print(df_delivered['order_status'].value_counts())



final_df = df_delivered[['order_id', 'order_status',
                          'order_purchase_timestamp',
                          'order_delivered_customer_date',
                          'delivery_time_days', 'customer_state',
                          'product_category_name', 'total_item_value',
                          'total_payment', 'payment_type']].copy()
print(f"Final DataFrame shape: {final_df.shape}")
print(f"\nColumns: {final_df.columns.tolist()}")
print(f"\nSample data:")
print(final_df.head(3))
print(f"\nNull values:")
print(final_df.isnull().sum())


final_df['delivery_time_days'] = final_df['delivery_time_days'].fillna(final_df['delivery_time_days'].median())
final_df['total_payment'] = final_df['total_payment'].fillna(0)
final_df['payment_type'] = final_df['payment_type'].fillna('unknown')

# Verify
print(final_df.isnull().sum())

print(final_df.isnull().sum())
print(f"\nShape: {final_df.shape}")


final_df = final_df.dropna(subset=['order_delivered_customer_date'])


print(final_df.isnull().sum())

print(final_df.isnull().sum())
print(f"\nShape: {final_df.shape}")

# Replace the dummy credentials below with your own PostgreSQL credentials

engine = create_engine(
    "postgresql+psycopg2://your_username:your_password@localhost:5432/your_database"
)

final_df.to_sql('olist_orders', engine, if_exists='replace', index=False)

print("Data loaded successfully!")


query = """
SELECT customer_state, avg(delivery_time_days) as avg_delivery_time
FROM olist_orders
GROUP BY customer_state
ORDER BY avg_delivery_time desc 
"""
result = pd.read_sql(query, engine)
print(result)


query = """ 
SELECT product_category_name, sum(total_payment) as total_revenue 
FROM olist_orders  
GROUP BY product_category_name 
ORDER BY total_revenue desc 
""" 
result = pd.read_sql(query, engine) 
print(result)


query = """ 
SELECT DATE_TRUNC('month', order_purchase_timestamp) AS order_month, COUNT(*) AS total_orders 
FROM olist_orders 
GROUP BY order_month ORDER BY order_month asc
""" 
result = pd.read_sql(query, engine) 
print(result)

engine.dispose()
print("Database connection closed.")







