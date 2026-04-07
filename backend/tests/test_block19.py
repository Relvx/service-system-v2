"""
Тесты блока 19 — Выезды: расширение функционала.

1. Несколько мастеров: создание с master_ids, проверка visit_masters
2. Несколько типов выезда: создание с visit_types, проверка
3. Редактирование master_ids и visit_types через PUT
4. contract_id передаётся при создании и сохраняется
5. client_id возвращается в VisitOut
6. master_names и master_ids возвращаются в VisitOut
"""

import pytest
from datetime import date, timedelta
from httpx import AsyncClient
from tests.conftest import auth_headers

FUTURE = str(date.today() + timedelta(days=5))


@pytest.mark.asyncio
class TestMultiMasters:
    """Несколько мастеров на один выезд."""

    async def test_create_visit_with_master_ids(
        self, http_client: AsyncClient, admin_token: str, site_id: int, admin_user_id: int
    ):
        """Создание выезда с master_ids возвращает master_ids и master_names."""
        payload = {
            "site_id": site_id,
            "master_ids": [admin_user_id],
            "planned_date": FUTURE,
            "visit_type": "maintenance",
        }
        res = await http_client.post("/api/visits", json=payload, headers=auth_headers(admin_token))
        assert res.status_code == 201
        data = res.json()
        assert int(admin_user_id) in data["master_ids"]
        assert len(data["master_names"]) >= 1
        # cleanup
        await http_client.delete(f"/api/visits/{data['id']}", headers=auth_headers(admin_token))

    async def test_get_visit_has_master_ids(
        self, http_client: AsyncClient, admin_token: str, site_id: int, admin_user_id: int
    ):
        """GET /visits возвращает master_ids и master_names для каждого выезда."""
        # Создаём
        payload = {
            "site_id": site_id,
            "master_ids": [admin_user_id],
            "planned_date": FUTURE,
            "visit_type": "maintenance",
        }
        res = await http_client.post("/api/visits", json=payload, headers=auth_headers(admin_token))
        assert res.status_code == 201
        vid = res.json()["id"]

        # Получаем по ID
        r = await http_client.get(f"/api/visits/{vid}", headers=auth_headers(admin_token))
        assert r.status_code == 200
        d = r.json()
        assert "master_ids" in d
        assert isinstance(d["master_ids"], list)
        assert "master_names" in d
        assert isinstance(d["master_names"], list)

        # cleanup
        await http_client.delete(f"/api/visits/{vid}", headers=auth_headers(admin_token))

    async def test_update_visit_master_ids(
        self, http_client: AsyncClient, admin_token: str, site_id: int, admin_user_id: int
    ):
        """PUT /visits/{id} с master_ids обновляет список мастеров."""
        payload = {
            "site_id": site_id,
            "master_ids": [admin_user_id],
            "planned_date": FUTURE,
            "visit_type": "maintenance",
        }
        create_res = await http_client.post("/api/visits", json=payload, headers=auth_headers(admin_token))
        assert create_res.status_code == 201
        vid = create_res.json()["id"]

        # Обновляем мастеров (пустой список)
        update_res = await http_client.put(
            f"/api/visits/{vid}",
            json={"master_ids": []},
            headers=auth_headers(admin_token),
        )
        assert update_res.status_code == 200
        assert update_res.json()["master_ids"] == []

        # cleanup
        await http_client.delete(f"/api/visits/{vid}", headers=auth_headers(admin_token))

    async def test_filter_by_master_id_uses_visit_masters(
        self, http_client: AsyncClient, admin_token: str, site_id: int, admin_user_id: int
    ):
        """Фильтр master_id ищет по таблице visit_masters."""
        payload = {
            "site_id": site_id,
            "master_ids": [admin_user_id],
            "planned_date": FUTURE,
            "visit_type": "maintenance",
        }
        create_res = await http_client.post("/api/visits", json=payload, headers=auth_headers(admin_token))
        assert create_res.status_code == 201
        vid = create_res.json()["id"]

        filter_res = await http_client.get(
            f"/api/visits?master_id={admin_user_id}",
            headers=auth_headers(admin_token),
        )
        assert filter_res.status_code == 200
        ids = [v["id"] for v in filter_res.json()["items"]]
        assert vid in ids

        # cleanup
        await http_client.delete(f"/api/visits/{vid}", headers=auth_headers(admin_token))


