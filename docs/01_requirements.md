# Requirements — ERPNext Order-to-Cash Governance Audit

## Objective and scope

Migrate the published UCI Online Retail II workbook into a controlled ERPNext order-to-cash model and produce evidence that every source row is accepted or rejected, accepted documents are traceable, submitted invoices balance in the general ledger, and access/workflow conflicts are detected.

The source contains real, anonymized transactions; ERP users, company configuration, migration batch metadata, and defect owners are demonstration artifacts. The project does not claim a production deployment.

## Functional requirements

| ID | Requirement | Acceptance evidence |
|---|---|---|
| FR-01 | Acquire the exact UCI archive and retain provenance. | URL, DOI, timestamp, SHA-256 manifest, 1,067,371-row gate. |
| FR-02 | Create customers and items before transactional documents. | REST audit records and ERP source-ID custom fields. |
| FR-03 | Group valid source lines into Sales Invoices. | One document payload per `InvoiceNo`; line-level source IDs. |
| FR-04 | Represent valid cancellations as ERP returns. | Negative quantities, `is_return=1`, and `return_against`. |
| FR-05 | Reject invalid records without silently discarding them. | Rejection parquet with one or more DQ reason codes. |
| FR-06 | Prevent duplicate file and document processing. | Unique source checksum plus source invoice custom field/payload hash. |
| FR-07 | Reconcile row counts and net source revenue. | Batch and control tables; Power BI reconciliation page. |
| FR-08 | Verify submitted invoice GL balance. | SQL query returns no debit/credit variances over £0.01. |
| FR-09 | Enforce preparer/approver segregation of duties. | RBAC matrix and access-conflict query. |
| FR-10 | Support failed-batch restart and recovery. | Persistent volumes, per-document audit, replay test. |

## Non-functional requirements

- Secrets are supplied only through ignored environment files.
- The raw dataset is checksum-controlled and not committed to Git.
- Validation of 1,067,371 rows must be vectorized and repeatable.
- Default migration mode creates drafts; document submission requires explicit configuration.
- All correction logic must be version controlled; raw source values remain unchanged.
- Dashboard outputs contain aggregate control evidence and no direct customer identity.

## Exit criteria

1. All automated tests pass.
2. The published source count gate passes.
3. Source rows equal accepted plus rejected rows.
4. Every rejection has a documented reason code.
5. Controlled UAT sample migration completes with no duplicate documents.
6. Submitted sample invoices show balanced GL entries.
7. Return, approval, recovery, and period-close scenarios have evidence.

