"""
Тесты Block 16 — навигация по уведомлениям (entity linkage).

Проверяет что уведомления содержат корректные related_*_id поля
для навигации на фронтенде к соответствующим сущностям.
"""

import pytest
from httpx import AsyncClient

from tests.conftest import auth_headers


class TestNotificationEntityLinkage:
    """related_*_id поля в уведомлениях заполняются корректно."""

    async def test_visit_assigned_notification_has_visit_id(
        self,
        http_client: AsyncClient,
        admin_token: str,
        office_token: str,
        site_id: int,
        admin_user_id: int,
    ):
        """Уведомление о назначении выезда содержит related_visit_id."""
        admin_headers = auth_headers(admin_token)
        office_headers = auth_headers(office_token)

        await http_client.put("/api/notifications/read-all", headers=admin_headers)

        visit_res = await http_client.post("/api/visits", headers=office_headers, json={
            "site_id": site_id,
            "assigned_user_id": admin_user_id,
            "planned_date": "2026-05-10",
            "visit_type": "maintenance",
            "priority": "medium",
        })
        assert visit_res.status_code == 201
        visit_id = visit_res.json()["id"]

        notifs = await http_client.get("/api/notifications", headers=admin_headers)
        assert notifs.status_code == 200

        visit_notifs = [n for n in notifs.json() if n.get("related_visit_id") == visit_id]
        assert len(visit_notifs) >= 1, "Уведомление о назначении выезда не найдено"

        notif = visit_notifs[0]
        assert notif["related_visit_id"] == visit_id
        assert notif["related_defect_id"] is None
        assert notif["related_purchase_id"] is None
        assert notif["type"] == "visit_assigned"

    async def test_defect_notification_has_defect_id(
        self,
        http_client: AsyncClient,
        admin_token: str,
        office_token: str,
        site_id: int,
    ):
        """Уведомление о смене статуса дефекта содержит related_defect_id."""
        admin_headers = auth_headers(admin_token)
        office_headers = auth_headers(office_token)

        await http_client.put("/api/notifications/read-all", headers=admin_headers)

        defect_res = await http_client.post("/api/defects", headers=office_headers, json={
            "title": "__block16__ defect linkage",
            "site_id": site_id,
            "status": "new",
            "priority": "medium",
        })
        assert defect_res.status_code == 201
        defect_id = defect_res.json()["id"]

        await http_client.put(f"/api/defects/{defect_id}", headers=office_headers,
                               json={"status": "in_progress"})

        notifs = await http_client.get("/api/notifications", headers=admin_headers)
        assert notifs.status_code == 200

        defect_notifs = [n for n in notifs.json() if n.get("related_defect_id") == defect_id]
        assert len(defect_notifs) >= 1, "Уведомление о дефекте не найдено"

        notif = defect_notifs[0]
        assert notif["related_defect_id"] == defect_id
        assert notif["related_visit_id"] is None
        assert notif["related_purchase_id"] is None
        assert notif["type"] == "defect_status_changed"

    async def test_purchase_notification_has_purchase_id(
        self,
        http_client: AsyncClient,
        admin_token: str,
        office_token: str,
        site_id: int,
    ):
        """Уведомление о смене статуса закупки содержит related_purchase_id."""
        admin_headers = auth_headers(admin_token)
        office_headers = auth_headers(office_token)

        await http_client.put("/api/notifications/read-all", headers=admin_headers)

        purchase_res = await http_client.post("/api/purchases", headers=office_headers, json={
            "item": "__block16__ purchase linkage",
            "site_id": site_id,
            "status": "draft",
            "qty": 2,
        })
        assert purchase_res.status_code == 201
        purchase_id = purchase_res.json()["id"]

        await http_client.put(f"/api/purchases/{purchase_id}", headers=office_headers,
                               json={"status": "ordered"})

        notifs = await http_client.get("/api/notifications", headers=admin_headers)
        assert notifs.status_code == 200

        purchase_notifs = [n for n in notifs.json() if n.get("related_purchase_id") == purchase_id]
        assert len(purchase_notifs) >= 1, "Уведомление о закупке не найдено"

        notif = purchase_notifs[0]
        assert notif["related_purchase_id"] == purchase_id
        assert notif["related_visit_id"] is None
        assert notif["related_defect_id"] is None
        assert notif["type"] == "purchase_status_changed"

    async def test_notification_schema_has_all_entity_fields(
        self,
        http_client: AsyncClient,
        admin_token: str,
    ):
        """Схема уведомления содержит все поля для навигации на фронте."""
        res = await http_client.get("/api/notifications", headers=auth_headers(admin_token))
        assert res.status_code == 200
        notifs = res.json()
        assert isinstance(notifs, list)

        if notifs:
            n = notifs[0]
            required_fields = [
                "id", "type", "title", "message", "is_read", "created_at",
                "related_visit_id", "related_defect_id", "related_purchase_id",
            ]
            for field in required_fields:
                assert field in n, f"Поле '{field}' отсутствует в схеме уведомления"

    async def test_visit_completed_notification_has_visit_id(
        self,
        http_client: AsyncClient,
        admin_token: str,
        office_token: str,
        site_id: int,
        admin_user_id: int,
    ):
        """Уведомление о завершении выезда содержит related_visit_id."""
        office_headers = auth_headers(office_token)
        admin_headers = auth_headers(admin_token)

        visit_res = await http_client.post("/api/visits", headers=office_headers, json={
            "site_id": site_id,
            "assigned_user_id": admin_user_id,
            "planned_date": "2026-05-15",
            "visit_type": "maintenance",
            "priority": "low",
        })
        assert visit_res.status_code == 201
        visit_id = visit_res.json()["id"]

        await http_client.put("/api/notifications/read-all", headers=admin_headers)

        await http_client.post(f"/api/visits/{visit_id}/complete", headers=admin_headers,
                                json={"work_summary": "ТО выполнено", "defects_present": False})

        notifs = await http_client.get("/api/notifications", headers=office_headers)
        visit_notifs = [n for n in notifs.json() if n.get("related_visit_id") == visit_id]
        assert len(visit_notifs) >= 1

        notif = visit_notifs[0]
        assert notif["related_visit_id"] == visit_id
        assert notif["related_defect_id"] is None
        assert notif["related_purchase_id"] is None
        assert notif["type"] == "visit_completed"

    async def test_multiple_status_changes_create_multiple_notifications(
        self,
        http_client: AsyncClient,
        admin_token: str,
        office_token: str,
        site_id: int,
    ):
        """Несколько смен статуса дефекта → несколько уведомлений с одинаковым related_defect_id."""
        admin_headers = auth_headers(admin_token)
        office_headers = auth_headers(office_token)

        await http_client.put("/api/notifications/read-all", headers=admin_headers)

        defect_res = await http_client.post("/api/defects", headers=office_headers, json={
            "title": "__block16__ multiple status changes",
            "site_id": site_id,
            "status": "new",
            "priority": "low",
        })
        assert defect_res.status_code == 201
        defect_id = defect_res.json()["id"]

        await http_client.put(f"/api/defects/{defect_id}", headers=office_headers,
                               json={"status": "in_progress"})
        await http_client.put(f"/api/defects/{defect_id}", headers=office_headers,
                               json={"status": "fixed"})

        notifs = await http_client.get("/api/notifications", headers=admin_headers)
        defect_notifs = [n for n in notifs.json() if n.get("related_defect_id") == defect_id]
        assert len(defect_notifs) >= 2, "Ожидалось >= 2 уведомлений для нескольких смен статуса"

        for n in defect_notifs:
            assert n["related_defect_id"] == defect_id
