WITH source AS (
    SELECT * FROM read_parquet($source_path)
)
SELECT 'DQ001' AS control_id, 'Missing customer identifiers' AS control_name,
       COUNT(*) FILTER (WHERE customer_id IS NULL OR customer_id = '') AS failed_rows
FROM source
UNION ALL
SELECT 'DQ002', 'Missing invoice identifiers',
       COUNT(*) FILTER (WHERE invoice_no IS NULL OR invoice_no = '')
FROM source
UNION ALL
SELECT 'DQ003', 'Missing item identifiers',
       COUNT(*) FILTER (WHERE stock_code IS NULL OR stock_code = '')
FROM source
UNION ALL
SELECT 'DQ004', 'Invalid invoice timestamps',
       COUNT(*) FILTER (WHERE invoice_date IS NULL)
FROM source
UNION ALL
SELECT 'DQ005', 'Zero quantities',
       COUNT(*) FILTER (WHERE quantity IS NULL OR quantity = 0)
FROM source
UNION ALL
SELECT 'DQ006', 'Non-positive prices',
       COUNT(*) FILTER (WHERE unit_price IS NULL OR unit_price <= 0)
FROM source;

