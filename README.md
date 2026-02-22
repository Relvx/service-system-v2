# Service System v2

Полный рерайт Service System: FastAPI + SQLAlchemy async + Vue 3 + Pinia.

## Стек
- **Backend**: FastAPI + SQLAlchemy (asyncpg) + Alembic + Pydantic v2
- **Frontend**: Vue 3 (Composition API + `<script setup>`) + Pinia + Vue Router 4
- **БД**: PostgreSQL (`service_system_v2`)
- **Карта**: 2GIS MapGL
- **Фото**: Cloudinary
- **Календарь**: FullCalendar Vue3

## Запуск

### 1. База данных
```bash
createdb service_system_v2
```

### 2. Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # отредактируй DATABASE_URL если нужно
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### 3. Frontend
```bash
cd frontend
npm install
npm run dev   # http://localhost:3000
```

## Тестовые аккаунты (пароль: admin123)
| Email | Роль |
|---|---|
| admin@system.local | Администратор |
| master1@system.local | Мастер |
| master2@system.local | Мастер |
| office1@system.local | Офис |

## Переменные окружения

### backend/.env
```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/service_system_v2
JWT_SECRET=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRES_MINUTES=10080
```

### frontend/.env
```
VITE_API_URL=http://localhost:8000/api
VITE_2GIS_KEY=your-2gis-key
VITE_CLOUDINARY_CLOUD_NAME=your-cloud-name
VITE_CLOUDINARY_UPLOAD_PRESET=your-preset
```

## API Endpoints
- `POST /api/auth/login` — авторизация
- `GET /api/auth/me` — текущий пользователь
- `GET /api/config/*` — справочники (roles, visit-statuses, priorities, etc.)
- `GET/POST/PUT/DELETE /api/clients` — клиенты
- `GET/POST/PUT/DELETE /api/sites` — объекты
- `GET/POST/PUT/DELETE /api/visits` — выезды
- `GET /api/visits/calendar` — для FullCalendar
- `POST /api/visits/{id}/complete` — завершение выезда мастером
- `GET/POST/PUT /api/defects` — дефекты
- `GET/POST/PUT /api/purchases` — закупки
- `GET/POST /api/attachments` — фотографии
- `GET/PUT /api/notifications` — уведомления
- `GET /api/dashboard/stats` — статистика дашборда
