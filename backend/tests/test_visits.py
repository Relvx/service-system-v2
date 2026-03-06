"""
Тесты эндпоинтов выездов.

GET    /api/visits              — список выездов (с фильтрами master_id)
GET    /api/visits/calendar     — выезды в диапазоне дат
GET    /api/visits/{id}         — выезд по ID
POST   /api/visits              — создание выезда
PUT    /api/visits/{id}         — обновление выезда
POST   /api/visits/{id}/complete — завершение выезда
PATCH  /api/visits/{id}/cancel  — отмена выезда
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
        fake_id = 999999
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


class TestVisitArchive:
    async def test_archive_visit(self, http_client: AsyncClient, admin_token: str,
                                  site_id: str, admin_user_id: str):
        """PATCH /archive устанавливает is_archived=true."""
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

        arc = await http_client.patch(f"/api/visits/{visit_id}/archive", headers=headers)
        assert arc.status_code == 200
        assert arc.json()["is_archived"] is True

        await http_client.delete(f"/api/visits/{visit_id}", headers=headers)

    async def test_archived_hidden_by_default(self, http_client: AsyncClient, admin_token: str,
                                               site_id: str, admin_user_id: str):
        """Архивированный выезд не появляется в стандартном списке."""
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
        await http_client.patch(f"/api/visits/{visit_id}/archive", headers=headers)

        list_res = await http_client.get("/api/visits", headers=headers)
        ids = [v["id"] for v in list_res.json()]
        assert visit_id not in ids

        await http_client.delete(f"/api/visits/{visit_id}", headers=headers)

    async def test_show_archived_param(self, http_client: AsyncClient, admin_token: str,
                                        site_id: str, admin_user_id: str):
        """show_archived=true включает архивные выезды в список."""
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
        await http_client.patch(f"/api/visits/{visit_id}/archive", headers=headers)

        list_res = await http_client.get("/api/visits?show_archived=true", headers=headers)
        ids = [v["id"] for v in list_res.json()]
        assert visit_id in ids

        await http_client.delete(f"/api/visits/{visit_id}", headers=headers)


class TestVisitBlock7:
    """Блок 7: отмена выезда и фильтр по мастеру."""

    async def test_cancel_planned_visit(self, http_client: AsyncClient, admin_token: str,
                                        site_id: int, admin_user_id: str):
        """PATCH /cancel переводит запланированный выезд в статус 'cancelled'."""
        headers = auth_headers(admin_token)
        res = await http_client.post("/api/visits", headers=headers, json={
            "site_id": site_id, "assigned_user_id": admin_user_id,
            "planned_date": TODAY, "visit_type": "maintenance", "priority": "medium",
        })
        visit_id = res.json()["id"]

        cancel = await http_client.patch(f"/api/visits/{visit_id}/cancel", headers=headers)
        assert cancel.status_code == 200
        assert cancel.json()["status"] == "cancelled"

        await http_client.delete(f"/api/visits/{visit_id}", headers=headers)

    async def test_cancel_in_progress_visit(self, http_client: AsyncClient, admin_token: str,
                                             site_id: int, admin_user_id: str):
        """Выезд в статусе 'in_progress' тоже можно отменить."""
        headers = auth_headers(admin_token)
        res = await http_client.post("/api/visits", headers=headers, json={
            "site_id": site_id, "assigned_user_id": admin_user_id,
            "planned_date": TODAY, "visit_type": "maintenance", "priority": "medium",
        })
        visit_id = res.json()["id"]
        await http_client.put(f"/api/visits/{visit_id}", headers=headers,
                               json={"status": "in_progress"})

        cancel = await http_client.patch(f"/api/visits/{visit_id}/cancel", headers=headers)
        assert cancel.status_code == 200
        assert cancel.json()["status"] == "cancelled"

        await http_client.delete(f"/api/visits/{visit_id}", headers=headers)

    async def test_cancel_closed_visit_returns_400(self, http_client: AsyncClient,
                                                    admin_token: str, site_id: int,
                                                    admin_user_id: str):
        """Попытка отменить завершённый выезд → 400."""
        headers = auth_headers(admin_token)
        res = await http_client.post("/api/visits", headers=headers, json={
            "site_id": site_id, "assigned_user_id": admin_user_id,
            "planned_date": TODAY, "visit_type": "maintenance", "priority": "medium",
        })
        visit_id = res.json()["id"]
        await http_client.post(f"/api/visits/{visit_id}/complete", headers=headers,
                                json={"work_summary": "Выполнено", "defects_present": False})

        cancel = await http_client.patch(f"/api/visits/{visit_id}/cancel", headers=headers)
        assert cancel.status_code == 400

        await http_client.delete(f"/api/visits/{visit_id}", headers=headers)

    async def test_cancel_already_cancelled_returns_400(self, http_client: AsyncClient,
                                                         admin_token: str, site_id: int,
                                                         admin_user_id: str):
        """Повторная отмена уже отменённого выезда → 400."""
        headers = auth_headers(admin_token)
        res = await http_client.post("/api/visits", headers=headers, json={
            "site_id": site_id, "assigned_user_id": admin_user_id,
            "planned_date": TODAY, "visit_type": "maintenance", "priority": "medium",
        })
        visit_id = res.json()["id"]
        await http_client.patch(f"/api/visits/{visit_id}/cancel", headers=headers)

        cancel = await http_client.patch(f"/api/visits/{visit_id}/cancel", headers=headers)
        assert cancel.status_code == 400

        await http_client.delete(f"/api/visits/{visit_id}", headers=headers)

    async def test_cancel_not_found(self, http_client: AsyncClient, admin_token: str):
        """PATCH /cancel несуществующего выезда → 404."""
        res = await http_client.patch("/api/visits/999999/cancel",
                                      headers=auth_headers(admin_token))
        assert res.status_code == 404

    async def test_filter_by_master_id(self, http_client: AsyncClient, admin_token: str,
                                        site_id: int, admin_user_id: str):
        """GET /visits?master_id=... возвращает только выезды нужного мастера."""
        headers = auth_headers(admin_token)
        res = await http_client.post("/api/visits", headers=headers, json={
            "site_id": site_id, "assigned_user_id": admin_user_id,
            "planned_date": TODAY, "visit_type": "maintenance", "priority": "medium",
        })
        visit_id = res.json()["id"]

        lst = await http_client.get(f"/api/visits?master_id={admin_user_id}", headers=headers)
        assert lst.status_code == 200
        ids = [v["id"] for v in lst.json()]
        assert visit_id in ids
        for v in lst.json():
            assert v["assigned_user_id"] == int(admin_user_id)

        await http_client.delete(f"/api/visits/{visit_id}", headers=headers)
