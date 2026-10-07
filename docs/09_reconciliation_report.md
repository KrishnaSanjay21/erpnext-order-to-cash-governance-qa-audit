# Source validation and reconciliation report

**Dataset:** UCI Online Retail II  
**Source archive SHA-256:** `572e36277c2390fbfde10664750731e0a86f55e33470d91919085f0408e67bfb`  
**Execution date:** 2026-10-07  
**ERP posting status:** Controlled live UAT passed on ERPNext 16.50.0; full accepted population not run.

## Source control totals

| Measure | Observed |
|---|---:|
| Published/source rows | 1,067,371 |
| Distinct source invoices | 53,628 |
| Distinct known customers | 5,942 |
| Distinct item codes | 5,304 |
| Source net revenue | £19,287,250.57 |

## Validation disposition

| Disposition | Type | Rows | Documents | Net revenue |
|---|---|---:|---:|---:|
| Accepted | Sale | 805,549 | 36,969 | £17,743,429.18 |
| Accepted | Return | 10,447 | 5,301 | -£595,209.84 |
| Rejected | Sale | 242,328 | 8,422 | £3,070,489.25 |
| Rejected | Return | 9,047 | 2,991 | -£931,458.02 |
| **Total** |  | **1,067,371** | not additive | **£19,287,250.57** |

Accepted rows: **815,996**. Rejected rows: **251,375**. Accepted net scope: **£17,148,219.34**. Rejected net scope: **£2,139,031.23**. Counts and revenue reconcile exactly to the canonical source snapshot before any ERP posting.

## Exception counts

Reason counts are non-additive because one row can fail multiple controls.

| Control | Failed rows |
|---|---:|
| DQ001 missing customer | 243,007 |
| DQ009 unmatched/ambiguous return | 9,047 |
| DQ006 non-positive price | 6,207 |
| DQ007 negative non-cancellation quantity | 3,457 |
| DQ008 non-negative cancellation quantity | 1 |

## Controlled live ERP reconciliation

| Measure | Observed |
|---|---:|
| Sale | `ACC-SINV-2026-00001`, £39.90, submitted |
| Linked credit note | `ACC-SINV-2026-00002`, -£39.90, submitted |
| Credit-note link | `return_against = ACC-SINV-2026-00001` |
| Net amount | £0.00 |
| Sale GL | £40.00 debit = £40.00 credit; £0.00 difference |
| Return GL | £40.00 debit = £40.00 credit; £0.00 difference |
| Lineage | Unique source invoice and batch IDs retained on both documents |
| Access check | Integration-only user cannot submit Sales Invoices |

The £0.10 round-off entry on each voucher explains the difference between the £39.90 document total and £40.00 balanced GL turnover. See `docs/11_live_verification_report.md` for exact SQL evidence.

## Full-population ERP reconciliation gates

These remain **NOT RUN** because the controlled UAT does not represent a full migration:

1. Accepted documents versus successful ERP Sales Invoice audit rows.
2. Accepted signed revenue versus ERP invoice grand totals.
3. Every ERP return linked to its original submitted invoice.
4. Every submitted invoice balanced by `tabGL Entry` within £0.01.
5. Zero duplicate source invoice custom keys.

