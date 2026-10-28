
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
    path = DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")
    return pd.read_csv(path)


def normalize_value(value):
    if pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.date()
    return value


def upsert_table(cur, table, key, columns, df):
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
        record[0]: tuple(normalize_value(v) for v in record[1:])
        for record in cur.fetchall()
    }

    stats = {"inserted": 0, "updated": 0, "unchanged": 0}

    for row in rows:
        record_id = row[0]
        values = tuple(row[1:])

        if record_id not in existing:
            stats["inserted"] += 1
        elif existing[record_id] == values:
            stats["unchanged"] += 1
        else:
            stats["updated"] += 1

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
    cur.executemany(sql, rows)

    return stats


def write_run_log(conn, run_id, stats, status, error_message=None):
    """Save the ETL run outcome in a separate transaction."""
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE etl_run_log
            SET finished_at = NOW(),
                status = %s,
                customers_inserted = %s,
                customers_updated = %s,
                customers_unchanged = %s,
                products_inserted = %s,
                products_updated = %s,
                products_unchanged = %s,
                orders_inserted = %s,
                orders_updated = %s,
                orders_unchanged = %s,
                error_message = %s
            WHERE run_id = %s
            """,
            (
                status,
                stats["customers"]["inserted"],
                stats["customers"]["updated"],
                stats["customers"]["unchanged"],
                stats["products"]["inserted"],
                stats["products"]["updated"],
                stats["products"]["unchanged"],
                stats["orders"]["inserted"],
                stats["orders"]["updated"],
                stats["orders"]["unchanged"],
                error_message,
                run_id,
            ),
        )


def load_data() -> None:
    stats = {
        "customers": {"inserted": 0, "updated": 0, "unchanged": 0},
        "products": {"inserted": 0, "updated": 0, "unchanged": 0},
        "orders": {"inserted": 0, "updated": 0, "unchanged": 0},
    }

    # Create a run record first so failed runs can also be logged.
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO etl_run_log (status) VALUES ('running') RETURNING run_id"
            )
            run_id = cur.fetchone()[0]

    try:
        customers = load_csv("customers.csv")
        products = load_csv("products.csv")
        orders = load_csv("orders.csv")

        orders["order_date"] = pd.to_datetime(
            orders["order_date"], errors="raise"
        ).dt.date

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
                stats["customers"] = upsert_table(
                    cur, "customers", "customer_id",
                    ["name", "city"], customers
                )
                stats["products"] = upsert_table(
                    cur, "products", "product_id",
                    ["product_name", "price"], products
                )
                stats["orders"] = upsert_table(
                    cur, "orders", "order_id",
                    ["customer_id", "product_id", "quantity", "order_date", "status"],
                    orders
                )

        with psycopg.connect(DATABASE_URL) as conn:
            write_run_log(conn, run_id, stats, "success")

        print("ETL completed successfully.")
        for name, result in stats.items():
            print(
                f"{name.title()}: inserted={result['inserted']}, "
                f"updated={result['updated']}, "
                f"unchanged={result['unchanged']}"
            )
        print(f"ETL run ID: {run_id}")

    except Exception as exc:
        with psycopg.connect(DATABASE_URL) as conn:
            write_run_log(conn, run_id, stats, "failed", str(exc))
        raise


if __name__ == "__main__":
    load_data()
