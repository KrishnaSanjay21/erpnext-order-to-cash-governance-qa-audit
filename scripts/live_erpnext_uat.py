"""Run a small, idempotent live ERPNext order-to-cash verification.

This module is copied into the ERPNext container and invoked with ``bench
execute``.  It deliberately uses one non-stock sale and its full credit-note
return so that accounting, lineage, reconciliation, and access controls can be
verified without loading the full million-row source into a portfolio demo.
"""

from __future__ import annotations

import json

import frappe
from erpnext.accounts.doctype.sales_invoice.sales_invoice import make_sales_return
from frappe.utils import add_days, flt, nowdate

COMPANY = "UCI Retail Audit Ltd"
BATCH_ID = "LIVE-UAT-20261007"
CUSTOMER = "UCI Live Verification Customer"
ITEM = "UCI-LIVE-VERIFY-ITEM"
INTEGRATION_USER = "otc.integration@example.com"
SALE_SOURCE_ID = "UAT-SALE-001"
RETURN_SOURCE_ID = "UAT-RETURN-001"

ROLES = (
    "OTC Integration User",
    "OTC Invoice Preparer",
    "OTC Invoice Approver",
    "OTC Auditor",
)

CUSTOM_FIELDS = (
    {
        "dt": "Customer",
        "fieldname": "custom_source_customer_id",
        "label": "Source Customer ID",
        "fieldtype": "Data",
        "unique": 1,
        "insert_after": "customer_name",
        "read_only": 1,
    },
    {
        "dt": "Customer",
        "fieldname": "custom_source_country",
        "label": "Source Country",
        "fieldtype": "Data",
        "insert_after": "custom_source_customer_id",
        "read_only": 1,
    },
    {
        "dt": "Item",
        "fieldname": "custom_source_stock_code",
        "label": "Source Stock Code",
        "fieldtype": "Data",
        "unique": 1,
        "insert_after": "item_name",
        "read_only": 1,
    },
    {
        "dt": "Sales Invoice",
        "fieldname": "custom_source_invoice_no",
        "label": "Source Invoice No",
        "fieldtype": "Data",
        "unique": 1,
        "insert_after": "customer",
        "read_only": 1,
    },
    {
        "dt": "Sales Invoice",
        "fieldname": "custom_migration_batch_id",
        "label": "Migration Batch ID",
        "fieldtype": "Data",
        "insert_after": "custom_source_invoice_no",
        "read_only": 1,
    },
    {
        "dt": "Sales Invoice Item",
        "fieldname": "custom_source_row_id",
        "label": "Source Row ID",
        "fieldtype": "Data",
        "insert_after": "item_code",
        "read_only": 1,
    },
)


def _ensure_governance_configuration() -> None:
    for role in ROLES:
        if not frappe.db.exists("Role", role):
            frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert()

    for definition in CUSTOM_FIELDS:
        name = f"{definition['dt']}-{definition['fieldname']}"
        if not frappe.db.exists("Custom Field", name):
            frappe.get_doc({"doctype": "Custom Field", **definition}).insert()

    frappe.clear_cache()


def _ensure_masters() -> None:
    if not frappe.db.exists("Item Group", "UCI Retail Items"):
        frappe.get_doc(
            {
                "doctype": "Item Group",
                "item_group_name": "UCI Retail Items",
                "parent_item_group": "All Item Groups",
                "is_group": 0,
            }
        ).insert()

    if not frappe.db.exists("Customer", CUSTOMER):
        frappe.get_doc(
            {
                "doctype": "Customer",
                "customer_name": CUSTOMER,
                "customer_type": "Company",
                "customer_group": "Commercial",
                "territory": "All Territories",
                "custom_source_customer_id": "UAT-CUSTOMER-001",
                "custom_source_country": "United Kingdom",
            }
        ).insert()

    if not frappe.db.exists("Item", ITEM):
        frappe.get_doc(
            {
                "doctype": "Item",
                "item_code": ITEM,
                "item_name": "UCI Live Verification Item",
                "item_group": "UCI Retail Items",
                "stock_uom": "Nos",
                "is_stock_item": 0,
                "custom_source_stock_code": "UAT-STOCK-001",
            }
        ).insert()

    if not frappe.db.exists("User", INTEGRATION_USER):
        user = frappe.get_doc(
            {
                "doctype": "User",
                "email": INTEGRATION_USER,
                "first_name": "OTC Integration",
                "enabled": 1,
                "send_welcome_email": 0,
                "user_type": "System User",
            }
        )
        user.append("roles", {"role": "OTC Integration User"})
        user.insert(ignore_permissions=True)


