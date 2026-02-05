"""Initial migration

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create tenants table
    op.create_table(
        "tenants",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("biztel_api_key", sqlmodel.sql.sqltypes.AutoString(length=512), nullable=True),
        sa.Column("biztel_api_secret", sqlmodel.sql.sqltypes.AutoString(length=512), nullable=True),
        sa.Column("biztel_base_url", sqlmodel.sql.sqltypes.AutoString(length=512), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tenants_name"), "tenants", ["name"], unique=False)

    # Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("email", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("password_hash", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column("google_id", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column("role", sa.Enum("ADMIN", "SV", "QA", "OPERATOR", "EXECUTIVE", name="userrole"), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("google_id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_tenant_id"), "users", ["tenant_id"], unique=False)

    # Create operators table
    op.create_table(
        "operators",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("biztel_operator_id", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_operators_biztel_operator_id"), "operators", ["biztel_operator_id"], unique=False)
    op.create_index(op.f("ix_operators_tenant_id"), "operators", ["tenant_id"], unique=False)

    # Create operation_flows table
    op.create_table(
        "operation_flows",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("classification_criteria", sa.Text(), nullable=True),
        sa.Column("flow_definition", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_operation_flows_tenant_id"), "operation_flows", ["tenant_id"], unique=False)

    # Create call_records table
    op.create_table(
        "call_records",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("biztel_id", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column("request_id", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column("event_datetime", sa.DateTime(), nullable=False),
        sa.Column("call_center_name", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column("call_center_extension", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=True),
        sa.Column("business_label", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column("operator_id", sa.UUID(), nullable=True),
        sa.Column("operation_flow_id", sa.UUID(), nullable=True),
        sa.Column("inquiry_category", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column("event_type", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=True),
        sa.Column("caller_number", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=True),
        sa.Column("callee_number", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=True),
        sa.Column("wait_time_seconds", sa.Integer(), nullable=True),
        sa.Column("talk_time_seconds", sa.Integer(), nullable=True),
        sa.Column("audio_file_path", sqlmodel.sql.sqltypes.AutoString(length=512), nullable=True),
        sa.Column(
            "analysis_status",
            sa.Enum("PENDING", "PROCESSING", "COMPLETED", "FAILED", name="analysisstatus"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["operator_id"], ["operators.id"]),
        sa.ForeignKeyConstraint(["operation_flow_id"], ["operation_flows.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_call_records_analysis_status"), "call_records", ["analysis_status"], unique=False)
    op.create_index(op.f("ix_call_records_biztel_id"), "call_records", ["biztel_id"], unique=False)
    op.create_index(op.f("ix_call_records_event_datetime"), "call_records", ["event_datetime"], unique=False)
    op.create_index(op.f("ix_call_records_operator_id"), "call_records", ["operator_id"], unique=False)
    op.create_index(op.f("ix_call_records_operation_flow_id"), "call_records", ["operation_flow_id"], unique=False)
    op.create_index(op.f("ix_call_records_request_id"), "call_records", ["request_id"], unique=False)
    op.create_index(op.f("ix_call_records_tenant_id"), "call_records", ["tenant_id"], unique=False)

    # Create analysis_results table
    op.create_table(
        "analysis_results",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("call_record_id", sa.UUID(), nullable=False),
        sa.Column("transcript", sa.Text(), nullable=True),
        sa.Column("flow_compliance", sa.Boolean(), nullable=True),
        sa.Column("compliance_details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("overall_score", sa.Float(), nullable=True),
        sa.Column("fillers_count", sa.Integer(), nullable=True),
        sa.Column("silence_duration", sa.Float(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["call_record_id"], ["call_records.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("call_record_id"),
    )
    op.create_index(op.f("ix_analysis_results_call_record_id"), "analysis_results", ["call_record_id"], unique=True)

    # Create emotion_data table
    op.create_table(
        "emotion_data",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("analysis_id", sa.UUID(), nullable=False),
        sa.Column("timestamp", sa.Float(), nullable=False),
        sa.Column("emotion_type", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("audio_features", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["analysis_id"], ["analysis_results.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_emotion_data_analysis_id"), "emotion_data", ["analysis_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_emotion_data_analysis_id"), table_name="emotion_data")
    op.drop_table("emotion_data")
    op.drop_index(op.f("ix_analysis_results_call_record_id"), table_name="analysis_results")
    op.drop_table("analysis_results")
    op.drop_index(op.f("ix_call_records_tenant_id"), table_name="call_records")
    op.drop_index(op.f("ix_call_records_request_id"), table_name="call_records")
    op.drop_index(op.f("ix_call_records_operation_flow_id"), table_name="call_records")
    op.drop_index(op.f("ix_call_records_operator_id"), table_name="call_records")
    op.drop_index(op.f("ix_call_records_event_datetime"), table_name="call_records")
    op.drop_index(op.f("ix_call_records_biztel_id"), table_name="call_records")
    op.drop_index(op.f("ix_call_records_analysis_status"), table_name="call_records")
    op.drop_table("call_records")
    op.drop_index(op.f("ix_operation_flows_tenant_id"), table_name="operation_flows")
    op.drop_table("operation_flows")
    op.drop_index(op.f("ix_operators_tenant_id"), table_name="operators")
    op.drop_index(op.f("ix_operators_biztel_operator_id"), table_name="operators")
    op.drop_table("operators")
    op.drop_index(op.f("ix_users_tenant_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
    op.drop_index(op.f("ix_tenants_name"), table_name="tenants")
    op.drop_table("tenants")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS userrole")
    op.execute("DROP TYPE IF EXISTS analysisstatus")
