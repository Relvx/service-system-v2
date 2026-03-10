"""
Тесты блока 10 — Календарь + Карта UI.

- GET /api/visits/calendar — доступен мастеру
- GET /api/visits?master_id=X&date_from=... — фильтрация для карты
- GET /api/users/masters — список мастеров для фильтра в календаре
"""

import datetime
from httpx import AsyncClient
from tests.conftest import auth_headers

TODAY = datetime.date.today().isoformat()
FUTURE = (datetime.date.today() + datetime.timedelta(days=30)).isoformat()


class TestCalendarBlock10:
    async def test_master_can_access_calendar(self, http_client: AsyncClient, master_token: str):
        """Мастер имеет доступ к эндпоинту календаря."""
        res = await http_client.get(
            f"/api/visits/calendar?start={TODAY}&end={FUTURE}",
            headers=auth_headers(master_token),
        )
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    async def test_calendar_returns_assigned_user_id(self, http_client: AsyncClient, admin_token: str):
        """Ответ календаря содержит assigned_user_id для фильтрации по мастеру."""
        res = await http_client.get(
            f"/api/visits/calendar?start={TODAY}&end={FUTURE}",
            headers=auth_headers(admin_token),
        )
        assert res.status_code == 200
        data = res.json()
        # Если есть выезды — проверяем наличие поля
        for v in data:
            assert "assigned_user_id" in v
            assert "master_name" in v
            assert "site_title" in v

    async def test_visits_filter_by_master_id(
        self, http_client: AsyncClient, admin_token: str, site_id: int, admin_user_id: str
    ):
        """GET /api/visits?master_id= возвращает только выезды этого мастера."""
        headers = auth_headers(admin_token)

        # Создаём выезд на имя admin_user_id
        res = await http_client.post(
            "/api/visits",
            headers=headers,
            json={
                "site_id": site_id,
                "assigned_user_id": int(admin_user_id),
                "planned_date": TODAY,
                "visit_type": "maintenance",
                "priority": "medium",
                "status": "planned",
            },
        )
        assert res.status_code == 201
        visit_id = res.json()["id"]

        # Фильтрация по мастеру — должен вернуть наш выезд
        res2 = await http_client.get(
            f"/api/visits?master_id={admin_user_id}&date_from={TODAY}&date_to={TODAY}",
            headers=headers,
        )
        assert res2.status_code == 200
        ids = [v["id"] for v in res2.json()]
        assert visit_id in ids

        # Фильтрация по несуществующему мастеру — не должен вернуть наш выезд
        res3 = await http_client.get(
            f"/api/visits?master_id=999999&date_from={TODAY}&date_to={TODAY}",
            headers=headers,
        )
        assert res3.status_code == 200
        ids3 = [v["id"] for v in res3.json()]
        assert visit_id not in ids3

        # Cleanup
        await http_client.delete(f"/api/visits/{visit_id}", headers=headers)

    async def test_visits_date_filter_for_map(
        self, http_client: AsyncClient, admin_token: str, site_id: int, admin_user_id: str
    ):
        """GET /api/visits?date_from=today фильтрует выезды начиная с сегодня."""
        headers = auth_headers(admin_token)

        res = await http_client.post(
            "/api/visits",
            headers=headers,
            json={
                "site_id": site_id,
                "assigned_user_id": int(admin_user_id),
                "planned_date": TODAY,
                "visit_type": "repair",
                "priority": "high",
                "status": "planned",
            },
        )
        assert res.status_code == 201
        visit_id = res.json()["id"]

        res2 = await http_client.get(
            f"/api/visits?date_from={TODAY}",
            headers=headers,
        )
        assert res2.status_code == 200
        ids = [v["id"] for v in res2.json()]
        assert visit_id in ids

        # Cleanup
        await http_client.delete(f"/api/visits/{visit_id}", headers=headers)


class TestMastersEndpointBlock10:
    async def test_get_masters_admin(self, http_client: AsyncClient, admin_token: str):
        """Администратор получает список мастеров."""
        res = await http_client.get("/api/users/masters", headers=auth_headers(admin_token))
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        for m in data:
            assert "id" in m
            assert "full_name" in m

    async def test_get_masters_office(self, http_client: AsyncClient, office_token: str):
        """Офис получает список мастеров."""
        res = await http_client.get("/api/users/masters", headers=auth_headers(office_token))
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    async def test_get_masters_unauthenticated(self, http_client: AsyncClient):
        """Неаутентифицированный запрос отклоняется."""
        res = await http_client.get("/api/users/masters")
        assert res.status_code == 401
