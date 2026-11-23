"""Esquema inicial: usuarios admin, datasets, trabajos, versiones de modelo y predicciones.

Revision ID: 0001
Revises:
Create Date: 2026-11-23 22:42:39.104933+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "admin_users",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("role IN ('admin')", name=op.f("ck_admin_users_role_allowed")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_admin_users")),
        sa.UniqueConstraint("email", name=op.f("uq_admin_users_email")),
    )
    op.create_table(
        "datasets",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("storage_path", sa.String(length=512), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("validation_report", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("uploaded_by", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("char_length(sha256) = 64", name=op.f("ck_datasets_sha256_length")),
        sa.CheckConstraint("row_count > 0", name=op.f("ck_datasets_row_count_positive")),
        sa.CheckConstraint("size_bytes > 0", name=op.f("ck_datasets_size_bytes_positive")),
        sa.ForeignKeyConstraint(
            ["uploaded_by"],
            ["admin_users.id"],
            name=op.f("fk_datasets_uploaded_by_admin_users"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_datasets")),
        sa.UniqueConstraint("sha256", name=op.f("uq_datasets_sha256")),
        sa.UniqueConstraint("storage_path", name=op.f("uq_datasets_storage_path")),
    )
    op.create_table(
        "training_jobs",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("dataset_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="PENDING", nullable=False),
        sa.Column("attempts", sa.SmallInteger(), server_default=sa.text("0"), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("requested_by", sa.Uuid(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('PENDING', 'RUNNING', 'SUCCEEDED', 'FAILED', 'TIMED_OUT')",
            name=op.f("ck_training_jobs_status_allowed"),
        ),
        sa.CheckConstraint(
            "attempts BETWEEN 0 AND 3", name=op.f("ck_training_jobs_attempts_range")
        ),
        sa.ForeignKeyConstraint(
            ["dataset_id"],
            ["datasets.id"],
            name=op.f("fk_training_jobs_dataset_id_datasets"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["requested_by"],
            ["admin_users.id"],
            name=op.f("fk_training_jobs_requested_by_admin_users"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_training_jobs")),
    )
    op.create_index(
        op.f("ix_training_jobs_dataset_id"), "training_jobs", ["dataset_id"], unique=False
    )
    op.create_index(
        "ix_training_jobs_status_created_at",
        "training_jobs",
        ["status", "created_at"],
        unique=False,
    )
    op.create_index(
        "uq_training_jobs_single_running",
        "training_jobs",
        [sa.literal_column("(true)")],
        unique=True,
        postgresql_where=sa.text("status = 'RUNNING'"),
    )
    op.create_table(
        "model_versions",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("version", sa.String(length=20), nullable=False),
        sa.Column("dataset_id", sa.Uuid(), nullable=False),
        sa.Column("training_job_id", sa.Uuid(), nullable=True),
        sa.Column("algorithm", sa.String(length=100), nullable=False),
        sa.Column("hyperparameters", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("metrics", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("acceptance_report", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("dependencies", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("preprocessing_version", sa.String(length=20), nullable=False),
        sa.Column("random_seed", sa.Integer(), nullable=False),
        sa.Column("artifact_path", sa.String(length=512), nullable=False),
        sa.Column("artifact_sha256", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("trained_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('CANDIDATE', 'APPROVED', 'REJECTED', 'ACTIVE', 'RETIRED')",
            name=op.f("ck_model_versions_status_allowed"),
        ),
        sa.CheckConstraint(
            "char_length(artifact_sha256) = 64",
            name=op.f("ck_model_versions_artifact_sha256_length"),
        ),
        sa.ForeignKeyConstraint(
            ["dataset_id"],
            ["datasets.id"],
            name=op.f("fk_model_versions_dataset_id_datasets"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["training_job_id"],
            ["training_jobs.id"],
            name=op.f("fk_model_versions_training_job_id_training_jobs"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_model_versions")),
        sa.UniqueConstraint("artifact_path", name=op.f("uq_model_versions_artifact_path")),
        sa.UniqueConstraint("training_job_id", name=op.f("uq_model_versions_training_job_id")),
        sa.UniqueConstraint("version", name=op.f("uq_model_versions_version")),
    )
    op.create_index(
        op.f("ix_model_versions_dataset_id"), "model_versions", ["dataset_id"], unique=False
    )
    op.create_index(op.f("ix_model_versions_status"), "model_versions", ["status"], unique=False)
    op.create_index(
        "uq_model_versions_single_active",
        "model_versions",
        [sa.literal_column("(true)")],
        unique=True,
        postgresql_where=sa.text("status = 'ACTIVE'"),
    )
    op.create_table(
        "model_activation_events",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("model_version_id", sa.Uuid(), nullable=False),
        sa.Column("previous_model_version_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.String(length=20), nullable=False),
        sa.Column("performed_by", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "action IN ('ACTIVATE', 'ROLLBACK')",
            name=op.f("ck_model_activation_events_action_allowed"),
        ),
        sa.ForeignKeyConstraint(
            ["model_version_id"],
            ["model_versions.id"],
            name=op.f("fk_model_activation_events_model_version_id_model_versions"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["performed_by"],
            ["admin_users.id"],
            name=op.f("fk_model_activation_events_performed_by_admin_users"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["previous_model_version_id"],
            ["model_versions.id"],
            name=op.f("fk_model_activation_events_previous_model_version_id_model_versions"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_model_activation_events")),
    )
    op.create_index(
        op.f("ix_model_activation_events_model_version_id"),
        "model_activation_events",
        ["model_version_id"],
        unique=False,
    )
    op.create_table(
        "predictions",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("model_version_id", sa.Uuid(), nullable=False),
        sa.Column("input_features", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("predicted_class", sa.SmallInteger(), nullable=False),
        sa.Column("probability", sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column("risk_band", sa.String(length=10), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "risk_band IN ('LOW', 'MODERATE', 'HIGH')",
            name=op.f("ck_predictions_risk_band_allowed"),
        ),
        sa.CheckConstraint("latency_ms >= 0", name=op.f("ck_predictions_latency_non_negative")),
        sa.CheckConstraint(
            "predicted_class IN (0, 1)", name=op.f("ck_predictions_predicted_class_binary")
        ),
        sa.CheckConstraint(
            "probability BETWEEN 0 AND 1", name=op.f("ck_predictions_probability_range")
        ),
        sa.ForeignKeyConstraint(
            ["model_version_id"],
            ["model_versions.id"],
            name=op.f("fk_predictions_model_version_id_model_versions"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_predictions")),
    )
    op.create_index("ix_predictions_created_at", "predictions", ["created_at"], unique=False)
    op.create_index(
        "ix_predictions_model_version_created_at",
        "predictions",
        ["model_version_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_predictions_model_version_created_at", table_name="predictions")
    op.drop_index("ix_predictions_created_at", table_name="predictions")
    op.drop_table("predictions")
    op.drop_index(
        op.f("ix_model_activation_events_model_version_id"), table_name="model_activation_events"
    )
    op.drop_table("model_activation_events")
    op.drop_index(
        "uq_model_versions_single_active",
        table_name="model_versions",
        postgresql_where=sa.text("status = 'ACTIVE'"),
    )
    op.drop_index(op.f("ix_model_versions_status"), table_name="model_versions")
    op.drop_index(op.f("ix_model_versions_dataset_id"), table_name="model_versions")
    op.drop_table("model_versions")
    op.drop_index(
        "uq_training_jobs_single_running",
        table_name="training_jobs",
        postgresql_where=sa.text("status = 'RUNNING'"),
    )
    op.drop_index("ix_training_jobs_status_created_at", table_name="training_jobs")
    op.drop_index(op.f("ix_training_jobs_dataset_id"), table_name="training_jobs")
    op.drop_table("training_jobs")
    op.drop_table("datasets")
    op.drop_table("admin_users")
