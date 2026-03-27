"""
Тесты безопасности и бизнес-логики — полный чекап системы.

Покрывает:
- complete_visit: только назначенный мастер или офис/админ
- DELETE /clients, /sites, /visits: только admin_group
- Бизнес-логика: статусы, фильтры, граничные случаи
"""

import pytest
from datetime import date, timedelta
from httpx import AsyncClient
from tests.conftest import auth_headers


# ─── Фикстуры ────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"


# ─── complete_visit ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestCompleteVisitAuth:
    """Только назначенный мастер или офис/админ могут завершать выезд."""

    async def _create_visit_assigned_to_master(self, http_client, admin_token, site_id):
        res = await http_client.post("/api/visits", headers=auth_headers(admin_token), json={
            "site_id": site_id,
            "assigned_user_id": 2,
            "planned_date": "2026-09-01",
            "visit_type": "maintenance",
            "priority": "medium",
        })
        assert res.status_code == 201
        return res.json()["id"]

    async def _create_visit_unassigned(self, http_client, admin_token, site_id):
        res = await http_client.post("/api/visits", headers=auth_headers(admin_token), json={
            "site_id": site_id,
            "assigned_user_id": 2,
            "planned_date": "2026-09-02",
            "visit_type": "maintenance",
            "priority": "medium",
        })
        assert res.status_code == 201
        vid = res.json()["id"]
        await http_client.put(f"/api/visits/{vid}", headers=auth_headers(admin_token),
                              json={"assigned_user_id": None})
        return vid

    async def test_assigned_master_can_complete(
        self, http_client: AsyncClient, admin_token: str, master_token: str, site_id: int
    ):
        visit_id = await self._create_visit_assigned_to_master(http_client, admin_token, site_id)
        res = await http_client.post(
            f"/api/visits/{visit_id}/complete",
            headers=auth_headers(master_token),
            json={"work_summary": "Работы выполнены"},
        )
        assert res.status_code == 200
        await http_client.delete(f"/api/visits/{visit_id}", headers=auth_headers(admin_token))

    async def test_other_master_cannot_complete(
        self, http_client: AsyncClient, admin_token: str, master_token: str, site_id: int
    ):
        visit_id = await self._create_visit_assigned_to_master(http_client, admin_token, site_id)

        login = await http_client.post("/api/auth/login", json={
            "email": "master2@system.local", "password": "admin123"
        })
        master2_token = login.json()["token"]

        res = await http_client.post(
            f"/api/visits/{visit_id}/complete",
            headers=auth_headers(master2_token),
            json={"work_summary": "Пытаюсь завершить чужой выезд"},
        )
        assert res.status_code == 403
        await http_client.delete(f"/api/visits/{visit_id}", headers=auth_headers(admin_token))

    async def test_office_can_complete_any_visit(
        self, http_client: AsyncClient, admin_token: str, office_token: str, site_id: int
    ):
        visit_id = await self._create_visit_assigned_to_master(http_client, admin_token, site_id)
        res = await http_client.post(
            f"/api/visits/{visit_id}/complete",
            headers=auth_headers(office_token),
            json={"work_summary": "Завершено офисом"},
        )
        assert res.status_code == 200
        await http_client.delete(f"/api/visits/{visit_id}", headers=auth_headers(admin_token))

    async def test_unassigned_visit_only_office_can_complete(
        self, http_client: AsyncClient, admin_token: str, master_token: str, site_id: int
    ):
        visit_id = await self._create_visit_unassigned(http_client, admin_token, site_id)
        res = await http_client.post(
            f"/api/visits/{visit_id}/complete",
            headers=auth_headers(master_token),
            json={"work_summary": "Попытка без назначения"},
        )
        assert res.status_code == 403
        await http_client.delete(f"/api/visits/{visit_id}", headers=auth_headers(admin_token))


