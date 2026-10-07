CREATE TABLE IF NOT EXISTS batch_run (
    batch_id VARCHAR PRIMARY KEY,
    source_sha256 VARCHAR NOT NULL UNIQUE,
    source_file VARCHAR NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    status VARCHAR NOT NULL CHECK (status IN ('STARTED','VALIDATED','MIGRATING','COMPLETED','FAILED')),
    source_rows BIGINT,
    accepted_rows BIGINT,
    rejected_rows BIGINT,
    error_message VARCHAR
);

CREATE TABLE IF NOT EXISTS migration_audit (
    batch_id VARCHAR NOT NULL,
    source_document_no VARCHAR NOT NULL,
    document_type VARCHAR NOT NULL,
    erp_doctype VARCHAR NOT NULL,
    erp_document_name VARCHAR,
    payload_hash VARCHAR NOT NULL,
    migration_status VARCHAR NOT NULL,
    http_status INTEGER,
    migrated_at TIMESTAMP,
    response_excerpt VARCHAR,
    PRIMARY KEY (batch_id, source_document_no, erp_doctype)
);

CREATE TABLE IF NOT EXISTS control_result (
    control_run_id VARCHAR NOT NULL,
    batch_id VARCHAR NOT NULL,
    control_id VARCHAR NOT NULL,
    control_name VARCHAR NOT NULL,
    severity VARCHAR NOT NULL,
    observed_value DOUBLE,
    expected_value DOUBLE,
    variance DOUBLE,
    status VARCHAR NOT NULL CHECK (status IN ('PASS','FAIL','WARN')),
    executed_at TIMESTAMP NOT NULL,
    evidence_query VARCHAR,
    PRIMARY KEY (control_run_id, control_id)
);

CREATE TABLE IF NOT EXISTS defect_log (
    defect_id VARCHAR PRIMARY KEY,
    batch_id VARCHAR,
    control_id VARCHAR,
    severity VARCHAR NOT NULL,
    title VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    owner VARCHAR,
    opened_at TIMESTAMP NOT NULL,
    due_at TIMESTAMP,
    remediation VARCHAR,
    closed_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS access_assignment (
    user_id VARCHAR NOT NULL,
    role_name VARCHAR NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    extracted_at TIMESTAMP NOT NULL
);

