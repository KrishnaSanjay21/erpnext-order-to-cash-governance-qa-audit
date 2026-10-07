# Data dictionary

## Canonical source and validation fields

| Field | Type | Definition |
|---|---|---|
| `source_row_id` | string | Stable `<sheet>:<Excel row>` locator. |
| `invoice_no` | string | Source transaction/invoice identifier; `C` prefix means cancellation. |
| `stock_code` | string | Source product identifier. |
| `description` | string | Source product description. |
| `quantity` | integer | Units; negative values represent reversals/adjustments. |
| `invoice_date` | timestamp | Source transaction time. |
| `unit_price` | decimal | GBP price per unit. |
| `customer_id` | nullable string | Anonymized source customer identifier. |
| `country` | string | Source destination country. |
| `line_amount` | decimal | `quantity × unit_price`; signed, unrounded analytical amount. |
| `document_type` | enum | `SALE` or `RETURN`, derived from invoice prefix. |
| `original_invoice_no` | nullable string | Nearest prior sale matched on customer, item, unit price, and sufficient quantity; populated only when every cancellation line resolves to one original. |
| `record_status` | enum | `ACCEPTED` only when no blocking rule failed; otherwise `REJECTED`. |
| `reason_codes` | string | Pipe-delimited complete set of failed DQ controls. |
| `source_line_hash` | hex string | Deterministic 64-bit content fingerprint for duplicate analysis. |

## Audit warehouse entities

| Entity | Grain | Purpose |
|---|---|---|
| `batch_run` | One row per unique archive SHA-256 | File idempotency and batch lifecycle. |
| `migration_audit` | Batch × source document × ERP DocType | Payload hash, ERP identifier, status, response. |
| `control_result` | Control execution × control | Observed, expected, variance, status, evidence query. |
| `defect_log` | Defect | Severity, ownership, status, due date, remediation. |
| `access_assignment` | User × role snapshot | Segregation-of-duties testing. |

## Reason codes

| Code | Blocking condition |
|---|---|
| DQ001 | Customer identifier is missing. |
| DQ002 | Invoice identifier is missing. |
| DQ003 | Item identifier is missing. |
| DQ004 | Invoice date is invalid. |
| DQ005 | Quantity is null or zero. |
| DQ006 | Unit price is null, zero, or negative. |
| DQ007 | Non-cancellation has a non-positive quantity. |
| DQ008 | Cancellation has a non-negative quantity. |
| DQ009 | Cancellation cannot be linked to a source original invoice. |

