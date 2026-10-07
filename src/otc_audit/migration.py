"""Resumable ERPNext migration with a document-level audit trail."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import duckdb
import pandas as pd

from .erpnext import (
    ERPNextClient,
    MigrationConfig,
    customer_payload,
    document_groups,
    invoice_payload,
    item_payload,
    payload_hash,
    safe_key,
)


def _record(
    connection: duckdb.DuckDBPyConnection,
    batch_id: str,
    source_no: str,
    doctype: str,
    digest: str,
    status: str,
    erp_name: str | None,
    response: str,
) -> None:
    connection.execute(
        """INSERT OR REPLACE INTO migration_audit
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [batch_id, source_no, "RETURN" if source_no.startswith("C") else "SALE", doctype,
         erp_name, digest, status, None, datetime.now(UTC), response[:1000]],
    )


def migrate_masters(client: ERPNextClient, accepted: pd.DataFrame, config: MigrationConfig) -> dict:
    customer_rows = accepted.sort_values("invoice_date").drop_duplicates("customer_id")
    item_rows = accepted.sort_values("invoice_date").drop_duplicates("stock_code")
    counts = {"customers_created": 0, "items_created": 0}
    for row in customer_rows.itertuples(index=False):
        name = safe_key("UCI-CUST-", row.customer_id)
        _, created = client.ensure_named("Customer", name, customer_payload(row.customer_id, row.country, config))
        counts["customers_created"] += int(created)
    for row in item_rows.itertuples(index=False):
        name = safe_key("UCI-ITEM-", row.stock_code)
        _, created = client.ensure_named("Item", name, item_payload(row.stock_code, row.description, config))
        counts["items_created"] += int(created)
    return counts


def migrate_invoices(
    client: ERPNextClient,
    connection: duckdb.DuckDBPyConnection,
    accepted: pd.DataFrame,
    config: MigrationConfig,
    batch_id: str,
    limit: int | None = None,
) -> dict[str, int]:
    summary = {"created": 0, "submitted": 0, "skipped": 0, "failed": 0}
    originals: dict[str, str] = {}
    for sequence, (source_no, lines) in enumerate(document_groups(accepted), start=1):
        if limit is not None and sequence > limit:
            break
        is_return = lines.iloc[0]["document_type"] == "RETURN"
        original_source = str(lines.iloc[0]["original_invoice_no"]) if is_return else None
        return_against = originals.get(original_source) if original_source else None
        if is_return and not return_against:
            found_original = client.find_one("Sales Invoice", "custom_source_invoice_no", original_source)
            return_against = found_original["name"] if found_original else None
        payload = None
        try:
            payload = invoice_payload(lines, config, batch_id, return_against)
            digest = payload_hash(payload)
            prior = connection.execute(
                """SELECT erp_document_name, payload_hash FROM migration_audit
                   WHERE batch_id=? AND source_document_no=? AND erp_doctype='Sales Invoice'
                     AND migration_status='SUCCESS'""", [batch_id, source_no]
            ).fetchone()
            if prior:
                if prior[1] != digest:
                    raise RuntimeError("Payload changed after successful migration; manual review required")
                originals[source_no] = prior[0]
                summary["skipped"] += 1
                continue
            existing = client.find_one("Sales Invoice", "custom_source_invoice_no", source_no)
            document = existing or client.create("Sales Invoice", payload)
            name = document["name"]
            if not existing and config.submit_documents:
                client.submit("Sales Invoice", name)
                summary["submitted"] += 1
            _record(connection, batch_id, source_no, "Sales Invoice", digest, "SUCCESS", name, json.dumps(document))
            originals[source_no] = name
            summary["created" if not existing else "skipped"] += 1
        except Exception as exc:  # noqa: BLE001 - audit and continue at the document boundary
            digest = payload_hash(payload) if payload is not None else "NOT_BUILT"
            _record(connection, batch_id, source_no, "Sales Invoice", digest, "FAILED", None, repr(exc))
            summary["failed"] += 1
    return summary