def _invoice_by_source(source_id: str):
    name = frappe.db.get_value("Sales Invoice", {"custom_source_invoice_no": source_id}, "name")
    return frappe.get_doc("Sales Invoice", name) if name else None


def _ensure_sale():
    invoice = _invoice_by_source(SALE_SOURCE_ID)
    if not invoice:
        invoice = frappe.get_doc(
            {
                "doctype": "Sales Invoice",
                "company": COMPANY,
                "customer": CUSTOMER,
                "posting_date": nowdate(),
                "due_date": add_days(nowdate(), 30),
                "currency": "GBP",
                "custom_source_invoice_no": SALE_SOURCE_ID,
                "custom_migration_batch_id": BATCH_ID,
                "items": [
                    {
                        "item_code": ITEM,
                        "qty": 2,
                        "rate": 19.95,
                        "custom_source_row_id": "UAT-ROW-SALE-001",
                    }
                ],
            }
        ).insert()
    if invoice.docstatus == 0:
        invoice.submit()
    return invoice


def _ensure_return(sale):
    credit_note = _invoice_by_source(RETURN_SOURCE_ID)
    if not credit_note:
        credit_note = make_sales_return(sale.name)
        credit_note.custom_source_invoice_no = RETURN_SOURCE_ID
        credit_note.custom_migration_batch_id = BATCH_ID
        for index, line in enumerate(credit_note.items, start=1):
            line.custom_source_row_id = f"UAT-ROW-RETURN-{index:03d}"
        credit_note.insert()
    if credit_note.docstatus == 0:
        credit_note.submit()
    return credit_note


def _gl_summary(voucher_no: str) -> dict:
    entries = frappe.get_all(
        "GL Entry",
        filters={"voucher_type": "Sales Invoice", "voucher_no": voucher_no, "is_cancelled": 0},
        fields=["account", "debit", "credit"],
        order_by="account",
    )
    debit = sum(flt(row.debit, 2) for row in entries)
    credit = sum(flt(row.credit, 2) for row in entries)
    return {
        "entry_count": len(entries),
        "debit": round(debit, 2),
        "credit": round(credit, 2),
        "difference": round(debit - credit, 2),
        "accounts": [row.account for row in entries],
    }


def run() -> dict:
    _ensure_governance_configuration()
    _ensure_masters()
    sale = _ensure_sale()
    credit_note = _ensure_return(sale)
    frappe.db.commit()

    result = {
        "erpnext_version": frappe.get_attr("erpnext.__version__"),
        "company": COMPANY,
        "batch_id": BATCH_ID,
        "sale": {
            "name": sale.name,
            "source_invoice": sale.custom_source_invoice_no,
            "docstatus": sale.docstatus,
            "grand_total": round(flt(sale.grand_total), 2),
            "gl": _gl_summary(sale.name),
        },
        "return": {
            "name": credit_note.name,
            "source_invoice": credit_note.custom_source_invoice_no,
            "return_against": credit_note.return_against,
            "docstatus": credit_note.docstatus,
            "grand_total": round(flt(credit_note.grand_total), 2),
            "gl": _gl_summary(credit_note.name),
        },
        "reconciled_net": round(flt(sale.grand_total) + flt(credit_note.grand_total), 2),
        "integration_user_can_submit_sales_invoice": bool(
            frappe.has_permission("Sales Invoice", ptype="submit", user=INTEGRATION_USER)
        ),
        "configured_roles": list(ROLES),
        "configured_lineage_fields": len(CUSTOM_FIELDS),
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return result
