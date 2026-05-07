"""
UBID-Sync — Main FastAPI Application
─────────────────────────────────────
Combines mock systems, middleware polling, and dashboard API
into a single lightweight server for prototype demonstration.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .database import engine, SessionLocal, Base
from .models import *  # noqa — ensure all models are registered
from .seed import seed_database
from .middleware.polling_engine import poll_all, initialize_snapshots

# Mock system routers
from .mock_systems.sws import router as sws_router
from .mock_systems.factory import router as factory_router
from .mock_systems.shop import router as shop_router

# Dashboard router
from .api.dashboard import router as dashboard_router

# ── Logging ──────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(name)-25s │ %(levelname)-7s │ %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("ubid_sync")

# ── Scheduler ────────────────────────────────────────────────────────
scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    log.info("Database tables created")

    # Seed data
    db = SessionLocal()
    try:
        # Check if we already have data; if not, seed it.
        # This is vital for Render Free Tier which resets every time it sleeps.
        if db.query(SWSRecord).count() == 0:
            seed_database(db)
            log.info("Fresh seed data loaded for demo")
        else:
            log.info("Database already contains data, skipping seed")
    finally:
        db.close()


    # Initialize polling snapshots
    initialize_snapshots()

    # Start polling scheduler (every 5 seconds)
    scheduler.add_job(poll_all, "interval", seconds=5, id="poll_all", replace_existing=True)
    scheduler.start()
    
    with open("scheduler_status.log", "w") as f:
        f.write(f"Scheduler started at {datetime.now()}\n")
    
    log.info("Polling scheduler started (5s interval)")

    yield

    # Shutdown
    scheduler.shutdown(wait=False)
    log.info("Scheduler stopped")


# ── App ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="UBID-Sync Interoperability Middleware",
    description="Bidirectional synchronization prototype for Karnataka SWS ↔ Department systems",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(sws_router)
app.include_router(factory_router)
app.include_router(shop_router)
app.include_router(dashboard_router)


@app.get("/")
def root():
    return {
        "service": "UBID-Sync Interoperability Middleware",
        "version": "1.0.0",
        "docs": "/docs",
        "systems": ["SWS", "FACTORY", "SHOP"],
    }
