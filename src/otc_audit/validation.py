"""Vectorized, reason-coded validation for the UCI migration scope."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


ERROR_COLUMNS = {
    "DQ001": "missing_customer",
    "DQ002": "missing_invoice",
    "DQ003": "missing_item",
    "DQ004": "invalid_date",
    "DQ005": "zero_quantity",
    "DQ006": "nonpositive_price",
    "DQ007": "negative_sale_quantity",
    "DQ008": "nonnegative_return_quantity",
    "DQ009": "unmatched_return",
}


def _match_returns(result: pd.DataFrame, is_return: pd.Series) -> pd.Series:
    """Resolve complete return documents to one nearest prior compatible sale."""
    keys = ["customer_id", "stock_code", "unit_price"]
    sales = result.loc[
        (~is_return)
        & result["quantity"].gt(0)
        & result["customer_id"].notna()
        & result["unit_price"].gt(0),
        ["invoice_no", "customer_id", "stock_code", "unit_price", "quantity", "invoice_date"],
    ].copy()
    sales = sales.rename(columns={"quantity": "sale_quantity"})
    sales = sales.rename(columns={"invoice_no": "matched_original_invoice"})
    returns = result.loc[
        is_return
        & result["quantity"].lt(0)
        & result["customer_id"].notna()
        & result["unit_price"].gt(0),
        ["invoice_no", "customer_id", "stock_code", "unit_price", "quantity", "invoice_date"],
    ].copy()
    returns["source_index"] = returns.index
    returns["return_quantity"] = returns.pop("quantity").abs()
    if returns.empty:
        return pd.Series(pd.NA, index=result.index, dtype="string")
    matched = pd.merge_asof(
        returns.sort_values("invoice_date"),
        sales.sort_values("invoice_date"),
        on="invoice_date",
        by=keys,
        direction="backward",
        allow_exact_matches=True,
    )
    matched.loc[
        matched["sale_quantity"].lt(matched["return_quantity"]), "matched_original_invoice"
    ] = pd.NA
    stats = matched.groupby("invoice_no", dropna=False)["matched_original_invoice"].agg(
        matched_lines="count", original_count="nunique"
    )
    expected_lines = result.loc[is_return].groupby("invoice_no", dropna=False).size()
    stats["expected_lines"] = expected_lines
    eligible = stats.index[
        stats["matched_lines"].eq(stats["expected_lines"]) & stats["original_count"].eq(1)
    ]
    matched.loc[~matched["invoice_no"].isin(eligible), "matched_original_invoice"] = pd.NA
    original = pd.Series(pd.NA, index=result.index, dtype="string")
    original.loc[matched["source_index"]] = matched["matched_original_invoice"].astype("string").to_numpy()
    return original


def validate_transactions(frame: pd.DataFrame) -> pd.DataFrame:
    """Return every source row with migration disposition and all triggered controls."""
    result = frame.copy()
    invoice = result["invoice_no"].astype("string")
    is_return = invoice.str.upper().str.startswith("C", na=False)
    original = _match_returns(result, is_return)

    flags = {
        "DQ001": result["customer_id"].isna() | result["customer_id"].eq(""),
        "DQ002": invoice.isna() | invoice.eq(""),
        "DQ003": result["stock_code"].isna() | result["stock_code"].eq(""),
        "DQ004": result["invoice_date"].isna(),
        "DQ005": result["quantity"].isna() | result["quantity"].eq(0),
        "DQ006": result["unit_price"].isna() | result["unit_price"].le(0),
        "DQ007": (~is_return) & result["quantity"].le(0),
        "DQ008": is_return & result["quantity"].ge(0),
        "DQ009": is_return & original.isna(),
    }
    for rule, column in ERROR_COLUMNS.items():
        result[column] = flags[rule].fillna(True)

    result["reason_codes"] = ""
    for rule, flag in flags.items():
        failed = flag.fillna(True)
        separator = result.loc[failed, "reason_codes"].ne("").map({True: "|", False: ""})
        result.loc[failed, "reason_codes"] += separator + rule
    result["record_status"] = result["reason_codes"].map(lambda value: "REJECTED" if value else "ACCEPTED")
    result["document_type"] = is_return.map({True: "RETURN", False: "SALE"})
    result["original_invoice_no"] = original
    result["line_amount"] = result["quantity"].astype("float64") * result["unit_price"]
    hash_columns = [
        "invoice_no", "stock_code", "quantity", "invoice_date",
        "unit_price", "customer_id", "country",
    ]
    result["source_line_hash"] = pd.util.hash_pandas_object(
        result[hash_columns], index=False
    ).map(lambda value: f"{value:016x}")
    return result


def write_validation_outputs(validated: pd.DataFrame, processed_dir: Path) -> dict[str, int | float]:
    processed_dir.mkdir(parents=True, exist_ok=True)
    validated.to_parquet(processed_dir / "validated_transactions.parquet", index=False)
    accepted = validated.loc[validated["record_status"].eq("ACCEPTED")]
    rejected = validated.loc[validated["record_status"].eq("REJECTED")]
    accepted.to_parquet(processed_dir / "accepted_transactions.parquet", index=False)
    rejected.to_parquet(processed_dir / "rejected_transactions.parquet", index=False)
    return {
        "source_rows": len(validated),
        "accepted_rows": len(accepted),
        "rejected_rows": len(rejected),
        "accepted_net_revenue_gbp": round(float(accepted["line_amount"].sum()), 2),
        "rejected_net_revenue_gbp": round(float(rejected["line_amount"].sum()), 2),
    }

