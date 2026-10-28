
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "ecommerce.db"

def test_pipeline_runs_successfully():
    result = subprocess.run(
        [sys.executable, str(ROOT / "src" / "pipeline.py")],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert result.returncode == 0, result.stdout + result.stderr

def test_warehouse_has_seven_unique_orders():
    with sqlite3.connect(DB) as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM fact_orders"
        ).fetchone()[0]
        unique_count = conn.execute(
            "SELECT COUNT(DISTINCT order_id) FROM fact_orders"
        ).fetchone()[0]

    assert count == 7
    assert unique_count == 7

def test_no_invalid_order_values():
    with sqlite3.connect(DB) as conn:
        invalid = conn.execute("""
            SELECT COUNT(*) FROM fact_orders
            WHERE quantity <= 0 OR revenue < 0
        """).fetchone()[0]

    assert invalid == 0
