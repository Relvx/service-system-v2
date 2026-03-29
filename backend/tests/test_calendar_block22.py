"""
Block 22 — Календарь: корректность эндпоинта /visits/calendar.

Проверяем:
1. Эндпоинт возвращает выезды в диапазоне дат
2. Выезды вне диапазона не возвращаются
3. Фильтрация по master_id работает
"""
import pytest
from datetime import date, timedelta
from httpx import AsyncClient
from tests.conftest import auth_headers


@pytest.mark.asyncio
class TestCalendarEndpoint:

    async def _get_any_master(self, http_client: AsyncClient, admin_h: dict) -> int:
        """Возвращает ID любого мастера из системы."""
        res = await http_client.get("/api/users/masters", headers=admin_h)
        assert res.status_code == 200
        masters = res.json()
        assert len(masters) > 0, "Нет мастеров в системе"
        return masters[0]["id"]

    async def test_calendar_returns_visits_in_range(self, http_client: AsyncClient, admin_token: str, office_token: str):
        """GET /visits/calendar возвращает выезды в заданном диапазоне."""
        admin_h = auth_headers(admin_token)
        master_id = await self._get_any_master(http_client, admin_h)

        today = date.today().isoformat()
        tomorrow = (date.today() + timedelta(days=1)).isoformat()

        r_client = await http_client.post("/api/clients", headers=admin_h, json={"name": "B22_CAL_CLIENT"})
        assert r_client.status_code == 201
        client_id = r_client.json()["id"]

        r_site = await http_client.post("/api/sites", headers=admin_h, json={
            "title": "B22_CAL_SITE", "client_id": client_id, "address": "Тест"
        })
        assert r_site.status_code == 201
        site_id = r_site.json()["id"]

        r_visit = await http_client.post("/api/visits", headers=admin_h, json={
            "site_id": site_id,
            "planned_date": today,
            "assigned_user_id": master_id,
        })
        assert r_visit.status_code == 201
        visit_id = r_visit.json()["id"]

        try:
            res = await http_client.get(
                f"/api/visits/calendar?start={today}&end={tomorrow}",
                headers=auth_headers(office_token),
            )
            assert res.status_code == 200
            ids = [v["id"] for v in res.json()]
            assert visit_id in ids

        finally:
            await http_client.delete(f"/api/visits/{visit_id}", headers=admin_h)
            await http_client.delete(f"/api/sites/{site_id}", headers=admin_h)
            await http_client.delete(f"/api/clients/{client_id}", headers=admin_h)

    async def test_calendar_excludes_out_of_range(self, http_client: AsyncClient, admin_token: str):
        """GET /visits/calendar не возвращает выезды вне диапазона."""
        admin_h = auth_headers(admin_token)
        master_id = await self._get_any_master(http_client, admin_h)

        today = date.today().isoformat()
        next_month = (date.today() + timedelta(days=32)).isoformat()
        far_future = (date.today() + timedelta(days=60)).isoformat()

        r_client = await http_client.post("/api/clients", headers=admin_h, json={"name": "B22_OUT_CLIENT"})
        assert r_client.status_code == 201
        client_id = r_client.json()["id"]

        r_site = await http_client.post("/api/sites", headers=admin_h, json={
            "title": "B22_OUT_SITE", "client_id": client_id, "address": "Тест"
        })
        assert r_site.status_code == 201
        site_id = r_site.json()["id"]

        r_visit = await http_client.post("/api/visits", headers=admin_h, json={
            "site_id": site_id,
            "planned_date": far_future,
            "assigned_user_id": master_id,
        })
        assert r_visit.status_code == 201
        visit_id = r_visit.json()["id"]

        try:
            res = await http_client.get(
                f"/api/visits/calendar?start={today}&end={next_month}",
                headers=admin_h,
            )
            assert res.status_code == 200
            ids = [v["id"] for v in res.json()]
            assert visit_id not in ids

        finally:
            await http_client.delete(f"/api/visits/{visit_id}", headers=admin_h)
            await http_client.delete(f"/api/sites/{site_id}", headers=admin_h)
            await http_client.delete(f"/api/clients/{client_id}", headers=admin_h)

    async def test_calendar_master_filter(self, http_client: AsyncClient, admin_token: str, office_token: str):
        """GET /visits/calendar?master_id= фильтрует по мастеру."""
        admin_h = auth_headers(admin_token)
        master_id = await self._get_any_master(http_client, admin_h)

        today = date.today().isoformat()
        tomorrow = (date.today() + timedelta(days=1)).isoformat()

        r_client = await http_client.post("/api/clients", headers=admin_h, json={"name": "B22_MASTER_CLIENT"})
        assert r_client.status_code == 201
        client_id = r_client.json()["id"]

        r_site = await http_client.post("/api/sites", headers=admin_h, json={
            "title": "B22_MASTER_SITE", "client_id": client_id, "address": "Тест"
        })
        assert r_site.status_code == 201
        site_id = r_site.json()["id"]

        r_visit = await http_client.post("/api/visits", headers=admin_h, json={
            "site_id": site_id,
            "planned_date": today,
            "assigned_user_id": master_id,
        })
        assert r_visit.status_code == 201
        visit_id = r_visit.json()["id"]

        try:
            # С фильтром по мастеру — выезд есть
            res_filtered = await http_client.get(
                f"/api/visits/calendar?start={today}&end={tomorrow}&master_id={master_id}",
                headers=auth_headers(office_token),
            )
            assert res_filtered.status_code == 200
            ids_filtered = [v["id"] for v in res_filtered.json()]
            assert visit_id in ids_filtered

        finally:
            await http_client.delete(f"/api/visits/{visit_id}", headers=admin_h)
            await http_client.delete(f"/api/sites/{site_id}", headers=admin_h)
            await http_client.delete(f"/api/clients/{client_id}", headers=admin_h)