# ─── DELETE authorization ─────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestDeleteAuthorization:
    """DELETE эндпоинты требуют admin_group."""

    async def test_master_cannot_delete_client(
        self, http_client: AsyncClient, admin_token: str, master_token: str
    ):
        cr = await http_client.post("/api/clients", headers=auth_headers(admin_token),
                                    json={"name": "__test__ delete auth client"})
        cid = cr.json()["id"]
        res = await http_client.delete(f"/api/clients/{cid}", headers=auth_headers(master_token))
        assert res.status_code == 403
        await http_client.delete(f"/api/clients/{cid}", headers=auth_headers(admin_token))

    async def test_office_cannot_delete_client(
        self, http_client: AsyncClient, admin_token: str, office_token: str
    ):
        cr = await http_client.post("/api/clients", headers=auth_headers(admin_token),
                                    json={"name": "__test__ delete auth client2"})
        cid = cr.json()["id"]
        res = await http_client.delete(f"/api/clients/{cid}", headers=auth_headers(office_token))
        assert res.status_code == 403
        await http_client.delete(f"/api/clients/{cid}", headers=auth_headers(admin_token))

    async def test_admin_can_delete_client(
        self, http_client: AsyncClient, admin_token: str
    ):
        cr = await http_client.post("/api/clients", headers=auth_headers(admin_token),
                                    json={"name": "__test__ delete auth client3"})
        cid = cr.json()["id"]
        res = await http_client.delete(f"/api/clients/{cid}", headers=auth_headers(admin_token))
        assert res.status_code == 204

    async def test_master_cannot_delete_site(
        self, http_client: AsyncClient, admin_token: str, master_token: str, site_id: int
    ):
        cr = await http_client.post("/api/clients", headers=auth_headers(admin_token),
                                    json={"name": "__test__ site del client"})
        cid = cr.json()["id"]
        sr = await http_client.post("/api/sites", headers=auth_headers(admin_token),
                                    json={"title": "__test__ site del", "address": "тест", "client_id": cid})
        sid = sr.json()["id"]

        res = await http_client.delete(f"/api/sites/{sid}", headers=auth_headers(master_token))
        assert res.status_code == 403

        await http_client.delete(f"/api/sites/{sid}", headers=auth_headers(admin_token))
        await http_client.delete(f"/api/clients/{cid}", headers=auth_headers(admin_token))

    async def test_master_cannot_delete_visit(
        self, http_client: AsyncClient, admin_token: str, master_token: str, site_id: int
    ):
        vr = await http_client.post("/api/visits", headers=auth_headers(admin_token), json={
            "site_id": site_id, "assigned_user_id": 2, "planned_date": "2026-10-01",
            "visit_type": "maintenance", "priority": "medium",
        })
        vid = vr.json()["id"]
        res = await http_client.delete(f"/api/visits/{vid}", headers=auth_headers(master_token))
        assert res.status_code == 403
        await http_client.delete(f"/api/visits/{vid}", headers=auth_headers(admin_token))

    async def test_office_can_delete_visit(
        self, http_client: AsyncClient, admin_token: str, office_token: str, site_id: int
    ):
        # office_group теперь может удалять выезды
        vr = await http_client.post("/api/visits", headers=auth_headers(admin_token), json={
            "site_id": site_id, "assigned_user_id": 2, "planned_date": "2026-10-02",
            "visit_type": "maintenance", "priority": "medium",
        })
        vid = vr.json()["id"]
        res = await http_client.delete(f"/api/visits/{vid}", headers=auth_headers(office_token))
        assert res.status_code == 204


# ─── Business logic edge cases ────────────────────────────────────────────────

