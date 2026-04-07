"""Initial schema

Revision ID: 001
Revises:
Create Date: 2025-01-01 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(64), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column(
            "role",
            sa.Enum("admin", "user", name="userrole"),
            nullable=False,
            server_default="user",
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_id"), "users", ["id"])
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "coaches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("region", sa.String(100), nullable=False),
        sa.Column("sport_type", sa.String(100), nullable=False),
        sa.Column("experience_years", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_coaches_id"), "coaches", ["id"])
    op.create_index(op.f("ix_coaches_full_name"), "coaches", ["full_name"])
    op.create_index(op.f("ix_coaches_sport_type"), "coaches", ["sport_type"])

    op.create_table(
        "athletes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("birth_date", sa.Date(), nullable=False),
        sa.Column("region", sa.String(100), nullable=False),
        sa.Column("sport_type", sa.String(100), nullable=False),
        sa.Column("rank", sa.String(100), nullable=True),
        sa.Column("coach_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["coach_id"], ["coaches.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_athletes_id"), "athletes", ["id"])
    op.create_index(op.f("ix_athletes_full_name"), "athletes", ["full_name"])
    op.create_index(op.f("ix_athletes_region"), "athletes", ["region"])
    op.create_index(op.f("ix_athletes_sport_type"), "athletes", ["sport_type"])
    op.create_index(op.f("ix_athletes_coach_id"), "athletes", ["coach_id"])

    op.create_table(
        "competitions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("location", sa.String(200), nullable=False),
        sa.Column("sport_type", sa.String(100), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_competitions_id"), "competitions", ["id"])
    op.create_index(op.f("ix_competitions_date"), "competitions", ["date"])
    op.create_index(op.f("ix_competitions_sport_type"), "competitions", ["sport_type"])

    op.create_table(
        "results",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("athlete_id", sa.Integer(), nullable=False),
        sa.Column("competition_id", sa.Integer(), nullable=False),
        sa.Column("place", sa.Integer(), nullable=True),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["athlete_id"], ["athletes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["competition_id"], ["competitions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_results_id"), "results", ["id"])
    op.create_index(op.f("ix_results_athlete_id"), "results", ["athlete_id"])
    op.create_index(op.f("ix_results_competition_id"), "results", ["competition_id"])
    op.create_index(op.f("ix_results_year"), "results", ["year"])

    op.create_table(
        "chat_sessions",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(200), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_chat_sessions_user_id"), "chat_sessions", ["user_id"])

    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.String(36), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("context_used", sa.Text(), nullable=True),
        sa.Column("tokens_used", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["session_id"], ["chat_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_chat_messages_id"), "chat_messages", ["id"])
    op.create_index(op.f("ix_chat_messages_session_id"), "chat_messages", ["session_id"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource", sa.String(100), nullable=True),
        sa.Column("resource_id", sa.Integer(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_logs_id"), "audit_logs", ["id"])
    op.create_index(op.f("ix_audit_logs_user_id"), "audit_logs", ["user_id"])
    op.create_index(op.f("ix_audit_logs_action"), "audit_logs", ["action"])
    op.create_index(op.f("ix_audit_logs_created_at"), "audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("chat_messages")
    op.drop_table("chat_sessions")
    op.drop_table("results")
    op.drop_table("competitions")
    op.drop_table("athletes")
    op.drop_table("coaches")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS userrole")
