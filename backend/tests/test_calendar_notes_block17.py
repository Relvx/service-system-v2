"""
Тесты Block 17 — Заметки календаря.

POST   /api/calendar-notes          — создание заметки
GET    /api/calendar-notes?year=N   — список заметок за год
PUT    /api/calendar-notes/{id}     — редактирование текста
DELETE /api/calendar-notes/{id}     — удаление
"""

import pytest
from httpx import AsyncClient
from tests.conftest import auth_headers


@pytest.mark.asyncio
class TestCalendarNotesCRUD:
    async def test_create_note(self, http_client: AsyncClient, office_token: str):
        """Офис создаёт заметку — возвращается 201 с полями."""
        res = await http_client.post("/api/calendar-notes", headers=auth_headers(office_token), json={
            "date": "2026-04-15",
            "text": "__test__ заметка календаря",
        })
        assert res.status_code == 201
        data = res.json()
        assert data["date"] == "2026-04-15"
        assert data["text"] == "__test__ заметка календаря"
        assert data["id"] > 0
        assert data["created_by_name"] is not None

    async def test_get_notes(self, http_client: AsyncClient, office_token: str):
        """GET /calendar-notes возвращает список."""
        res = await http_client.get("/api/calendar-notes", headers=auth_headers(office_token))
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    async def test_get_notes_by_year(self, http_client: AsyncClient, office_token: str):
        """Фильтр по году возвращает только заметки за этот год."""
        # Создаём заметку за 2026
        await http_client.post("/api/calendar-notes", headers=auth_headers(office_token), json={
            "date": "2026-06-01",
            "text": "__test__ 2026 year",
        })
        res = await http_client.get("/api/calendar-notes?year=2026", headers=auth_headers(office_token))
        assert res.status_code == 200
        for n in res.json():
            assert n["date"].startswith("2026")

    async def test_update_note(self, http_client: AsyncClient, office_token: str):
        """Редактирование заметки меняет текст."""
        cr = await http_client.post("/api/calendar-notes", headers=auth_headers(office_token), json={
            "date": "2026-05-10",
            "text": "__test__ update before",
        })
        note_id = cr.json()["id"]

        up = await http_client.put(f"/api/calendar-notes/{note_id}", headers=auth_headers(office_token),
                                    json={"text": "Обновлённая заметка"})
        assert up.status_code == 200
        assert up.json()["text"] == "Обновлённая заметка"

    async def test_delete_note(self, http_client: AsyncClient, office_token: str):
        """Удаление заметки возвращает 204."""
        cr = await http_client.post("/api/calendar-notes", headers=auth_headers(office_token), json={
            "date": "2026-07-01",
            "text": "__test__ delete",
        })
        note_id = cr.json()["id"]

        res = await http_client.delete(f"/api/calendar-notes/{note_id}", headers=auth_headers(office_token))
        assert res.status_code == 204

        all_notes = await http_client.get("/api/calendar-notes", headers=auth_headers(office_token))
        ids = [n["id"] for n in all_notes.json()]
        assert note_id not in ids

    async def test_delete_not_found(self, http_client: AsyncClient, office_token: str):
        """DELETE несуществующей заметки → 404."""
        res = await http_client.delete("/api/calendar-notes/999999", headers=auth_headers(office_token))
        assert res.status_code == 404

    async def test_another_user_can_edit(self, http_client: AsyncClient, office_token: str, admin_token: str):
        """Другой пользователь (офис/админ) может редактировать чужую заметку."""
        cr = await http_client.post("/api/calendar-notes", headers=auth_headers(office_token), json={
            "date": "2026-08-01",
            "text": "__test__ shared edit",
        })
        note_id = cr.json()["id"]

        up = await http_client.put(f"/api/calendar-notes/{note_id}", headers=auth_headers(admin_token),
                                    json={"text": "Отредактировано другим"})
        assert up.status_code == 200

    async def test_master_forbidden(self, http_client: AsyncClient, master_token: str):
        """Мастер не имеет доступа к заметкам календаря."""
        res = await http_client.get("/api/calendar-notes", headers=auth_headers(master_token))
        assert res.status_code == 403
