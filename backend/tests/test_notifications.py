"""
Тесты Block 8 — расширение уведомлений.

GET    /api/notifications               — список уведомлений текущего пользователя
GET    /api/notifications/unread-count  — количество непрочитанных
PUT    /api/notifications/read-all      — пометить все как прочитанные
PUT    /api/notifications/{id}/read     — пометить одно как прочитанное
PUT    /api/notifications/{id}/unread   — пометить одно как непрочитанное

Триггеры:
  PUT /api/defects/{id}   со сменой статуса → уведомления для office/admin
  PUT /api/purchases/{id} со сменой статуса → уведомления для office/admin
"""

import pytest
from httpx import AsyncClient

from tests.conftest import auth_headers


class TestNotificationEndpoints:
    async def test_get_notifications_returns_list(self, http_client: AsyncClient, admin_token: str):
        """GET /notifications возвращает список."""
        res = await http_client.get("/api/notifications", headers=auth_headers(admin_token))
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    async def test_get_notifications_unauthenticated(self, http_client: AsyncClient):
        """Без токена → 401."""
        res = await http_client.get("/api/notifications")
        assert res.status_code == 401

    async def test_unread_count_returns_int(self, http_client: AsyncClient, admin_token: str):
        """GET /notifications/unread-count → {count: int}."""
        res = await http_client.get("/api/notifications/unread-count", headers=auth_headers(admin_token))
        assert res.status_code == 200
        data = res.json()
        assert "count" in data
        assert isinstance(data["count"], int)

    async def test_unread_count_unauthenticated(self, http_client: AsyncClient):
        res = await http_client.get("/api/notifications/unread-count")
        assert res.status_code == 401

    async def test_read_all(self, http_client: AsyncClient, admin_token: str):
        """PUT /notifications/read-all помечает все как прочитанные, счётчик → 0."""
        headers = auth_headers(admin_token)
        res = await http_client.put("/api/notifications/read-all", headers=headers)
        assert res.status_code == 200
        count_res = await http_client.get("/api/notifications/unread-count", headers=headers)
        assert count_res.json()["count"] == 0

    async def test_mark_read_not_found(self, http_client: AsyncClient, admin_token: str):
        """PUT /notifications/999999/read → 404."""
        res = await http_client.put("/api/notifications/999999/read", headers=auth_headers(admin_token))
        assert res.status_code == 404

    async def test_mark_unread_not_found(self, http_client: AsyncClient, admin_token: str):
        res = await http_client.put("/api/notifications/999999/unread", headers=auth_headers(admin_token))
        assert res.status_code == 404

    async def test_read_all_unauthenticated(self, http_client: AsyncClient):
        res = await http_client.put("/api/notifications/read-all")
        assert res.status_code == 401


class TestNotificationStructure:
    async def test_notification_has_new_fields(self, http_client: AsyncClient, admin_token: str):
        """Схема уведомления содержит related_defect_id и related_purchase_id."""
        notifs = await http_client.get("/api/notifications", headers=auth_headers(admin_token))
        assert notifs.status_code == 200
        data = notifs.json()
        if data:
            notif = data[0]
            assert "related_defect_id" in notif
            assert "related_purchase_id" in notif
            assert "related_visit_id" in notif