@pytest.mark.asyncio
class TestVisitBusinessLogic:
    """Граничные случаи бизнес-логики выездов."""

    async def test_cancel_completed_visit_returns_400(
        self, http_client: AsyncClient, admin_token: str, office_token: str, site_id: int
    ):
        vr = await http_client.post("/api/visits", headers=auth_headers(admin_token), json={
            "site_id": site_id, "assigned_user_id": 2, "planned_date": "2026-11-01",
            "visit_type": "maintenance", "priority": "medium",
        })
        vid = vr.json()["id"]
        await http_client.post(f"/api/visits/{vid}/complete",
                               headers=auth_headers(office_token),
                               json={"work_summary": "готово"})
        res = await http_client.patch(f"/api/visits/{vid}/cancel",
                                      headers=auth_headers(office_token))
        assert res.status_code == 400
        await http_client.delete(f"/api/visits/{vid}", headers=auth_headers(admin_token))

    async def test_visit_complete_sets_status_closed(
        self, http_client: AsyncClient, admin_token: str, office_token: str, site_id: int
    ):
        vr = await http_client.post("/api/visits", headers=auth_headers(admin_token), json={
            "site_id": site_id, "assigned_user_id": 2, "planned_date": "2026-11-02",
            "visit_type": "repair", "priority": "high",
        })
        vid = vr.json()["id"]
        cr = await http_client.post(f"/api/visits/{vid}/complete",
                                    headers=auth_headers(office_token),
                                    json={"work_summary": "выполнено", "defects_present": True,
                                          "defects_summary": "Обнаружена трещина"})
        assert cr.json()["status"] == "closed"
        assert cr.json()["work_summary"] == "выполнено"
        assert cr.json()["defects_present"] is True
        await http_client.delete(f"/api/visits/{vid}", headers=auth_headers(admin_token))

    async def test_archived_visit_hidden_by_default(
        self, http_client: AsyncClient, admin_token: str, office_token: str, site_id: int
    ):
        """Заархивированный выезд не виден без show_archived=true."""
        far_future = str(date.today() + timedelta(days=5000))
        vr = await http_client.post("/api/visits", headers=auth_headers(admin_token), json={
            "site_id": site_id, "assigned_user_id": 2, "planned_date": far_future,
            "visit_type": "maintenance", "priority": "low",
        })
        vid = vr.json()["id"]
        await http_client.patch(f"/api/visits/{vid}/archive", headers=auth_headers(office_token))

        # Без флага — не виден (фильтруем по site_id + дате для надёжности)
        res = await http_client.get(
            f"/api/visits?site_id={site_id}&date_from={far_future}&date_to={far_future}",
            headers=auth_headers(office_token)
        )
        ids = [v["id"] for v in res.json()["items"]]
        assert vid not in ids

        # С флагом — виден
        res2 = await http_client.get(
            f"/api/visits?show_archived=true&site_id={site_id}&date_from={far_future}&date_to={far_future}",
            headers=auth_headers(admin_token)
        )
        ids2 = [v["id"] for v in res2.json()["items"]]
        assert vid in ids2

        await http_client.delete(f"/api/visits/{vid}", headers=auth_headers(admin_token))

    async def test_visit_notification_sent_on_create(
        self, http_client: AsyncClient, admin_token: str, site_id: int
    ):
        vr = await http_client.post("/api/visits", headers=auth_headers(admin_token), json={
            "site_id": site_id, "assigned_user_id": 2,
            "planned_date": "2026-12-01",
            "visit_type": "maintenance", "priority": "medium",
        })
        assert vr.status_code == 201
        vid = vr.json()["id"]
        await http_client.delete(f"/api/visits/{vid}", headers=auth_headers(admin_token))


@pytest.mark.asyncio
class TestDefectBusinessLogic:
    """Граничные случаи дефектов."""

    async def test_defect_status_transitions(
        self, http_client: AsyncClient, admin_token: str, site_id: int
    ):
        dr = await http_client.post("/api/defects", headers=auth_headers(admin_token), json={
            "site_id": site_id, "title": "__test__ статус-цепочка",
            "priority": "medium", "action_type": "repair",
        })
        assert dr.status_code == 201
        did = dr.json()["id"]
        assert dr.json()["status"] == "open"

        for new_status in ["approved", "in_progress", "fixed"]:
            upd = await http_client.put(f"/api/defects/{did}",
                                        headers=auth_headers(admin_token),
                                        json={"status": new_status})
            assert upd.status_code == 200
            assert upd.json()["status"] == new_status

    async def test_defect_filter_by_status(
        self, http_client: AsyncClient, admin_token: str, site_id: int
    ):
        """Фильтрация дефектов по статусу работает корректно."""
        dr = await http_client.post("/api/defects", headers=auth_headers(admin_token), json={
            "site_id": site_id, "title": "__test__ filter defect",
            "priority": "low", "action_type": "monitor",
        })
        did = dr.json()["id"]

        # Use site_id filter to narrow down
        res = await http_client.get(
            f"/api/defects?status=open&site_id={site_id}", headers=auth_headers(admin_token)
        )
        open_ids = [d["id"] for d in res.json()["items"]]
        assert did in open_ids

        res2 = await http_client.get(
            f"/api/defects?status=fixed&site_id={site_id}", headers=auth_headers(admin_token)
        )
        fixed_ids = [d["id"] for d in res2.json()["items"]]
        assert did not in fixed_ids


