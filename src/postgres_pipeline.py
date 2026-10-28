
import os
from pathlib import Path

import pandas as pd
import psycopg


ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://ecommerce_user:ecommerce_dev_password@localhost:5432/ecommerce",
)


def load_csv(filename: str) -> pd.DataFrame:
    """Read a CSV file from the project's data directory."""
    path = DATA_DIR / filename

    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    return pd.read_csv(path)


def load_data() -> None:
    """Load customers, products, and orders into PostgreSQL."""
    customers = load_csv("customers.csv")
    products = load_csv("products.csv")
    orders = load_csv("orders.csv")

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            # Load parent tables first because orders has foreign keys.
            cur.executemany(
                """
                INSERT INTO customers (customer_id, name, city)
                VALUES (%s, %s, %s)
                ON CONFLICT (customer_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    city = EXCLUDED.city
                """,
                customers[["customer_id", "name", "city"]].itertuples(
                    index=False, name=None
                ),
            )

            cur.executemany(
                """
                INSERT INTO products (product_id, product_name, price)
                VALUES (%s, %s, %s)
                ON CONFLICT (product_id) DO UPDATE SET
                    product_name = EXCLUDED.product_name,
                    price = EXCLUDED.price
                """,
                products[["product_id", "product_name", "price"]].itertuples(
                    index=False, name=None
                ),
            )

            cur.executemany(
                """
                INSERT INTO orders
                    (order_id, customer_id, product_id, quantity, order_date, status)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (order_id) DO UPDATE SET
                    customer_id = EXCLUDED.customer_id,
                    product_id = EXCLUDED.product_id,
                    quantity = EXCLUDED.quantity,
                    order_date = EXCLUDED.order_date,
                    status = EXCLUDED.status
                """,
                orders[
                    [
                        "order_id",
                        "customer_id",
                        "product_id",
                        "quantity",
                        "order_date",
                        "status",
                    ]
                ].itertuples(index=False, name=None),
            )

        # The transaction commits when the connection context exits successfully.

    print("ETL completed successfully.")
    print(f"Customers read: {len(customers)}")
    print(f"Products read: {len(products)}")
    print(f"Orders read: {len(orders)}")


if __name__ == "__main__":
    load_data()
