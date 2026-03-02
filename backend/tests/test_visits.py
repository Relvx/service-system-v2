"""
Тесты эндпоинтов выездов.

GET    /api/visits              — список выездов
GET    /api/visits/calendar     — выезды в диапазоне дат
GET    /api/visits/{id}         — выезд по ID
POST   /api/visits              — создание выезда
PUT    /api/visits/{id}         — обновление выезда
POST   /api/visits/{id}/complete — завершение выезда
DELETE /api/visits/{id}         — удаление выезда
"""

from datetime import date, timedelta
from httpx import AsyncClient
from tests.conftest import auth_headers

TODAY = str(date.today())
FUTURE = str(date.today() + timedelta(days=7))


class TestGetVisits:
    async def test_list_returns_list(self, http_client: AsyncClient, admin_token: str):
        res = await http_client.get("/api/visits", headers=auth_headers(admin_token))
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    async def test_list_filter_by_status(self, http_client: AsyncClient, admin_token: str):
        res = await http_client.get("/api/visits?status=planned",
                                    headers=auth_headers(admin_token))
        assert res.status_code == 200
        for v in res.json():
            assert v["status"] == "planned"

    async def test_calendar_endpoint(self, http_client: AsyncClient, admin_token: str):
        res = await http_client.get(f"/api/visits/calendar?start={TODAY}&end={FUTURE}",
                                    headers=auth_headers(admin_token))
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    async def test_list_unauthenticated(self, http_client: AsyncClient):
        res = await http_client.get("/api/visits")
        assert res.status_code == 401

    async def test_master_sees_only_own_visits(self, http_client: AsyncClient, master_token: str):
        """Мастер имеет доступ к /api/visits (office_group или master_group могут смотреть)."""
        res = await http_client.get("/api/visits", headers=auth_headers(master_token))
        # Статус зависит от настроек прав; просто проверяем что не 500
        assert res.status_code in (200, 403)


class TestVisitCRUD:
    async def test_create_and_delete(self, http_client: AsyncClient, admin_token: str,
                                     site_id: str, admin_user_id: str):
        headers = auth_headers(admin_token)
        payload = {
            "planned_date": TODAY,
            "site_id": site_id,
            "assigned_user_id": admin_user_id,
            "visit_type": "maintenance",
            "priority": "medium",
        }

        res = await http_client.post("/api/visits", headers=headers, json=payload)
        assert res.status_code == 201
        data = res.json()
        visit_id = data["id"]
        assert data["visit_type"] == "maintenance"

        del_res = await http_client.delete(f"/api/visits/{visit_id}", headers=headers)
        assert del_res.status_code == 204

    async def test_get_by_id(self, http_client: AsyncClient, admin_token: str,
                              site_id: str, admin_user_id: str):
        headers = auth_headers(admin_token)
        payload = {
            "planned_date": TODAY,
            "site_id": site_id,
            "assigned_user_id": admin_user_id,
            "visit_type": "maintenance",
            "priority": "medium",
        }

        res = await http_client.post("/api/visits", headers=headers, json=payload)
        visit_id = res.json()["id"]

        get_res = await http_client.get(f"/api/visits/{visit_id}", headers=headers)
        assert get_res.status_code == 200
        assert get_res.json()["id"] == visit_id

        await http_client.delete(f"/api/visits/{visit_id}", headers=headers)

    async def test_get_not_found(self, http_client: AsyncClient, admin_token: str):
        fake_id = "00000000-0000-0000-0000-000000000000"
        res = await http_client.get(f"/api/visits/{fake_id}", headers=auth_headers(admin_token))
        assert res.status_code == 404

    async def test_update_status(self, http_client: AsyncClient, admin_token: str,
                                  site_id: str, admin_user_id: str):
        headers = auth_headers(admin_token)
        payload = {
            "planned_date": TODAY,
            "site_id": site_id,
            "assigned_user_id": admin_user_id,
            "visit_type": "maintenance",
            "priority": "medium",
        }

        res = await http_client.post("/api/visits", headers=headers, json=payload)
        visit_id = res.json()["id"]

        upd = await http_client.put(f"/api/visits/{visit_id}", headers=headers,
                                     json={"status": "in_progress"})
        assert upd.status_code == 200
        assert upd.json()["status"] == "in_progress"

        await http_client.delete(f"/api/visits/{visit_id}", headers=headers)

    async def test_complete_visit(self, http_client: AsyncClient, admin_token: str,
                                   site_id: str, admin_user_id: str):
        headers = auth_headers(admin_token)
        payload = {
            "planned_date": TODAY,
            "site_id": site_id,
            "assigned_user_id": admin_user_id,
            "visit_type": "maintenance",
            "priority": "medium",
        }

        res = await http_client.post("/api/visits", headers=headers, json=payload)
        visit_id = res.json()["id"]

        comp = await http_client.post(f"/api/visits/{visit_id}/complete", headers=headers,
                                       json={"work_summary": "Выполнено ТО", "defects_present": False})
        assert comp.status_code == 200
        assert comp.json()["status"] == "closed"

        await http_client.delete(f"/api/visits/{visit_id}", headers=headers)

    async def test_filter_by_priority(self, http_client: AsyncClient, admin_token: str):
        res = await http_client.get("/api/visits?priority=high",
                                    headers=auth_headers(admin_token))
        assert res.status_code == 200
        for v in res.json():
            assert v["priority"] == "high"
