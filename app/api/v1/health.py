from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.agency import Agency
from app.models.agent import AgentProfile
from app.models.snapshot import AgentRankSnapshot
from app.models.transaction import AgentTransaction

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Healthcheck endpoint reporting database connection and record statistics."""
    try:
        agency_count = (await db.execute(select(func.count(Agency.id)))).scalar_one()
        agent_count = (await db.execute(select(func.count(AgentProfile.id)))).scalar_one()
        tx_count = (await db.execute(select(func.count(AgentTransaction.id)))).scalar_one()
        snapshot_count = (await db.execute(select(func.count(AgentRankSnapshot.id)))).scalar_one()

        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "database": "connected",
            "stats": {
                "agencies": agency_count,
                "agents": agent_count,
                "transactions": tx_count,
                "rank_snapshots": snapshot_count,
            },
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "database": f"error: {str(e)}",
        }
