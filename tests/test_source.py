import pandas as pd

from otc_audit.source import canonicalize_columns


def test_canonicalize_columns_supports_first_year_headers():
    frame = pd.DataFrame(
        {
            "Invoice": ["489434"],
            "StockCode": ["85048"],
            "Description": ["15CM CHRISTMAS GLASS BALL"],
            "Quantity": [12],
            "InvoiceDate": ["2009-12-01"],
            "Price": [6.95],
            "Customer ID": [13085],
            "Country": ["United Kingdom"],
        }
    )
    result = canonicalize_columns(frame)
    assert result.columns.tolist() == [
        "invoice_no",
        "stock_code",
        "description",
        "quantity",
        "invoice_date",
        "unit_price",
        "customer_id",
        "country",
    ]


def test_canonicalize_columns_supports_second_year_headers():
    frame = pd.DataFrame(
        {
            "InvoiceNo": ["536365"],
            "StockCode": ["85123A"],
            "Description": ["WHITE HANGING HEART T-LIGHT HOLDER"],
            "Quantity": [6],
            "InvoiceDate": ["2010-12-01"],
            "UnitPrice": [2.55],
            "CustomerID": [17850],
            "Country": ["United Kingdom"],
        }
    )
    assert canonicalize_columns(frame).loc[0, "unit_price"] == 2.55

