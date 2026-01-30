"""
FastAPI Application Entry Point
ZKP Attestation Agent (ZKPA)
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from prometheus_client import make_asgi_app

from app.config import settings
from app.utils.logger import setup_logging
from app.api.v1 import attestations, verification, lifecycle, health, evidence, proofs, attestation_assembly, anchoring
from app.db.session import engine, Base

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events - startup and shutdown
    """
    # Startup
    logger.info("Starting ZKPA service...")
    logger.info(f"Environment: {settings.APP_ENV}")
    logger.info(f"Version: {settings.APP_VERSION}")
    
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Database tables created/verified")
    logger.info("ZKPA service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down ZKPA service...")
    await engine.dispose()
    logger.info("ZKPA service shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="ZKP Attestation Agent (ZKPA)",
    description="Privacy-Preserving Compliance Attestations using Zero-Knowledge Proofs",
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# CORS Middleware
if settings.CORS_ENABLED:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# GZip Middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include routers
app.include_router(
    health.router,
    tags=["Health"],
)

app.include_router(
    attestations.router,
    prefix="/api/v1/attestations",
    tags=["Attestations"],
)

app.include_router(
    verification.router,
    prefix="/api/v1",
    tags=["Verification"],
)

app.include_router(
    lifecycle.router,
    prefix="/api/v1",
    tags=["Lifecycle"],
)

app.include_router(
    evidence.router,
    prefix="/api/v1",
    tags=["Evidence"],
)

app.include_router(
    proofs.router,
    prefix="/api/v1",
    tags=["Proofs"],
)

app.include_router(
    attestation_assembly.router,
    prefix="/api/v1",
    tags=["Attestation Assembly"],
)

app.include_router(
    anchoring.router,
    prefix="/api/v1",
    tags=["Anchoring & Publication"],
)

# Prometheus metrics endpoint
if settings.PROMETHEUS_ENABLED:
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred",
            "request_id": request.state.request_id if hasattr(request.state, "request_id") else None
        }
    )


@app.middleware("http")
async def add_request_id_middleware(request: Request, call_next):
    """
    Add request ID to each request for tracing
    """
    import uuid
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.get("/", include_in_schema=False)
async def root():
    """
    Root endpoint - service info
    """
    return {
        "service": "ZKP Attestation Agent (ZKPA)",
        "version": settings.APP_VERSION,
        "status": "operational",
        "docs": "/docs" if settings.DEBUG else "disabled in production",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower()
    )
