CREATE TABLE IF NOT EXISTS master_registry (
 master_reference VARCHAR(64) PRIMARY KEY,
 system_name VARCHAR(128) NOT NULL,
 version VARCHAR(32) NOT NULL,
 status VARCHAR(64) NOT NULL,
 created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS components (
 component_id UUID PRIMARY KEY,
 master_reference VARCHAR(64) NOT NULL REFERENCES master_registry(master_reference),
 component_type VARCHAR(64) NOT NULL,
 owner VARCHAR(255) NOT NULL,
 jurisdiction VARCHAR(32) NOT NULL,
 current_gate VARCHAR(8) NOT NULL,
 lifecycle_state VARCHAR(32) NOT NULL,
 archive_state VARCHAR(32) NOT NULL,
 created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS audit_events (
 event_id UUID PRIMARY KEY,
 master_reference VARCHAR(64) NOT NULL REFERENCES master_registry(master_reference),
 component_id UUID REFERENCES components(component_id),
 actor VARCHAR(255) NOT NULL,
 action VARCHAR(128) NOT NULL,
 previous_state VARCHAR(32),
 new_state VARCHAR(32) NOT NULL,
 sha256_hash CHAR(64) NOT NULL,
 sha512_hash CHAR(128) NOT NULL,
 payload_json JSONB NOT NULL,
 external_receipt JSONB,
 primary_evidence JSONB,
 human_authorisation JSONB,
 exception_json JSONB,
 created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
