"""
Тесты детальной страницы объекта (Блок 3).

GET  /api/sites/{id}     — детальная карточка SiteDetailOut
POST /api/sites          — создание объекта с ценами
PUT  /api/sites/{id}     — обновление цен
POST /api/visits         — автоподстановка стоимости при создании выезда
"""

from httpx import AsyncClient
from tests.conftest import auth_headers

SITE_PAYLOAD = {
    "title": "__test_detail__ Объект с ценами",
    "address": "г. Тест, ул. Детали, д. 99",
    "price_maintenance": 5000.0,
    "price_repair": 8000.0,
    "price_emergency": 12000.0,
}


class TestSiteDetail:
    async def test_get_detail_returns_structure(self, http_client: AsyncClient, admin_token: str):
        """GET /:id возвращает SiteDetailOut с active_defects и recent_visits."""
        headers = auth_headers(admin_token)

        res = await http_client.post("/api/sites", headers=headers, json=SITE_PAYLOAD)
        assert res.status_code == 201
        site_id = res.json()["id"]

        detail = await http_client.get(f"/api/sites/{site_id}", headers=headers)
        assert detail.status_code == 200
        data = detail.json()
        assert data["id"] == site_id
        assert "active_defects" in data
        assert "recent_visits" in data
        assert isinstance(data["active_defects"], list)
        assert isinstance(data["recent_visits"], list)

        await http_client.delete(f"/api/sites/{site_id}", headers=headers)

    async def test_get_detail_has_prices(self, http_client: AsyncClient, admin_token: str):
        """GET /:id возвращает price_maintenance, price_repair, price_emergency."""
        headers = auth_headers(admin_token)

        res = await http_client.post("/api/sites", headers=headers, json=SITE_PAYLOAD)
        assert res.status_code == 201
        site_id = res.json()["id"]

        detail = await http_client.get(f"/api/sites/{site_id}", headers=headers)
        data = detail.json()
        assert data["price_maintenance"] == 5000.0
        assert data["price_repair"] == 8000.0
        assert data["price_emergency"] == 12000.0

        await http_client.delete(f"/api/sites/{site_id}", headers=headers)

    async def test_create_site_with_prices(self, http_client: AsyncClient, admin_token: str):
        """POST /sites сохраняет цены."""
        headers = auth_headers(admin_token)

        res = await http_client.post("/api/sites", headers=headers, json=SITE_PAYLOAD)
        assert res.status_code == 201
        data = res.json()
        assert data["price_maintenance"] == 5000.0
        assert data["price_repair"] == 8000.0
        assert data["price_emergency"] == 12000.0

        await http_client.delete(f"/api/sites/{data['id']}", headers=headers)

    async def test_update_site_prices(self, http_client: AsyncClient, admin_token: str):
        """PUT /sites/:id обновляет цены."""
        headers = auth_headers(admin_token)

        res = await http_client.post("/api/sites", headers=headers, json=SITE_PAYLOAD)
        site_id = res.json()["id"]

        upd = await http_client.put(f"/api/sites/{site_id}", headers=headers,
                                    json={"price_maintenance": 6500.0})
        assert upd.status_code == 200
        assert upd.json()["price_maintenance"] == 6500.0

        await http_client.delete(f"/api/sites/{site_id}", headers=headers)

    async def test_get_detail_not_found(self, http_client: AsyncClient, admin_token: str):
        """GET несуществующего объекта → 404."""
        fake_id = 999999
        res = await http_client.get(f"/api/sites/{fake_id}",
                                    headers=auth_headers(admin_token))
        assert res.status_code == 404