@pytest.mark.asyncio
class TestMultiVisitTypes:
    """Несколько типов выезда."""

    async def test_create_visit_with_visit_types(
        self, http_client: AsyncClient, admin_token: str, site_id: int, admin_user_id: int
    ):
        """Создание выезда с visit_types сохраняет все типы."""
        payload = {
            "site_id": site_id,
            "master_ids": [admin_user_id],
            "planned_date": FUTURE,
            "visit_types": ["maintenance", "emergency"],
        }
        res = await http_client.post("/api/visits", json=payload, headers=auth_headers(admin_token))
        assert res.status_code == 201
        data = res.json()
        assert data["visit_types"] == ["maintenance", "emergency"]
        assert data["visit_type"] == "maintenance"  # первый = основной
        # cleanup
        await http_client.delete(f"/api/visits/{data['id']}", headers=auth_headers(admin_token))

    async def test_update_visit_types(
        self, http_client: AsyncClient, admin_token: str, site_id: int, admin_user_id: int
    ):
        """PUT позволяет изменить типы даже у завершённого выезда."""
        # Создаём
        payload = {
            "site_id": site_id,
            "master_ids": [admin_user_id],
            "planned_date": FUTURE,
            "visit_types": ["maintenance"],
            "status": "done",
        }
        create_res = await http_client.post("/api/visits", json=payload, headers=auth_headers(admin_token))
        assert create_res.status_code == 201
        vid = create_res.json()["id"]

        # Обновляем типы у завершённого
        upd = await http_client.put(
            f"/api/visits/{vid}",
            json={"visit_types": ["repair", "emergency"]},
            headers=auth_headers(admin_token),
        )
        assert upd.status_code == 200
        assert upd.json()["visit_types"] == ["repair", "emergency"]
        assert upd.json()["visit_type"] == "repair"

        # cleanup
        await http_client.delete(f"/api/visits/{vid}", headers=auth_headers(admin_token))


@pytest.mark.asyncio
class TestVisitContractAndClientId:
    """contract_id и client_id в выезде."""

    async def test_create_visit_with_contract_id(
        self, http_client: AsyncClient, admin_token: str, site_id: int, admin_user_id: int
    ):
        """contract_id сохраняется при создании."""
        # Получаем любой контракт из системы
        cr = await http_client.get("/api/contracts?limit=1", headers=auth_headers(admin_token))
        if not cr.json()["items"]:
            pytest.skip("Нет договоров в БД")
        contract_id = cr.json()["items"][0]["id"]

        payload = {
            "site_id": site_id,
            "master_ids": [admin_user_id],
            "planned_date": FUTURE,
            "visit_types": ["maintenance"],
            "contract_id": contract_id,
        }
        res = await http_client.post("/api/visits", json=payload, headers=auth_headers(admin_token))
        assert res.status_code == 201
        assert res.json()["contract_id"] == contract_id
        # cleanup
        await http_client.delete(f"/api/visits/{res.json()['id']}", headers=auth_headers(admin_token))

    async def test_visit_returns_client_id(
        self, http_client: AsyncClient, admin_token: str, site_id: int, admin_user_id: int
    ):
        """GET /visits/{id} возвращает client_id."""
        payload = {
            "site_id": site_id,
            "master_ids": [admin_user_id],
            "planned_date": FUTURE,
            "visit_types": ["maintenance"],
        }
        create_res = await http_client.post("/api/visits", json=payload, headers=auth_headers(admin_token))
        assert create_res.status_code == 201
        vid = create_res.json()["id"]

        r = await http_client.get(f"/api/visits/{vid}", headers=auth_headers(admin_token))
        assert r.status_code == 200
        # client_id может быть None если объект не привязан к клиенту
        assert "client_id" in r.json()

        # cleanup
        await http_client.delete(f"/api/visits/{vid}", headers=auth_headers(admin_token))

    async def test_visit_returns_contract_number(
        self, http_client: AsyncClient, admin_token: str, site_id: int, admin_user_id: int
    ):
        """GET /visits/{id} возвращает поле contract_number (null если нет договора)."""
        payload = {
            "site_id": site_id,
            "master_ids": [admin_user_id],
            "planned_date": FUTURE,
            "visit_types": ["maintenance"],
        }
        create_res = await http_client.post("/api/visits", json=payload, headers=auth_headers(admin_token))
        assert create_res.status_code == 201
        vid = create_res.json()["id"]

        r = await http_client.get(f"/api/visits/{vid}", headers=auth_headers(admin_token))
        assert r.status_code == 200
        assert "contract_number" in r.json()

        # cleanup
        await http_client.delete(f"/api/visits/{vid}", headers=auth_headers(admin_token))