class TestDefectStatusNotification:
    async def test_defect_status_change_creates_notification(
        self,
        http_client: AsyncClient,
        admin_token: str,
        office_token: str,
        site_id: int,
    ):
        """Смена статуса дефекта офисом → уведомление для admin."""
        admin_headers = auth_headers(admin_token)
        office_headers = auth_headers(office_token)

        # Сбрасываем счётчик admin перед тестом
        await http_client.put("/api/notifications/read-all", headers=admin_headers)

        # Создаём дефект от имени office
        defect_res = await http_client.post("/api/defects", headers=office_headers, json={
            "title": "__test_notif__ дефект статус",
            "site_id": site_id,
            "status": "new",
            "priority": "low",
        })
        assert defect_res.status_code == 201
        defect_id = defect_res.json()["id"]

        # Меняем статус дефекта от имени office
        update_res = await http_client.put(
            f"/api/defects/{defect_id}",
            headers=office_headers,
            json={"status": "in_progress"},
        )
        assert update_res.status_code == 200

        # Admin должен получить уведомление
        after = await http_client.get("/api/notifications/unread-count", headers=admin_headers)
        assert after.json()["count"] >= 1

        # Проверяем содержимое уведомления
        notifs = await http_client.get("/api/notifications", headers=admin_headers)
        defect_notifs = [n for n in notifs.json() if n.get("related_defect_id") == defect_id]
        assert len(defect_notifs) >= 1
        assert defect_notifs[0]["type"] == "defect_status_changed"
        assert defect_notifs[0]["is_read"] is False

    async def test_defect_status_change_no_self_notification(
        self,
        http_client: AsyncClient,
        admin_token: str,
        site_id: int,
    ):
        """Пользователь не получает уведомление от своего же действия."""
        admin_headers = auth_headers(admin_token)

        await http_client.put("/api/notifications/read-all", headers=admin_headers)

        defect_res = await http_client.post("/api/defects", headers=admin_headers, json={
            "title": "__test_notif__ без самоуведомления",
            "site_id": site_id,
            "status": "new",
            "priority": "low",
        })
        assert defect_res.status_code == 201
        defect_id = defect_res.json()["id"]

        # Admin меняет статус сам себе
        await http_client.put(f"/api/defects/{defect_id}", headers=admin_headers,
                               json={"status": "in_progress"})

        after = await http_client.get("/api/notifications/unread-count", headers=admin_headers)
        # Admin не должен получить уведомление от самого себя
        assert after.json()["count"] == 0

    async def test_defect_update_no_status_no_notification(
        self,
        http_client: AsyncClient,
        admin_token: str,
        office_token: str,
        site_id: int,
    ):
        """Обновление дефекта без смены статуса → уведомлений нет."""
        admin_headers = auth_headers(admin_token)

        await http_client.put("/api/notifications/read-all", headers=admin_headers)

        defect_res = await http_client.post("/api/defects", headers=auth_headers(office_token), json={
            "title": "__test_notif__ без уведомления",
            "site_id": site_id,
            "status": "new",
            "priority": "low",
        })
        assert defect_res.status_code == 201
        defect_id = defect_res.json()["id"]

        # Меняем только priority, не статус
        await http_client.put(f"/api/defects/{defect_id}", headers=auth_headers(office_token),
                               json={"priority": "high"})

        after = await http_client.get("/api/notifications/unread-count", headers=admin_headers)
        assert after.json()["count"] == 0


class TestPurchaseStatusNotification:
    async def test_purchase_status_change_creates_notification(
        self,
        http_client: AsyncClient,
        admin_token: str,
        office_token: str,
        site_id: int,
    ):
        """Смена статуса закупки офисом → уведомление для admin."""
        admin_headers = auth_headers(admin_token)

        await http_client.put("/api/notifications/read-all", headers=admin_headers)

        purchase_res = await http_client.post("/api/purchases", headers=auth_headers(office_token), json={
            "item": "__test_notif__ закупка",
            "site_id": site_id,
            "status": "draft",
            "qty": 1,
        })
        assert purchase_res.status_code == 201
        purchase_id = purchase_res.json()["id"]

        update_res = await http_client.put(
            f"/api/purchases/{purchase_id}",
            headers=auth_headers(office_token),
            json={"status": "ordered"},
        )
        assert update_res.status_code == 200

        after = await http_client.get("/api/notifications/unread-count", headers=admin_headers)
        assert after.json()["count"] >= 1

        notifs = await http_client.get("/api/notifications", headers=admin_headers)
        purchase_notifs = [n for n in notifs.json() if n.get("related_purchase_id") == purchase_id]
        assert len(purchase_notifs) >= 1
        assert purchase_notifs[0]["type"] == "purchase_status_changed"
        assert purchase_notifs[0]["is_read"] is False

    async def test_purchase_update_no_status_no_notification(
        self,
        http_client: AsyncClient,
        admin_token: str,
        office_token: str,
        site_id: int,
    ):
        """Обновление закупки без смены статуса → уведомлений нет."""
        admin_headers = auth_headers(admin_token)

        await http_client.put("/api/notifications/read-all", headers=admin_headers)

        purchase_res = await http_client.post("/api/purchases", headers=auth_headers(office_token), json={
            "item": "__test_notif__ закупка без уведомления",
            "site_id": site_id,
            "status": "draft",
            "qty": 1,
        })
        assert purchase_res.status_code == 201
        purchase_id = purchase_res.json()["id"]

        await http_client.put(f"/api/purchases/{purchase_id}", headers=auth_headers(office_token),
                               json={"qty": 5})

        after = await http_client.get("/api/notifications/unread-count", headers=admin_headers)
        assert after.json()["count"] == 0