@pytest.mark.asyncio
class TestPurchaseBusinessLogic:
    """Граничные случаи закупок."""

    async def test_purchase_archive_unarchive(
        self, http_client: AsyncClient, admin_token: str, site_id: int
    ):
        pr = await http_client.post("/api/purchases", headers=auth_headers(admin_token), json={
            "site_id": site_id, "item": "__test__ archive purchase", "qty": 1,
        })
        assert pr.status_code == 201
        pid = pr.json()["id"]

        arc = await http_client.patch(f"/api/purchases/{pid}/archive",
                                      headers=auth_headers(admin_token))
        assert arc.status_code == 200
        assert arc.json()["is_archived"] is True

        unarc = await http_client.patch(f"/api/purchases/{pid}/unarchive",
                                        headers=auth_headers(admin_token))
        assert unarc.status_code == 200
        assert unarc.json()["is_archived"] is False

    async def test_purchase_status_flow(
        self, http_client: AsyncClient, admin_token: str, site_id: int
    ):
        pr = await http_client.post("/api/purchases", headers=auth_headers(admin_token), json={
            "site_id": site_id, "item": "__test__ status flow", "qty": 2,
        })
        pid = pr.json()["id"]

        upd = await http_client.put(f"/api/purchases/{pid}",
                                    headers=auth_headers(admin_token),
                                    json={"status": "ordered"})
        assert upd.status_code == 200
        assert upd.json()["status"] == "ordered"


@pytest.mark.asyncio
class TestReminderOwnership:
    """Проверка прав на личные напоминания."""

    async def test_personal_reminder_isolation(
        self, http_client: AsyncClient, office_token: str, admin_token: str
    ):
        cr = await http_client.post("/api/reminders", headers=auth_headers(office_token),
                                    json={"text": "__test__ изоляция", "is_personal": True})
        rid = cr.json()["id"]

        res = await http_client.get("/api/reminders", headers=auth_headers(admin_token))
        ids = [r["id"] for r in res.json()]
        assert rid not in ids

        del_res = await http_client.delete(f"/api/reminders/{rid}",
                                           headers=auth_headers(admin_token))
        assert del_res.status_code == 403

        own_del = await http_client.delete(f"/api/reminders/{rid}",
                                           headers=auth_headers(office_token))
        assert own_del.status_code == 204

    async def test_shared_reminder_visible_to_all(
        self, http_client: AsyncClient, office_token: str, admin_token: str, master_token: str
    ):
        cr = await http_client.post("/api/reminders", headers=auth_headers(office_token),
                                    json={"text": "__test__ общее видимость", "is_personal": False})
        rid = cr.json()["id"]

        res = await http_client.get("/api/reminders", headers=auth_headers(admin_token))
        assert rid in [r["id"] for r in res.json()]

        await http_client.delete(f"/api/reminders/{rid}", headers=auth_headers(office_token))


@pytest.mark.asyncio
class TestCalendarNotes:
    """Проверка заметок календаря."""

    async def test_note_crud_full_cycle(
        self, http_client: AsyncClient, office_token: str, admin_token: str
    ):
        cr = await http_client.post("/api/calendar-notes", headers=auth_headers(office_token),
                                    json={"date": "2026-09-15", "text": "__test__ полный цикл"})
        assert cr.status_code == 201
        nid = cr.json()["id"]
        assert cr.json()["text"] == "__test__ полный цикл"

        upd = await http_client.put(f"/api/calendar-notes/{nid}",
                                    headers=auth_headers(admin_token),
                                    json={"text": "обновлённая заметка"})
        assert upd.status_code == 200
        assert upd.json()["text"] == "обновлённая заметка"

        dl = await http_client.delete(f"/api/calendar-notes/{nid}",
                                      headers=auth_headers(office_token))
        assert dl.status_code == 204

    async def test_date_range_filter(self, http_client: AsyncClient, office_token: str):
        cr = await http_client.post("/api/calendar-notes", headers=auth_headers(office_token),
                                    json={"date": "2027-03-01", "text": "__test__ 2027 range"})
        nid = cr.json()["id"]

        res_in = await http_client.get("/api/calendar-notes?start=2027-01-01&end=2027-12-31",
                                       headers=auth_headers(office_token))
        assert nid in [n["id"] for n in res_in.json()]

        res_out = await http_client.get("/api/calendar-notes?start=2026-01-01&end=2026-12-31",
                                        headers=auth_headers(office_token))
        assert nid not in [n["id"] for n in res_out.json()]

        await http_client.delete(f"/api/calendar-notes/{nid}",
                                 headers=auth_headers(office_token))


