"""Геокодирование адресов через 2GIS Geocoding API."""

from typing import Optional, Tuple
import httpx
from app.config import settings

_GEOCODE_URL = "https://catalog.api.2gis.com/3.0/items/geocode"


async def geocode_address(address: str) -> Optional[Tuple[float, float]]:
    """Возвращает (latitude, longitude) для адреса через 2GIS, или None при ошибке.

    Не бросает исключений — при любой проблеме возвращает None, чтобы
    создание/обновление объекта не падало из-за внешнего сервиса.
    """
    if not settings.DGIS_API_KEY:
        return None

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                _GEOCODE_URL,
                params={
                    "q": address,
                    "fields": "items.point",
                    "key": settings.DGIS_API_KEY,
                },
            )
        if resp.status_code != 200:
            return None

        data = resp.json()
        items = data.get("result", {}).get("items", [])
        if not items:
            return None

        point = items[0].get("point")
        if not point:
            return None

        return float(point["lat"]), float(point["lon"])
    except Exception:
        return None