class TestVisitCostAutofill:
    async def test_cost_autofill_maintenance(
        self, http_client: AsyncClient, admin_token: str, admin_user_id: str
    ):
        """При создании выезда типа 'maintenance' cost подставляется из price_maintenance объекта."""
        headers = auth_headers(admin_token)

        site_res = await http_client.post("/api/sites", headers=headers, json=SITE_PAYLOAD)
        site_id = site_res.json()["id"]

        visit_res = await http_client.post("/api/visits", headers=headers, json={
            "site_id": site_id,
            "assigned_user_id": admin_user_id,
            "planned_date": "2099-06-01",
            "visit_type": "maintenance",
            "priority": "medium",
        })
        assert visit_res.status_code == 201
        data = visit_res.json()
        assert data["cost"] == 5000.0
        visit_id = data["id"]

        await http_client.delete(f"/api/visits/{visit_id}", headers=headers)
        await http_client.delete(f"/api/sites/{site_id}", headers=headers)

    async def test_cost_autofill_repair(
        self, http_client: AsyncClient, admin_token: str, admin_user_id: str
    ):
        """При создании выезда типа 'repair' cost подставляется из price_repair."""
        headers = auth_headers(admin_token)

        site_res = await http_client.post("/api/sites", headers=headers, json=SITE_PAYLOAD)
        site_id = site_res.json()["id"]

        visit_res = await http_client.post("/api/visits", headers=headers, json={
            "site_id": site_id,
            "assigned_user_id": admin_user_id,
            "planned_date": "2099-06-02",
            "visit_type": "repair",
            "priority": "high",
        })
        assert visit_res.status_code == 201
        assert visit_res.json()["cost"] == 8000.0

        visit_id = visit_res.json()["id"]
        await http_client.delete(f"/api/visits/{visit_id}", headers=headers)
        await http_client.delete(f"/api/sites/{site_id}", headers=headers)

    async def test_cost_autofill_emergency(
        self, http_client: AsyncClient, admin_token: str, admin_user_id: str
    ):
        """При создании выезда типа 'emergency' cost подставляется из price_emergency."""
        headers = auth_headers(admin_token)

        site_res = await http_client.post("/api/sites", headers=headers, json=SITE_PAYLOAD)
        site_id = site_res.json()["id"]

        visit_res = await http_client.post("/api/visits", headers=headers, json={
            "site_id": site_id,
            "assigned_user_id": admin_user_id,
            "planned_date": "2099-06-03",
            "visit_type": "emergency",
            "priority": "critical",
        })
        assert visit_res.status_code == 201
        assert visit_res.json()["cost"] == 12000.0

        visit_id = visit_res.json()["id"]
        await http_client.delete(f"/api/visits/{visit_id}", headers=headers)
        await http_client.delete(f"/api/sites/{site_id}", headers=headers)

    async def test_cost_manual_override(
        self, http_client: AsyncClient, admin_token: str, admin_user_id: str
    ):
        """Если cost передан явно, автоподстановка не перезаписывает его."""
        headers = auth_headers(admin_token)

        site_res = await http_client.post("/api/sites", headers=headers, json=SITE_PAYLOAD)
        site_id = site_res.json()["id"]

        visit_res = await http_client.post("/api/visits", headers=headers, json={
            "site_id": site_id,
            "assigned_user_id": admin_user_id,
            "planned_date": "2099-06-04",
            "visit_type": "maintenance",
            "priority": "low",
            "cost": 9999.0,
        })
        assert visit_res.status_code == 201
        assert visit_res.json()["cost"] == 9999.0

        visit_id = visit_res.json()["id"]
        await http_client.delete(f"/api/visits/{visit_id}", headers=headers)
        await http_client.delete(f"/api/sites/{site_id}", headers=headers)

    async def test_cost_none_when_no_price(
        self, http_client: AsyncClient, admin_token: str, admin_user_id: str
    ):
        """Если у объекта нет цен — cost остаётся null."""
        headers = auth_headers(admin_token)

        site_res = await http_client.post("/api/sites", headers=headers, json={
            "title": "__test_detail__ Объект без цен",
            "address": "г. Тест, ул. Нет цен, д. 1",
        })
        site_id = site_res.json()["id"]

        visit_res = await http_client.post("/api/visits", headers=headers, json={
            "site_id": site_id,
            "assigned_user_id": admin_user_id,
            "planned_date": "2099-06-05",
            "visit_type": "maintenance",
            "priority": "medium",
        })
        assert visit_res.status_code == 201
        assert visit_res.json()["cost"] is None

        visit_id = visit_res.json()["id"]
        await http_client.delete(f"/api/visits/{visit_id}", headers=headers)
        await http_client.delete(f"/api/sites/{site_id}", headers=headers)
