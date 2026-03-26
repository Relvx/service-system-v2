"""
Тесты блока 12 — Оптимизация запросов календаря.

- GET /api/visits/calendar — загрузка по окну start/end (не весь год)
- GET /api/calendar-notes — фильтрация по start/end (не по year)
- Проверка что данные вне окна не возвращаются
"""

import datetime
import pytest
from httpx import AsyncClient
from tests.conftest import auth_headers

TODAY = datetime.date.today()
TODAY_STR = TODAY.isoformat()

# Окно: текущий месяц (примерно 6 недель как в гриде FullCalendar)
WINDOW_START = (TODAY.replace(day=1) - datetime.timedelta(days=7)).isoformat()
WINDOW_END = (TODAY.replace(day=1) + datetime.timedelta(days=42)).isoformat()

# Дата вне окна — за 3 года до
OUT_OF_WINDOW = (TODAY - datetime.timedelta(days=1100)).isoformat()


@pytest.mark.asyncio
class TestCalendarWindowedLoading:
    async def test_calendar_visits_window(self, http_client: AsyncClient, admin_token: str, site_id: int, admin_user_id: str):
        """Выезды возвращаются только за указанное окно start/end."""
        headers = auth_headers(admin_token)

        # Создаём выезд ВНУТРИ окна
        res_in = await http_client.post("/api/visits", headers=headers, json={
            "site_id": site_id,
            "assigned_user_id": int(admin_user_id),
            "planned_date": TODAY_STR,
            "visit_type": "maintenance",
            "priority": "medium",
            "status": "planned",
        })
        assert res_in.status_code == 201
        visit_in_id = res_in.json()["id"]

        # Создаём выезд ВНЕ окна
        res_out = await http_client.post("/api/visits", headers=headers, json={
            "site_id": site_id,
            "assigned_user_id": int(admin_user_id),
            "planned_date": OUT_OF_WINDOW,
            "visit_type": "maintenance",
            "priority": "medium",
            "status": "planned",
        })
        assert res_out.status_code == 201
        visit_out_id = res_out.json()["id"]

        # Запрашиваем только окно
        res = await http_client.get(
            f"/api/visits/calendar?start={WINDOW_START}&end={WINDOW_END}",
            headers=headers,
        )
        assert res.status_code == 200
        ids = [v["id"] for v in res.json()]

        # Выезд внутри окна — должен быть
        assert visit_in_id in ids
        # Выезд вне окна — не должен быть
        assert visit_out_id not in ids

        # Cleanup
        await http_client.delete(f"/api/visits/{visit_in_id}", headers=headers)
        await http_client.delete(f"/api/visits/{visit_out_id}", headers=headers)

    async def test_calendar_visits_requires_start_end(self, http_client: AsyncClient, admin_token: str):
        """GET /api/visits/calendar без start/end → 422."""
        res = await http_client.get("/api/visits/calendar", headers=auth_headers(admin_token))
        assert res.status_code == 422

    async def test_calendar_visits_start_equals_end(self, http_client: AsyncClient, admin_token: str, site_id: int, admin_user_id: str):
        """Можно запросить один день — start == end."""
        headers = auth_headers(admin_token)
        res_v = await http_client.post("/api/visits", headers=headers, json={
            "site_id": site_id,
            "assigned_user_id": int(admin_user_id),
            "planned_date": TODAY_STR,
            "visit_type": "repair",
            "priority": "high",
            "status": "planned",
        })
        assert res_v.status_code == 201
        visit_id = res_v.json()["id"]

        res = await http_client.get(
            f"/api/visits/calendar?start={TODAY_STR}&end={TODAY_STR}",
            headers=headers,
        )
        assert res.status_code == 200
        ids = [v["id"] for v in res.json()]
        assert visit_id in ids

        await http_client.delete(f"/api/visits/{visit_id}", headers=headers)


@pytest.mark.asyncio
class TestCalendarNotesWindowedLoading:
    async def test_notes_filter_by_start_end(self, http_client: AsyncClient, office_token: str):
        """Заметки фильтруются по start/end, не по year."""
        headers = auth_headers(office_token)

        # Создаём заметку ВНУТРИ окна
        note_date_in = TODAY_STR
        res_in = await http_client.post("/api/calendar-notes", headers=headers, json={
            "date": note_date_in,
            "text": "__test__ block12 in-window note",
        })
        assert res_in.status_code == 201
        note_in_id = res_in.json()["id"]

        # Создаём заметку ВНЕ окна
        res_out = await http_client.post("/api/calendar-notes", headers=headers, json={
            "date": OUT_OF_WINDOW,
            "text": "__test__ block12 out-of-window note",
        })
        assert res_out.status_code == 201
        note_out_id = res_out.json()["id"]

        # Запрашиваем с фильтром start/end
        res = await http_client.get(
            f"/api/calendar-notes?start={WINDOW_START}&end={WINDOW_END}",
            headers=headers,
        )
        assert res.status_code == 200
        ids = [n["id"] for n in res.json()]

        assert note_in_id in ids
        assert note_out_id not in ids

        # Cleanup
        await http_client.delete(f"/api/calendar-notes/{note_in_id}", headers=headers)
        await http_client.delete(f"/api/calendar-notes/{note_out_id}", headers=headers)

    async def test_notes_no_filter_returns_all(self, http_client: AsyncClient, office_token: str):
        """Без start/end возвращаются все заметки."""
        headers = auth_headers(office_token)

        res_a = await http_client.post("/api/calendar-notes", headers=headers, json={
            "date": TODAY_STR,
            "text": "__test__ block12 no-filter A",
        })
        res_b = await http_client.post("/api/calendar-notes", headers=headers, json={
            "date": OUT_OF_WINDOW,
            "text": "__test__ block12 no-filter B",
        })
        id_a = res_a.json()["id"]
        id_b = res_b.json()["id"]

        res = await http_client.get("/api/calendar-notes", headers=headers)
        assert res.status_code == 200
        ids = [n["id"] for n in res.json()]
        assert id_a in ids
        assert id_b in ids

        await http_client.delete(f"/api/calendar-notes/{id_a}", headers=headers)
        await http_client.delete(f"/api/calendar-notes/{id_b}", headers=headers)

    async def test_notes_only_start_filter(self, http_client: AsyncClient, office_token: str):
        """Только start — возвращает заметки от start и новее."""
        headers = auth_headers(office_token)

        res_n = await http_client.post("/api/calendar-notes", headers=headers, json={
            "date": TODAY_STR,
            "text": "__test__ block12 start-only",
        })
        note_id = res_n.json()["id"]

        far_past = (TODAY - datetime.timedelta(days=3000)).isoformat()
        res = await http_client.get(
            f"/api/calendar-notes?start={far_past}",
            headers=headers,
        )
        assert res.status_code == 200
        ids = [n["id"] for n in res.json()]
        assert note_id in ids

        await http_client.delete(f"/api/calendar-notes/{note_id}", headers=headers)

    async def test_notes_master_forbidden(self, http_client: AsyncClient, master_token: str):
        """Мастер не имеет доступа к заметкам даже с параметрами start/end."""
        res = await http_client.get(
            f"/api/calendar-notes?start={WINDOW_START}&end={WINDOW_END}",
            headers=auth_headers(master_token),
        )
        assert res.status_code == 403
