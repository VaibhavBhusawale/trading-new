"""broker_accounts

Revision ID: 20260320_0002
Revises: 20260320_0001
Create Date: 2026-03-20

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260320_0002"
down_revision: str | None = "20260320_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

broker_provider = postgresql.ENUM(
    "mock",
    "zerodha",
    "angel_one",
    "upstox",
    name="broker_provider",
    create_type=False,
)
broker_account_status = postgresql.ENUM(
    "draft",
    "configured",
    "session_expired",
    "error",
    name="broker_account_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    broker_provider.create(bind, checkfirst=True)
    broker_account_status.create(bind, checkfirst=True)

    # Extend audit_event_type with BROKER if missing
    op.execute("ALTER TYPE audit_event_type ADD VALUE IF NOT EXISTS 'BROKER'")

    op.create_table(
        "broker_accounts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("provider", broker_provider, nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="false", nullable=False),
        sa.Column(
            "status",
            broker_account_status,
            server_default="draft",
            nullable=False,
        ),
        sa.Column("credentials_encrypted", sa.Text(), nullable=True),
        sa.Column("public_meta", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_broker_accounts_provider", "broker_accounts", ["provider"])
    op.create_index("ix_broker_accounts_active", "broker_accounts", ["is_active"])


def downgrade() -> None:
    op.drop_index("ix_broker_accounts_active", table_name="broker_accounts")
    op.drop_index("ix_broker_accounts_provider", table_name="broker_accounts")
    op.drop_table("broker_accounts")
    bind = op.get_bind()
    broker_account_status.drop(bind, checkfirst=True)
    broker_provider.drop(bind, checkfirst=True)
