
from pathlib import Path
import logging
import sqlite3
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DB = ROOT / "ecommerce.db"

logging.basicConfig(
    filename=ROOT / "pipeline.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

def run_pipeline():
    logging.info("Pipeline started")

    # 1. EXTRACT
    customers = pd.read_csv(DATA / "customers.csv")
    products = pd.read_csv(DATA / "products.csv")
    orders = pd.read_csv(DATA / "orders.csv")

    raw_count = len(orders)

    # 2. TRANSFORM: remove duplicate IDs
    duplicate_count = int(orders.duplicated("order_id").sum())
    orders = orders.drop_duplicates("order_id", keep="first").copy()

    # Validate required values
    orders["quantity"] = pd.to_numeric(
        orders["quantity"], errors="coerce"
    )
    orders["order_date"] = pd.to_datetime(
        orders["order_date"], errors="coerce"
    )

    orders = orders.dropna(
        subset=[
            "order_id", "customer_id", "product_id",
            "quantity", "order_date", "status"
        ]
    )
    orders = orders[orders["quantity"] > 0].copy()

    # Join customers and products
    enriched = orders.merge(
        customers, on="customer_id", how="left",
        validate="many_to_one"
    )
    enriched = enriched.merge(
        products, on="product_id", how="left",
        validate="many_to_one"
    )

    rejected = enriched[
        enriched["name"].isna()
        | enriched["product_name"].isna()
    ].copy()

    valid = enriched[
        enriched["name"].notna()
        & enriched["product_name"].notna()
    ].copy()

    valid["revenue"] = valid["quantity"] * valid["price"]
    valid["order_date"] = valid["order_date"].dt.strftime("%Y-%m-%d")

    # 3. LOAD into SQLite Data Warehouse
    with sqlite3.connect(DB) as conn:
        conn.execute("PRAGMA foreign_keys = ON")

        conn.executescript("""
            CREATE TABLE IF NOT EXISTS dim_customer (
                customer_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                city TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS dim_product (
                product_id INTEGER PRIMARY KEY,
                product_name TEXT NOT NULL,
                price REAL NOT NULL CHECK(price >= 0)
            );

            CREATE TABLE IF NOT EXISTS fact_orders (
                order_id INTEGER PRIMARY KEY,
                customer_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                order_date TEXT NOT NULL,
                quantity INTEGER NOT NULL CHECK(quantity > 0),
                status TEXT NOT NULL,
                revenue REAL NOT NULL,
                FOREIGN KEY(customer_id)
                    REFERENCES dim_customer(customer_id),
                FOREIGN KEY(product_id)
                    REFERENCES dim_product(product_id)
            );

            CREATE TABLE IF NOT EXISTS rejected_orders (
                order_id INTEGER,
                reason TEXT
            );
        """)

        # Load dimensions using upserts
        for _, row in customers.drop_duplicates("customer_id").iterrows():
            conn.execute("""
                INSERT INTO dim_customer (customer_id, name, city)
                VALUES (?, ?, ?)
                ON CONFLICT(customer_id) DO UPDATE SET
                    name = excluded.name,
                    city = excluded.city
            """, (
                int(row["customer_id"]), row["name"], row["city"]
            ))

        for _, row in products.drop_duplicates("product_id").iterrows():
            conn.execute("""
                INSERT INTO dim_product
                    (product_id, product_name, price)
                VALUES (?, ?, ?)
                ON CONFLICT(product_id) DO UPDATE SET
                    product_name = excluded.product_name,
                    price = excluded.price
            """, (
                int(row["product_id"]),
                row["product_name"],
                float(row["price"])
            ))

        # Upsert fact records; reruns won't create duplicates
        for _, row in valid.iterrows():
            conn.execute("""
                INSERT INTO fact_orders
                    (order_id, customer_id, product_id,
                     order_date, quantity, status, revenue)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(order_id) DO UPDATE SET
                    customer_id = excluded.customer_id,
                    product_id = excluded.product_id,
                    order_date = excluded.order_date,
                    quantity = excluded.quantity,
                    status = excluded.status,
                    revenue = excluded.revenue
            """, (
                int(row["order_id"]),
                int(row["customer_id"]),
                int(row["product_id"]),
                row["order_date"],
                int(row["quantity"]),
                row["status"],
                float(row["revenue"])
            ))

        conn.execute("DELETE FROM rejected_orders")
        for _, row in rejected.iterrows():
            conn.execute(
                "INSERT INTO rejected_orders (order_id, reason) VALUES (?, ?)",
                (int(row["order_id"]), "Missing customer/product")
            )

        # 4. DATA QUALITY CHECKS
        total = conn.execute(
            "SELECT COUNT(*) FROM fact_orders"
        ).fetchone()[0]

        duplicates = conn.execute("""
            SELECT COUNT(*) FROM (
                SELECT order_id FROM fact_orders
                GROUP BY order_id HAVING COUNT(*) > 1
            )
        """).fetchone()[0]

        invalid = conn.execute("""
            SELECT COUNT(*) FROM fact_orders
            WHERE quantity <= 0 OR revenue < 0
        """).fetchone()[0]

        assert duplicates == 0, "Duplicate orders detected"
        assert invalid == 0, "Invalid warehouse records detected"

    logging.info("Pipeline completed successfully")
    print("ETL pipeline completed successfully!")
    print(f"Raw order rows: {raw_count}")
    print(f"Duplicate rows removed: {duplicate_count}")
    print(f"Rejected records: {len(rejected)}")
    print(f"Orders in warehouse: {total}")
    print(f"Database saved at: {DB}")

if __name__ == "__main__":
    try:
        run_pipeline()
    except Exception:
        logging.exception("Pipeline failed")
        raise
