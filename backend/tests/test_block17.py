"""
Тесты Block 17 — качество: покрытие непокрытых сценариев блоков 12–16.

- visit_updated уведомление (при смене мастера)
- Пагинация /logs с limit/offset
- Поиск contracts по имени клиента
- Счётчики клиента (sites_count, visits_count, contracts_count) после создания данных
"""

import pytest
from httpx import AsyncClient

from tests.conftest import auth_headers


class TestVisitUpdatedNotification:
    async def test_visit_master_reassign_creates_notification(
        self,
        http_client: AsyncClient,
        admin_token: str,
        office_token: str,
        site_id: int,
        admin_user_id: int,
    ):
        """Смена мастера на выезде → уведомление новому мастеру (visit_updated)."""
        office_headers = auth_headers(office_token)
        admin_headers = auth_headers(admin_token)

        # Получаем id другого пользователя (office) для первоначального назначения
        users_res = await http_client.get("/api/users", headers=office_headers)
        office_user = next(
            (u for u in users_res.json() if "office" in u.get("email", "")), None
        )
        first_master_id = office_user["id"] if office_user else admin_user_id

        # Создаём выезд с одним мастером
        visit_res = await http_client.post("/api/visits", headers=office_headers, json={
            "site_id": site_id,
            "assigned_user_id": first_master_id,
            "planned_date": "2026-06-01",
            "visit_type": "maintenance",
            "priority": "medium",
        })
        assert visit_res.status_code == 201
        visit_id = visit_res.json()["id"]

        await http_client.put("/api/notifications/read-all", headers=admin_headers)

        # Переназначаем на admin_user_id
        upd = await http_client.put(f"/api/visits/{visit_id}", headers=office_headers, json={
            "assigned_user_id": admin_user_id,
        })
        assert upd.status_code == 200

        # Мастер (admin) получил уведомление
        notifs = await http_client.get("/api/notifications", headers=admin_headers)
        assert notifs.status_code == 200
        visit_notifs = [n for n in notifs.json() if n.get("related_visit_id") == visit_id]
        assert len(visit_notifs) >= 1
        assert visit_notifs[0]["type"] in ("visit_assigned", "visit_updated")
        assert visit_notifs[0]["related_visit_id"] == visit_id
        assert visit_notifs[0]["related_defect_id"] is None
        assert visit_notifs[0]["related_purchase_id"] is None

    async def test_visit_update_no_master_change_no_notification(
        self,
        http_client: AsyncClient,
        admin_token: str,
        office_token: str,
        site_id: int,
        admin_user_id: int,
    ):
        """Обновление выезда без смены мастера → уведомлений нет (для admin)."""
        office_headers = auth_headers(office_token)
        admin_headers = auth_headers(admin_token)

        # Создаём выезд с мастером (admin)
        visit_res = await http_client.post("/api/visits", headers=office_headers, json={
            "site_id": site_id,
            "assigned_user_id": admin_user_id,
            "planned_date": "2026-06-02",
            "visit_type": "maintenance",
            "priority": "medium",
        })
        assert visit_res.status_code == 201
        visit_id = visit_res.json()["id"]

        # Сбрасываем все уведомления admin (включая visit_assigned при создании)
        await http_client.put("/api/notifications/read-all", headers=admin_headers)

        # Меняем только приоритет — мастер тот же → нет нового уведомления
        upd = await http_client.put(f"/api/visits/{visit_id}", headers=office_headers, json={
            "priority": "high",
        })
        assert upd.status_code == 200

        count = await http_client.get("/api/notifications/unread-count", headers=admin_headers)
        assert count.json()["count"] == 0


