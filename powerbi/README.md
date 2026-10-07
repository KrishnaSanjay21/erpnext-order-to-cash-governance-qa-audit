# Power BI governance dashboard build kit

Power BI Desktop is not installed in the build environment, so this folder is an implementation-ready, source-controlled dashboard specification—not a falsely labeled compiled `.pbix`.

Run `python scripts/build_dashboard_data.py`, create a blank Power BI report, add a text parameter named `DataRoot`, and paste the queries from `powerquery/`. Then add the measures from `measures.dax`, import `theme.json`, and build the pages in `dashboard_spec.md`.

## Refresh contract

1. Run `python -m otc_audit.cli build-audit` after validation/migration reconciliation.
2. Run `python scripts/build_dashboard_data.py`.
3. Refresh Power BI and record the refresh timestamp and batch ID.
4. Do not label ERP controls PASS until `migration_audit` and live GL control results exist.

