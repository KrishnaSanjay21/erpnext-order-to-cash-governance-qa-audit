WITH accepted AS (
    SELECT * FROM read_parquet($accepted_path)
), migrated AS (
    SELECT * FROM migration_audit WHERE batch_id = $batch_id AND migration_status = 'SUCCESS'
)
SELECT
    COUNT(*) AS accepted_source_lines,
    COUNT(DISTINCT invoice_no) AS accepted_source_documents,
    ROUND(SUM(line_amount), 2) AS accepted_source_net_revenue_gbp,
    (SELECT COUNT(*) FROM migrated WHERE erp_doctype = 'Sales Invoice') AS migrated_documents;