@pytest.mark.asyncio
class TestClientSiteIntegrity:
    """Проверка целостности клиентов и объектов."""

    async def test_archived_client_hidden_by_default(
        self, http_client: AsyncClient, admin_token: str, office_token: str
    ):
        """Архивный клиент не виден в основном списке."""
        unique_name = "__test__ archive client checkup уникальный"
        cr = await http_client.post("/api/clients", headers=auth_headers(admin_token),
                                    json={"name": unique_name})
        cid = cr.json()["id"]
        await http_client.patch(f"/api/clients/{cid}/archive",
                                headers=auth_headers(office_token))

        res = await http_client.get(
            f"/api/clients?search={unique_name}", headers=auth_headers(office_token)
        )
        ids = [c["id"] for c in res.json()["items"]]
        assert cid not in ids

        res2 = await http_client.get(
            f"/api/clients?show_archived=true&search={unique_name}",
            headers=auth_headers(admin_token)
        )
        ids2 = [c["id"] for c in res2.json()["items"]]
        assert cid in ids2

        await http_client.delete(f"/api/clients/{cid}", headers=auth_headers(admin_token))

    async def test_client_detail_returns_sites_and_visits(
        self, http_client: AsyncClient, admin_token: str, site_id: int
    ):
        sr = await http_client.get(f"/api/sites/{site_id}", headers=auth_headers(admin_token))
        cid = sr.json()["client_id"]

        cr = await http_client.get(f"/api/clients/{cid}", headers=auth_headers(admin_token))
        assert cr.status_code == 200
        data = cr.json()
        assert "sites" in data
        assert "recent_visits" in data
        assert "contact_persons" in data

    async def test_site_detail_shows_active_defects(
        self, http_client: AsyncClient, admin_token: str, site_id: int
    ):
        dr = await http_client.post("/api/defects", headers=auth_headers(admin_token), json={
            "site_id": site_id, "title": "__test__ active defect for site",
            "priority": "high", "action_type": "repair",
        })
        did = dr.json()["id"]

        sr = await http_client.get(f"/api/sites/{site_id}", headers=auth_headers(admin_token))
        defect_ids = [d["id"] for d in sr.json()["active_defects"]]
        assert did in defect_ids

        await http_client.put(f"/api/defects/{did}", headers=auth_headers(admin_token),
                              json={"status": "fixed"})
        sr2 = await http_client.get(f"/api/sites/{site_id}", headers=auth_headers(admin_token))
        defect_ids2 = [d["id"] for d in sr2.json()["active_defects"]]
        assert did not in defect_ids2


@pytest.mark.asyncio
class TestAttachments:
    """Проверка аттачментов."""

    async def test_upload_and_retrieve(
        self, http_client: AsyncClient, admin_token: str, site_id: int
    ):
        res = await http_client.post("/api/attachments", headers=auth_headers(admin_token), json={
            "site_id": site_id, "kind": "photo",
            "file_url": "https://res.cloudinary.com/test/image/upload/v1/test.jpg",
            "file_name": "test.jpg",
        })
        assert res.status_code == 201
        aid = res.json()["id"]

        get_res = await http_client.get(f"/api/attachments?site_id={site_id}",
                                        headers=auth_headers(admin_token))
        ids = [a["id"] for a in get_res.json()]
        assert aid in ids

        del_res = await http_client.delete(f"/api/attachments/{aid}",
                                           headers=auth_headers(admin_token))
        assert del_res.status_code == 204

    async def test_attachment_not_found_on_delete(
        self, http_client: AsyncClient, admin_token: str
    ):
        res = await http_client.delete("/api/attachments/999999",
                                       headers=auth_headers(admin_token))
        assert res.status_code == 404


@pytest.mark.asyncio
class TestNotifications:
    """Проверка уведомлений."""

    async def test_unread_count_decreases_after_read_all(
        self, http_client: AsyncClient, admin_token: str
    ):
        await http_client.put("/api/notifications/read-all",
                              headers=auth_headers(admin_token))
        res = await http_client.get("/api/notifications/unread-count",
                                    headers=auth_headers(admin_token))
        assert res.json()["count"] == 0

    async def test_master_cannot_access_reminders(
        self, http_client: AsyncClient, master_token: str
    ):
        res = await http_client.get("/api/reminders", headers=auth_headers(master_token))
        assert res.status_code == 403

    async def test_master_cannot_access_tasks(
        self, http_client: AsyncClient, master_token: str
    ):
        res = await http_client.get("/api/tasks", headers=auth_headers(master_token))
        assert res.status_code == 403

    async def test_master_cannot_access_calendar_notes(
        self, http_client: AsyncClient, master_token: str
    ):
        res = await http_client.get("/api/calendar-notes", headers=auth_headers(master_token))
        assert res.status_code == 403
