"""
Seed script: creates 10 test clients and 15 test sites for demo/testing.
Usage: python scripts/seed_demo_data.py
Requires the backend to be running at http://localhost:8000.
"""

import asyncio
import httpx

API = "http://localhost:8000/api"
ADMIN_EMAIL = "admin@system.local"
ADMIN_PASSWORD = "admin123"


CLIENTS = [
    {
        "name": "ООО «АльфаТех»",
        "inn": "7701234567",
        "contact_person": "Иванов Алексей Петрович",
        "contacts": "+7 (495) 111-22-33",
        "notes": "Крупный клиент, промышленное оборудование",
    },
    {
        "name": "ЗАО «БетаСервис»",
        "inn": "7712345678",
        "contact_person": "Смирнова Елена Владимировна",
        "contacts": "+7 (495) 222-33-44",
        "notes": "Торговые центры, регулярное ТО",
    },
    {
        "name": "ИП Горбунов Дмитрий",
        "inn": "781234567890",
        "contact_person": "Горбунов Дмитрий Николаевич",
        "contacts": "+7 (812) 333-44-55",
    },
    {
        "name": "ООО «ГаммаХолдинг»",
        "inn": "7723456789",
        "contact_person": "Петров Сергей Михайлович",
        "contacts": "+7 (495) 444-55-66",
        "notes": "Офисные здания в центре",
    },
    {
        "name": "АО «ДельтаСтрой»",
        "inn": "7734567890",
        "contact_person": "Кузнецова Ольга Андреевна",
        "contacts": "+7 (495) 555-66-77",
        "notes": "Строительная компания, склады и объекты",
    },
    {
        "name": "ООО «ЭпсилонМед»",
        "inn": "7745678901",
        "contact_person": "Новиков Андрей Борисович",
        "contacts": "+7 (495) 666-77-88",
        "notes": "Медицинские учреждения",
    },
    {
        "name": "ООО «ЗетаФуд»",
        "inn": "7756789012",
        "contact_person": "Морозова Татьяна Сергеевна",
        "contacts": "+7 (495) 777-88-99",
        "notes": "Ресторанный холдинг, холодильное оборудование",
    },
    {
        "name": "ПАО «ЭтаЭнерго»",
        "inn": "7767890123",
        "contact_person": "Волков Игорь Александрович",
        "contacts": "+7 (495) 888-99-00",
        "notes": "Энергетические объекты",
    },
    {
        "name": "ООО «ТетаЛогистик»",
        "inn": "7778901234",
        "contact_person": "Соколова Наталья Ивановна",
        "contacts": "+7 (495) 900-11-22",
        "notes": "Логистический центр, склады",
    },
    {
        "name": "ЗАО «ИотаРетейл»",
        "inn": "7789012345",
        "contact_person": "Лебедев Константин Юрьевич",
        "contacts": "+7 (495) 011-22-33",
        "notes": "Розничная сеть магазинов",
    },
]


# 15 sites distributed among clients (by index into created client IDs)
SITES_TEMPLATE = [
    # client_index, title, address, lat, lon, service_frequency, price_maintenance
    (0, "Завод Северный", "Москва, Дмитровское ш., 58", 55.8897, 37.5368, "monthly", 15000),
    (0, "Склад АльфаТех №2", "Москва, ул. Складочная, 1", 55.7956, 37.5934, "quarterly", 8000),
    (1, "ТЦ «Весна»", "Москва, Ленинградский пр-т, 76", 55.8008, 37.5072, "monthly", 25000),
    (1, "ТЦ «Осень»", "Москва, Варшавское ш., 148", 55.6201, 37.6247, "monthly", 22000),
    (2, "Офис Горбунова", "Санкт-Петербург, Невский пр., 100", 59.9320, 30.3609, "quarterly", 5000),
    (3, "БЦ «Гамма Плаза»", "Москва, Пресненская наб., 10", 55.7494, 37.5399, "monthly", 30000),
    (3, "БЦ «Гамма Сити»", "Москва, ул. Новый Арбат, 19", 55.7520, 37.5792, "monthly", 28000),
    (4, "Склад ДельтаСтрой-1", "Москва, МКАД 25-й км", 55.7558, 37.3660, "quarterly", 10000),
    (5, "Клиника «МедЦентр»", "Москва, ул. Профсоюзная, 56", 55.6778, 37.5593, "monthly", 18000),
    (5, "Лаборатория ЭпсилонМед", "Москва, ул. Академика Варги, 8", 55.6503, 37.4681, "monthly", 12000),
    (6, "Ресторан «Арбат»", "Москва, Арбат, 28", 55.7506, 37.5955, "monthly", 9000),
    (6, "Ресторан «Замоскворечье»", "Москва, ул. Пятницкая, 40", 55.7341, 37.6276, "monthly", 9000),
    (7, "Подстанция №47", "Москва, ул. Энергетическая, 7", 55.7565, 37.7205, "quarterly", 20000),
    (8, "Логистический хаб «Юг»", "Москва, А-107, 22-й км", 55.5879, 37.7010, "quarterly", 14000),
    (9, "Магазин «Иота» на Тверской", "Москва, Тверская ул., 15", 55.7637, 37.6066, "monthly", 7000),
]


async def main():
    async with httpx.AsyncClient(base_url=API, timeout=30) as client:
        # Login
        login_res = await client.post("/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
        if login_res.status_code != 200:
            print(f"Login failed: {login_res.status_code} {login_res.text}")
            return
        token = login_res.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        print(f"Logged in as {ADMIN_EMAIL}")

        # Create clients
        client_ids = []
        for c in CLIENTS:
            res = await client.post("/clients", headers=headers, json=c)
            if res.status_code == 201:
                cid = res.json()["id"]
                client_ids.append(cid)
                print(f"  Created client: {c['name']} (id={cid})")
            else:
                print(f"  FAILED client {c['name']}: {res.status_code} {res.text}")
                client_ids.append(None)

        # Create sites
        freq_map = {"monthly": "monthly", "quarterly": "quarterly"}
        for (ci, title, address, lat, lon, freq, price) in SITES_TEMPLATE:
            cid = client_ids[ci] if ci < len(client_ids) else None
            payload = {
                "client_id": cid,
                "title": title,
                "address": address,
                "latitude": lat,
                "longitude": lon,
                "service_frequency": freq_map.get(freq, freq),
                "price_maintenance": float(price),
            }
            res = await client.post("/sites", headers=headers, json=payload)
            if res.status_code == 201:
                sid = res.json()["id"]
                print(f"  Created site: {title} (id={sid}, client_id={cid})")
            else:
                print(f"  FAILED site {title}: {res.status_code} {res.text}")

        print("\nDone.")


if __name__ == "__main__":
    asyncio.run(main())
