from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import (
    auth, config, users, clients, sites, visits, defects,
    purchases, attachments, notifications, dashboard, tasks, reminders,
    calendar_notes,
)
from app.routers import admin, logs


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.database import AsyncSessionLocal
    from app.enums import load_enums
    async with AsyncSessionLocal() as db:
        await load_enums(db)
    yield


app = FastAPI(
    title="Service System v2 API",
    version="2.0.0",
    redirect_slashes=False,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5002",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(config.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(clients.router, prefix="/api")
app.include_router(sites.router, prefix="/api")
app.include_router(visits.router, prefix="/api")
app.include_router(defects.router, prefix="/api")
app.include_router(purchases.router, prefix="/api")
app.include_router(attachments.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(reminders.router, prefix="/api")
app.include_router(calendar_notes.router, prefix="/api")
app.include_router(logs.router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}
