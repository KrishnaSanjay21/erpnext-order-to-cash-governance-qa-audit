# Troubleshooting and batch-recovery runbook

## Triage order

1. Record the batch ID, source checksum, command, timestamp, and error without modifying source files.
2. Check `batch_run`, then `migration_audit`, then ERPNext worker/web logs.
3. Identify whether the failure is source validation, network/API, master data, workflow/permission, accounting, or infrastructure.
4. Correct configuration or approved transformation code. Never edit a posted ERP document or raw source to hide a variance.
5. Run automated tests, resume the batch, then rerun reconciliation controls.

## Common failures

| Symptom | Check | Recovery |
|---|---|---|
| Docker API unavailable | Start Docker Desktop; `docker version`. | Start engine, then `docker compose up -d`; do not delete volumes. |
| Frontend returns 502 | `docker compose ps`; backend/websocket logs. | Wait for site creation; restart only unhealthy service. |
| API 401/403 | Integration user's key, secret, roles, and expiry. | Rotate credential and update ignored `.env`; rerun failed documents. |
| Duplicate archive | Existing `batch_run.source_sha256`. | Treat as controlled replay; use existing batch, do not register another. |
| Payload changed after success | Compare payload hash and Git revision. | Stop; open High defect; obtain data-owner approval before correction. |
| Missing Customer/Item | Master migration audit and custom source field. | Rerun idempotent masters, then failed invoices. |
| Return lacks original | DQ009 evidence and original invoice status. | Quarantine until one submitted original is proven. |
| Closed period error | ERP Accounts Frozen Till Date and role. | Use approved open posting date or finance-authorized exception; retain evidence. |
| Unbalanced GL query result | Invoice, tax, currency, rounding and GL rows. | Hold batch; do not force-close; resolve accounting configuration and retest. |

## Safe recovery sequence

```powershell
docker compose ps
docker compose logs --tail 200 backend queue scheduler
python -m pytest
python -m otc_audit.cli build-audit
python scripts/migrate_to_erpnext.py --batch-id <BATCH-ID> --skip-masters
```

The migration reads successful audit rows and skips an identical payload. Failed documents are retried. A different payload for a successful source invoice fails closed and requires manual review.

## Backup and rollback

- Before a submission UAT, run `docker compose exec backend bench --site frontend backup --with-files`.
- Draft documents may be deleted only under the approved UAT cleanup procedure.
- Submitted documents are reversed/cancelled through ERPNext; never delete their GL rows.
- `docker compose down` preserves volumes. `docker compose down -v` is destructive and is excluded from normal recovery.

