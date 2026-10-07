"""Local audit warehouse backed by DuckDB and portable SQL evidence."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path

import duckdb


def open_warehouse(database: Path, schema_path: Path) -> duckdb.DuckDBPyConnection:
    database.parent.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect(str(database))
    connection.execute(schema_path.read_text(encoding="utf-8"))
    return connection


def register_batch(
    connection: duckdb.DuckDBPyConnection,
    source_file: Path,
    source_sha256: str,
) -> tuple[str, bool]:
    """Register idempotently; return existing batch and False for a replay."""
    existing = connection.execute(
        "SELECT batch_id FROM batch_run WHERE source_sha256 = ?", [source_sha256]
    ).fetchone()
    if existing:
        return existing[0], False
    batch_id = f"BATCH-{datetime.now(UTC):%Y%m%d}-{uuid.uuid4().hex[:8].upper()}"
    connection.execute(
        "INSERT INTO batch_run VALUES (?, ?, ?, ?, NULL, 'STARTED', NULL, NULL, NULL, NULL)",
        [batch_id, source_sha256, source_file.name, datetime.now(UTC)],
    )
    return batch_id, True


def complete_validation(connection, batch_id: str, profile: dict) -> None:
    connection.execute(
        """UPDATE batch_run SET status='VALIDATED', source_rows=?, accepted_rows=?, rejected_rows=?
           WHERE batch_id=?""",
        [profile["source_rows"], profile["accepted_rows"], profile["rejected_rows"], batch_id],
    )


def export_dashboard_tables(connection, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for table in ("batch_run", "migration_audit", "control_result", "defect_log"):
        connection.execute(
            f"COPY (SELECT * FROM {table}) TO ? (FORMAT PARQUET, OVERWRITE_OR_IGNORE TRUE)",
            [str(output_dir / f"{table}.parquet")],
        )


def batch_summary(connection, batch_id: str) -> dict:
    row = connection.execute(
        """SELECT batch_id, status, source_rows, accepted_rows, rejected_rows
           FROM batch_run WHERE batch_id=?""", [batch_id]
    ).fetchone()
    if not row:
        raise KeyError(batch_id)
    return dict(zip(("batch_id", "status", "source_rows", "accepted_rows", "rejected_rows"), row))


def write_summary(connection, batch_id: str, output: Path) -> None:
    output.write_text(json.dumps(batch_summary(connection, batch_id), indent=2, default=str), encoding="utf-8")

