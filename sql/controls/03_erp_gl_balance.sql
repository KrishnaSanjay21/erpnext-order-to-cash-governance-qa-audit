-- Run against a read replica/export of ERPNext's MariaDB database.
-- Zero returned rows is PASS. A tolerance of GBP 0.01 handles currency rounding.
SELECT
    gle.voucher_type,
    gle.voucher_no,
    ROUND(SUM(gle.debit), 2) AS total_debit,
    ROUND(SUM(gle.credit), 2) AS total_credit,
    ROUND(SUM(gle.debit) - SUM(gle.credit), 2) AS variance
FROM `tabGL Entry` AS gle
JOIN `tabSales Invoice` AS si
  ON gle.voucher_type = 'Sales Invoice' AND gle.voucher_no = si.name
WHERE si.custom_migration_batch_id = %(batch_id)s
  AND gle.is_cancelled = 0
GROUP BY gle.voucher_type, gle.voucher_no
HAVING ABS(SUM(gle.debit) - SUM(gle.credit)) > 0.01;

