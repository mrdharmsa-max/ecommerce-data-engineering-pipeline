
import os
from pathlib import Path

import pandas as pd
import psycopg

# Fixed import: both Python files are inside the same src folder.
from incremental_utils import (
    file_fingerprint,
    has_file_changed,
    save_file_fingerprint,
)


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
    rows = [
        tuple(normalize_value(value) for value in row)
        for row in df[[key] + columns].itertuples(index=False, name=None)
    ]

    stats = {"inserted": 0, "updated": 0, "unchanged": 0}
    if not rows:
        return stats

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

    for row in rows:
        record_id, values = row[0], tuple(row[1:])
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


def load_data() -> None:
    stats = {
        "customers": {"inserted": 0, "updated": 0, "unchanged": 0},
        "products": {"inserted": 0, "updated": 0, "unchanged": 0},
        "orders": {"inserted": 0, "updated": 0, "unchanged": 0},
    }

    run_id = None

    # Create a run record first.
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO etl_run_log (status) VALUES ('running') RETURNING run_id"
            )
            run_id = cur.fetchone()[0]

    try:
        filenames = [
            "customers.csv",
            "products.csv",
            "orders.csv",
        ]
        fingerprints = {
            filename: file_fingerprint(DATA_DIR / filename)
            for filename in filenames
        }

        with psycopg.connect(DATABASE_URL) as conn:
            changed_files = {
                filename: has_file_changed(conn, filename, fingerprint)
                for filename, fingerprint in fingerprints.items()
            }

        if not any(changed_files.values()):
            print("No CSV files changed. Database processing skipped.")
        else:
            customers = (
                load_csv("customers.csv")
                if changed_files["customers.csv"]
                else None
            )
            products = (
                load_csv("products.csv")
                if changed_files["products.csv"]
                else None
            )
            orders = (
                load_csv("orders.csv")
                if changed_files["orders.csv"]
                else None
            )

            if orders is not None:
                orders["order_date"] = pd.to_datetime(
                    orders["order_date"], errors="raise"
                ).dt.date

            for name, df, key in [
                ("customers", customers, "customer_id"),
                ("products", products, "product_id"),
                ("orders", orders, "order_id"),
            ]:
                if df is not None:
                    if df[key].isna().any():
                        raise ValueError(f"Missing {key} in {name}.csv")
                    if df[key].duplicated().any():
                        raise ValueError(f"Duplicate {key} in {name}.csv")

            with psycopg.connect(DATABASE_URL) as conn:
                with conn.cursor() as cur:
                    if customers is not None:
                        stats["customers"] = upsert_table(
                            cur,
                            "customers",
                            "customer_id",
                            ["name", "city"],
                            customers,
                        )

                    if products is not None:
                        stats["products"] = upsert_table(
                            cur,
                            "products",
                            "product_id",
                            ["product_name", "price"],
                            products,
                        )

                    if orders is not None:
                        stats["orders"] = upsert_table(
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

            # Save fingerprints only after the data transaction succeeded.
            with psycopg.connect(DATABASE_URL) as conn:
                for filename, changed in changed_files.items():
                    if changed:
                        save_file_fingerprint(
                            conn, filename, fingerprints[filename]
                        )

        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE etl_run_log
                    SET finished_at = NOW(),
                        status = 'success',
                        customers_inserted = %s,
                        customers_updated = %s,
                        customers_unchanged = %s,
                        products_inserted = %s,
                        products_updated = %s,
                        products_unchanged = %s,
                        orders_inserted = %s,
                        orders_updated = %s,
                        orders_unchanged = %s
                    WHERE run_id = %s
                    """,
                    (
                        stats["customers"]["inserted"],
                        stats["customers"]["updated"],
                        stats["customers"]["unchanged"],
                        stats["products"]["inserted"],
                        stats["products"]["updated"],
                        stats["products"]["unchanged"],
                        stats["orders"]["inserted"],
                        stats["orders"]["updated"],
                        stats["orders"]["unchanged"],
                        run_id,
                    ),
                )

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
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE etl_run_log
                    SET finished_at = NOW(),
                        status = 'failed',
                        error_message = %s
                    WHERE run_id = %s
                    """,
                    (str(exc), run_id),
                )
        raise


if __name__ == "__main__":
    load_data()
