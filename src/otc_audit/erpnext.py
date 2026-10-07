"""ERPNext REST client and deterministic source-to-document payloads."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Iterable
from urllib.parse import quote

import httpx
import pandas as pd
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential


def safe_key(prefix: str, value: str, limit: int = 140) -> str:
    normalized = re.sub(r"[^A-Za-z0-9._-]+", "-", str(value).strip()).strip("-")
    key = f"{prefix}{normalized}"
    if len(key) <= limit:
        return key
    digest = hashlib.sha1(key.encode()).hexdigest()[:10]
    return f"{key[:limit - 11]}-{digest}"


@dataclass(frozen=True)
class MigrationConfig:
    company: str
    currency: str
    territory: str
    customer_group: str
    item_group: str
    warehouse: str
    income_account: str
    receivable_account: str
    cost_center: str
    submit_documents: bool = False


class ERPNextClient:
    def __init__(self, base_url: str, api_key: str, api_secret: str, timeout: float = 60.0):
        self.client = httpx.Client(
            base_url=base_url.rstrip("/"),
            headers={"Authorization": f"token {api_key}:{api_secret}", "Accept": "application/json"},
            timeout=timeout,
        )

    def close(self) -> None:
        self.client.close()

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )
    def request(self, method: str, path: str, **kwargs) -> dict[str, Any]:
        response = self.client.request(method, path, **kwargs)
        response.raise_for_status()
        return response.json()

    def get(self, doctype: str, name: str) -> dict[str, Any] | None:
        response = self.client.get(f"/api/resource/{quote(doctype)}/{quote(name)}")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()["data"]

    def create(self, doctype: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self.request("POST", f"/api/resource/{quote(doctype)}", json=payload)["data"]

    def find_one(self, doctype: str, field: str, value: str) -> dict[str, Any] | None:
        data = self.request(
            "GET",
            f"/api/resource/{quote(doctype)}",
            params={
                "fields": json.dumps(["name", field]),
                "filters": json.dumps([[field, "=", value]]),
                "limit_page_length": 1,
            },
        )["data"]
        return data[0] if data else None

    def submit(self, doctype: str, name: str) -> dict[str, Any]:
        return self.request(
            "POST", "/api/method/frappe.client.submit",
            json={"doc": {"doctype": doctype, "name": name}},
        )["message"]

    def ensure_named(self, doctype: str, name: str, payload: dict[str, Any]) -> tuple[dict, bool]:
        existing = self.get(doctype, name)
        if existing:
            return existing, False
        return self.create(doctype, {"name": name, **payload}), True


def customer_payload(customer_id: str, country: str, config: MigrationConfig) -> dict[str, Any]:
    return {
        "customer_name": f"UCI Customer {customer_id}",
        "customer_type": "Company",
        "customer_group": config.customer_group,
        "territory": config.territory,
        "custom_source_customer_id": str(customer_id),
        "custom_source_country": country or "Unknown",
    }


def item_payload(stock_code: str, description: str, config: MigrationConfig) -> dict[str, Any]:
    return {
        "item_name": (description or f"UCI Item {stock_code}")[:140],
        "description": description or "Description unavailable in source",
        "item_group": config.item_group,
        "stock_uom": "Nos",
        "is_stock_item": 0,
        "include_item_in_manufacturing": 0,
        "custom_source_stock_code": str(stock_code),
    }


def invoice_payload(
    lines: pd.DataFrame,
    config: MigrationConfig,
    batch_id: str,
    return_against: str | None = None,
) -> dict[str, Any]:
    first = lines.iloc[0]
    source_invoice = str(first["invoice_no"])
    is_return = str(first["document_type"]) == "RETURN"
    if is_return and not return_against:
        raise ValueError(f"Return {source_invoice} requires ERP original invoice name")
    posting_date = pd.Timestamp(first["invoice_date"]).date().isoformat()
    items = []
    for row in lines.itertuples(index=False):
        items.append({
            "item_code": safe_key("UCI-ITEM-", row.stock_code),
            "qty": int(row.quantity),
            "rate": float(row.unit_price),
            "warehouse": config.warehouse,
            "income_account": config.income_account,
            "cost_center": config.cost_center,
            "custom_source_row_id": row.source_row_id,
        })
    payload = {
        "customer": safe_key("UCI-CUST-", first["customer_id"]),
        "company": config.company,
        "currency": config.currency,
        "posting_date": posting_date,
        "due_date": posting_date,
        "debit_to": config.receivable_account,
        "items": items,
        "is_return": 1 if is_return else 0,
        "custom_source_invoice_no": source_invoice,
        "custom_migration_batch_id": batch_id,
    }
    if return_against:
        payload["return_against"] = return_against
    return payload


def payload_hash(payload: dict[str, Any]) -> str:
    packed = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(packed.encode()).hexdigest()


def document_groups(accepted: pd.DataFrame) -> Iterable[tuple[str, pd.DataFrame]]:
    ordered = accepted.assign(
        _return_order=accepted["document_type"].eq("RETURN").astype(int)
    ).sort_values(["_return_order", "invoice_date", "invoice_no", "source_row_id"])
    for invoice_no, lines in ordered.groupby("invoice_no", sort=False):
        yield str(invoice_no), lines.drop(columns="_return_order")

