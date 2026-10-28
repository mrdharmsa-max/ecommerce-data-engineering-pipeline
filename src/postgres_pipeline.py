
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


def normalize_value(value):
    """Normalize pandas and PostgreSQL values for reliable comparison."""
    if pd.isna(value):
        return None

    if isinstance(value, pd.Timestamp):
        return value.date()

    return value


def upsert_table(cur, table, key, columns, df):
    """Insert new rows, update changed rows, and count unchanged rows."""
    selected = df[[key] + columns]
    rows = [
        tuple(normalize_value(value) for value in row)
        for row in selected.itertuples(index=False, name=None)
    ]

    if not rows:
        return {"inserted": 0, "updated": 0, "unchanged": 0}

    ids = [row[0] for row in rows]

    cur.execute(
        f"SELECT {', '.join([key] + columns)} "
        f"FROM {table} WHERE {key} = ANY(%s)",
        (ids,),
    )

    existing = {
        record[0]: tuple(normalize_value(value) for value in record[1:])
        for record in cur.fetchall()
    }

    inserted = 0
    updated = 0
    unchanged = 0

    placeholders = ", ".join(["%s"] * (len(columns) + 1))
    assignments = ", ".join(
        f"{column} = EXCLUDED.{column}" for column in columns
    )

    update_condition = " OR ".join(
        f"{table}.{column} IS DISTINCT FROM EXCLUDED.{column}"
        for column in columns
    )

    sql = f"""
        INSERT INTO {table} ({key}, {', '.join(columns)})
        VALUES ({placeholders})
        ON CONFLICT ({key}) DO UPDATE SET
            {assignments}
        WHERE {update_condition}
    """

    for row in rows:
        record_id = row[0]
        new_values = tuple(row[1:])

        if record_id not in existing:
            inserted += 1
        elif existing[record_id] == new_values:
            unchanged += 1
        else:
            updated += 1

    cur.executemany(sql, rows)

    return {
        "inserted": inserted,
        "updated": updated,
        "unchanged": unchanged,
    }


def load_data() -> None:
    """Load CSV data into PostgreSQL and report row changes."""
    customers = load_csv("customers.csv")
    products = load_csv("products.csv")
    orders = load_csv("orders.csv")

    # Convert CSV dates to Python date objects.
    orders["order_date"] = pd.to_datetime(
        orders["order_date"], errors="raise"
    ).dt.date

    # Reject duplicate primary keys before writing to the database.
    for name, df, key in [
        ("customers", customers, "customer_id"),
        ("products", products, "product_id"),
        ("orders", orders, "order_id"),
    ]:
        if df[key].isna().any():
            raise ValueError(f"Missing {key} found in {name}.csv")

        if df[key].duplicated().any():
            raise ValueError(f"Duplicate {key} found in {name}.csv")

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            customer_stats = upsert_table(
                cur,
                "customers",
                "customer_id",
                ["name", "city"],
                customers,
            )

            product_stats = upsert_table(
                cur,
                "products",
                "product_id",
                ["product_name", "price"],
                products,
            )

            order_stats = upsert_table(
                cur,
                "orders",
                "order_id",
                [
                    "customer_id",
                    "product_id",
                    "quantity",
                    "order_date",
                    "status",
                ],
                orders,
            )

    print("ETL completed successfully.")

    for name, stats in [
        ("Customers", customer_stats),
        ("Products", product_stats),
        ("Orders", order_stats),
    ]:
        print(
            f"{name}: inserted={stats['inserted']}, "
            f"updated={stats['updated']}, "
            f"unchanged={stats['unchanged']}"
        )


if __name__ == "__main__":
    load_data()
