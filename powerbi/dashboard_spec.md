# Dashboard specification

## Page 1 — Executive governance

- KPI cards: source rows, accepted rows, rejected rows, acceptance rate, accepted net revenue, reconciliation status.
- Monthly stacked columns: accepted/rejected rows; overlay signed revenue.
- Control-status strip: source count, row disposition, ERP document count, revenue, GL balance, return links, access conflicts.
- Prominent status: **LIVE ERP UAT PASS / FULL POPULATION NOT RUN** until complete migration extracts are loaded.

## Page 2 — Data quality

- Ranked bars: failed rows by control ID.
- Trend: failures by month and control.
- Matrix: control, severity, observed count, remediation owner, status.
- Drillthrough: document disposition, reason codes, source lineage (restricted analyst view).

## Page 3 — Reconciliation

- Waterfall: source revenue → rejected sales → rejected returns → accepted ERP scope.
- Cards: source documents, accepted documents, migrated documents, submitted documents.
- Variance table: source versus ERP count and signed amount by month/document type.
- GL balance exception table and return-to-original coverage.

## Page 4 — Defects and UAT

- Open defects by severity and age.
- UAT completion matrix by requirement and execution status.
- Failed batches and last successful recovery.
- QA completion gauge calculated from PASS/(PASS+FAIL), excluding NOT RUN/BLOCKED.

Slicers: batch ID, year/month, document type, country, control, severity, and status. Use red only for failures, amber for warnings/not run, teal for passed controls, and navy for neutral context.

