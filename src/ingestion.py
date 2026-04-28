import pandas as pd
import numpy as np
import sqlite3
import os
from datetime import datetime, timedelta

# ── Seed for reproducibility ──────────────────────────────────────────────────
np.random.seed(42)

def generate_orders(n=2000):
    """Generate synthetic supply chain orders data."""
    
    products = ['Laptop', 'Phone', 'Tablet', 'Monitor', 'Keyboard',
                'Mouse', 'Headphones', 'Camera', 'Printer', 'Speaker']
    
    suppliers = ['TechCorp India', 'GlobalParts Ltd', 'FastSupply Co',
                 'ReliableGoods', 'QuickShip Asia']
    
    regions = ['North', 'South', 'East', 'West', 'Central']
    
    start_date = datetime(2022, 1, 1)
    
    data = {
        'order_id':        [f'ORD-{str(i).zfill(5)}' for i in range(1, n+1)],
        'order_date':      [start_date + timedelta(days=np.random.randint(0, 730))
                            for _ in range(n)],
        'product_name':    np.random.choice(products, n),
        'supplier_name':   np.random.choice(suppliers, n),
        'region':          np.random.choice(regions, n),
        'quantity_ordered':np.random.randint(10, 500, n),
        'unit_cost':       np.round(np.random.uniform(50, 2000, n), 2),
        'lead_time_days':  np.random.randint(3, 45, n),
        'actual_delivery': None,   # filled below
        'is_delayed':      None,
        'warehouse_stock': np.random.randint(0, 1000, n),
    }
    
    df = pd.DataFrame(data)
    
    # Calculate total cost
    df['total_cost'] = df['quantity_ordered'] * df['unit_cost']
    
    # Simulate actual delivery (some orders delayed)
    delay_chance = np.random.random(n)
    df['delay_days'] = np.where(delay_chance > 0.75,
                                np.random.randint(1, 15, n), 0)
    df['actual_delivery_days'] = df['lead_time_days'] + df['delay_days']
    df['is_delayed'] = df['delay_days'] > 0
    
    # Sort by order date
    df = df.sort_values('order_date').reset_index(drop=True)
    
    return df


def generate_inventory(df_orders):
    """Generate inventory snapshot per product."""
    
    inventory = df_orders.groupby('product_name').agg(
        avg_stock      = ('warehouse_stock', 'mean'),
        total_ordered  = ('quantity_ordered', 'sum'),
        total_cost     = ('total_cost', 'sum'),
        avg_lead_time  = ('lead_time_days', 'mean'),
    ).reset_index()
    
    inventory['reorder_point'] = (
        inventory['avg_lead_time'] * (inventory['total_ordered'] / 730)
    ).round(0)
    
    inventory['stock_status'] = np.where(
        inventory['avg_stock'] < inventory['reorder_point'],
        'Low Stock', 'Adequate'
    )
    
    return inventory


def save_to_csv(df, filename):
    """Save dataframe to data/raw/ folder."""
    os.makedirs('data/raw', exist_ok=True)
    path = f'data/raw/{filename}'
    df.to_csv(path, index=False)
    print(f'Saved {len(df)} rows to {path}')
    return path


def load_to_sqlite(df, table_name, db_path='data/supply_chain.db'):
    """Load dataframe into SQLite database."""
    conn = sqlite3.connect(db_path)
    df.to_sql(table_name, conn, if_exists='replace', index=False)
    conn.close()
    print(f'Loaded {len(df)} rows into table: {table_name}')


# ── Run everything ────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print('Generating supply chain data...')
    
    df_orders    = generate_orders(2000)
    df_inventory = generate_inventory(df_orders)
    
    # Save to CSV
    save_to_csv(df_orders,    'orders.csv')
    save_to_csv(df_inventory, 'inventory.csv')
    
    # Load to SQLite (your local data warehouse)
    load_to_sqlite(df_orders,    'raw_orders')
    load_to_sqlite(df_inventory, 'raw_inventory')
    
    print('\nData sample:')
    print(df_orders.head(3).to_string())
    print(f'\nTotal orders: {len(df_orders)}')
    print(f'Total value:  ₹{df_orders["total_cost"].sum():,.0f}')
    print(f'Delayed orders: {df_orders["is_delayed"].sum()} '
          f'({df_orders["is_delayed"].mean()*100:.1f}%)')