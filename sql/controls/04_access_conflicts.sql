-- Segregation-of-duties conflicts: no user may both create and approve invoices.
SELECT user_id,
       STRING_AGG(role_name, ', ' ORDER BY role_name) AS conflicting_roles
FROM access_assignment
WHERE active AND role_name IN ('OTC Invoice Preparer', 'OTC Invoice Approver')
GROUP BY user_id
HAVING COUNT(DISTINCT role_name) = 2;

