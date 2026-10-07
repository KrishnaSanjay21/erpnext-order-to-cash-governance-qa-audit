import pandas as pd

from otc_audit.erpnext import MigrationConfig
from otc_audit.migration import migrate_masters

CONFIG = MigrationConfig(
    company="UCI Retail Audit Ltd", currency="GBP", territory="All Territories",
    customer_group="Commercial", item_group="Items", warehouse="Stores - URA",
    income_account="Sales - URA", receivable_account="Debtors - URA", cost_center="Main - URA",
)


class FakeClient:
    def __init__(self):
        self.keys = []

    def ensure_named(self, doctype, name, payload):
        self.keys.append((doctype, name))
        return {"name": name}, True


def test_master_migration_deduplicates_source_keys():
    frame = pd.DataFrame([{
        "invoice_no": "100", "stock_code": "A/1", "description": "Widget", "quantity": 2,
        "unit_price": 3.5, "customer_id": "42", "country": "United Kingdom",
        "invoice_date": pd.Timestamp("2011-02-03"), "document_type": "SALE",
        "source_row_id": "2010:2",
    }])
    frame = frame._append(frame.assign(invoice_no="101"), ignore_index=True)
    client = FakeClient()
    result = migrate_masters(client, frame, CONFIG)
    assert result == {"customers_created": 1, "items_created": 1}
    assert client.keys == [("Customer", "UCI-CUST-42"), ("Item", "UCI-ITEM-A-1")]
