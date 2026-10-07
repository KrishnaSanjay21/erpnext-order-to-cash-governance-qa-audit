"""Command-line entry points for the controlled migration lifecycle."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import typer

from .settings import Settings
from .source import download_dataset, extract_workbook, load_workbook, sha256_file, snapshot_source
from .validation import validate_transactions, write_validation_outputs
from .warehouse import complete_validation, export_dashboard_tables, open_warehouse, register_batch


app = typer.Typer(no_args_is_help=True)
ROOT = Path(__file__).parents[2]


@app.command()
def acquire(force: bool = False) -> None:
    """Download, checksum, extract, and profile the official UCI workbook."""
    settings = Settings()
    settings.ensure_directories()
    archive = settings.raw_dir / "online_retail_ii.zip"
    workbook = settings.raw_dir / "online_retail_II.xlsx"
    if force or not archive.exists():
        download_dataset(archive)
    if force or not workbook.exists():
        extract_workbook(archive, settings.raw_dir)
    profile = snapshot_source(load_workbook(workbook), settings.processed_dir)
    typer.echo(json.dumps(profile, indent=2))


@app.command("validate")
def validate_command() -> None:
    """Apply all row controls and create accepted/rejected evidence sets."""
    settings = Settings()
    source_path = settings.processed_dir / "source_transactions.parquet"
    if not source_path.exists():
        raise typer.BadParameter("Run `otc-audit acquire` first")
    profile = write_validation_outputs(
        validate_transactions(pd.read_parquet(source_path)), settings.processed_dir
    )
    typer.echo(json.dumps(profile, indent=2))


@app.command("build-audit")
def build_audit() -> None:
    """Register the checksum-controlled batch and export dashboard-ready evidence."""
    settings = Settings()
    archive = settings.raw_dir / "online_retail_ii.zip"
    accepted = settings.processed_dir / "accepted_transactions.parquet"
    rejected = settings.processed_dir / "rejected_transactions.parquet"
    if not (archive.exists() and accepted.exists() and rejected.exists()):
        raise typer.BadParameter("Run `otc-audit acquire` and `otc-audit validate` first")
    accepted_frame = pd.read_parquet(accepted, columns=["line_amount"])
    rejected_frame = pd.read_parquet(rejected, columns=["line_amount"])
    profile = {
        "source_rows": len(accepted_frame) + len(rejected_frame),
        "accepted_rows": len(accepted_frame),
        "rejected_rows": len(rejected_frame),
        "accepted_net_revenue_gbp": round(float(accepted_frame["line_amount"].sum()), 2),
        "rejected_net_revenue_gbp": round(float(rejected_frame["line_amount"].sum()), 2),
    }
    connection = open_warehouse(settings.otc_control_db, ROOT / "sql" / "warehouse_schema.sql")
    batch_id, created = register_batch(connection, archive, sha256_file(archive))
    complete_validation(connection, batch_id, profile)
    export_dashboard_tables(connection, settings.processed_dir / "dashboard")
    report = {"batch_id": batch_id, "new_file_registration": created, **profile}
    settings.reports_dir.mkdir(parents=True, exist_ok=True)
    (settings.reports_dir / "validation_summary.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    typer.echo(json.dumps(report, indent=2))


@app.command()
def all(force_download: bool = False) -> None:
    """Run acquisition, validation, and local audit construction end to end."""
    acquire(force_download)
    validate_command()
    build_audit()


if __name__ == "__main__":
    app()

