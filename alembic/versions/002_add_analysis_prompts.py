"""Add analysis prompts table

Revision ID: 002
Revises: 001
Create Date: 2024-01-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create prompt_type enum
    op.execute("""
        CREATE TYPE prompttype AS ENUM (
            'quality_score', 'summary', 'emotion',
            'flow_classification', 'flow_compliance', 'custom'
        )
    """)

    # Create analysis_prompts table
    op.create_table(
        "analysis_prompts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column(
            "prompt_type",
            sa.Enum(
                "quality_score", "summary", "emotion",
                "flow_classification", "flow_compliance", "custom",
                name="prompttype",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(length=1000), nullable=True),
        sa.Column("prompt_text", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("is_default", sa.Boolean(), nullable=False, default=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_analysis_prompts_tenant_id"), "analysis_prompts", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_analysis_prompts_prompt_type"), "analysis_prompts", ["prompt_type"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_analysis_prompts_prompt_type"), table_name="analysis_prompts")
    op.drop_index(op.f("ix_analysis_prompts_tenant_id"), table_name="analysis_prompts")
    op.drop_table("analysis_prompts")
    op.execute("DROP TYPE IF EXISTS prompttype")
