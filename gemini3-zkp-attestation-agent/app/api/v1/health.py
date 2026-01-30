"""
Health Check Endpoint
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import logging

from app.config import settings
from app.db.session import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Health check endpoint
    Returns service status and component health
    """
    components = {}
    
    # Database health
    try:
        await db.execute("SELECT 1")
        components["database"] = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        components["database"] = "unhealthy"
    
    # Proof engine health (placeholder)
    components["proof_engine"] = "healthy"
    
    # Storage health (placeholder)
    components["storage"] = "healthy"
    
    # Anchoring service health (placeholder)
    if settings.ANCHORING_ENABLED:
        components["anchoring_service"] = "healthy"
    
    # Overall status
    all_healthy = all(status == "healthy" for status in components.values())
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "components": components,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@router.get("/health/live")
async def liveness_check():
    """
    Liveness probe - simple check if service is running
    """
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """
    Readiness probe - check if service is ready to accept requests
    """
    try:
        await db.execute("SELECT 1")
        return {"status": "ready"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {"status": "not_ready", "reason": str(e)}
