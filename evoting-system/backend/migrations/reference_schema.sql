-- ============================================================
-- REFERENCE SCHEMA — Neon PostgreSQL
-- ============================================================
-- This file is a human-readable reference matching app/models/*.py.
-- It is NOT run directly — Alembic ("flask db migrate") generates the
-- real, versioned migration from the SQLAlchemy models. Keep this in
-- sync manually if you hand-edit models without regenerating.
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto"; -- for gen_random_uuid(), if needed outside SQLAlchemy

-- ---------- ENUM TYPES ----------
CREATE TYPE election_status AS ENUM ('draft','scheduled','live','paused','closed');
CREATE TYPE fraud_type AS ENUM (
    'multiple_faces','face_mismatch','fingerprint_mismatch','duplicate_vote',
    'multiple_sessions','multiple_devices','excessive_failed_attempts',
    'liveness_failure','vpn_detected','other'
);
CREATE TYPE fraud_severity AS ENUM ('low','medium','high','critical');
CREATE TYPE actor_type AS ENUM ('super_admin','election_admin','voter','system');
CREATE TYPE session_user_type AS ENUM ('admin','election_admin','voter');

-- ---------- ADMINS ----------
CREATE TABLE admins (
    id UUID PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX ix_admins_email ON admins(email);

-- ---------- ELECTION ADMINS ----------
CREATE TABLE election_admins (
    id UUID PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX ix_election_admins_email ON election_admins(email);

-- ---------- VOTERS ----------
CREATE TABLE voters (
    id UUID PRIMARY KEY,
    voter_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(120) NOT NULL,
    dob DATE NOT NULL,
    gender VARCHAR(20),
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    address TEXT,
    password_hash VARCHAR(255) NOT NULL,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    has_face_registered BOOLEAN NOT NULL DEFAULT FALSE,
    has_fingerprint_registered BOOLEAN NOT NULL DEFAULT FALSE,
    failed_login_attempts INTEGER NOT NULL DEFAULT 0,
    account_locked_until TIMESTAMPTZ,
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX ix_voters_voter_id ON voters(voter_id);
CREATE INDEX ix_voters_email ON voters(email);
CREATE INDEX ix_voters_locked_until ON voters(account_locked_until);

-- ---------- ELECTIONS ----------
CREATE TABLE elections (
    id UUID PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    start_date TIMESTAMPTZ NOT NULL,
    end_date TIMESTAMPTZ NOT NULL,
    status election_status NOT NULL DEFAULT 'draft',
    created_by_id UUID REFERENCES election_admins(id),
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT ck_election_dates_valid CHECK (end_date > start_date)
);
CREATE INDEX ix_elections_status ON elections(status);

-- ---------- ELECTION <-> ELECTION_ADMIN (assignment) ----------
CREATE TABLE election_admin_assignments (
    election_admin_id UUID REFERENCES election_admins(id) ON DELETE CASCADE,
    election_id UUID REFERENCES elections(id) ON DELETE CASCADE,
    PRIMARY KEY (election_admin_id, election_id)
);

-- ---------- ELECTION <-> VOTER (eligibility) ----------
CREATE TABLE election_eligible_voters (
    voter_id UUID REFERENCES voters(id) ON DELETE CASCADE,
    election_id UUID REFERENCES elections(id) ON DELETE CASCADE,
    PRIMARY KEY (voter_id, election_id)
);

-- ---------- CANDIDATES ----------
CREATE TABLE candidates (
    id UUID PRIMARY KEY,
    election_id UUID NOT NULL REFERENCES elections(id) ON DELETE CASCADE,
    name VARCHAR(120) NOT NULL,
    party VARCHAR(120),
    photo_url VARCHAR(500),
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX ix_candidates_election_id ON candidates(election_id);

-- ---------- VOTES ----------
CREATE TABLE votes (
    id UUID PRIMARY KEY,
    election_id UUID NOT NULL REFERENCES elections(id) ON DELETE CASCADE,
    candidate_id UUID NOT NULL REFERENCES candidates(id),
    voter_id UUID NOT NULL REFERENCES voters(id),
    encrypted_vote_hash VARCHAR(128) NOT NULL,
    cast_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT uq_one_vote_per_election UNIQUE (voter_id, election_id)
);
CREATE INDEX ix_votes_election_id ON votes(election_id);

-- ---------- BLOCKCHAIN ----------
CREATE TABLE blockchain (
    id UUID PRIMARY KEY,
    block_index INTEGER UNIQUE NOT NULL,
    previous_hash CHAR(64) NOT NULL,
    current_hash CHAR(64) UNIQUE NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    nonce INTEGER NOT NULL DEFAULT 0,
    election_id UUID NOT NULL REFERENCES elections(id),
    candidate_id UUID NOT NULL REFERENCES candidates(id),
    encrypted_vote_hash VARCHAR(128) NOT NULL,
    transaction_id UUID UNIQUE NOT NULL,
    vote_id UUID UNIQUE NOT NULL REFERENCES votes(id)
);
CREATE INDEX ix_blockchain_block_index ON blockchain(block_index);
CREATE INDEX ix_blockchain_current_hash ON blockchain(current_hash);
CREATE INDEX ix_blockchain_election_id ON blockchain(election_id);
CREATE INDEX ix_blockchain_transaction_id ON blockchain(transaction_id);

-- ---------- FRAUD LOGS ----------
CREATE TABLE fraud_logs (
    id UUID PRIMARY KEY,
    voter_id UUID REFERENCES voters(id),
    election_id UUID REFERENCES elections(id),
    fraud_type fraud_type NOT NULL,
    severity fraud_severity NOT NULL DEFAULT 'medium',
    fraud_score INTEGER NOT NULL DEFAULT 0,
    description TEXT,
    ip_address VARCHAR(64),
    device_fingerprint VARCHAR(255),
    is_resolved BOOLEAN NOT NULL DEFAULT FALSE,
    resolved_by_id UUID,
    resolved_at TIMESTAMPTZ,
    resolution_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX ix_fraud_logs_voter_id ON fraud_logs(voter_id);
CREATE INDEX ix_fraud_logs_severity ON fraud_logs(severity);

-- ---------- AUDIT LOGS ----------
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY,
    actor_type actor_type NOT NULL,
    actor_id UUID,
    action VARCHAR(100) NOT NULL,
    details JSONB,
    ip_address VARCHAR(64),
    user_agent VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX ix_audit_logs_action ON audit_logs(action);
CREATE INDEX ix_audit_logs_actor ON audit_logs(actor_type, actor_id);
CREATE INDEX ix_audit_logs_created_at ON audit_logs(created_at);

-- ---------- FINGERPRINT TEMPLATES ----------
CREATE TABLE fingerprint_templates (
    id UUID PRIMARY KEY,
    voter_id UUID UNIQUE NOT NULL REFERENCES voters(id) ON DELETE CASCADE,
    auth_method VARCHAR(20) NOT NULL DEFAULT 'webauthn',
    credential_id VARCHAR(500) UNIQUE,
    public_key TEXT,
    sign_count INTEGER NOT NULL DEFAULT 0,
    template_data BYTEA,
    device_info VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

-- ---------- FACE EMBEDDINGS ----------
CREATE TABLE face_embeddings (
    id UUID PRIMARY KEY,
    voter_id UUID UNIQUE NOT NULL REFERENCES voters(id) ON DELETE CASCADE,
    encrypted_embedding BYTEA NOT NULL,
    embedding_model VARCHAR(50) NOT NULL DEFAULT 'insightface-buffalo_l',
    sample_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

-- ---------- SESSIONS ----------
CREATE TABLE sessions (
    id UUID PRIMARY KEY,
    voter_id UUID REFERENCES voters(id) ON DELETE CASCADE,
    admin_id UUID,
    user_type session_user_type NOT NULL,
    refresh_token_hash VARCHAR(128) UNIQUE NOT NULL,
    device_fingerprint VARCHAR(255),
    ip_address VARCHAR(64),
    user_agent VARCHAR(255),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX ix_sessions_voter_active ON sessions(voter_id, is_active);
