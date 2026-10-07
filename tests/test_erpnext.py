import pandas as pd
import pytest

from otc_audit.erpnext import MigrationConfig, invoice_payload, payload_hash, safe_key

CONFIG = MigrationConfig(
    company="UCI Retail Audit Ltd", currency="GBP", territory="All Territories",
    customer_group="Commercial", item_group="Items", warehouse="Stores - URA",
    income_account="Sales - URA", receivable_account="Debtors - URA",
    cost_center="Main - URA",
)


def line(document_type="SALE"):
    return pd.DataFrame([{
        "invoice_no": "C100" if document_type == "RETURN" else "100",
        "stock_code": "A/1", "description": "Widget", "quantity": -1 if document_type == "RETURN" else 2,
        "unit_price": 3.5, "customer_id": "42", "invoice_date": pd.Timestamp("2011-02-03"),
        "document_type": document_type, "source_row_id": "2010:2",
    }])


def test_sale_payload_keeps_lineage_and_accounting_dimensions():
    payload = invoice_payload(line(), CONFIG, "BATCH-1")
    assert payload["customer"] == "UCI-CUST-42"
    assert payload["items"][0]["item_code"] == "UCI-ITEM-A-1"
    assert payload["items"][0]["custom_source_row_id"] == "2010:2"
    assert payload["is_return"] == 0


def test_return_requires_and_uses_original_document():
    with pytest.raises(ValueError):
        invoice_payload(line("RETURN"), CONFIG, "BATCH-1")
    payload = invoice_payload(line("RETURN"), CONFIG, "BATCH-1", "SINV-00001")
    assert payload["return_against"] == "SINV-00001"
    assert payload["items"][0]["qty"] == -1


def test_payload_hash_is_order_independent():
    assert payload_hash({"a": 1, "b": 2}) == payload_hash({"b": 2, "a": 1})


def test_long_keys_are_deterministic_and_bounded():
    value = "x" * 200
    assert safe_key("UCI-", value) == safe_key("UCI-", value)
    assert len(safe_key("UCI-", value)) <= 140
