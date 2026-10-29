
import hashlib
from pathlib import Path

import psycopg


def file_fingerprint(path: Path) -> str:
    """Return a SHA-256 fingerprint for a file."""
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(8192), b""):
            digest.update(chunk)

    return digest.hexdigest()


def has_file_changed(conn, file_name: str, fingerprint: str) -> bool:
    """Return True if this file is new or its fingerprint changed."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT fingerprint FROM etl_file_state WHERE file_name = %s",
            (file_name,),
        )
        row = cur.fetchone()

    return row is None or row[0] != fingerprint


def save_file_fingerprint(conn, file_name: str, fingerprint: str) -> None:
    """Save the latest successfully processed fingerprint."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO etl_file_state (file_name, fingerprint, last_processed_at)
            VALUES (%s, %s, NOW())
            ON CONFLICT (file_name) DO UPDATE SET
                fingerprint = EXCLUDED.fingerprint,
                last_processed_at = NOW()
            """,
            (file_name, fingerprint),
        )
