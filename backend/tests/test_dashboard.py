"""
Тесты эндпоинта дашборда.

GET /api/dashboard/stats — агрегированная статистика (admin + office)
"""

from httpx import AsyncClient
from tests.conftest import auth_headers


class TestDashboard:
    async def test_admin_gets_stats(self, http_client: AsyncClient, admin_token: str):
        """Администратор получает статистику."""
        res = await http_client.get("/api/dashboard/stats", headers=auth_headers(admin_token))
        assert res.status_code == 200
        data = res.json()
        # Проверяем наличие ключевых полей статистики
        assert isinstance(data, dict)

    async def test_office_gets_stats(self, http_client: AsyncClient, office_token: str):
        """Офис получает статистику."""
        res = await http_client.get("/api/dashboard/stats", headers=auth_headers(office_token))
        assert res.status_code == 200

    async def test_master_forbidden(self, http_client: AsyncClient, master_token: str):
        """Мастер не имеет доступа к дашборду."""
        res = await http_client.get("/api/dashboard/stats", headers=auth_headers(master_token))
        assert res.status_code == 403

    async def test_unauthenticated_forbidden(self, http_client: AsyncClient):
        res = await http_client.get("/api/dashboard/stats")
        assert res.status_code == 401

    async def test_stats_structure(self, http_client: AsyncClient, admin_token: str):
        """Структура ответа содержит все обязательные поля."""
        res = await http_client.get("/api/dashboard/stats", headers=auth_headers(admin_token))
        data = res.json()
        assert "visits_today" in data
        assert "visits_this_week" in data
        assert "open_defects" in data
        assert "active_purchases" in data
        assert "today_visits" in data
        assert "recent_completed" in data
        assert isinstance(data["visits_today"], int)
        assert isinstance(data["visits_this_week"], int)
        assert isinstance(data["active_purchases"], int)
        assert isinstance(data["open_defects"], list)
        assert isinstance(data["today_visits"], list)
        assert isinstance(data["recent_completed"], list)

    async def test_today_visits_structure(self, http_client: AsyncClient, admin_token: str, site_id: int, admin_user_id: str):
        """today_visits содержит выезды с нужными полями."""
        import datetime
        today = datetime.date.today().isoformat()
        headers = auth_headers(admin_token)

        # Создаём выезд на сегодня
        visit_res = await http_client.post("/api/visits", headers=headers, json={
            "site_id": site_id,
            "assigned_user_id": int(admin_user_id),
            "planned_date": today,
            "visit_type": "maintenance",
            "priority": "medium",
            "status": "planned",
        })
        assert visit_res.status_code == 201
        visit_id = visit_res.json()["id"]

        res = await http_client.get("/api/dashboard/stats", headers=headers)
        data = res.json()
        assert len(data["today_visits"]) >= 1

        visit = next((v for v in data["today_visits"] if v["id"] == visit_id), None)
        assert visit is not None
        assert "planned_date" in visit
        assert "status" in visit
        assert "visit_type" in visit
        assert "site_title" in visit
        assert "client_name" in visit
        assert "master_name" in visit

        # Cleanup
        await http_client.delete(f"/api/visits/{visit_id}", headers=headers)

    async def test_recent_completed_structure(self, http_client: AsyncClient, admin_token: str, site_id: int, admin_user_id: str):
        """recent_completed содержит завершённые выезды (не более 5)."""
        headers = auth_headers(admin_token)

        res = await http_client.get("/api/dashboard/stats", headers=headers)
        data = res.json()
        assert len(data["recent_completed"]) <= 5

        for v in data["recent_completed"]:
            assert v["status"] == "closed"
            assert "id" in v
            assert "planned_date" in v

    async def test_today_visits_excludes_cancelled(self, http_client: AsyncClient, admin_token: str, site_id: int, admin_user_id: str):
        """Отменённые выезды не попадают в today_visits."""
        import datetime
        today = datetime.date.today().isoformat()
        headers = auth_headers(admin_token)

        # Создаём выезд на сегодня и отменяем его
        visit_res = await http_client.post("/api/visits", headers=headers, json={
            "site_id": site_id,
            "assigned_user_id": int(admin_user_id),
            "planned_date": today,
            "visit_type": "maintenance",
            "priority": "medium",
            "status": "planned",
        })
        assert visit_res.status_code == 201
        visit_id = visit_res.json()["id"]

        await http_client.patch(f"/api/visits/{visit_id}/cancel", headers=headers)

        res = await http_client.get("/api/dashboard/stats", headers=headers)
        data = res.json()
        cancelled_ids = [v["id"] for v in data["today_visits"]]
        assert visit_id not in cancelled_ids

        # Cleanup
        await http_client.delete(f"/api/visits/{visit_id}", headers=headers)
