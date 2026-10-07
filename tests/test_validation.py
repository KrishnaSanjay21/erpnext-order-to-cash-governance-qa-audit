import pandas as pd

from otc_audit.validation import validate_transactions


def sample() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"invoice_no": "100", "stock_code": "A", "description": "Item", "quantity": 2,
             "invoice_date": pd.Timestamp("2011-01-01"), "unit_price": 3.0,
             "customer_id": "1", "country": "UK", "source_row_id": "s:2"},
            {"invoice_no": "C100", "stock_code": "A", "description": "Item", "quantity": -1,
             "invoice_date": pd.Timestamp("2011-01-02"), "unit_price": 3.0,
             "customer_id": "1", "country": "UK", "source_row_id": "s:3"},
        ]
    )


def test_valid_sale_and_matched_return_are_accepted():
    result = validate_transactions(sample())
    assert result["record_status"].tolist() == ["ACCEPTED", "ACCEPTED"]
    assert result["document_type"].tolist() == ["SALE", "RETURN"]
    assert result.loc[1, "original_invoice_no"] == "100"


def test_all_triggered_reasons_are_preserved():
    frame = sample().iloc[[0]].copy()
    frame.loc[0, "customer_id"] = pd.NA
    frame.loc[0, "unit_price"] = -1
    result = validate_transactions(frame)
    assert result.loc[0, "record_status"] == "REJECTED"
    assert set(result.loc[0, "reason_codes"].split("|")) == {"DQ001", "DQ006"}


def test_unmatched_return_is_rejected():
    frame = sample().iloc[[1]].copy()
    result = validate_transactions(frame)
    assert result.loc[1, "reason_codes"] == "DQ009"
