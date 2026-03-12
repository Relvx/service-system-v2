"""
Тесты Block 15 — Раздел задач.

POST   /api/tasks            — создание задачи
GET    /api/tasks             — список задач (фильтр: all/active/done)
PUT    /api/tasks/{id}        — редактирование + отметка выполненной
DELETE /api/tasks/{id}        — удаление
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from tests.conftest import auth_headers


@pytest.mark.asyncio
class TestTasksCRUD:
    async def test_create_task(self, http_client: AsyncClient, office_token: str):
        """Офис создаёт задачу — возвращается 201 с полями."""
        res = await http_client.post("/api/tasks", headers=auth_headers(office_token), json={
            "title": "__test__ задача",
            "description": "Описание",
            "deadline": "2026-04-30",
        })
        assert res.status_code == 201
        data = res.json()
        assert data["title"] == "__test__ задача"
        assert data["description"] == "Описание"
        assert data["deadline"] == "2026-04-30"
        assert data["is_done"] is False
        assert data["id"] > 0

    async def test_get_tasks(self, http_client: AsyncClient, office_token: str):
        """GET /tasks возвращает список."""
        res = await http_client.get("/api/tasks", headers=auth_headers(office_token))
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    async def test_filter_active(self, http_client: AsyncClient, office_token: str):
        """Фильтр active возвращает только невыполненные."""
        res = await http_client.get("/api/tasks?filter=active", headers=auth_headers(office_token))
        assert res.status_code == 200
        for t in res.json():
            assert t["is_done"] is False

    async def test_filter_done(self, http_client: AsyncClient, admin_token: str, office_token: str):
        """Фильтр done возвращает только выполненные."""
        # Создаём задачу и помечаем выполненной
        cr = await http_client.post("/api/tasks", headers=auth_headers(office_token), json={
            "title": "__test__ done task",
        })
        task_id = cr.json()["id"]
        await http_client.put(f"/api/tasks/{task_id}", headers=auth_headers(office_token),
                              json={"is_done": True})

        res = await http_client.get("/api/tasks?filter=done", headers=auth_headers(office_token))
        assert res.status_code == 200
        for t in res.json():
            assert t["is_done"] is True

    async def test_update_task(self, http_client: AsyncClient, office_token: str):
        """Редактирование задачи изменяет поля."""
        cr = await http_client.post("/api/tasks", headers=auth_headers(office_token), json={
            "title": "__test__ update",
        })
        task_id = cr.json()["id"]

        up = await http_client.put(f"/api/tasks/{task_id}", headers=auth_headers(office_token),
                                    json={"title": "Обновлено", "is_done": True})
        assert up.status_code == 200
        assert up.json()["title"] == "Обновлено"
        assert up.json()["is_done"] is True

    async def test_delete_task(self, http_client: AsyncClient, office_token: str):
        """Удаление задачи возвращает 204."""
        cr = await http_client.post("/api/tasks", headers=auth_headers(office_token), json={
            "title": "__test__ delete",
        })
        task_id = cr.json()["id"]

        res = await http_client.delete(f"/api/tasks/{task_id}", headers=auth_headers(office_token))
        assert res.status_code == 204

        # Проверяем что задача недоступна (GET не упадёт, просто её не будет в списке)
        all_tasks = await http_client.get("/api/tasks", headers=auth_headers(office_token))
        ids = [t["id"] for t in all_tasks.json()]
        assert task_id not in ids

    async def test_delete_not_found(self, http_client: AsyncClient, office_token: str):
        """DELETE несуществующей задачи → 404."""
        res = await http_client.delete("/api/tasks/999999", headers=auth_headers(office_token))
        assert res.status_code == 404

    async def test_master_forbidden(self, http_client: AsyncClient, master_token: str):
        """Мастер не имеет доступа к задачам."""
        res = await http_client.get("/api/tasks", headers=auth_headers(master_token))
        assert res.status_code == 403
