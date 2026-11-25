BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 0001

CREATE TABLE admin_users (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    email VARCHAR(254) NOT NULL, 
    password_hash VARCHAR(255) NOT NULL, 
    role VARCHAR(20) NOT NULL, 
    is_active BOOLEAN DEFAULT true NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    CONSTRAINT pk_admin_users PRIMARY KEY (id), 
    CONSTRAINT ck_admin_users_role_allowed CHECK (role IN ('admin')), 
    CONSTRAINT uq_admin_users_email UNIQUE (email)
);

CREATE TABLE datasets (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    original_filename VARCHAR(255) NOT NULL, 
    storage_path VARCHAR(512) NOT NULL, 
    sha256 VARCHAR(64) NOT NULL, 
    row_count INTEGER NOT NULL, 
    size_bytes BIGINT NOT NULL, 
    validation_report JSONB NOT NULL, 
    uploaded_by UUID, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    CONSTRAINT pk_datasets PRIMARY KEY (id), 
    CONSTRAINT ck_datasets_sha256_length CHECK (char_length(sha256) = 64), 
    CONSTRAINT ck_datasets_row_count_positive CHECK (row_count > 0), 
    CONSTRAINT ck_datasets_size_bytes_positive CHECK (size_bytes > 0), 
    CONSTRAINT fk_datasets_uploaded_by_admin_users FOREIGN KEY(uploaded_by) REFERENCES admin_users (id) ON DELETE RESTRICT, 
    CONSTRAINT uq_datasets_sha256 UNIQUE (sha256), 
    CONSTRAINT uq_datasets_storage_path UNIQUE (storage_path)
);

CREATE TABLE training_jobs (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    dataset_id UUID NOT NULL, 
    status VARCHAR(20) DEFAULT 'PENDING' NOT NULL, 
    attempts SMALLINT DEFAULT 0 NOT NULL, 
    error_message TEXT, 
    requested_by UUID NOT NULL, 
    started_at TIMESTAMP WITH TIME ZONE, 
    heartbeat_at TIMESTAMP WITH TIME ZONE, 
    finished_at TIMESTAMP WITH TIME ZONE, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    CONSTRAINT pk_training_jobs PRIMARY KEY (id), 
    CONSTRAINT ck_training_jobs_status_allowed CHECK (status IN ('PENDING', 'RUNNING', 'SUCCEEDED', 'FAILED', 'TIMED_OUT')), 
    CONSTRAINT ck_training_jobs_attempts_range CHECK (attempts BETWEEN 0 AND 3), 
    CONSTRAINT fk_training_jobs_dataset_id_datasets FOREIGN KEY(dataset_id) REFERENCES datasets (id) ON DELETE RESTRICT, 
    CONSTRAINT fk_training_jobs_requested_by_admin_users FOREIGN KEY(requested_by) REFERENCES admin_users (id) ON DELETE RESTRICT
);

CREATE INDEX ix_training_jobs_dataset_id ON training_jobs (dataset_id);

CREATE INDEX ix_training_jobs_status_created_at ON training_jobs (status, created_at);

CREATE UNIQUE INDEX uq_training_jobs_single_running ON training_jobs ((true)) WHERE status = 'RUNNING';

