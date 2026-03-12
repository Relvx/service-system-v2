"""
Тесты Block 4 — 2GIS Geocoding.

Мокаем httpx.AsyncClient, чтобы не зависеть от внешнего API.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from tests.conftest import auth_headers


# ─── Юнит-тесты функции geocode_address ──────────────────────────────────────

@pytest.mark.asyncio
class TestGeocodeFunction:

    async def test_returns_coords_on_success(self):
        """При успешном ответе API возвращает (lat, lon)."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": {
                "items": [{"point": {"lat": 55.7558, "lon": 37.6173}}]
            }
        }

        with patch("app.utils.geocoding.settings") as mock_settings, \
             patch("app.utils.geocoding.httpx.AsyncClient") as mock_client_cls:
            mock_settings.DGIS_API_KEY = "test-key"
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            from app.utils.geocoding import geocode_address
            result = await geocode_address("Москва, ул. Тверская, 1")

        assert result == (55.7558, 37.6173)

    async def test_returns_none_when_no_items(self):
        """Если 2GIS ничего не нашёл — возвращает None."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": {"items": []}}

        with patch("app.utils.geocoding.settings") as mock_settings, \
             patch("app.utils.geocoding.httpx.AsyncClient") as mock_client_cls:
            mock_settings.DGIS_API_KEY = "test-key"
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            from app.utils.geocoding import geocode_address
            result = await geocode_address("невалидный адрес xyz")

        assert result is None

    async def test_returns_none_when_api_key_empty(self):
        """Без API-ключа сразу возвращает None без HTTP-запроса."""
        with patch("app.utils.geocoding.settings") as mock_settings:
            mock_settings.DGIS_API_KEY = ""

            from app.utils.geocoding import geocode_address
            result = await geocode_address("Москва")

        assert result is None

    async def test_returns_none_on_http_error(self):
        """При HTTP-ошибке не бросает исключение, возвращает None."""
        mock_response = MagicMock()
        mock_response.status_code = 503

        with patch("app.utils.geocoding.settings") as mock_settings, \
             patch("app.utils.geocoding.httpx.AsyncClient") as mock_client_cls:
            mock_settings.DGIS_API_KEY = "test-key"
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            from app.utils.geocoding import geocode_address
            result = await geocode_address("Москва")

        assert result is None

    async def test_returns_none_on_network_exception(self):
        """При сетевом исключении не бросает, возвращает None."""
        with patch("app.utils.geocoding.settings") as mock_settings, \
             patch("app.utils.geocoding.httpx.AsyncClient") as mock_client_cls:
            mock_settings.DGIS_API_KEY = "test-key"
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=Exception("timeout"))
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            from app.utils.geocoding import geocode_address
            result = await geocode_address("Москва")

        assert result is None


# ─── Интеграционные тесты через API ──────────────────────────────────────────

MOCK_COORDS = (55.7558, 37.6173)


def _mock_geocode(address: str):
    """Мок geocode_address для интеграционных тестов."""
    async def _inner(addr):
        return MOCK_COORDS
    return _inner


@pytest.mark.asyncio
class TestSiteGeocodingIntegration:

    async def test_create_site_auto_geocodes(
        self, http_client, admin_token: str
    ):
        """При создании объекта без координат автоматически заполняются из 2GIS."""
        with patch("app.routers.sites.geocode_address",
                   new=AsyncMock(return_value=MOCK_COORDS)):
            res = await http_client.post(
                "/api/sites",
                headers=auth_headers(admin_token),
                json={"title": "__test__ geocode create", "address": "Москва, Тверская 1"},
            )
        assert res.status_code == 201
        data = res.json()
        assert data["latitude"] == MOCK_COORDS[0]
        assert data["longitude"] == MOCK_COORDS[1]
        sid = data["id"]
        await http_client.delete(f"/api/sites/{sid}", headers=auth_headers(admin_token))

    async def test_create_site_with_explicit_coords_not_overridden(
        self, http_client, admin_token: str
    ):
        """Явно переданные координаты не перезаписываются геокодером."""
        with patch("app.routers.sites.geocode_address",
                   new=AsyncMock(return_value=MOCK_COORDS)):
            res = await http_client.post(
                "/api/sites",
                headers=auth_headers(admin_token),
                json={
                    "title": "__test__ explicit coords",
                    "address": "Адрес",
                    "latitude": 59.9343,
                    "longitude": 30.3351,
                },
            )
        assert res.status_code == 201
        data = res.json()
        # Координаты должны остаться явно заданными, геокодер не вызывался
        assert data["latitude"] == 59.9343
        assert data["longitude"] == 30.3351
        sid = data["id"]
        await http_client.delete(f"/api/sites/{sid}", headers=auth_headers(admin_token))

    async def test_update_site_address_triggers_geocoding(
        self, http_client, admin_token: str, site_id: int
    ):
        """При изменении адреса координаты обновляются автоматически."""
        with patch("app.routers.sites.geocode_address",
                   new=AsyncMock(return_value=(60.0, 30.0))):
            res = await http_client.put(
                f"/api/sites/{site_id}",
                headers=auth_headers(admin_token),
                json={"address": "Санкт-Петербург, Невский проспект 1"},
            )
        assert res.status_code == 200
        data = res.json()
        assert data["latitude"] == 60.0
        assert data["longitude"] == 30.0

    async def test_update_site_without_address_no_geocoding(
        self, http_client, admin_token: str, site_id: int
    ):
        """Если адрес не меняется, геокодер не вызывается."""
        geocode_mock = AsyncMock(return_value=MOCK_COORDS)
        with patch("app.routers.sites.geocode_address", new=geocode_mock):
            res = await http_client.put(
                f"/api/sites/{site_id}",
                headers=auth_headers(admin_token),
                json={"access_notes": "обновлённые заметки"},
            )
        assert res.status_code == 200
        geocode_mock.assert_not_called()

    async def test_manual_geocode_endpoint(
        self, http_client, admin_token: str, site_id: int
    ):
        """POST /sites/{id}/geocode обновляет координаты объекта."""
        with patch("app.routers.sites.geocode_address",
                   new=AsyncMock(return_value=(51.5074, -0.1278))):
            res = await http_client.post(
                f"/api/sites/{site_id}/geocode",
                headers=auth_headers(admin_token),
            )
        assert res.status_code == 200
        data = res.json()
        assert data["latitude"] == 51.5074
        assert data["longitude"] == -0.1278

    async def test_manual_geocode_fails_gracefully(
        self, http_client, admin_token: str, site_id: int
    ):
        """POST /sites/{id}/geocode возвращает 502 если API недоступен."""
        with patch("app.routers.sites.geocode_address", new=AsyncMock(return_value=None)):
            res = await http_client.post(
                f"/api/sites/{site_id}/geocode",
                headers=auth_headers(admin_token),
            )
        assert res.status_code == 502

    async def test_geocode_not_found_site(
        self, http_client, admin_token: str
    ):
        """POST /sites/999999/geocode → 404."""
        res = await http_client.post(
            "/api/sites/999999/geocode",
            headers=auth_headers(admin_token),
        )
        assert res.status_code == 404
