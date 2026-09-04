from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.api.views import router as views_router
from app.config import settings
from app.core.database import AsyncSessionLocal, init_db
from app.ingestion.cea_client import CEAClient
from app.models.agent import AgentProfile
from app.pipeline.aggregator import AggregationPipeline
from sqlalchemy import func, select

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cea_engine")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Database Tables
    logger.info("Initializing database schema...")
    await init_db()

    # Auto-seed sample dataset if database is empty
    async with AsyncSessionLocal() as session:
        agent_count = (await session.execute(select(func.count(AgentProfile.id)))).scalar_one()
        if agent_count == 0:
            logger.info("Database empty. Auto-seeding initial CEA cohort for immediate testing...")
            client = CEAClient()
            raw_agents, raw_txs = await client.ingest_raw_feed(use_fixtures=True, sample_size=100)
            pipeline = AggregationPipeline(session=session)
            await pipeline.sync_raw_data(raw_agents, raw_txs)
            await pipeline.compute_and_save_rankings()
            logger.info("Initial CEA cohort seeding complete.")

    yield
    logger.info("Shutting down CEA Ranking Engine.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Agent 1: CEA Ranking & Property Transaction Ingestion Engine for Singapore Real Estate.",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(views_router)

# Mount Static assets for UI
if settings.STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(settings.STATIC_DIR)), name="static")
