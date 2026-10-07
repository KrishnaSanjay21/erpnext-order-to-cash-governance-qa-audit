# UAT and regression test plan

## Test strategy

Python unit tests verify canonicalization, validation, idempotency, payload structure, and master deduplication. UAT executes a deliberately small ERP batch in draft mode, captures ERP document IDs, and then submits only approved evidence documents. Regression reruns automated tests and the source reconciliation after any rule, mapping, ERP version, or workflow change.

## UAT cases

| ID | Scenario | Expected result | Evidence |
|---|---|---|---|
| UAT-001 | Normal sale | Customer/item exist; one draft invoice; source line IDs retained. | ERP JSON export and audit row. |
| UAT-002 | Product return | Negative-quantity return references submitted original invoice. | Return document, `return_against`, GL extract. |
| UAT-003 | Duplicate invoice | Same payload is skipped; changed successful payload opens defect. | Audit shows SKIPPED or FAILED, one ERP invoice. |
| UAT-004 | Invalid customer | Row receives DQ001 and never reaches ERP. | Rejection extract. |
| UAT-005 | Missing item | Row receives DQ003 and never reaches ERP. | Rejection extract. |
| UAT-006 | Unauthorized approval | Preparer cannot approve/submit pending invoice. | Permission error screenshot/log and role extract. |
| UAT-007 | Corrected reprocessing | New checksum creates a new batch; prior batch remains immutable. | Two batch rows and correction record. |
| UAT-008 | Period close | Posting to frozen/closed date fails for non-authorized user. | ERP error and unchanged GL. |
| UAT-009 | Failed and successful recovery | Restart skips successes and retries failures without duplicates. | Before/after migration audit. |
| UAT-010 | Balanced accounting | Each submitted invoice has debit equal credit within £0.01. | GL balance query returns zero exceptions. |

## Regression cases

| ID | Trigger | Assertion |
|---|---|---|
| REG-001 | Parser or dependency change | Published workbook still loads exactly 1,067,371 rows. |
| REG-002 | Validation change | Accepted + rejected equals source; every rejected row has reasons. |
| REG-003 | Mapping change | Payload fixture retains customer, item, amount, batch, and row lineage. |
| REG-004 | ERP image change | Compose validates; setup script creates all fields and roles. |
| REG-005 | Replay | Same archive checksum returns existing batch ID; successful document is skipped. |
| REG-006 | Dashboard change | All measures preserve filter context and reconciliation variance remains visible. |

## Evidence status conventions

- **PASS**: observed result equals expectation and evidence is attached.
- **FAIL**: expectation not met; defect required.
- **BLOCKED**: environment or upstream dependency unavailable; not counted as a pass.
- **NOT RUN**: execution has not begun. Never report NOT RUN/BLOCKED as passed.

## Live execution evidence — 2026-10-07

| ID | Status | Observed evidence |
|---|---|---|
| UAT-001 | PASS | Submitted `ACC-SINV-2026-00001`; source and batch lineage retained. |
| UAT-002 | PASS | Submitted `ACC-SINV-2026-00002`; linked to the original with `return_against`. |
| UAT-006 | PASS | `otc.integration@example.com` returned false for Sales Invoice submit permission. |
| UAT-010 | PASS | Both documents produced three active GL lines and a £0.00 debit-credit difference. |

The other UAT cases remain **NOT RUN** in ERP unless separately supported by the source-validation or automated-test evidence. Results are documented in `docs/11_live_verification_report.md`.