CREATE TABLE model_versions (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    version VARCHAR(20) NOT NULL, 
    dataset_id UUID NOT NULL, 
    training_job_id UUID, 
    algorithm VARCHAR(100) NOT NULL, 
    hyperparameters JSONB NOT NULL, 
    metrics JSONB NOT NULL, 
    acceptance_report JSONB NOT NULL, 
    dependencies JSONB NOT NULL, 
    preprocessing_version VARCHAR(20) NOT NULL, 
    random_seed INTEGER NOT NULL, 
    artifact_path VARCHAR(512) NOT NULL, 
    artifact_sha256 VARCHAR(64) NOT NULL, 
    status VARCHAR(20) NOT NULL, 
    trained_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    activated_at TIMESTAMP WITH TIME ZONE, 
    CONSTRAINT pk_model_versions PRIMARY KEY (id), 
    CONSTRAINT ck_model_versions_status_allowed CHECK (status IN ('CANDIDATE', 'APPROVED', 'REJECTED', 'ACTIVE', 'RETIRED')), 
    CONSTRAINT ck_model_versions_artifact_sha256_length CHECK (char_length(artifact_sha256) = 64), 
    CONSTRAINT fk_model_versions_dataset_id_datasets FOREIGN KEY(dataset_id) REFERENCES datasets (id) ON DELETE RESTRICT, 
    CONSTRAINT fk_model_versions_training_job_id_training_jobs FOREIGN KEY(training_job_id) REFERENCES training_jobs (id) ON DELETE RESTRICT, 
    CONSTRAINT uq_model_versions_artifact_path UNIQUE (artifact_path), 
    CONSTRAINT uq_model_versions_training_job_id UNIQUE (training_job_id), 
    CONSTRAINT uq_model_versions_version UNIQUE (version)
);

CREATE INDEX ix_model_versions_dataset_id ON model_versions (dataset_id);

CREATE INDEX ix_model_versions_status ON model_versions (status);

CREATE UNIQUE INDEX uq_model_versions_single_active ON model_versions ((true)) WHERE status = 'ACTIVE';

CREATE TABLE model_activation_events (
    id BIGSERIAL NOT NULL, 
    model_version_id UUID NOT NULL, 
    previous_model_version_id UUID, 
    action VARCHAR(20) NOT NULL, 
    performed_by UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    CONSTRAINT pk_model_activation_events PRIMARY KEY (id), 
    CONSTRAINT ck_model_activation_events_action_allowed CHECK (action IN ('ACTIVATE', 'ROLLBACK')), 
    CONSTRAINT fk_model_activation_events_model_version_id_model_versions FOREIGN KEY(model_version_id) REFERENCES model_versions (id) ON DELETE RESTRICT, 
    CONSTRAINT fk_model_activation_events_performed_by_admin_users FOREIGN KEY(performed_by) REFERENCES admin_users (id) ON DELETE RESTRICT, 
    CONSTRAINT fk_model_activation_events_previous_model_version_id_mo_291e FOREIGN KEY(previous_model_version_id) REFERENCES model_versions (id) ON DELETE RESTRICT
);

CREATE INDEX ix_model_activation_events_model_version_id ON model_activation_events (model_version_id);

CREATE TABLE predictions (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    model_version_id UUID NOT NULL, 
    input_features JSONB NOT NULL, 
    predicted_class SMALLINT NOT NULL, 
    probability NUMERIC(5, 4) NOT NULL, 
    risk_band VARCHAR(10) NOT NULL, 
    latency_ms INTEGER NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    CONSTRAINT pk_predictions PRIMARY KEY (id), 
    CONSTRAINT ck_predictions_risk_band_allowed CHECK (risk_band IN ('LOW', 'MODERATE', 'HIGH')), 
    CONSTRAINT ck_predictions_latency_non_negative CHECK (latency_ms >= 0), 
    CONSTRAINT ck_predictions_predicted_class_binary CHECK (predicted_class IN (0, 1)), 
    CONSTRAINT ck_predictions_probability_range CHECK (probability BETWEEN 0 AND 1), 
    CONSTRAINT fk_predictions_model_version_id_model_versions FOREIGN KEY(model_version_id) REFERENCES model_versions (id) ON DELETE RESTRICT
);

CREATE INDEX ix_predictions_created_at ON predictions (created_at);

CREATE INDEX ix_predictions_model_version_created_at ON predictions (model_version_id, created_at);

INSERT INTO alembic_version (version_num) VALUES ('0001') RETURNING alembic_version.version_num;

-- Running upgrade 0001 -> 0002

ALTER TABLE predictions RENAME latency_ms TO latency_milliseconds;

UPDATE predictions
            SET input_features = (input_features - 'cgpa')
                || jsonb_build_object('grade_point_average', input_features -> 'cgpa')
            WHERE input_features ? 'cgpa';

UPDATE alembic_version SET version_num='0002' WHERE alembic_version.version_num = '0001';

COMMIT;

