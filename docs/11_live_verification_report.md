# Live ERPNext verification report

**Execution date:** 2026-10-07  
**Environment:** local Docker Desktop, ERPNext 16.50.0, Frappe 16.50.0, MariaDB 11.8  
**Scope:** controlled portfolio UAT; not a full-population or production migration

## Environment evidence

- Docker client and server: 29.4.3.
- Docker data is stored on `D:\DockerDesktop\wsl`; the expected local Docker path is a junction to that location.
- ERPNext, MariaDB, Redis, backend, frontend, workers, scheduler, and websocket services started successfully.
- `GET http://127.0.0.1:8080/api/method/ping` returned HTTP 200 with `{"message":"pong"}`.
- `bench --site frontend list-apps` returned Frappe 16.50.0 and ERPNext 16.50.0.

## Controlled UAT design

The live check creates one fictional customer, one non-stock item, one submitted sale, and a full return. It also creates the four documented governance roles and six lineage fields. This isolates accounting and authorization behavior from the million-row source validation and makes the test safe to repeat.

Run it with:

```powershell
docker compose cp scripts/live_erpnext_uat.py backend:/home/frappe/frappe-bench/apps/erpnext/erpnext/live_otc_uat.py
docker compose exec -T backend bench --site frontend execute erpnext.live_otc_uat.run
```

## Results

| Control | Result | Evidence |
|---|---|---|
| UAT-001 normal sale | PASS | `ACC-SINV-2026-00001`, submitted, £39.90 |
| UAT-002 product return | PASS | `ACC-SINV-2026-00002`, submitted, -£39.90, linked to original |
| Amount reconciliation | PASS | £39.90 + -£39.90 = £0.00 |
| UAT-010 sale GL balance | PASS | £40.00 debit, £40.00 credit, £0.00 difference, 3 entries |
| UAT-010 return GL balance | PASS | £40.00 debit, £40.00 credit, £0.00 difference, 3 entries |
| Source lineage | PASS | `UAT-SALE-001` and `UAT-RETURN-001`; batch `LIVE-UAT-20261007` |
| UAT-006 unauthorized submit | PASS | Integration-only user submit permission evaluated to false |
| Governance configuration | PASS | 4 roles and 6 custom lineage fields present |

Each voucher includes Debtors, Sales, and Round Off accounts. The £0.10 round-off entry is why £39.90 document value produces £40.00 of debit and credit turnover while remaining balanced.

## Direct SQL cross-check

```text
voucher_no             debit  credit  difference  entries
ACC-SINV-2026-00001    40.00  40.00   0.00        3
ACC-SINV-2026-00002    40.00  40.00   0.00        3
```

```text
name                    is_return  return_against         grand_total  docstatus  source_invoice   batch
ACC-SINV-2026-00001     0          NULL                   39.90        1          UAT-SALE-001    LIVE-UAT-20261007
ACC-SINV-2026-00002     1          ACC-SINV-2026-00001   -39.90        1          UAT-RETURN-001  LIVE-UAT-20261007
```

## Boundary of the claim

This report verifies a real local ERPNext accounting and permissions sample. It does not claim that all 42,270 accepted source documents were loaded, that every open source-data defect was resolved, or that the environment is production-deployed. The full-population ERP count, signed-revenue, return-link, duplicate-key, and GL controls remain **NOT RUN**.
