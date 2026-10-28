
from pathlib import Path
import pandas as pd

# Project data directory
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

# Customers dataset
customers = pd.DataFrame([
    {"customer_id": 1, "name": "Aman", "city": "Jaipur"},
    {"customer_id": 2, "name": "Priya", "city": "Delhi"},
    {"customer_id": 3, "name": "Rahul", "city": "Mumbai"},
    {"customer_id": 4, "name": "Neha", "city": "Sikar"},
    {"customer_id": 5, "name": "Karan", "city": "Jaipur"},
])

# Products dataset
products = pd.DataFrame([
    {"product_id": 101, "product_name": "Laptop", "price": 55000},
    {"product_id": 102, "product_name": "Headphones", "price": 2000},
    {"product_id": 103, "product_name": "Keyboard", "price": 1500},
    {"product_id": 104, "product_name": "Mouse", "price": 800},
])

# Orders dataset (includes one duplicate for testing)
orders = pd.DataFrame([
    {"order_id": 1001, "customer_id": 1, "product_id": 101,
     "quantity": 1, "order_date": "2026-10-25", "status": "delivered"},
    {"order_id": 1002, "customer_id": 2, "product_id": 102,
     "quantity": 2, "order_date": "2026-10-25", "status": "delivered"},
    {"order_id": 1003, "customer_id": 1, "product_id": 103,
     "quantity": 1, "order_date": "2026-10-26", "status": "shipped"},
    {"order_id": 1004, "customer_id": 3, "product_id": 104,
     "quantity": 3, "order_date": "2026-10-26", "status": "cancelled"},
    {"order_id": 1005, "customer_id": 4, "product_id": 102,
     "quantity": 1, "order_date": "2026-10-27", "status": "delivered"},
    {"order_id": 1006, "customer_id": 5, "product_id": 101,
     "quantity": 1, "order_date": "2026-10-27", "status": "shipped"},
    {"order_id": 1007, "customer_id": 2, "product_id": 104,
     "quantity": 2, "order_date": "2026-10-27", "status": "delivered"},
    {"order_id": 1007, "customer_id": 2, "product_id": 104,
     "quantity": 2, "order_date": "2026-10-27", "status": "delivered"},
])

customers.to_csv(DATA_DIR / "customers.csv", index=False)
products.to_csv(DATA_DIR / "products.csv", index=False)
orders.to_csv(DATA_DIR / "orders.csv", index=False)

print("Dataset generated successfully!")
print(f"Customers: {len(customers)}")
print(f"Products: {len(products)}")
print(f"Orders including duplicate: {len(orders)}")
print(f"Files saved in: {DATA_DIR}")
