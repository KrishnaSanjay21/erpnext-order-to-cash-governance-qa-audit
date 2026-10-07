"""Acquire and standardize the UCI Online Retail II workbook."""

from __future__ import annotations

import hashlib
import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pandas as pd
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

DATASET_URL = "https://archive.ics.uci.edu/static/public/502/online%2Bretail%2Bii.zip"
DATASET_DOI = "https://doi.org/10.24432/C5CG6D"
EXPECTED_ROWS = 1_067_371

COLUMN_ALIASES = {
    "invoice": "invoice_no",
    "invoiceno": "invoice_no",
    "stockcode": "stock_code",
    "description": "description",
    "quantity": "quantity",
    "invoicedate": "invoice_date",
    "price": "unit_price",
    "unitprice": "unit_price",
    "customer id": "customer_id",
    "customerid": "customer_id",
    "country": "country",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@retry(
    retry=retry_if_exception_type(httpx.HTTPError),
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True,
)
def download_dataset(destination: Path, timeout_seconds: float = 180.0) -> dict:
    """Download the published UCI archive with provenance metadata."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".part")
    with httpx.stream("GET", DATASET_URL, timeout=timeout_seconds, follow_redirects=True) as response:
        response.raise_for_status()
        with temporary.open("wb") as target:
            for chunk in response.iter_bytes():
                target.write(chunk)
    temporary.replace(destination)
    manifest = {
        "dataset": "UCI Online Retail II",
        "source_url": DATASET_URL,
        "doi": DATASET_DOI,
        "license": "CC BY 4.0",
        "downloaded_at_utc": datetime.now(UTC).isoformat(),
        "file_size_bytes": destination.stat().st_size,
        "sha256": sha256_file(destination),
    }
    destination.with_suffix(".manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    return manifest


def extract_workbook(archive: Path, raw_dir: Path) -> Path:
    with zipfile.ZipFile(archive) as bundle:
        workbook_members = [name for name in bundle.namelist() if name.lower().endswith(".xlsx")]
        if len(workbook_members) != 1:
            raise ValueError(f"Expected one workbook in UCI archive, found {workbook_members}")
        member = workbook_members[0]
        output = raw_dir / "online_retail_II.xlsx"
        with bundle.open(member) as source, output.open("wb") as target:
            while chunk := source.read(1024 * 1024):
                target.write(chunk)
    return output


def canonicalize_columns(frame: pd.DataFrame) -> pd.DataFrame:
    mapped = {}
    for column in frame.columns:
        normalized = str(column).strip().lower().replace("_", "")
        key = str(column).strip().lower()
        canonical = COLUMN_ALIASES.get(key) or COLUMN_ALIASES.get(normalized)
        if canonical:
            mapped[column] = canonical
    result = frame.rename(columns=mapped)
    ordered = list(dict.fromkeys(COLUMN_ALIASES.values()))
    missing = sorted(set(ordered).difference(result.columns))
    if missing:
        raise ValueError(f"Workbook is missing expected columns: {missing}")
    result = result[ordered].copy()
    for column in ("invoice_no", "stock_code", "description", "country"):
        result[column] = result[column].astype("string").str.strip()
    result["invoice_no"] = result["invoice_no"].str.replace(r"\.0$", "", regex=True)
    result["stock_code"] = result["stock_code"].str.replace(r"\.0$", "", regex=True)
    result["customer_id"] = (
        pd.to_numeric(result["customer_id"], errors="coerce").round().astype("Int64").astype("string")
    )
    result["quantity"] = pd.to_numeric(result["quantity"], errors="coerce").astype("Int64")
    result["unit_price"] = pd.to_numeric(result["unit_price"], errors="coerce")
    result["invoice_date"] = pd.to_datetime(result["invoice_date"], errors="coerce")
    return result


def load_workbook(workbook: Path) -> pd.DataFrame:
    """Load both published years and assign stable source-row lineage."""
    sheets = pd.read_excel(workbook, sheet_name=None, engine="calamine")
    frames = []
    for sheet_name, sheet_frame in sheets.items():
        canonical = canonicalize_columns(sheet_frame)
        canonical["source_sheet"] = sheet_name
        canonical["source_excel_row"] = range(2, len(canonical) + 2)
        canonical["source_row_id"] = (
            canonical["source_sheet"].astype(str)
            + ":"
            + canonical["source_excel_row"].astype(str)
        )
        frames.append(canonical)
    combined = pd.concat(frames, ignore_index=True)
    if len(combined) != EXPECTED_ROWS:
        raise ValueError(f"Expected {EXPECTED_ROWS:,} published rows, loaded {len(combined):,}")
    return combined


def snapshot_source(frame: pd.DataFrame, processed_dir: Path) -> dict:
    output = processed_dir / "source_transactions.parquet"
    processed_dir.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(output, index=False)
    quantity = pd.to_numeric(frame["quantity"], errors="coerce")
    unit_price = pd.to_numeric(frame["unit_price"], errors="coerce")
    profile = {
        "rows": len(frame),
        "invoices": int(frame["invoice_no"].nunique(dropna=True)),
        "customers": int(frame["customer_id"].nunique(dropna=True)),
        "items": int(frame["stock_code"].nunique(dropna=True)),
        "missing_customer_rows": int(frame["customer_id"].isna().sum()),
        "cancellation_rows": int(
            frame["invoice_no"].astype("string").str.upper().str.startswith("C", na=False).sum()
        ),
        "source_revenue_gbp": float((quantity * unit_price).sum()),
    }
    (processed_dir / "source_profile.json").write_text(
        json.dumps(profile, indent=2), encoding="utf-8"
    )
    return profile