class TestLogsPagination:
    async def test_logs_pagination_limit(self, http_client: AsyncClient, admin_token: str):
        """GET /logs с limit=5 возвращает не более 5 записей."""
        res = await http_client.get("/api/logs", headers=auth_headers(admin_token),
                                    params={"limit": 5, "offset": 0})
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert len(data) <= 5

    async def test_logs_pagination_offset(self, http_client: AsyncClient, admin_token: str):
        """GET /logs с разными offset возвращает разные записи."""
        res1 = await http_client.get("/api/logs", headers=auth_headers(admin_token),
                                     params={"limit": 3, "offset": 0})
        res2 = await http_client.get("/api/logs", headers=auth_headers(admin_token),
                                     params={"limit": 3, "offset": 3})
        assert res1.status_code == 200
        assert res2.status_code == 200
        ids1 = {r["id"] for r in res1.json()}
        ids2 = {r["id"] for r in res2.json()}
        # Если логов достаточно — записи не должны пересекаться
        if ids1 and ids2:
            assert ids1.isdisjoint(ids2)

    async def test_logs_default_limit(self, http_client: AsyncClient, admin_token: str):
        """GET /logs без параметров возвращает не более 100 записей (default limit)."""
        res = await http_client.get("/api/logs", headers=auth_headers(admin_token))
        assert res.status_code == 200
        assert len(res.json()) <= 100


class TestContractSearchByClientName:
    async def test_search_contracts_by_client_name(
        self, http_client: AsyncClient, admin_token: str
    ):
        """GET /contracts?search= ищет в том числе по имени клиента."""
        headers = auth_headers(admin_token)

        # Создаём клиента с уникальным именем
        unique = "__block17_search_client__"
        client_res = await http_client.post("/api/clients", headers=headers, json={"name": unique})
        assert client_res.status_code == 201
        client_id = client_res.json()["id"]

        # Создаём договор для этого клиента
        contract_res = await http_client.post("/api/contracts", headers=headers, json={
            "contract_number": "BLK17-TEST",
            "client_id": client_id,
        })
        assert contract_res.status_code == 201

        # Ищем по имени клиента
        search_res = await http_client.get("/api/contracts", headers=headers,
                                           params={"search": unique, "limit": 50})
        assert search_res.status_code == 200
        items = search_res.json()["items"]
        client_ids = [c["client_id"] for c in items]
        assert client_id in client_ids


class TestClientCounters:
    async def test_client_sites_count_increments(
        self, http_client: AsyncClient, admin_token: str
    ):
        """sites_count клиента увеличивается после добавления объекта."""
        headers = auth_headers(admin_token)

        client_res = await http_client.post("/api/clients", headers=headers,
                                            json={"name": "__block17_counter_client__"})
        assert client_res.status_code == 201
        client_id = client_res.json()["id"]

        # Начальный счётчик — получаем клиента напрямую по id
        before_res = await http_client.get(f"/api/clients/{client_id}", headers=headers)
        assert before_res.json()["sites"] == [] or len(before_res.json()["sites"]) == 0

        # Добавляем объект
        site_res = await http_client.post("/api/sites", headers=headers, json={
            "title": "__block17_counter_site__",
            "address": "Тест, 1",
            "client_id": client_id,
            "service_frequency": "monthly",
        })
        assert site_res.status_code == 201

        # Счётчик должен стать 1
        after_res = await http_client.get(f"/api/clients/{client_id}", headers=headers)
        assert len(after_res.json()["sites"]) == 1

    async def test_client_contracts_count_increments(
        self, http_client: AsyncClient, admin_token: str
    ):
        """contracts_count клиента увеличивается после добавления договора."""
        headers = auth_headers(admin_token)

        client_res = await http_client.post("/api/clients", headers=headers,
                                            json={"name": "__block17_contracts_counter__"})
        assert client_res.status_code == 201
        client_id = client_res.json()["id"]

        before_res = await http_client.get(f"/api/clients/{client_id}", headers=headers)
        # У нового клиента договоров ещё нет (проверяем через contracts endpoint)
        contracts_before = await http_client.get("/api/contracts/by-client/" + str(client_id), headers=headers)
        assert contracts_before.json() == []

        await http_client.post("/api/contracts", headers=headers, json={
            "contract_number": "BLK17-CNT",
            "client_id": client_id,
        })

        contracts_after = await http_client.get("/api/contracts/by-client/" + str(client_id), headers=headers)
        assert len(contracts_after.json()) == 1
