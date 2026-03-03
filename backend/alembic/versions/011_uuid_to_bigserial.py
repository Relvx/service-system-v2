"""Replace UUID PKs with BIGSERIAL in all main entity tables.

Revision ID: 011
Revises: 010
Create Date: 2026-03-03

NOTE: This migration drops all transactional data. For dev use only.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "011"
down_revision: Union[str, None] = "010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # ─── Drop history tables (they reference users via FK) ────────────────────
    for tbl in ["purchases_history", "visits_history", "sites_history",
                "users_history", "clients_history"]:
        op.drop_table(tbl)

    # ─── Drop transactional tables (child → parent) ───────────────────────────
    op.drop_table("purchases")
    op.drop_table("notifications")
    op.drop_table("attachments")
    op.drop_table("defects")
    op.drop_table("visits")
    op.drop_table("user_permission_groups")
    op.drop_table("logs")
    op.drop_table("client_legal")
    op.drop_table("client_contacts")
    op.drop_table("sites")
    op.drop_table("clients")
    op.drop_table("users")

    # ─── Recreate with BIGSERIAL PKs (parent → child) ────────────────────────

    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "clients",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("inn", sa.String(50), nullable=True),
        sa.Column("kpp", sa.String(50), nullable=True),
        sa.Column("contacts", sa.Text(), nullable=True),
        sa.Column("contact_person", sa.String(255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_clients_is_archived", "clients", ["is_archived"])

    op.create_table(
        "sites",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("client_id", sa.BigInteger(),
                  sa.ForeignKey("clients.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("address", sa.Text(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("access_notes", sa.Text(), nullable=True),
        sa.Column("onsite_contact", sa.Text(), nullable=True),
        sa.Column("service_frequency", sa.String(30), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("price_maintenance", sa.Float(), nullable=True),
        sa.Column("price_repair", sa.Float(), nullable=True),
        sa.Column("price_emergency", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_sites_is_archived", "sites", ["is_archived"])

    op.create_table(
        "client_contacts",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("client_id", sa.BigInteger(),
                  sa.ForeignKey("clients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("full_name", sa.Text(), nullable=False),
        sa.Column("position", sa.String(100), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("email", sa.String(100), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_client_contacts_client_id", "client_contacts", ["client_id"])

    op.create_table(
        "client_legal",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("client_id", sa.BigInteger(),
                  sa.ForeignKey("clients.id", ondelete="CASCADE"),
                  nullable=False, unique=True),
        sa.Column("legal_address", sa.Text(), nullable=True),
        sa.Column("bank", sa.String(200), nullable=True),
        sa.Column("bik", sa.String(20), nullable=True),
        sa.Column("account", sa.String(30), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "logs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action_sysname", sa.String(50),
                  sa.ForeignKey("log_actions.sysname", ondelete="SET NULL"), nullable=True),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.BigInteger(), nullable=False),
        sa.Column("details", JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_logs_entity", "logs", ["entity_type", "entity_id"])
    op.create_index("idx_logs_user", "logs", ["user_id"])

    op.create_table(
        "user_permission_groups",
        sa.Column("user_id", sa.BigInteger(),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("group_id", sa.Integer(),
                  sa.ForeignKey("permission_groups.id", ondelete="CASCADE"), nullable=False),
        sa.PrimaryKeyConstraint("user_id", "group_id"),
    )

    op.create_table(
        "visits",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("site_id", sa.BigInteger(),
                  sa.ForeignKey("sites.id", ondelete="CASCADE"), nullable=True),
        sa.Column("assigned_user_id", sa.BigInteger(),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("planned_date", sa.Date(), nullable=False),
        sa.Column("planned_time_from", sa.Time(), nullable=True),
        sa.Column("planned_time_to", sa.Time(), nullable=True),
        sa.Column("visit_type", sa.String(30), nullable=False, server_default="maintenance"),
        sa.Column("priority", sa.String(20), nullable=False, server_default="medium"),
        sa.Column("status", sa.String(20), nullable=False, server_default="planned"),
        sa.Column("work_summary", sa.Text(), nullable=True),
        sa.Column("checklist", JSONB(), nullable=True),
        sa.Column("defects_present", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("defects_summary", sa.Text(), nullable=True),
        sa.Column("recommendations", sa.Text(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("office_notes", sa.Text(), nullable=True),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("cost", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_visits_planned_date", "visits", ["planned_date"])
    op.create_index("idx_visits_assigned_user", "visits", ["assigned_user_id"])
    op.create_index("idx_visits_site", "visits", ["site_id"])
    op.create_index("idx_visits_status", "visits", ["status"])
    op.create_index("ix_visits_is_archived", "visits", ["is_archived"])

    op.create_table(
        "defects",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("visit_id", sa.BigInteger(),
                  sa.ForeignKey("visits.id", ondelete="CASCADE"), nullable=True),
        sa.Column("site_id", sa.BigInteger(),
                  sa.ForeignKey("sites.id", ondelete="CASCADE"), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("priority", sa.String(20), nullable=False, server_default="medium"),
        sa.Column("action_type", sa.String(20), nullable=False, server_default="repair"),
        sa.Column("suggested_parts", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "attachments",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("visit_id", sa.BigInteger(),
                  sa.ForeignKey("visits.id", ondelete="CASCADE"), nullable=True),
        sa.Column("kind", sa.String(30), nullable=False, server_default="act_photo"),
        sa.Column("file_url", sa.Text(), nullable=False),
        sa.Column("created_by_user_id", sa.BigInteger(),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "notifications",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("related_visit_id", sa.BigInteger(),
                  sa.ForeignKey("visits.id", ondelete="SET NULL"), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_notifications_user", "notifications", ["user_id"])
    op.create_index("idx_notifications_read", "notifications", ["is_read"])

    op.create_table(
        "purchases",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("defect_id", sa.BigInteger(),
                  sa.ForeignKey("defects.id", ondelete="CASCADE"), nullable=True),
        sa.Column("site_id", sa.BigInteger(),
                  sa.ForeignKey("sites.id", ondelete="SET NULL"), nullable=True),
        sa.Column("item", sa.Text(), nullable=False),
        sa.Column("qty", sa.Numeric(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )

    # ─── History tables ───────────────────────────────────────────────────────

    op.create_table(
        "clients_history",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("v_id",             sa.BigInteger(), nullable=True, index=True),
        sa.Column("v_name",           sa.Text(),       nullable=True),
        sa.Column("v_inn",            sa.String(50),   nullable=True),
        sa.Column("v_kpp",            sa.String(50),   nullable=True),
        sa.Column("v_contacts",       sa.Text(),       nullable=True),
        sa.Column("v_contact_person", sa.String(255),  nullable=True),
        sa.Column("v_notes",          sa.Text(),       nullable=True),
        sa.Column("v_is_active",      sa.Boolean(),    nullable=True),
        sa.Column("v_created_at",     sa.DateTime(),   nullable=True),
        sa.Column("v_updated_at",     sa.DateTime(),   nullable=True),
        sa.Column("changed_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("changed_by_user_id", sa.BigInteger(),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("method", sa.String(20), nullable=False),
    )

    op.create_table(
        "sites_history",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("v_id",               sa.BigInteger(), nullable=True, index=True),
        sa.Column("v_client_id",         sa.BigInteger(), nullable=True),
        sa.Column("v_title",             sa.Text(),       nullable=True),
        sa.Column("v_address",           sa.Text(),       nullable=True),
        sa.Column("v_latitude",          sa.Float(),      nullable=True),
        sa.Column("v_longitude",         sa.Float(),      nullable=True),
        sa.Column("v_access_notes",      sa.Text(),       nullable=True),
        sa.Column("v_onsite_contact",    sa.Text(),       nullable=True),
        sa.Column("v_service_frequency", sa.String(30),   nullable=True),
        sa.Column("v_price_maintenance", sa.Float(),      nullable=True),
        sa.Column("v_price_repair",      sa.Float(),      nullable=True),
        sa.Column("v_price_emergency",   sa.Float(),      nullable=True),
        sa.Column("v_is_active",         sa.Boolean(),    nullable=True),
        sa.Column("v_created_at",        sa.DateTime(),   nullable=True),
        sa.Column("v_updated_at",        sa.DateTime(),   nullable=True),
        sa.Column("changed_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("changed_by_user_id", sa.BigInteger(),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("method", sa.String(20), nullable=False),
    )

    op.create_table(
        "users_history",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("v_id",            sa.BigInteger(), nullable=True, index=True),
        sa.Column("v_email",         sa.String(255),  nullable=True),
        sa.Column("v_password_hash", sa.String(255),  nullable=True),
        sa.Column("v_full_name",     sa.String(255),  nullable=True),
        sa.Column("v_phone",         sa.String(50),   nullable=True),
        sa.Column("v_is_active",     sa.Boolean(),    nullable=True),
        sa.Column("v_created_at",    sa.DateTime(),   nullable=True),
        sa.Column("v_updated_at",    sa.DateTime(),   nullable=True),
        sa.Column("changed_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("changed_by_user_id", sa.BigInteger(),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("method", sa.String(20), nullable=False),
    )

    op.create_table(
        "visits_history",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("v_id",               sa.BigInteger(), nullable=True, index=True),
        sa.Column("v_site_id",           sa.BigInteger(), nullable=True),
        sa.Column("v_assigned_user_id",  sa.BigInteger(), nullable=True),
        sa.Column("v_planned_date",      sa.Date(),       nullable=True),
        sa.Column("v_planned_time_from", sa.Time(),       nullable=True),
        sa.Column("v_planned_time_to",   sa.Time(),       nullable=True),
        sa.Column("v_visit_type",        sa.String(30),   nullable=True),
        sa.Column("v_priority",          sa.String(20),   nullable=True),
        sa.Column("v_status",            sa.String(20),   nullable=True),
        sa.Column("v_work_summary",      sa.Text(),       nullable=True),
        sa.Column("v_checklist",         JSONB(),         nullable=True),
        sa.Column("v_defects_present",   sa.Boolean(),    nullable=True),
        sa.Column("v_defects_summary",   sa.Text(),       nullable=True),
        sa.Column("v_recommendations",   sa.Text(),       nullable=True),
        sa.Column("v_completed_at",      sa.DateTime(),   nullable=True),
        sa.Column("v_office_notes",      sa.Text(),       nullable=True),
        sa.Column("v_cost",              sa.Float(),      nullable=True),
        sa.Column("v_created_at",        sa.DateTime(),   nullable=True),
        sa.Column("v_updated_at",        sa.DateTime(),   nullable=True),
        sa.Column("changed_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("changed_by_user_id", sa.BigInteger(),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("method", sa.String(20), nullable=False),
    )

    op.create_table(
        "purchases_history",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("v_id",         sa.BigInteger(), nullable=True, index=True),
        sa.Column("v_defect_id",  sa.BigInteger(), nullable=True),
        sa.Column("v_site_id",    sa.BigInteger(), nullable=True),
        sa.Column("v_item",       sa.Text(),       nullable=True),
        sa.Column("v_qty",        sa.Numeric(),    nullable=True),
        sa.Column("v_status",     sa.String(20),   nullable=True),
        sa.Column("v_due_date",   sa.Date(),       nullable=True),
        sa.Column("v_notes",      sa.Text(),       nullable=True),
        sa.Column("v_created_at", sa.DateTime(),   nullable=True),
        sa.Column("v_updated_at", sa.DateTime(),   nullable=True),
        sa.Column("changed_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("changed_by_user_id", sa.BigInteger(),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("method", sa.String(20), nullable=False),
    )

    # ─── Re-seed users ────────────────────────────────────────────────────────

    conn.execute(sa.text("""
        INSERT INTO users (email, password_hash, full_name, phone, is_active) VALUES
        ('admin@system.local',
         '$2b$12$IYRa/XTcXPnpTgZ3gjoFxu3NhRA5ig89y0fdmHHq9zIpDP.3UdCHW',
         'Администратор', NULL, true),
        ('master1@system.local',
         '$2b$12$IYRa/XTcXPnpTgZ3gjoFxu3NhRA5ig89y0fdmHHq9zIpDP.3UdCHW',
         'Мастер Иванов', '8-999-111-22-33', true),
        ('master2@system.local',
         '$2b$12$IYRa/XTcXPnpTgZ3gjoFxu3NhRA5ig89y0fdmHHq9zIpDP.3UdCHW',
         'Мастер Петров', '8-999-444-55-66', true),
        ('office1@system.local',
         '$2b$12$IYRa/XTcXPnpTgZ3gjoFxu3NhRA5ig89y0fdmHHq9zIpDP.3UdCHW',
         'Офис Сидоров', '8-495-777-88-99', true)
    """))

    conn.execute(sa.text("""
        INSERT INTO user_permission_groups (user_id, group_id)
        SELECT u.id, pg.id
        FROM users u
        JOIN permission_groups pg ON pg.sysname = CASE u.email
            WHEN 'admin@system.local'   THEN 'admin_group'
            WHEN 'office1@system.local' THEN 'office_group'
            ELSE 'master_group'
        END
    """))


def downgrade() -> None:
    # Drop BIGSERIAL tables in reverse dependency order
    for tbl in ["purchases_history", "visits_history", "sites_history",
                "users_history", "clients_history"]:
        op.drop_table(tbl)

    op.drop_table("purchases")
    op.drop_table("notifications")
    op.drop_table("attachments")
    op.drop_table("defects")
    op.drop_table("visits")
    op.drop_table("user_permission_groups")
    op.drop_table("logs")
    op.drop_table("client_legal")
    op.drop_table("client_contacts")
    op.drop_table("sites")
    op.drop_table("clients")
    op.drop_table("users")

    # Recreate UUID-based tables (010 state, no data preserved)
    from sqlalchemy.dialects.postgresql import UUID

    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "clients",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("inn", sa.String(50), nullable=True),
        sa.Column("kpp", sa.String(50), nullable=True),
        sa.Column("contacts", sa.Text(), nullable=True),
        sa.Column("contact_person", sa.String(255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "sites",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("client_id", UUID(as_uuid=True),
                  sa.ForeignKey("clients.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("address", sa.Text(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("access_notes", sa.Text(), nullable=True),
        sa.Column("onsite_contact", sa.Text(), nullable=True),
        sa.Column("service_frequency", sa.String(30), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("price_maintenance", sa.Float(), nullable=True),
        sa.Column("price_repair", sa.Float(), nullable=True),
        sa.Column("price_emergency", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "client_contacts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("client_id", UUID(as_uuid=True),
                  sa.ForeignKey("clients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("full_name", sa.Text(), nullable=False),
        sa.Column("position", sa.String(100), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("email", sa.String(100), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "client_legal",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("client_id", UUID(as_uuid=True),
                  sa.ForeignKey("clients.id", ondelete="CASCADE"),
                  nullable=False, unique=True),
        sa.Column("legal_address", sa.Text(), nullable=True),
        sa.Column("bank", sa.String(200), nullable=True),
        sa.Column("bik", sa.String(20), nullable=True),
        sa.Column("account", sa.String(30), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action_sysname", sa.String(50),
                  sa.ForeignKey("log_actions.sysname", ondelete="SET NULL"), nullable=True),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", UUID(as_uuid=True), nullable=False),
        sa.Column("details", JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "user_permission_groups",
        sa.Column("user_id", UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("group_id", sa.Integer(),
                  sa.ForeignKey("permission_groups.id", ondelete="CASCADE"), nullable=False),
        sa.PrimaryKeyConstraint("user_id", "group_id"),
    )

    op.create_table(
        "visits",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("site_id", UUID(as_uuid=True),
                  sa.ForeignKey("sites.id", ondelete="CASCADE"), nullable=True),
        sa.Column("assigned_user_id", UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("planned_date", sa.Date(), nullable=False),
        sa.Column("planned_time_from", sa.Time(), nullable=True),
        sa.Column("planned_time_to", sa.Time(), nullable=True),
        sa.Column("visit_type", sa.String(30), nullable=False, server_default="maintenance"),
        sa.Column("priority", sa.String(20), nullable=False, server_default="medium"),
        sa.Column("status", sa.String(20), nullable=False, server_default="planned"),
        sa.Column("work_summary", sa.Text(), nullable=True),
        sa.Column("checklist", JSONB(), nullable=True),
        sa.Column("defects_present", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("defects_summary", sa.Text(), nullable=True),
        sa.Column("recommendations", sa.Text(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("office_notes", sa.Text(), nullable=True),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("cost", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "defects",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("visit_id", UUID(as_uuid=True),
                  sa.ForeignKey("visits.id", ondelete="CASCADE"), nullable=True),
        sa.Column("site_id", UUID(as_uuid=True),
                  sa.ForeignKey("sites.id", ondelete="CASCADE"), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("priority", sa.String(20), nullable=False, server_default="medium"),
        sa.Column("action_type", sa.String(20), nullable=False, server_default="repair"),
        sa.Column("suggested_parts", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "attachments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("visit_id", UUID(as_uuid=True),
                  sa.ForeignKey("visits.id", ondelete="CASCADE"), nullable=True),
        sa.Column("kind", sa.String(30), nullable=False, server_default="act_photo"),
        sa.Column("file_url", sa.Text(), nullable=False),
        sa.Column("created_by_user_id", UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "notifications",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("related_visit_id", UUID(as_uuid=True),
                  sa.ForeignKey("visits.id", ondelete="SET NULL"), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "purchases",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("defect_id", UUID(as_uuid=True),
                  sa.ForeignKey("defects.id", ondelete="CASCADE"), nullable=True),
        sa.Column("site_id", UUID(as_uuid=True),
                  sa.ForeignKey("sites.id", ondelete="SET NULL"), nullable=True),
        sa.Column("item", sa.Text(), nullable=False),
        sa.Column("qty", sa.Numeric(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )

    for entity in ["clients", "sites", "users", "visits", "purchases"]:
        op.create_table(
            f"{entity}_history",
            sa.Column("id", UUID(as_uuid=True), primary_key=True,
                      server_default=sa.text("gen_random_uuid()")),
            sa.Column("changed_by_user_id", UUID(as_uuid=True),
                      sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("changed_at", sa.DateTime(), nullable=False,
                      server_default=sa.text("now()")),
            sa.Column("method", sa.String(20), nullable=False),
        )
