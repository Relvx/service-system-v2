"""
Тесты блока 21 — Галерея фотографий:
  1. GET /attachments/gallery возвращает items + total
  2. Только act_photo попадают в галерею
  3. Поля visit_date, site_title, client_name присутствуют
  4. Пагинация работает
  5. Фильтр по site_id
"""

import pytest
from datetime import date, timedelta
from httpx import AsyncClient
from tests.conftest import auth_headers

FUTURE = str(date.today() + timedelta(days=5))
CLOUDINARY_URL = "https://res.cloudinary.com/test/image/upload/v1/test_photo.jpg"


@pytest.mark.asyncio
class TestGallery:

    async def test_gallery_returns_structure(self, http_client: AsyncClient, admin_token: str):
        """Ответ содержит items и total."""
        res = await http_client.get("/api/attachments/gallery", headers=auth_headers(admin_token))
        assert res.status_code == 200
        data = res.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)
        assert isinstance(data["total"], int)

    async def test_gallery_only_act_photos(
        self, http_client: AsyncClient, admin_token: str, site_id: int, admin_user_id: int
    ):
        """В галерее только kind='act_photo', не document."""
        # создаём выезд
        vr = await http_client.post("/api/visits", json={
            "site_id": site_id,
            "master_ids": [admin_user_id],
            "planned_date": FUTURE,
            "visit_types": ["maintenance"],
        }, headers=auth_headers(admin_token))
        assert vr.status_code == 201
        vid = vr.json()["id"]

        # добавляем act_photo
        ar = await http_client.post("/api/attachments", json={
            "visit_id": vid,
            "kind": "act_photo",
            "file_url": CLOUDINARY_URL,
            "file_name": "test.jpg",
        }, headers=auth_headers(admin_token))
        assert ar.status_code == 201
        att_id = ar.json()["id"]

        # добавляем document — не должно попасть в галерею
        dr = await http_client.post("/api/attachments", json={
            "visit_id": vid,
            "kind": "document",
            "file_url": "https://res.cloudinary.com/test/raw/upload/doc.pdf",
            "file_name": "doc.pdf",
        }, headers=auth_headers(admin_token))
        assert dr.status_code == 201
        doc_id = dr.json()["id"]

        # проверяем галерею
        gr = await http_client.get("/api/attachments/gallery", headers=auth_headers(admin_token))
        assert gr.status_code == 200
        ids_in_gallery = [i["id"] for i in gr.json()["items"]]
        assert att_id in ids_in_gallery
        assert doc_id not in ids_in_gallery

        # cleanup
        await http_client.delete(f"/api/attachments/{att_id}", headers=auth_headers(admin_token))
        await http_client.delete(f"/api/attachments/{doc_id}", headers=auth_headers(admin_token))
        await http_client.delete(f"/api/visits/{vid}", headers=auth_headers(admin_token))

    async def test_gallery_enriched_fields(
        self, http_client: AsyncClient, admin_token: str, site_id: int, admin_user_id: int
    ):
        """Элемент галереи содержит visit_date, site_id, site_title."""
        vr = await http_client.post("/api/visits", json={
            "site_id": site_id,
            "master_ids": [admin_user_id],
            "planned_date": FUTURE,
            "visit_types": ["maintenance"],
        }, headers=auth_headers(admin_token))
        assert vr.status_code == 201
        vid = vr.json()["id"]

        ar = await http_client.post("/api/attachments", json={
            "visit_id": vid,
            "kind": "act_photo",
            "file_url": CLOUDINARY_URL,
        }, headers=auth_headers(admin_token))
        assert ar.status_code == 201
        att_id = ar.json()["id"]

        gr = await http_client.get("/api/attachments/gallery", headers=auth_headers(admin_token))
        assert gr.status_code == 200
        item = next((i for i in gr.json()["items"] if i["id"] == att_id), None)
        assert item is not None
        assert item["visit_id"] == vid
        assert item["visit_date"] == FUTURE
        assert item["site_id"] == site_id
        assert item["site_title"] is not None

        # cleanup
        await http_client.delete(f"/api/attachments/{att_id}", headers=auth_headers(admin_token))
        await http_client.delete(f"/api/visits/{vid}", headers=auth_headers(admin_token))

    async def test_gallery_pagination(self, http_client: AsyncClient, admin_token: str):
        """limit/offset работают."""
        res = await http_client.get(
            "/api/attachments/gallery?limit=1&offset=0", headers=auth_headers(admin_token)
        )
        assert res.status_code == 200
        data = res.json()
        assert len(data["items"]) <= 1

    async def test_gallery_filter_by_site(
        self, http_client: AsyncClient, admin_token: str, site_id: int, admin_user_id: int
    ):
        """Фильтр по site_id возвращает только фото этого объекта."""
        vr = await http_client.post("/api/visits", json={
            "site_id": site_id,
            "master_ids": [admin_user_id],
            "planned_date": FUTURE,
            "visit_types": ["maintenance"],
        }, headers=auth_headers(admin_token))
        assert vr.status_code == 201
        vid = vr.json()["id"]

        ar = await http_client.post("/api/attachments", json={
            "visit_id": vid,
            "kind": "act_photo",
            "file_url": CLOUDINARY_URL,
        }, headers=auth_headers(admin_token))
        assert ar.status_code == 201
        att_id = ar.json()["id"]

        gr = await http_client.get(
            f"/api/attachments/gallery?site_id={site_id}", headers=auth_headers(admin_token)
        )
        assert gr.status_code == 200
        items = gr.json()["items"]
        assert all(i["site_id"] == site_id for i in items)
        assert any(i["id"] == att_id for i in items)

        # cleanup
        await http_client.delete(f"/api/attachments/{att_id}", headers=auth_headers(admin_token))
        await http_client.delete(f"/api/visits/{vid}", headers=auth_headers(admin_token))
