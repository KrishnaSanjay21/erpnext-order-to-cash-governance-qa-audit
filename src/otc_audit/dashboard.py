"""Create small, aggregate, Power BI-ready governance fact tables."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def build_dashboard_facts(validated: pd.DataFrame, output_dir: Path) -> dict[str, int]:
    output_dir.mkdir(parents=True, exist_ok=True)
    monthly = (
        validated.assign(month=validated["invoice_date"].dt.to_period("M").dt.to_timestamp())
        .groupby(["month", "record_status", "document_type"], dropna=False)
        .agg(rows=("source_row_id", "size"), documents=("invoice_no", "nunique"), net_revenue_gbp=("line_amount", "sum"))
        .reset_index()
    )
    monthly.to_parquet(output_dir / "fact_monthly_disposition.parquet", index=False)

    exploded = validated.loc[
        validated["record_status"].eq("REJECTED"),
        ["source_row_id", "invoice_date", "reason_codes"],
    ].copy()
    exploded["control_id"] = exploded.pop("reason_codes").str.split("|")
    exploded = exploded.explode("control_id")
    failures = (
        exploded.assign(month=exploded["invoice_date"].dt.to_period("M").dt.to_timestamp())
        .groupby(["month", "control_id"], dropna=False)
        .size().rename("failed_rows").reset_index()
    )
    failures.to_parquet(output_dir / "fact_control_failures.parquet", index=False)

    documents = (
        validated.groupby(["invoice_no", "record_status", "document_type"], dropna=False)
        .agg(
            invoice_date=("invoice_date", "min"),
            lines=("source_row_id", "size"),
            net_revenue_gbp=("line_amount", "sum"),
            country=("country", "first"),
            original_invoice_no=("original_invoice_no", "first"),
        ).reset_index()
    )
    documents.to_parquet(output_dir / "fact_document_disposition.parquet", index=False)
    return {"monthly_rows": len(monthly), "failure_rows": len(failures), "document_rows": len(documents)}

