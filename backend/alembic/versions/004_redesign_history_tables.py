"""Redesign history tables: v_ prefixed columns + v_date/v_user_id/v_method

Revision ID: 004
Revises: 003
Create Date: 2026-02-27
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ─── Drop old history tables ─────────────────────────────────────────────
    for entity in ["clients", "sites", "users", "visits", "purchases"]:
        op.drop_index(f"idx_{entity}_history_record", f"{entity}_history")
        op.drop_table(f"{entity}_history")

    # ─── clients_history ─────────────────────────────────────────────────────
    op.create_table(
        "clients_history",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("v_id",             UUID(as_uuid=True), nullable=True),
        sa.Column("v_name",           sa.Text(),          nullable=True),
        sa.Column("v_inn",            sa.String(50),      nullable=True),
        sa.Column("v_kpp",            sa.String(50),      nullable=True),
        sa.Column("v_contacts",       sa.Text(),          nullable=True),
        sa.Column("v_contact_person", sa.String(255),     nullable=True),
        sa.Column("v_notes",          sa.Text(),          nullable=True),
        sa.Column("v_is_active",      sa.Boolean(),       nullable=True),
        sa.Column("v_created_at",     sa.DateTime(),      nullable=True),
        sa.Column("v_updated_at",     sa.DateTime(),      nullable=True),
        sa.Column("v_date",    sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("v_user_id", UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("v_method",  sa.String(20), nullable=False),
    )
    op.create_index("idx_clients_history_v_id", "clients_history", ["v_id"])

    # ─── sites_history ───────────────────────────────────────────────────────
    op.create_table(
        "sites_history",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("v_id",               UUID(as_uuid=True), nullable=True),
        sa.Column("v_client_id",         UUID(as_uuid=True), nullable=True),
        sa.Column("v_title",             sa.Text(),          nullable=True),
        sa.Column("v_address",           sa.Text(),          nullable=True),
        sa.Column("v_latitude",          sa.Float(),         nullable=True),
        sa.Column("v_longitude",         sa.Float(),         nullable=True),
        sa.Column("v_access_notes",      sa.Text(),          nullable=True),
        sa.Column("v_onsite_contact",    sa.Text(),          nullable=True),
        sa.Column("v_service_frequency", sa.String(30),      nullable=True),
        sa.Column("v_is_active",         sa.Boolean(),       nullable=True),
        sa.Column("v_created_at",        sa.DateTime(),      nullable=True),
        sa.Column("v_updated_at",        sa.DateTime(),      nullable=True),
        sa.Column("v_date",    sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("v_user_id", UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("v_method",  sa.String(20), nullable=False),
    )
    op.create_index("idx_sites_history_v_id", "sites_history", ["v_id"])

    # ─── users_history ───────────────────────────────────────────────────────
    op.create_table(
        "users_history",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("v_id",            UUID(as_uuid=True), nullable=True),
        sa.Column("v_email",         sa.String(255),     nullable=True),
        sa.Column("v_password_hash", sa.String(255),     nullable=True),
        sa.Column("v_full_name",     sa.String(255),     nullable=True),
        sa.Column("v_phone",         sa.String(50),      nullable=True),
        sa.Column("v_is_active",     sa.Boolean(),       nullable=True),
        sa.Column("v_created_at",    sa.DateTime(),      nullable=True),
        sa.Column("v_updated_at",    sa.DateTime(),      nullable=True),
        sa.Column("v_date",    sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("v_user_id", UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("v_method",  sa.String(20), nullable=False),
    )
    op.create_index("idx_users_history_v_id", "users_history", ["v_id"])

    # ─── visits_history ──────────────────────────────────────────────────────
    op.create_table(
        "visits_history",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("v_id",               UUID(as_uuid=True), nullable=True),
        sa.Column("v_site_id",           UUID(as_uuid=True), nullable=True),
        sa.Column("v_assigned_user_id",  UUID(as_uuid=True), nullable=True),
        sa.Column("v_planned_date",      sa.Date(),          nullable=True),
        sa.Column("v_planned_time_from", sa.Time(),          nullable=True),
        sa.Column("v_planned_time_to",   sa.Time(),          nullable=True),
        sa.Column("v_visit_type",        sa.String(30),      nullable=True),
        sa.Column("v_priority",          sa.String(20),      nullable=True),
        sa.Column("v_status",            sa.String(20),      nullable=True),
        sa.Column("v_work_summary",      sa.Text(),          nullable=True),
        sa.Column("v_checklist",         JSONB(),            nullable=True),
        sa.Column("v_defects_present",   sa.Boolean(),       nullable=True),
        sa.Column("v_defects_summary",   sa.Text(),          nullable=True),
        sa.Column("v_recommendations",   sa.Text(),          nullable=True),
        sa.Column("v_completed_at",      sa.DateTime(),      nullable=True),
        sa.Column("v_office_notes",      sa.Text(),          nullable=True),
        sa.Column("v_created_at",        sa.DateTime(),      nullable=True),
        sa.Column("v_updated_at",        sa.DateTime(),      nullable=True),
        sa.Column("v_date",    sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("v_user_id", UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("v_method",  sa.String(20), nullable=False),
    )
    op.create_index("idx_visits_history_v_id", "visits_history", ["v_id"])

    # ─── purchases_history ───────────────────────────────────────────────────
    op.create_table(
        "purchases_history",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("v_id",        UUID(as_uuid=True), nullable=True),
        sa.Column("v_defect_id", UUID(as_uuid=True), nullable=True),
        sa.Column("v_site_id",   UUID(as_uuid=True), nullable=True),
        sa.Column("v_item",      sa.Text(),          nullable=True),
        sa.Column("v_qty",       sa.Numeric(),       nullable=True),
        sa.Column("v_status",    sa.String(20),      nullable=True),
        sa.Column("v_due_date",  sa.Date(),          nullable=True),
        sa.Column("v_notes",     sa.Text(),          nullable=True),
        sa.Column("v_created_at", sa.DateTime(),     nullable=True),
        sa.Column("v_updated_at", sa.DateTime(),     nullable=True),
        sa.Column("v_date",    sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("v_user_id", UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("v_method",  sa.String(20), nullable=False),
    )
    op.create_index("idx_purchases_history_v_id", "purchases_history", ["v_id"])


def downgrade() -> None:
    for entity in ["clients", "sites", "users", "visits", "purchases"]:
        op.drop_index(f"idx_{entity}_history_v_id", f"{entity}_history")
        op.drop_table(f"{entity}_history")

    # Re-create original JSONB-based history tables
    for entity in ["clients", "sites", "users", "visits", "purchases"]:
        op.create_table(
            f"{entity}_history",
            sa.Column("id", UUID(as_uuid=True), primary_key=True,
                      server_default=sa.text("gen_random_uuid()")),
            sa.Column("record_id", UUID(as_uuid=True), nullable=False),
            sa.Column("changed_by_user_id", UUID(as_uuid=True),
                      sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("changed_at", sa.DateTime(), nullable=False,
                      server_default=sa.text("now()")),
            sa.Column("snapshot", JSONB(), nullable=False),
        )
        op.create_index(f"idx_{entity}_history_record", f"{entity}_history", ["record_id"])
