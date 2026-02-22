"""Initial schema and seed data

Revision ID: 001
Revises:
Create Date: 2026-02-22

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ─── Config / lookup tables ─────────────────────────────────────────────

    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(50), unique=True, nullable=False),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("default_redirect", sa.String(100), nullable=False),
    )

    op.create_table(
        "visit_statuses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(50), unique=True, nullable=False),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("color", sa.String(50), nullable=False),
    )

    op.create_table(
        "visit_types",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(50), unique=True, nullable=False),
        sa.Column("display_name", sa.String(100), nullable=False),
    )

    op.create_table(
        "priorities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(50), unique=True, nullable=False),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("color", sa.String(50), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
    )

    op.create_table(
        "defect_statuses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(50), unique=True, nullable=False),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("color", sa.String(50), nullable=False),
    )

    op.create_table(
        "defect_action_types",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(50), unique=True, nullable=False),
        sa.Column("display_name", sa.String(100), nullable=False),
    )

    op.create_table(
        "attachment_kinds",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(50), unique=True, nullable=False),
        sa.Column("display_name", sa.String(100), nullable=False),
    )

    op.create_table(
        "purchase_statuses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(50), unique=True, nullable=False),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("color", sa.String(50), nullable=False),
    )

    op.create_table(
        "service_frequencies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(50), unique=True, nullable=False),
        sa.Column("display_name", sa.String(100), nullable=False),
    )

    op.create_table(
        "notification_types",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(50), unique=True, nullable=False),
        sa.Column("display_name", sa.String(100), nullable=False),
    )

    # ─── Main tables ────────────────────────────────────────────────────────

    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "clients",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("inn", sa.String(50), nullable=True),
        sa.Column("kpp", sa.String(50), nullable=True),
        sa.Column("contacts", sa.Text(), nullable=True),
        sa.Column("contact_person", sa.String(255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "sites",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("client_id", UUID(as_uuid=True), sa.ForeignKey("clients.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("address", sa.Text(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("access_notes", sa.Text(), nullable=True),
        sa.Column("onsite_contact", sa.Text(), nullable=True),
        sa.Column("service_frequency", sa.String(30), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "visits",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("site_id", UUID(as_uuid=True), sa.ForeignKey("sites.id", ondelete="CASCADE"), nullable=True),
        sa.Column("assigned_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
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
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_visits_planned_date", "visits", ["planned_date"])
    op.create_index("idx_visits_assigned_user", "visits", ["assigned_user_id"])
    op.create_index("idx_visits_site", "visits", ["site_id"])
    op.create_index("idx_visits_status", "visits", ["status"])

    op.create_table(
        "attachments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("visit_id", UUID(as_uuid=True), sa.ForeignKey("visits.id", ondelete="CASCADE"), nullable=True),
        sa.Column("kind", sa.String(30), nullable=False, server_default="act_photo"),
        sa.Column("file_url", sa.Text(), nullable=False),
        sa.Column("created_by_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "defects",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("visit_id", UUID(as_uuid=True), sa.ForeignKey("visits.id", ondelete="CASCADE"), nullable=True),
        sa.Column("site_id", UUID(as_uuid=True), sa.ForeignKey("sites.id", ondelete="CASCADE"), nullable=True),
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
        "purchases",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("defect_id", UUID(as_uuid=True), sa.ForeignKey("defects.id", ondelete="CASCADE"), nullable=True),
        sa.Column("site_id", UUID(as_uuid=True), sa.ForeignKey("sites.id", ondelete="SET NULL"), nullable=True),
        sa.Column("item", sa.Text(), nullable=False),
        sa.Column("qty", sa.Numeric(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "notifications",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("related_visit_id", UUID(as_uuid=True), sa.ForeignKey("visits.id", ondelete="SET NULL"), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_notifications_user", "notifications", ["user_id"])
    op.create_index("idx_notifications_read", "notifications", ["is_read"])

    # ─── Seed config tables ──────────────────────────────────────────────────

    conn = op.get_bind()

    conn.execute(sa.text("""
        INSERT INTO roles (code, display_name, default_redirect) VALUES
        ('master', 'Мастер', '/my-visits'),
        ('office', 'Офис', '/dashboard'),
        ('admin', 'Администратор', '/dashboard')
    """))

    conn.execute(sa.text("""
        INSERT INTO visit_statuses (code, display_name, color) VALUES
        ('planned', 'Запланирован', 'blue'),
        ('in_progress', 'В работе', 'yellow'),
        ('closed', 'Завершён', 'green'),
        ('cancelled', 'Отменён', 'gray')
    """))

    conn.execute(sa.text("""
        INSERT INTO visit_types (code, display_name) VALUES
        ('maintenance', 'Техобслуживание'),
        ('repair', 'Ремонт'),
        ('inspection', 'Осмотр'),
        ('emergency', 'Аварийный')
    """))

    conn.execute(sa.text("""
        INSERT INTO priorities (code, display_name, color, sort_order) VALUES
        ('low', 'Низкий', 'green', 1),
        ('medium', 'Средний', 'yellow', 2),
        ('high', 'Высокий', 'orange', 3),
        ('urgent', 'Срочный', 'red', 4)
    """))

    conn.execute(sa.text("""
        INSERT INTO defect_statuses (code, display_name, color) VALUES
        ('open', 'Открыт', 'red'),
        ('approved', 'Согласован', 'blue'),
        ('in_progress', 'В работе', 'yellow'),
        ('fixed', 'Устранён', 'green')
    """))

    conn.execute(sa.text("""
        INSERT INTO defect_action_types (code, display_name) VALUES
        ('repair', 'Ремонт'),
        ('replace', 'Замена'),
        ('monitor', 'Наблюдение'),
        ('other', 'Другое')
    """))

    conn.execute(sa.text("""
        INSERT INTO attachment_kinds (code, display_name) VALUES
        ('act_photo', 'Фото акта'),
        ('defect_photo', 'Фото дефекта'),
        ('other', 'Другое')
    """))

    conn.execute(sa.text("""
        INSERT INTO purchase_statuses (code, display_name, color) VALUES
        ('draft', 'Черновик', 'gray'),
        ('approved', 'Согласовано', 'blue'),
        ('ordered', 'Заказано', 'yellow'),
        ('received', 'Получено', 'cyan'),
        ('installed', 'Установлено', 'orange'),
        ('closed', 'Закрыто', 'green')
    """))

    conn.execute(sa.text("""
        INSERT INTO service_frequencies (code, display_name) VALUES
        ('monthly', 'Ежемесячно'),
        ('quarterly', 'Ежеквартально'),
        ('seasonal', 'Сезонно'),
        ('custom', 'Индивидуально')
    """))

    conn.execute(sa.text("""
        INSERT INTO notification_types (code, display_name) VALUES
        ('visit_assigned', 'Назначен выезд'),
        ('visit_updated', 'Изменён выезд')
    """))

    # ─── Seed users (password: admin123) ─────────────────────────────────────
    # bcrypt hash of 'admin123' (generated with bcrypt.hashpw)

    conn.execute(sa.text("""
        INSERT INTO users (email, password_hash, full_name, phone, role) VALUES
        ('admin@system.local',
         '$2b$12$IYRa/XTcXPnpTgZ3gjoFxu3NhRA5ig89y0fdmHHq9zIpDP.3UdCHW',
         'Администратор', NULL, 'admin'),
        ('master1@system.local',
         '$2b$12$IYRa/XTcXPnpTgZ3gjoFxu3NhRA5ig89y0fdmHHq9zIpDP.3UdCHW',
         'Мастер Иванов', '8-999-111-22-33', 'master'),
        ('master2@system.local',
         '$2b$12$IYRa/XTcXPnpTgZ3gjoFxu3NhRA5ig89y0fdmHHq9zIpDP.3UdCHW',
         'Мастер Петров', '8-999-444-55-66', 'master'),
        ('office1@system.local',
         '$2b$12$IYRa/XTcXPnpTgZ3gjoFxu3NhRA5ig89y0fdmHHq9zIpDP.3UdCHW',
         'Офис Сидоров', '8-495-777-88-99', 'office')
    """))

    # ─── Seed clients & sites ────────────────────────────────────────────────

    conn.execute(sa.text("""
        INSERT INTO clients (name, contacts, contact_person, notes) VALUES
        ('Тестовый клиент 1', '8-495-123-45-67', 'Иван Иванов', 'Тестовый клиент для разработки'),
        ('Тестовый клиент 2', '8-495-765-43-21', 'Петр Петров', 'Ещё один тестовый клиент')
    """))

    conn.execute(sa.text("""
        INSERT INTO sites (client_id, title, address, latitude, longitude, access_notes) VALUES
        ((SELECT id FROM clients WHERE name = 'Тестовый клиент 1'),
         'Котельная №1', 'Москва, ул. Ленина, д. 10', 55.751244, 37.618423, 'Ключ у охранника'),
        ((SELECT id FROM clients WHERE name = 'Тестовый клиент 2'),
         'Котельная №2', 'Московская область, г. Химки, ул. Победы, д. 5', 55.889339, 37.429857, 'Вход с торца здания')
    """))

    # ─── Seed visits ─────────────────────────────────────────────────────────

    conn.execute(sa.text("""
        INSERT INTO visits (site_id, assigned_user_id, planned_date, visit_type, priority, status) VALUES
        ((SELECT id FROM sites WHERE title = 'Котельная №1'),
         (SELECT id FROM users WHERE email = 'master1@system.local'),
         CURRENT_DATE, 'maintenance', 'medium', 'planned'),
        ((SELECT id FROM sites WHERE title = 'Котельная №2'),
         (SELECT id FROM users WHERE email = 'master2@system.local'),
         CURRENT_DATE + INTERVAL '1 day', 'repair', 'high', 'planned')
    """))


def downgrade() -> None:
    op.drop_table("notifications")
    op.drop_table("purchases")
    op.drop_table("defects")
    op.drop_table("attachments")
    op.drop_table("visits")
    op.drop_table("sites")
    op.drop_table("clients")
    op.drop_table("users")
    op.drop_table("notification_types")
    op.drop_table("service_frequencies")
    op.drop_table("purchase_statuses")
    op.drop_table("attachment_kinds")
    op.drop_table("defect_action_types")
    op.drop_table("defect_statuses")
    op.drop_table("priorities")
    op.drop_table("visit_types")
    op.drop_table("visit_statuses")
    op.drop_table("roles")
