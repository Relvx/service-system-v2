"""
Тесты Block 16 — Напоминания.

GET    /api/reminders           — список (общие + личные текущего пользователя)
POST   /api/reminders           — создание напоминания
DELETE /api/reminders/{id}      — удаление (личное — только владельцем)
"""

import pytest
from httpx import AsyncClient
from tests.conftest import auth_headers


@pytest.mark.asyncio
class TestRemindersCRUD:
    async def test_create_shared_reminder(self, http_client: AsyncClient, office_token: str):
        """Офис создаёт общее напоминание — возвращается 201."""
        res = await http_client.post("/api/reminders", headers=auth_headers(office_token), json={
            "text": "__test__ общее",
            "is_personal": False,
        })
        assert res.status_code == 201
        data = res.json()
        assert data["text"] == "__test__ общее"
        assert data["is_personal"] is False
        assert data["id"] > 0
        assert data["created_by_name"] is not None

    async def test_create_personal_reminder(self, http_client: AsyncClient, office_token: str):
        """Создание личного напоминания."""
        res = await http_client.post("/api/reminders", headers=auth_headers(office_token), json={
            "text": "__test__ личное",
            "is_personal": True,
        })
        assert res.status_code == 201
        data = res.json()
        assert data["is_personal"] is True

    async def test_get_reminders(self, http_client: AsyncClient, office_token: str):
        """GET /reminders возвращает список."""
        res = await http_client.get("/api/reminders", headers=auth_headers(office_token))
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    async def test_shared_visible_to_another_user(
        self, http_client: AsyncClient, office_token: str, admin_token: str
    ):
        """Общее напоминание видно другому пользователю."""
        cr = await http_client.post("/api/reminders", headers=auth_headers(office_token), json={
            "text": "__test__ shared visibility",
            "is_personal": False,
        })
        reminder_id = cr.json()["id"]

        res = await http_client.get("/api/reminders", headers=auth_headers(admin_token))
        ids = [r["id"] for r in res.json()]
        assert reminder_id in ids

    async def test_personal_not_visible_to_another_user(
        self, http_client: AsyncClient, office_token: str, admin_token: str
    ):
        """Личное напоминание НЕ видно другому пользователю."""
        cr = await http_client.post("/api/reminders", headers=auth_headers(office_token), json={
            "text": "__test__ personal hidden",
            "is_personal": True,
        })
        reminder_id = cr.json()["id"]

        res = await http_client.get("/api/reminders", headers=auth_headers(admin_token))
        ids = [r["id"] for r in res.json()]
        assert reminder_id not in ids

    async def test_delete_own_reminder(self, http_client: AsyncClient, office_token: str):
        """Удаление своего напоминания → 204."""
        cr = await http_client.post("/api/reminders", headers=auth_headers(office_token), json={
            "text": "__test__ delete own",
            "is_personal": False,
        })
        reminder_id = cr.json()["id"]

        res = await http_client.delete(f"/api/reminders/{reminder_id}", headers=auth_headers(office_token))
        assert res.status_code == 204

    async def test_delete_personal_by_owner(self, http_client: AsyncClient, office_token: str):
        """Владелец может удалить своё личное напоминание."""
        cr = await http_client.post("/api/reminders", headers=auth_headers(office_token), json={
            "text": "__test__ personal by owner",
            "is_personal": True,
        })
        reminder_id = cr.json()["id"]

        res = await http_client.delete(f"/api/reminders/{reminder_id}", headers=auth_headers(office_token))
        assert res.status_code == 204

    async def test_delete_personal_by_other_forbidden(
        self, http_client: AsyncClient, office_token: str, admin_token: str
    ):
        """Чужое личное напоминание нельзя удалить → 403."""
        cr = await http_client.post("/api/reminders", headers=auth_headers(office_token), json={
            "text": "__test__ personal forbidden",
            "is_personal": True,
        })
        reminder_id = cr.json()["id"]

        res = await http_client.delete(f"/api/reminders/{reminder_id}", headers=auth_headers(admin_token))
        assert res.status_code == 403

    async def test_delete_not_found(self, http_client: AsyncClient, office_token: str):
        """DELETE несуществующего напоминания → 404."""
        res = await http_client.delete("/api/reminders/999999", headers=auth_headers(office_token))
        assert res.status_code == 404

    async def test_master_forbidden(self, http_client: AsyncClient, master_token: str):
        """Мастер не имеет доступа к напоминаниям."""
        res = await http_client.get("/api/reminders", headers=auth_headers(master_token))
        assert res.status_code == 403