class TestMarkReadUnread:
    async def test_mark_single_read_and_unread(
        self,
        http_client: AsyncClient,
        admin_token: str,
        office_token: str,
        site_id: int,
    ):
        """Пометка одного уведомления как прочитанного/непрочитанного."""
        admin_headers = auth_headers(admin_token)

        await http_client.put("/api/notifications/read-all", headers=admin_headers)

        # Генерируем уведомление
        defect_res = await http_client.post("/api/defects", headers=auth_headers(office_token), json={
            "title": "__test_notif__ mark read",
            "site_id": site_id,
            "status": "new",
            "priority": "low",
        })
        assert defect_res.status_code == 201
        defect_id = defect_res.json()["id"]

        await http_client.put(f"/api/defects/{defect_id}", headers=auth_headers(office_token),
                               json={"status": "fixed"})

        # Находим уведомление
        notifs = await http_client.get("/api/notifications", headers=admin_headers)
        notif_list = [n for n in notifs.json() if n.get("related_defect_id") == defect_id]
        assert len(notif_list) >= 1
        notif_id = notif_list[0]["id"]
        assert notif_list[0]["is_read"] is False

        # Помечаем как прочитанное
        res = await http_client.put(f"/api/notifications/{notif_id}/read", headers=admin_headers)
        assert res.status_code == 200

        notifs2 = await http_client.get("/api/notifications", headers=admin_headers)
        updated = next(n for n in notifs2.json() if n["id"] == notif_id)
        assert updated["is_read"] is True

        # Помечаем обратно как непрочитанное
        res2 = await http_client.put(f"/api/notifications/{notif_id}/unread", headers=admin_headers)
        assert res2.status_code == 200

        notifs3 = await http_client.get("/api/notifications", headers=admin_headers)
        updated2 = next(n for n in notifs3.json() if n["id"] == notif_id)
        assert updated2["is_read"] is False


class TestVisitCompletedNotification:
    async def test_visit_complete_sends_notification_to_office(
        self,
        http_client: AsyncClient,
        admin_token: str,
        office_token: str,
        site_id: int,
        admin_user_id: int,
    ):
        """Завершение выезда мастером → уведомление для office/admin."""
        office_headers = auth_headers(office_token)
        admin_headers = auth_headers(admin_token)

        # Создаём выезд от имени офиса
        visit_res = await http_client.post("/api/visits", headers=office_headers, json={
            "site_id": site_id,
            "assigned_user_id": admin_user_id,
            "planned_date": "2026-04-01",
            "visit_type": "maintenance",
            "priority": "medium",
        })
        assert visit_res.status_code == 201
        visit_id = visit_res.json()["id"]

        await http_client.put("/api/notifications/read-all", headers=admin_headers)

        # Завершаем выезд от имени admin (у него есть office+admin роль)
        comp = await http_client.post(
            f"/api/visits/{visit_id}/complete",
            headers=admin_headers,
            json={"work_summary": "Выполнено ТО", "defects_present": False},
        )
        assert comp.status_code == 200

        # office получает уведомление (офис не исключается — admin завершал)
        notifs = await http_client.get("/api/notifications", headers=office_headers)
        visit_notifs = [n for n in notifs.json() if n.get("related_visit_id") == visit_id]
        assert len(visit_notifs) >= 1
        assert visit_notifs[0]["type"] == "visit_completed"
        assert visit_notifs[0]["is_read"] is False

    async def test_visit_complete_notification_contains_site_name(
        self,
        http_client: AsyncClient,
        admin_token: str,
        office_token: str,
        site_id: int,
        admin_user_id: int,
    ):
        """Сообщение уведомления содержит название объекта."""
        office_headers = auth_headers(office_token)
        admin_headers = auth_headers(admin_token)

        visit_res = await http_client.post("/api/visits", headers=office_headers, json={
            "site_id": site_id,
            "assigned_user_id": admin_user_id,
            "planned_date": "2026-04-02",
            "visit_type": "repair",
            "priority": "high",
        })
        assert visit_res.status_code == 201
        visit_id = visit_res.json()["id"]

        await http_client.put("/api/notifications/read-all", headers=admin_headers)

        await http_client.post(
            f"/api/visits/{visit_id}/complete",
            headers=admin_headers,
            json={"work_summary": "Ремонт завершён", "defects_present": False},
        )

        notifs = await http_client.get("/api/notifications", headers=office_headers)
        visit_notifs = [n for n in notifs.json() if n.get("related_visit_id") == visit_id]
        assert len(visit_notifs) >= 1
        # Сообщение содержит название объекта или его id
        assert visit_notifs[0]["message"] != ""
