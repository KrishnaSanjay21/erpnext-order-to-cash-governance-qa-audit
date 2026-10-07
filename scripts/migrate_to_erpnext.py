"""Execute a resumable master-data and Sales Invoice migration."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import yaml

from otc_audit.erpnext import ERPNextClient, MigrationConfig
from otc_audit.migration import migrate_invoices, migrate_masters
from otc_audit.settings import Settings
from otc_audit.warehouse import open_warehouse


ROOT = Path(__file__).parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-id", required=True)
    parser.add_argument("--limit", type=int, help="Migrate only this many invoices for controlled UAT")
    parser.add_argument("--skip-masters", action="store_true")
    arguments = parser.parse_args()
    settings = Settings()
    if "replace-me" in {settings.erpnext_api_key, settings.erpnext_api_secret}:
        raise SystemExit("Set ERPNEXT_API_KEY and ERPNEXT_API_SECRET in .env")
    raw_config = yaml.safe_load((ROOT / "config" / "migration.yml").read_text(encoding="utf-8"))
    config = MigrationConfig(**{key: raw_config[key] for key in MigrationConfig.__dataclass_fields__})
    accepted = pd.read_parquet(settings.processed_dir / "accepted_transactions.parquet")
    connection = open_warehouse(settings.otc_control_db, ROOT / "sql" / "warehouse_schema.sql")
    client = ERPNextClient(settings.erpnext_base_url, settings.erpnext_api_key, settings.erpnext_api_secret)
    try:
        if not arguments.skip_masters:
            print(migrate_masters(client, accepted, config))
        print(migrate_invoices(client, connection, accepted, config, arguments.batch_id, arguments.limit))
    finally:
        client.close()


if __name__ == "__main__":
    main()
