# Order-to-cash migration process map

```mermaid
flowchart LR
    A[UCI archive] --> B[Checksum and row-count gate]
    B --> C[Canonical source snapshot]
    C --> D{Python validation}
    D -->|Valid| E[Accepted staging]
    D -->|Invalid| F[Rejected staging + reason codes]
    E --> G[Customer and Item upsert]
    G --> H[Draft Sales Invoices]
    H --> I{Approval workflow}
    I -->|Approved| J[Submit / GL posting]
    I -->|Rejected| K[Defect remediation]
    J --> L[ERP extraction]
    F --> M[Audit warehouse]
    K --> M
    L --> M
    M --> N[Reconciliation + controls]
    N --> O[Power BI governance dashboard]
```

## Control points

| Gate | Owner | Preventive/detective | Failure route |
|---|---|---|---|
| Archive SHA-256 uniqueness | Integration operator | Preventive | Stop duplicate batch. |
| Schema and published row count | Data engineer | Preventive | Fail acquisition. |
| Row validation | Data steward | Preventive | Quarantine with DQ codes. |
| Source invoice uniqueness | Integration service | Preventive | Skip same payload; defect on changed payload. |
| Approval workflow | OTC approver | Preventive | Reject to preparer. |
| GL balance | Finance auditor | Detective | High-severity defect and posting hold. |
| Count and revenue reconciliation | Data/finance owners | Detective | Investigate mapping, missing docs, or rounding. |
| Segregation of duties | Security administrator | Preventive/detective | Remove conflicting role before approval. |

