"""
Тесты эндпоинтов дефектов.

GET  /api/defects        — список дефектов
POST /api/defects        — создание дефекта
PUT  /api/defects/{id}   — обновление / смена статуса дефекта
"""

from httpx import AsyncClient
from tests.conftest import auth_headers

DEFECT_PAYLOAD = {
    "title": "__test__ Тестовый дефект",
    "description": "Обнаружена неисправность в системе отопления",
    "priority": "medium",
    "action_type": "repair",
    "status": "open",
}


class TestGetDefects:
    async def test_list_returns_list(self, http_client: AsyncClient, admin_token: str):
        res = await http_client.get("/api/defects", headers=auth_headers(admin_token))
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    async def test_filter_by_status(self, http_client: AsyncClient, admin_token: str):
        res = await http_client.get("/api/defects?status=open",
                                    headers=auth_headers(admin_token))
        assert res.status_code == 200
        for d in res.json():
            assert d["status"] == "open"

    async def test_filter_by_priority(self, http_client: AsyncClient, admin_token: str):
        res = await http_client.get("/api/defects?priority=high",
                                    headers=auth_headers(admin_token))
        assert res.status_code == 200
        for d in res.json():
            assert d["priority"] == "high"

    async def test_list_unauthenticated(self, http_client: AsyncClient):
        res = await http_client.get("/api/defects")
        assert res.status_code == 401


class TestDefectCRUD:
    async def test_create(self, http_client: AsyncClient, admin_token: str):
        headers = auth_headers(admin_token)

        res = await http_client.post("/api/defects", headers=headers, json=DEFECT_PAYLOAD)
        assert res.status_code == 201
        data = res.json()
        assert data["title"] == DEFECT_PAYLOAD["title"]
        assert data["status"] == "open"
        return data["id"]

    async def test_update_status(self, http_client: AsyncClient, admin_token: str):
        headers = auth_headers(admin_token)

        res = await http_client.post("/api/defects", headers=headers, json=DEFECT_PAYLOAD)
        defect_id = res.json()["id"]

        upd = await http_client.put(f"/api/defects/{defect_id}", headers=headers,
                                     json={"status": "in_progress"})
        assert upd.status_code == 200
        assert upd.json()["status"] == "in_progress"

    async def test_approve_defect(self, http_client: AsyncClient, admin_token: str):
        headers = auth_headers(admin_token)

        res = await http_client.post("/api/defects", headers=headers, json=DEFECT_PAYLOAD)
        defect_id = res.json()["id"]

        upd = await http_client.put(f"/api/defects/{defect_id}", headers=headers,
                                     json={"status": "approved"})
        assert upd.status_code == 200
        assert upd.json()["status"] == "approved"

    async def test_update_not_found(self, http_client: AsyncClient, admin_token: str):
        fake_id = 999999
        res = await http_client.put(f"/api/defects/{fake_id}",
                                     headers=auth_headers(admin_token),
                                     json={"status": "closed"})
        assert res.status_code == 404


class TestDefectBlock5:
    """Блок 5: создание дефекта офисом, привязка к объекту, фильтрация."""

    async def test_create_with_site_id(self, http_client: AsyncClient, admin_token: str,
                                       site_id: int):
        """Создание дефекта с site_id → site_title подтягивается из JOIN."""
        headers = auth_headers(admin_token)
        res = await http_client.post("/api/defects", headers=headers, json={
            **DEFECT_PAYLOAD,
            "site_id": site_id,
        })
        assert res.status_code == 201
        data = res.json()
        assert data["site_id"] == site_id
        assert data["site_title"] is not None

    async def test_create_with_suggested_parts(self, http_client: AsyncClient, admin_token: str):
        """Создание дефекта с полем suggested_parts → поле возвращается в ответе."""
        headers = auth_headers(admin_token)
        res = await http_client.post("/api/defects", headers=headers, json={
            **DEFECT_PAYLOAD,
            "suggested_parts": "Прокладка 100мм, термостат",
        })
        assert res.status_code == 201
        assert res.json()["suggested_parts"] == "Прокладка 100мм, термостат"

    async def test_filter_by_site_id(self, http_client: AsyncClient, admin_token: str,
                                     site_id: int):
        """GET /defects?site_id=... возвращает только дефекты нужного объекта."""
        headers = auth_headers(admin_token)
        # создаём дефект с известным site_id
        await http_client.post("/api/defects", headers=headers, json={
            **DEFECT_PAYLOAD, "site_id": site_id,
        })
        res = await http_client.get(f"/api/defects?site_id={site_id}", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert len(data) >= 1
        for d in data:
            assert d["site_id"] == site_id

    async def test_client_name_populated_via_site(self, http_client: AsyncClient,
                                                   admin_token: str, site_id: int):
        """client_name заполняется в ответе через JOIN Site → Client."""
        headers = auth_headers(admin_token)
        res = await http_client.post("/api/defects", headers=headers, json={
            **DEFECT_PAYLOAD, "site_id": site_id,
        })
        assert res.status_code == 201
        # site_id создан conftest'ом и привязан к тестовому клиенту
        assert res.json()["client_name"] is not None
