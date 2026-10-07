"""Create ERPNext lineage fields and governance roles through the REST API."""

from __future__ import annotations

import json
from pathlib import Path

from otc_audit.erpnext import ERPNextClient
from otc_audit.settings import Settings


ROOT = Path(__file__).parents[1]


def main() -> None:
    settings = Settings()
    if "replace-me" in {settings.erpnext_api_key, settings.erpnext_api_secret}:
        raise SystemExit("Set ERPNEXT_API_KEY and ERPNEXT_API_SECRET in .env")
    client = ERPNextClient(
        settings.erpnext_base_url, settings.erpnext_api_key, settings.erpnext_api_secret
    )
    try:
        for role in ("OTC Integration User", "OTC Invoice Preparer", "OTC Invoice Approver", "OTC Auditor"):
            client.ensure_named("Role", role, {"role_name": role, "desk_access": 1})
        fields = json.loads((ROOT / "erpnext" / "custom_fields.json").read_text(encoding="utf-8"))
        for field in fields:
            name = f"{field['dt']}-{field['fieldname']}"
            client.ensure_named("Custom Field", name, field)
    finally:
        client.close()
    print("ERPNext lineage fields and OTC governance roles are configured.")


if __name__ == "__main__":
    main()
